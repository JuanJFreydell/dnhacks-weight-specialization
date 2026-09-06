import cocotb

from common import run_suite


@cocotb.test()
async def verify_generic_sky130_sram_moe_expert(dut):
    await run_suite(dut, "generic")
