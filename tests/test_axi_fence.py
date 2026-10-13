from __future__ import annotations

from pathlib import Path

from tools.rtl_test_utils import compile_zlang_top, run_iverilog


def test_axi_read_fence_passes_or_synthesizes_error(tmp_path: Path) -> None:
    source = compile_zlang_top(
        tmp_path, "ZtpuAxiReadFence64x32", "axi_fence.zhl"
    )
    output = run_iverilog(
        tmp_path,
        [source],
        r"""`timescale 1ns/1ps
module tb;
  logic clk=0,rst=0,enable=0;
  logic [63:0] base='h100,limit='h200;
  logic fault;logic [63:0] fault_addr;logic [7:0] fault_len;logic [2:0] fault_size;
  logic up_ar_valid=0,up_ar_ready;logic [63:0] up_ar_addr=0;
  logic [7:0] up_ar_len=0;logic [2:0] up_ar_size=2;
  logic up_r_valid,up_r_ready=0,up_r_last;logic [31:0] up_r_data;
  logic [1:0] up_r_resp;
  logic down_ar_valid,down_ar_ready=0;logic [63:0] down_ar_addr;
  logic [7:0] down_ar_len;logic [2:0] down_ar_size;
  logic down_r_valid=0,down_r_ready,down_r_last=0;
  logic [31:0] down_r_data=0;logic [1:0] down_r_resp=0;
  integer beat;
  always #5 clk=~clk;
  ZtpuAxiReadFence64x32 dut(.*);
  task automatic tick; begin @(posedge clk);#1;end endtask
  initial begin
    #1;rst=1;repeat(2)tick();@(negedge clk);rst=0;

    // Disabled fence is transparent even for an otherwise illegal range.
    up_ar_valid=1;up_ar_addr='h800;up_ar_len=3;down_ar_ready=1;#1;
    if(!down_ar_valid || !up_ar_ready || fault || down_ar_addr!='h800 ||
       down_ar_len!=3 || down_ar_size!=2) $fatal(1,"read pass-through mismatch");
    down_r_valid=1;down_r_data=32'h12345678;down_r_last=1;down_r_resp=1;
    up_r_ready=1;#1;
    if(!up_r_valid || up_r_data!=32'h12345678 || !up_r_last ||
       up_r_resp!=1 || !down_r_ready) $fatal(1,"read response pass mismatch");

    // Enabled legal request is also transparent.
    enable=1;up_ar_addr='h180;up_ar_len=3;#1;
    if(!down_ar_valid || !up_ar_ready || fault)
      $fatal(1,"legal read was blocked");

    // Three four-byte beats at 0x1f8 cross the exclusive 0x200 limit.
    down_r_valid=0;up_r_ready=0;up_ar_addr='h1f8;up_ar_len=2;#1;
    if(!up_ar_ready || down_ar_valid!==0 || !fault || fault_addr!='h1f8 ||
       fault_len!=2 || fault_size!=2) $fatal(1,"blocked read accept mismatch");
    tick();@(negedge clk);up_ar_valid=0;
    for(beat=0;beat<3;beat=beat+1) begin
      #1;
      if(!up_r_valid || up_r_data!=0 || up_r_resp!=2 ||
         (up_r_last!==(beat==2)) || down_r_ready)
        $fatal(1,"synthetic read response mismatch beat=%0d",beat);
      if(beat==1) begin tick(); end
      up_r_ready=1;tick();@(negedge clk);up_r_ready=0;
    end
    #1;if(up_r_valid) $fatal(1,"blocked read did not retire");
    $display("AXI read fence: PASS");$finish;
  end
endmodule
""",
    )
    assert "AXI read fence: PASS" in output


def test_axi_write_fence_passes_or_synthesizes_error(tmp_path: Path) -> None:
    source = compile_zlang_top(
        tmp_path, "ZtpuAxiWriteFence64x32", "axi_fence.zhl"
    )
    output = run_iverilog(
        tmp_path,
        [source],
        r"""`timescale 1ns/1ps
module tb;
  logic clk=0,rst=0,enable=0;
  logic [63:0] base='h100,limit='h200;
  logic fault;logic [63:0] fault_addr;logic [7:0] fault_len;logic [2:0] fault_size;
  logic up_aw_valid=0,up_aw_ready;logic [63:0] up_aw_addr=0;
  logic [7:0] up_aw_len=0;logic [2:0] up_aw_size=2;
  logic up_w_valid=0,up_w_ready,up_w_last=0;logic [31:0] up_w_data=0;
  logic up_b_valid,up_b_ready=0;logic [1:0] up_b_resp;
  logic down_aw_valid,down_aw_ready=0;logic [63:0] down_aw_addr;
  logic [7:0] down_aw_len;logic [2:0] down_aw_size;
  logic down_w_valid,down_w_ready=0,down_w_last;logic [31:0] down_w_data;
  logic down_b_valid=0,down_b_ready;logic [1:0] down_b_resp=0;
  integer beat;
  always #5 clk=~clk;
  ZtpuAxiWriteFence64x32 dut(.*);
  task automatic tick; begin @(posedge clk);#1;end endtask
  initial begin
    #1;rst=1;repeat(2)tick();@(negedge clk);rst=0;

    up_aw_valid=1;up_aw_addr='h800;up_aw_len=1;down_aw_ready=1;
    up_w_valid=1;up_w_data=32'hcafebabe;up_w_last=1;down_w_ready=1;
    down_b_valid=1;down_b_resp=1;up_b_ready=1;#1;
    if(!down_aw_valid || !up_aw_ready || !down_w_valid || !up_w_ready ||
       down_w_data!=32'hcafebabe || !down_w_last || !up_b_valid ||
       up_b_resp!=1 || !down_b_ready || fault)
      $fatal(1,"write pass-through mismatch");

    enable=1;down_b_valid=0;up_b_ready=0;down_w_ready=0;
    up_aw_addr='h1fc;up_aw_len=1;#1;
    if(!up_aw_ready || down_aw_valid!==0 || !fault || fault_addr!='h1fc ||
       fault_len!=1 || fault_size!=2) $fatal(1,"blocked write accept mismatch");
    tick();@(negedge clk);up_aw_valid=0;
    for(beat=0;beat<2;beat=beat+1) begin
      up_w_valid=1;up_w_data=beat;up_w_last=(beat==1);#1;
      if(!up_w_ready || down_w_valid) $fatal(1,"blocked W mismatch");
      tick();
    end
    @(negedge clk);up_w_valid=0;up_w_last=0;#1;
    if(!up_b_valid || up_b_resp!=2 || down_b_ready)
      $fatal(1,"synthetic B mismatch");
    tick();
    if(!up_b_valid) $fatal(1,"synthetic B did not hold");
    @(negedge clk);up_b_ready=1;tick();@(negedge clk);up_b_ready=0;#1;
    if(up_b_valid) $fatal(1,"blocked write did not retire");
    $display("AXI write fence: PASS");$finish;
  end
endmodule
""",
    )
    assert "AXI write fence: PASS" in output
