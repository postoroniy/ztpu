import json
from pathlib import Path

from tools.check_tree import (
    ALLOWED_TOP_LEVEL,
    FORBIDDEN_FILENAMES,
    FORBIDDEN_PARTS,
    FORBIDDEN_SUFFIXES,
)


ROOT = Path(__file__).resolve().parents[1]


def test_tree_policy_definitions_are_fail_closed() -> None:
    assert {"ip", "sw", "librelane", "yosys"} <= FORBIDDEN_PARTS
    assert {".sv", ".gds", ".lef", ".npz", ".onnx", ".pt"} <= FORBIDDEN_SUFFIXES
    assert {"src", "contracts", "docs", "tests", "tools"} <= ALLOWED_TOP_LEVEL
    assert not (FORBIDDEN_FILENAMES & ALLOWED_TOP_LEVEL)


def test_simulator_diff_manifest_has_ahb_and_queued_top_scenarios() -> None:
    manifest = json.loads(
        (ROOT / "contracts" / "simulator_scenarios.json").read_text(
            encoding="ascii"
        )
    )
    scenarios = {item["name"]: item for item in manifest["scenarios"]}
    assert scenarios["native_ahb_cfgbus"]["top"] == "ZtpuQueuedCfgAhb64x32"
    assert scenarios["queued_top_direct_ub_dma"]["top"] == "ZtpuQueuedQ16AhbTop"
    assert all(item["timeout_seconds"] > 0 for item in scenarios.values())
