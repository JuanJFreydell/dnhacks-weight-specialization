// Behavioral model for a synchronous one-read/one-write SRAM macro port.
// ASIC integration replaces this module with technology SRAM macros of the
// same interface; it is intentionally not reset because real SRAMs are not.
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
    logic [WIDTH-1:0] mem [0:DEPTH-1];

    always_ff @(posedge clk) begin
        if (we) mem[addr] <= wdata;
        rdata <= mem[addr];
    end
endmodule
