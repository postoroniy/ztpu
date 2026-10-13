from __future__ import annotations

from pathlib import Path

from tools.rtl_test_utils import compile_zlang_top, run_iverilog


def test_ub_stream_reader_linear_and_transpose(tmp_path: Path) -> None:
    source = compile_zlang_top(tmp_path, "ZtpuUbStreamReader32", "ub_stream.zhl")
    output = run_iverilog(
        tmp_path,
        [source],
        r"""`timescale 1ns/1ps
module tb;
  logic clk=0,rst=0,start=0,transpose_enable=0;
  logic [63:0] base=0,stride_bytes=0,ub_read_addr;
  logic [15:0] count=0;
  logic [2:0] row_count=0;
  logic busy,done,ub_read_valid,ub_read_ready=1,source_valid,source_ready=0;
  logic [31:0] ub_read_data,source_data;
  always #5 clk=~clk;
  ZtpuUbStreamReader32 dut(.*);

  always_comb begin
    case (ub_read_addr)
      64'h100: ub_read_data=32'h04030201;
      64'h110: ub_read_data=32'h14131211;
      64'h120: ub_read_data=32'h24232221;
      64'h130: ub_read_data=32'h34333231;
      default: ub_read_data=32'habc00000 | ub_read_addr[19:0];
    endcase
  end

  task automatic tick;
    begin @(posedge clk);#1; end
  endtask

  initial begin
    #1;rst=1;repeat(2)tick();@(negedge clk);rst=0;

    base=64'h20;count=2;stride_bytes=0;transpose_enable=0;row_count=0;start=1;
    tick();start=0;
    if (!busy || !source_valid || ub_read_addr!=64'h20 || source_data!=32'habc00020)
      $fatal(1,"linear first word mismatch");
    source_ready=0;tick();
    if (ub_read_addr!=64'h20 || source_data!=32'habc00020)
      $fatal(1,"linear stall mismatch");
    source_ready=1;tick();
    if (ub_read_addr!=64'h24 || source_data!=32'habc00024)
      $fatal(1,"linear second word mismatch");
    tick();
    if (source_valid) $fatal(1,"linear stream did not drain");
    tick();if (!done) $fatal(1,"linear done mismatch");
    tick();source_ready=0;

    @(negedge clk);base=64'h100;count=2;stride_bytes=16;
    transpose_enable=1;row_count=4;start=1;tick();start=0;
    repeat(4) tick();
    if (!source_valid || source_data!=32'h31211101)
      $fatal(1,"transpose k0 mismatch %h",source_data);
    source_ready=1;tick();source_ready=0;
    repeat(4) tick();
    if (!source_valid || source_data!=32'h32221202)
      $fatal(1,"transpose k1 mismatch %h",source_data);
    source_ready=1;tick();
    if (!done) $fatal(1,"transpose done mismatch");

    $display("UB stream reader: PASS");$finish;
  end
endmodule
""",
    )
    assert "UB stream reader: PASS" in output


def test_ub_stream_writer_backpressure_and_addresses(tmp_path: Path) -> None:
    source = compile_zlang_top(tmp_path, "ZtpuUbStreamWriter32", "ub_stream.zhl")
    output = run_iverilog(
        tmp_path,
        [source],
        r"""`timescale 1ns/1ps
module tb;
  logic clk=0,rst=0,start=0;
  logic [63:0] base=0,ub_write_addr;
  logic [15:0] count=0;
  logic busy,done,ub_write_valid,ub_write_ready=1,sink_valid=0,sink_ready;
  logic [31:0] ub_write_data,sink_data=0;
  logic [3:0] ub_write_mask;
  always #5 clk=~clk;
  ZtpuUbStreamWriter32 dut(.*);
  task automatic tick; begin @(posedge clk);#1; end endtask
  initial begin
    #1;rst=1;repeat(2)tick();@(negedge clk);rst=0;
    base=64'h80;count=2;start=1;tick();start=0;
    sink_valid=1;sink_data=32'h11112222;ub_write_ready=0;#1;
    if (sink_ready || !ub_write_valid || ub_write_addr!=64'h80)
      $fatal(1,"writer backpressure mismatch ready=%b valid=%b addr=%h busy=%b",
        sink_ready,ub_write_valid,ub_write_addr,busy);
    tick();ub_write_ready=1;#1;
    if (!sink_ready || !ub_write_valid || ub_write_data!=32'h11112222 ||
        ub_write_mask!=4'hf || ub_write_addr!=64'h80)
      $fatal(1,"writer first transfer mismatch");
    tick();sink_data=32'h33334444;#1;
    if (ub_write_addr!=64'h84 || ub_write_data!=32'h33334444)
      $fatal(1,"writer second transfer mismatch");
    tick();sink_valid=0;
    if (ub_write_valid) $fatal(1,"writer did not drain");
    tick();if (!done) $fatal(1,"writer done mismatch");
    $display("UB stream writer: PASS");$finish;
  end
endmodule
""",
    )
    assert "UB stream writer: PASS" in output
