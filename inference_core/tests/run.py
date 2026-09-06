#!/usr/bin/env python3
"""Build and run one paired MoE-expert cocotb suite."""

import argparse
import os
from pathlib import Path
from xml.etree import ElementTree

from cocotb_tools.runner import get_runner


ROOT = Path(__file__).resolve().parents[2]
CORE = ROOT / "inference_core"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("design", choices=("generic", "generic-sram", "fixed"))
    parser.add_argument("--sim", default="icarus")
    parser.add_argument("--waves", action="store_true")
    args = parser.parse_args()

    if args.design == "generic":
        top = "generic_moe_expert"
        sources = [CORE / "rtl" / "weight_sram_1rw.sv", CORE / "rtl" / "generic_moe_expert.sv"]
        test_module = "test_generic"
    elif args.design == "generic-sram":
        top = "generic_moe_expert"
        sources = [
            CORE / "rtl" / "sky130_sram_sim.sv",
            CORE / "rtl" / "weight_sram_sky130_1rw.sv",
            CORE / "rtl" / "generic_moe_expert.sv",
        ]
        test_module = "test_generic_sram"
    else:
        top = "fixed_moe_expert"
        sources = [CORE / "rtl" / "fixed_moe_expert.sv"]
        test_module = "test_fixed"
    build_dir = ROOT / "sim_build" / f"expert-{args.design}"
    reports_dir = ROOT / "reports" / "inference_core"
    reports_dir.mkdir(parents=True, exist_ok=True)
    test_path = str(CORE / "tests")
    pythonpath = os.pathsep.join(
        entry for entry in (test_path, os.environ.get("PYTHONPATH", "")) if entry
    )
    runner = get_runner(args.sim)
    runner.build(
        sources=sources,
        hdl_toplevel=top,
        build_args=["-g2012"] if args.sim == "icarus" else [],
        includes=[ROOT],
        build_dir=build_dir,
        always=True,
        timescale=("1ns", "1ps"),
        waves=args.waves,
    )
    results = runner.test(
        test_module=test_module,
        hdl_toplevel=top,
        hdl_toplevel_lang="verilog",
        build_dir=build_dir,
        test_dir=ROOT,
        results_xml=str(reports_dir / f"{args.design}.junit.xml"),
        extra_env={"PYTHONPATH": pythonpath},
        waves=args.waves,
    )
    suites = ElementTree.parse(results).getroot().findall("testsuite")
    failures = sum(int(suite.get("failures", "0")) for suite in suites)
    errors = sum(int(suite.get("errors", "0")) for suite in suites)
    if failures or errors:
        raise SystemExit(f"cocotb reported {failures} failure(s) and {errors} error(s)")


if __name__ == "__main__":
    main()
