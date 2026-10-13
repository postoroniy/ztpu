from __future__ import annotations

from pathlib import Path

from tools.rtl_test_utils import compile_zlang_top, run_iverilog


def test_command_descriptor_dma_decodes_unions_and_errors(tmp_path: Path) -> None:
    source = compile_zlang_top(
        tmp_path, "ZtpuCommandDescriptorDma64x24", "cmd_dma.zhl"
    )
    output = run_iverilog(
        tmp_path,
        [source],
        r"""`timescale 1ns/1ps
module tb;
  logic clk=0,rst=0,start=0,clear=0;
  logic [63:0] base='h8000;
  logic [23:0] count=3;
  logic busy,done,error;
  logic [3:0] error_code;
  logic [23:0] fetched_count;
  logic axi_ar_valid,axi_ar_ready=0;
  logic [63:0] axi_ar_addr;
  logic [7:0] axi_ar_len;
  logic [2:0] axi_ar_size;
  logic axi_r_valid=0,axi_r_ready,axi_r_last=0;
  logic [31:0] axi_r_data=0;
  logic [1:0] axi_r_resp=0;
  logic out_valid,out_ready=0;
  logic [3:0] out_opcode;
  logic [63:0] out_addr,out_aux,out_src1_base;
  logic [15:0] out_length;
  logic [7:0] out_tag,out_dep_tag;
  logic [31:0] out_scalar0,out_scalar1,out_scalar2,out_scalar3;
  logic out_mxu_valid;
  logic [63:0] out_mxu_a_base,out_mxu_b_base;
  logic [63:0] out_mxu_c_base,out_mxu_acc_base;
  logic [31:0] out_mxu_a_stride,out_mxu_b_stride,out_mxu_k_dim;
  logic out_mxu_accum_en,out_mxu_acc_clear;
  logic out_mxu_spill_en,out_mxu_restore_en,out_mxu_rq_enable;
  logic [31:0] out_mxu_rq_scale;
  logic [7:0] out_mxu_rq_shift;
  logic [31:0] out_mxu_rq_zero;
  logic [2:0] out_mxu_mode;
  logic out_mxu_a_transpose,out_mxu_b_transpose;
  logic out_mxu_zs_enable_a,out_mxu_zs_enable_b;
  logic out_adam_valid,out_adam_clear;
  logic [63:0] out_adam_m_base,out_adam_v_base;
  logic [31:0] out_adam_lr,out_adam_beta1,out_adam_beta2,out_adam_eps;
  logic [31:0] words [0:47];
  integer i,j,cycles;

  always #5 clk=~clk;
  ZtpuCommandDescriptorDma64x24 dut(.*);
  task automatic tick; begin @(posedge clk);#1; end endtask
  task automatic launch;
    begin @(negedge clk);start=1;tick();@(negedge clk);start=0;end
  endtask
  task automatic pulse_clear;
    begin @(negedge clk);clear=1;tick();@(negedge clk);clear=0;end
  endtask
  task automatic serve(input integer descriptor);
    begin
      cycles=0;
      while(!axi_ar_valid && cycles<20) begin tick();cycles=cycles+1;end
      if(!axi_ar_valid || axi_ar_addr!==('h8000+descriptor*64) ||
         axi_ar_len!=15 || axi_ar_size!=2)
        $fatal(1,"descriptor AR mismatch index=%0d",descriptor);
      @(negedge clk);axi_ar_ready=1;tick();
      @(negedge clk);axi_ar_ready=0;
      for(j=0;j<16;j=j+1) begin
        axi_r_valid=1;axi_r_data=words[descriptor*16+j];axi_r_last=(j==15);
        tick();
      end
      @(negedge clk);axi_r_valid=0;axi_r_last=0;
      cycles=0;
      while(!out_valid && cycles<20) begin tick();cycles=cycles+1;end
      if(!out_valid) $fatal(1,"descriptor output timeout");
    end
  endtask
  task automatic accept_output;
    begin
      tick();
      if(!out_valid) $fatal(1,"descriptor did not hold under backpressure");
      @(negedge clk);out_ready=1;tick();@(negedge clk);out_ready=0;
    end
  endtask

  initial begin
    for(i=0;i<48;i=i+1) words[i]=0;
    // Generic/DCOPY union.
    words[0]=32'h00060708;words[1]=64;
    words[2]=32'h87654320;words[3]=32'h12345678;
    words[4]=32'h00000200;words[5]=0;
    words[6]=32'h11223344;words[7]=32'habcdef00;
    words[8]=3;words[9]=128;words[10]=256;words[11]=17;
    // MXU union.
    words[16]=32'h00070805;words[17]=4;
    words[18]=4;words[19]=1;words[20]=8;words[21]=2;
    words[22]=12;words[23]=3;words[24]=16;words[25]=4;
    words[26]=16;words[27]=32;words[28]=4;
    words[29]=32'h001ec27f;words[30]=32'h00001234;words[31]=32'hfffffffe;
    // ADAM union.
    words[32]=32'h00080906;words[33]=12;
    words[34]=32'h00000100;words[35]=0;
    words[36]=32'h00000200;words[37]=0;
    words[38]=20;words[39]=5;words[40]=24;words[41]=6;
    words[42]=1;words[43]=2;words[44]=3;words[45]=4;words[46]=3;

    #1;rst=1;repeat(2)tick();@(negedge clk);rst=0;
    launch();

    serve(0);
    if(out_opcode!=8 || out_tag!=7 || out_dep_tag!=6 || out_length!=64 ||
       out_addr!==64'h1234567887654320 || out_aux!=64'h200 ||
       out_src1_base!==64'habcdef0011223344 || out_scalar0!=3 ||
       out_scalar1!=128 || out_scalar2!=256 || out_scalar3!=17 ||
       out_mxu_valid || out_adam_valid)
      $fatal(1,"generic descriptor decode mismatch");
    accept_output();

    serve(1);
    if(out_opcode!=5 || out_tag!=8 || out_dep_tag!=7 || !out_mxu_valid ||
       out_mxu_a_base!==64'h0000000100000004 ||
       out_mxu_b_base!==64'h0000000200000008 ||
       out_mxu_c_base!==64'h000000030000000c ||
       out_mxu_acc_base!==64'h0000000400000010 ||
       out_mxu_a_stride!=16 || out_mxu_b_stride!=32 || out_mxu_k_dim!=4 ||
       !out_mxu_accum_en || !out_mxu_acc_clear || !out_mxu_spill_en ||
       !out_mxu_restore_en || !out_mxu_rq_enable || out_mxu_rq_shift!=9 ||
       out_mxu_mode!=3 || !out_mxu_a_transpose || !out_mxu_b_transpose ||
       !out_mxu_zs_enable_a || !out_mxu_zs_enable_b ||
       out_mxu_rq_scale!=32'h1234 || out_mxu_rq_zero!=32'hfffffffe)
      $fatal(1,"MXU descriptor decode mismatch");
    accept_output();

    serve(2);
    if(out_opcode!=6 || out_tag!=9 || out_dep_tag!=8 || !out_adam_valid ||
       !out_adam_clear || out_addr!=64'h100 || out_aux!=64'h200 ||
       out_adam_m_base!==64'h0000000500000014 ||
       out_adam_v_base!==64'h0000000600000018 || out_adam_lr!=1 ||
       out_adam_beta1!=2 || out_adam_beta2!=3 || out_adam_eps!=4)
      $fatal(1,"ADAM descriptor decode mismatch");
    accept_output();
    if(busy || !done || error || fetched_count!=3)
      $fatal(1,"descriptor completion status mismatch");

    pulse_clear();
    if(done || error || error_code!=0) $fatal(1,"clear mismatch");
    count=0;base='h8000;launch();
    if(busy || !done || error || fetched_count!=0 || axi_ar_valid)
      $fatal(1,"zero-count behavior mismatch");

    count=1;base='h8004;launch();
    if(busy || done || !error || error_code!=1 || axi_ar_valid)
      $fatal(1,"alignment error mismatch");

    pulse_clear();base='h8000;launch();
    while(!axi_ar_valid) tick();
    @(negedge clk);axi_ar_ready=1;tick();@(negedge clk);axi_ar_ready=0;
    axi_r_valid=1;axi_r_resp=2;axi_r_last=0;tick();
    @(negedge clk);axi_r_valid=0;axi_r_resp=0;
    if(busy || !error || error_code!=2) $fatal(1,"AXI error mismatch");

    pulse_clear();launch();
    while(!axi_ar_valid) tick();
    @(negedge clk);axi_ar_ready=1;tick();@(negedge clk);axi_ar_ready=0;
    axi_r_valid=1;axi_r_data=words[0];axi_r_last=1;tick();
    @(negedge clk);axi_r_valid=0;axi_r_last=0;
    if(busy || !error || error_code!=3) $fatal(1,"RLAST error mismatch");

    $display("Command descriptor DMA: PASS");$finish;
  end
endmodule
""",
    )
    assert "Command descriptor DMA: PASS" in output
