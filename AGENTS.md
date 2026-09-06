# Local Codex instructions

## Mission

Continue the FPGA weight-specialization experiment described in `README.md`. The
immediate task is step 5: implement and execute cocotb verification for both RTL
designs. Proceed to synthesis only after both pass and the FPGA target is known.

## Start-of-session procedure

1. Read this file and `README.md` completely.
2. Inspect the repository and working-tree status before editing.
3. Inspect the environment:

   ```bash
   uname -a
   python3 --version
   command -v iverilog || true
   command -v verilator || true
   command -v aws || true
   git status --short 2>/dev/null || true
   ```

4. On the user's Mac, inspect existing SSH/AWS configuration safely. Never print
   private keys, tokens, secret values, or credential files. Reuse existing auth.
5. Regenerate deterministic artifacts:

   ```bash
   python3 scripts/generate_artifacts.py
   python3 scripts/generate_fixed_rtl.py
   ```

## Experimental invariants

Preserve these unless the user explicitly approves a new experiment:

- Same `y = Wx` operation, matrix, inputs, and expected outputs.
- Signed INT8 inputs and weights with signed 24-bit accumulation.
- Same 64 parallel multiplications in the default 8x8 case.
- Intentional difference: runtime weights versus compile-time constants.
- Same clock and synthesis settings.
- Never compare a sequential generic design with a parallel fixed design and
  attribute the result solely to specialization.

## Immediate implementation requirements

Create:

```text
tests/common.py
tests/test_generic.py
tests/test_fixed.py
Makefile
requirements-dev.txt
```

The tests must:

- Use cocotb clock and reset primitives.
- Load NumPy data relative to the repository root, not the caller's CWD.
- Drive INT8 values as 8-bit two's-complement values.
- Convert output back to a signed 24-bit Python integer.
- Load weights row-major for `generic_matvec`.
- Check `done` timing explicitly.
- Test all 32 vectors and eight outputs against `expected_outputs.npy`.
- Produce assertion messages with design/vector/output indices and values.
- Emit VCD or FST waveforms when requested.

Prefer shared helpers and thin design-specific wrappers over duplicated tests.

## Required commands

The final interface must be:

```bash
make generate
make test-generic
make test-fixed
make test
```

Run every command. Do not report success from inspection alone. Record the simulator
version and complete pass/fail summary.

If Icarus rejects SystemVerilog, determine whether it is a simulator limitation or
RTL defect. Portability edits are allowed only if architecture, parallelism, widths,
latency, and interfaces remain equivalent.

## Arithmetic checks

- Verify sign extension for every multiplication.
- Ensure intermediates are not truncated before 24-bit accumulation.
- Check negative constant syntax in generated RTL.
- Check output timing relative to nonblocking assignments and `done`.
- Check reset initialization and address widths.
- Do not assert `start` in the final input-write cycle unless supported deliberately.

If a defect appears, add a regression test before fixing it. Modify generated fixed
RTL through `scripts/generate_fixed_rtl.py`, never by hand.

## Step 6 synthesis rules

Do not interpret performance until step 5 passes. Identify the exact FPGA board or
part number before vendor synthesis; ask the user rather than guessing for final
claims. Yosys may support exploratory netlist inspection, but vendor timing/resource
claims must come from the vendor tool.

Record FPGA part/board, tool version, synthesis strategy, clock constraint, source
identity, and all resource/timing/power reports. Do not claim LUTs are categorically
better than DSPs. Confirm that constant coefficients were actually optimized and
that incomplete top-level I/O did not let synthesis delete relevant logic.

## AWS and security

- The repository contains no AWS credentials or SSH keys.
- Never ask for private keys, passwords, OTPs, or secret access keys in chat.
- Reuse the user's existing local SSH/AWS authentication.
- Safe identity checks include `aws sts get-caller-identity` and `aws configure list`.
- Creating/resizing EC2 is billable; explain lifecycle and stop unused instances.
- Prefer an existing suitable instance.
- Step 5 needs little compute; Vivado may need x86 Linux, more RAM, and large storage.
- AWS F1 is unnecessary for simulation or ordinary synthesis.

## Repository discipline

- Use `rg`/`rg --files` for searches and `apply_patch` for hand edits.
- Preserve unrelated user changes.
- Add `.gitignore` before producing virtual environments, simulator builds,
  waveforms, caches, or vendor working directories.
- Keep generated RTL under `rtl/generated/` and generated data under `models/`.
- Prefer reproducible scripts and Make targets over undocumented commands.

## Communication

Clearly distinguish verified correctness, synthesis estimates, board measurements,
scaling projections, and untested hypotheses. The user prefers concise, technically
serious explanations without overstating what this small experiment proves.

## Definition of done for step 5

Step 5 is complete only when:

1. Both cocotb suites run from a clean setup.
2. Both circuits pass all 32 vectors and eight outputs per vector.
3. Tests assert `done` behavior.
4. Commands, simulator version, and results are recorded.
5. Generator changes represent any fixes to generated RTL.
6. `README.md` status is updated with the measured result.
