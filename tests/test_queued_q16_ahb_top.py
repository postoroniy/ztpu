from __future__ import annotations

import subprocess

from tools.rtl_test_utils import ROOT, compile_zlang_top, require_tool, run_iverilog


def test_ahb_top_hierarchy_is_semantically_valid() -> None:
    zlangc = require_tool("zlang", "ZLANGC")
    result = subprocess.run(
        [
            zlangc,
            str(ROOT / "src" / "queued_q16_ahb_top.zhl"),
            "--project",
            str(ROOT / "zlang.toml"),
            "--top",
            "ZtpuQueuedQ16AhbTop",
            "--check",
            "-v",
        ],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    assert "syntax and semantics valid" in result.stdout


def test_ahb_top_keeps_host_control_source_only() -> None:
    source = (ROOT / "src" / "queued_q16_ahb_top.zhl").read_text(encoding="ascii")
    assert "interface ahb : AHBLite<32,32>.slave @clk" in source
    assert "inst cfg : ZtpuQueuedCfgAhb64x32" in source
    assert "ahb -> cfg.ahb" in source
    assert "inst layout_cfg" not in source
    assert "inst layout_path : ZtpuLayoutPath64x32" in source
    assert "inst queued_read_arbiter : ZtpuAxiReadArbiter2x64x32" in source
    assert "inst queued_write_arbiter : ZtpuAxiWriteArbiter2x64x32" in source
    assert "inst slice : ZtpuQueuedQ16Slice" in source
    assert "cfg.status = cfg_status" in source
    assert "pending_command : ZtpuCommand = cfg.control.queued_command" in source
    assert "slice.command_valid = cfg.control.queued_valid" in source
    assert "slice.dma_fence_ub_read_enable" in source
    assert "slice.dma_fence_ub_write_enable" in source
    assert "slice.direct_dma_start = cfg.control.direct.dma.start" in source
    assert "slice.direct_mxu_start = cfg.control.direct.mxu.start" in source
    assert "slice.direct_adam_start = cfg.control.direct.adam.start" in source
    assert "slice.direct_vmu_start = cfg.control.direct.vmu.start" in source
def test_ahb_top_executes_direct_and_descriptor_commands(tmp_path) -> None:
    source = compile_zlang_top(
        tmp_path, "ZtpuQueuedQ16AhbTop", "queued_q16_ahb_top.zhl"
    )
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

  logic [31:0] dram [0:4095];
  logic [31:0] command_memory [0:31];
  logic read_active=0,write_active=0,b_pending=0;
  logic command_read_active=0;
  logic [63:0] read_addr=0,write_addr=0,command_read_addr=0;
  logic [8:0] read_left=0,write_left=0;
  logic [4:0] command_read_left=0;
  logic [31:0] status=0,head=0,perf=0;
  integer i,cycles;

  always #5 clk=~clk;
  assign axi_read_ar_ready=!read_active;
  assign axi_read_r_valid=read_active;
  assign axi_read_r_data=dram[read_addr[13:2]];
  assign axi_read_r_last=read_left==1;
  assign axi_write_aw_ready=!write_active && !b_pending;
  assign axi_write_w_ready=write_active;
  assign axi_write_b_valid=b_pending;
  assign command_axi_ar_ready=!command_read_active;
  assign command_axi_r_valid=command_read_active;
  assign command_axi_r_data=command_memory[command_read_addr[6:2]];
  assign command_axi_r_last=command_read_left==1;

  always @(posedge clk) begin
    if(rst) begin
      read_active<=0;write_active<=0;b_pending<=0;
      command_read_active<=0;read_left<=0;write_left<=0;
      command_read_left<=0;
    end else begin
      if(axi_read_ar_valid && axi_read_ar_ready) begin
        if(axi_read_ar_len>3 || axi_read_ar_size!=2)
          $fatal(1,"bad AHB-top read burst");
        read_active<=1;read_addr<=axi_read_ar_addr;
        read_left<=axi_read_ar_len+1;
      end
      if(axi_read_r_valid && axi_read_r_ready) begin
        if(read_left==1) begin read_active<=0;read_left<=0;end
        else begin read_addr<=read_addr+4;read_left<=read_left-1;end
      end
      if(axi_write_aw_valid && axi_write_aw_ready) begin
        if(axi_write_aw_len>3 || axi_write_aw_size!=2)
          $fatal(1,"bad AHB-top write burst");
        write_active<=1;write_addr<=axi_write_aw_addr;
        write_left<=axi_write_aw_len+1;
      end
      if(axi_write_w_valid && axi_write_w_ready) begin
        dram[write_addr[13:2]]<=axi_write_w_data;
        if((write_left==1)!==axi_write_w_last)
          $fatal(1,"bad AHB-top WLAST");
        if(write_left==1) begin
          write_active<=0;write_left<=0;b_pending<=1;
        end else begin write_addr<=write_addr+4;write_left<=write_left-1;end
      end
      if(axi_write_b_valid && axi_write_b_ready) b_pending<=0;
      if(command_axi_ar_valid && command_axi_ar_ready) begin
        if(command_axi_ar_len!=15 || command_axi_ar_size!=2)
          $fatal(1,"bad AHB-top descriptor burst");
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

  ZtpuQueuedQ16AhbTop dut(.*);

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
  task automatic push_dma(
    input [3:0] opcode,input [31:0] dram_base,input [31:0] ub_base,
    input [15:0] length,input [7:0] tag,input [7:0] dependency
  ); begin
    wr(32'h00e8,opcode);wr(32'h00ec,dram_base);wr(32'h00f0,0);
    wr(32'h01d4,ub_base);wr(32'h01d8,0);wr(32'h00f4,length);
    wr(32'h00f8,tag);wr(32'h00fc,dependency);wr(32'h00e4,1);
  end endtask
  task automatic wait_for_count(input [3:0] expected); begin
    status=0;cycles=0;
    while(status[3:0]!=expected && cycles<500) begin
      rd(32'h0204,status);cycles=cycles+1;
    end
    if(status[3:0]!=expected)
      $fatal(1,"completion timeout status=%h expected=%0d",status,expected);
  end endtask
  task automatic pop_expected(input [31:0] expected); begin
    rd(32'h0208,head);
    if(head!==expected) $fatal(1,"completion head=%h expected=%h",head,expected);
    wr(32'h020c,1);
  end endtask

  initial begin
    for(i=0;i<4096;i=i+1) dram[i]=0;
    for(i=0;i<32;i=i+1) command_memory[i]=0;
    dram[('h1000>>2)+0]=32'h11223344;
    dram[('h1000>>2)+1]=32'h55667788;
    dram[('h1100>>2)+0]=32'haabbccdd;
    dram[('h1100>>2)+1]=32'h12345678;

    #1;rst=1;repeat(2)tick();@(negedge clk);rst=0;
    wr(32'h0200,5);wr(32'h0060,1);

    // Program intersecting global, UB-domain, and UB-master windows.
    wr(32'h0214,32'h1000);wr(32'h0218,0);wr(32'h021c,32'h4000);
    wr(32'h0220,0);wr(32'h0210,1);
    wr(32'h0250,32'h1000);wr(32'h0254,0);wr(32'h0258,32'h3000);
    wr(32'h025c,0);wr(32'h024c,1);
    wr(32'h02f0,32'h1000);wr(32'h02f4,0);wr(32'h02f8,32'h1800);
    wr(32'h02fc,0);wr(32'h02ec,1);
    wr(32'h0304,32'h2000);wr(32'h0308,0);wr(32'h030c,32'h2800);
    wr(32'h0310,0);wr(32'h0300,1);

    // Direct-register UB DMA bypasses the command/completion queues
    // while sharing the same fenced AXI master and unified buffer.
    wr(32'h0194,32'h1000);wr(32'h0198,0);
    wr(32'h019c,32'h80);wr(32'h01a0,0);wr(32'h01a4,8);
    wr(32'h0190,3);repeat(20)tick();rd(32'h01a8,status);
    if(status[2:0]!==0)$fatal(1,"direct UB load status=%h",status);
    wr(32'h0194,32'h2400);wr(32'h0190,7);repeat(20)tick();rd(32'h01a8,status);
    if(status[2:0]!==0 || dram[('h2400>>2)+0]!==32'h11223344 ||
       dram[('h2400>>2)+1]!==32'h55667788)
      $fatal(1,"direct UB DMA copy/status mismatch status=%h",status);
    rd(32'h0204,status);
    if(status[3:0]!==0)$fatal(1,"direct UB DMA entered completion queue=%h",status);

    // Direct Q16 MXU: A times identity, using the direct registers.
    dram[('h1500>>2)+0]=32'h00010000;dram[('h1500>>2)+1]=32'h00020000;
    dram[('h1500>>2)+2]=32'h00030000;dram[('h1500>>2)+3]=32'h00040000;
    dram[('h1500>>2)+4]=32'h00010000;dram[('h1500>>2)+5]=0;
    dram[('h1500>>2)+6]=0;dram[('h1500>>2)+7]=32'h00010000;
    wr(32'h0194,32'h1500);wr(32'h019c,0);wr(32'h01a4,32);wr(32'h0190,3);
    repeat(30)tick();
    wr(32'h01b4,0);wr(32'h01bc,16);wr(32'h01c4,32);wr(32'h01dc,64);
    wr(32'h01cc,2);wr(32'h01f4,3);wr(32'h01f8,8);wr(32'h01fc,8);
    wr(32'h01b0,32'h0b);repeat(100)tick();rd(32'h01d0,status);
    if(status[2:0]!==0)$fatal(1,"direct MXU status=%h",status);
    wr(32'h0194,32'h2500);wr(32'h019c,32);wr(32'h01a4,16);wr(32'h0190,7);
    repeat(30)tick();
    if(dram[('h2500>>2)+0]!==32'h00010000 ||
       dram[('h2500>>2)+1]!==32'h00020000 ||
       dram[('h2500>>2)+2]!==32'h00030000 ||
       dram[('h2500>>2)+3]!==32'h00040000)
      $fatal(1,"direct MXU result mismatch");

    // Direct VMU ReLU reads the MXU result and writes another UB window.
    wr(32'h0370,9);wr(32'h0390,32);wr(32'h0398,48);wr(32'h03a0,4);
    wr(32'h036c,3);repeat(100)tick();rd(32'h038c,status);
    if(status[2:0]!==0)$fatal(1,"direct VMU status=%h",status);
    wr(32'h0194,32'h2600);wr(32'h019c,48);wr(32'h01a4,16);wr(32'h0190,7);
    repeat(30)tick();
    if(dram[('h2600>>2)+0]!==32'h00010000 ||
       dram[('h2600>>2)+1]!==32'h00020000 ||
       dram[('h2600>>2)+2]!==32'h00030000 ||
       dram[('h2600>>2)+3]!==32'h00040000)
      $fatal(1,"direct VMU result mismatch");

    // Direct one-word ADAM update, including clear pulse and power readback.
    dram[('h1700>>2)+0]=32'h00010000;dram[('h1700>>2)+1]=32'h00002000;
    dram[('h1700>>2)+2]=0;dram[('h1700>>2)+3]=0;
    wr(32'h0194,32'h1700);wr(32'h019c,64);wr(32'h01a4,16);wr(32'h0190,3);
    repeat(30)tick();
    wr(32'h0330,64);wr(32'h0338,68);wr(32'h0340,72);wr(32'h0348,76);
    wr(32'h0350,1);wr(32'h0354,655);wr(32'h0358,58982);
    wr(32'h035c,64881);wr(32'h0360,7);wr(32'h0328,7);
    repeat(300)tick();rd(32'h032c,status);
    if(status[2:0]!==0)$fatal(1,"direct ADAM status=%h",status);
    rd(32'h0364,status);if(status!==58982)$fatal(1,"direct ADAM b1t=%h",status);
    rd(32'h0368,status);if(status!==64881)$fatal(1,"direct ADAM b2t=%h",status);
    wr(32'h0194,32'h2700);wr(32'h019c,64);wr(32'h01a4,16);wr(32'h0190,7);
    repeat(30)tick();
    if(dram[('h2700>>2)+0]!==32'h0000fd6c ||
       dram[('h2700>>2)+1]!==32'h00002000 ||
       dram[('h2700>>2)+2]!==32'h00000333 ||
       dram[('h2700>>2)+3]!==32'h0000000a)
      $fatal(1,"direct ADAM result mismatch");
    rd(32'h0204,status);
    if(status[3:0]!==0)$fatal(1,"direct engines entered completion queue=%h",status);

    push_dma(3,32'h1000,0,8,1,0);
    push_dma(4,32'h2000,0,8,2,1);
    wait_for_count(2);
    if(!irq || dram[('h2000>>2)+0]!==32'h11223344 ||
       dram[('h2000>>2)+1]!==32'h55667788)
      $fatal(1,"AHB direct queued copy mismatch");
    pop_expected(32'h01000301);pop_expected(32'h01000402);

    // Debug CSRs expose real queue and UB-dispatch state. The first committed
    // queue entry remains sticky while the UB-start snapshot tracks the latest
    // load/store launch.
    rd(32'h0428,status);if(status!==3) $fatal(1,"debug UB start flags=%h",status);
    rd(32'h042c,status);if(status!==32'h2000)
      $fatal(1,"debug UB start DRAM=%h",status);
    rd(32'h0434,status);if(status!==8) $fatal(1,"debug UB start length=%h",status);
    rd(32'h0450,status);if(status!==32'h1000)
      $fatal(1,"debug queue push address=%h",status);
    rd(32'h0458,status);if(status!==32'h00130008)
      $fatal(1,"debug queue push meta=%h",status);
    rd(32'h045c,status);if(status!==32'h1000)
      $fatal(1,"debug queue head address=%h",status);
    rd(32'h0468,status);if(status!==32'h00020002)
      $fatal(1,"debug queue pointers=%h",status);
    rd(32'h046c,status);if(status!==32'h00020000)
      $fatal(1,"debug queue state=%h",status);

    // Fetch dependent load/store descriptors through the AHB-started DMA.
    command_memory[0]=32'h00020303;command_memory[1]=8;
    command_memory[2]=32'h00001100;command_memory[3]=0;
    command_memory[4]=32'h00000040;command_memory[5]=0;
    command_memory[16]=32'h00030404;command_memory[17]=8;
    command_memory[18]=32'h00002100;command_memory[19]=0;
    command_memory[20]=32'h00000040;command_memory[21]=0;
    wr(32'h0484,32'h3000);wr(32'h0488,0);wr(32'h048c,2);wr(32'h0480,1);
    wait_for_count(2);
    if(dram[('h2100>>2)+0]!==32'haabbccdd ||
       dram[('h2100>>2)+1]!==32'h12345678)
      $fatal(1,"AHB descriptor queued copy mismatch");
    rd(32'h0490,status);
    if(status[6:0]!==7'b0000010) $fatal(1,"command DMA status=%h",status);
    rd(32'h0494,status);
    if(status!==2) $fatal(1,"command DMA fetched count=%h",status);
    pop_expected(32'h01000303);pop_expected(32'h01000404);
    if(irq) $fatal(1,"IRQ remained asserted after completion drain");

    rd(32'h006c,perf);if(perf!==4) $fatal(1,"command count=%h",perf);
    // Six data read bursts (the 32-byte preload splits in two) plus two
    // 64-byte descriptor fetches.
    rd(32'h0070,perf);if(perf!==8) $fatal(1,"DMA read count=%h",perf);
    rd(32'h0074,perf);if(perf!==6) $fatal(1,"DMA write count=%h",perf);

    // Queued opcode 1 -> address remap -> fenced Layout DMA -> shared AXI.
    dram[('h1200>>2)]=32'hcafef00d;
    wr(32'h0084,0); // NCHW -> NCHW, one element.
    wr(32'h0088,32'h1200);wr(32'h008c,0);
    wr(32'h0090,32'h2200);wr(32'h0094,0);
    wr(32'h0098,4);wr(32'h009c,4);wr(32'h00a0,4);
    wr(32'h00a4,4);wr(32'h00a8,4);
    wr(32'h00ac,4);wr(32'h00b0,4);wr(32'h00b4,4);
    wr(32'h00b8,4);wr(32'h00bc,4);
    wr(32'h00c0,1);wr(32'h00c4,1);wr(32'h00c8,1);wr(32'h00cc,1);
    wr(32'h0080,2); // DMA enabled; scheduler supplies the start pulse.
    push_dma(1,0,0,0,5,0);
    wait_for_count(1);
    cycles=0;
    while(dram[('h2200>>2)]!==32'hcafef00d && cycles<100) begin
      tick();cycles=cycles+1;
    end
    if(dram[('h2200>>2)]!==32'hcafef00d)
      $fatal(1,"layout DMA did not reach shared AXI");
    pop_expected(32'h01000105);
    rd(32'h0070,perf);if(perf!==9) $fatal(1,"combined read count=%h",perf);
    rd(32'h0074,perf);if(perf!==7) $fatal(1,"combined write count=%h",perf);

    // A layout-domain window intersects the existing global window and blocks
    // the same read before arbitration. The sticky record uses master ID 5.
    wr(32'h023c,32'h3000);wr(32'h0240,0);
    wr(32'h0244,32'h4000);wr(32'h0248,0);wr(32'h0238,1);
    // Opcode 2 completes on the DMA terminal response and reports failure in
    // the completion status while the sticky fault retains the AXI context.
    push_dma(2,0,0,0,6,0);
    wait_for_count(1);
    pop_expected(32'h01001206);
    rd(32'h0470,status);
    if(status[0]!==1 || status[2]!==0 || status[7:4]!==5)
      $fatal(1,"layout fence fault status=%h",status);
    rd(32'h0474,status);
    if(status!==32'h1200)$fatal(1,"layout fence address=%h",status);
    rd(32'h0078,perf);if(perf!==1) $fatal(1,"combined error count=%h",perf);
    wr(32'h0470,3);rd(32'h0470,status);
    if(status[1:0]!==0)$fatal(1,"layout fence clear failed=%h",status);
    $display("Queued Q16 AHB top: PASS");$finish;
  end
endmodule
""",
    )
    assert "Queued Q16 AHB top: PASS" in output
