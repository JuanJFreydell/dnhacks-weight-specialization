// Technology binding for the runtime-programmable inference core.
//
// This module deliberately has the same interface as weight_sram_1rw.sv, so
// generic_moe_expert.sv remains the common architecture.  It binds the three
// logical shapes used by that core to the characterized OpenRAM SKY130 macros
// available in the reproducible OpenROAD container:
//   * router: 4 x 64  -> one 80 x 64 macro (64 bits used per word)
//   * up/gate: 256 x 64 -> one 64 x 256 macro each
//   * down: 64 x 256 -> four 80 x 64 macros (64 bits used from each)
//
// The macro has one read/write and one read port. Configuration writes use
// the RW port; inference reads use the independent read port. No read is
// requested during a configuration write, avoiding an undefined same-address
// read/write collision. The 80-bit macro leaves 16 bits unused per word.
module weight_sram_1rw #(
    parameter int WIDTH = 64,
    parameter int DEPTH = 4,
    parameter int ADDR_WIDTH = $clog2(DEPTH)
) (
    input  logic                  clk,
    input  logic                  we,
    input  logic [ADDR_WIDTH-1:0] addr,
    input  logic [WIDTH-1:0]      wdata,
    output logic [WIDTH-1:0]      rdata
);
    generate
        if (WIDTH == 64 && DEPTH == 256) begin : g_64x256
            logic [63:0] dout0_unused, dout1;
            sky130_sram_1rw1r_64x256_8 macro (
                .clk0(clk), .csb0(!we), .web0(!we), .wmask0({8{we}}),
                .addr0(addr), .din0(wdata), .dout0(dout0_unused),
                .clk1(clk), .csb1(we), .addr1(addr), .dout1(dout1)
            );
            assign rdata = dout1;
        end else if (WIDTH == 64 && DEPTH == 4) begin : g_64x4
            logic [79:0] dout0_unused, dout1;
            logic [5:0] macro_addr;
            assign macro_addr = {{(6-ADDR_WIDTH){1'b0}}, addr};
            sky130_sram_1rw1r_80x64_8 macro (
                .clk0(clk), .csb0(!we), .web0(!we), .wmask0({10{we}}),
                .addr0(macro_addr), .din0({16'b0, wdata}), .dout0(dout0_unused),
                .clk1(clk), .csb1(we), .addr1(macro_addr), .dout1(dout1)
            );
            assign rdata = dout1[63:0];
        end else if (WIDTH == 256 && DEPTH == 64) begin : g_256x64
            logic [79:0] dout0_unused [0:3];
            logic [79:0] dout1 [0:3];
            sky130_sram_1rw1r_80x64_8 macro0 (
                .clk0(clk), .csb0(!we), .web0(!we), .wmask0({10{we}}),
                .addr0(addr), .din0({16'b0, wdata[63:0]}), .dout0(dout0_unused[0]),
                .clk1(clk), .csb1(we), .addr1(addr), .dout1(dout1[0])
            );
            sky130_sram_1rw1r_80x64_8 macro1 (
                .clk0(clk), .csb0(!we), .web0(!we), .wmask0({10{we}}),
                .addr0(addr), .din0({16'b0, wdata[127:64]}), .dout0(dout0_unused[1]),
                .clk1(clk), .csb1(we), .addr1(addr), .dout1(dout1[1])
            );
            sky130_sram_1rw1r_80x64_8 macro2 (
                .clk0(clk), .csb0(!we), .web0(!we), .wmask0({10{we}}),
                .addr0(addr), .din0({16'b0, wdata[191:128]}), .dout0(dout0_unused[2]),
                .clk1(clk), .csb1(we), .addr1(addr), .dout1(dout1[2])
            );
            sky130_sram_1rw1r_80x64_8 macro3 (
                .clk0(clk), .csb0(!we), .web0(!we), .wmask0({10{we}}),
                .addr0(addr), .din0({16'b0, wdata[255:192]}), .dout0(dout0_unused[3]),
                .clk1(clk), .csb1(we), .addr1(addr), .dout1(dout1[3])
            );
            assign rdata = {dout1[3][63:0], dout1[2][63:0],
                            dout1[1][63:0], dout1[0][63:0]};
        end else begin : g_unsupported
            initial $error("Unsupported SRAM shape WIDTH=%0d DEPTH=%0d", WIDTH, DEPTH);
            assign rdata = 'x;
        end
    endgenerate
endmodule
