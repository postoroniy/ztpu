from __future__ import annotations

from pathlib import Path

from tools.rtl_test_utils import compile_zlang_top, run_iverilog


def test_command_queue_dependency_and_payload(tmp_path: Path) -> None:
    source = compile_zlang_top(tmp_path, "ZtpuCommandQueue4", "scheduler.zhl")
    output = run_iverilog(
        tmp_path,
        [source],
        r"""`timescale 1ns/1ps
module tb;
  logic clk=0,rst=0,in_valid=0,out_ready=0,done_valid=0;
  logic [3:0] in_opcode=0,out_opcode;
  logic [63:0] in_addr=0,in_aux=0,out_addr,out_aux;
  logic [15:0] in_length=0,out_length;
  logic [7:0] in_tag=0,in_dep_tag=0,out_tag,out_dep_tag,done_tag=0,last_done;
  logic [63:0] in_src1_base=0,out_src1_base;
  logic [31:0] in_scalar0=0,in_scalar1=0,in_scalar2=0,in_scalar3=0;
  logic [31:0] out_scalar0,out_scalar1,out_scalar2,out_scalar3;
  logic in_mxu_valid=0,out_mxu_valid;
  logic [63:0] in_mxu_a_base=0,in_mxu_b_base=0,in_mxu_c_base=0,in_mxu_acc_base=0;
  logic [63:0] out_mxu_a_base,out_mxu_b_base,out_mxu_c_base,out_mxu_acc_base;
  logic [31:0] in_mxu_a_stride=0,in_mxu_b_stride=0,in_mxu_k_dim=0;
  logic [31:0] out_mxu_a_stride,out_mxu_b_stride,out_mxu_k_dim;
  logic in_mxu_accum_en=0,in_mxu_acc_clear=0,in_mxu_spill_en=0,in_mxu_restore_en=0;
  logic out_mxu_accum_en,out_mxu_acc_clear,out_mxu_spill_en,out_mxu_restore_en;
  logic in_mxu_rq_enable=0,out_mxu_rq_enable;
  logic [31:0] in_mxu_rq_scale=0,out_mxu_rq_scale;
  logic [7:0] in_mxu_rq_shift=0,out_mxu_rq_shift;
  logic [31:0] in_mxu_rq_zero=0,out_mxu_rq_zero;
  logic [2:0] in_mxu_mode=0,out_mxu_mode;
  logic in_mxu_a_transpose=0,in_mxu_b_transpose=0,out_mxu_a_transpose,out_mxu_b_transpose;
  logic in_mxu_zs_enable_a=0,in_mxu_zs_enable_b=0,out_mxu_zs_enable_a,out_mxu_zs_enable_b;
  logic in_adam_valid=0,in_adam_clear=0,out_adam_valid,out_adam_clear;
  logic [63:0] in_adam_m_base=0,in_adam_v_base=0,out_adam_m_base,out_adam_v_base;
  logic [31:0] in_adam_lr=0,in_adam_beta1=0,in_adam_beta2=0,in_adam_eps=0;
  logic [31:0] out_adam_lr,out_adam_beta1,out_adam_beta2,out_adam_eps;
  logic in_ready,out_valid;
  logic [2:0] count;
  logic debug_push_seen,debug_head_seen,debug_empty,debug_head_valid;
  logic [63:0] debug_push_address,debug_push_auxiliary;
  logic [63:0] debug_head_address,debug_head_auxiliary;
  logic [15:0] debug_push_length,debug_head_length;
  logic [3:0] debug_push_opcode,debug_head_opcode;
  logic [15:0] debug_head_pointer,debug_tail_pointer,debug_count;
  always #5 clk=~clk;
  ZtpuCommandQueue4 dut(.*);
  task automatic tick; begin @(posedge clk);#1; end endtask
  task automatic enqueue(input [3:0] op,input [7:0] tag,input [7:0] dep);
    begin
      while(!in_ready) tick();
      @(negedge clk);in_valid=1;in_opcode=op;in_addr={56'h0,tag};
      in_aux={56'h0,tag^8'h55};in_length={8'h0,tag};in_tag=tag;in_dep_tag=dep;
      in_src1_base=64'h1122334455667788;in_scalar0=32'ha0a0a0a0;
      in_mxu_valid=1;in_mxu_a_base=64'h1000+tag;in_mxu_k_dim=32'h20+tag;
      in_mxu_rq_enable=1;in_mxu_rq_scale=32'h12345678;in_mxu_mode=3'h5;
      in_adam_valid=1;in_adam_m_base=64'h2000+tag;in_adam_lr=32'h01020304;
      tick();@(negedge clk);in_valid=0;
    end
  endtask
  task automatic wait_valid; integer i; begin
    for(i=0;i<20;i=i+1) begin if(out_valid) return; tick(); end
    $fatal(1,"queue output timeout");
  end endtask
  task automatic consume; begin @(negedge clk);out_ready=1;tick();@(negedge clk);out_ready=0;end endtask
  initial begin
    #1;rst=1;repeat(2)tick();@(negedge clk);rst=0;
    enqueue(4'h7,8'h1,8'h0);wait_valid();
    if(out_opcode!=7 || out_tag!=1 || out_addr!=1 || out_aux!=(8'h1^8'h55) ||
       out_src1_base!=64'h1122334455667788 || out_scalar0!=32'ha0a0a0a0 ||
       !out_mxu_valid || out_mxu_a_base!=64'h1001 || out_mxu_k_dim!=32'h21 ||
       !out_mxu_rq_enable || out_mxu_rq_scale!=32'h12345678 || out_mxu_mode!=5 ||
       !out_adam_valid || out_adam_m_base!=64'h2001 || out_adam_lr!=32'h01020304)
      $fatal(1,"command payload mismatch");
    consume();
    enqueue(4'h8,8'h2,8'h1);repeat(8)tick();
    if(out_valid) $fatal(1,"dependency issued before completion");
    @(negedge clk);done_valid=1;done_tag=1;tick();@(negedge clk);done_valid=0;
    wait_valid();
    if(out_tag!=2 || out_dep_tag!=1 || last_done!=1) $fatal(1,"dependency release mismatch");
    consume();
    enqueue(4'h9,8'h1,8'h0);wait_valid();consume();
    enqueue(4'ha,8'h3,8'h1);repeat(8)tick();
    if(out_valid) $fatal(1,"reused dependency tag released on stale completion");
    @(negedge clk);done_valid=1;done_tag=1;tick();@(negedge clk);done_valid=0;
    wait_valid();
    if(out_tag!=3 || out_dep_tag!=1 || last_done!=1) $fatal(1,"reused tag release mismatch");
    consume();
    $display("command queue: PASS");$finish;
  end
endmodule
""",
    )
    assert "command queue: PASS" in output
