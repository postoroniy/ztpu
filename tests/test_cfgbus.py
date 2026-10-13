from __future__ import annotations

from pathlib import Path

from tools.rtl_test_utils import compile_zlang_top, run_iverilog


def test_cfgbus_uses_native_banks_and_standard_frontends() -> None:
    source = (Path(__file__).resolve().parents[1] / "src" / "cfgbus.zhl").read_text(
        encoding="ascii"
    )
    assert source.count("csr registers @ 0") == 1
    assert source.count("csr extended @ 0x0300") == 1
    assert "module ZtpuQueuedCfgAhb64x32" in source
    assert "module ZtpuQueuedCfgRegBus64x32" in source
    assert "module ZtpuQueuedCfgApb64x32" in source
    assert "inst frontend : AHBLiteToRegBus<32,32>" in source
    assert "inst frontend : APBToRegBus<32,32>" in source
    assert "module ZtpuQueuedCfgBusCore64x32" not in source
    assert "module ZtpuQueuedCfgBus64x32" not in source
    assert "in status : ZtpuCfgStatus" in source
    assert "out control : ZtpuCfgControl" in source
    assert "csr group FENCE_WINDOW" in source
    assert "global_fence : FENCE_WINDOW[1] @ 0x0210 stride 0x14" in source
    assert "domain_fences : FENCE_WINDOW[2] @ 0x0238 stride 0x14" in source
    assert "master_fences : FENCE_WINDOW[4] @ 0x02c4 stride 0x14" in source
    assert "inst queued_command_snapshot : StorageSnapshot<" in source
    assert "reset_value=fn empty_command" in source
    assert "switch address" not in source
    assert "address_valid" not in source


def test_native_ahb_cfgbus_pipeline_pulses_and_errors(tmp_path: Path) -> None:
    source = compile_zlang_top(tmp_path, "ZtpuQueuedCfgAhb64x32", "cfgbus.zhl")
    output = run_iverilog(
        tmp_path,
        [source],
        r"""`timescale 1ns/1ps
module tb;
  logic clk=0,rst=0;
  logic ahb_HSEL=0,ahb_HWRITE=0;
  logic [31:0] ahb_HADDR=0,ahb_HWDATA=0,ahb_HRDATA;
  logic [1:0] ahb_HTRANS=0;
  logic [2:0] ahb_HSIZE=2,ahb_HBURST=0;
  logic [3:0] ahb_HPROT=0;
  logic ahb_HMASTLOCK=0,ahb_HREADYOUT,ahb_HRESP;
  wire ahb_HREADY=ahb_HREADYOUT;
  logic control_perf_enable,control_perf_clear,control_command_push;
  logic control_queued_valid;
  logic [3:0] control_queued_command_opcode;
  logic [63:0] control_queued_command_address;
  logic [7:0] control_queued_command_tag;
  logic saw_perf_clear=0,saw_command_push=0;
  integer i;

  always #5 clk=~clk;
  always @(posedge clk) begin
    if(control_perf_clear) saw_perf_clear<=1;
    if(control_command_push) saw_command_push<=1;
  end

  ZtpuQueuedCfgAhb64x32 dut(
    .clk,.rst,
    .ahb_HSEL,.ahb_HADDR,.ahb_HWRITE,.ahb_HTRANS,.ahb_HSIZE,
    .ahb_HBURST,.ahb_HPROT,.ahb_HMASTLOCK,.ahb_HWDATA,.ahb_HREADY,
    .ahb_HRDATA,.ahb_HREADYOUT,.ahb_HRESP,
    .status_command_ready(1'b1),.status_command_accept(1'b0),
    .status_command_count(3'd0),.status_command_last_done(8'd0),
    .control_perf_enable,.control_perf_clear,.control_command_push,
    .control_queued_valid,.control_queued_command_opcode,
    .control_queued_command_address,.control_queued_command_tag
  );

  task automatic tick; begin @(posedge clk);#1;end endtask
  task automatic idle_address; begin
    @(negedge clk);ahb_HSEL=0;ahb_HTRANS=0;ahb_HWRITE=0;
    ahb_HADDR=0;ahb_HSIZE=2;
  end endtask
  task automatic wr(input [31:0] addr,input [31:0] data); begin
    @(negedge clk);ahb_HSEL=1;ahb_HTRANS=2;ahb_HWRITE=1;
    ahb_HADDR=addr;ahb_HSIZE=2;ahb_HWDATA=0;
    tick();
    if(ahb_HREADYOUT || ahb_HRESP)
      $fatal(1,"AHB write did not enter request phase addr=%h",addr);
    @(negedge clk);ahb_HSEL=0;ahb_HTRANS=0;ahb_HWRITE=0;
    ahb_HADDR=0;ahb_HWDATA=data;
    tick();
    if(!ahb_HREADYOUT || ahb_HRESP)
      $fatal(1,"AHB write response addr=%h ready=%b resp=%b",
             addr,ahb_HREADYOUT,ahb_HRESP);
    @(negedge clk);ahb_HWDATA=0;tick();
  end endtask
  task automatic rd(input [31:0] addr,input [31:0] expected); begin
    @(negedge clk);ahb_HSEL=1;ahb_HTRANS=2;ahb_HWRITE=0;
    ahb_HADDR=addr;ahb_HSIZE=2;
    tick();
    if(ahb_HREADYOUT || ahb_HRESP)
      $fatal(1,"AHB read did not enter request phase addr=%h",addr);
    idle_address();tick();
    if(!ahb_HREADYOUT || ahb_HRESP || ahb_HRDATA!==expected)
      $fatal(1,"AHB read addr=%h got=%h expected=%h ready=%b resp=%b",
             addr,ahb_HRDATA,expected,ahb_HREADYOUT,ahb_HRESP);
    tick();
  end endtask
  task automatic bad(input [31:0] addr,input [2:0] size); begin
    logic saw_wait_error;
    logic saw_terminal_error;
    saw_wait_error=0;saw_terminal_error=0;
    @(negedge clk);ahb_HSEL=1;ahb_HTRANS=2;ahb_HWRITE=0;
    ahb_HADDR=addr;ahb_HSIZE=size;
    tick();idle_address();
    for(i=0;i<6;i=i+1) begin
      if(ahb_HRESP && !ahb_HREADYOUT) saw_wait_error=1;
      if(ahb_HRESP && ahb_HREADYOUT) begin
        saw_terminal_error=1;i=6;
      end else tick();
    end
    if(!saw_wait_error || !saw_terminal_error)
      $fatal(1,"AHB error sequence missing addr=%h size=%0d",addr,size);
    tick();
  end endtask
  task automatic back_to_back_reads; begin
    @(negedge clk);ahb_HSEL=1;ahb_HTRANS=2;ahb_HWRITE=0;
    ahb_HADDR=32'h0000;ahb_HSIZE=2;
    tick();
    @(negedge clk);ahb_HADDR=32'h0004;
    tick();
    if(!ahb_HREADYOUT || ahb_HRDATA!==32'h5a545055)
      $fatal(1,"first back-to-back read mismatch");
    tick();
    if(ahb_HREADYOUT) $fatal(1,"second request was not accepted");
    idle_address();tick();
    if(!ahb_HREADYOUT || ahb_HRESP || ahb_HRDATA!==32'h1)
      $fatal(1,"second back-to-back read mismatch");
    tick();
  end endtask

  initial begin
    #1;rst=1;repeat(2)tick();@(negedge clk);rst=0;tick();
    rd(32'h0000,32'h5a545055);
    rd(32'h0004,32'h1);
    wr(32'h0060,32'h1);rd(32'h0060,32'h1);
    wr(32'h0060,32'h3);
    if(!control_perf_enable || !saw_perf_clear)
      $fatal(1,"persistent or pulse CSR write missing");

    wr(32'h00e8,32'h7);
    wr(32'h00ec,32'h89abcdef);
    wr(32'h00f0,32'h01234567);
    wr(32'h00f8,32'h55);
    wr(32'h00e4,32'h1);
    if(!saw_command_push || !control_queued_valid ||
       control_queued_command_opcode!==4'h7 ||
       control_queued_command_address!==64'h0123456789abcdef ||
       control_queued_command_tag!==8'h55)
      $fatal(1,"queued command snapshot mismatch");

    back_to_back_reads();
    bad(32'h0001,3'd2);
    bad(32'h0000,3'd1);
    bad(32'h5000,3'd2);

    // Reset must return an in-flight bridge request and CSR state to idle.
    @(negedge clk);ahb_HSEL=1;ahb_HTRANS=2;ahb_HADDR=32'h0000;
    ahb_HSIZE=2;tick();
    @(negedge clk);rst=1;ahb_HSEL=0;ahb_HTRANS=0;tick();
    if(!ahb_HREADYOUT || ahb_HRESP || control_perf_enable || control_queued_valid)
      $fatal(1,"AHB reset did not restore idle/default state");
    @(negedge clk);rst=0;tick();

    $display("Native AHB cfgbus: PASS");$finish;
  end
endmodule
""",
    )
    assert "Native AHB cfgbus: PASS" in output
