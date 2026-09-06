module generic_matvec #(
    parameter int ROWS = 8,
    parameter int COLS = 8,
    parameter int ACC_WIDTH = 24
) (
    input  logic clk,
    input  logic rst_n,
    input  logic weight_we,
    input  logic [$clog2(ROWS*COLS)-1:0] weight_addr,
    input  logic signed [7:0] weight_data,
    input  logic input_we,
    input  logic [$clog2(COLS)-1:0] input_addr,
    input  logic signed [7:0] input_data,
    input  logic start,
    input  logic [$clog2(ROWS)-1:0] output_addr,
    output logic signed [ACC_WIDTH-1:0] output_data,
    output logic done
);

    // Runtime-programmable state: this is the flexibility cost under test.
    logic signed [7:0] w_q [0:ROWS*COLS-1];
    logic signed [7:0] x_q [0:COLS-1];
    logic signed [ACC_WIDTH-1:0] y_q [0:ROWS-1];

    logic signed [ACC_WIDTH-1:0] dot [0:ROWS-1];
    integer row;
    integer col;
    always_comb begin
        for (row = 0; row < ROWS; row = row + 1) begin
            dot[row] = '0;
            for (col = 0; col < COLS; col = col + 1) begin
                dot[row] = dot[row]
                    + ($signed(w_q[row*COLS+col]) * $signed(x_q[col]));
            end
        end
    end

    integer i;
    always_ff @(posedge clk) begin
        if (!rst_n) begin
            done <= 1'b0;
            for (i = 0; i < ROWS*COLS; i = i + 1) w_q[i] <= '0;
            for (i = 0; i < COLS; i = i + 1) x_q[i] <= '0;
            for (i = 0; i < ROWS; i = i + 1) y_q[i] <= '0;
        end else begin
            done <= 1'b0;
            if (weight_we) w_q[weight_addr] <= weight_data;
            if (input_we) x_q[input_addr] <= input_data;
            if (start) begin
                for (i = 0; i < ROWS; i = i + 1) y_q[i] <= dot[i];
                done <= 1'b1;
            end
        end
    end

    assign output_data = y_q[output_addr];
endmodule
