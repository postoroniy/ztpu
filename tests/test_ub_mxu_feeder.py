from __future__ import annotations

from pathlib import Path

from tools.rtl_test_utils import compile_zlang_top, run_iverilog


def test_ub_mxu_feeder_lockstep_unpack_and_stall(tmp_path: Path) -> None:
    source = compile_zlang_top(tmp_path, "ZtpuUbMxuFeeder4x4I8", "ub_mxu_feeder.zhl")
    output = run_iverilog(
        tmp_path,
        [source],
        r"""`timescale 1ns/1ps
module tb;
  logic clk=0,rst=0,start=0;
  logic [63:0] a_base=0,b_base=0,ub_a_addr,ub_b_addr;
  logic [15:0] k_dim=0;
  logic busy,done,clear_pulse,stream_valid,ub_a_valid,ub_b_valid;
  logic ub_a_ready=0,ub_b_ready=0;
  logic [31:0] ub_a_data=0,ub_b_data=0;
  logic signed [31:0] a0,a1,a2,a3,b0,b1,b2,b3;
  always #5 clk=~clk;
  ZtpuUbMxuFeeder4x4I8 dut(.*);
  task automatic tick; begin @(posedge clk);#1; end endtask
  initial begin
    #1;rst=1;repeat(2)tick();@(negedge clk);rst=0;
    a_base=64'h100;b_base=64'h200;k_dim=2;start=1;#1;
    if (!clear_pulse) $fatal(1,"clear pulse missing");
    tick();start=0;
    if (!busy || !ub_a_valid || !ub_b_valid || ub_a_addr!=64'h100 || ub_b_addr!=64'h200)
      $fatal(1,"run entry mismatch");

    ub_a_ready=1;ub_b_ready=0;ub_a_data=32'h807f01ff;ub_b_data=32'h04030201;#1;
    if (stream_valid || a0!=0 || b0!=0) $fatal(1,"partial-ready stall mismatch");
    tick();ub_b_ready=1;#1;
    if (!stream_valid || a0!=-1 || a1!=1 || a2!=127 || a3!=-128 ||
        b0!=1 || b1!=2 || b2!=3 || b3!=4)
      $fatal(1,"first unpack mismatch");
    tick();
    ub_a_data=32'hfcfdfeff;ub_b_data=32'h7f008001;#1;
    if (ub_a_addr!=64'h104 || ub_b_addr!=64'h204 ||
        a0!=-1 || a1!=-2 || a2!=-3 || a3!=-4 ||
        b0!=1 || b1!=-128 || b2!=0 || b3!=127)
      $fatal(1,"second unpack/address mismatch");
    tick();
    if (stream_valid) $fatal(1,"stream did not stop at K");
    tick();if (!done || busy) $fatal(1,"done mismatch");
    $display("UB MXU feeder: PASS");$finish;
  end
endmodule
""",
    )
    assert "UB MXU feeder: PASS" in output
