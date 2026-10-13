from __future__ import annotations

from pathlib import Path

from tools.rtl_test_utils import compile_zlang_top, run_iverilog


def test_unified_buffer_dma_load_store_and_alignment_error(tmp_path: Path) -> None:
    source = compile_zlang_top(
        tmp_path, "ZtpuUnifiedBufferDma64x32", "ub_dma.zhl"
    )
    output = run_iverilog(
        tmp_path,
        [source],
        r"""`timescale 1ns/1ps
module tb;
  logic clk=0,rst=0,start=0,direction=0;
  logic [63:0] dram_base=0,ub_base=0;
  logic [15:0] length_bytes=0;
  logic busy,done,error;
  logic [7:0] error_code;

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
  logic ub_read_valid,ub_read_ready=1;
  logic [63:0] ub_read_addr;
  logic [31:0] ub_read_data;
  logic ub_write_valid,ub_write_ready=1;
  logic [63:0] ub_write_addr;
  logic [31:0] ub_write_data;
  logic [3:0] ub_write_mask;

  logic [31:0] dram [0:4095];
  logic [31:0] ub [0:255];
  logic read_active=0,write_active=0,b_pending=0;
  logic [63:0] read_addr=0,write_addr=0;
  logic [8:0] read_left=0,write_left=0;
  integer i,cycles,read_bursts,write_bursts;

  always #5 clk=~clk;
  assign axi_read_ar_ready=1;
  assign axi_read_r_valid=read_active;
  assign axi_read_r_data=dram[read_addr[13:2]];
  assign axi_read_r_last=read_left==1;
  assign axi_write_aw_ready=1;
  assign axi_write_w_ready=write_active;
  assign axi_write_b_valid=b_pending;
  assign ub_read_data=ub[ub_read_addr[9:2]];

  always @(posedge clk) begin
    if(rst) begin
      read_active<=0;write_active<=0;b_pending<=0;
      read_left<=0;write_left<=0;
    end else begin
      if(axi_read_ar_valid && axi_read_ar_ready) begin
        if(axi_read_ar_len>3 || axi_read_ar_size!=2) $fatal(1,"bad read burst");
        read_active<=1;read_addr<=axi_read_ar_addr;
        read_left<=axi_read_ar_len+1;read_bursts=read_bursts+1;
      end
      if(axi_read_r_valid && axi_read_r_ready) begin
        if(read_left==1) begin read_active<=0;read_left<=0;end
        else begin read_addr<=read_addr+4;read_left<=read_left-1;end
      end
      if(axi_write_aw_valid && axi_write_aw_ready) begin
        if(axi_write_aw_len>3 || axi_write_aw_size!=2) $fatal(1,"bad write burst");
        write_active<=1;write_addr<=axi_write_aw_addr;
        write_left<=axi_write_aw_len+1;write_bursts=write_bursts+1;
      end
      if(axi_write_w_valid && axi_write_w_ready) begin
        dram[write_addr[13:2]]<=axi_write_w_data;
        if((write_left==1)!==axi_write_w_last) $fatal(1,"bad WLAST");
        if(write_left==1) begin
          write_active<=0;write_left<=0;b_pending<=1;
        end else begin write_addr<=write_addr+4;write_left<=write_left-1;end
      end
      if(axi_write_b_valid && axi_write_b_ready) b_pending<=0;
      if(ub_write_valid && ub_write_ready) ub[ub_write_addr[9:2]]<=ub_write_data;
    end
  end

  ZtpuUnifiedBufferDma64x32 dut(.*);
  task automatic tick; begin @(posedge clk);#1; end endtask
  task automatic launch; begin start=1;tick();start=0;end endtask
  task automatic wait_done;
    begin cycles=0;while(!done && cycles<200) begin tick();cycles=cycles+1;end
      if(!done) $fatal(1,"DMA timeout");tick();end
  endtask

  initial begin
    read_bursts=0;write_bursts=0;
    for(i=0;i<4096;i=i+1) dram[i]=0;
    for(i=0;i<256;i=i+1) ub[i]=0;
    for(i=0;i<8;i=i+1) dram[('h1000>>2)+i]=32'habc00000+i;
    #1;rst=1;repeat(2)tick();@(negedge clk);rst=0;

    direction=0;dram_base='h1000;ub_base='h20;length_bytes=32;
    launch();wait_done();
    if(error || error_code!=0 || read_bursts!=2) $fatal(1,"load status mismatch");
    for(i=0;i<8;i=i+1)
      if(ub[('h20>>2)+i]!==32'habc00000+i) $fatal(1,"UB load mismatch");

    direction=1;dram_base='h2000;ub_base='h20;length_bytes=32;
    launch();wait_done();
    if(error || error_code!=0 || write_bursts!=2) $fatal(1,"store status mismatch");
    for(i=0;i<8;i=i+1)
      if(dram[('h2000>>2)+i]!==32'habc00000+i) $fatal(1,"DRAM store mismatch");

    length_bytes=6;launch();wait_done();
    if(!error || error_code!=1) $fatal(1,"alignment error mismatch");
    $display("Unified buffer DMA: PASS");$finish;
  end
endmodule
""",
    )
    assert "Unified buffer DMA: PASS" in output
