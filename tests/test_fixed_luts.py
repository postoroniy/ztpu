from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from tools.rtl_test_utils import compile_zlang_rom, run_iverilog


EXPECTED_TABLE_HASHES = {
    "recip_05_1": "5799d49bd7603e3ba63ad2c2732ac984df31032576b2508f71260efcc50e13c9",
    "rsqrt_05_1": "c50cd6fc263e8e347c1f716d74f4ab961e0d8277dded0f433380b1f20049393d",
    "exp_neg_0_8": "9e6c8c296cd5531be7d3d57f8aa55710274cd5373487a93b5d3d53beea855095",
    "ln_05_1": "da6a194dab8d3f8a1fd0d2822f5187cfe96101c59a64dc228442fabfe938bb01",
}

TABLES = [
    ("ZtpuReciprocalSeedLutQ16", "recip_05_1", 8, 256),
    ("ZtpuRsqrtSeedLutQ16", "rsqrt_05_1", 8, 256),
    ("ZtpuExpNegLutQ16", "exp_neg_0_8", 10, 1024),
    ("ZtpuLnMantissaLutQ16", "ln_05_1", 8, 256),
]


def _table_hash(values: list[int]) -> str:
    packed = b"".join(value.to_bytes(4, "little") for value in values)
    return hashlib.sha256(packed).hexdigest()


def test_native_fixed_lut_hashes_are_current(tmp_path: Path) -> None:
    actual = {}
    for top, table_name, _, depth in TABLES:
        output = tmp_path / top
        output.mkdir()
        _, values = compile_zlang_rom(output, top, "fixed_luts.zhl")
        assert len(values) == depth
        actual[table_name] = _table_hash(values)
    assert actual == EXPECTED_TABLE_HASHES


@pytest.mark.parametrize(
    ("top", "table_name", "address_width"),
    [(top, name, width) for top, name, width, _ in TABLES],
)
def test_fixed_lut_single_cycle_read_contract(
    tmp_path: Path, top: str, table_name: str, address_width: int
) -> None:
    source, values = compile_zlang_rom(tmp_path, top, "fixed_luts.zhl")
    samples = [0, len(values) // 2, len(values) - 1]
    checks = "\n".join(
        f"    read_and_check({address_width}'d{address},32'h{values[address]:08x});"
        for address in samples
    )
    output = run_iverilog(
        tmp_path,
        [source],
        f"""`timescale 1ns/1ps
module tb;
  logic clk=0,rst=0,request=0;
  logic [{address_width - 1}:0] address=0;
  logic [31:0] data;
  logic data_valid;
  always #5 clk=~clk;
  {top} dut(.*);
  task automatic read_and_check(
    input [{address_width - 1}:0] requested_address,input [31:0] expected
  );
    begin
      @(negedge clk);address=requested_address;request=1;
      @(posedge clk);#1;
      if(!data_valid || data!==expected)
        $fatal(1,"LUT mismatch address=%0d data=%h expected=%h",
          requested_address,data,expected);
      @(negedge clk);request=0;@(posedge clk);#1;
      if(data_valid) $fatal(1,"data_valid did not clear");
    end
  endtask
  initial begin
    #1;rst=1;repeat(2)@(posedge clk);@(negedge clk);rst=0;
{checks}
    $display("fixed LUT {table_name}: PASS");$finish;
  end
endmodule
""",
    )
    assert f"fixed LUT {table_name}: PASS" in output
