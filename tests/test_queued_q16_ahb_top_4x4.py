from __future__ import annotations

from pathlib import Path

from tools.ahb_descriptor_replay import run_ahb_descriptor_replay, write_hex_words


def _generic_descriptor(
    *, opcode: int, tag: int, dependency: int, length: int, address: int, auxiliary: int
) -> list[int]:
    words = [0] * 16
    words[0] = int(opcode) | (int(tag) << 8) | (int(dependency) << 16)
    words[1] = int(length)
    words[2] = int(address) & 0xFFFFFFFF
    words[3] = int(address) >> 32
    words[4] = int(auxiliary) & 0xFFFFFFFF
    words[5] = int(auxiliary) >> 32
    return words


def _q16_compute_descriptor() -> list[int]:
    words = [0] * 16
    words[0] = 5 | (3 << 8) | (2 << 16)
    words[2] = 0x000
    words[4] = 0x100
    words[6] = 0x200
    words[8] = 0x300
    words[10] = 16
    words[11] = 16
    words[12] = 4
    words[13] = 1 | (1 << 2) | (3 << 14)
    return words


def test_4x4_q16_compute_through_ahb_descriptor_dma(tmp_path: Path) -> None:
    descriptors = [
        *_generic_descriptor(
            opcode=3, tag=1, dependency=0, length=64, address=0x1000, auxiliary=0
        ),
        *_generic_descriptor(
            opcode=3,
            tag=2,
            dependency=1,
            length=64,
            address=0x1100,
            auxiliary=0x100,
        ),
        *_q16_compute_descriptor(),
        *_generic_descriptor(
            opcode=4,
            tag=4,
            dependency=3,
            length=64,
            address=0x1200,
            auxiliary=0x200,
        ),
    ]
    dram = [0] * 2048
    a = [
        0x00010000, 0, 0, 0,
        0, 0x00008000, 0, 0,
        0, 0, 0xFFFF0000, 0,
        0, 0, 0, 0x00004000,
    ]
    b = [
        0x00004000, 0xFFFF8000, 0x0000C000, 0x00010000,
        0x00010000, 0x00008000, 0xFFFFC000, 0x00002000,
        0xFFFF8000, 0x00004000, 0x00010000, 0xFFFF0000,
        0x00008000, 0xFFFF8000, 0x00004000, 0xFFFFC000,
    ]
    expected = [
        0x00004000, 0xFFFF8000, 0x0000C000, 0x00010000,
        0x00008000, 0x00004000, 0xFFFFE000, 0x00001000,
        0x00008000, 0xFFFFC000, 0xFFFF0000, 0x00010000,
        0x00002000, 0xFFFFE000, 0x00001000, 0xFFFFF000,
    ]
    dram[0x1000 // 4 : 0x1000 // 4 + 16] = a
    dram[0x1100 // 4 : 0x1100 // 4 + 16] = b
    descriptor_hex = write_hex_words(tmp_path / "descriptors.hex", descriptors)
    dram_hex = write_hex_words(tmp_path / "dram.hex", dram)
    selected = [
        {"name": "linear4x4", "word": index, "address": 0x1200 + index * 4, "value": value}
        for index, value in enumerate(expected)
    ]
    output = run_ahb_descriptor_replay(
        tmp_path,
        top="ZtpuQueuedQ16AhbTop4x4",
        source_name="queued_q16_ahb_top.zhl",
        descriptor_hex=descriptor_hex,
        dram_hex=dram_hex,
        command_count=4,
        descriptor_words=len(descriptors),
        dram_words=len(dram),
        descriptor_base=0x2000,
        fence_limit=0x3000,
        final_tag=4,
        selected_expected=selected,
        register_expected=[
            {"name": "zs_steps", "address": 0x0318, "value": 0},
            {"name": "zs_total_macs", "address": 0x031C, "value": 0},
            {"name": "zs_active_macs", "address": 0x0320, "value": 0},
            {"name": "zs_skipped_macs", "address": 0x0324, "value": 0},
        ],
        marker="Queued 4x4 Q16 AHB descriptor replay",
        max_rtl_cycles=10000,
    )
    assert "Queued 4x4 Q16 AHB descriptor replay: PASS" in output
