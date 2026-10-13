from __future__ import annotations

from pathlib import Path
import subprocess

from tools.rtl_test_utils import ROOT, require_tool, run_iverilog


def _compile_apb_frontend(tmp_path: Path) -> Path:
    zlangc = require_tool("zlang", "ZLANGC")
    output = tmp_path / "ZtpuCfgApbSmoke64x32.sv"
    subprocess.run(
        [
            zlangc,
            str(ROOT / "src" / "cfgbus.zhl"),
            "--project",
            str(ROOT / "zlang.toml"),
            "--top",
            "ZtpuQueuedCfgApb64x32",
            "--systemverilog",
            str(output),
        ],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    return output


def test_cfgbus_frontends_share_one_native_csr_map() -> None:
    source = (ROOT / "src" / "cfgbus.zhl").read_text(encoding="ascii")
    assert source.count("module ZtpuCsrBank64x32") == 1
    assert "module ZtpuQueuedCfgAccessCore64x32" in source
    assert "module ZtpuQueuedCfgRegBus64x32" in source
    assert "module ZtpuQueuedCfgAhb64x32" in source
    assert "module ZtpuQueuedCfgApb64x32" in source
    assert "inst frontend : AHBLiteToRegBus<32,32>" in source
    assert "inst frontend : APBToRegBus<32,32>" in source
    assert "frontend.regbus -> target.regbus" in source
    assert "ZtpuQueuedCfgBusCore64x32" not in source


def test_registered_apb_reads_writes_pulses_and_errors(tmp_path: Path) -> None:
    source = _compile_apb_frontend(tmp_path)
    output = run_iverilog(
        tmp_path,
        [source],
        r"""`timescale 1ns/1ps
module tb;
  logic clk=0,rst=0;
  logic apb_psel=0,apb_penable=0,apb_pwrite=0;
  logic [31:0] apb_paddr=0,apb_pwdata=0,apb_prdata;
  logic apb_pready,apb_pslverr;
  logic perf_enable,perf_clear,command_push;
  logic saw_perf_clear=0;
  always #5 clk=~clk;
  always @(posedge clk) if(perf_clear)saw_perf_clear<=1;

  ZtpuQueuedCfgApb64x32 dut(
    .clk,.rst,.apb_psel,.apb_penable,.apb_pwrite,.apb_paddr,.apb_pwdata,
    .apb_pready,.apb_prdata,.apb_pslverr,
    .control_perf_enable(perf_enable),.control_perf_clear(perf_clear),
    .control_command_push(command_push));

  task tick; begin @(posedge clk); #1; end endtask
  task apb_access(
    input logic write,
    input logic [31:0] addr,
    input logic [31:0] data,
    input logic [31:0] expected,
    input logic expected_error
  ); begin
    apb_psel=1;apb_penable=0;apb_pwrite=write;
    apb_paddr=addr;apb_pwdata=data;tick();
    apb_penable=1;
    while(!apb_pready) tick();
    if(apb_pslverr!==expected_error)
      $fatal(1,"APB error mismatch addr=%h got=%b",addr,apb_pslverr);
    if(!write && !expected_error && apb_prdata!==expected)
      $fatal(1,"APB read mismatch addr=%h got=%h expected=%h",
             addr,apb_prdata,expected);
    apb_psel=0;apb_penable=0;apb_pwrite=0;tick();
  end endtask

  initial begin
    rst=1;repeat(2)tick();rst=0;tick();
    apb_access(0,32'h0000,0,32'h5a545055,0);
    apb_access(1,32'h0060,32'h00000001,0,0);
    if(!perf_enable)$fatal(1,"APB persistent CSR write was lost");
    apb_access(0,32'h0060,0,32'h00000001,0);
    apb_access(1,32'h0060,32'h00000003,0,0);
    if(!perf_enable)$fatal(1,"APB enable changed unexpectedly");
    if(!saw_perf_clear)$fatal(1,"APB pulse CSR was not observed");
    apb_access(0,32'h0010,0,0,1);
    $display("Registered APB cfgbus: PASS");$finish;
  end
endmodule
""",
    )
    assert "Registered APB cfgbus: PASS" in output
