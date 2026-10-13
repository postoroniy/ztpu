from __future__ import annotations

from pathlib import Path

from tools.rtl_test_utils import compile_zlang_top, run_iverilog


def test_perf_counters_and_sticky_error(tmp_path: Path) -> None:
    source = compile_zlang_top(tmp_path, "ZtpuPerfCounters32x8", "perfmon.zhl")
    output = run_iverilog(
        tmp_path,
        [source],
        r"""`timescale 1ns/1ps
module tb;
  logic clk=0,rst=0,enable=0,clear=0,clear_error=0;
  logic busy=0,command_start=0,dma_read=0,dma_write=0,error_event=0;
  logic [7:0] error_code_in=0,error_code;
  logic [31:0] cycles,busy_cycles,command_count;
  logic [31:0] dma_read_count,dma_write_count,error_count;
  logic error_valid;
  always #5 clk=~clk;
  ZtpuPerfCounters32x8 dut(.*);
  task automatic tick; begin @(posedge clk);#1; end endtask
  initial begin
    #1;rst=1;repeat(2)tick();@(negedge clk);rst=0;
    clear=1;clear_error=1;tick();
    clear=0;clear_error=0;enable=1;busy=1;command_start=1;
    dma_read=1;error_event=1;error_code_in=8'ha5;tick();
    command_start=0;dma_read=0;dma_write=1;error_event=0;tick();
    if(cycles!=2 || busy_cycles!=2 || command_count!=1 ||
       dma_read_count!=1 || dma_write_count!=1 || error_count!=1 ||
       !error_valid || error_code!=8'ha5)
      $fatal(1,"performance counter result mismatch");
    clear_error=1;tick();clear_error=0;
    if(error_valid || error_code!=0 || error_count!=1)
      $fatal(1,"sticky error clear mismatch");
    clear=1;error_event=1;error_code_in=8'h3c;tick();
    clear=0;error_event=0;
    if(cycles!=0 || busy_cycles!=0 || command_count!=0 ||
       dma_read_count!=0 || dma_write_count!=0 || error_count!=0 ||
       !error_valid || error_code!=8'h3c)
      $fatal(1,"counter clear/error priority mismatch");
    $display("Performance counters: PASS");$finish;
  end
endmodule
""",
    )
    assert "Performance counters: PASS" in output
