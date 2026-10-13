from pathlib import Path

from tools.rtl_test_utils import compile_zlang_top, run_iverilog


def test_read_arbiter_holds_owner_through_rlast(tmp_path: Path) -> None:
    source = compile_zlang_top(
        tmp_path, "ZtpuAxiReadArbiter2x64x32", "axi_arbiter.zhl"
    )
    output = run_iverilog(
        tmp_path,
        [source],
        r"""`timescale 1ns/1ps
module tb;
 logic clk=0,rst=0;
 logic m0_ar_valid=0,m0_ar_ready;logic[63:0]m0_ar_payload_addr=0;
 logic[7:0]m0_ar_payload_len=0;logic[2:0]m0_ar_payload_size=2;
 logic m0_r_valid,m0_r_ready=1,m0_r_payload_last;logic[31:0]m0_r_payload_data;logic[1:0]m0_r_payload_resp;
 logic m1_ar_valid=0,m1_ar_ready;logic[63:0]m1_ar_payload_addr=0;
 logic[7:0]m1_ar_payload_len=0;logic[2:0]m1_ar_payload_size=2;
 logic m1_r_valid,m1_r_ready=1,m1_r_payload_last;logic[31:0]m1_r_payload_data;logic[1:0]m1_r_payload_resp;
 logic s_ar_valid,s_ar_ready=1;logic[63:0]s_ar_payload_addr;logic[7:0]s_ar_payload_len;
 logic[2:0]s_ar_payload_size;logic s_r_valid=0,s_r_ready,s_r_payload_last=0;
 logic[31:0]s_r_payload_data=0;logic[1:0]s_r_payload_resp=0;
 always #5 clk=~clk;ZtpuAxiReadArbiter2x64x32 dut(.*);
 task tick;begin @(posedge clk);#1;end endtask
 initial begin
  rst=1;repeat(2)tick();rst=0;tick();
  m0_ar_valid=1;m0_ar_payload_addr=64'h100;m0_ar_payload_len=1;
  m1_ar_valid=1;m1_ar_payload_addr=64'h200;#1;
  if(!m0_ar_ready||m1_ar_ready||s_ar_payload_addr!=64'h100)$fatal(1,"priority");tick();
  m0_ar_valid=0;s_r_valid=1;s_r_payload_data=32'haaaa;s_r_payload_last=0;#1;
  if(!m0_r_valid||m1_r_valid||!s_r_ready)$fatal(1,"owner beat0");tick();
  s_r_payload_last=1;#1;if(!m0_r_valid)$fatal(1,"owner last");tick();
  s_r_valid=0;s_r_payload_last=0;#1;
  if(!m1_ar_ready||s_ar_payload_addr!=64'h200)$fatal(1,"second grant");
  $display("AXI read arbitration: PASS");$finish;
 end
endmodule
""",
    )
    assert "AXI read arbitration: PASS" in output


def test_write_arbiter_holds_owner_through_response(tmp_path: Path) -> None:
    source = compile_zlang_top(
        tmp_path, "ZtpuAxiWriteArbiter2x64x32", "axi_arbiter.zhl"
    )
    output = run_iverilog(
        tmp_path,
        [source],
        r"""`timescale 1ns/1ps
module tb;
 logic clk=0,rst=0;
 logic m0_aw_valid=0,m0_aw_ready;logic[63:0]m0_aw_payload_addr=0;logic[7:0]m0_aw_payload_len=0;logic[2:0]m0_aw_payload_size=2;
 logic m0_w_valid=0,m0_w_ready;logic[31:0]m0_w_payload_data=0;logic m0_w_payload_last=1,m0_b_valid,m0_b_ready=1;logic[1:0]m0_b_payload_resp;
 logic m1_aw_valid=0,m1_aw_ready;logic[63:0]m1_aw_payload_addr=0;logic[7:0]m1_aw_payload_len=0;logic[2:0]m1_aw_payload_size=2;
 logic m1_w_valid=0,m1_w_ready;logic[31:0]m1_w_payload_data=0;logic m1_w_payload_last=1,m1_b_valid,m1_b_ready=1;logic[1:0]m1_b_payload_resp;
 logic s_aw_valid,s_aw_ready=1;logic[63:0]s_aw_payload_addr;logic[7:0]s_aw_payload_len;logic[2:0]s_aw_payload_size;
 logic s_w_valid,s_w_ready=1;logic[31:0]s_w_payload_data;logic s_w_payload_last,s_b_valid=0,s_b_ready;logic[1:0]s_b_payload_resp=0;
 always #5 clk=~clk;ZtpuAxiWriteArbiter2x64x32 dut(.*);
 task tick;begin @(posedge clk);#1;end endtask
 initial begin
  rst=1;repeat(2)tick();rst=0;tick();
  m0_aw_valid=1;m0_aw_payload_addr=64'h100;m1_aw_valid=1;m1_aw_payload_addr=64'h200;#1;
  if(!m0_aw_ready||m1_aw_ready)$fatal(1,"priority");tick();m0_aw_valid=0;
  m0_w_valid=1;m0_w_payload_data=32'h1234;#1;
  if(!m0_w_ready||m1_w_ready||s_w_payload_data!=32'h1234)$fatal(1,"owner data");tick();m0_w_valid=0;
  s_b_valid=1;#1;if(!m0_b_valid||m1_b_valid)$fatal(1,"owner response");tick();
  s_b_valid=0;#1;if(!m1_aw_ready||s_aw_payload_addr!=64'h200)$fatal(1,"second grant");
  $display("AXI write arbitration: PASS");$finish;
 end
endmodule
""",
    )
    assert "AXI write arbitration: PASS" in output
