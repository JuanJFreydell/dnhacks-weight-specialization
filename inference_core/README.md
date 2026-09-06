# Fixed-weight MoE inference-core ASIC candidate

This experiment scales the verified 8x8 matrix baseline into a complete
single-token, Top-1 routed ReGLU mixture-of-experts inference block:

```text
INT8 token
  -> four-way INT4 router
  -> selected expert: INT4 up projection + INT4 gate projection
  -> ReGLU: up * ReLU(gate), arithmetic right shift by six
  -> INT4 down projection + residual token
  -> signed INT24 output token
```

The deterministic default has four experts, model width 16, hidden width 64,
and 12,352 INT4 weights. It executes 3,136 active MACs per token: 64 router
MACs plus 3 x 16 x 64 MACs in the selected expert. The complete model stores
49,408 weight bits (6,176 bytes before SRAM banking and metadata).

## Paired architectures

`rtl/generic_moe_expert.sv` is the runtime-programmable reference. It writes
weights as 580 packed words into four independently readable, synchronous
one-read/one-write SRAM regions: router, up, gate, and down. The behavioral
`weight_sram_1rw.sv` module has no reset and the same clocked port semantics
as the ASIC SRAM abstraction that will replace it during physical design.

`rtl/fixed_moe_expert.sv` has the same model dimensions, input/output protocol,
integer arithmetic, and token buffering. Its coefficients are emitted by
`scripts/generate_fixed_rtl.py` into `rtl/generated/fixed_moe_words.svh` as
compile-time constants. It does not include writable weight storage or SRAM
read phases.

The fixed design therefore has a shorter control schedule by construction:
it computes one hidden unit per cycle and one output per cycle, while the
generic design spends an issue and consume cycle for every synchronous SRAM
word. This is a valid system-level specialization tradeoff, but it is **not**
an iso-latency causal comparison. A future fixed design that retains identical
SRAM-style issue cycles will isolate constant arithmetic separately.

## Reproducible commands

From the repository root:

```bash
make generate-expert
make test-expert-generic
make test-expert-fixed
make test-expert
```

The cocotb suites load the generated NumPy arrays relative to the repository
root, program all generic SRAM words once after reset, execute all 16 inputs,
check each selected route and each of 16 signed INT24 outputs, and check that
`done` is a one-cycle pulse. JUnit results are written to
`reports/inference_core/`.

## ASIC status

This is an RTL and verification candidate, not fabricated silicon. The generic
memory model is deliberately isolated behind a macro-like interface so it can
be replaced by characterized SRAM macros for ASIC synthesis. Until that macro
substitution and post-layout signoff run, no area, power, or silicon-performance
claim is valid.
