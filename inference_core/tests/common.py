"""Shared cocotb helpers for the paired SRAM and fixed MoE expert cores."""

from __future__ import annotations

import json
from pathlib import Path

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, FallingEdge, ReadOnly, RisingEdge, Timer
import numpy as np


ROOT = Path(__file__).resolve().parents[2]
CORE = ROOT / "inference_core"
MODELS = CORE / "models"
SPEC = json.loads((CORE / "spec.json").read_text())
EXPERTS = int(SPEC["experts"])
WIDTH = int(SPEC["model_width"])
HIDDEN = int(SPEC["hidden_width"])
ACC_WIDTH = int(SPEC["accumulator_bits"])
CLOCK_NS = 10


def twos(value: int, width: int) -> int:
    return value & ((1 << width) - 1)


def signed(signal, width: int) -> int:
    raw = int(signal.value)
    return raw - (1 << width) if raw & (1 << (width - 1)) else raw


def pack_int4(row: np.ndarray) -> int:
    return sum((int(value) & 0xF) << (4 * index) for index, value in enumerate(row))


async def reset(dut, design: str) -> None:
    await Timer(1, unit="ns")
    dut.rst_n.value = 0
    dut.start.value = 0
    dut.input_we.value = 0
    dut.input_addr.value = 0
    dut.input_data.value = 0
    dut.output_addr.value = 0
    if design == "generic":
        dut.weight_we.value = 0
        dut.weight_region.value = 0
        dut.weight_addr.value = 0
        dut.weight_data.value = 0
    await ClockCycles(dut.clk, 3)
    await ReadOnly()
    assert int(dut.busy.value) == 0
    assert int(dut.done.value) == 0
    for output_index in range(WIDTH):
        await FallingEdge(dut.clk)
        dut.output_addr.value = output_index
        await Timer(1, unit="ns")
        await ReadOnly()
        assert signed(dut.output_data, ACC_WIDTH) == 0, (
            f"design={design} reset output={output_index} was not zero"
        )
    await FallingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert int(dut.done.value) == 0


async def load_word(dut, region: int, address: int, data: int) -> None:
    await FallingEdge(dut.clk)
    dut.weight_we.value = 1
    dut.weight_region.value = region
    dut.weight_addr.value = address
    dut.weight_data.value = data
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert int(dut.busy.value) == 0
    assert int(dut.done.value) == 0


async def load_runtime_model(dut) -> None:
    router = np.load(MODELS / "router_weights.npy")
    up = np.load(MODELS / "up_weights.npy")
    gate = np.load(MODELS / "gate_weights.npy")
    down = np.load(MODELS / "down_weights.npy")
    for address, row in enumerate(router):
        await load_word(dut, 0, address, pack_int4(row))
    for expert in range(EXPERTS):
        for hidden in range(HIDDEN):
            address = expert * HIDDEN + hidden
            await load_word(dut, 1, address, pack_int4(up[expert, hidden]))
            await load_word(dut, 2, address, pack_int4(gate[expert, hidden]))
    for expert in range(EXPERTS):
        for output in range(WIDTH):
            address = expert * WIDTH + output
            await load_word(dut, 3, address, pack_int4(down[expert, output]))
    await FallingEdge(dut.clk)
    dut.weight_we.value = 0


async def load_input(dut, values: np.ndarray, design: str, vector_index: int) -> None:
    for address, value in enumerate(values):
        await FallingEdge(dut.clk)
        dut.input_we.value = 1
        dut.input_addr.value = address
        dut.input_data.value = twos(int(value), 8)
        await RisingEdge(dut.clk)
        await ReadOnly()
        assert int(dut.done.value) == 0, (
            f"design={design} vector={vector_index} done during input load"
        )
    await FallingEdge(dut.clk)
    dut.input_we.value = 0
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert int(dut.busy.value) == 0
    assert int(dut.done.value) == 0


async def start_and_wait(dut, design: str, vector_index: int) -> int:
    await FallingEdge(dut.clk)
    dut.start.value = 1
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert int(dut.busy.value) == 1, f"design={design} vector={vector_index} never became busy"
    assert int(dut.done.value) == 0
    await FallingEdge(dut.clk)
    dut.start.value = 0
    latency = 0
    while latency < 400:
        await RisingEdge(dut.clk)
        await ReadOnly()
        latency += 1
        if int(dut.done.value):
            assert int(dut.busy.value) == 0
            break
    else:
        raise AssertionError(f"design={design} vector={vector_index} timed out waiting for done")
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert int(dut.done.value) == 0, (
        f"design={design} vector={vector_index} done was not a one-cycle pulse"
    )
    return latency


async def check_outputs(dut, expected: np.ndarray, design: str, vector_index: int) -> None:
    for output_index, expected_value in enumerate(expected):
        await FallingEdge(dut.clk)
        dut.output_addr.value = output_index
        await Timer(1, unit="ns")
        await ReadOnly()
        observed = signed(dut.output_data, ACC_WIDTH)
        assert observed == int(expected_value), (
            f"design={design} vector={vector_index} output={output_index} "
            f"expected={int(expected_value)} observed={observed}"
        )


async def run_suite(dut, design: str) -> None:
    inputs = np.load(MODELS / "inputs.npy")
    expected = np.load(MODELS / "expected_outputs.npy")
    routes = np.load(MODELS / "expected_routes.npy")
    assert inputs.shape == (int(SPEC["test_vectors"]), WIDTH)
    assert expected.shape == (len(inputs), WIDTH)

    dut.clk.value = 0
    cocotb.start_soon(Clock(dut.clk, CLOCK_NS, unit="ns").start())
    await reset(dut, design)
    if design == "generic":
        await load_runtime_model(dut)

    latencies = []
    for vector_index, vector in enumerate(inputs):
        await load_input(dut, vector, design, vector_index)
        latencies.append(await start_and_wait(dut, design, vector_index))
        await check_outputs(dut, expected[vector_index], design, vector_index)
        observed_route = int(dut.selected_expert.value)
        assert observed_route == int(routes[vector_index]), (
            f"design={design} vector={vector_index} route "
            f"expected={int(routes[vector_index])} observed={observed_route}"
        )

    assert len(set(latencies)) == 1, f"design={design} latency varied: {latencies}"
    dut._log.info(
        "%s: %d/%d vectors passed, latency=%d cycles/token",
        design,
        len(inputs),
        len(inputs),
        latencies[0],
    )
