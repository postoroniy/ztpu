from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src" / "arithmetic.zhl"
PROJECT = ROOT / "zlang.toml"


def _tool(name: str, env_name: str | None = None) -> str:
    value = os.environ.get(env_name, "") if env_name else ""
    found = value or shutil.which(name)
    if not found:
        pytest.skip(f"{name} is not installed")
    return found


def _compile_top(tmp_path: Path, top: str) -> Path:
    output = tmp_path / f"{top}.sv"
    subprocess.run(
        [
            _tool("zlang", "ZLANGC"),
            str(SOURCE),
            "--project",
            str(PROJECT),
            "--top",
            top,
            "--systemverilog",
            str(output),
        ],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    return output


def _run_sv(tmp_path: Path, sources: list[Path], testbench: str) -> str:
    tb = tmp_path / "tb.sv"
    tb.write_text(testbench, encoding="ascii")
    executable = tmp_path / "sim"
    subprocess.run(
        [
            _tool("iverilog"),
            "-g2012",
            "-s",
            "tb",
            "-o",
            str(executable),
            *[str(path) for path in sources],
            str(tb),
        ],
        check=True,
        text=True,
        capture_output=True,
    )
    return subprocess.run(
        [_tool("vvp"), str(executable)],
        check=True,
        text=True,
        capture_output=True,
    ).stdout


def test_activation_q16x4(tmp_path: Path) -> None:
    source = _compile_top(tmp_path, "ZtpuActivationQ16x4")
    output = _run_sv(
        tmp_path,
        [source],
        """`timescale 1ns/1ps
module tb;
  logic clk = 0, rst = 0;
  logic signed [15:0] input0, input1, input2, input3;
  logic [1:0] activation_type;
  logic signed [15:0] output0, output1, output2, output3;
  always #5 clk = ~clk;
  ZtpuActivationQ16x4 dut(.*);
  task automatic check_activation(input signed [15:0] e0, e1, e2, e3);
    begin
      @(posedge clk); #1;
      if (output0 !== e0 || output1 !== e1 || output2 !== e2 || output3 !== e3)
        $fatal(1, "activation mismatch got=(%0d,%0d,%0d,%0d)",
          output0, output1, output2, output3);
    end
  endtask
  initial begin
    input0 = 0; input1 = 0; input2 = 0; input3 = 0; activation_type = 0;
    #1; rst = 1; repeat (2) @(posedge clk); @(negedge clk); rst = 0;
    input0 = -10; input1 = -3; input2 = 0; input3 = 10; activation_type = 0;
    check_activation(-10, -3, 0, 10);
    @(negedge clk); activation_type = 1;
    check_activation(0, 0, 0, 10);
    @(negedge clk); input0 = -4; input1 = -3; input2 = -2; input3 = 0;
    activation_type = 2;
    check_activation(0, 32, 64, 128);
    @(negedge clk); input0 = 1; input1 = 2; input2 = 3; input3 = 4;
    check_activation(160, 192, 224, 255);
    $display("activation: PASS"); $finish;
  end
endmodule
""",
    )
    assert "activation: PASS" in output


def test_bias_accumulate_q16x4(tmp_path: Path) -> None:
    source = _compile_top(tmp_path, "ZtpuBiasAccumulateQ16x4")
    output = _run_sv(
        tmp_path,
        [source],
        """`timescale 1ns/1ps
module tb;
  logic clk = 0, rst = 0, enable_accumulate = 0;
  logic signed [15:0] input0, input1, input2, input3;
  logic signed [15:0] bias0, bias1, bias2, bias3;
  logic signed [15:0] output0, output1, output2, output3;
  always #5 clk = ~clk;
  ZtpuBiasAccumulateQ16x4 dut(.*);
  task automatic check(input signed [15:0] e0, e1, e2, e3);
    begin
      #1;
      if (output0 !== e0 || output1 !== e1 || output2 !== e2 || output3 !== e3)
        $fatal(1, "BAU mismatch got=(%0d,%0d,%0d,%0d)",
          output0, output1, output2, output3);
    end
  endtask
  initial begin
    input0=0; input1=0; input2=0; input3=0;
    bias0=0; bias1=0; bias2=0; bias3=0;
    #1; rst=1; repeat(2) @(posedge clk); @(negedge clk); rst=0;
    input0=2; input1=-4; input2=6; input3=8;
    bias0=5; bias1=10; bias2=-5; bias3=20; enable_accumulate=0;
    check(7,6,1,28);
    @(posedge clk); #1;
    @(negedge clk); enable_accumulate=1;
    check(9,2,7,36);
    @(posedge clk); #1;
    @(negedge clk); input0=4; input1=-8; input2=12; input3=16;
    check(13,-6,19,52);
    $display("bau: PASS"); $finish;
  end
endmodule
""",
    )
    assert "bau: PASS" in output


@pytest.mark.parametrize(
    ("top", "zero_width", "body"),
    [
        (
            "ZtpuAccRequant8",
            8,
            """
    enable=1; scale=1; shift=0; zero_point=0; value=1000; #1;
    if (result !== 127) $fatal(1, "rq8 positive saturation");
    value=-1000; #1; if (result !== -128) $fatal(1, "rq8 negative saturation");
""",
        ),
        (
            "ZtpuAccRequant16",
            16,
            """
    enable=1; scale=1; shift=1; zero_point=0; value=3; #1;
    if (result !== 2) $fatal(1, "rq16 rounding 3");
    value=1; #1; if (result !== 1) $fatal(1, "rq16 rounding 1");
    enable=0; value=-1; #1; if (result !== -1) $fatal(1, "rq16 bypass");
    enable=1; shift=0; zero_point=5; value=7; #1;
    if (result !== 12) $fatal(1, "rq16 zero point");
""",
        ),
        (
            "ZtpuAccRequant32",
            32,
            """
    enable=1; scale=3; shift=1; zero_point=0; value=5; #1;
    if (result !== 8) $fatal(1, "rq32 rounding");
    enable=0; value=-123; #1; if (result !== -123) $fatal(1, "rq32 bypass");
""",
        ),
    ],
)
def test_acc_requant(tmp_path: Path, top: str, zero_width: int, body: str) -> None:
    source = _compile_top(tmp_path, top)
    output = _run_sv(
        tmp_path,
        [source],
        f"""`timescale 1ns/1ps
module tb;
  logic enable;
  logic signed [31:0] scale;
  logic [5:0] shift;
  logic signed [{zero_width - 1}:0] zero_point;
  logic signed [31:0] value;
  logic signed [{zero_width - 1}:0] result;
  {top} dut(.*);
  initial begin
{body}
    $display("requant: PASS"); $finish;
  end
endmodule
""",
    )
    assert "requant: PASS" in output
