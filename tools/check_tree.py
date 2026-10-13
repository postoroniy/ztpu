from __future__ import annotations

from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
ALLOWED_TOP_LEVEL = {
    ".gitignore",
    "CHANGELOG.md",
    "COMMERCIAL-LICENSE.md",
    "CONTRIBUTING.md",
    "LICENSE",
    "Makefile",
    "NOTICE",
    "README.md",
    "RELEASING.md",
    "contracts",
    "docs",
    "src",
    "tests",
    "tools",
    "zlang.lock",
    "zlang.toml",
}
FORBIDDEN_FILENAMES: set[str] = set()
FORBIDDEN_PARTS = {"ip", "sw", "config", "librelane", "openlane", "yosys"}
FORBIDDEN_SUFFIXES = {
    ".v", ".sv", ".vcd", ".fst", ".gds", ".lef", ".lib",
    ".bin", ".h5", ".npy", ".npz", ".onnx", ".pt", ".pth", ".tflite",
}


def tracked_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    return [Path(line) for line in result.stdout.splitlines() if line]


def main() -> int:
    errors: list[str] = []
    for path in tracked_files():
        if path.name in FORBIDDEN_FILENAMES:
            errors.append(f"excluded file is tracked: {path}")
        if path.parts[0] not in ALLOWED_TOP_LEVEL:
            errors.append(f"unapproved top-level path: {path}")
        if any(part in FORBIDDEN_PARTS for part in path.parts):
            errors.append(f"forbidden inherited path: {path}")
        if path.suffix in FORBIDDEN_SUFFIXES:
            errors.append(f"generated/physical artifact is tracked: {path}")
    if errors:
        raise SystemExit("\n".join(errors))
    print(f"tree policy: PASS ({len(tracked_files())} tracked files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
