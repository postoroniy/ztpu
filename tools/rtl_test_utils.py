from __future__ import annotations

from pathlib import Path
import os
import re
import shutil
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[1]


def require_tool(name: str, env_name: str | None = None) -> str:
    candidate = os.environ.get(env_name) if env_name else None
    resolved = candidate or shutil.which(name)
    if not resolved:
        pytest.skip(f"{name} is not installed")
    return resolved


def compile_zlang_top(tmp_path: Path, top: str, source_name: str = "mxu.zhl") -> Path:
    zlangc = require_tool("zlang", "ZLANGC")
    output = tmp_path / f"{top}.sv"
    subprocess.run(
        [
            zlangc,
            str(ROOT / "src" / source_name),
            "--project",
            str(ROOT / "zlang.toml"),
            "--top",
            top,
            "--systemverilog",
            str(output),
        ],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    return output


def compile_zlang_rom(
    tmp_path: Path, top: str, source_name: str
) -> tuple[Path, list[int]]:
    """Compile one ROM top and return the exact emitted memory words."""
    source = compile_zlang_top(tmp_path, top, source_name)
    match = re.search(r'\$readmemb\("([^"]+)"', source.read_text(encoding="ascii"))
    if match is None:
        raise AssertionError(f"generated RTL for {top} has no $readmemb companion")
    memory = source.parent / match.group(1)
    return source, [int(line, 2) for line in memory.read_text(encoding="ascii").splitlines()]


def run_iverilog(tmp_path: Path, sources: list[Path], testbench: str) -> str:
    iverilog = require_tool("iverilog")
    vvp = require_tool("vvp")
    tb = tmp_path / "tb.sv"
    tb.write_text(testbench, encoding="ascii")
    executable = tmp_path / "sim"
    subprocess.run(
        [iverilog, "-g2012", "-s", "tb", "-o", str(executable), *map(str, sources), str(tb)],
        cwd=tmp_path,
        check=True,
        text=True,
        capture_output=True,
    )
    return subprocess.run(
        [vvp, str(executable)], cwd=tmp_path, check=True, text=True, capture_output=True
    ).stdout


def run_verilator(tmp_path: Path, sources: list[Path], testbench: str) -> str:
    verilator = require_tool("verilator")
    tb = tmp_path / "tb_verilator.sv"
    tb.write_text(testbench, encoding="ascii")
    object_dir = tmp_path / "obj_dir"
    environment = os.environ.copy()
    environment["CCACHE_DISABLE"] = "1"
    subprocess.run(
        [
            verilator,
            "--binary",
            "--timing",
            "--top-module",
            "tb",
            "--Mdir",
            str(object_dir),
            "-Wno-fatal",
            *map(str, sources),
            str(tb),
        ],
        cwd=tmp_path,
        env=environment,
        check=True,
        text=True,
        capture_output=True,
    )
    return subprocess.run(
        [str(object_dir / "Vtb")],
        cwd=tmp_path,
        check=True,
        text=True,
        capture_output=True,
    ).stdout
