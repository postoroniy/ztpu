from __future__ import annotations

from pathlib import Path

from tools.rtl_test_utils import compile_zlang_top, run_iverilog


def write_hex_words(path: Path, words: list[int]) -> Path:
    path.write_text(
        "".join(f"{int(word) & 0xFFFFFFFF:08x}\n" for word in words),
        encoding="ascii",
    )
    return path


def run_ahb_descriptor_replay(
    tmp_path: Path,
    *,
    top: str,
    source_name: str,
    descriptor_hex: Path,
    dram_hex: Path,
    command_count: int,
    descriptor_words: int,
    dram_words: int,
    descriptor_base: int,
    fence_limit: int,
    final_tag: int,
    selected_expected: list[dict],
    marker: str,
    max_rtl_cycles: int,
    register_expected: list[dict] | None = None,
) -> str:
    expected_checks = "\n".join(
        "    if (dram[{index}] !== 32'h{value:08x}) "
        '$fatal(1,"{name}[{word}] mismatch: got=%h expected={value:08x}", '
        "dram[{index}]);".format(
            index=int(item["address"]) // 4,
            value=int(item["value"]),
            name=item["name"],
            word=int(item["word"]),
        )
        for item in selected_expected
    )
    register_checks = "\n".join(
        "    rd(32'h{address:08x},status); "
        "if(status!==32'h{value:08x}) "
        '$fatal(1,"{name} mismatch: got=%h expected={value:08x}",status);'.format(
            address=int(item["address"]),
            value=int(item["value"]) & 0xFFFFFFFF,
            name=item["name"],
        )
        for item in (register_expected or [])
    )
    source = compile_zlang_top(tmp_path, top, source_name)
    return run_iverilog(
        tmp_path,
        [source],
        f"""`timescale 1ns/1ps
module tb;
  localparam integer COMMAND_COUNT = {int(command_count)};
  localparam integer DESCRIPTOR_WORDS = {int(descriptor_words)};
  localparam integer DRAM_WORDS = {int(dram_words)};
  localparam integer MAX_RTL_CYCLES = {int(max_rtl_cycles)};
  localparam [31:0] DESCRIPTOR_BASE = 32'h{int(descriptor_base):08x};
  localparam [31:0] FENCE_LIMIT = 32'h{int(fence_limit):08x};
  localparam [7:0] FINAL_TAG = 8'h{int(final_tag):02x};

  logic clk=0,rst=0;
  logic ahb_HSEL=0,ahb_HWRITE=0;
  logic [31:0] ahb_HADDR=0,ahb_HWDATA=0,ahb_HRDATA;
  logic [1:0] ahb_HTRANS=0;
  logic [2:0] ahb_HSIZE=2,ahb_HBURST=0;
  logic [3:0] ahb_HPROT=0;
  logic ahb_HMASTLOCK=0,ahb_HREADYOUT,ahb_HRESP,irq;
  wire ahb_HREADY=ahb_HREADYOUT;
  logic command_axi_ar_valid,command_axi_ar_ready;
  logic [63:0] command_axi_ar_addr;
  logic [7:0] command_axi_ar_len;
  logic [2:0] command_axi_ar_size;
  logic command_axi_r_valid,command_axi_r_ready,command_axi_r_last;
  logic [31:0] command_axi_r_data;
  logic [1:0] command_axi_r_resp=0;
  logic axi_read_ar_valid,axi_read_ar_ready;
  logic [63:0] axi_read_ar_addr;
  logic [7:0] axi_read_ar_len;
  logic [2:0] axi_read_ar_size;
  logic axi_read_r_valid,axi_read_r_ready,axi_read_r_last;
  logic [31:0] axi_read_r_data;
  logic [1:0] axi_read_r_resp=0;
  logic axi_write_aw_valid,axi_write_aw_ready;
  logic [63:0] axi_write_aw_addr;
  logic [7:0] axi_write_aw_len;
  logic [2:0] axi_write_aw_size;
  logic axi_write_w_valid,axi_write_w_ready,axi_write_w_last;
  logic [31:0] axi_write_w_data;
  logic axi_write_b_valid,axi_write_b_ready;
  logic [1:0] axi_write_b_resp=0;
  logic [31:0] dram [0:DRAM_WORDS-1];
  logic [31:0] command_memory [0:DESCRIPTOR_WORDS-1];
  logic read_active=0,write_active=0,b_pending=0;
  logic command_read_active=0;
  logic [63:0] read_addr=0,write_addr=0,command_read_addr=0;
  logic [8:0] read_left=0,write_left=0;
  logic [4:0] command_read_left=0;
  logic [31:0] status=0,cmd_status=0,perf=0;
  integer rtl_cycles=0;
  integer engine_start_cycle=0;
  integer engine_done_cycle=0;
  integer polls=0;

  always #5 clk=~clk;
  always @(posedge clk) begin
    if(rst) rtl_cycles<=0;
    else begin
      rtl_cycles<=rtl_cycles+1;
      if(rtl_cycles>=MAX_RTL_CYCLES)
        $fatal(1,"descriptor replay exceeded %0d RTL cycles",MAX_RTL_CYCLES);
    end
  end
  assign axi_read_ar_ready=!read_active;
  assign axi_read_r_valid=read_active;
  assign axi_read_r_data=dram[read_addr>>2];
  assign axi_read_r_last=read_left==1;
  assign axi_write_aw_ready=!write_active && !b_pending;
  assign axi_write_w_ready=write_active;
  assign axi_write_b_valid=b_pending;
  assign command_axi_ar_ready=!command_read_active;
  assign command_axi_r_valid=command_read_active;
  assign command_axi_r_data=command_memory[(command_read_addr-DESCRIPTOR_BASE)>>2];
  assign command_axi_r_last=command_read_left==1;

  always @(posedge clk) begin
    if(rst) begin
      read_active<=0;write_active<=0;b_pending<=0;
      command_read_active<=0;read_left<=0;write_left<=0;
      command_read_left<=0;
    end else begin
      if(axi_read_ar_valid && axi_read_ar_ready) begin
        if(axi_read_ar_len>3 || axi_read_ar_size!=2)
          $fatal(1,"bad data read burst");
        read_active<=1;read_addr<=axi_read_ar_addr;
        read_left<=axi_read_ar_len+1;
      end
      if(axi_read_r_valid && axi_read_r_ready) begin
        if(read_left==1) begin read_active<=0;read_left<=0;end
        else begin read_addr<=read_addr+4;read_left<=read_left-1;end
      end
      if(axi_write_aw_valid && axi_write_aw_ready) begin
        if(axi_write_aw_len>3 || axi_write_aw_size!=2)
          $fatal(1,"bad data write burst");
        write_active<=1;write_addr<=axi_write_aw_addr;
        write_left<=axi_write_aw_len+1;
      end
      if(axi_write_w_valid && axi_write_w_ready) begin
        dram[write_addr>>2]<=axi_write_w_data;
        if((write_left==1)!==axi_write_w_last) $fatal(1,"bad data WLAST");
        if(write_left==1) begin
          write_active<=0;write_left<=0;b_pending<=1;
        end else begin write_addr<=write_addr+4;write_left<=write_left-1;end
      end
      if(axi_write_b_valid && axi_write_b_ready) b_pending<=0;
      if(command_axi_ar_valid && command_axi_ar_ready) begin
        if(command_axi_ar_addr<DESCRIPTOR_BASE || command_axi_ar_len!=15 ||
           command_axi_ar_size!=2) $fatal(1,"bad descriptor burst");
        command_read_active<=1;command_read_addr<=command_axi_ar_addr;
        command_read_left<=16;
      end
      if(command_axi_r_valid && command_axi_r_ready) begin
        if(command_read_left==1) begin
          command_read_active<=0;command_read_left<=0;
        end else begin
          command_read_addr<=command_read_addr+4;
          command_read_left<=command_read_left-1;
        end
      end
    end
  end

  {top} dut(.*);
  task automatic tick; begin @(posedge clk);#1;end endtask
  task automatic idle_address; begin
    @(negedge clk);ahb_HSEL=0;ahb_HTRANS=0;ahb_HWRITE=0;
    ahb_HADDR=0;ahb_HSIZE=2;
  end endtask
  task automatic wr(input [31:0] addr,input [31:0] data); begin
    @(negedge clk);ahb_HSEL=1;ahb_HTRANS=2;ahb_HWRITE=1;
    ahb_HADDR=addr;ahb_HWDATA=0;ahb_HSIZE=2;tick();
    @(negedge clk);ahb_HSEL=0;ahb_HTRANS=0;ahb_HWRITE=0;
    ahb_HADDR=0;ahb_HWDATA=data;tick();
    if(ahb_HRESP || !ahb_HREADYOUT)
      $fatal(1,"AHB write error addr=%h",addr);
    if(addr==32'h00000480 && data[0]) engine_start_cycle=rtl_cycles;
    @(negedge clk);ahb_HWDATA=0;tick();
  end endtask
  task automatic rd(input [31:0] addr,output [31:0] data); begin
    @(negedge clk);ahb_HSEL=1;ahb_HTRANS=2;ahb_HWRITE=0;
    ahb_HADDR=addr;ahb_HWDATA=0;ahb_HSIZE=2;tick();
    idle_address();tick();
    if(ahb_HRESP || !ahb_HREADYOUT)
      $fatal(1,"AHB read error addr=%h",addr);
    data=ahb_HRDATA;tick();
  end endtask

  initial begin
    $readmemh("{dram_hex.as_posix()}",dram);
    $readmemh("{descriptor_hex.as_posix()}",command_memory);
    #1;rst=1;repeat(2)tick();@(negedge clk);rst=0;
    wr(32'h0200,0);wr(32'h0060,1);
    wr(32'h0214,0);wr(32'h0218,0);
    wr(32'h021c,FENCE_LIMIT);wr(32'h0220,0);wr(32'h0210,1);
    wr(32'h0484,DESCRIPTOR_BASE);wr(32'h0488,0);
    wr(32'h048c,COMMAND_COUNT);wr(32'h0480,1);
    perf=0;cmd_status=0;
    while((perf!=COMMAND_COUNT || cmd_status[3:1]!=0 ||
           cmd_status[16:9]!=FINAL_TAG) && polls<MAX_RTL_CYCLES) begin
      rd(32'h006c,perf);rd(32'h0100,cmd_status);polls=polls+1;
    end
    if(perf!=COMMAND_COUNT || cmd_status[3:1]!=0 ||
       cmd_status[16:9]!=FINAL_TAG)
      $fatal(1,"completion timeout commands=%0d status=%h cycles=%0d",
             perf,cmd_status,rtl_cycles);
    engine_done_cycle=rtl_cycles;
    rd(32'h0490,status);
    if(status[2:0]!==3'b010) $fatal(1,"command DMA status=%h",status);
    rd(32'h0494,status);
    if(status!==COMMAND_COUNT) $fatal(1,"descriptor count=%0d",status);
    rd(32'h0204,status);
    if(status!==0 || irq) $fatal(1,"disabled completion state=%h irq=%b",status,irq);
    rd(32'h0078,status);
    if(status!==0) $fatal(1,"error count=%0d",status);
    rd(32'h007c,status);
    if(status!==0) $fatal(1,"sticky error=%h",status);
    rd(32'h0470,status);
    if(status!==0) $fatal(1,"fence fault=%h",status);
{register_checks}
{expected_checks}
    $display("{marker}: PASS commands=%0d engine_cycles=%0d e2e_cycles=%0d",
             COMMAND_COUNT,engine_done_cycle-engine_start_cycle,rtl_cycles);
    $finish;
  end
endmodule
""",
    )
