from __future__ import annotations

from pathlib import Path

from tools.rtl_test_utils import compile_zlang_top, run_iverilog


def test_stream_fifo_order_backpressure_and_simultaneous_transfer(tmp_path: Path) -> None:
    source = compile_zlang_top(tmp_path, "ZtpuStreamFifo32x4", "storage.zhl")
    output = run_iverilog(
        tmp_path,
        [source],
        r"""`timescale 1ns/1ps
module tb;
  logic clk=0,rst=0,sink_valid=0,source_ready=0;
  logic [31:0] sink_data=0,source_data;
  logic sink_ready,source_valid;
  logic [2:0] level;
  always #5 clk=~clk;
  ZtpuStreamFifo32x4 dut(.*);
  task automatic step(input logic push_valid,input logic pop_ready,input logic [31:0] data);
    begin
      @(negedge clk); sink_valid=push_valid;source_ready=pop_ready;sink_data=data;
      @(posedge clk);#1;
    end
  endtask
  initial begin
    #1;rst=1;repeat(2)@(posedge clk);@(negedge clk);rst=0;
    #1;
    if (!sink_ready || source_valid || level!=0) $fatal(1,"empty mismatch");
    step(1,0,32'h11); step(1,0,32'h22); step(1,0,32'h33); step(1,0,32'h44);
    if (sink_ready || !source_valid || source_data!==32'h11 || level!=4)
      $fatal(1,"full mismatch data=%h level=%0d",source_data,level);
    step(1,1,32'h55);
    if (!sink_ready || source_data!==32'h22 || level!=3)
      $fatal(1,"full pop policy mismatch data=%h level=%0d",source_data,level);
    step(1,1,32'h55);
    if (source_data!==32'h33 || level!=3) $fatal(1,"replace mismatch");
    step(0,1,0); if (source_data!==32'h44 || level!=2) $fatal(1,"order 44 mismatch");
    step(0,1,0); if (source_data!==32'h55 || level!=1) $fatal(1,"order 55 mismatch");
    step(0,1,0); if (source_valid || level!=0) $fatal(1,"drain mismatch");
    $display("stream fifo: PASS");$finish;
  end
endmodule
""",
    )
    assert "stream fifo: PASS" in output


def test_completion_queue_wraparound_clear_and_overflow(tmp_path: Path) -> None:
    source = compile_zlang_top(tmp_path, "ZtpuCompletionQueue8", "storage.zhl")
    output = run_iverilog(
        tmp_path,
        [source],
        r"""`timescale 1ns/1ps
module tb;
  logic clk=0,rst=0,enable=1,clear=0,push_valid=0,pop=0;
  logic [7:0] push_tag=0,push_error=0,head_tag,head_error;
  logic [3:0] push_opcode=0,push_status=0,head_opcode,head_status;
  logic push_ready,head_valid,overflow;
  logic [3:0] count;
  always #5 clk=~clk;
  ZtpuCompletionQueue8 dut(.*);
  task automatic step(input logic pv,input logic pp,input logic [7:0] tag);
    begin
      @(negedge clk);push_valid=pv;pop=pp;push_tag=tag;
      push_opcode=tag[3:0];push_status=tag[7:4];push_error=tag^8'h5a;
      @(posedge clk);#1;
    end
  endtask
  initial begin
    #1;rst=1;repeat(2)@(posedge clk);@(negedge clk);rst=0;
    for(integer i=1;i<=8;i=i+1) step(1,0,i);
    if (push_ready || count!=8 || !head_valid || head_tag!=1) $fatal(1,"full mismatch");
    step(1,1,9);
    if (!overflow || count!=7 || head_tag!=2) $fatal(1,"overflow/full pop mismatch");
    step(1,1,9);
    if (count!=7 || head_tag!=3) $fatal(1,"replacement mismatch");
    enable=0;step(1,1,10);
    if (push_ready || head_valid || count!=7) $fatal(1,"disable mismatch");
    @(negedge clk);enable=1;clear=1;@(posedge clk);#1;
    if (count!=0 || overflow || head_valid) $fatal(1,"clear mismatch");
    @(negedge clk);clear=0;push_valid=0;pop=0;
    step(1,0,8'haa);
    if (!head_valid || head_tag!=8'haa || head_opcode!=4'ha ||
        head_status!=4'ha || head_error!=(8'haa^8'h5a))
      $fatal(1,"payload mismatch valid=%b tag=%h opcode=%h status=%h err=%h",
        head_valid,head_tag,head_opcode,head_status,head_error);
    $display("completion queue: PASS");$finish;
  end
endmodule
""",
    )
    assert "completion queue: PASS" in output
