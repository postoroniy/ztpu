from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess


ROOT = Path(__file__).resolve().parents[1]
LICENSE_SHA256 = "c0ea4a896d2c8c394b29f9427589996db826cd501c512279ff0ed3ef48fabbe5"
NOTICE = "Required Notice: Copyright 2026 Viacheslav Vinogradov\n"
REMOTE = "https://github.com/postoroniy/ztpu.git"
PIN = {
    "schema": "ztpu-zlang-toolchain-v2",
    "zlang_version": "0.1.0a23",
    "zlang_revision": "f773a89aa7ebfe3539b8834d339b072b35a0e562",
    "zlang_release_tag": "v0.1.0a23",
    "zlang_tag_object": "507fabbdfd15886c16d1a9496b26e510af308edb",
    "compiler_wheel_sha256": "f74e49f3c1b3a0cc9980d423b327f79c56e7376de48d9a9cff3de1d41d63a0f6",
    "native_wheel_sha256": "e491a03fcb62d2c55b23bc904d3837a43b4a094fe91214cf5a308e1164006c97",
}
REQUIRED = {
    Path("CHANGELOG.md"),
    Path("COMMERCIAL-LICENSE.md"),
    Path("CONTRIBUTING.md"),
    Path("LICENSE"),
    Path("NOTICE"),
    Path("README.md"),
    Path("RELEASING.md"),
    Path("zlang.toml"),
    Path("zlang.lock"),
    Path("contracts/formal_targets.json"),
    Path("contracts/simulator_scenarios.json"),
    Path("docs/GENERATED_OUTPUT.md"),
    Path("docs/FORMAL_VERIFICATION.md"),
    Path("docs/LICENSING.md"),
    Path("docs/ZLANG_DESIGN.md"),
    Path("docs/release/RELEASE_NOTES_0.1.0-alpha.1.md"),
    Path("docs/release/VALIDATION.md"),
    Path("tools/build_release_archive.py"),
    Path("tools/formal_verify.py"),
    Path("tools/simulator_diff.py"),
}


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    ).stdout.strip()


def tracked_files() -> list[Path]:
    return [Path(name) for name in git("ls-files").splitlines() if name]


def read_text(path: Path) -> str | None:
    try:
        return (ROOT / path).read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the public ZTPU release tree")
    parser.add_argument("--require-single-commit", action="store_true")
    parser.add_argument("--require-clean", action="store_true")
    args = parser.parse_args()

    errors: list[str] = []
    tracked = set(tracked_files())
    missing = sorted(REQUIRED - tracked)
    errors.extend(f"required release file is not tracked: {path}" for path in missing)

    license_digest = hashlib.sha256((ROOT / "LICENSE").read_bytes()).hexdigest()
    if license_digest != LICENSE_SHA256:
        errors.append(f"LICENSE is not the official byte-exact text: {license_digest}")
    if (ROOT / "NOTICE").read_text(encoding="ascii") != NOTICE:
        errors.append("NOTICE does not contain the approved Required Notice")

    toolchain = json.loads((ROOT / "contracts/toolchain.json").read_text())
    for key, expected in PIN.items():
        if toolchain.get(key) != expected:
            errors.append(f"toolchain pin mismatch for {key}: {toolchain.get(key)!r}")
    if toolchain.get("zlang_tag_signature_verified") is not True:
        errors.append("ZLang tag signature verification is not recorded")

    source_spdx = "SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0"
    for path in sorted(tracked):
        if path.suffix == ".zhl":
            text = read_text(path)
            if text is None or not any(source_spdx in line for line in text.splitlines()[:5]):
                errors.append(f"missing ZTPU SPDX identifier: {path}")

    private_fragments = (
        "/" + "home/",
        "/" + "Users/",
        "piz" + "data",
        "piece" + "data",
        ".co" + "dex/attachments",
        "ztpu-zlang-" + "dev",
    )
    old_spdx = "SPDX-License-Identifier: " + "BSD-3-Clause"
    apache_spdx = "SPDX-License-Identifier: " + "Apache-2.0"
    public_term = re.compile(r"\bopen[- ]source\b", re.IGNORECASE)
    secret_patterns = (
        re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
        re.compile(r"ghp_[A-Za-z0-9]{30,}"),
        re.compile(r"AKIA[0-9A-Z]{16}"),
    )
    for path in sorted(tracked):
        text = read_text(path)
        if text is None:
            errors.append(f"binary tracked file requires provenance review: {path}")
            continue
        for fragment in private_fragments:
            if fragment in text:
                errors.append(f"private path/name fragment in {path}: {fragment}")
        if old_spdx in text:
            errors.append(f"old BSD SPDX identifier in {path}")
        if apache_spdx in text:
            errors.append(f"Apache SPDX identifier incorrectly applied to ZTPU file: {path}")
        if public_term.search(text):
            errors.append(f"prohibited project-positioning term in {path}")
        for pattern in secret_patterns:
            if pattern.search(text):
                errors.append(f"possible credential/private key in {path}")

    remote = git("remote", "get-url", "origin")
    if remote != REMOTE:
        errors.append(f"unexpected origin remote: {remote}")
    if args.require_single_commit and git("rev-list", "--count", "HEAD") != "1":
        errors.append("release branch must contain exactly one commit")
    if args.require_clean and git("status", "--porcelain"):
        errors.append("release branch has tracked or untracked worktree changes")

    if errors:
        raise SystemExit("\n".join(errors))
    print(
        "release audit: PASS "
        f"({len(tracked)} tracked files, LICENSE sha256={LICENSE_SHA256}, "
        f"ZLang {PIN['zlang_version']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
