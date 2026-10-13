from __future__ import annotations

from pathlib import Path

from tools.rtl_test_utils import compile_zlang_top, run_iverilog


def test_ub_mxu_q16_compute_stall_spill_restore(tmp_path: Path) -> None:
    source = compile_zlang_top(
        tmp_path, "ZtpuUbMxuCompute2x2Q16", "ub_mxu_compute.zhl"
    )
    output = run_iverilog(
        tmp_path,
        [source],
        r"""`timescale 1ns/1ps
module tb;
  logic clk=0,rst=0,start=0;
  logic [63:0] a_base=0,b_base=0,c_base=0,acc_base=0;
  logic [63:0] a_stride=0,b_stride=0;
  logic a_transpose=0,b_transpose=0;
  logic [15:0] k_dim=0;
  logic [2:0] mode=3;
  logic accum_enable=0,acc_clear=0,spill_enable=0,restore_enable=0;
  logic busy,done;
  logic ub_read_a_valid,ub_read_a_ready=1;
  logic [63:0] ub_read_a_addr;
  logic [31:0] ub_read_a_data;
  logic ub_read_b_valid,ub_read_b_ready=1;
  logic [63:0] ub_read_b_addr;
  logic [31:0] ub_read_b_data;
  logic ub_write_valid,ub_write_ready=1;
  logic [63:0] ub_write_addr;
  logic [31:0] ub_write_data;
  logic [3:0] ub_write_mask;
  logic [31:0] mem [0:255];
  integer i,cycles;

  always #5 clk=~clk;
  assign ub_read_a_data=mem[ub_read_a_addr[9:2]];
  assign ub_read_b_data=mem[ub_read_b_addr[9:2]];
  always @(posedge clk)
    if (ub_write_valid && ub_write_ready) mem[ub_write_addr[9:2]] <= ub_write_data;

  ZtpuUbMxuCompute2x2Q16 dut(.*);

  task automatic tick; begin @(posedge clk);#1; end endtask
  task automatic launch;
    begin start=1;tick();start=0; end
  endtask
  task automatic wait_done;
    begin
      cycles=0;
      while(!done && cycles<200) begin
        ub_read_a_ready=(cycles%4)!=1;
        ub_read_b_ready=(cycles%5)!=2;
        ub_write_ready=(cycles%3)!=0;
        tick();cycles=cycles+1;
      end
      if(!done) $fatal(1,"compute timeout");
      ub_read_a_ready=1;ub_read_b_ready=1;ub_write_ready=1;
      tick();
    end
  endtask

  initial begin
    for(i=0;i<256;i=i+1) mem[i]=0;
    // A = [[0.5,-0.25],[0.75,0.125]], row stride 8 bytes.
    mem['h00>>2]=32'h00008000;mem['h04>>2]=32'hffffc000;
    mem['h08>>2]=32'h0000c000;mem['h0c>>2]=32'h00002000;
    // B = [[0.25,-0.5],[0.5,0.25]], row stride 8 bytes.
    mem['h40>>2]=32'h00004000;mem['h44>>2]=32'hffff8000;
    mem['h48>>2]=32'h00008000;mem['h4c>>2]=32'h00004000;

    #1;rst=1;repeat(2)tick();@(negedge clk);rst=0;
    a_base='h00;b_base='h40;c_base='h80;acc_base='hc0;
    a_stride=8;b_stride=8;k_dim=2;mode=3;acc_clear=1;
    launch();acc_clear=0;wait_done();
    if(mem['h80>>2]!==32'h00000000 || mem['h84>>2]!==32'hffffb000 ||
       mem['h88>>2]!==32'h00004000 || mem['h8c>>2]!==32'hffffa800) begin
      $display("got C=%h,%h,%h,%h",mem['h80>>2],mem['h84>>2],mem['h88>>2],mem['h8c>>2]);
      $fatal(1,"Q16 matrix result mismatch");
    end

    // Spill the computed accumulator, clear it, then restore it.
    k_dim=0;spill_enable=1;launch();spill_enable=0;wait_done();
    acc_clear=1;launch();acc_clear=0;wait_done();
    restore_enable=1;launch();restore_enable=0;wait_done();

    // Add a zero product. The restored accumulators must be written unchanged.
    a_base='h100;b_base='h120;c_base='ha0;
    a_stride=4;b_stride=4;k_dim=1;accum_enable=1;
    launch();wait_done();accum_enable=0;
    if(mem['ha0>>2]!==32'h00000000 || mem['ha4>>2]!==32'hffffb000 ||
       mem['ha8>>2]!==32'h00004000 || mem['hac>>2]!==32'hffffa800)
      $fatal(1,"spill/restore accumulator mismatch");

    $display("UB MXU Q16 compute: PASS");$finish;
  end
endmodule
""",
    )
    assert "UB MXU Q16 compute: PASS" in output


def test_ub_mxu_q16_compute_4x4_matrix_and_accumulator_roundtrip(
    tmp_path: Path,
) -> None:
    source = compile_zlang_top(
        tmp_path, "ZtpuUbMxuCompute4x4Q16", "ub_mxu_compute.zhl"
    )
    output = run_iverilog(
        tmp_path,
        [source],
        r"""`timescale 1ns/1ps
module tb;
  logic clk=0,rst=0,start=0;
  logic [63:0] a_base='h00,b_base='h80,c_base='h100,acc_base='h180;
  logic [63:0] a_stride=16,b_stride=16;
  logic a_transpose=0,b_transpose=0;
  logic [15:0] k_dim=4;
  logic [2:0] mode=3;
  logic accum_enable=0,acc_clear=1,spill_enable=0,restore_enable=0;
  logic busy,done;
  logic ub_read_a_valid,ub_read_a_ready=1;
  logic [63:0] ub_read_a_addr;
  logic [31:0] ub_read_a_data;
  logic ub_read_b_valid,ub_read_b_ready=1;
  logic [63:0] ub_read_b_addr;
  logic [31:0] ub_read_b_data;
  logic ub_write_valid,ub_write_ready=1;
  logic [63:0] ub_write_addr;
  logic [31:0] ub_write_data;
  logic [3:0] ub_write_mask;
  logic [31:0] mem [0:255];
  integer i,cycles,writes;

  always #5 clk=~clk;
  assign ub_read_a_data=mem[ub_read_a_addr[9:2]];
  assign ub_read_b_data=mem[ub_read_b_addr[9:2]];
  always @(posedge clk)
    if(ub_write_valid && ub_write_ready) begin
      mem[ub_write_addr[9:2]]<=ub_write_data;writes=writes+1;
    end
  ZtpuUbMxuCompute4x4Q16 dut(.*);

  task automatic tick; begin @(posedge clk);#1;end endtask
  task automatic launch; begin start=1;tick();start=0;end endtask
  task automatic wait_done; begin
    cycles=0;
    while(!done && cycles<800) begin
      ub_read_a_ready=(cycles%4)!=1;
      ub_read_b_ready=(cycles%5)!=2;
      ub_write_ready=(cycles%3)!=0;
      tick();cycles=cycles+1;
    end
    if(!done) $fatal(1,"4x4 Q16 compute timeout");
    ub_read_a_ready=1;ub_read_b_ready=1;ub_write_ready=1;tick();
  end endtask

  initial begin
    writes=0;for(i=0;i<256;i=i+1)mem[i]=0;
    // Diagonal A scales each row of B by 1, 1/2, -1, and 1/4.
    mem[0]=32'h00010000;mem[5]=32'h00008000;
    mem[10]=32'hffff0000;mem[15]=32'h00004000;
    mem[32]=32'h00004000;mem[33]=32'hffff8000;
    mem[34]=32'h0000c000;mem[35]=32'h00010000;
    mem[36]=32'h00010000;mem[37]=32'h00008000;
    mem[38]=32'hffffc000;mem[39]=32'h00002000;
    mem[40]=32'hffff8000;mem[41]=32'h00004000;
    mem[42]=32'h00010000;mem[43]=32'hffff0000;
    mem[44]=32'h00008000;mem[45]=32'hffff8000;
    mem[46]=32'h00004000;mem[47]=32'hffffc000;

    #1;rst=1;repeat(2)tick();@(negedge clk);rst=0;
    launch();acc_clear=0;wait_done();
    if(writes!=16) $fatal(1,"4x4 write count=%0d",writes);
    if(mem[64]!==32'h00004000 || mem[65]!==32'hffff8000 ||
       mem[66]!==32'h0000c000 || mem[67]!==32'h00010000 ||
       mem[68]!==32'h00008000 || mem[69]!==32'h00004000 ||
       mem[70]!==32'hffffe000 || mem[71]!==32'h00001000 ||
       mem[72]!==32'h00008000 || mem[73]!==32'hffffc000 ||
       mem[74]!==32'hffff0000 || mem[75]!==32'h00010000 ||
       mem[76]!==32'h00002000 || mem[77]!==32'hffffe000 ||
       mem[78]!==32'h00001000 || mem[79]!==32'hfffff000)
      $fatal(1,"4x4 Q16 matrix result mismatch");

    k_dim=0;spill_enable=1;launch();spill_enable=0;wait_done();
    acc_clear=1;launch();acc_clear=0;wait_done();
    restore_enable=1;launch();restore_enable=0;wait_done();
    a_base='h200;b_base='h240;c_base='h140;k_dim=1;accum_enable=1;
    launch();wait_done();
    for(i=0;i<16;i=i+1)
      if(mem[80+i]!==mem[64+i]) $fatal(1,"4x4 accumulator word %0d mismatch",i);
    $display("UB MXU 4x4 Q16 compute: PASS");$finish;
  end
endmodule
""",
    )
    assert "UB MXU 4x4 Q16 compute: PASS" in output
