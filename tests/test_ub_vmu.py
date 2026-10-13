from __future__ import annotations

from pathlib import Path

from tools.rtl_test_utils import compile_zlang_top, run_iverilog


def test_ub_vmu_elementwise_q16_operations_and_stalls(tmp_path: Path) -> None:
    source = compile_zlang_top(
        tmp_path, "ZtpuUbVmuElementwiseQ16", "ub_vmu.zhl"
    )
    output = run_iverilog(
        tmp_path,
        [source],
        r"""`timescale 1ns/1ps
module tb;
  logic clk=0,rst=0,start=0,enable=1;
  logic [3:0] op=0;
  logic [63:0] src0_base=0,src1_base='h40,dst_base='h80;
  logic [15:0] length=4;
  logic signed [31:0] scalar0=0,scalar1=0;
  logic [31:0] scalar2=0,scalar3=0;
  logic busy,done,error;
  logic ub_read0_valid,ub_read0_ready=1;
  logic [63:0] ub_read0_addr;
  logic [31:0] ub_read0_data;
  logic ub_read1_valid,ub_read1_ready=1;
  logic [63:0] ub_read1_addr;
  logic [31:0] ub_read1_data;
  logic ub_write_valid,ub_write_ready=1;
  logic [63:0] ub_write_addr;
  logic [31:0] ub_write_data;
  logic [3:0] ub_write_mask;
  logic [31:0] mem [0:255];
  integer i,n,writes;

  always #5 clk=~clk;
  assign ub_read0_data=mem[ub_read0_addr[9:2]];
  assign ub_read1_data=mem[ub_read1_addr[9:2]];
  always @(posedge clk)
    if(ub_write_valid && ub_write_ready) begin
      mem[ub_write_addr[9:2]]<=ub_write_data;
      writes=writes+1;
    end

  ZtpuUbVmuElementwiseQ16 dut(.*);

  task automatic tick; begin @(posedge clk);#1; end endtask
  task automatic clear_dst;
    begin for(i=0;i<4;i=i+1) mem[('h80>>2)+i]=32'hdeadbeef; end
  endtask
  task automatic launch(input [3:0] operation,input signed [31:0] scale);
    begin
      op=operation;scalar0=scale;writes=0;
      @(negedge clk);start=1;ub_read0_ready=1;ub_read1_ready=1;
      ub_write_ready=1;#1;@(posedge clk);#1;start=0;
    end
  endtask
  task automatic run_to_done;
    begin
      n=0;
      while(!done && n<100) begin
        @(negedge clk);start=0;
        ub_read0_ready=(n%4)!=1;
        ub_read1_ready=(n%5)!=2;
        ub_write_ready=(n%3)!=0;
        #1;@(posedge clk);#1;n=n+1;
      end
      if(!done || error) $fatal(1,"VMU timeout or error");
      ub_read0_ready=1;ub_read1_ready=1;ub_write_ready=1;tick();
    end
  endtask
  task automatic expect4(
    input [31:0] a,input [31:0] b,input [31:0] c,input [31:0] d
  );
    begin
      if(mem['h80>>2]!==a || mem['h84>>2]!==b ||
         mem['h88>>2]!==c || mem['h8c>>2]!==d) begin
        $display("got=%h,%h,%h,%h",mem['h80>>2],mem['h84>>2],
          mem['h88>>2],mem['h8c>>2]);
        $fatal(1,"VMU result mismatch");
      end
      if(writes!=4) $fatal(1,"VMU write count mismatch %0d",writes);
    end
  endtask

  initial begin
    for(i=0;i<256;i=i+1) mem[i]=0;
    mem['h00>>2]=32'h00004000;mem['h04>>2]=32'hffff8000;
    mem['h08>>2]=32'h7fffffff;mem['h0c>>2]=32'h80000000;
    mem['h40>>2]=32'h0000c000;mem['h44>>2]=32'h00004000;
    mem['h48>>2]=32'h00000001;mem['h4c>>2]=32'hffffffff;
    #1;rst=1;repeat(2)tick();@(negedge clk);rst=0;

    clear_dst();launch(9,0);run_to_done();
    expect4(32'h00004000,32'h00000000,32'h7fffffff,32'h00000000);

    clear_dst();launch(11,0);run_to_done();
    expect4(32'h00010000,32'hffffc000,32'h7fffffff,32'h80000000);

    clear_dst();launch(12,32'h00008000);run_to_done();
    expect4(32'h00002000,32'hffffc000,32'h40000000,32'hc0000000);

    clear_dst();launch(13,0);run_to_done();
    expect4(32'h0000c000,32'h00000000,32'h00000001,32'h00000000);

    clear_dst();launch(15,0);run_to_done();
    if(writes!=0 || mem['h80>>2]!==32'hdeadbeef)
      $fatal(1,"unsupported VMU operation generated traffic");

    $display("UB VMU elementwise Q16: PASS");$finish;
  end
endmodule
""",
    )
    assert "UB VMU elementwise Q16: PASS" in output


def test_ub_vmu_q16_to_q8_pack_and_stalls(tmp_path: Path) -> None:
    source = compile_zlang_top(tmp_path, "ZtpuUbVmuQ16", "ub_vmu.zhl")
    output = run_iverilog(
        tmp_path,
        [source],
        r"""`timescale 1ns/1ps
module tb;
  logic clk=0,rst=0,start=0,enable=1;
  logic [3:0] op=14;
  logic [63:0] src0_base=0,src1_base=0,dst_base='h40;
  logic [15:0] length=2;
  logic signed [31:0] scalar0=1,scalar1=0;
  logic [31:0] scalar2=4,scalar3=(8<<8)|4;
  logic busy,done,error;
  logic ub_read0_valid,ub_read0_ready=1;
  logic [63:0] ub_read0_addr;
  logic [31:0] ub_read0_data;
  logic ub_read1_valid,ub_read1_ready=1;
  logic [63:0] ub_read1_addr;
  logic [31:0] ub_read1_data=0;
  logic ub_write_valid,ub_write_ready=1;
  logic [63:0] ub_write_addr;
  logic [31:0] ub_write_data;
  logic [3:0] ub_write_mask;
  logic [31:0] mem [0:63];
  integer i,n,writes=0;

  always #5 clk=~clk;
  assign ub_read0_data=mem[ub_read0_addr[7:2]];
  always @(posedge clk)
    if(ub_write_valid && ub_write_ready) begin
      mem[ub_write_addr[7:2]]<=ub_write_data;writes=writes+1;
    end
  ZtpuUbVmuQ16 dut(.*);
  initial begin
    for(i=0;i<64;i=i+1) mem[i]=0;
    mem[0]=37;mem[1]=74;mem[2]=32'hffffffce;mem[3]=32'hffffffef;
    mem[4]=32'hffffffe8;mem[5]=24;mem[6]=32'hffffffa7;
    mem[7]=32'hffffffc4;
    #1;rst=1;repeat(2)@(posedge clk);@(negedge clk);rst=0;
    start=1;@(posedge clk);#1;start=0;n=0;
    while(!done && n<100) begin
      @(negedge clk);ub_read0_ready=(n%4)!=1;ub_write_ready=(n%3)!=0;
      @(posedge clk);#1;n=n+1;
    end
    if(!done || error) $fatal(1,"Q8 pack timeout or error");
    ub_write_ready=1;@(posedge clk);#1;
    if(mem['h40>>2]!==32'ha7e8ce25 || mem['h44>>2]!==32'hc418ef4a)
      $fatal(1,"Q8 pack result mismatch %h %h",mem['h40>>2],mem['h44>>2]);
    if(writes!=2 || ub_write_mask!=15 || ub_read1_valid)
      $fatal(1,"Q8 pack protocol mismatch");
    $display("UB VMU Q16-to-Q8 pack: PASS");$finish;
  end
endmodule
""",
    )
    assert "UB VMU Q16-to-Q8 pack: PASS" in output


def test_ub_vmu_reduce_max_keeps_signed_register_comparison(
    tmp_path: Path,
) -> None:
    source = compile_zlang_top(tmp_path, "ZtpuUbVmuQ16", "ub_vmu.zhl")
    output = run_iverilog(
        tmp_path,
        [source],
        r"""`timescale 1ns/1ps
module tb;
  logic clk=0,rst=0,start=0,enable=1;
  logic [3:0] op=3;
  logic [63:0] src0_base=0,src1_base=0,dst_base='h40;
  logic [15:0] length=2;
  logic signed [31:0] scalar0=0,scalar1=0;
  logic [31:0] scalar2=0,scalar3=0;
  logic busy,done,error;
  logic ub_read0_valid,ub_read0_ready=1;
  logic [63:0] ub_read0_addr;
  logic [31:0] ub_read0_data;
  logic ub_read1_valid,ub_read1_ready=1;
  logic [63:0] ub_read1_addr;
  logic [31:0] ub_read1_data=0;
  logic ub_write_valid,ub_write_ready=1;
  logic [63:0] ub_write_addr;
  logic [31:0] ub_write_data;
  logic [3:0] ub_write_mask;
  logic [31:0] mem [0:31];
  integer i,cycles,writes=0;

  always #5 clk=~clk;
  assign ub_read0_data=mem[ub_read0_addr[6:2]];
  always @(posedge clk)
    if(ub_write_valid && ub_write_ready) begin
      mem[ub_write_addr[6:2]]<=ub_write_data;
      writes=writes+1;
    end

  ZtpuUbVmuQ16 dut(.*);
  task automatic tick; begin @(posedge clk);#1; end endtask

  initial begin
    for(i=0;i<32;i=i+1) mem[i]=0;
    // This ordering catches an unsigned comparison of the held maximum:
    // signed -0.5 must be replaced by signed +1.5.
    mem[0]=32'hffff8000;
    mem[1]=32'h00018000;
    #1;rst=1;repeat(2)tick();@(negedge clk);rst=0;
    start=1;tick();@(negedge clk);start=0;

    cycles=0;
    while(writes==0 && cycles<32) begin tick();cycles=cycles+1;end
    if(writes!=1 || mem['h40>>2]!==32'h00018000)
      $fatal(1,"signed REDUCE_MAX mismatch writes=%0d value=%h",
        writes,mem['h40>>2]);
    if(error || ub_write_mask!=15 || ub_read1_valid)
      $fatal(1,"signed REDUCE_MAX protocol mismatch");
    $display("UB VMU signed REDUCE_MAX: PASS");$finish;
  end
endmodule
""",
    )
    assert "UB VMU signed REDUCE_MAX: PASS" in output
