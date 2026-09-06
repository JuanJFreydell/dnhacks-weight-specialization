"""Shared cocotb verification for the generic and fixed matvec designs."""

from pathlib import Path

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, FallingEdge, ReadOnly, RisingEdge, Timer
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
MODELS = ROOT / "models"
ROWS = 8
COLS = 8
ACC_WIDTH = 24
CLOCK_PERIOD_NS = 10


def twos_complement(value: int, width: int) -> int:
    """Encode a signed Python integer for assignment to an unsigned HDL handle."""
    return value & ((1 << width) - 1)


def signed_value(signal, width: int) -> int:
    """Read an HDL vector and interpret it as a width-bit two's-complement value."""
    raw = int(signal.value)
    sign_bit = 1 << (width - 1)
    return raw - (1 << width) if raw & sign_bit else raw


def assert_interface_widths(dut, *, has_runtime_weights: bool) -> None:
    assert len(dut.input_data) == 8, "input_data must be signed INT8"
    assert len(dut.input_addr) == 3, "input_addr must address all eight inputs"
    assert len(dut.output_data) == ACC_WIDTH, "output_data must be signed 24-bit"
    assert len(dut.output_addr) == 3, "output_addr must address all eight outputs"
    if has_runtime_weights:
        assert len(dut.weight_data) == 8, "weight_data must be signed INT8"
        assert len(dut.weight_addr) == 6, "weight_addr must address 64 row-major weights"


def assert_done(dut, expected: int, design: str, vector_index: int, phase: str) -> None:
    observed = int(dut.done.value)
    assert observed == expected, (
        f"design={design} vector={vector_index} done phase={phase} "
        f"expected={expected} observed={observed}"
    )


async def reset_dut(dut, design: str, vector_index: int) -> None:
    # Move out of a prior ReadOnly phase before driving the next reset.
    await Timer(1, unit="ns")
    dut.rst_n.value = 0
    dut.start.value = 0
    dut.input_we.value = 0
    dut.input_addr.value = 0
    dut.input_data.value = 0
    dut.output_addr.value = 0
    if hasattr(dut, "weight_we"):
        dut.weight_we.value = 0
        dut.weight_addr.value = 0
        dut.weight_data.value = 0

    await ClockCycles(dut.clk, 2)
    await ReadOnly()
    assert_done(dut, 0, design, vector_index, "reset")

    # Reset must initialize every externally readable result register.
    for output_index in range(ROWS):
        await FallingEdge(dut.clk)
        dut.output_addr.value = output_index
        await Timer(1, unit="ns")
        await ReadOnly()
        observed = signed_value(dut.output_data, ACC_WIDTH)
        assert observed == 0, (
            f"design={design} vector={vector_index} output={output_index} "
            f"reset expected=0 observed={observed}"
        )

    await FallingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert_done(dut, 0, design, vector_index, "after-reset")


async def load_runtime_weights(dut, weights, design: str, vector_index: int) -> None:
    for address, value in enumerate(weights.ravel(order="C")):
        await FallingEdge(dut.clk)
        dut.weight_we.value = 1
        dut.weight_addr.value = address
        dut.weight_data.value = twos_complement(int(value), 8)
        await RisingEdge(dut.clk)
        await ReadOnly()
        assert_done(dut, 0, design, vector_index, f"weight-load-{address}")

    await FallingEdge(dut.clk)
    dut.weight_we.value = 0


async def load_inputs(dut, values, design: str, vector_index: int) -> None:
    for address, value in enumerate(values):
        await FallingEdge(dut.clk)
        dut.input_we.value = 1
        dut.input_addr.value = address
        dut.input_data.value = twos_complement(int(value), 8)
        await RisingEdge(dut.clk)
        await ReadOnly()
        assert_done(dut, 0, design, vector_index, f"input-load-{address}")

    # Give the final input write its own cycle; start is deliberately still low.
    await FallingEdge(dut.clk)
    dut.input_we.value = 0
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert_done(dut, 0, design, vector_index, "pre-start-idle")


async def pulse_start_and_check_done(dut, design: str, vector_index: int) -> None:
    await FallingEdge(dut.clk)
    dut.start.value = 1
    await Timer(1, unit="ns")
    await ReadOnly()
    assert_done(dut, 0, design, vector_index, "before-start-edge")

    await RisingEdge(dut.clk)
    await ReadOnly()
    assert_done(dut, 1, design, vector_index, "start-capture")

    await FallingEdge(dut.clk)
    dut.start.value = 0
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert_done(dut, 0, design, vector_index, "one-cycle-after-start")


async def check_outputs(dut, expected_values, design: str, vector_index: int) -> None:
    for output_index, expected in enumerate(expected_values):
        await FallingEdge(dut.clk)
        dut.output_addr.value = output_index
        await Timer(1, unit="ns")
        await ReadOnly()
        observed = signed_value(dut.output_data, ACC_WIDTH)
        expected_int = int(expected)
        assert observed == expected_int, (
            f"design={design} vector={vector_index} output={output_index} "
            f"expected={expected_int} observed={observed}"
        )


async def run_matvec_suite(dut, *, design: str, has_runtime_weights: bool) -> None:
    weights = np.load(MODELS / "weights.npy")
    inputs = np.load(MODELS / "inputs.npy")
    expected = np.load(MODELS / "expected_outputs.npy")

    assert weights.shape == (ROWS, COLS)
    assert inputs.shape == (32, COLS)
    assert expected.shape == (32, ROWS)
    assert_interface_widths(dut, has_runtime_weights=has_runtime_weights)

    dut.clk.value = 0
    dut.rst_n.value = 0
    dut.start.value = 0
    dut.input_we.value = 0
    dut.input_addr.value = 0
    dut.input_data.value = 0
    dut.output_addr.value = 0
    if has_runtime_weights:
        dut.weight_we.value = 0
        dut.weight_addr.value = 0
        dut.weight_data.value = 0

    cocotb.start_soon(Clock(dut.clk, CLOCK_PERIOD_NS, unit="ns").start())

    for vector_index, input_values in enumerate(inputs):
        await reset_dut(dut, design, vector_index)
        if has_runtime_weights:
            await load_runtime_weights(dut, weights, design, vector_index)
        await load_inputs(dut, input_values, design, vector_index)
        await pulse_start_and_check_done(dut, design, vector_index)
        await check_outputs(dut, expected[vector_index], design, vector_index)

    dut._log.info("%s: %d/%d vectors passed", design, len(inputs), len(inputs))

