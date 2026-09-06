"""Cocotb wrapper for the runtime-programmable matvec."""

import cocotb

from common import run_matvec_suite


@cocotb.test()
async def verify_generic_matvec(dut):
    await run_matvec_suite(
        dut,
        design="generic_matvec",
        has_runtime_weights=True,
    )

