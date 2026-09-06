# Screening-only fallback. This maps behavioral SRAM arrays to standard cells
# and must never be presented as a realistic SRAM area or power result.
export DESIGN_NAME = generic_moe_expert
export PLATFORM = sky130hd
export VERILOG_FILES = /work/inference_core/rtl/weight_sram_1rw.sv /work/inference_core/rtl/generic_moe_expert.sv
export SDC_FILE = /work/inference_core/openroad/constraints.sdc
export CORE_UTILIZATION = 35
export PLACE_DENSITY = 0.55
export TNS_END_PERCENT = 100
export ABC_AREA = 0
