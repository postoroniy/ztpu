from __future__ import annotations

from pathlib import Path

from tools.rtl_test_utils import compile_zlang_top, run_iverilog


def test_dma_fence_first_fault_and_overflow_semantics(tmp_path: Path) -> None:
    source = compile_zlang_top(
        tmp_path, "ZtpuDmaFenceFaultLatch64", "fault_status.zhl"
    )
    output = run_iverilog(
        tmp_path,
        [source],
        r"""`timescale 1ns/1ps
module tb;
  logic clk=0,rst=0,fault=0,fault_write=0,clear_valid=0,clear_overflow=0;
  logic [3:0] fault_master=0,sticky_master;logic [63:0] fault_addr=0,sticky_addr;
  logic [7:0] fault_len=0,sticky_len;logic [2:0] fault_size=0,sticky_size;
  logic valid,overflow,sticky_write;
  always #5 clk=~clk;
  ZtpuDmaFenceFaultLatch64 dut(.*);
  task automatic tick;begin @(posedge clk);#1;end endtask
  initial begin
    #1;rst=1;repeat(2)tick();@(negedge clk);rst=0;
    fault=1;fault_write=0;fault_master=7;fault_addr='h1234;
    fault_len=3;fault_size=2;tick();
    if(!valid || overflow || sticky_write || sticky_master!=7 ||
       sticky_addr!='h1234 || sticky_len!=3 || sticky_size!=2)
      $fatal(1,"first fault capture mismatch");
    @(negedge clk);fault_write=1;fault_master=8;fault_addr='h5678;
    fault_len=1;tick();
    if(!valid || !overflow || sticky_write || sticky_master!=7 ||
       sticky_addr!='h1234 || sticky_len!=3)
      $fatal(1,"overflow changed first fault");
    @(negedge clk);fault=0;clear_overflow=1;tick();
    if(!valid || overflow || sticky_master!=7)
      $fatal(1,"overflow clear mismatch");
    @(negedge clk);clear_overflow=0;clear_valid=1;tick();
    if(valid || overflow) $fatal(1,"valid clear mismatch");
    @(negedge clk);fault=1;clear_valid=1;fault_write=1;
    fault_master=9;fault_addr='h9000;fault_len=15;fault_size=2;tick();
    if(!valid || overflow || !sticky_write || sticky_master!=9 ||
       sticky_addr!='h9000 || sticky_len!=15)
      $fatal(1,"fault priority over clear mismatch");
    $display("DMA fence fault latch: PASS");$finish;
  end
endmodule
""",
    )
    assert "DMA fence fault latch: PASS" in output
