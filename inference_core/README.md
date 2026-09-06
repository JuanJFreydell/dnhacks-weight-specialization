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

`rtl/weight_sram_sky130_1rw.sv` is the realistic programmable ASIC binding.
It retains the generic core's external programming interface and synchronous
read behavior, but replaces the behavioral arrays with seven characterized
Sky130 OpenRAM macros: one 80x64 router macro, two 64x256 projection macros,
and four 80x64 banks for the 256-bit down-projection words. This is 7,296
bytes of physical SRAM capacity for the 6,176-byte logical model. The separate
`sky130_sram_sim.sv` model is used only for functional verification; physical
flows use blackbox declarations plus the macro LEF, Liberty, and GDS views.

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
make test-expert-generic-sram
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
model is deliberately isolated behind a macro-like interface, and the
`generic-sram` cocotb target verifies the actual macro-bank binding against the
same golden vectors. Physical results are produced reproducibly with:

```bash
make asic-fixed
make asic-generic-sram
```

These use OpenROAD Flow Scripts, SKY130HD standard cells, a 10 ns target, and
the public macro views referenced by `openroad/generic-sram-macro/config.mk`.
They are open-source P&R estimates, not foundry signoff, fabricated-silicon
measurements, or power claims. Results and flow logs are retained beneath
`reports/inference_core/openroad/`.
