"""Cocotb wrapper for the compile-time-fixed matvec."""

import cocotb

from common import run_matvec_suite


@cocotb.test()
async def verify_fixed_matvec(dut):
    await run_matvec_suite(
        dut,
        design="fixed_matvec",
        has_runtime_weights=False,
    )

