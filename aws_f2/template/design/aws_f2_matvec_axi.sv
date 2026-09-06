// Host-register wrapper used by the AWS F2 custom-logic target.
//
// The AWS F2 shell exposes a 32-bit AXI-Lite OCL window.  This wrapper keeps
// the experiment's original core interface intact and presents a small,
// deterministic register map to the host.  It deliberately uses no DMA or
// external memory: the 8x8 test transaction is small enough for registers.

module dnhacks_matvec_axi #(
    parameter bit FIXED_WEIGHTS = 1'b0
) (
    input  logic        clk,
    input  logic        rst_n,

    input  logic [31:0] s_axi_awaddr,
    input  logic        s_axi_awvalid,
    output logic        s_axi_awready,
    input  logic [31:0] s_axi_wdata,
    input  logic  [3:0] s_axi_wstrb,
    input  logic        s_axi_wvalid,
    output logic        s_axi_wready,
    output logic  [1:0] s_axi_bresp,
    output logic        s_axi_bvalid,
    input  logic        s_axi_bready,

    input  logic [31:0] s_axi_araddr,
    input  logic        s_axi_arvalid,
    output logic        s_axi_arready,
    output logic [31:0] s_axi_rdata,
    output logic  [1:0] s_axi_rresp,
    output logic        s_axi_rvalid,
    input  logic        s_axi_rready
);

    localparam logic [31:0] ADDR_CTRL   = 32'h0000_0120;
    localparam logic [31:0] ADDR_STATUS = 32'h0000_0124;
    localparam logic [31:0] ADDR_ID     = 32'h0000_0300;

    logic        aw_pending_q;
    logic        w_pending_q;
    logic [31:0] awaddr_q;
    logic [31:0] wdata_q;
    logic  [3:0] wstrb_q;
    logic        bvalid_q;

    logic        read_pending_q;
    logic [31:0] read_addr_q;
    logic        rvalid_q;
    logic [31:0] rdata_q;
    logic [31:0] read_data_comb;

    logic        done_q;
    logic        core_start_q;
    logic        core_weight_we_q;
    logic  [5:0] core_weight_addr_q;
    logic  [7:0] core_weight_data_q;
    logic        core_input_we_q;
    logic  [2:0] core_input_addr_q;
    logic  [7:0] core_input_data_q;
    logic  [2:0] core_output_addr;
    logic signed [23:0] core_output_data;
    logic        core_done;

    wire aw_fire = s_axi_awvalid && s_axi_awready;
    wire w_fire  = s_axi_wvalid  && s_axi_wready;
    wire ar_fire = s_axi_arvalid && s_axi_arready;
    wire write_commit = !bvalid_q
                      && (aw_pending_q || aw_fire)
                      && (w_pending_q  || w_fire);
    wire [31:0] commit_addr = aw_fire ? s_axi_awaddr : awaddr_q;
    wire [31:0] commit_data = w_fire  ? s_axi_wdata  : wdata_q;
    wire  [3:0] commit_strb = w_fire ? s_axi_wstrb  : wstrb_q;

    assign s_axi_awready = !aw_pending_q && !bvalid_q && !read_pending_q;
    assign s_axi_wready  = !w_pending_q  && !bvalid_q && !read_pending_q;
    assign s_axi_bresp   = 2'b00;
    assign s_axi_bvalid  = bvalid_q;

    assign s_axi_arready = !read_pending_q && !rvalid_q
                         && !aw_pending_q && !w_pending_q && !bvalid_q;
    assign s_axi_rdata   = rdata_q;
    assign s_axi_rresp   = 2'b00;
    assign s_axi_rvalid  = rvalid_q;

    // The core's indexed output is selected one cycle before a host read is
    // completed, so the registered AXI response sees the selected value.
    assign core_output_addr = read_addr_q[4:2];

    generate
        if (FIXED_WEIGHTS) begin : g_fixed
            fixed_matvec core (
                .clk        (clk),
                .rst_n      (rst_n),
                .input_we   (core_input_we_q),
                .input_addr (core_input_addr_q),
                .input_data ($signed(core_input_data_q)),
                .start      (core_start_q),
                .output_addr(core_output_addr),
                .output_data(core_output_data),
                .done       (core_done)
            );
        end else begin : g_generic
            generic_matvec core (
                .clk        (clk),
                .rst_n      (rst_n),
                .weight_we  (core_weight_we_q),
                .weight_addr(core_weight_addr_q),
                .weight_data($signed(core_weight_data_q)),
                .input_we   (core_input_we_q),
                .input_addr (core_input_addr_q),
                .input_data ($signed(core_input_data_q)),
                .start      (core_start_q),
                .output_addr(core_output_addr),
                .output_data(core_output_data),
                .done       (core_done)
            );
        end
    endgenerate

    always_comb begin
        read_data_comb = 32'd0;
        if (read_addr_q == ADDR_STATUS) begin
            read_data_comb = {31'd0, done_q};
        end else if (read_addr_q == ADDR_ID) begin
            read_data_comb = FIXED_WEIGHTS ? 32'h444E_4642 : 32'h444E_4742;
        end else if ((read_addr_q >= 32'h0000_0200)
                  && (read_addr_q <  32'h0000_0220)
                  && (read_addr_q[1:0] == 2'b00)) begin
            read_data_comb = {{8{core_output_data[23]}}, core_output_data};
        end
    end

    always_ff @(posedge clk) begin
        if (!rst_n) begin
            aw_pending_q      <= 1'b0;
            w_pending_q       <= 1'b0;
            awaddr_q          <= 32'd0;
            wdata_q           <= 32'd0;
            wstrb_q           <= 4'd0;
            bvalid_q          <= 1'b0;
            read_pending_q    <= 1'b0;
            read_addr_q       <= 32'd0;
            rvalid_q          <= 1'b0;
            rdata_q           <= 32'd0;
            done_q            <= 1'b0;
            core_start_q      <= 1'b0;
            core_weight_we_q  <= 1'b0;
            core_weight_addr_q<= 6'd0;
            core_weight_data_q<= 8'd0;
            core_input_we_q   <= 1'b0;
            core_input_addr_q <= 3'd0;
            core_input_data_q <= 8'd0;
        end else begin
            core_start_q     <= 1'b0;
            core_weight_we_q <= 1'b0;
            core_input_we_q  <= 1'b0;

            if (aw_fire) begin
                aw_pending_q <= 1'b1;
                awaddr_q     <= s_axi_awaddr;
            end
            if (w_fire) begin
                w_pending_q <= 1'b1;
                wdata_q     <= s_axi_wdata;
                wstrb_q     <= s_axi_wstrb;
            end

            if (write_commit) begin
                aw_pending_q <= 1'b0;
                w_pending_q  <= 1'b0;
                bvalid_q     <= 1'b1;

                if (commit_strb[0]) begin
                    if ((commit_addr < 32'h0000_0100)
                     && (commit_addr[1:0] == 2'b00)) begin
                        core_weight_we_q   <= 1'b1;
                        core_weight_addr_q <= commit_addr[7:2];
                        core_weight_data_q <= commit_data[7:0];
                    end else if ((commit_addr >= 32'h0000_0100)
                              && (commit_addr <  32'h0000_0120)
                              && (commit_addr[1:0] == 2'b00)) begin
                        core_input_we_q   <= 1'b1;
                        core_input_addr_q <= commit_addr[4:2];
                        core_input_data_q <= commit_data[7:0];
                    end else if (commit_addr == ADDR_CTRL) begin
                        core_start_q <= commit_data[0];
                        if (commit_data[1]) done_q <= 1'b0;
                    end
                end
            end

            if (bvalid_q && s_axi_bready) bvalid_q <= 1'b0;

            if (ar_fire) begin
                read_pending_q <= 1'b1;
                read_addr_q    <= s_axi_araddr;
            end
            if (read_pending_q) begin
                read_pending_q <= 1'b0;
                rdata_q        <= read_data_comb;
                rvalid_q       <= 1'b1;
            end
            if (rvalid_q && s_axi_rready) rvalid_q <= 1'b0;

            if (core_done) done_q <= 1'b1;
        end
    end
endmodule
