#!/usr/bin/env python3
"""Build and run one cocotb suite without path-sensitive Makefile includes."""

import argparse
import os
from pathlib import Path
from xml.etree import ElementTree

from cocotb_tools.runner import get_runner


ROOT = Path(__file__).resolve().parents[1]
DESIGNS = {
    "generic": ("generic_matvec", ROOT / "rtl" / "generic_matvec.sv"),
    "fixed": ("fixed_matvec", ROOT / "rtl" / "generated" / "fixed_matvec.sv"),
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("design", choices=DESIGNS)
    parser.add_argument("--sim", default="icarus")
    parser.add_argument("--waves", action="store_true")
    args = parser.parse_args()

    top, source = DESIGNS[args.design]
    build_dir = ROOT / "sim_build" / args.design
    tests_dir = ROOT / "tests"
    pythonpath = os.pathsep.join(
        entry for entry in (str(tests_dir), os.environ.get("PYTHONPATH", "")) if entry
    )

    runner = get_runner(args.sim)
    runner.build(
        sources=[source],
        hdl_toplevel=top,
        build_args=["-g2012"] if args.sim == "icarus" else [],
        build_dir=build_dir,
        always=True,
        timescale=("1ns", "1ps"),
        waves=args.waves,
    )
    results_path = runner.test(
        test_module=f"test_{args.design}",
        hdl_toplevel=top,
        hdl_toplevel_lang="verilog",
        build_dir=build_dir,
        test_dir=ROOT,
        results_xml=str(ROOT / f"results-{args.design}.xml"),
        extra_env={"PYTHONPATH": pythonpath},
        waves=args.waves,
    )

    suites = ElementTree.parse(results_path).getroot().findall("testsuite")
    failures = sum(int(suite.get("failures", "0")) for suite in suites)
    errors = sum(int(suite.get("errors", "0")) for suite in suites)
    if failures or errors:
        raise SystemExit(
            f"cocotb reported {failures} failure(s) and {errors} error(s)"
        )


if __name__ == "__main__":
    main()
