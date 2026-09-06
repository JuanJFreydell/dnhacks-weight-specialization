# FPGA Weight-Specialization Experiment

## Project purpose

This repository is the first experimental slice of a broader DN Hacks idea:

> Determine whether fixing a neural network's trained weights at hardware-design
> time can create materially smaller, faster, or more energy-efficient inference
> circuits than hardware that must accept arbitrary weights at runtime.

The long-term product concept is an AI-assisted model-to-hardware environment:
something like a hardware-focused Cursor that accepts a frozen model and design
objective, generates candidate accelerator architectures, verifies them, runs
synthesis, and explains the performance/area/power tradeoffs. It should build on
existing compilers and EDA tools rather than attempting to replace TensorFlow,
PyTorch, synthesis, verification, or physical-design software.

The immediate goal is intentionally narrower. We first need a controlled physical
experiment establishing whether weight specialization produces measurable hardware
differences at all.

## Experimental question

Both circuits compute the same signed integer matrix-vector multiplication:

```text
y = W x
```

The experiment compares:

1. **Generic circuit:** `W` is stored in writable registers and loaded at runtime.
2. **Fixed circuit:** the exact values in `W` are emitted as SystemVerilog constants
   before synthesis.

The default problem is an `8 x 8` signed INT8 matrix multiplied by an eight-element
signed INT8 vector. Accumulation uses 24 bits. There are 64 multiplications exposed
in parallel in both designs. This keeps the intended independent variable narrow:

```text
runtime-programmable weights  vs.  compile-time-fixed weights
```

This same-FPGA comparison is the causal experiment. PyTorch/CUDA can later be added
as a practical external reference, but it is not an apples-to-apples measurement of
specialization because a GPU and FPGA differ in process, clock, memory, scale, and
software stack.

## Current repository

```text
fpga-specialization/
├── .gitignore
├── AGENTS.md
├── README.md
├── Makefile
├── requirements-dev.txt
├── specs/
│   └── experiment.yaml
├── models/
│   ├── weights.npy
│   ├── weights.csv
│   ├── weights.mem
│   ├── inputs.npy
│   ├── inputs.csv
│   ├── inputs.mem
│   ├── expected_outputs.npy
│   └── expected_outputs.csv
├── scripts/
│   ├── generate_artifacts.py
│   └── generate_fixed_rtl.py
├── tests/
│   ├── common.py
│   ├── run.py
│   ├── test_fixed.py
│   └── test_generic.py
└── rtl/
    ├── generic_matvec.sv
    └── generated/
        └── fixed_matvec.sv
```

## Completed build targets: steps 1–4

### 1. Experiment specification

`specs/experiment.yaml` records the operation, dimensions, precision, random seed,
input range, accumulator width, test-vector count, and comparison controls.

| Property | Value |
|---|---:|
| Operation | Matrix-vector multiplication |
| Matrix | 8 x 8 |
| Input/weight type | Signed INT8 |
| Accumulator | Signed 24-bit |
| Test vectors | 32 |
| Random seed | 5510 |
| Generated value range | -8 through 7 |
| Parallel multiplications | 64 in each circuit |

### 2. Golden software reference

`scripts/generate_artifacts.py` deterministically generates the fixed matrix, 32
input vectors, trusted NumPy results, readable CSV files, NumPy binary files, and
flat two's-complement hexadecimal `.mem` files.

```bash
python3 scripts/generate_artifacts.py
```

### 3. Generic RTL

`rtl/generic_matvec.sv` contains 64 writable signed INT8 weight registers, eight
input registers, eight parallel dot-product datapaths, runtime loading interfaces,
a `start`/`done` interface, and indexed output reading. A different matrix can be
used without resynthesizing the circuit.

### 4. Fixed-weight RTL

`scripts/generate_fixed_rtl.py` reads `models/weights.npy` and emits
`rtl/generated/fixed_matvec.sv`. The generated circuit has the same arithmetic and
parallelism, but no writable weight array. Every coefficient is visible to synthesis
as an RTL constant.

```bash
python3 scripts/generate_fixed_rtl.py
```

Changing `W` requires regenerating and resynthesizing this circuit. That simulates
the loss of flexibility in a model-specific ASIC while an FPGA lets us test the
idea without fabricating silicon.

## Circuit interfaces

The generic circuit first receives 64 row-major weights using
`weight_we`, `weight_addr`, and `weight_data`. Both circuits receive eight input
elements using `input_we`, `input_addr`, and `input_data`.

After inputs are loaded, a one-cycle `start` pulse captures all eight dot-product
results. `done` pulses for one cycle. Select each result using `output_addr` and read
`output_data`.

## Current status: step 5 verified locally

On 2026-09-05, both designs were compiled and executed on the local Apple Silicon
Mac with Icarus Verilog 13.0, cocotb 2.1.0, Python 3.14.4, and NumPy 2.5.2.
The deterministic artifact regeneration check produced no changes.

Measured verification result:

```text
generic_matvec: 32/32 vectors passed (256/256 output comparisons)
fixed_matvec:   32/32 vectors passed (256/256 output comparisons)
generic == fixed == NumPy
```

Each vector is tested after reset. The testbench checks reset initialization,
runtime weights in row-major order, signed INT8 stimulus encoding, signed 24-bit
result decoding, an idle cycle between the final input write and `start`, and the
exact one-cycle `done` pulse. Icarus accepted the generated negative constant
syntax. Requested waveform runs produce FST files for both designs under
`sim_build/`.

Commands executed successfully:

```bash
make generate
make test-generic
make test-fixed
make test
make waves
```

Functional correctness is now verified for the 32 deterministic vectors. No area,
timing, power, or efficiency advantage has been established; those remain step 6.

## F2 pivot status

The experiment now has an AWS F2 portability layer in addition to the original
core tests. `rtl/aws_f2_matvec_axi.sv` exposes both cores through a 32-bit
AXI-Lite register map; `aws_f2/host/matvec_host.c` is the corresponding AWS FPGA
SDK driver. The wrapper preserves the original signed INT8 arithmetic, 24-bit
accumulators, 64 parallel products, and generic-versus-fixed distinction.

The local host-style wrapper test passes for both variants:

```text
make test-f2-generic: PASS, 32/32 vectors, 256/256 outputs
make test-f2-fixed:   PASS, 32/32 vectors, 256/256 outputs
```

The AWS F2 template and shell connection are under `aws_f2/template/`. The
Marketplace Developer AMI subscription is active, and the AWS HDK smoke test
passes on the `c7i.4xlarge` Ubuntu 24.04 build host with Vivado 2025.2. The
vendor flow targets the F2 VU47P part `xcvu47p-fsvh2892-2-e`, `clk_main_a0` at
4.000 ns, `small_shell`, and the default `SSI_SpreadLogic_high` /
`AggressiveExplore` directives.

Preliminary F2 shell-integrated results (same wrapper and settings) are now
available from routed Vivado reports:

```text
                     generic       fixed       fixed vs generic
CL CARRY8 cells           672         131             -80.5%
CL LUT primitives       6,899       1,269             -81.6%
CL flip-flops            1,388         821             -40.9%
post-route WNS        -0.841 ns    +0.036 ns          timing met
post-route TNS       -79.418 ns     0.000 ns
```

These are CL-level out-of-context resource counts plus full-shell routed timing;
they are not FPGA-board measurements. The generic routed checkpoint is marked
`VIOLATED`, while the fixed checkpoint is routed with timing met. The AWS F2
Service Quotas request for 24 F vCPUs in `us-east-1` remains open
(`CASE_OPENED`), so AFI creation and execution on a physical F2 instance are
still pending quota approval.

## Inference-core ASIC candidates

Alongside the controlled 8x8 matrix experiment, `inference_core/` now contains
a concrete small inference primitive: a single-token, Top-1 routed ReGLU MoE
block with four experts, width 16, hidden width 64, INT8 activations, INT4
weights, signed INT24 outputs, and 3,136 active MACs per token. The fixed core
emits the trained coefficients as RTL constants. Its matched programmable
counterpart keeps the same math and I/O interface but programs coefficients at
runtime into seven characterized Sky130 OpenRAM macros (7,296 physical bytes
for 6,176 logical coefficient bytes due to available macro shapes).

All three functional views are reproducible and have stored JUnit output under
`reports/inference_core/`:

```bash
make generate-expert
make test-expert-generic
make test-expert-generic-sram
make test-expert-fixed
```

The ASIC build recipes use the same Sky130HD standard-cell platform and 20 ns
constraint for both candidates:

```bash
make asic-fixed
make asic-generic-sram
```

Only post-flow reports stored in `reports/inference_core/openroad/` should be
used for ASIC estimates. They are open-source physical-design estimates, not
fabricated-silicon measurements or foundry signoff.

## Step 5: functional verification

Use a shared cocotb verification strategy. For each of the 32 input vectors:

1. Reset the design.
2. Load the 64 weights into the generic circuit only.
3. Load the eight input elements into both circuits.
4. Pulse `start` for one clock.
5. Confirm the expected `done` behavior.
6. Read all eight signed outputs.
7. Compare every result exactly with `models/expected_outputs.npy`.

The required proof is:

```text
generic RTL(W, x) == fixed RTL(x) == NumPy(W, x)
```

The verification implementation is:

```text
tests/common.py
tests/run.py
tests/test_generic.py
tests/test_fixed.py
Makefile
requirements-dev.txt
```

The Makefile should expose:

```bash
make generate
make test-generic
make test-fixed
make test
make waves
```

Local macOS setup:

```bash
brew install icarus-verilog gtkwave
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install cocotb numpy pytest
make test
```

Verilator is also acceptable. Start with Icarus because installation and cocotb
integration are simpler. Generate `.fst` or `.vcd` waveforms for GTKWave.

Verified success summary:

```text
generic_matvec: 32/32 vectors passed
fixed_matvec:   32/32 vectors passed
generic == fixed == NumPy
```

When diagnosing failures, report the design, vector index, output index, expected
signed integer, and observed signed integer.

## Step 6: synthesis and comparison

After verification, synthesize both designs for the **same FPGA part**, using the
same tool version, clock constraint, I/O assumptions, and synthesis settings.

| Metric | Generic | Fixed |
|---|---:|---:|
| LUTs | measured | measured |
| Flip-flops | measured | measured |
| DSP blocks | measured | measured |
| BRAM | measured | measured |
| Worst slack | measured | measured |
| Maximum achievable clock | derived | derived |
| Cycles per operation | measured | measured |
| Throughput | derived | derived |
| Estimated power | estimated | estimated |
| Estimated energy/operation | derived | derived |

HLS/RTL synthesis may map constant arithmetic to DSP blocks instead of optimizing
it into shifts/adds/LUTs. A null result is scientifically meaningful. Inspect the
netlists and reports before interpreting it. Do not tune only the fixed circuit;
architectural or pipeline changes must be applied symmetrically unless explicitly
classified as a new experiment.

## AWS execution plan

The user's normal Codex environment runs locally on a Mac and has previously used
an authenticated root SSH session to an AWS machine. The originating cloud workspace
could not see that local SSH configuration.

As of 2026-09-05, the local AWS CLI `default` profile is authenticated in
`us-east-1`. The only running instance found there is `rendi-internal-mcp`, an
SSM-managed `t3.micro` with 1 GiB RAM and an 8 GiB root volume; it belongs to a
separate workload and has not been modified or used for this experiment. No EC2
host alias is currently present in `~/.ssh/config`; only GitHub is configured there.

Step 5 is small enough to run locally. If the Mac is already connected to an Ubuntu
EC2 host, verification can instead run there after installing:

```bash
sudo apt update
sudo apt install -y git make python3 python3-venv iverilog
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install cocotb numpy pytest
make test
```

For step 6, an x86 Ubuntu EC2 machine is useful because Vivado does not run natively
on macOS. A normal EC2 CPU instance is sufficient for synthesis; AWS F1 is unnecessary
unless the project later targets deployment on an AWS FPGA. Stop or resize billable
instances when they are no longer needed.

Do not copy private SSH keys into the repository or chat. Reuse the user's existing
local SSH configuration and authentication.

## Interpretation boundaries

A successful small FPGA experiment demonstrates that synthesis can exploit fixed
weights under a controlled design. It does not directly prove that a model-specific
ASIC beats a modern GPU or that the gain survives at MoE scale.

Later analysis must separately model:

```text
total inference cost =
    compute
  + weight movement
  + activation movement
  + inter-chip communication
  + control/routing
```

The FPGA provides evidence about local compute, storage, and weight movement. Scaling
to an MoE requires adding routing, expert partitioning, memory hierarchy, utilization,
and communication costs.

## Intended roadmap

1. Verify both matrix-vector circuits.
2. Synthesize both under controlled conditions.
3. Explain netlist and resource differences.
4. Sweep dimensions, weight distributions, sparsity, precision, and architecture.
5. Chain two fixed matrix operations and an activation into a tiny MoE expert.
6. Model whether local benefits survive realistic MoE partitioning.
7. Wrap the deterministic generation/verification/synthesis loop in a natural-language
   design interface.

The LLM should orchestrate templates, constraints, tests, simulation, and synthesis.
The simulator and synthesis tools—not the LLM—remain the sources of truth.
