// Physical macro declarations. Their LEF, Liberty, and GDS views are
// configured in openroad/generic-sram-macro/config.mk.
(* blackbox *) module sky130_sram_1rw1r_64x256_8 (
    input clk0, csb0, web0,
    input [7:0] wmask0,
    input [7:0] addr0,
    input [63:0] din0,
    output [63:0] dout0,
    input clk1, csb1,
    input [7:0] addr1,
    output [63:0] dout1
);
endmodule

(* blackbox *) module sky130_sram_1rw1r_80x64_8 (
    input clk0, csb0, web0,
    input [9:0] wmask0,
    input [5:0] addr0,
    input [79:0] din0,
    output [79:0] dout0,
    input clk1, csb1,
    input [5:0] addr1,
    output [79:0] dout1
);
endmodule
