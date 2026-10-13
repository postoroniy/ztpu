from __future__ import annotations

from pathlib import Path

from tools.rtl_test_utils import compile_zlang_top, run_iverilog


def test_systolic_array_matrix_product(tmp_path: Path) -> None:
    source = compile_zlang_top(tmp_path, "ZtpuSystolicArray2x2Q16")
    output = run_iverilog(
        tmp_path,
        [source],
        r"""`timescale 1ns/1ps
module tb;
  logic clk = 0;
  logic rst = 0;
  logic clear = 0;
  logic signed [15:0] input0 = 0, input1 = 0;
  logic signed [15:0] weight0 = 0, weight1 = 0;
  logic signed [31:0] output00, output01, output10, output11;
  always #5 clk = ~clk;
  ZtpuSystolicArray2x2Q16 dut(.*);
  task automatic drive(
      input logic clr,
      input signed [15:0] i0, input signed [15:0] i1,
      input signed [15:0] w0, input signed [15:0] w1);
    begin
      @(negedge clk); clear = clr; input0 = i0; input1 = i1;
      weight0 = w0; weight1 = w1;
      @(posedge clk); #1;
    end
  endtask
  initial begin
    #1; rst = 1;
    repeat (2) @(posedge clk);
    @(negedge clk); rst = 0;
    drive(1, 0, 0, 0, 0);
    drive(0, 1, 3, 5, 6);
    drive(0, 2, 4, 7, 8);
    drive(0, 0, 0, 0, 0);
    drive(0, 0, 0, 0, 0);
    drive(0, 0, 0, 0, 0);
    drive(0, 0, 0, 0, 0);
    if (output00 !== 19 || output01 !== 22 ||
        output10 !== 43 || output11 !== 50)
      $fatal(1, "matrix mismatch %0d %0d %0d %0d",
        output00, output01, output10, output11);
    $display("systolic array: PASS");
    $finish;
  end
endmodule
""",
    )
    assert "systolic array: PASS" in output


def test_mxu_microsequencer_drain_timing(tmp_path: Path) -> None:
    source = compile_zlang_top(tmp_path, "ZtpuMxuMicroSequencerD4")
    output = run_iverilog(
        tmp_path,
        [source],
        r"""`timescale 1ns/1ps
module tb;
  logic clk = 0;
  logic rst = 0;
  logic start = 0;
  logic [15:0] k_dim = 3;
  logic feeder_done = 0;
  logic kick, busy, done;
  always #5 clk = ~clk;
  ZtpuMxuMicroSequencerD4 dut(.*);
  initial begin
    #1; rst = 1;
    repeat (2) @(posedge clk);
    @(negedge clk); rst = 0; start = 1;
    @(posedge clk); #1;
    if (!kick || !busy || done) $fatal(1, "kick state mismatch");
    @(negedge clk); start = 0;
    @(posedge clk); #1;
    if (kick || !busy || done) $fatal(1, "stream state mismatch");
    repeat (2) @(posedge clk);
    @(negedge clk); feeder_done = 1;
    @(posedge clk); #1;
    if (done || !busy) $fatal(1, "early done");
    @(negedge clk); feeder_done = 0;
    repeat (4) begin
      @(posedge clk); #1;
      if (done || !busy) $fatal(1, "drain mismatch");
    end
    @(posedge clk); #1;
    if (!done || busy) $fatal(1, "missing done pulse");
    @(posedge clk); #1;
    if (done || busy) $fatal(1, "done did not clear");
    $display("mxu microsequencer: PASS");
    $finish;
  end
endmodule
""",
    )
    assert "mxu microsequencer: PASS" in output


def test_mxu_stream_feeder_alignment_and_sign_extension(tmp_path: Path) -> None:
    source = compile_zlang_top(tmp_path, "ZtpuMxuStreamFeeder4x4I8")
    output = run_iverilog(
        tmp_path,
        [source],
        r"""`timescale 1ns/1ps
module tb;
  logic clk = 0;
  logic rst = 0;
  logic start = 0;
  logic [15:0] k_dim = 2;
  logic [1:0] b_format = 0;
  logic sink_a_valid = 0, sink_b_valid = 0;
  logic [31:0] sink_a_data = 0, sink_b_data = 0;
  logic sink_a_ready, sink_b_ready, busy, done, clear_pulse, step_valid;
  logic signed [31:0] a0, a1, a2, a3, b0, b1, b2, b3;
  always #5 clk = ~clk;
  ZtpuMxuStreamFeeder4x4I8 dut(.*);
  initial begin
    #1; rst = 1;
    repeat (2) @(posedge clk);
    @(negedge clk); rst = 0; start = 1;
    #1;
    if (!clear_pulse) $fatal(1, "missing clear pulse");
    @(posedge clk); #1;
    if (!busy || clear_pulse) $fatal(1, "run state mismatch");
    @(negedge clk); start = 0; sink_a_valid = 1; sink_b_valid = 0;
    sink_a_data = 32'h7f0080ff; sink_b_data = 32'h01fe03fc;
    #1;
    if (sink_a_ready || sink_b_ready || step_valid) $fatal(1, "unaligned consume");
    @(posedge clk);
    @(negedge clk); sink_b_valid = 1;
    #1;
    if (!sink_a_ready || !sink_b_ready || !step_valid) $fatal(1, "missing consume");
    if (a0 !== -1 || a1 !== -128 || a2 !== 0 || a3 !== 127)
      $fatal(1, "A lane mismatch %0d %0d %0d %0d", a0, a1, a2, a3);
    if (b0 !== -4 || b1 !== 3 || b2 !== -2 || b3 !== 1)
      $fatal(1, "B lane mismatch %0d %0d %0d %0d", b0, b1, b2, b3);
    @(posedge clk);
    @(negedge clk); sink_a_data = 32'h04030201; sink_b_data = 32'h08070605;
    #1;
    if (!step_valid) $fatal(1, "missing second consume");
    @(posedge clk);
    @(negedge clk); sink_a_valid = 0; sink_b_valid = 0;
    @(posedge clk); #1;
    if (!done || busy) $fatal(1, "missing feeder done");
    @(posedge clk); #1;
    if (done || busy) $fatal(1, "feeder done did not clear");
    $display("mxu stream feeder: PASS");
    $finish;
  end
endmodule
""",
    )
    assert "mxu stream feeder: PASS" in output


def test_zero_skip_passthrough_and_metadata(tmp_path: Path) -> None:
    source = compile_zlang_top(tmp_path, "ZtpuZeroSkipMask32")
    output = run_iverilog(
        tmp_path,
        [source],
        r"""`timescale 1ns/1ps
module tb;
  logic enable = 1;
  logic sink_valid = 1;
  logic [31:0] sink_data = 32'h01007f00;
  logic source_ready = 1;
  logic sink_ready, source_valid, mask_valid, all_zero;
  logic [31:0] source_data;
  logic [3:0] mask;
  logic [2:0] nz_count;
  ZtpuZeroSkipMask32 dut(.*);
  initial begin
    #1;
    if (!sink_ready || !source_valid || !mask_valid || source_data !== sink_data)
      $fatal(1, "passthrough mismatch");
    if (mask !== 4'b1010 || nz_count !== 2 || all_zero)
      $fatal(1, "metadata mismatch mask=%b count=%0d zero=%b", mask, nz_count, all_zero);
    enable = 0; sink_data = 32'hffffffff; #1;
    if (mask !== 0 || nz_count !== 0 || !all_zero || source_data !== sink_data)
      $fatal(1, "disabled mismatch");
    enable = 1; sink_data = 0; source_ready = 0; #1;
    if (sink_ready || mask !== 0 || nz_count !== 0 || !all_zero)
      $fatal(1, "zero/backpressure mismatch");
    $display("zero skip: PASS");
    $finish;
  end
endmodule
""",
    )
    assert "zero skip: PASS" in output
