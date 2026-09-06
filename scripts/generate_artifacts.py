#!/usr/bin/env python3
"""Generate deterministic experiment data and trusted NumPy outputs."""

from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = ROOT / "models"
SEED = 5510
ROWS = 8
COLS = 8
TEST_VECTORS = 32
LOW = -8
HIGH_EXCLUSIVE = 8


def int8_hex(value: int) -> str:
    return f"{value & 0xFF:02x}"


def main() -> None:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)

    weights = rng.integers(LOW, HIGH_EXCLUSIVE, size=(ROWS, COLS), dtype=np.int8)
    inputs = rng.integers(
        LOW, HIGH_EXCLUSIVE, size=(TEST_VECTORS, COLS), dtype=np.int8
    )
    expected = inputs.astype(np.int32) @ weights.astype(np.int32).T

    np.save(MODEL_DIR / "weights.npy", weights)
    np.save(MODEL_DIR / "inputs.npy", inputs)
    np.save(MODEL_DIR / "expected_outputs.npy", expected)

    np.savetxt(MODEL_DIR / "weights.csv", weights, fmt="%d", delimiter=",")
    np.savetxt(MODEL_DIR / "inputs.csv", inputs, fmt="%d", delimiter=",")
    np.savetxt(
        MODEL_DIR / "expected_outputs.csv", expected, fmt="%d", delimiter=","
    )

    (MODEL_DIR / "weights.mem").write_text(
        "\n".join(int8_hex(int(v)) for v in weights.ravel()) + "\n"
    )
    (MODEL_DIR / "inputs.mem").write_text(
        "\n".join(int8_hex(int(v)) for v in inputs.ravel()) + "\n"
    )

    print(f"Generated {ROWS}x{COLS} weights and {TEST_VECTORS} test vectors")
    print(f"Artifacts: {MODEL_DIR}")


if __name__ == "__main__":
    main()
