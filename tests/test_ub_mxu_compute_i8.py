from pathlib import Path

from tools.rtl_test_utils import compile_zlang_top, run_iverilog


def test_ub_mxu_i8_compute_requant_and_zero_skip(tmp_path: Path) -> None:
    source = compile_zlang_top(
        tmp_path, "ZtpuUbMxuCompute4x4I8", "ub_mxu_compute.zhl"
    )
    output = run_iverilog(
        tmp_path,
        [source],
        r"""`timescale 1ns/1ps
module tb;
  logic clk=0,rst=0,start=0;
  logic [63:0] a_base=0,b_base='h40,c_base='h80,acc_base='hc0;
  logic [63:0] a_stride=0,b_stride=0;
  logic a_transpose=0,b_transpose=0;
  logic [15:0] k_dim=2;logic [2:0] mode=0;
  logic accum_enable=0,acc_clear=1,spill_enable=0,restore_enable=0;
  logic rq_enable=1;logic signed [31:0] rq_scale=131072,rq_zero=0;
  logic [7:0] rq_shift=16;logic zs_enable_a=1,zs_enable_b=1;
  logic busy,done,arv,brv,wv;
  logic [63:0] ara,bra,wa;logic [31:0] wd;logic [3:0] wm;
  logic [31:0] steps,total,active,skipped;
  logic ardy=1,brdy=1,wrdy=1;logic [31:0] mem[0:255];
  wire [31:0] ard=mem[ara[9:2]],brd=mem[bra[9:2]];
  integer i,cycles,writes;
  always #5 clk=~clk;
  always @(posedge clk)if(wv&&wrdy)begin mem[wa[9:2]]<=wd;writes=writes+1;end

  ZtpuUbMxuCompute4x4I8 dut(
    .clk,.rst,.start,.a_base,.b_base,.c_base,.acc_base,.a_stride,.b_stride,
    .a_transpose,.b_transpose,.k_dim,.mode,.accum_enable,.acc_clear,
    .spill_enable,.restore_enable,.rq_enable,.rq_scale,.rq_shift,.rq_zero,
    .zs_enable_a,.zs_enable_b,.busy,.done,.zs_steps(steps),
    .zs_total_macs(total),.zs_active_macs(active),.zs_skipped_macs(skipped),
    .ub_read_a_valid(arv),.ub_read_a_ready(ardy),.ub_read_a_addr(ara),
    .ub_read_a_data(ard),.ub_read_b_valid(brv),.ub_read_b_ready(brdy),
    .ub_read_b_addr(bra),.ub_read_b_data(brd),.ub_write_valid(wv),
    .ub_write_ready(wrdy),.ub_write_addr(wa),.ub_write_data(wd),
    .ub_write_mask(wm));

  initial begin
    writes=0;cycles=0;for(i=0;i<256;i=i+1)mem[i]=0;
    mem[0]=32'h01010101;mem[1]=32'h00010101;
    mem[16]=32'h01010101;mem[17]=32'h01010101;
    #1;rst=1;repeat(2)@(posedge clk);@(negedge clk);rst=0;start=1;
    @(posedge clk);@(negedge clk);start=0;acc_clear=0;
    while(!done&&cycles<200)begin @(posedge clk);cycles=cycles+1;end
    if(!done)$fatal(1,"packed I8 compute timeout");
    @(posedge clk);#1;
    if(writes!=16)$fatal(1,"write count=%0d",writes);
    // Requant scale 2.0 makes the first three rows 4 and the zero lane row 2.
    for(i=32;i<44;i=i+1)if(mem[i]!==32'd4)$fatal(1,"result[%0d]=%h",i-32,mem[i]);
    for(i=44;i<48;i=i+1)if(mem[i]!==32'd2)$fatal(1,"result[%0d]=%h",i-32,mem[i]);
    if(steps!==2||total!==32||active!==28||skipped!==4)
      $fatal(1,"zero-skip counters %0d %0d %0d %0d",steps,total,active,skipped);
    $display("UB MXU packed I8 direct: PASS");$finish;
  end
endmodule
""",
    )
    assert "UB MXU packed I8 direct: PASS" in output


def test_ub_mxu_w4a8_low_and_high_nibble_modes(tmp_path: Path) -> None:
    source = compile_zlang_top(
        tmp_path, "ZtpuUbMxuCompute4x4I8", "ub_mxu_compute.zhl"
    )
    output = run_iverilog(
        tmp_path,
        [source],
        r"""`timescale 1ns/1ps
module tb;
  logic clk=0,rst=0,start=0;
  logic [63:0] a_base=0,b_base='h40,c_base='h80,acc_base='h100;
  logic [63:0] a_stride=0,b_stride=0;
  logic a_transpose=0,b_transpose=0;
  logic [15:0] k_dim=1;logic [2:0] mode=4;
  logic accum_enable=0,acc_clear=1,spill_enable=0,restore_enable=0;
  logic rq_enable=0;logic signed [31:0] rq_scale=0,rq_zero=0;
  logic [7:0] rq_shift=0;logic zs_enable_a=0,zs_enable_b=0;
  logic busy,done,arv,brv,wv;
  logic [63:0] ara,bra,wa;logic [31:0] wd;logic [3:0] wm;
  logic [31:0] steps,total,active,skipped;
  logic ardy=1,brdy=1,wrdy=1;logic [31:0] mem[0:255];
  wire [31:0] ard=mem[ara[9:2]],brd=mem[bra[9:2]];
  integer i,cycles,writes;
  always #5 clk=~clk;
  always @(posedge clk)if(wv&&wrdy)begin mem[wa[9:2]]<=wd;writes=writes+1;end

  ZtpuUbMxuCompute4x4I8 dut(
    .clk,.rst,.start,.a_base,.b_base,.c_base,.acc_base,.a_stride,.b_stride,
    .a_transpose,.b_transpose,.k_dim,.mode,.accum_enable,.acc_clear,
    .spill_enable,.restore_enable,.rq_enable,.rq_scale,.rq_shift,.rq_zero,
    .zs_enable_a,.zs_enable_b,.busy,.done,.zs_steps(steps),
    .zs_total_macs(total),.zs_active_macs(active),.zs_skipped_macs(skipped),
    .ub_read_a_valid(arv),.ub_read_a_ready(ardy),.ub_read_a_addr(ara),
    .ub_read_a_data(ard),.ub_read_b_valid(brv),.ub_read_b_ready(brdy),
    .ub_read_b_addr(bra),.ub_read_b_data(brd),.ub_write_valid(wv),
    .ub_write_ready(wrdy),.ub_write_addr(wa),.ub_write_data(wd),
    .ub_write_mask(wm));

  task automatic run_mode(input logic [2:0] selected_mode,
                          input logic [63:0] selected_c_base);
    begin
      @(negedge clk);mode=selected_mode;c_base=selected_c_base;
      acc_clear=1;start=1;
      @(posedge clk);@(negedge clk);start=0;acc_clear=0;
      cycles=0;
      while(!done&&cycles<200)begin @(posedge clk);cycles=cycles+1;end
      if(!done)$fatal(1,"W4A8 mode %0d timeout",selected_mode);
      @(posedge clk);#1;
    end
  endtask

  initial begin
    writes=0;cycles=0;for(i=0;i<256;i=i+1)mem[i]=0;
    mem[0]=32'h01010101;
    // Low nibbles are 1,2,3,4; high nibbles are -1,-2,-3,-4.
    mem[16]=32'hcdef4321;
    #1;rst=1;repeat(2)@(posedge clk);@(negedge clk);rst=0;
    run_mode(4,64'h80);
    if(writes!=16)$fatal(1,"low-half write count=%0d",writes);
    for(i=0;i<4;i=i+1)begin
      if(mem[32+4*i]!==32'd1||mem[33+4*i]!==32'd2||
         mem[34+4*i]!==32'd3||mem[35+4*i]!==32'd4)
        $fatal(1,"low-half row %0d mismatch",i);
    end
    run_mode(5,64'hc0);
    if(writes!=32)$fatal(1,"high-half write count=%0d",writes);
    for(i=0;i<4;i=i+1)begin
      if(mem[48+4*i]!==32'hffffffff||mem[49+4*i]!==32'hfffffffe||
         mem[50+4*i]!==32'hfffffffd||mem[51+4*i]!==32'hfffffffc)
        $fatal(1,"high-half row %0d mismatch",i);
    end
    $display("UB MXU W4A8 low/high direct: PASS");$finish;
  end
endmodule
""",
    )
    assert "UB MXU W4A8 low/high direct: PASS" in output
