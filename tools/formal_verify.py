from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
TARGETS_PATH = ROOT / "contracts" / "formal_targets.json"


def _property_name(result: dict[str, object]) -> str:
    origin = result.get("source_origin")
    if not isinstance(origin, dict):
        return ""
    construct = origin.get("construct")
    return construct if isinstance(construct, str) else ""


def validate_report(report: dict[str, object], target: dict[str, object]) -> str:
    if report.get("outcome") != "passed":
        raise ValueError(f"verification outcome is {report.get('outcome')!r}")
    results = report.get("results")
    if not isinstance(results, list):
        raise ValueError("verification report has no results list")

    named = {
        _property_name(result): result
        for result in results
        if isinstance(result, dict) and _property_name(result)
    }
    missing = sorted(set(target["properties"]) - set(named))
    if missing:
        raise ValueError(f"missing named properties: {', '.join(missing)}")

    bad: list[str] = []
    for name in target["properties"]:
        result = named[name]
        expected = "witnessed" if name.startswith("cover ") else target["require"]
        if result.get("status") != expected:
            bad.append(f"{name}={result.get('status')} (expected {expected})")
    if bad:
        raise ValueError("unexpected property results: " + ", ".join(bad))

    counts = Counter(
        str(result.get("status")) for result in results if isinstance(result, dict)
    )
    return ", ".join(f"{status}={counts[status]}" for status in sorted(counts))


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the ZTPU ZLang formal suite")
    parser.add_argument("--zlang", default=str(ROOT / ".venv" / "bin" / "zlang"))
    parser.add_argument("--output", type=Path, default=ROOT / "build" / "formal")
    parser.add_argument("--timeout", type=int)
    parser.add_argument("--target", action="append", default=[])
    args = parser.parse_args()

    manifest = json.loads(TARGETS_PATH.read_text(encoding="utf-8"))
    selected = set(args.target)
    targets = [
        target
        for target in manifest["targets"]
        if not selected or target["name"] in selected
    ]
    unknown = selected - {target["name"] for target in targets}
    if unknown:
        raise SystemExit(f"unknown formal target(s): {', '.join(sorted(unknown))}")

    timeout = args.timeout or manifest["default_timeout_seconds"]
    args.output.mkdir(parents=True, exist_ok=True)
    for target in targets:
        name = target["name"]
        report_path = args.output / f"{name}.json"
        command = [
            args.zlang,
            target["source"],
            "--top",
            target["top"],
            "--profile",
            manifest["profile"],
            "--verify",
            "--verify-require",
            target["require"],
            "--formal-depth",
            str(target["depth"]),
            "--formal-timeout",
            str(timeout),
            "--verification-work-dir",
            str(args.output / "work" / name),
            "--verification-report",
            str(report_path),
            "--verification-format",
            "json",
            "--verification-bundle",
            str(args.output / "bundles" / name),
            "--contracts-sva",
            str(args.output / "sva" / f"{name}.sv"),
        ]
        print(f"formal: {name}: {target['top']} depth={target['depth']}", flush=True)
        run = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
        if run.returncode:
            sys.stderr.write(run.stdout[-4000:])
            sys.stderr.write(run.stderr[-4000:])
            raise SystemExit(f"formal: {name}: ZLang exited {run.returncode}")
        try:
            report = json.loads(report_path.read_text(encoding="utf-8"))
            summary = validate_report(report, target)
        except (OSError, ValueError, json.JSONDecodeError) as error:
            raise SystemExit(f"formal: {name}: invalid result: {error}") from error
        print(f"formal: {name}: PASS ({summary})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
