#!/usr/bin/env python3
"""Emit fixed-weight SystemVerilog word functions for the MoE expert core."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
CORE = ROOT / "inference_core"
MODELS = CORE / "models"
OUTPUT = CORE / "rtl" / "generated" / "fixed_moe_words.svh"


def pack_int4(values: np.ndarray) -> int:
    packed = 0
    for index, value in enumerate(values.ravel()):
        packed |= (int(value) & 0xF) << (4 * index)
    return packed


def word_function(name: str, width: int, words: list[int]) -> list[str]:
    lines = [
        f"function automatic logic [{width - 1}:0] {name}(input integer address);",
        "    begin",
        "        case (address)",
    ]
    hex_width = width // 4
    for address, word in enumerate(words):
        lines.append(f"            {address}: {name} = {width}'h{word:0{hex_width}x};")
    lines.extend(
        [
            f"            default: {name} = '0;",
            "        endcase",
            "    end",
            "endfunction",
            "",
        ]
    )
    return lines


def main() -> None:
    spec = json.loads((CORE / "spec.json").read_text())
    width = int(spec["model_width"])
    hidden = int(spec["hidden_width"])
    router = np.load(MODELS / "router_weights.npy")
    up = np.load(MODELS / "up_weights.npy")
    gate = np.load(MODELS / "gate_weights.npy")
    down = np.load(MODELS / "down_weights.npy")
    if router.shape[1] != width or up.shape[1:] != (hidden, width):
        raise SystemExit("Generated weights do not match inference_core/spec.json")

    router_words = [pack_int4(row) for row in router]
    up_words = [pack_int4(row) for expert in up for row in expert]
    gate_words = [pack_int4(row) for expert in gate for row in expert]
    down_words = [pack_int4(row) for expert in down for row in expert]
    lines = [
        "// Generated file: do not hand-edit.",
        "// Fixed INT4 model coefficients packed least-significant coefficient first.",
        "",
    ]
    lines.extend(word_function("fixed_router_word", width * 4, router_words))
    lines.extend(word_function("fixed_up_word", width * 4, up_words))
    lines.extend(word_function("fixed_gate_word", width * 4, gate_words))
    lines.extend(word_function("fixed_down_word", hidden * 4, down_words))
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines))
    print(f"Generated fixed coefficient functions: {OUTPUT}")


if __name__ == "__main__":
    main()
