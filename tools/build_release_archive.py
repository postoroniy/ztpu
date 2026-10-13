from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import subprocess
import tarfile


ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.1.0-alpha.1"
PREFIX = f"ztpu-{VERSION}"
LICENSE_SHA256 = "c0ea4a896d2c8c394b29f9427589996db826cd501c512279ff0ed3ef48fabbe5"


def git(*args: str, binary: bool = False) -> bytes | str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=not binary,
    )
    return result.stdout if binary else result.stdout.strip()


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def validate_repository() -> None:
    if git("rev-list", "--count", "HEAD") != "1":
        raise SystemExit("release branch must contain exactly one commit")
    if git("status", "--porcelain"):
        raise SystemExit("release worktree must be clean")


def archive_bytes() -> bytes:
    tar_data = git(
        "archive",
        "--format=tar",
        f"--prefix={PREFIX}/",
        "HEAD",
        binary=True,
    )
    assert isinstance(tar_data, bytes)
    return gzip.compress(tar_data, compresslevel=9, mtime=0)


def validate_archive(data: bytes) -> int:
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as archive:
        members = archive.getmembers()
        if not members:
            raise SystemExit("release archive is empty")
        for member in members:
            path = PurePosixPath(member.name)
            if path.parts[0] != PREFIX or ".." in path.parts or path.is_absolute():
                raise SystemExit(f"unsafe archive member: {member.name}")
            if member.issym() or member.islnk():
                raise SystemExit(f"links are not allowed in release archive: {member.name}")
        names = {member.name for member in members}
        for required in ("LICENSE", "README.md", "src/queued_q16_ahb_top.zhl"):
            expected = f"{PREFIX}/{required}"
            if expected not in names:
                raise SystemExit(f"release archive is missing {expected}")
    return len(members)


def write_package(output_dir: Path) -> tuple[Path, Path, Path]:
    data = archive_bytes()
    if data != archive_bytes():
        raise SystemExit("git archive output is not reproducible")
    member_count = validate_archive(data)

    output_dir.mkdir(parents=True, exist_ok=True)
    archive_path = output_dir / f"{PREFIX}.tar.gz"
    metadata_path = output_dir / f"{PREFIX}.release.json"
    sums_path = output_dir / "SHA256SUMS"
    archive_path.write_bytes(data)

    toolchain = json.loads((ROOT / "contracts/toolchain.json").read_text())
    metadata = {
        "schema": "ztpu-source-release-v1",
        "version": VERSION,
        "commit": git("rev-parse", "HEAD"),
        "tree": git("rev-parse", "HEAD^{tree}"),
        "archive": archive_path.name,
        "archive_sha256": sha256(data),
        "archive_members": member_count,
        "license": "PolyForm-Noncommercial-1.0.0",
        "license_sha256": LICENSE_SHA256,
        "zlang_version": toolchain["zlang_version"],
        "zlang_revision": toolchain["zlang_revision"],
        "zlang_release_tag": toolchain["zlang_release_tag"],
    }
    metadata_bytes = (json.dumps(metadata, indent=2, sort_keys=True) + "\n").encode()
    metadata_path.write_bytes(metadata_bytes)
    sums_path.write_text(
        f"{sha256(data)}  {archive_path.name}\n"
        f"{sha256(metadata_bytes)}  {metadata_path.name}\n",
        encoding="ascii",
    )
    return archive_path, metadata_path, sums_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Build deterministic ZTPU source release")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "build" / "release")
    args = parser.parse_args()
    validate_repository()
    archive_path, metadata_path, sums_path = write_package(args.output_dir)
    print(f"release archive: {archive_path}")
    print(f"release metadata: {metadata_path}")
    print(f"checksums: {sums_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
