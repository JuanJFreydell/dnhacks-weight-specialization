# Superseded 10 ns exploratory run

On 2026-09-06, the initial fixed-core ORFS run used a 10 ns constraint. It
passed Yosys synthesis but entered a long setup-repair loop with roughly 1,900
violating endpoints and approximately -6.8 ns worst slack during repair. The
run was deliberately cancelled before completion to avoid consuming an AWS
build instance for an unproductive, unpipelined target.

This is not a completed timing report and must not be used as a PPA result.
The stored, paired physical runs use the shared 20 ns constraint in
`inference_core/openroad/constraints.sdc`.
