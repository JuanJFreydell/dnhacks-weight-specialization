import cocotb

from common import run_suite


@cocotb.test()
async def verify_fixed_moe_expert(dut):
    await run_suite(dut, "fixed")
