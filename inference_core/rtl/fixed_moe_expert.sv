// Compile-time-specialized counterpart to generic_moe_expert.
// The generated word functions contain every INT4 coefficient as an RTL constant.
module fixed_moe_expert #(
    parameter int EXPERTS = 4,
    parameter int MODEL_WIDTH = 16,
    parameter int HIDDEN_WIDTH = 64,
    parameter int ACC_WIDTH = 24,
    parameter int ACTIVATION_SHIFT = 6
) (
    input  logic clk,
    input  logic rst_n,
    input  logic input_we,
    input  logic [$clog2(MODEL_WIDTH)-1:0] input_addr,
    input  logic signed [7:0] input_data,
    input  logic start,
    input  logic [$clog2(MODEL_WIDTH)-1:0] output_addr,
    output logic signed [ACC_WIDTH-1:0] output_data,
    output logic [$clog2(EXPERTS)-1:0] selected_expert,
    output logic busy,
    output logic done
);
    localparam int ROUTER_WORD_WIDTH = MODEL_WIDTH * 4;
    localparam int DOWN_WORD_WIDTH = HIDDEN_WIDTH * 4;
    typedef enum logic [2:0] {IDLE, HIDDEN, OUTPUT, COMPLETE} state_t;
    state_t state_q;

    logic signed [7:0] x_q [0:MODEL_WIDTH-1];
    logic signed [ACC_WIDTH-1:0] hidden_q [0:HIDDEN_WIDTH-1];
    logic signed [ACC_WIDTH-1:0] y_q [0:MODEL_WIDTH-1];
    logic [$clog2(HIDDEN_WIDTH)-1:0] hidden_index_q;
    logic [$clog2(MODEL_WIDTH)-1:0] output_index_q;

    `include "inference_core/rtl/generated/fixed_moe_words.svh"

    function automatic logic signed [31:0] dot_input(
        input logic [ROUTER_WORD_WIDTH-1:0] word
    );
        integer index;
        logic signed [31:0] sum;
        begin
            sum = '0;
            for (index = 0; index < MODEL_WIDTH; index = index + 1)
                sum = sum + ($signed(word[index*4 +: 4]) * $signed(x_q[index]));
            dot_input = sum;
        end
    endfunction

    function automatic logic signed [47:0] dot_hidden(
        input logic [DOWN_WORD_WIDTH-1:0] word
    );
        integer index;
        logic signed [47:0] sum;
        begin
            sum = '0;
            for (index = 0; index < HIDDEN_WIDTH; index = index + 1)
                sum = sum + ($signed(word[index*4 +: 4]) * $signed(hidden_q[index]));
            dot_hidden = sum;
        end
    endfunction

    function automatic logic signed [ACC_WIDTH-1:0] clamp24(
        input logic signed [63:0] value
    );
        begin
            // The generated operating range is proven by the NumPy model not
            // to overflow 24 bits. This is an explicit final-width cast; all
            // products and reductions above remain wider than ACC_WIDTH.
            clamp24 = value[ACC_WIDTH-1:0];
        end
    endfunction

    function automatic logic signed [ACC_WIDTH-1:0] reglu(
        input logic signed [31:0] up_value,
        input logic signed [31:0] gate_value
    );
        logic signed [63:0] product;
        begin
            product = gate_value > 0 ? up_value * gate_value : '0;
            reglu = clamp24(product >>> ACTIVATION_SHIFT);
        end
    endfunction

    function automatic logic [$clog2(EXPERTS)-1:0] choose_expert_fixed;
        integer index;
        logic signed [31:0] score, best_score;
        begin
            choose_expert_fixed = '0;
            best_score = dot_input(fixed_router_word(0));
            for (index = 1; index < EXPERTS; index = index + 1) begin
                score = dot_input(fixed_router_word(index));
                if (score > best_score) begin
                    choose_expert_fixed = index[$clog2(EXPERTS)-1:0];
                    best_score = score;
                end
            end
        end
    endfunction

    integer i;
    logic signed [47:0] output_sum;
    always_ff @(posedge clk) begin
        if (!rst_n) begin
            state_q <= IDLE;
            busy <= 1'b0;
            done <= 1'b0;
            selected_expert <= '0;
            hidden_index_q <= '0;
            output_index_q <= '0;
            for (i = 0; i < MODEL_WIDTH; i = i + 1) begin
                x_q[i] <= '0;
                y_q[i] <= '0;
            end
            for (i = 0; i < HIDDEN_WIDTH; i = i + 1) hidden_q[i] <= '0;
        end else begin
            done <= 1'b0;
            if (input_we && !busy) x_q[input_addr] <= input_data;
            case (state_q)
                IDLE: if (start && !input_we) begin
                    busy <= 1'b1;
                    selected_expert <= choose_expert_fixed();
                    hidden_index_q <= '0;
                    state_q <= HIDDEN;
                end
                HIDDEN: begin
                    hidden_q[hidden_index_q] <= reglu(
                        dot_input(fixed_up_word(selected_expert * HIDDEN_WIDTH + hidden_index_q)),
                        dot_input(fixed_gate_word(selected_expert * HIDDEN_WIDTH + hidden_index_q))
                    );
                    if (hidden_index_q == HIDDEN_WIDTH - 1) begin
                        output_index_q <= '0;
                        state_q <= OUTPUT;
                    end else hidden_index_q <= hidden_index_q + 1'b1;
                end
                OUTPUT: begin
                    output_sum = dot_hidden(
                        fixed_down_word(selected_expert * MODEL_WIDTH + output_index_q)
                    ) + $signed(x_q[output_index_q]);
                    y_q[output_index_q] <= clamp24(output_sum);
                    if (output_index_q == MODEL_WIDTH - 1) state_q <= COMPLETE;
                    else output_index_q <= output_index_q + 1'b1;
                end
                COMPLETE: begin
                    busy <= 1'b0;
                    done <= 1'b1;
                    state_q <= IDLE;
                end
                default: state_q <= IDLE;
            endcase
        end
    end

    assign output_data = y_q[output_addr];
endmodule
