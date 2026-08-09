#!/usr/bin/env python3
"""Create a new, allowlisted MAHO public tree without mutating the source."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import tempfile
from pathlib import Path
from typing import Iterable


SOURCE_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = SOURCE_ROOT / "release/public-manifest.json"
PRIVATE_PATTERNS = {
    "macOS user path": re.compile(rb"/Users/[A-Za-z0-9._-]+/"),
    "private temporary path": re.compile(rb"/(?:private/tmp|private/var/folders|var/folders)/"),
    "AWS access key": re.compile(rb"AKIA[A-Z0-9]{16}"),
    "GitHub token": re.compile(rb"(?:ghp_|github_pat_)[A-Za-z0-9_-]{12,}"),
    "generic API secret": re.compile(rb"sk-[A-Za-z0-9_-]{20,}"),
    "private key": re.compile(rb"BEGIN [A-Z ]*PRIVATE KEY"),
}
PUBLIC_BLOCKERS = {
    "copyright holder": b"[COPYRIGHT " + b"HOLDER TO BE CONFIRMED BEFORE PUBLIC RELEASE]",
    "repository owner": b"github.com/" + b"OWNER/maho",
}


class ReleaseError(ValueError):
    pass


def _safe_manifest_path(value: object, *, field: str) -> Path:
    if not isinstance(value, str) or not value:
        raise ReleaseError(f"{field} entries must be non-empty strings")
    relative = Path(value)
    if (
        relative.is_absolute()
        or re.match(r"^[A-Za-z]:", value) is not None
        or relative == Path(".")
        or ".." in relative.parts
        or "\\" in value
        or "\x00" in value
        or relative.as_posix() != value
    ):
        raise ReleaseError(f"unsafe {field} path: {value!r}")
    return relative


def _contained_source(source: Path, relative: Path, *, require_directory: bool) -> Path:
    lexical = source / relative
    if lexical.is_symlink():
        raise ReleaseError(f"refusing public symlink: {relative}")
    try:
        resolved = lexical.resolve(strict=True)
        resolved.relative_to(source)
    except (OSError, ValueError) as exc:
        raise ReleaseError(f"source path escapes public root: {relative}") from exc
    expected = resolved.is_dir() if require_directory else resolved.is_file()
    if not expected:
        kind = "include root" if require_directory else "include file"
        raise ReleaseError(f"missing {kind}: {relative}")
    return lexical


def _manifest_paths(manifest: dict, source: Path) -> list[Path]:
    if not isinstance(manifest, dict):
        raise ReleaseError("release manifest must be an object")
    if manifest.get("schema_version") != 1:
        raise ReleaseError("release manifest requires schema_version 1")
    for field in ("include_roots", "include_files", "excluded_internal_roots"):
        value = manifest.get(field)
        if not isinstance(value, list):
            raise ReleaseError(f"release manifest {field} must be an array")
    for value in manifest["excluded_internal_roots"]:
        _safe_manifest_path(value, field="excluded_internal_roots")
    paths: set[Path] = set()
    for value in manifest["include_roots"]:
        relative = _safe_manifest_path(value, field="include_roots")
        root = _contained_source(source, relative, require_directory=True)
        for current, directories, files in os.walk(root, followlinks=False):
            current_path = Path(current)
            for name in directories:
                path = current_path / name
                if path.is_symlink():
                    raise ReleaseError(
                        f"refusing public symlink: {path.relative_to(source)}"
                    )
            directories[:] = sorted(directories)
            for name in sorted(files):
                path = current_path / name
                if path.is_symlink():
                    raise ReleaseError(f"refusing public symlink: {path.relative_to(source)}")
                relative_file = path.relative_to(source)
                _contained_source(source, relative_file, require_directory=False)
                paths.add(relative_file)
    for value in manifest["include_files"]:
        relative = _safe_manifest_path(value, field="include_files")
        _contained_source(source, relative, require_directory=False)
        paths.add(relative)
    return sorted(paths)


def _scan(paths: Iterable[Path], source: Path, allow_placeholders: bool) -> list[str]:
    findings: list[str] = []
    for relative in paths:
        data = (source / relative).read_bytes()
        for label, pattern in PRIVATE_PATTERNS.items():
            if pattern.search(data):
                findings.append(f"{relative}: {label}")
        if not allow_placeholders:
            for label, marker in PUBLIC_BLOCKERS.items():
                if marker in data:
                    findings.append(f"{relative}: unresolved {label}")
    return findings


def _copy(paths: Iterable[Path], source: Path, output: Path) -> None:
    for relative in paths:
        _safe_manifest_path(relative.as_posix(), field="resolved export")
        destination = output / relative
        try:
            destination.resolve(strict=False).relative_to(output)
        except ValueError as exc:
            raise ReleaseError(f"destination escapes export root: {relative}") from exc
        destination.parent.mkdir(parents=True, exist_ok=True)
        source_file = _contained_source(source, relative, require_directory=False)
        shutil.copy2(source_file, destination)


def _checksums(output: Path) -> None:
    lines = []
    for path in sorted(item for item in output.rglob("*") if item.is_file()):
        relative = path.relative_to(output)
        if str(relative) == "SHA256SUMS":
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        lines.append(f"{digest}  {relative.as_posix()}")
    (output / "SHA256SUMS").write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_public_tree(
    output: Path,
    *,
    source: Path = SOURCE_ROOT,
    manifest_path: Path = DEFAULT_MANIFEST,
    allow_private_beta_placeholders: bool = False,
) -> dict:
    source = source.resolve(strict=True)
    output = output.resolve()
    if output.exists() or output.is_symlink():
        raise ReleaseError(f"output already exists: {output}")
    try:
        output.relative_to(source)
    except ValueError:
        pass
    else:
        raise ReleaseError("output must be outside the development repository")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    paths = _manifest_paths(manifest, source)
    findings = _scan(paths, source, allow_private_beta_placeholders)
    if findings:
        raise ReleaseError("public release scan failed:\n- " + "\n- ".join(findings))
    result = {
        "schema_version": 1,
        "mode": "private-beta" if allow_private_beta_placeholders else "public-candidate",
        "file_count": len(paths),
        "output": str(output),
        "overwritten": 0,
        "excluded_internal_roots": manifest["excluded_internal_roots"],
    }
    persisted_result = {**result, "output": "."}
    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(
        tempfile.mkdtemp(
            prefix=f".{output.name}.staging-",
            dir=output.parent,
        )
    )
    try:
        _copy(paths, source, stage)
        (stage / "RELEASE_EXPORT.json").write_text(
            json.dumps(persisted_result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        _checksums(stage)
        stage.rename(output)
    except Exception:
        shutil.rmtree(stage, ignore_errors=True)
        raise
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument(
        "--allow-private-beta-placeholders",
        action="store_true",
        help="allow known copyright and repository placeholders for a non-public test tree",
    )
    args = parser.parse_args()
    try:
        result = build_public_tree(
            args.output,
            allow_private_beta_placeholders=args.allow_private_beta_placeholders,
        )
    except (OSError, ReleaseError, json.JSONDecodeError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
