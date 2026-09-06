"""Register-level tests for the AWS F2 AXI-Lite portability wrapper."""

import os

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, RisingEdge
import numpy as np

from common import ACC_WIDTH, ROWS, MODELS


def signed24(raw: int) -> int:
    raw &= (1 << ACC_WIDTH) - 1
    return raw - (1 << ACC_WIDTH) if raw & (1 << (ACC_WIDTH - 1)) else raw


async def axil_write(dut, addr: int, data: int) -> None:
    dut.s_axi_awaddr.value = addr
    dut.s_axi_awvalid.value = 1
    dut.s_axi_wdata.value = data & 0xFFFFFFFF
    dut.s_axi_wstrb.value = 0xF
    dut.s_axi_wvalid.value = 1
    while True:
        await RisingEdge(dut.clk)
        if int(dut.s_axi_awready.value) and int(dut.s_axi_wready.value):
            break
    dut.s_axi_awvalid.value = 0
    dut.s_axi_wvalid.value = 0
    while not int(dut.s_axi_bvalid.value):
        await RisingEdge(dut.clk)
    dut.s_axi_bready.value = 1
    await RisingEdge(dut.clk)
    dut.s_axi_bready.value = 0


async def axil_read(dut, addr: int) -> int:
    dut.s_axi_araddr.value = addr
    dut.s_axi_arvalid.value = 1
    while True:
        await RisingEdge(dut.clk)
        if int(dut.s_axi_arready.value):
            break
    dut.s_axi_arvalid.value = 0
    while not int(dut.s_axi_rvalid.value):
        await RisingEdge(dut.clk)
    value = int(dut.s_axi_rdata.value)
    dut.s_axi_rready.value = 1
    await RisingEdge(dut.clk)
    dut.s_axi_rready.value = 0
    return value


@cocotb.test()
async def verify_f2_register_wrapper(dut):
    design = os.environ.get("F2_DESIGN", "generic")
    fixed = design == "fixed"
    inputs = np.load(MODELS / "inputs.npy")
    weights = np.load(MODELS / "weights.npy")
    expected_outputs = np.load(MODELS / "expected_outputs.npy")
    flat_weights = weights.ravel(order="C")

    for signal in (
        dut.s_axi_awvalid,
        dut.s_axi_wvalid,
        dut.s_axi_bready,
        dut.s_axi_arvalid,
        dut.s_axi_rready,
    ):
        signal.value = 0
    dut.s_axi_awaddr.value = 0
    dut.s_axi_wdata.value = 0
    dut.s_axi_wstrb.value = 0
    dut.s_axi_araddr.value = 0

    cocotb.start_soon(Clock(dut.clk, 4, unit="ns").start())
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 3)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 2)

    assert await axil_read(dut, 0x124) == 0, f"design={design} done set after reset"

    for vector_index in range(len(inputs)):
        if not fixed:
            for weight_index, value in enumerate(flat_weights):
                await axil_write(dut, weight_index * 4, int(value) & 0xFF)
        for input_index, value in enumerate(inputs[vector_index]):
            await axil_write(dut, 0x100 + input_index * 4, int(value) & 0xFF)

        await ClockCycles(dut.clk, 1)
        await axil_write(dut, 0x120, 0x3)  # start and clear stale done
        await ClockCycles(dut.clk, 2)

        for _ in range(8):
            status = await axil_read(dut, 0x124)
            if status & 1:
                break
        else:
            raise AssertionError(f"design={design} vector={vector_index} no done")

        for output_index in range(ROWS):
            observed = signed24(await axil_read(dut, 0x200 + output_index * 4))
            expected = int(expected_outputs[vector_index, output_index])
            assert observed == expected, (
                f"design={design} vector={vector_index} output={output_index} "
                f"expected={expected} observed={observed}"
            )

        assert (await axil_read(dut, 0x124)) & 1
        await axil_write(dut, 0x120, 0x2)
        assert (await axil_read(dut, 0x124)) & 1 == 0
