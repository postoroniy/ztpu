from __future__ import annotations

from pathlib import Path

from tools.rtl_test_utils import compile_zlang_top, run_iverilog


def test_ub_adam_q16_updates_state_with_stalls(tmp_path: Path) -> None:
    source = compile_zlang_top(tmp_path, "ZtpuUbAdamQ16", "ub_adam.zhl")
    output = run_iverilog(
        tmp_path,
        [source],
        r"""`timescale 1ns/1ps
module tb;
  logic clk=0,rst=0,start=0,clear_state=0;
  logic [63:0] w_base='hc0,g_base='h40,m_base=0,v_base='h80;
  logic [15:0] length=3;
  logic signed [31:0] learning_rate=655,beta1=58982,beta2=64881,epsilon=7;
  logic busy,done,error,read0_valid,read1_valid,write_valid;
  logic read0_ready=1,read1_ready=1,write_ready=1;
  logic [31:0] b1t,b2t,read0_data,read1_data,write_data;
  logic [63:0] read0_addr,read1_addr,write_addr;
  logic [3:0] write_mask;
  logic [31:0] mem [0:255];
  integer i,n,writes;

  always #5 clk=~clk;
  assign read0_data=mem[read0_addr[9:2]];
  assign read1_data=mem[read1_addr[9:2]];
  always @(posedge clk)
    if(write_valid && write_ready) begin
      mem[write_addr[9:2]]<=write_data;writes=writes+1;
    end

  ZtpuUbAdamQ16 dut(
    .clk,.rst,.start,.clear_state,.w_base,.g_base,.m_base,.v_base,.length,
    .learning_rate,.beta1,.beta2,.epsilon,.busy,.done,.error,.b1t,.b2t,
    .ub_read0_valid(read0_valid),.ub_read0_ready(read0_ready),
    .ub_read0_addr(read0_addr),.ub_read0_data(read0_data),
    .ub_read1_valid(read1_valid),.ub_read1_ready(read1_ready),
    .ub_read1_addr(read1_addr),.ub_read1_data(read1_data),
    .ub_write_valid(write_valid),.ub_write_ready(write_ready),
    .ub_write_addr(write_addr),.ub_write_data(write_data),
    .ub_write_mask(write_mask));

  task automatic cycle(input integer cycle_index);
    begin
      @(negedge clk);start=0;clear_state=0;
      read0_ready=(cycle_index%4)!=1;
      read1_ready=(cycle_index%5)!=2;
      write_ready=(cycle_index%3)!=0;
      @(posedge clk);#1;
    end
  endtask

  task automatic run_step(input clear,input [15:0] words);
    begin
      writes=0;n=0;length=words;
      @(negedge clk);start=1;clear_state=clear;
      read0_ready=1;read1_ready=1;write_ready=1;
      @(posedge clk);#1;start=0;clear_state=0;
      while(!done && n<500) begin cycle(n);n=n+1;end
      if(!done) $fatal(1,"ADAM timeout");
      while(busy && n<520) begin cycle(n);n=n+1;end
      if(busy || error) $fatal(1,"ADAM did not retire cleanly");
    end
  endtask

  initial begin
    for(i=0;i<256;i=i+1) mem[i]=0;
    mem['hc0>>2]=32'h00010000;mem['hc4>>2]=32'hffff8000;
    mem['hc8>>2]=32'h00004000;
    mem['h40>>2]=32'h00002000;mem['h44>>2]=32'hffffc000;
    mem['h48>>2]=32'h00008000;
    #1;rst=1;repeat(2)@(posedge clk);@(negedge clk);rst=0;

    run_step(1,3);
    if(writes!=9 || b1t!=58982 || b2t!=64881 ||
       mem['hc0>>2]!==32'h0000fd6c || mem['hc4>>2]!==32'hffff828e ||
       mem['hc8>>2]!==32'h00003d72 || mem[0]!==32'h00000333 ||
       mem[1]!==32'hfffff99a || mem[2]!==32'h00000ccd ||
       mem['h80>>2]!==32'h0000000a || mem['h84>>2]!==32'h00000029 ||
       mem['h88>>2]!==32'h000000a4)
      $fatal(1,"ADAM step 1 mismatch");

    run_step(0,3);
    if(writes!=9 || b1t!=53083 || b2t!=64233 ||
       mem['hc0>>2]!==32'h0000fada || mem['hc4>>2]!==32'hffff851a ||
       mem['hc8>>2]!==32'h00003ae3 || mem[0]!==32'h00000614 ||
       mem[1]!==32'hfffff3d8 || mem[2]!==32'h00001852 ||
       mem['h80>>2]!==32'h00000014 || mem['h84>>2]!==32'h00000052 ||
       mem['h88>>2]!==32'h00000146)
      $fatal(1,"ADAM step 2 mismatch");

    run_step(0,0);
    if(writes!=0) $fatal(1,"zero-length ADAM generated writes");
    $display("UB ADAM Q16: PASS");$finish;
  end
endmodule
""",
    )
    assert "UB ADAM Q16: PASS" in output
