from __future__ import annotations

from pathlib import Path

from tools.rtl_test_utils import compile_zlang_top, run_iverilog


def test_ub_dcopy_sequences_rows_zero_size_and_errors(tmp_path: Path) -> None:
    source = compile_zlang_top(tmp_path, "ZtpuUbDcopy64x32", "ub_dcopy.zhl")
    output = run_iverilog(
        tmp_path,
        [source],
        r"""`timescale 1ns/1ps
module tb;
  logic clk=0,rst=0,start=0;
  logic [63:0] source_base='h1004,destination_base='h2000,ub_base='h40;
  logic [15:0] row_bytes=8;
  logic [31:0] row_count=3;
  logic [63:0] source_stride=16,destination_stride=8;
  logic busy,done,error;
  logic [7:0] error_code;
  logic dma_busy=0,dma_done=0,dma_error=0;
  logic [7:0] dma_error_code=0;
  logic dma_start,dma_direction;
  logic [63:0] dma_dram_base,dma_ub_base;
  logic [15:0] dma_length_bytes;
  integer cycles=0,delay_count=0,request_count=0,fail_request=-1;

  logic expected_direction [0:5];
  logic [63:0] expected_address [0:5];

  always #5 clk=~clk;
  always @(posedge clk) begin
    if(rst) begin
      dma_busy<=0;dma_done<=0;dma_error<=0;dma_error_code<=0;
      delay_count<=0;request_count<=0;
    end else begin
      dma_done<=0;
      if(dma_start && !dma_busy) begin
        if(request_count<6 &&
           (dma_direction!==expected_direction[request_count] ||
            dma_dram_base!==expected_address[request_count]))
          $fatal(1,"dcopy request mismatch index=%0d dir=%0d addr=%h",
            request_count,dma_direction,dma_dram_base);
        if(dma_ub_base!='h40 || dma_length_bytes!=8)
          $fatal(1,"dcopy request payload mismatch");
        dma_busy<=1;delay_count<=2;
        dma_error<=request_count==fail_request;
        dma_error_code<=(request_count==fail_request) ? 8'h52 : 0;
        request_count<=request_count+1;
      end else if(dma_busy) begin
        if(delay_count==0) begin dma_busy<=0;dma_done<=1;end
        else delay_count<=delay_count-1;
      end
    end
  end

  ZtpuUbDcopy64x32 dut(.*);
  task automatic tick; begin @(posedge clk);#1;cycles=cycles+1;end endtask
  task automatic launch; begin @(negedge clk);start=1;tick();@(negedge clk);start=0;end endtask
  task automatic wait_done;
    begin
      while(!done && cycles<300) tick();
      if(!done) $fatal(1,"dcopy timeout");
      tick();
      if(busy || done) $fatal(1,"dcopy did not retire");
    end
  endtask

  initial begin
    expected_direction[0]=0;expected_address[0]='h1004;
    expected_direction[1]=1;expected_address[1]='h2000;
    expected_direction[2]=0;expected_address[2]='h1014;
    expected_direction[3]=1;expected_address[3]='h2008;
    expected_direction[4]=0;expected_address[4]='h1024;
    expected_direction[5]=1;expected_address[5]='h2010;
    #1;rst=1;repeat(2)tick();@(negedge clk);rst=0;

    launch();wait_done();
    if(request_count!=6 || error || error_code!=0)
      $fatal(1,"dcopy successful transfer status mismatch");

    row_count=0;launch();wait_done();
    if(request_count!=6 || error)
      $fatal(1,"zero-row dcopy generated traffic");

    row_count=1;fail_request=6;launch();wait_done();
    if(request_count!=7 || !error || error_code!=8'h52)
      $fatal(1,"dcopy error propagation mismatch");

    $display("UB DCOPY: PASS");$finish;
  end
endmodule
""",
    )
    assert "UB DCOPY: PASS" in output
