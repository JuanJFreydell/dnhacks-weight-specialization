# Runtime-programmable core using characterized OpenRAM SKY130 SRAM macros.
# The wrapper binds logical arrays as follows: one 80x64 macro for the router,
# one 64x256 macro for each up/gate store, and four 80x64 macros for the
# 256-bit down-projection words. Total physical SRAM capacity is 7,296 bytes
# for 6,176 bytes of logical INT4 coefficients.
export DESIGN_NAME = generic_moe_expert
export PLATFORM = sky130hd
export VERILOG_FILES = /work/inference_core/rtl/sky130_sram_blackbox.sv /work/inference_core/rtl/weight_sram_sky130_1rw.sv /work/inference_core/rtl/generic_moe_expert.sv
export SDC_FILE = /work/inference_core/openroad/constraints.sdc
export CORE_UTILIZATION = 35
export PLACE_DENSITY = 0.55
export TNS_END_PERCENT = 100
export ABC_AREA = 0
export PDN_TCL = /work/inference_core/openroad/generic-sram-macro/pdn.tcl

export SRAM_DIR = /OpenROAD-flow-scripts/flow/platforms/sky130ram
export ADDITIONAL_LEFS = $(SRAM_DIR)/sky130_sram_1rw1r_64x256_8/sky130_sram_1rw1r_64x256_8.lef \
                         $(SRAM_DIR)/sky130_sram_1rw1r_80x64_8/sky130_sram_1rw1r_80x64_8.lef
export ADDITIONAL_LIBS = $(SRAM_DIR)/sky130_sram_1rw1r_64x256_8/sky130_sram_1rw1r_64x256_8_TT_1p8V_25C.lib \
                         $(SRAM_DIR)/sky130_sram_1rw1r_80x64_8/sky130_sram_1rw1r_80x64_8_TT_1p8V_25C.lib
export ADDITIONAL_GDS = $(SRAM_DIR)/sky130_sram_1rw1r_64x256_8/sky130_sram_1rw1r_64x256_8.gds \
                        $(SRAM_DIR)/sky130_sram_1rw1r_80x64_8/sky130_sram_1rw1r_80x64_8.gds
