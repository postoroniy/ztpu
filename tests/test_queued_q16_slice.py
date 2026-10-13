from __future__ import annotations

from pathlib import Path

from tools.rtl_test_utils import compile_zlang_top, run_iverilog


def test_queued_q16_load_compute_store_and_completions(tmp_path: Path) -> None:
    source = compile_zlang_top(
        tmp_path, "ZtpuQueuedQ16Slice", "queued_q16_slice.zhl"
    )
    output = run_iverilog(
        tmp_path,
        [source],
        r"""`timescale 1ns/1ps
module tb;
  logic clk=0,rst=0;
  logic command_valid=0,command_ready,command_supported;
  logic [3:0] command_opcode=0;
  logic [63:0] command_address=0,command_auxiliary=0;
  logic [15:0] command_length=0;
  logic [7:0] command_tag=0,command_dependency_tag=0;
  logic [63:0] command_src1_base=0;
  logic [31:0] command_scalar0=0,command_scalar1=0;
  logic [31:0] command_scalar2=0,command_scalar3=0;
  logic command_mxu_valid=0;
  logic [63:0] command_mxu_a_base=0,command_mxu_b_base=0;
  logic [63:0] command_mxu_c_base=0,command_mxu_acc_base=0;
  logic [31:0] command_mxu_a_stride=0,command_mxu_b_stride=0;
  logic [31:0] command_mxu_k_dim=0;
  logic command_mxu_accum_en=0,command_mxu_acc_clear=0;
  logic command_mxu_spill_en=0,command_mxu_restore_en=0;
  logic [2:0] command_mxu_mode=0;
  logic command_mxu_a_transpose=0,command_mxu_b_transpose=0;
  logic command_mxu_zs_enable_a=0,command_mxu_zs_enable_b=0;
  logic command_adam_valid=0,command_adam_clear=0;
  logic [63:0] command_adam_m_base=0,command_adam_v_base=0;
  logic [31:0] command_adam_lr=0,command_adam_beta1=0;
  logic [31:0] command_adam_beta2=0,command_adam_eps=0;
  logic direct_dma_enable=0,direct_dma_start=0,direct_dma_store=0;
  logic [63:0] direct_dma_dram_base=0,direct_dma_ub_base=0;
  logic [31:0] direct_dma_length=0;
  logic direct_dma_busy,direct_dma_done,direct_dma_error;
  logic [7:0] direct_dma_error_code;
  logic direct_mxu_enable=0,direct_mxu_start=0;
  logic direct_mxu_accum_en=0,direct_mxu_acc_clear=0;
  logic direct_mxu_spill_en=0,direct_mxu_restore_en=0;
  logic [63:0] direct_mxu_a_base=0,direct_mxu_b_base=0;
  logic [63:0] direct_mxu_c_base=0,direct_mxu_acc_base=0;
  logic [31:0] direct_mxu_a_stride=0,direct_mxu_b_stride=0;
  logic [31:0] direct_mxu_k_dim=0;
  logic direct_mxu_rq_enable=0;logic [31:0] direct_mxu_rq_scale=0;
  logic [7:0] direct_mxu_rq_shift=0;logic [31:0] direct_mxu_rq_zero=0;
  logic [2:0] direct_mxu_mode=0;
  logic direct_mxu_a_transpose=0,direct_mxu_b_transpose=0;
  logic direct_mxu_zs_enable_a=0,direct_mxu_zs_enable_b=0;
  logic direct_mxu_busy,direct_mxu_done,direct_mxu_error;
  logic direct_adam_enable=0,direct_adam_start=0,direct_adam_clear=0;
  logic [63:0] direct_adam_w_base=0,direct_adam_g_base=0;
  logic [63:0] direct_adam_m_base=0,direct_adam_v_base=0;
  logic [31:0] direct_adam_length=0,direct_adam_lr=0;
  logic [31:0] direct_adam_beta1=0,direct_adam_beta2=0,direct_adam_eps=0;
  logic direct_adam_busy,direct_adam_done,direct_adam_error;
  logic [31:0] direct_adam_b1t,direct_adam_b2t;
  logic direct_vmu_enable=0,direct_vmu_start=0;logic [3:0] direct_vmu_op=0;
  logic [63:0] direct_vmu_src0_base=0,direct_vmu_src1_base=0;
  logic [63:0] direct_vmu_dst_base=0;logic [31:0] direct_vmu_length=0;
  logic [31:0] direct_vmu_scalar0=0,direct_vmu_scalar1=0;
  logic [31:0] direct_vmu_scalar2=0,direct_vmu_scalar3=0;
  logic direct_vmu_busy,direct_vmu_done,direct_vmu_error;
  logic command_dma_start=0,command_dma_clear=0;
  logic [63:0] command_dma_base=0;
  logic [23:0] command_dma_count=0;
  logic command_dma_busy,command_dma_done,command_dma_error;
  logic [3:0] command_dma_error_code;
  logic [23:0] command_dma_fetched_count;
  logic dma_fence_enable=0;
  logic [63:0] dma_fence_base=0,dma_fence_limit=0;
  logic dma_fence_ub_enable=0;
  logic [63:0] dma_fence_ub_base=0,dma_fence_ub_limit=0;
  logic dma_fence_ub_read_enable=0,dma_fence_ub_write_enable=0;
  logic [63:0] dma_fence_ub_read_base=0,dma_fence_ub_read_limit=0;
  logic [63:0] dma_fence_ub_write_base=0,dma_fence_ub_write_limit=0;
  logic dma_fence_fault_clear_valid=0,dma_fence_fault_clear_overflow=0;
  logic external_fence_fault=0,external_fence_fault_write=0;
  logic [3:0] external_fence_fault_master=0;
  logic [63:0] external_fence_fault_addr=0;
  logic [7:0] external_fence_fault_len=0;
  logic [2:0] external_fence_fault_size=0;
  logic dma_fence_fault_valid,dma_fence_fault_overflow,dma_fence_fault_write;
  logic [3:0] dma_fence_fault_master;
  logic [63:0] dma_fence_fault_addr;
  logic [7:0] dma_fence_fault_len;
  logic [2:0] dma_fence_fault_size;
  logic perf_enable=0,perf_clear=0,perf_clear_error=0;
  logic external_busy=0,external_dma_read=0,external_dma_write=0;
  logic external_error_event=0;logic [7:0] external_error_code=0;
  logic external_layout_source_tiler=0;
  logic external_layout_busy=0,external_layout_done=0;
  logic external_layout_error=0,external_layout_dma_busy=0;
  logic external_layout_dma_done=0,external_layout_dma_error=0;
  logic external_layout_command_start;
  logic [31:0] perf_cycles,perf_busy_cycles,perf_command_count;
  logic [31:0] perf_dma_read_count,perf_dma_write_count,perf_error_count;
  logic perf_error_valid;logic [7:0] perf_error_code;
  logic [31:0] mxu_zs_steps,mxu_zs_total_macs;
  logic [31:0] mxu_zs_active_macs,mxu_zs_skipped_macs;
  logic command_axi_ar_valid,command_axi_ar_ready;
  logic [63:0] command_axi_ar_addr;
  logic [7:0] command_axi_ar_len;
  logic [2:0] command_axi_ar_size;
  logic command_axi_r_valid,command_axi_r_ready,command_axi_r_last;
  logic [31:0] command_axi_r_data;
  logic [1:0] command_axi_r_resp=0;
  logic [2:0] command_count;
  logic [7:0] last_done_tag;
  logic debug_queue_output_valid,debug_queue_input_valid;
  logic [63:0] debug_queue_output_address,debug_queue_output_auxiliary;
  logic [63:0] debug_queue_input_address,debug_queue_input_auxiliary;
  logic [15:0] debug_queue_output_length,debug_queue_input_length;
  logic [3:0] debug_queue_output_opcode,debug_queue_input_opcode;
  logic debug_queue_push_seen,debug_queue_head_seen;
  logic [63:0] debug_queue_push_address,debug_queue_push_auxiliary;
  logic [63:0] debug_queue_head_address,debug_queue_head_auxiliary;
  logic [15:0] debug_queue_push_length,debug_queue_head_length;
  logic [3:0] debug_queue_push_opcode,debug_queue_head_opcode;
  logic debug_queue_empty,debug_queue_head_valid;
  logic [15:0] debug_queue_head_pointer,debug_queue_tail_pointer;
  logic [15:0] debug_queue_count;
  logic debug_ub_launch_pending,debug_ub_capture_armed;
  logic debug_ub_capture_ok,debug_ub_capture,debug_ub_start;
  logic [63:0] debug_ub_launch_dram_base,debug_ub_launch_ub_base;
  logic [15:0] debug_ub_launch_length;
  logic debug_ub_start_seen,debug_ub_start_store;
  logic [63:0] debug_ub_start_dram_base,debug_ub_start_ub_base;
  logic [15:0] debug_ub_start_length;

  logic completion_enable=1,completion_clear=0,completion_pop=0,completion_valid;
  logic [7:0] completion_tag,completion_error;
  logic [3:0] completion_opcode,completion_status,completion_count;
  logic completion_overflow;

  logic axi_read_ar_valid,axi_read_ar_ready;
  logic [63:0] axi_read_ar_payload_addr;
  logic [7:0] axi_read_ar_payload_len;
  logic [2:0] axi_read_ar_payload_size;
  logic axi_read_r_valid,axi_read_r_ready,axi_read_r_payload_last;
  logic [31:0] axi_read_r_payload_data;
  logic [1:0] axi_read_r_payload_resp=0;
  logic axi_write_aw_valid,axi_write_aw_ready;
  logic [63:0] axi_write_aw_payload_addr;
  logic [7:0] axi_write_aw_payload_len;
  logic [2:0] axi_write_aw_payload_size;
  logic axi_write_w_valid,axi_write_w_ready,axi_write_w_payload_last;
  logic [31:0] axi_write_w_payload_data;
  logic axi_write_b_valid,axi_write_b_ready;
  logic [1:0] axi_write_b_payload_resp=0;

  logic [31:0] dram [0:4095];
  logic [31:0] command_memory [0:31];
  logic read_active=0,write_active=0,b_pending=0;
  logic [63:0] read_addr=0,write_addr=0;
  logic [8:0] read_left=0,write_left=0;
  logic command_read_active=0;
  logic [63:0] command_read_addr=0;
  logic [4:0] command_read_left=0;
  integer i,cycles,bus_cycle=0;

  always #5 clk=~clk;
  assign axi_read_ar_ready=(bus_cycle%3)!=1;
  assign axi_read_r_valid=read_active && ((bus_cycle%4)!=2);
  assign axi_read_r_payload_data=dram[read_addr[13:2]];
  assign axi_read_r_payload_last=read_left==1;
  assign axi_write_aw_ready=(bus_cycle%4)!=1;
  assign axi_write_w_ready=write_active && ((bus_cycle%3)!=0);
  assign axi_write_b_valid=b_pending && ((bus_cycle%4)!=3);
  assign command_axi_ar_ready=(bus_cycle%4)!=2;
  assign command_axi_r_valid=command_read_active && ((bus_cycle%5)!=3);
  assign command_axi_r_data=command_memory[command_read_addr[6:2]];
  assign command_axi_r_last=command_read_left==1;

  always @(posedge clk) begin
    if(rst) begin
      read_active<=0;write_active<=0;b_pending<=0;
      read_left<=0;write_left<=0;
      command_read_active<=0;command_read_addr<=0;command_read_left<=0;
      bus_cycle<=0;
    end else begin
      bus_cycle<=bus_cycle+1;
      if(axi_read_ar_valid && axi_read_ar_ready) begin
        if(axi_read_ar_payload_len>3 || axi_read_ar_payload_size!=2)
          $fatal(1,"bad queued read burst");
        read_active<=1;read_addr<=axi_read_ar_payload_addr;
        read_left<=axi_read_ar_payload_len+1;
      end
      if(axi_read_r_valid && axi_read_r_ready) begin
        if(read_left==1) begin read_active<=0;read_left<=0;end
        else begin read_addr<=read_addr+4;read_left<=read_left-1;end
      end
      if(axi_write_aw_valid && axi_write_aw_ready) begin
        if(axi_write_aw_payload_len>3 || axi_write_aw_payload_size!=2)
          $fatal(1,"bad queued write burst");
        write_active<=1;write_addr<=axi_write_aw_payload_addr;
        write_left<=axi_write_aw_payload_len+1;
      end
      if(axi_write_w_valid && axi_write_w_ready) begin
        dram[write_addr[13:2]]<=axi_write_w_payload_data;
        if((write_left==1)!==axi_write_w_payload_last) $fatal(1,"bad queued WLAST");
        if(write_left==1) begin
          write_active<=0;write_left<=0;b_pending<=1;
        end else begin write_addr<=write_addr+4;write_left<=write_left-1;end
      end
      if(axi_write_b_valid && axi_write_b_ready) b_pending<=0;
      if(command_axi_ar_valid && command_axi_ar_ready) begin
        if(command_axi_ar_len!=15 || command_axi_ar_size!=2)
          $fatal(1,"bad command descriptor read burst");
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

  ZtpuQueuedQ16Slice dut(.*);

  task automatic tick; begin @(posedge clk);#1; end endtask
  task automatic clear_payload;
    begin
      command_address=0;command_auxiliary=0;command_length=0;
      command_src1_base=0;command_scalar0=0;command_scalar1=0;
      command_scalar2=0;command_scalar3=0;
      command_mxu_valid=0;command_mxu_a_base=0;command_mxu_b_base=0;
      command_mxu_c_base=0;command_mxu_acc_base=0;
      command_mxu_a_stride=0;command_mxu_b_stride=0;command_mxu_k_dim=0;
      command_mxu_accum_en=0;command_mxu_acc_clear=0;
      command_mxu_spill_en=0;command_mxu_restore_en=0;
      command_mxu_mode=0;command_mxu_a_transpose=0;
      command_mxu_b_transpose=0;
      command_adam_valid=0;command_adam_clear=0;
      command_adam_m_base=0;command_adam_v_base=0;
      command_adam_lr=0;command_adam_beta1=0;
      command_adam_beta2=0;command_adam_eps=0;
    end
  endtask
  task automatic push_adam(input [7:0] tag,input [7:0] dependency);
    begin
      clear_payload();command_opcode=6;command_address='h00;
      command_auxiliary='h40;command_length=3;
      command_tag=tag;command_dependency_tag=dependency;
      command_adam_valid=1;command_adam_clear=1;
      command_adam_m_base='h80;command_adam_v_base='hc0;
      command_adam_lr=655;command_adam_beta1=58982;
      command_adam_beta2=64881;command_adam_eps=7;
      while(!command_ready) tick();
      command_valid=1;tick();command_valid=0;
    end
  endtask
  task automatic push_dma(
    input [3:0] opcode,input [63:0] dram_base,input [63:0] ub_base,
    input [15:0] length,input [7:0] tag,input [7:0] dependency
  );
    begin
      clear_payload();command_opcode=opcode;command_address=dram_base;
      command_auxiliary=ub_base;command_length=length;
      command_tag=tag;command_dependency_tag=dependency;
      while(!command_ready) tick();
      command_valid=1;tick();command_valid=0;
    end
  endtask
  task automatic push_dcopy(
    input [63:0] source_base,input [63:0] destination_base,
    input [63:0] ub_base,input [15:0] row_bytes,input [31:0] rows,
    input [31:0] source_stride,input [31:0] destination_stride,
    input [7:0] tag,input [7:0] dependency
  );
    begin
      clear_payload();command_opcode=8;command_address=source_base;
      command_src1_base=destination_base;command_auxiliary=ub_base;
      command_length=row_bytes;command_scalar0=rows;
      command_scalar1=source_stride;command_scalar2=destination_stride;
      command_tag=tag;command_dependency_tag=dependency;
      while(!command_ready) tick();
      command_valid=1;tick();command_valid=0;
    end
  endtask
  task automatic push_compute(input [7:0] tag,input [7:0] dependency);
    begin
      clear_payload();command_opcode=5;command_tag=tag;
      command_dependency_tag=dependency;command_mxu_valid=1;
      command_mxu_a_base='h00;command_mxu_b_base='h40;
      command_mxu_c_base='h80;command_mxu_acc_base='hc0;
      command_mxu_a_stride=8;command_mxu_b_stride=8;
      command_mxu_k_dim=2;command_mxu_acc_clear=1;command_mxu_mode=3;
      while(!command_ready) tick();
      command_valid=1;tick();command_valid=0;
    end
  endtask
  task automatic push_vmu_relu(input [7:0] tag,input [7:0] dependency);
    begin
      clear_payload();command_opcode=7;command_address='h80;
      command_auxiliary='h100;command_length=(9<<12)|4;
      command_tag=tag;command_dependency_tag=dependency;
      while(!command_ready) tick();
      command_valid=1;tick();command_valid=0;
    end
  endtask
  task automatic push_vmu(
    input [3:0] operation,input [63:0] src0,input [63:0] src1,
    input [63:0] dst,input [11:0] words,input [31:0] scalar0,
    input [31:0] scalar1,input [31:0] scalar2,input [31:0] scalar3,
    input [7:0] tag,input [7:0] dependency
  );
    begin
      clear_payload();command_opcode=7;command_address=src0;
      command_src1_base=src1;command_auxiliary=dst;
      command_length=(operation<<12)|words;
      command_scalar0=scalar0;command_scalar1=scalar1;
      command_scalar2=scalar2;command_scalar3=scalar3;command_tag=tag;
      command_dependency_tag=dependency;
      while(!command_ready) tick();
      command_valid=1;tick();command_valid=0;
    end
  endtask
  task automatic check_and_pop_completion(
    input [7:0] expected_tag,input [3:0] expected_opcode
  );
    begin
      if(!completion_valid || completion_tag!=expected_tag ||
         completion_opcode!=expected_opcode || completion_status!=0 ||
         completion_error!=0)
        $fatal(1,"completion mismatch tag=%0d opcode=%0d status=%0d error=%0d",
          completion_tag,completion_opcode,completion_status,completion_error);
      completion_pop=1;tick();completion_pop=0;
    end
  endtask

  initial begin
    for(i=0;i<4096;i=i+1) dram[i]=0;
    for(i=0;i<32;i=i+1) command_memory[i]=0;
    // A = [[0.5,-0.25],[0.75,0.125]].
    dram[('h1000>>2)+0]=32'h00008000;
    dram[('h1000>>2)+1]=32'hffffc000;
    dram[('h1000>>2)+2]=32'h0000c000;
    dram[('h1000>>2)+3]=32'h00002000;
    // B = [[0.25,-0.5],[0.5,0.25]].
    dram[('h1100>>2)+0]=32'h00004000;
    dram[('h1100>>2)+1]=32'hffff8000;
    dram[('h1100>>2)+2]=32'h00008000;
    dram[('h1100>>2)+3]=32'h00004000;

    #1;rst=1;repeat(2)tick();@(negedge clk);rst=0;

    command_opcode=15;command_mxu_valid=0;command_valid=1;#1;
    if(command_supported || command_ready)
      $fatal(1,"unsupported command was accepted");
    tick();command_valid=0;

    push_dma(3,'h1000,'h00,16,1,0);
    push_dma(3,'h1100,'h40,16,2,1);
    push_compute(3,2);
    push_vmu_relu(4,3);
    push_dma(4,'h2000,'h100,16,5,4);

    cycles=0;
    while(completion_count!=5 && cycles<500) begin tick();cycles=cycles+1;end
    if(completion_count!=5) $fatal(1,"queued Q16 slice timeout");
    if(last_done_tag!=5 || command_count!=0 || completion_overflow)
      $fatal(1,"final queue state mismatch");

    if(dram[('h2000>>2)+0]!==32'h00000000 ||
       dram[('h2000>>2)+1]!==32'h00000000 ||
       dram[('h2000>>2)+2]!==32'h00004000 ||
       dram[('h2000>>2)+3]!==32'h00000000) begin
      $display("got C=%h,%h,%h,%h",dram[('h2000>>2)+0],
        dram[('h2000>>2)+1],dram[('h2000>>2)+2],dram[('h2000>>2)+3]);
      $fatal(1,"queued Q16 DRAM result mismatch");
    end

    check_and_pop_completion(1,3);
    check_and_pop_completion(2,3);
    check_and_pop_completion(3,5);
    check_and_pop_completion(4,7);
    check_and_pop_completion(5,4);
    if(completion_count!=0 || completion_valid)
      $fatal(1,"completion queue did not drain");

    // The integration layer preserves the DMA error namespace in completions.
    push_dma(3,'h3000,'h00,6,6,5);
    cycles=0;
    while(!completion_valid && cycles<100) begin tick();cycles=cycles+1;end
    if(!completion_valid || completion_tag!=6 || completion_opcode!=3 ||
       completion_status!=1 || completion_error!=8'h41)
      $fatal(1,"DMA error completion mismatch");
    if(last_done_tag!=6) $fatal(1,"DMA error did not retire command tag");
    completion_pop=1;tick();completion_pop=0;

    // Full queued VMU path: softmax([0,0,0,0]) = [0.25,0.25,0.25,0.25].
    dram[('h1200>>2)+0]=0;dram[('h1200>>2)+1]=0;
    dram[('h1200>>2)+2]=0;dram[('h1200>>2)+3]=0;
    push_dma(3,'h1200,'h180,16,7,6);
    push_vmu(4,'h180,0,'h1c0,4,0,0,0,0,8,7);
    push_dma(4,'h2100,'h1c0,16,9,8);
    cycles=0;
    while(completion_count!=3 && cycles<500) begin tick();cycles=cycles+1;end
    if(completion_count!=3) $fatal(1,"queued softmax timeout");
    if(dram[('h2100>>2)+0]!==32'h00004000 ||
       dram[('h2100>>2)+1]!==32'h00004000 ||
       dram[('h2100>>2)+2]!==32'h00004000 ||
       dram[('h2100>>2)+3]!==32'h00004000)
      $fatal(1,"queued softmax result mismatch");
    check_and_pop_completion(7,3);
    check_and_pop_completion(8,7);
    check_and_pop_completion(9,4);

    // Q16-to-Q8 gather/requant packs four strided lanes per output word.
    dram[('h1300>>2)+0]=37;dram[('h1300>>2)+1]=74;
    dram[('h1300>>2)+2]=32'hffffffce;dram[('h1300>>2)+3]=32'hffffffef;
    dram[('h1300>>2)+4]=32'hffffffe8;dram[('h1300>>2)+5]=24;
    dram[('h1300>>2)+6]=32'hffffffa7;dram[('h1300>>2)+7]=32'hffffffc4;
    push_dma(3,'h1300,'h240,32,10,9);
    // scalar3 encodes lane stride 8 bytes and four valid lanes.
    push_vmu(14,'h240,0,'h2c0,2,1,0,4,(8<<8)|4,11,10);
    push_dma(4,'h2200,'h2c0,8,12,11);
    cycles=0;
    while(completion_count!=3 && cycles<500) begin tick();cycles=cycles+1;end
    if(completion_count!=3) $fatal(1,"queued Q8 pack timeout");
    if(dram[('h2200>>2)+0]!==32'ha7e8ce25 ||
       dram[('h2200>>2)+1]!==32'hc418ef4a)
      $fatal(1,"queued Q8 pack result mismatch");
    check_and_pop_completion(10,3);
    check_and_pop_completion(11,7);
    check_and_pop_completion(12,4);

    // One exact Q16 ADAM step through the queued UB path.
    dram[('h1400>>2)+0]=32'h00010000;
    dram[('h1400>>2)+1]=32'hffff8000;
    dram[('h1400>>2)+2]=32'h00004000;
    dram[('h1500>>2)+0]=32'h00002000;
    dram[('h1500>>2)+1]=32'hffffc000;
    dram[('h1500>>2)+2]=32'h00008000;
    dram[('h1600>>2)+0]=0;dram[('h1600>>2)+1]=0;dram[('h1600>>2)+2]=0;
    dram[('h1700>>2)+0]=0;dram[('h1700>>2)+1]=0;dram[('h1700>>2)+2]=0;
    push_dma(3,'h1400,'h00,12,13,12);
    push_dma(3,'h1500,'h40,12,14,13);
    push_dma(3,'h1600,'h80,12,15,14);
    push_dma(3,'h1700,'hc0,12,16,15);
    push_adam(17,16);
    push_dma(4,'h2300,'h00,12,18,17);
    push_dma(4,'h2400,'h80,12,19,18);
    push_dma(4,'h2500,'hc0,12,20,19);
    cycles=0;
    while(completion_count!=8 && cycles<1000) begin tick();cycles=cycles+1;end
    if(completion_count!=8) $fatal(1,"queued ADAM timeout");
    if(dram[('h2300>>2)+0]!==32'h0000fd6c ||
       dram[('h2300>>2)+1]!==32'hffff828e ||
       dram[('h2300>>2)+2]!==32'h00003d72 ||
       dram[('h2400>>2)+0]!==32'h00000333 ||
       dram[('h2400>>2)+1]!==32'hfffff99a ||
       dram[('h2400>>2)+2]!==32'h00000ccd ||
       dram[('h2500>>2)+0]!==32'h0000000a ||
       dram[('h2500>>2)+1]!==32'h00000029 ||
       dram[('h2500>>2)+2]!==32'h000000a4)
      $fatal(1,"queued ADAM result mismatch");
    check_and_pop_completion(13,3);
    check_and_pop_completion(14,3);
    check_and_pop_completion(15,3);
    check_and_pop_completion(16,3);
    check_and_pop_completion(17,6);
    check_and_pop_completion(18,4);
    check_and_pop_completion(19,4);
    check_and_pop_completion(20,4);

    // Strided DRAM copy reuses one UB row window for load/store sequencing.
    dram[('h1800>>2)+0]=32'ha0000000;
    dram[('h1800>>2)+1]=32'ha0000001;
    dram[('h1800>>2)+2]=32'ha0000002;
    dram[('h1800>>2)+3]=32'ha0000003;
    dram[('h1810>>2)+0]=32'hb0000000;
    dram[('h1810>>2)+1]=32'hb0000001;
    dram[('h1810>>2)+2]=32'hb0000002;
    dram[('h1810>>2)+3]=32'hb0000003;
    dram[('h1820>>2)+0]=32'hc0000000;
    dram[('h1820>>2)+1]=32'hc0000001;
    dram[('h1820>>2)+2]=32'hc0000002;
    dram[('h1820>>2)+3]=32'hc0000003;
    push_dcopy('h1804,'h2600,'h300,8,3,16,8,21,20);
    cycles=0;
    while(!completion_valid && cycles<500) begin tick();cycles=cycles+1;end
    if(!completion_valid) $fatal(1,"queued DCOPY timeout");
    if(dram[('h2600>>2)+0]!==32'ha0000001 ||
       dram[('h2600>>2)+1]!==32'ha0000002 ||
       dram[('h2600>>2)+2]!==32'hb0000001 ||
       dram[('h2600>>2)+3]!==32'hb0000002 ||
       dram[('h2600>>2)+4]!==32'hc0000001 ||
       dram[('h2600>>2)+5]!==32'hc0000002)
      $fatal(1,"queued strided DCOPY result mismatch");
    check_and_pop_completion(21,8);

    // Bulk command submission fetches two dependent descriptors into the
    // same finite queue used by direct host commands.
    dram[('h1900>>2)+0]=32'h11223344;
    dram[('h1900>>2)+1]=32'h55667788;
    command_memory[0]=32'h00151603;command_memory[1]=8;
    command_memory[2]=32'h00001900;command_memory[3]=0;
    command_memory[4]=32'h00000340;command_memory[5]=0;
    command_memory[16]=32'h00161704;command_memory[17]=8;
    command_memory[18]=32'h00002700;command_memory[19]=0;
    command_memory[20]=32'h00000340;command_memory[21]=0;
    command_dma_base='h3000;command_dma_count=2;
    @(negedge clk);command_dma_start=1;tick();
    @(negedge clk);command_dma_start=0;
    cycles=0;
    while(completion_count!=2 && cycles<1000) begin tick();cycles=cycles+1;end
    if(completion_count!=2 || !command_dma_done || command_dma_error ||
       command_dma_error_code!=0 || command_dma_fetched_count!=2)
      $fatal(1,"queued command DMA status mismatch");
    if(dram[('h2700>>2)+0]!==32'h11223344 ||
       dram[('h2700>>2)+1]!==32'h55667788)
      $fatal(1,"queued command DMA result mismatch");
    check_and_pop_completion(22,3);
    check_and_pop_completion(23,4);

    // Global fences block requests before the external buses, preserve the
    // first fault record, and still let each queued command retire with error.
    @(negedge clk);perf_clear=1;perf_clear_error=1;tick();
    @(negedge clk);perf_clear=0;perf_clear_error=0;perf_enable=1;
    dma_fence_base=0;dma_fence_limit='h1000;dma_fence_enable=1;
    push_dma(3,'h3000,'h380,4,24,23);
    cycles=0;
    while(!completion_valid && cycles<100) begin tick();cycles=cycles+1;end
    if(!completion_valid || completion_tag!=24 || completion_opcode!=3 ||
       completion_status!=1 || completion_error!=8'h42)
      $fatal(1,"fenced read completion mismatch");
    if(!dma_fence_fault_valid || dma_fence_fault_overflow ||
       dma_fence_fault_write || dma_fence_fault_master!=7 ||
       dma_fence_fault_addr!='h3000 || dma_fence_fault_len!=0 ||
       dma_fence_fault_size!=2)
      $fatal(1,"fenced read sticky record mismatch");
    completion_pop=1;tick();completion_pop=0;

    push_dma(4,'h3100,'h380,4,25,24);
    cycles=0;
    while(!completion_valid && cycles<100) begin tick();cycles=cycles+1;end
    if(!completion_valid || completion_tag!=25 || completion_opcode!=4 ||
       completion_status!=1 || completion_error!=8'h43)
      $fatal(1,"fenced write completion mismatch");
    if(!dma_fence_fault_valid || !dma_fence_fault_overflow ||
       dma_fence_fault_write || dma_fence_fault_master!=7 ||
       dma_fence_fault_addr!='h3000)
      $fatal(1,"fence overflow replaced first record");
    completion_pop=1;tick();completion_pop=0;

    @(negedge clk);dma_fence_fault_clear_valid=1;tick();
    @(negedge clk);dma_fence_fault_clear_valid=0;
    if(dma_fence_fault_valid || dma_fence_fault_overflow)
      $fatal(1,"fence fault clear mismatch");

    // The descriptor-fetch master uses the same global fence and master ID 9.
    command_dma_clear=1;tick();@(negedge clk);command_dma_clear=0;
    command_dma_base='h3000;command_dma_count=1;command_dma_start=1;tick();
    @(negedge clk);command_dma_start=0;
    cycles=0;
    while(!command_dma_error && cycles<100) begin tick();cycles=cycles+1;end
    tick();
    if(!command_dma_error || command_dma_error_code!=2 ||
       !dma_fence_fault_valid || dma_fence_fault_write ||
       dma_fence_fault_master!=9 || dma_fence_fault_addr!='h3000 ||
       dma_fence_fault_len!=15 || dma_fence_fault_size!=2)
      $fatal(1,"fenced descriptor DMA status mismatch");
    if(perf_command_count!=2 || perf_dma_read_count!=0 ||
       perf_dma_write_count!=0 || perf_error_count!=3 ||
       !perf_error_valid || perf_error_code!=8'h52 || perf_cycles==0 ||
       perf_busy_cycles==0) begin
      $display("perf cycles=%0d busy=%0d commands=%0d reads=%0d writes=%0d errors=%0d valid=%0d code=%h",
        perf_cycles,perf_busy_cycles,perf_command_count,perf_dma_read_count,
        perf_dma_write_count,perf_error_count,perf_error_valid,perf_error_code);
      $fatal(1,"fenced workload performance counters mismatch");
    end

    // UB-domain and per-master windows intersect independently for reads and
    // writes. The descriptor-fetch master remains global-only.
    @(negedge clk);dma_fence_fault_clear_valid=1;tick();
    @(negedge clk);dma_fence_fault_clear_valid=0;
    dma_fence_enable=0;
    dma_fence_ub_enable=1;dma_fence_ub_base='h1000;dma_fence_ub_limit='h3000;
    dma_fence_ub_read_enable=1;
    dma_fence_ub_read_base='h1000;dma_fence_ub_read_limit='h1800;
    dma_fence_ub_write_enable=1;
    dma_fence_ub_write_base='h2000;dma_fence_ub_write_limit='h2800;
    push_dma(3,'h1900,'h380,4,26,25);
    cycles=0;
    while(!completion_valid && cycles<100) begin tick();cycles=cycles+1;end
    if(!completion_valid || completion_tag!=26 || completion_error!=8'h42 ||
       !dma_fence_fault_valid || dma_fence_fault_write ||
       dma_fence_fault_master!=7 || dma_fence_fault_addr!='h1900)
      $fatal(1,"UB read hierarchy fence mismatch");
    completion_pop=1;tick();completion_pop=0;
    @(negedge clk);dma_fence_fault_clear_valid=1;tick();
    @(negedge clk);dma_fence_fault_clear_valid=0;
    push_dma(4,'h2900,'h380,4,27,26);
    cycles=0;
    while(!completion_valid && cycles<100) begin tick();cycles=cycles+1;end
    if(!completion_valid || completion_tag!=27 || completion_error!=8'h43 ||
       !dma_fence_fault_valid || !dma_fence_fault_write ||
       dma_fence_fault_master!=8 || dma_fence_fault_addr!='h2900)
      $fatal(1,"UB write hierarchy fence mismatch");
    completion_pop=1;tick();completion_pop=0;

    $display("Queued Q16 slice: PASS");$finish;
  end
endmodule
""",
    )
    assert "Queued Q16 slice: PASS" in output
