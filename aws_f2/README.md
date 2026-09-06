# AWS F2 target

This directory contains the first portability layer for the AWS F2 custom
logic (CL) target. The existing `generic_matvec` and generated
`fixed_matvec` cores remain unchanged. `rtl/aws_f2_matvec_axi.sv` exposes the
same core through the F2 shell's 32-bit AXI-Lite OCL window.

## Register map

All accesses are 32-bit and word aligned. Signed INT8 values occupy bits 7:0.

| Address | Meaning |
| --- | --- |
| `0x000`–`0x0FC` | Generic design: 64 row-major weight registers |
| `0x100`–`0x11C` | Eight input registers |
| `0x120` | Control: bit 0 starts; bit 1 clears sticky done |
| `0x124` | Status: bit 0 is sticky done |
| `0x200`–`0x21C` | Eight sign-extended 24-bit output registers |
| `0x300` | Design ID (`DNGB` generic, `DNFB` fixed) |

The wrapper accepts decoupled AXI-Lite write address/data channels and returns
one response per write. A host driver should wait for the final input write to
complete, issue an idle cycle, then write `CONTROL.start`. This preserves the
core's existing nonblocking-assignment timing. The wrapper converts the core's
one-cycle `done` pulse into the host-readable sticky status bit.

The AWS-specific CL top-level, shell tie-offs, and AFI build scripts will be
based on the AWS F2 `CL_TEMPLATE` in `template/`. The template now connects
the shell's OCL window directly to this wrapper and includes both core source
files. Define `DNHACKS_FIXED` for the fixed-weight implementation; otherwise
the generic implementation is selected. The same wrapper and register map are
used for both builds so the comparison remains controlled.

## Host program

`host/matvec_host.c` uses the AWS FPGA SDK (`fpga_pci_poke`/`fpga_pci_peek`) to
run all 32 deterministic vectors and compare all 256 outputs with the CSV
golden data. On an F2 Developer AMI:

```bash
source "$AWS_FPGA_REPO_DIR/sdk_setup.sh"
make -C host
./host/matvec_host generic
./host/matvec_host fixed
```

The host executable is only meaningful after the corresponding AFI has been
loaded into slot 0.
