# AWS F2 preliminary results

Date: 2026-09-06

## Flow identity

- Build host: Ubuntu 24.04 FPGA Developer AMI, `c7i.4xlarge`, Vivado 2025.2
- AWS HDK branch: `f2`, F2 `small_shell`
- FPGA part: `xcvu47p-fsvh2892-2-e` (VU47P)
- Clock: `clk_main_a0`, 4.000 ns period (250 MHz)
- Build directives: `SSI_SpreadLogic_high`, `AggressiveExplore`, default F2 clock recipes A1/B2/C0/H2
- Source: `aws_f2/template/`; fixed build adds the `DNHACKS_FIXED` Verilog define

## CL-level synthesis

| Resource | Generic | Fixed |
|---|---:|---:|
| CARRY8 | 672 | 131 |
| LUT primitives (LUT1–LUT6) | 6,899 | 1,269 |
| Flip-flops (FDCE + FDRE) | 1,388 | 821 |
| DSP/BRAM primitives in CL | 0 | 0 |

## Routed timing

| Metric | Generic | Fixed |
|---|---:|---:|
| WNS | -0.841 ns (violated) | +0.036 ns (met) |
| TNS | -79.418 ns | 0.000 ns |
| WHS | +0.010 ns | +0.014 ns |
| THS | 0.000 ns | 0.000 ns |

The generic design produced a `post_route.VIOLATED.dcp`; the fixed design
produced a timing-clean `post_route.dcp`. The post-route reports are generated
by Vivado under `build/reports/` on the AWS build host. These are synthesis and
routing results, not measurements from a physical F2 card. AFI creation and
hardware execution remain pending the open F2 vCPU quota request.
