#!/usr/bin/env python3
"""Generate deterministic INT4 MoE-expert weights, inputs, and golden outputs."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
CORE = ROOT / "inference_core"
SPEC = json.loads((CORE / "spec.json").read_text())
MODELS = CORE / "models"


def sat_signed(value: int, width: int) -> int:
    minimum = -(1 << (width - 1))
    maximum = (1 << (width - 1)) - 1
    return min(max(value, minimum), maximum)


def model_outputs(
    router: np.ndarray,
    up: np.ndarray,
    gate: np.ndarray,
    down: np.ndarray,
    inputs: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Reference Top-1 ReGLU expert inference with explicit integer arithmetic."""
    shift = int(SPEC["activation_shift"])
    acc_width = int(SPEC["accumulator_bits"])
    outputs = np.zeros((len(inputs), int(SPEC["model_width"])), dtype=np.int32)
    routes = np.zeros(len(inputs), dtype=np.int8)
    for vector_index, vector in enumerate(inputs):
        scores = router.astype(np.int64) @ vector.astype(np.int64)
        expert = int(np.argmax(scores))
        routes[vector_index] = expert
        up_values = up[expert].astype(np.int64) @ vector.astype(np.int64)
        gate_values = gate[expert].astype(np.int64) @ vector.astype(np.int64)
        hidden = (up_values * np.maximum(gate_values, 0)) >> shift
        raw_output = down[expert].astype(np.int64) @ hidden + vector.astype(np.int64)
        outputs[vector_index] = np.array(
            [sat_signed(int(value), acc_width) for value in raw_output], dtype=np.int32
        )
    return outputs, routes


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    MODELS.mkdir(parents=True, exist_ok=True)
    experts = int(SPEC["experts"])
    width = int(SPEC["model_width"])
    hidden = int(SPEC["hidden_width"])
    vectors = int(SPEC["test_vectors"])
    rng = np.random.default_rng(int(SPEC["seed"]))
    low = int(SPEC["weight_minimum"])
    high = int(SPEC["weight_maximum"]) + 1

    router = rng.integers(low, high, size=(experts, width), dtype=np.int8)
    up = rng.integers(low, high, size=(experts, hidden, width), dtype=np.int8)
    gate = rng.integers(low, high, size=(experts, hidden, width), dtype=np.int8)
    down = rng.integers(low, high, size=(experts, width, hidden), dtype=np.int8)
    input_low = int(SPEC["input_minimum"])
    input_high = int(SPEC["input_maximum"]) + 1
    inputs = rng.integers(input_low, input_high, size=(vectors, width), dtype=np.int8)
    expected, routes = model_outputs(router, up, gate, down, inputs)

    arrays = {
        "router_weights.npy": router,
        "up_weights.npy": up,
        "gate_weights.npy": gate,
        "down_weights.npy": down,
        "inputs.npy": inputs,
        "expected_outputs.npy": expected,
        "expected_routes.npy": routes,
    }
    for name, array in arrays.items():
        np.save(MODELS / name, array)

    np.savetxt(MODELS / "inputs.csv", inputs, fmt="%d", delimiter=",")
    np.savetxt(MODELS / "expected_outputs.csv", expected, fmt="%d", delimiter=",")
    np.savetxt(MODELS / "expected_routes.csv", routes, fmt="%d", delimiter=",")

    weight_count = router.size + up.size + gate.size + down.size
    manifest = {
        "spec": SPEC,
        "weight_count": int(weight_count),
        "active_macs_per_token": int(experts * width + 3 * width * hidden),
        "all_model_weight_bits": int(weight_count * SPEC["weight_bits"]),
        "files": {name: sha256(MODELS / name) for name in arrays},
    }
    (MODELS / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(
        f"Generated {experts}-expert ReGLU core: {weight_count} INT4 weights, "
        f"{vectors} vectors"
    )


if __name__ == "__main__":
    main()
