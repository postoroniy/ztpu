from __future__ import annotations

import argparse
import ast
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
from time import perf_counter
from typing import Any

from zlang import sim
from zlang.simulation_compare import SimulationComparisonError, compare_program


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "contracts" / "simulator_scenarios.json"
DEFAULT_OUTPUT = ROOT / "build" / "simulator-diff"
MISMATCH_RE = re.compile(
    r"at event (?P<event>\d+), output '(?P<signal>[^']+)': "
    r"native=(?P<native>[^,]+), verilator=(?P<verilator>.+)$"
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _mismatch_details(message: str, events: list[dict]) -> dict[str, Any] | None:
    match = MISMATCH_RE.search(message)
    if match is None:
        return None
    event = int(match.group("event"))
    start = max(0, event - 2)
    stop = min(len(events), event + 3)
    return {
        "event": event,
        "cycle": event,
        "signal": match.group("signal"),
        "native": ast.literal_eval(match.group("native")),
        "verilator": ast.literal_eval(match.group("verilator")),
        "stimulus_context_start": start,
        "stimulus_context": events[start:stop],
    }


def _existing_hashes(paths: dict[str, Path]) -> dict[str, str]:
    return {name: _sha256(path) for name, path in paths.items() if path.exists()}


def _edge(values: dict[str, int] | None = None, *, reset: bool | None = None) -> dict:
    event: dict[str, Any] = {"edges": ["clk"]}
    if values is not None:
        event["set"] = values
    if reset is not None:
        event["reset"] = {"rst": reset}
    return event


def _ahb_idle() -> dict[str, int]:
    return {
        "ahb__HSEL": 0,
        "ahb__HADDR": 0,
        "ahb__HWRITE": 0,
        "ahb__HTRANS": 0,
        "ahb__HSIZE": 2,
        "ahb__HBURST": 0,
        "ahb__HPROT": 0,
        "ahb__HMASTLOCK": 0,
        "ahb__HWDATA": 0,
        "ahb__HREADY": 1,
    }


def _ahb_write(address: int, data: int, base: dict[str, int] | None = None) -> list[dict]:
    idle = dict(base or _ahb_idle())
    address_phase = dict(idle)
    address_phase.update(
        ahb__HSEL=1,
        ahb__HADDR=address,
        ahb__HWRITE=1,
        ahb__HTRANS=2,
        ahb__HWDATA=0,
    )
    data_phase = dict(idle)
    data_phase["ahb__HWDATA"] = data
    return [_edge(address_phase), _edge(data_phase), _edge(idle)]


def _ahb_read(address: int, base: dict[str, int] | None = None) -> list[dict]:
    idle = dict(base or _ahb_idle())
    address_phase = dict(idle)
    address_phase.update(ahb__HSEL=1, ahb__HADDR=address, ahb__HTRANS=2)
    return [_edge(address_phase), _edge(idle), _edge(idle)]


def _cfgbus_events() -> list[dict]:
    idle = _ahb_idle()
    events = [_edge(reset=True), _edge(reset=True), _edge(idle, reset=False)]
    events.extend(_ahb_read(0x0000))
    events.extend(_ahb_write(0x0060, 0x00000001))
    events.extend(_ahb_read(0x0060))

    misaligned = dict(idle)
    misaligned.update(ahb__HSEL=1, ahb__HADDR=1, ahb__HTRANS=2)
    events.extend((_edge(misaligned), _edge(idle), _edge(idle)))

    unknown = dict(idle)
    unknown.update(ahb__HSEL=1, ahb__HADDR=0x5000, ahb__HTRANS=2)
    events.extend((_edge(unknown), _edge(idle), _edge(idle), _edge(idle)))

    pending = dict(idle)
    pending.update(ahb__HSEL=1, ahb__HADDR=0, ahb__HTRANS=2)
    events.extend((_edge(pending), _edge(idle, reset=True), _edge(idle, reset=False)))
    return events


def _top_idle() -> dict[str, int]:
    values = _ahb_idle()
    values.update(
        command_axi_ar_ready=0,
        command_axi_r_valid=0,
        command_axi_r_data=0,
        command_axi_r_last=0,
        command_axi_r_resp=0,
        axi_read_ar_ready=1,
        axi_read_r_valid=0,
        axi_read_r_data=0,
        axi_read_r_last=0,
        axi_read_r_resp=0,
        axi_write_aw_ready=1,
        axi_write_w_ready=1,
        axi_write_b_valid=0,
        axi_write_b_resp=0,
    )
    return values


def _top_events() -> list[dict]:
    idle = _top_idle()
    events = [_edge(reset=True), _edge(reset=True), _edge(idle, reset=False)]

    for address, data in (
        (0x0194, 0x1000),
        (0x0198, 0),
        (0x019C, 0),
        (0x01A0, 0),
        (0x01A4, 4),
        (0x0190, 3),
    ):
        events.extend(_ahb_write(address, data, idle))

    events.extend(_edge(idle) for _ in range(4))
    read_data = dict(idle)
    read_data.update(axi_read_r_valid=1, axi_read_r_data=0x12345678, axi_read_r_last=1)
    events.extend(_edge(read_data) for _ in range(3))
    events.extend(_edge(idle) for _ in range(6))

    events.extend(_ahb_write(0x0194, 0x1100, idle))
    events.extend(_ahb_write(0x0190, 7, idle))
    write_response = dict(idle)
    write_response["axi_write_b_valid"] = 1
    events.extend(_edge(write_response) for _ in range(8))
    events.extend(_edge(idle) for _ in range(6))
    return events


BUILDERS = {
    "native_ahb_cfgbus": _cfgbus_events,
    "queued_top_direct_ub_dma": _top_events,
}


def _validate_activity(name: str, trace: tuple[dict[str, int], ...]) -> None:
    if not any(sample.get("ahb_HREADYOUT") == 0 for sample in trace):
        raise RuntimeError(f"{name}: AHB trace never stalled")
    if name == "native_ahb_cfgbus":
        if not any(sample.get("ahb_HRDATA") == 0x5A545055 for sample in trace):
            raise RuntimeError(f"{name}: device ID was not returned")
        if not any(sample.get("ahb_HRESP") == 1 for sample in trace):
            raise RuntimeError(f"{name}: error response was not exercised")
    else:
        required = ("axi_read_ar_valid", "axi_write_aw_valid", "axi_write_w_valid")
        missing = [signal for signal in required if not any(row.get(signal) for row in trace)]
        if missing:
            raise RuntimeError(f"{name}: inactive datapath outputs: {', '.join(missing)}")


def _try_write_vcd(directory: Path) -> str | None:
    design = directory / "design.sv"
    testbench = directory / "compare_tb.sv"
    if not design.exists() or not testbench.exists() or shutil.which("iverilog") is None:
        return None
    vcd_tb = directory / "compare_vcd_tb.sv"
    text = testbench.read_text(encoding="utf-8")
    insertion = (
        'initial begin $dumpfile("mismatch.vcd"); '
        "$dumpvars(0, zlang_compare_tb); end\nendmodule"
    )
    vcd_tb.write_text(text.rsplit("endmodule", 1)[0] + insertion + "\n", encoding="utf-8")
    executable = directory / "compare_vcd"
    try:
        subprocess.run(
            ["iverilog", "-g2012", "-s", "zlang_compare_tb", "-o", str(executable), str(design), str(vcd_tb)],
            cwd=directory,
            check=True,
            capture_output=True,
            text=True,
            timeout=120,
        )
        subprocess.run([str(executable)], cwd=directory, timeout=120, check=False)
    except (OSError, subprocess.SubprocessError):
        return None
    vcd = directory / "mismatch.vcd"
    return str(vcd.relative_to(ROOT)) if vcd.exists() else None


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare ZTPU native JIT with generated RTL")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--scenario", action="append", default=[])
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    if manifest.get("schema") != "ztpu-simulator-scenarios-v1":
        raise SystemExit("unsupported simulator scenario manifest")
    selected = set(args.scenario)
    summaries: list[dict[str, Any]] = []
    args.output.mkdir(parents=True, exist_ok=True)

    for item in manifest.get("scenarios", []):
        name = str(item["name"])
        if selected and name not in selected:
            continue
        builder_name = str(item["builder"])
        if builder_name not in BUILDERS:
            raise SystemExit(f"{name}: unknown event builder {builder_name}")
        source = ROOT / str(item["source"])
        directory = args.output / name
        shutil.rmtree(directory, ignore_errors=True)
        directory.mkdir(parents=True)
        events = BUILDERS[builder_name]()
        (directory / "stimulus.json").write_text(
            json.dumps(events, sort_keys=True, indent=2) + "\n", encoding="utf-8"
        )
        started = perf_counter()
        try:
            program = sim.compile(source, top=str(item["top"]), project=ROOT / "zlang.toml")
            compiled_seconds = perf_counter() - started
            compared = compare_program(
                program,
                events,
                simulator="verilator",
                artifact_directory=directory / "comparison",
                timeout=float(item["timeout_seconds"]),
            )
            _validate_activity(name, compared.native_trace)
        except Exception as error:
            message = str(error)
            first_mismatch = _mismatch_details(message, events)
            if first_mismatch is not None:
                reproduction = events[: int(first_mismatch["event"]) + 1]
                (directory / "reproduction.json").write_text(
                    json.dumps(reproduction, sort_keys=True, indent=2) + "\n",
                    encoding="utf-8",
                )
            comparison_dir = directory / "comparison"
            failure = {
                "scenario": name,
                "error_type": type(error).__name__,
                "classification": (
                    "semantic_mismatch"
                    if isinstance(error, SimulationComparisonError)
                    and first_mismatch is not None
                    else "tool_or_runtime_failure"
                ),
                "message": message,
                "first_mismatch": first_mismatch,
                "hashes": {
                    "source": _sha256(source),
                    "scenario_manifest": _sha256(args.manifest),
                    "toolchain_contract": _sha256(ROOT / "contracts" / "toolchain.json"),
                    **_existing_hashes(
                        {
                            "generated_systemverilog": comparison_dir / "design.sv",
                            "comparison_testbench": comparison_dir / "compare_tb.sv",
                        }
                    ),
                },
                "zlang_version": version("zlang-hdl"),
                "native_runtime_version": version("zlang-native-sim"),
            }
            failure["vcd"] = _try_write_vcd(comparison_dir) if comparison_dir.exists() else None
            (directory / "failure.json").write_text(
                json.dumps(failure, sort_keys=True, indent=2) + "\n", encoding="utf-8"
            )
            print(f"[simulator-diff] {name}: FAIL: {error}", file=sys.stderr)
            return 1
        elapsed = perf_counter() - started
        summary = {
            "scenario": name,
            "top": item["top"],
            "event_count": len(events),
            "plan_identity": compared.plan_identity,
            "artifact_hash": compared.artifact_hash,
            "native_compile_seconds": round(compiled_seconds, 6),
            "total_compare_seconds": round(elapsed, 6),
            "status": "pass",
        }
        summaries.append(summary)
        print(f"[simulator-diff] {name}: PASS ({len(events)} events, {elapsed:.3f}s)")

    if selected and selected != {item["scenario"] for item in summaries}:
        missing = sorted(selected - {item["scenario"] for item in summaries})
        raise SystemExit(f"unknown scenarios: {', '.join(missing)}")
    report = {
        "schema": "ztpu-simulator-diff-v1",
        "zlang_version": version("zlang-hdl"),
        "native_runtime_version": version("zlang-native-sim"),
        "manifest_sha256": _sha256(args.manifest),
        "scenarios": summaries,
    }
    (args.output / "summary.json").write_text(
        json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
