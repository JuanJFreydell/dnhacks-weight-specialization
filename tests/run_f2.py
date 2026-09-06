#!/usr/bin/env python3
"""Build and run the local AXI-Lite wrapper for generic or fixed weights."""

import argparse
import os
from pathlib import Path
from xml.etree import ElementTree

from cocotb_tools.runner import get_runner


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("design", choices=("generic", "fixed"))
    parser.add_argument("--sim", default="icarus")
    args = parser.parse_args()

    top = "dnhacks_matvec_axi"
    wrapper = ROOT / "rtl" / "aws_f2_matvec_axi.sv"
    core = (ROOT / "rtl" / "generated" / "fixed_matvec.sv") if args.design == "fixed" else (ROOT / "rtl" / "generic_matvec.sv")
    build_dir = ROOT / "sim_build" / f"f2-{args.design}"
    tests_dir = ROOT / "tests"
    pythonpath = os.pathsep.join(
        entry for entry in (str(tests_dir), os.environ.get("PYTHONPATH", "")) if entry
    )

    runner = get_runner(args.sim)
    runner.build(
        sources=[wrapper, core],
        hdl_toplevel=top,
        build_args=["-g2012", f"-P{top}.FIXED_WEIGHTS={int(args.design == 'fixed')}"] if args.sim == "icarus" else [],
        build_dir=build_dir,
        always=True,
        timescale=("1ns", "1ps"),
    )
    result = runner.test(
        test_module="test_f2_wrapper",
        hdl_toplevel=top,
        hdl_toplevel_lang="verilog",
        build_dir=build_dir,
        test_dir=ROOT,
        results_xml=str(ROOT / f"results-f2-{args.design}.xml"),
        extra_env={"PYTHONPATH": pythonpath, "F2_DESIGN": args.design},
    )
    root = ElementTree.parse(result).getroot()
    failures = sum(int(s.get("failures", "0")) for s in root.findall("testsuite"))
    errors = sum(int(s.get("errors", "0")) for s in root.findall("testsuite"))
    if failures or errors:
        raise SystemExit(f"cocotb reported {failures} failure(s) and {errors} error(s)")


if __name__ == "__main__":
    main()
