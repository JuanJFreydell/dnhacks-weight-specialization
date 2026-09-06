// Generated file: do not hand-edit.
// Every W coefficient is a synthesis-time constant.
module fixed_matvec #(
    parameter int ROWS = 8,
    parameter int COLS = 8,
    parameter int ACC_WIDTH = 24
) (
    input  logic clk,
    input  logic rst_n,
    input  logic input_we,
    input  logic [$clog2(COLS)-1:0] input_addr,
    input  logic signed [7:0] input_data,
    input  logic start,
    input  logic [$clog2(ROWS)-1:0] output_addr,
    output logic signed [ACC_WIDTH-1:0] output_data,
    output logic done
);

    logic signed [7:0] x_q [0:COLS-1];
    logic signed [ACC_WIDTH-1:0] y_q [0:ROWS-1];

    wire signed [ACC_WIDTH-1:0] dot_0 =
                ($signed(8'sd7) * $signed(x_q[0])) +
                ($signed(8'sd3) * $signed(x_q[1])) +
                ($signed(-8'sd2) * $signed(x_q[2])) +
                ($signed(8'sd6) * $signed(x_q[3])) +
                ($signed(8'sd1) * $signed(x_q[4])) +
                ($signed(-8'sd1) * $signed(x_q[5])) +
                ($signed(8'sd2) * $signed(x_q[6])) +
                ($signed(8'sd6) * $signed(x_q[7]));

    wire signed [ACC_WIDTH-1:0] dot_1 =
                ($signed(-8'sd4) * $signed(x_q[0])) +
                ($signed(-8'sd8) * $signed(x_q[1])) +
                ($signed(8'sd7) * $signed(x_q[2])) +
                ($signed(-8'sd6) * $signed(x_q[3])) +
                ($signed(8'sd0) * $signed(x_q[4])) +
                ($signed(8'sd1) * $signed(x_q[5])) +
                ($signed(8'sd6) * $signed(x_q[6])) +
                ($signed(8'sd7) * $signed(x_q[7]));

    wire signed [ACC_WIDTH-1:0] dot_2 =
                ($signed(-8'sd4) * $signed(x_q[0])) +
                ($signed(8'sd5) * $signed(x_q[1])) +
                ($signed(8'sd1) * $signed(x_q[2])) +
                ($signed(-8'sd5) * $signed(x_q[3])) +
                ($signed(-8'sd1) * $signed(x_q[4])) +
                ($signed(8'sd2) * $signed(x_q[5])) +
                ($signed(8'sd4) * $signed(x_q[6])) +
                ($signed(8'sd3) * $signed(x_q[7]));

    wire signed [ACC_WIDTH-1:0] dot_3 =
                ($signed(-8'sd7) * $signed(x_q[0])) +
                ($signed(-8'sd2) * $signed(x_q[1])) +
                ($signed(-8'sd5) * $signed(x_q[2])) +
                ($signed(-8'sd1) * $signed(x_q[3])) +
                ($signed(-8'sd5) * $signed(x_q[4])) +
                ($signed(8'sd4) * $signed(x_q[5])) +
                ($signed(8'sd5) * $signed(x_q[6])) +
                ($signed(-8'sd1) * $signed(x_q[7]));

    wire signed [ACC_WIDTH-1:0] dot_4 =
                ($signed(8'sd1) * $signed(x_q[0])) +
                ($signed(8'sd1) * $signed(x_q[1])) +
                ($signed(-8'sd6) * $signed(x_q[2])) +
                ($signed(8'sd7) * $signed(x_q[3])) +
                ($signed(8'sd7) * $signed(x_q[4])) +
                ($signed(8'sd6) * $signed(x_q[5])) +
                ($signed(8'sd6) * $signed(x_q[6])) +
                ($signed(-8'sd8) * $signed(x_q[7]));

    wire signed [ACC_WIDTH-1:0] dot_5 =
                ($signed(-8'sd1) * $signed(x_q[0])) +
                ($signed(8'sd0) * $signed(x_q[1])) +
                ($signed(-8'sd8) * $signed(x_q[2])) +
                ($signed(-8'sd5) * $signed(x_q[3])) +
                ($signed(8'sd2) * $signed(x_q[4])) +
                ($signed(-8'sd7) * $signed(x_q[5])) +
                ($signed(-8'sd2) * $signed(x_q[6])) +
                ($signed(-8'sd7) * $signed(x_q[7]));

    wire signed [ACC_WIDTH-1:0] dot_6 =
                ($signed(-8'sd6) * $signed(x_q[0])) +
                ($signed(8'sd2) * $signed(x_q[1])) +
                ($signed(-8'sd4) * $signed(x_q[2])) +
                ($signed(8'sd4) * $signed(x_q[3])) +
                ($signed(-8'sd7) * $signed(x_q[4])) +
                ($signed(-8'sd4) * $signed(x_q[5])) +
                ($signed(8'sd7) * $signed(x_q[6])) +
                ($signed(-8'sd4) * $signed(x_q[7]));

    wire signed [ACC_WIDTH-1:0] dot_7 =
                ($signed(-8'sd7) * $signed(x_q[0])) +
                ($signed(8'sd5) * $signed(x_q[1])) +
                ($signed(-8'sd7) * $signed(x_q[2])) +
                ($signed(-8'sd7) * $signed(x_q[3])) +
                ($signed(-8'sd2) * $signed(x_q[4])) +
                ($signed(8'sd5) * $signed(x_q[5])) +
                ($signed(8'sd2) * $signed(x_q[6])) +
                ($signed(8'sd0) * $signed(x_q[7]));

    integer i;
    always_ff @(posedge clk) begin
        if (!rst_n) begin
            done <= 1'b0;
            for (i = 0; i < COLS; i = i + 1) x_q[i] <= '0;
            for (i = 0; i < ROWS; i = i + 1) y_q[i] <= '0;
        end else begin
            done <= 1'b0;
            if (input_we) x_q[input_addr] <= input_data;
            if (start) begin
                y_q[0] <= dot_0;
                y_q[1] <= dot_1;
                y_q[2] <= dot_2;
                y_q[3] <= dot_3;
                y_q[4] <= dot_4;
                y_q[5] <= dot_5;
                y_q[6] <= dot_6;
                y_q[7] <= dot_7;
                done <= 1'b1;
            end
        end
    end

    assign output_data = y_q[output_addr];
endmodule
