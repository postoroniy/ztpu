from tools.simulator_diff import _existing_hashes, _mismatch_details


def test_mismatch_details_extracts_first_difference_and_context() -> None:
    events = [{"edges": ["clk"], "set": {"value": index}} for index in range(7)]
    details = _mismatch_details(
        "simulation mismatch for plan abc at event 4, output 'done': "
        "native=1, verilator=0",
        events,
    )
    assert details == {
        "event": 4,
        "cycle": 4,
        "signal": "done",
        "native": 1,
        "verilator": 0,
        "stimulus_context_start": 2,
        "stimulus_context": events[2:7],
    }


def test_mismatch_helpers_ignore_non_mismatch_and_missing_files(tmp_path) -> None:
    present = tmp_path / "present.txt"
    present.write_text("ztpu\n", encoding="ascii")
    assert _mismatch_details("compiler failed", []) is None
    assert set(_existing_hashes({"present": present, "missing": tmp_path / "x"})) == {
        "present"
    }
