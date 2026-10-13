from __future__ import annotations

from pathlib import Path

from tools.rtl_test_utils import compile_zlang_top, run_iverilog


def test_unified_buffer_dual_read_masked_write_alias_and_reset(tmp_path: Path) -> None:
    source = compile_zlang_top(tmp_path, "ZtpuUnifiedBuffer256x32", "ub.zhl")
    output = run_iverilog(
        tmp_path,
        [source],
        r"""`timescale 1ns/1ps
module tb;
  logic clk=0,rst=0;
  logic read0_valid=1,read1_valid=1,write_valid=0;
  logic read0_ready,read1_ready,write_ready;
  logic [63:0] read0_addr=0,read1_addr=0,write_addr=0;
  logic [31:0] read0_data,read1_data,write_data=0;
  logic [3:0] write_mask=0;
  always #5 clk=~clk;
  ZtpuUnifiedBuffer256x32 dut(.*);

  task automatic write_word(
    input logic [63:0] address,
    input logic [31:0] data,
    input logic [3:0] mask
  );
    begin
      @(negedge clk);write_valid=1;write_addr=address;write_data=data;write_mask=mask;
      @(posedge clk);#1;write_valid=0;
    end
  endtask

  initial begin
    #1;rst=1;repeat(2)@(posedge clk);@(negedge clk);rst=0;#1;
    if (!read0_ready || !read1_ready || !write_ready) $fatal(1,"ready mismatch");

    write_word(64'h000,32'h11223344,4'hf);
    write_word(64'h004,32'h55667788,4'hf);
    write_word(64'h008,32'h99aabbcc,4'hf);
    write_word(64'h00c,32'hddeeff00,4'hf);

    read0_addr=64'h000;read1_addr=64'h00c;#1;
    if (read0_data!==32'h11223344 || read1_data!==32'hddeeff00)
      $fatal(1,"independent bank read mismatch %h %h",read0_data,read1_data);

    write_word(64'h000,32'haaaabbbb,4'h3);
    read0_addr=64'h000;read1_addr=64'h004;#1;
    if (read0_data!==32'h1122bbbb || read1_data!==32'h55667788)
      $fatal(1,"masked write mismatch %h %h",read0_data,read1_data);

    // Only the low eight word-index bits are decoded.
    read0_addr=64'h400;#1;
    if (read0_data!==32'h1122bbbb) $fatal(1,"high-address alias mismatch %h",read0_data);

    @(negedge clk);rst=1;@(posedge clk);#1;
    if (read0_data!==32'h1122bbbb) $fatal(1,"reset did not preserve contents");
    @(negedge clk);rst=0;

    // Reset suppresses an otherwise active write.
    @(negedge clk);rst=1;write_valid=1;write_addr=64'h004;
    write_data=32'hdeadbeef;write_mask=4'hf;@(posedge clk);#1;
    @(negedge clk);rst=0;write_valid=0;read0_addr=64'h004;#1;
    if (read0_data!==32'h55667788) $fatal(1,"reset write suppression mismatch %h",read0_data);

    $display("unified buffer: PASS");$finish;
  end
endmodule
""",
    )
    assert "unified buffer: PASS" in output


def test_unified_buffer_1024_word_profile_decodes_ten_word_bits(tmp_path: Path) -> None:
    source = compile_zlang_top(tmp_path, "ZtpuUnifiedBuffer1024x32", "ub.zhl")
    output = run_iverilog(
        tmp_path,
        [source],
        r"""`timescale 1ns/1ps
module tb;
  logic clk=0,rst=0;
  logic read0_valid=1,read1_valid=1,write_valid=0;
  logic read0_ready,read1_ready,write_ready;
  logic [63:0] read0_addr=0,read1_addr=0,write_addr=0;
  logic [31:0] read0_data,read1_data,write_data=0;
  logic [3:0] write_mask=4'hf;
  always #5 clk=~clk;
  ZtpuUnifiedBuffer1024x32 dut(.*);

  task automatic write_word(input logic [63:0] address,input logic [31:0] data);
    begin
      @(negedge clk);write_valid=1;write_addr=address;write_data=data;
      @(posedge clk);#1;write_valid=0;
    end
  endtask

  initial begin
    #1;rst=1;repeat(2)@(posedge clk);@(negedge clk);rst=0;#1;
    write_word(64'h000,32'h11223344);
    write_word(64'h400,32'h55667788);
    write_word(64'hc00,32'h99aabbcc);
    read0_addr=64'h000;read1_addr=64'h400;#1;
    if(read0_data!==32'h11223344 || read1_data!==32'h55667788)
      $fatal(1,"1024-word address decode mismatch %h %h",read0_data,read1_data);
    read0_addr=64'hc00;read1_addr=64'h1000;#1;
    if(read0_data!==32'h99aabbcc || read1_data!==32'h11223344)
      $fatal(1,"1024-word alias mismatch %h %h",read0_data,read1_data);
    $display("unified buffer 1024: PASS");$finish;
  end
endmodule
""",
    )
    assert "unified buffer 1024: PASS" in output
