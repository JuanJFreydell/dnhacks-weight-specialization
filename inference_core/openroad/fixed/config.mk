export DESIGN_NAME = fixed_moe_expert
export PLATFORM = sky130hd
export VERILOG_FILES = /work/inference_core/rtl/fixed_moe_expert.sv
export VERILOG_INCLUDE_DIRS = /work
export SDC_FILE = /work/inference_core/openroad/constraints.sdc
export CORE_UTILIZATION = 35
export PLACE_DENSITY = 0.55
export TNS_END_PERCENT = 100
export ABC_AREA = 0
# The generated constant-word lookup functions and local activation buffers are
# intentionally larger than ORFS's 4 KiB safety default.  This only permits
# synthesis; it does not infer a physical SRAM macro in this fixed-weight core.
export SYNTH_MEMORY_MAX_BITS = 65536
