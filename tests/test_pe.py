from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "zlang.toml"
SOURCE = ROOT / "src" / "pe.zhl"


def _tool(name: str, env_name: str | None = None) -> str | None:
    if env_name and os.environ.get(env_name):
        return os.environ[env_name]
    return shutil.which(name)


@pytest.fixture()
def zlang_pe_sv(tmp_path: Path) -> Path:
    zlangc = _tool("zlang", "ZLANGC")
    if zlangc is None:
        pytest.skip("zlangc is not installed")
    output = tmp_path / "ZtpuPeQ16.sv"
    subprocess.run(
        [
            zlangc,
            str(SOURCE),
            "--project",
            str(PROJECT),
            "--top",
            "ZtpuPeQ16",
            "--systemverilog",
            str(output),
        ],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    return output


def test_systemverilog_lints(zlang_pe_sv: Path) -> None:
    verilator = _tool("verilator")
    if verilator is None:
        pytest.skip("Verilator is not installed")
    subprocess.run(
        [verilator, "--lint-only", "-Wall", str(zlang_pe_sv)],
        check=True,
        text=True,
        capture_output=True,
    )


def _wrap_s32(value: int) -> int:
    value &= 0xFFFF_FFFF
    return value - (1 << 32) if value & (1 << 31) else value


def _sv_signed(width: int, value: int) -> str:
    return f"-{width}'sd{-value}" if value < 0 else f"{width}'sd{value}"


def test_behavioral_contract(zlang_pe_sv: Path, tmp_path: Path) -> None:
    iverilog = _tool("iverilog")
    vvp = _tool("vvp")
    if iverilog is None or vvp is None:
        pytest.skip("Icarus Verilog is not installed")
    vectors = [
        (3, 2, 10),
        (-3, 2, 10),
        (-32768, -32768, -2147483648),
        (32767, 32767, 2147483647),
        (-32768, 32767, 2147483647),
    ]
    checks = []
    for input_v, input_w, input_acc in vectors:
        expected = _wrap_s32(input_acc + input_v * input_w)
        checks.append(
            "    check_vector("
            f"{_sv_signed(16, input_v)}, {_sv_signed(16, input_w)}, "
            f"{_sv_signed(32, input_acc)}, {_sv_signed(32, expected)});"
        )
    testbench = tmp_path / "tb.sv"
    testbench.write_text(
        """`timescale 1ns/1ps
module tb;
  logic clk = 0;
  logic rst = 1;
  logic signed [15:0] input_v = 0;
  logic signed [15:0] input_w = 0;
  logic signed [31:0] input_acc = 0;
  logic signed [31:0] output_acc;
  logic signed [15:0] output_v;
  logic signed [15:0] output_w;
  always #5 clk = ~clk;
  ZtpuPeQ16 dut (.*);
  task automatic check_vector(
      input logic signed [15:0] v,
      input logic signed [15:0] w,
      input logic signed [31:0] acc,
      input logic signed [31:0] expected);
    begin
      @(negedge clk); input_v = v; input_w = w; input_acc = acc;
      @(posedge clk); #1;
      if ($signed(output_acc) !== expected || $signed(output_v) !== v ||
          $signed(output_w) !== w)
        $fatal(1, "ZtpuPeQ16 mismatch");
    end
  endtask
  initial begin
    repeat (2) @(posedge clk);
    @(negedge clk); rst = 0;
"""
        + "\n".join(checks)
        + """
    $display("ZtpuPeQ16 behavioral parity: PASS");
    $finish;
  end
endmodule
""",
        encoding="ascii",
    )
    executable = tmp_path / "pe_sim"
    subprocess.run(
        [iverilog, "-g2012", "-s", "tb", "-o", str(executable), str(zlang_pe_sv), str(testbench)],
        check=True,
        text=True,
        capture_output=True,
    )
    result = subprocess.run([vvp, str(executable)], check=True, text=True, capture_output=True)
    assert "behavioral parity: PASS" in result.stdout
