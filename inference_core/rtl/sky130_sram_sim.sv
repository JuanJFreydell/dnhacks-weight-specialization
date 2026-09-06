// Cycle-accurate functional models for the two characterized SKY130 macros.
// Used only by cocotb. Physical synthesis uses sky130_sram_blackbox.sv plus
// the macro LEF/Liberty/GDS views supplied by OpenROAD-flow-scripts.
module sky130_sram_1rw1r_64x256_8 (
    input logic clk0, csb0, web0,
    input logic [7:0] wmask0,
    input logic [7:0] addr0,
    input logic [63:0] din0,
    output logic [63:0] dout0,
    input logic clk1, csb1,
    input logic [7:0] addr1,
    output logic [63:0] dout1
);
    logic [63:0] mem [0:255];
    integer index;
    always_ff @(posedge clk0) begin
        if (!csb0 && !web0)
            for (index = 0; index < 8; index = index + 1)
                if (wmask0[index]) mem[addr0][index*8 +: 8] <= din0[index*8 +: 8];
        if (!csb0 && web0) dout0 <= mem[addr0];
    end
    always_ff @(posedge clk1) if (!csb1) dout1 <= mem[addr1];
endmodule

module sky130_sram_1rw1r_80x64_8 (
    input logic clk0, csb0, web0,
    input logic [9:0] wmask0,
    input logic [5:0] addr0,
    input logic [79:0] din0,
    output logic [79:0] dout0,
    input logic clk1, csb1,
    input logic [5:0] addr1,
    output logic [79:0] dout1
);
    logic [79:0] mem [0:63];
    integer index;
    always_ff @(posedge clk0) begin
        if (!csb0 && !web0)
            for (index = 0; index < 10; index = index + 1)
                if (wmask0[index]) mem[addr0][index*8 +: 8] <= din0[index*8 +: 8];
        if (!csb0 && web0) dout0 <= mem[addr0];
    end
    always_ff @(posedge clk1) if (!csb1) dout1 <= mem[addr1];
endmodule
