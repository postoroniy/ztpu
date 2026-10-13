from __future__ import annotations

import json
from pathlib import Path
import subprocess

from tools.rtl_test_utils import ROOT, compile_zlang_top, require_tool, run_iverilog


def test_layout_dma_native_matches_verilator(tmp_path: Path) -> None:
    zlangc = require_tool("zlang", "ZLANGC")
    require_tool("verilator")
    result = subprocess.run(
        [
            zlangc,
            "sim",
            str(ROOT / "src" / "layout_dma_core.zhl"),
            "--project",
            str(ROOT / "zlang.toml"),
            "--top",
            "ZtpuLayoutDmaControl64x32",
            "--engine",
            "native",
            "--events",
            str(ROOT / "tests" / "events" / "layout_dma_normal.jsonl"),
            "--json",
            "--compare-with",
            "verilator",
            "--compare-artifacts",
            str(tmp_path / "comparison"),
        ],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
        timeout=120,
    )
    trace = json.loads(result.stdout)
    assert len(trace) == 11
    assert (trace[3]["read_ar_valid"], trace[3]["read_ar_addr"]) == (1, 0x100)
    assert (trace[6]["write_aw_valid"], trace[6]["write_aw_addr"]) == (1, 0x200)
    assert (
        trace[7]["write_w_valid"],
        trace[7]["write_w_data"],
        trace[7]["write_w_last"],
    ) == (1, 0x12345678, 1)
    assert trace[10]["done"] == 1
    assert all(sample["error"] == 0 for sample in trace)


def test_layout_dma_full_axi4_adapter_and_id_check(tmp_path: Path) -> None:
    source = compile_zlang_top(
        tmp_path,
        "ZtpuLayoutDmaAxi4Master64x32",
        "layout_dma_axi4.zhl",
    )
    output = run_iverilog(
        tmp_path,
        [source],
        r"""`timescale 1ns/1ps
module tb;
  logic clk=0,rst=0,enable=1;
  logic [63:0] layout_payload_in_addr=0,layout_payload_out_addr=0;
  logic layout_valid=0,layout_ready,busy,done,error;

  logic axi_aw_payload_id;
  logic [63:0] axi_aw_payload_addr;
  logic [7:0] axi_aw_payload_len;
  logic [2:0] axi_aw_payload_size;
  logic [1:0] axi_aw_payload_burst;
  logic axi_aw_payload_lock;
  logic [3:0] axi_aw_payload_cache;
  logic [2:0] axi_aw_payload_prot;
  logic [3:0] axi_aw_payload_qos,axi_aw_payload_region;
  logic axi_aw_valid,axi_aw_ready=0;
  logic [31:0] axi_w_payload_data;
  logic [3:0] axi_w_payload_strb;
  logic axi_w_payload_last,axi_w_valid,axi_w_ready=0;
  logic axi_b_payload_id=0;
  logic [1:0] axi_b_payload_resp=0;
  logic axi_b_valid=0,axi_b_ready;
  logic axi_ar_payload_id;
  logic [63:0] axi_ar_payload_addr;
  logic [7:0] axi_ar_payload_len;
  logic [2:0] axi_ar_payload_size;
  logic [1:0] axi_ar_payload_burst;
  logic axi_ar_payload_lock;
  logic [3:0] axi_ar_payload_cache;
  logic [2:0] axi_ar_payload_prot;
  logic [3:0] axi_ar_payload_qos,axi_ar_payload_region;
  logic axi_ar_valid,axi_ar_ready=0;
  logic axi_r_payload_id=0;
  logic [31:0] axi_r_payload_data=0;
  logic [1:0] axi_r_payload_resp=0;
  logic axi_r_payload_last=0,axi_r_valid=0,axi_r_ready;
  integer cycles;

  always #5 clk=~clk;
  ZtpuLayoutDmaAxi4Master64x32 dut(.*);
  task automatic tick; begin @(posedge clk);#1; end endtask
  task automatic launch(input [63:0] source_addr,input [63:0] dest_addr);
    begin
      layout_payload_in_addr=source_addr;
      layout_payload_out_addr=dest_addr;
      layout_valid=1;tick();layout_valid=0;tick();
      if(!axi_ar_valid || axi_ar_payload_id!=0 ||
         axi_ar_payload_addr!=source_addr || axi_ar_payload_len!=0 ||
         axi_ar_payload_size!=2 || axi_ar_payload_burst!=1 ||
         axi_ar_payload_lock!=0 || axi_ar_payload_cache!=0 ||
         axi_ar_payload_prot!=0 || axi_ar_payload_qos!=0 ||
         axi_ar_payload_region!=0)
        $fatal(1,"bad full AXI4 read address");
      axi_ar_ready=1;tick();axi_ar_ready=0;
    end
  endtask
  task automatic finish_copy(input [63:0] dest_addr,input [31:0] value,input bad_bid);
    begin
      axi_r_payload_data=value;axi_r_payload_last=1;
      axi_r_payload_id=0;axi_r_valid=1;tick();
      axi_r_valid=0;axi_r_payload_last=0;tick();
      if(!axi_aw_valid || axi_aw_payload_id!=0 ||
         axi_aw_payload_addr!=dest_addr ||
         axi_aw_payload_len!=0 || axi_aw_payload_size!=2 ||
         axi_aw_payload_burst!=1 || axi_aw_payload_lock!=0 ||
         axi_aw_payload_cache!=0 || axi_aw_payload_prot!=0 ||
         axi_aw_payload_qos!=0 || axi_aw_payload_region!=0)
        $fatal(1,"bad full AXI4 write address");
      axi_aw_ready=1;tick();axi_aw_ready=0;
      if(!axi_w_valid || axi_w_payload_data!=value ||
         axi_w_payload_strb!=4'hf || !axi_w_payload_last)
        $fatal(1,"bad full AXI4 write data");
      axi_w_ready=1;tick();axi_w_ready=0;
      axi_b_payload_id=bad_bid;axi_b_valid=1;tick();axi_b_valid=0;
      tick();
    end
  endtask

  initial begin
    rst=1;repeat(2)tick();rst=0;tick();
    launch(64'h100,64'h200);
    finish_copy(64'h200,32'h12345678,0);
    if(!done || error) $fatal(1,"normal copy status mismatch");
    tick();

    launch(64'h104,64'h204);
    finish_copy(64'h204,32'h89abcdef,1);
    if(!done || !error) $fatal(1,"response ID mismatch was not rejected");
    $display("Layout DMA AXI4 adapter: PASS");$finish;
  end
endmodule
""",
    )
    assert "Layout DMA AXI4 adapter: PASS" in output
