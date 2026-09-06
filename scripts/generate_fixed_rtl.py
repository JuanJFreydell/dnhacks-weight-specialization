#!/usr/bin/env python3
"""Generate an unrolled fixed-weight SystemVerilog matrix-vector circuit."""

from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
WEIGHTS_PATH = ROOT / "models" / "weights.npy"
OUTPUT_PATH = ROOT / "rtl" / "generated" / "fixed_matvec.sv"
ACC_WIDTH = 24


def signed_literal(value: int) -> str:
    return f"-8'sd{abs(value)}" if value < 0 else f"8'sd{value}"


def main() -> None:
    if not WEIGHTS_PATH.exists():
        raise SystemExit("Run scripts/generate_artifacts.py first")

    weights = np.load(WEIGHTS_PATH)
    rows, cols = weights.shape
    lines = [
        "// Generated file: do not hand-edit.",
        "// Every W coefficient is a synthesis-time constant.",
        "module fixed_matvec #(",
        f"    parameter int ROWS = {rows},",
        f"    parameter int COLS = {cols},",
        f"    parameter int ACC_WIDTH = {ACC_WIDTH}",
        ") (",
        "    input  logic clk,",
        "    input  logic rst_n,",
        "    input  logic input_we,",
        "    input  logic [$clog2(COLS)-1:0] input_addr,",
        "    input  logic signed [7:0] input_data,",
        "    input  logic start,",
        "    input  logic [$clog2(ROWS)-1:0] output_addr,",
        "    output logic signed [ACC_WIDTH-1:0] output_data,",
        "    output logic done",
        ");",
        "",
        "    logic signed [7:0] x_q [0:COLS-1];",
        "    logic signed [ACC_WIDTH-1:0] y_q [0:ROWS-1];",
        "",
    ]

    for row in range(rows):
        terms = [
            f"($signed({signed_literal(int(weights[row, col]))}) * $signed(x_q[{col}]))"
            for col in range(cols)
        ]
        expression = " +\n                ".join(terms)
        lines.extend(
            [
                f"    wire signed [ACC_WIDTH-1:0] dot_{row} =",
                f"                {expression};",
                "",
            ]
        )

    lines.extend(
        [
            "    integer i;",
            "    always_ff @(posedge clk) begin",
            "        if (!rst_n) begin",
            "            done <= 1'b0;",
            "            for (i = 0; i < COLS; i = i + 1) x_q[i] <= '0;",
            "            for (i = 0; i < ROWS; i = i + 1) y_q[i] <= '0;",
            "        end else begin",
            "            done <= 1'b0;",
            "            if (input_we) x_q[input_addr] <= input_data;",
            "            if (start) begin",
        ]
    )
    for row in range(rows):
        lines.append(f"                y_q[{row}] <= dot_{row};")
    lines.extend(
        [
            "                done <= 1'b1;",
            "            end",
            "        end",
            "    end",
            "",
            "    assign output_data = y_q[output_addr];",
            "endmodule",
            "",
        ]
    )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text("\n".join(lines))
    print(f"Generated fixed circuit: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
