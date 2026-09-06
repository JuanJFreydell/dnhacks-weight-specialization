# OpenROAD physical-design reports

`fixed/` will hold the SKY130HD standard-cell physical-design reports for the
fixed-weight candidate at a 20 ns clock target.

`generic-register-screen/` is intentionally labeled as a screening run only:
it maps the behavioral SRAM model into registers and is not a fair SRAM area or
power comparison. A generic ASIC comparison is reportable only after replacing
`weight_sram_1rw.sv` with characterized SRAM macro wrappers and including their
LEF/Liberty views in the OpenROAD configuration.

`generic-sram-macro/` is that macro-based counterpart. It uses the public
Sky130 OpenRAM 64x256 and 80x64 1RW1R macro views carried in the pinned ORFS
container. Its physical capacity is 7,296 bytes for 6,176 logical coefficient
bytes because the small router and 256-bit down words are banked into the
available macro shapes. It is the comparison candidate; any reported result
must identify the macro banking, 20 ns constraint, and ORFS image digest.
