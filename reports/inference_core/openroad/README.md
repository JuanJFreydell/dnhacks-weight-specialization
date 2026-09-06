# OpenROAD physical-design reports

`fixed/` will hold the SKY130HD standard-cell physical-design reports for the
fixed-weight candidate at a 10 ns clock target.

`generic-register-screen/` is intentionally labeled as a screening run only:
it maps the behavioral SRAM model into registers and is not a fair SRAM area or
power comparison. A generic ASIC comparison is reportable only after replacing
`weight_sram_1rw.sv` with characterized SRAM macro wrappers and including their
LEF/Liberty views in the OpenROAD configuration.
