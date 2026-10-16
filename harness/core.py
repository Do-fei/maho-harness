"""Core discovery, bootstrap, readiness, and validation behavior.

The module deliberately uses only the Python standard library. It is a project
tool, not a security sandbox; platform sandbox and approval controls remain the
enforcement boundary.
"""

from __future__ import annotations

import hashlib
import fnmatch
import json
import os
import re
import shutil
import stat
import subprocess
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = 1
HARNESS_ROOT = Path(__file__).resolve().parent.parent
PACKAGED_ASSET_ROOT = Path(__file__).resolve().parent / "assets"


def runtime_asset_root() -> Path:
    """Return source assets in a checkout and bundled assets in an installed wheel."""
    if (HARNESS_ROOT / "stack-packs").is_dir() and (HARNESS_ROOT / "skills").is_dir():
        return HARNESS_ROOT
    return PACKAGED_ASSET_ROOT
IGNORED_DIRECTORIES = {
    ".git",
    ".harness",
    ".next",
    ".pytest_cache",
    ".venv",
    "__pycache__",
    "build",
    "coverage",
    "dist",
    "node_modules",
    "target",
    "venv",
}
MAX_DISCOVERY_FILES = 10_000
MAX_DISCOVERY_DEPTH = 8
MAX_JSON_BYTES = 1_000_000
MAX_TIMEOUT_SECONDS = 3_600
MAX_PROTECTED_SNAPSHOT_ENTRIES = 50_000
MAX_PROTECTED_SNAPSHOT_DEPTH = 128
MAX_PROTECTED_SNAPSHOT_FILE_BYTES = 64 * 1024 * 1024
MAX_PROTECTED_SNAPSHOT_TOTAL_BYTES = 512 * 1024 * 1024
MAX_PROTECTED_SNAPSHOT_SECONDS = 30.0
PROTECTED_SNAPSHOT_CHUNK_BYTES = 1024 * 1024
SHELL_EXECUTABLES = {"bash", "cmd", "fish", "pwsh", "powershell", "sh", "zsh"}
SHELL_CODE_FLAGS = {"-c", "-lc", "/c", "-command"}
SENSITIVE_ARGUMENT_NAMES = {
    "--access-token",
    "--api-key",
    "--authorization",
    "--client-secret",
    "--password",
    "--private-key",
    "--secret",
    "--token",
}
LIKELY_TOKEN_PATTERNS = (
    re.compile(r"^(?:sk-|ghp_|github_pat_)[A-Za-z0-9_-]{12,}$"),
    re.compile(r"^AKIA[A-Z0-9]{16}$"),
    re.compile(r"^[A-Z0-9_]*(?:TOKEN|PASSWORD|SECRET|API_KEY)=.+$", re.IGNORECASE),
    re.compile(r"^[a-z][a-z0-9+.-]*://[^/@\s:]+:[^@\s]+@", re.IGNORECASE),
)
PACK_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*$")
PACK_REQUIRED_FIELDS = {
    "schema_version",
    "id",
    "name",
    "version",
    "detect_any",
    "detect_all",
    "candidate_checks",
    "runtime_probe_types",
    "references",
    "conflicts",
}
PROJECT_REQUIRED_FIELDS = {
    "schema_version",
    "project_name",
    "checks",
    "proposed_checks",
    "protected_paths",
    "generated_paths",
    "runtime_probes",
    "selected_stack_packs",
}
CHECK_ALLOWED_FIELDS = {"id", "command", "cwd", "required", "timeout_seconds"}
PROPOSED_CHECK_ALLOWED_FIELDS = CHECK_ALLOWED_FIELDS | {"evidence", "stack_pack"}
CONSTITUTION_REQUIRED_HEADINGS = (
    "## Project",
    "## Supported commands",
    "## Protected paths",
    "## Generated paths",
    "## Stack guidance and runtime probes",
    "## Security and authority boundary",
    "## Required evidence",
)
CONSTITUTION_SECTION_REQUIRED_TERMS = {
    "## Project": (("name:",), ("goal", "scope"), ("stack", "repository")),
    "## Supported commands": (
        ("`", "no executable command"),
        ("proposed", "accepted", "validation"),
    ),
    "## Protected paths": (("`",), ("protect", "must not modify", "change")),
    "## Generated paths": (("`",),),
    "## Stack guidance and runtime probes": (
        ("stack", "guidance", "selected"),
        ("probe", "runtime"),
    ),
    "## Security and authority boundary": (
        ("sandbox", "approval", "permission", "authority"),
        ("secret", "credential", "push", "deploy", "publish", "account"),
    ),
    "## Required evidence": (("pass",), ("fail",), ("inconclusive",)),
}


class HarnessError(ValueError):
    """A user-actionable Harness input or boundary error."""


class ProtectedSnapshotError(HarnessError):
    """Protected evidence could not be captured conclusively."""

    def __init__(self, message: str, stats: dict[str, Any] | None = None):
        super().__init__(message)
        self.stats = stats or {}


class ProtectedSnapshotLimitError(ProtectedSnapshotError):
    """Protected evidence exceeded a declared resource budget."""


class _ProtectedSnapshotBudget:
    def __init__(self) -> None:
        self.started_at = time.monotonic()
        self.entries = 0
        self.files_hashed = 0
        self.bytes_hashed = 0
        self.max_depth_seen = 0

    @staticmethod
    def limits() -> dict[str, int | float]:
        return {
            "max_entries": MAX_PROTECTED_SNAPSHOT_ENTRIES,
            "max_depth": MAX_PROTECTED_SNAPSHOT_DEPTH,
            "max_file_bytes": MAX_PROTECTED_SNAPSHOT_FILE_BYTES,
            "max_total_bytes": MAX_PROTECTED_SNAPSHOT_TOTAL_BYTES,
            "max_seconds": MAX_PROTECTED_SNAPSHOT_SECONDS,
            "chunk_bytes": PROTECTED_SNAPSHOT_CHUNK_BYTES,
        }

    def stats(self) -> dict[str, int | float]:
        return {
            "entries": self.entries,
            "files_hashed": self.files_hashed,
            "bytes_hashed": self.bytes_hashed,
            "max_depth_seen": self.max_depth_seen,
            "elapsed_seconds": round(time.monotonic() - self.started_at, 6),
        }

    def _limit_error(self, message: str) -> None:
        raise ProtectedSnapshotLimitError(message, self.stats())

    def check_elapsed(self) -> None:
        if time.monotonic() - self.started_at > MAX_PROTECTED_SNAPSHOT_SECONDS:
            self._limit_error(
                f"protected snapshot exceeded {MAX_PROTECTED_SNAPSHOT_SECONDS:g}s time budget"
            )

    def add_entry(self, depth: int, label: str) -> None:
        self.check_elapsed()
        if depth > MAX_PROTECTED_SNAPSHOT_DEPTH:
            self._limit_error(
                f"protected snapshot depth exceeds {MAX_PROTECTED_SNAPSHOT_DEPTH}: {label}"
            )
        self.max_depth_seen = max(self.max_depth_seen, depth)
        self.entries += 1
        if self.entries > MAX_PROTECTED_SNAPSHOT_ENTRIES:
            self._limit_error(
                f"protected snapshot entry count exceeds {MAX_PROTECTED_SNAPSHOT_ENTRIES}: {label}"
            )

    def preflight_file(self, size: int, label: str) -> None:
        self.check_elapsed()
        if size > MAX_PROTECTED_SNAPSHOT_FILE_BYTES:
            self._limit_error(
                f"protected snapshot file exceeds {MAX_PROTECTED_SNAPSHOT_FILE_BYTES} bytes: {label}"
            )
        if self.bytes_hashed + size > MAX_PROTECTED_SNAPSHOT_TOTAL_BYTES:
            self._limit_error(
                "protected snapshot total file bytes exceed "
                f"{MAX_PROTECTED_SNAPSHOT_TOTAL_BYTES}: {label}"
            )


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def resolve_project(path: str | Path) -> Path:
    project = Path(path).expanduser().resolve(strict=True)
    if not project.is_dir():
        raise HarnessError(f"project is not a directory: {project}")
    return project


def is_within(root: Path, candidate: Path) -> bool:
    try:
        candidate.relative_to(root)
    except ValueError:
        return False
    return True


def contained_path(root: Path, value: str | Path, *, require_exists: bool = False) -> Path:
    raw = Path(value)
    candidate = raw if raw.is_absolute() else root / raw
    try:
        resolved = candidate.resolve(strict=require_exists)
    except OSError as exc:
        raise HarnessError(f"cannot resolve path {value!s}: {exc}") from exc
    if not is_within(root, resolved):
        raise HarnessError(f"path escapes project root: {value!s}")
    return resolved


def writable_path(root: Path, value: str | Path) -> Path:
    raw = Path(value)
    lexical = raw if raw.is_absolute() else root / raw
    if lexical.is_symlink():
        raise HarnessError(f"refusing to write through symlink: {value!s}")
    if lexical.exists() and not lexical.is_file():
        raise HarnessError(f"refusing non-file output collision: {value!s}")
    return contained_path(root, value)


def _safe_directory(root: Path, relative: str) -> Path:
    path = contained_path(root, relative)
    if path.exists() and not path.is_dir():
        raise HarnessError(f"expected directory, found non-directory: {relative}")
    path.mkdir(parents=True, exist_ok=True)
    resolved = path.resolve(strict=True)
    if not is_within(root, resolved):
        raise HarnessError(f"directory resolves outside project: {relative}")
    return resolved


def _json_bytes(data: Any) -> bytes:
    return (json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True) + "\n").encode()


def write_new(path: Path, content: bytes) -> str:
    """Write a file only when absent; return created or preserved."""
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    except FileExistsError:
        if not path.is_file():
            raise HarnessError(f"refusing non-file collision: {path}")
        return "preserved"
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(content)
    return "created"


def write_json(path: Path, data: Any, *, overwrite: bool = False) -> None:
    content = _json_bytes(data)
    path.parent.mkdir(parents=True, exist_ok=True)
    if overwrite:
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{path.name}.tmp-", dir=path.parent
        )
        temporary = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(content)
            os.replace(temporary, path)
        finally:
            if temporary.exists():
                temporary.unlink()
        return
    if write_new(path, content) == "preserved":
        raise HarnessError(f"refusing to overwrite existing file: {path}")


def read_json(path: Path) -> Any:
    try:
        if path.stat().st_size > MAX_JSON_BYTES:
            raise HarnessError(f"JSON file exceeds {MAX_JSON_BYTES} bytes: {path}")
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        if isinstance(exc, HarnessError):
            raise
        raise HarnessError(f"cannot read JSON {path}: {exc}") from exc


def _iter_files(root: Path) -> Iterable[Path]:
    count = 0
    for current, directories, files in os.walk(root, followlinks=False):
        current_path = Path(current)
        depth = len(current_path.relative_to(root).parts)
        directories[:] = sorted(
            directory
            for directory in directories
            if directory not in IGNORED_DIRECTORIES and depth < MAX_DISCOVERY_DEPTH
        )
        for filename in sorted(files):
            count += 1
            if count > MAX_DISCOVERY_FILES:
                return
            yield current_path / filename


def _relative_file_set(root: Path) -> set[str]:
    return {str(path.relative_to(root)) for path in _iter_files(root)}


def _package_metadata(root: Path) -> tuple[dict[str, Any], list[str]]:
    lexical_path = root / "package.json"
    if not lexical_path.exists() and not lexical_path.is_symlink():
        return {}, []
    try:
        package_path = contained_path(root, "package.json", require_exists=True)
    except HarnessError as exc:
        return {}, [str(exc)]
    if not package_path.is_file() or package_path.stat().st_size > MAX_JSON_BYTES:
        return {}, ["package.json is not a readable bounded file"]
    try:
        package = json.loads(package_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return {}, ["package.json exists but could not be parsed"]
    return package if isinstance(package, dict) else {}, []


def _safe_file_marker(root: Path, relative: str) -> bool:
    try:
        return contained_path(root, relative, require_exists=True).is_file()
    except HarnessError:
        return False


def _safe_directory_marker(root: Path, relative: str) -> bool:
    try:
        return contained_path(root, relative, require_exists=True).is_dir()
    except HarnessError:
        return False


def _bounded_text(root: Path, relative: str) -> str | None:
    try:
        path = contained_path(root, relative, require_exists=True)
        if not path.is_file() or path.stat().st_size > MAX_JSON_BYTES:
            return None
        return path.read_text(encoding="utf-8")
    except (HarnessError, OSError, UnicodeError):
        return None


def _constitution_is_resolved(text: str | None) -> bool:
    if text is None or len(text.strip()) < 200:
        return False
    upper = text.upper()
    if any(marker in upper for marker in ("TODO", "TBD", "PLACEHOLDER")):
        return False
    matches = list(re.finditer(r"^## .+$", text, re.MULTILINE))
    headings = [match.group(0).strip() for match in matches]
    required_positions = []
    for heading in CONSTITUTION_REQUIRED_HEADINGS:
        positions = [index for index, value in enumerate(headings) if value == heading]
        if len(positions) != 1:
            return False
        required_positions.append(positions[0])
    if required_positions != sorted(required_positions):
        return False
    for heading, heading_index in zip(
        CONSTITUTION_REQUIRED_HEADINGS, required_positions
    ):
        start = matches[heading_index].end()
        end = (
            matches[heading_index + 1].start()
            if heading_index + 1 < len(matches)
            else len(text)
        )
        body = text[start:end].strip().lower()
        if len(body) < 12:
            return False
        if any(
            not any(
                (
                    term in body
                    if term == "`"
                    else re.search(
                        rf"(?<![a-z0-9_-]){re.escape(term)}(?![a-z0-9_-])",
                        body,
                    )
                    is not None
                )
                for term in alternatives
            )
            for alternatives in CONSTITUTION_SECTION_REQUIRED_TERMS[heading]
        ):
            return False
    return True


def _package_manager(root: Path, files: set[str]) -> str:
    if "pnpm-lock.yaml" in files and _safe_file_marker(root, "pnpm-lock.yaml"):
        return "pnpm"
    if "yarn.lock" in files and _safe_file_marker(root, "yarn.lock"):
        return "yarn"
    if any(item in files and _safe_file_marker(root, item) for item in ("bun.lock", "bun.lockb")):
        return "bun"
    return "npm"


def _validate_marker(identifier: str, marker: str) -> None:
    path_value = marker
    if marker.startswith("dependency:") or marker.startswith("package-script:"):
        name = marker.split(":", 1)[1]
        if not name or ".." in name:
            raise HarnessError(f"stack pack {identifier} has unsafe marker: {marker}")
        return
    if marker.startswith("text:"):
        parts = marker.split(":", 2)
        if len(parts) != 3 or not parts[1] or not parts[2]:
            raise HarnessError(f"stack pack {identifier} has invalid text marker: {marker}")
        path_value = parts[1]
    elif marker.startswith("glob:"):
        path_value = marker.split(":", 1)[1]
    marker_path = Path(path_value)
    if not path_value or marker_path.is_absolute() or ".." in marker_path.parts:
        raise HarnessError(f"stack pack {identifier} has unsafe marker: {marker}")


def load_stack_packs(pack_root: Path | None = None) -> dict[str, dict[str, Any]]:
    root = pack_root or runtime_asset_root() / "stack-packs"
    if not root.is_dir():
        raise HarnessError(f"stack pack directory is missing: {root}")
    packs: dict[str, dict[str, Any]] = {}
    for path in sorted(root.glob("*/pack.json")):
        data = read_json(path)
        if not isinstance(data, dict):
            raise HarnessError(f"stack pack must be an object: {path}")
        missing = sorted(PACK_REQUIRED_FIELDS - data.keys())
        if missing:
            raise HarnessError(f"stack pack {path} is missing: {', '.join(missing)}")
        identifier = data.get("id")
        if not isinstance(identifier, str) or not PACK_ID_PATTERN.fullmatch(identifier):
            raise HarnessError(f"invalid stack pack id in {path}")
        if identifier != path.parent.name:
            raise HarnessError(f"stack pack id does not match directory: {path}")
        if identifier in packs:
            raise HarnessError(f"duplicate stack pack id: {identifier}")
        if data.get("schema_version") != SCHEMA_VERSION:
            raise HarnessError(f"stack pack {identifier} requires schema_version {SCHEMA_VERSION}")
        if not isinstance(data.get("version"), int) or isinstance(data.get("version"), bool) or data["version"] < 1:
            raise HarnessError(f"stack pack {identifier} has invalid version")
        for field in ("detect_any", "detect_all", "runtime_probe_types", "references", "conflicts"):
            value = data.get(field)
            if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
                raise HarnessError(f"stack pack {identifier} field {field} must be a string array")
        for marker in data["detect_any"] + data["detect_all"]:
            _validate_marker(identifier, marker)
        candidates = data.get("candidate_checks")
        if not isinstance(candidates, list):
            raise HarnessError(f"stack pack {identifier} candidate_checks must be an array")
        for index, candidate in enumerate(candidates):
            if not isinstance(candidate, dict):
                raise HarnessError(f"stack pack {identifier} candidate {index} must be an object")
            if not isinstance(candidate.get("id"), str) or not candidate["id"]:
                raise HarnessError(f"stack pack {identifier} candidate {index} requires id")
            when_any = candidate.get("when_any")
            if not isinstance(when_any, list) or not when_any or not all(
                isinstance(item, str) and item for item in when_any
            ):
                raise HarnessError(f"stack pack {identifier} candidate {index} requires when_any")
            for marker in when_any:
                _validate_marker(identifier, marker)
            command = candidate.get("command")
            if not isinstance(command, list) or not command or not all(
                isinstance(item, str) and item for item in command
            ):
                raise HarnessError(f"stack pack {identifier} candidate {index} requires command array")
            _validate_command(command)
            executable_path = Path(command[0])
            if executable_path.is_absolute() or ".." in executable_path.parts:
                raise HarnessError(
                    f"stack pack {identifier} candidate {index} has non-portable executable"
                )
            cwd = candidate.get("cwd", ".")
            cwd_path = Path(cwd) if isinstance(cwd, str) else None
            if cwd_path is None or cwd_path.is_absolute() or ".." in cwd_path.parts:
                raise HarnessError(f"stack pack {identifier} candidate {index} has unsafe cwd")
            required = candidate.get("required")
            timeout = candidate.get("timeout_seconds")
            if not isinstance(required, bool):
                raise HarnessError(f"stack pack {identifier} candidate {index} requires boolean required")
            if not isinstance(timeout, int) or isinstance(timeout, bool) or not 1 <= timeout <= MAX_TIMEOUT_SECONDS:
                raise HarnessError(f"stack pack {identifier} candidate {index} has invalid timeout")
        guidance_path = path.parent / "GUIDANCE.md"
        if (
            guidance_path.is_symlink()
            or not guidance_path.is_file()
            or guidance_path.stat().st_size > MAX_JSON_BYTES
        ):
            raise HarnessError(f"stack pack {identifier} requires a bounded GUIDANCE.md")
        data["_source_directory"] = str(path.parent.resolve(strict=True))
        packs[identifier] = data
    if not packs:
        raise HarnessError("no stack packs found")
    for identifier, pack in packs.items():
        for conflict in pack["conflicts"]:
            if conflict == identifier or conflict not in packs:
                raise HarnessError(
                    f"stack pack {identifier} has invalid conflict reference: {conflict}"
                )
    return packs


def _marker_evidence(
    root: Path,
    marker: str,
    files: set[str],
    dependencies: dict[str, Any],
    scripts: dict[str, Any],
    warnings: list[str],
) -> list[str]:
    if marker.startswith("dependency:"):
        name = marker.split(":", 1)[1]
        return [f"package.json dependency:{name}"] if name in dependencies else []
    if marker.startswith("package-script:"):
        name = marker.split(":", 1)[1]
        return [f"package.json script:{name}"] if name in scripts else []
    if marker.startswith("glob:"):
        pattern = marker.split(":", 1)[1]
        matches = [
            item
            for item in sorted(files)
            if fnmatch.fnmatch(item, pattern) and _safe_file_marker(root, item)
        ]
        return matches[:20]
    if marker.startswith("text:"):
        _, filename, needle = marker.split(":", 2)
        lexical_path = root / filename
        if not lexical_path.exists() and not lexical_path.is_symlink():
            return []
        try:
            path = contained_path(root, filename, require_exists=True)
            if not path.is_file() or path.stat().st_size > MAX_JSON_BYTES:
                warnings.append(f"{filename} is not a readable bounded file")
                return []
            content = path.read_text(encoding="utf-8").lower()
        except (HarnessError, OSError, UnicodeError) as exc:
            warnings.append(f"{filename} could not be read safely: {exc}")
            return []
        return [f"{filename} contains:{needle}"] if needle.lower() in content else []
    return [marker] if marker in files and _safe_file_marker(root, marker) else []


def _render_candidate_command(template: list[str], package_manager: str) -> list[str]:
    allowed = {"{package_manager}": package_manager}
    rendered: list[str] = []
    for item in template:
        if "{" in item or "}" in item:
            if item not in allowed:
                raise HarnessError(f"unsupported command placeholder: {item}")
            rendered.append(allowed[item])
        else:
            rendered.append(item)
    return rendered


def discover(root: Path, pack_root: Path | None = None) -> dict[str, Any]:
    pack_catalog = load_stack_packs(pack_root)
    files = _relative_file_set(root)
    package, warnings = _package_metadata(root)
    dependencies: dict[str, Any] = {}
    for key in ("dependencies", "devDependencies", "peerDependencies"):
        value = package.get(key, {})
        if isinstance(value, dict):
            dependencies.update(value)
    scripts = package.get("scripts", {})
    if not isinstance(scripts, dict):
        scripts = {}

    signals: list[dict[str, str]] = []
    stacks: list[dict[str, Any]] = []
    proposed_checks: list[dict[str, Any]] = []

    marker_cache: dict[str, list[str]] = {}

    def evidence_for(marker: str) -> list[str]:
        if marker not in marker_cache:
            marker_cache[marker] = _marker_evidence(
                root, marker, files, dependencies, scripts, warnings
            )
        return marker_cache[marker]

    matched_packs: list[dict[str, Any]] = []
    for identifier, pack in sorted(pack_catalog.items()):
        any_evidence = [item for marker in pack["detect_any"] for item in evidence_for(marker)]
        all_evidence = [evidence_for(marker) for marker in pack["detect_all"]]
        matches_any = not pack["detect_any"] or bool(any_evidence)
        matches_all = all(bool(items) for items in all_evidence)
        if not (matches_any and matches_all):
            continue
        evidence = sorted(set(any_evidence + [item for items in all_evidence for item in items]))
        stack = {
            "id": identifier,
            "pack_version": pack["version"],
            "match": "MATCH",
            "evidence": evidence,
            "guidance_source": str(
                Path(pack["_source_directory"]) / "GUIDANCE.md"
            ),
            "runtime_probe_types": pack["runtime_probe_types"],
            "references": pack["references"],
            "conflicts": pack["conflicts"],
        }
        stacks.append(stack)
        matched_packs.append(pack)
        for item in evidence:
            signals.append({"stack": identifier, "signal": item})

    manager = _package_manager(root, files)
    seen_check_ids: set[str] = set()
    for pack in matched_packs:
        for candidate in pack["candidate_checks"]:
            evidence = [
                item for marker in candidate["when_any"] for item in evidence_for(marker)
            ]
            if not evidence:
                continue
            identifier = candidate["id"]
            if identifier in seen_check_ids:
                warnings.append(f"duplicate proposed check id ignored: {identifier}")
                continue
            seen_check_ids.add(identifier)
            proposed_checks.append(
                {
                    "id": identifier,
                    "command": _render_candidate_command(candidate["command"], manager),
                    "cwd": candidate.get("cwd", "."),
                    "required": candidate["required"],
                    "timeout_seconds": candidate["timeout_seconds"],
                    "evidence": ", ".join(sorted(set(evidence))),
                    "stack_pack": pack["id"],
                }
            )

    matched_ids = {pack["id"] for pack in matched_packs}
    active_conflicts: list[dict[str, str]] = []
    seen_conflicts: set[tuple[str, str]] = set()
    for pack in matched_packs:
        for other in pack["conflicts"]:
            if other not in matched_ids:
                continue
            pair = tuple(sorted((pack["id"], other)))
            if pair in seen_conflicts:
                continue
            seen_conflicts.add(pair)
            active_conflicts.append({"left": pair[0], "right": pair[1]})
            warnings.append(f"stack pack conflict: {pair[0]} conflicts with {pair[1]}")

    runtime_probe_types = sorted(
        {
            probe
            for pack in matched_packs
            for probe in pack["runtime_probe_types"]
        }
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": utc_now(),
        "project_root": str(root),
        "file_count_scanned": min(len(files), MAX_DISCOVERY_FILES),
        "scan_truncated": len(files) >= MAX_DISCOVERY_FILES,
        "stacks": sorted(stacks, key=lambda item: item["id"]),
        "signals": sorted(signals, key=lambda item: (item["stack"], item["signal"])),
        "proposed_checks": proposed_checks,
        "runtime_probe_types": runtime_probe_types,
        "conflicts": active_conflicts,
        "warnings": warnings,
    }


def _git_state(root: Path) -> tuple[bool, list[str], str | None]:
    if not (root / ".git").exists():
        return False, [], None
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "status", "--porcelain"],
            capture_output=True,
            check=False,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return True, [], str(exc)
    lines = result.stdout.splitlines() if result.returncode == 0 else []
    error = None if result.returncode == 0 else result.stderr.strip() or "git status failed"
    return True, lines, error


def readiness(root: Path, discovery: dict[str, Any] | None = None) -> dict[str, Any]:
    discovery = discovery or discover(root)
    findings: list[dict[str, str]] = []

    def finding(identifier: str, status: str, message: str) -> None:
        findings.append({"id": identifier, "status": status, "message": message})

    git_present, dirty, git_error = _git_state(root)
    finding("version-control", "PASS" if git_present else "FAIL", "Git repository found" if git_present else "No Git repository found")
    if git_error:
        finding("git-status", "WARN", f"Git state unavailable: {git_error}")
    elif dirty:
        finding("git-status", "WARN", f"Working tree has {len(dirty)} changed path(s)")
    else:
        finding("git-status", "PASS", "Working tree is clean")

    files = _relative_file_set(root)
    has_readme = any(
        _safe_file_marker(root, name)
        for name in ("README.md", "README.rst", "README.txt")
    )
    finding(
        "documentation",
        "PASS" if has_readme else "WARN",
        "README found" if has_readme else "README not found",
    )

    has_guidance = _safe_file_marker(root, "AGENTS.md") and _safe_file_marker(
        root, ".harness/PROJECT_CONSTITUTION.md"
    )
    constitution_text = _bounded_text(root, ".harness/PROJECT_CONSTITUTION.md")
    guidance_status = (
        "PASS" if has_guidance and _constitution_is_resolved(constitution_text) else "FAIL"
    )
    guidance_message = (
        "AGENTS.md and resolved Project Constitution found"
        if guidance_status == "PASS"
        else "AGENTS.md or a complete resolved Project Constitution is missing"
    )
    finding("project-guidance", guidance_status, guidance_message)

    config_path = root / ".harness/project.json"
    configured_checks = 0
    config: dict[str, Any] | None = None
    if config_path.is_file():
        try:
            config = load_project_config(root, config_path)
            configured_checks = len(config["checks"])
            finding("configuration", "PASS", "Harness project configuration is valid")
        except HarnessError as exc:
            finding("configuration", "FAIL", str(exc))
    else:
        finding("configuration", "FAIL", "Missing .harness/project.json")

    finding(
        "validation-path",
        "PASS" if configured_checks else "FAIL",
        f"{configured_checks} configured check(s)" if configured_checks else "No accepted validation checks configured",
    )

    documentation_text = "\n".join(
        text.lower()
        for text in (
            _bounded_text(root, "README.md"),
            constitution_text,
        )
        if text is not None
    )
    undocumented_checks = []
    for item in (config or {}).get("checks", []):
        identifier = item["id"].lower()
        identifier_pattern = re.compile(
            rf"(?<![a-z0-9_-]){re.escape(identifier)}(?![a-z0-9_-])"
        )
        if not identifier_pattern.search(documentation_text):
            undocumented_checks.append(item["id"])
    finding(
        "command-documentation",
        "PASS" if configured_checks and not undocumented_checks else "WARN",
        (
            "All accepted check IDs are documented"
            if configured_checks and not undocumented_checks
            else (
                f"Undocumented accepted checks: {', '.join(undocumented_checks)}"
                if undocumented_checks
                else "No accepted checks are available to document"
            )
        ),
    )

    stacks = discovery.get("stacks", [])
    finding("stack-discovery", "PASS" if stacks else "WARN", f"Detected {len(stacks)} stack pack(s)" if stacks else "No known stack markers detected")
    finding(
        "stack-conflicts",
        "FAIL" if discovery.get("conflicts") else "PASS",
        (
            f"{len(discovery['conflicts'])} active Stack Pack conflict(s)"
            if discovery.get("conflicts")
            else "No active Stack Pack conflicts"
        ),
    )

    test_files = [
        item
        for item in files
        if (
            item.startswith(("test/", "tests/"))
            or Path(item).name.startswith(("test_", "test."))
            or Path(item).name.endswith((".test.js", ".test.mjs", ".spec.js", ".spec.ts"))
        )
        and _safe_file_marker(root, item)
    ]
    test_checks = [
        item
        for item in ((config or {}).get("checks", []) + discovery.get("proposed_checks", []))
        if "test" in item.get("id", "").lower()
    ]
    finding(
        "testability",
        "PASS" if test_files and test_checks else "WARN",
        (
            f"{len(test_files)} test file(s) and {len(test_checks)} test command(s) found"
            if test_files and test_checks
            else "Executable tests or a test command are not both discoverable"
        ),
    )

    package, _ = _package_metadata(root)
    dependencies = {}
    for key in ("dependencies", "devDependencies"):
        if isinstance(package.get(key), dict):
            dependencies.update(package[key])
    node_lock = any(
        item in files and _safe_file_marker(root, item)
        for item in (
            "package-lock.json",
            "pnpm-lock.yaml",
            "yarn.lock",
            "bun.lock",
            "bun.lockb",
        )
    )
    python_dependencies = False
    for name in ("pyproject.toml", "requirements.txt"):
        text = _bounded_text(root, name)
        if text is not None:
            python_dependencies = python_dependencies or any(
                token in text.lower()
                for token in ("dependencies", "==", ">=", "~=")
            )
    requirements_text = _bounded_text(root, "requirements.txt")
    python_lock = any(
        item in files and _safe_file_marker(root, item)
        for item in ("uv.lock", "poetry.lock", "Pipfile.lock", "requirements.lock")
    ) or (
        requirements_text is not None and "==" in requirements_text
    )
    reproducible = (not dependencies or node_lock) and (
        not python_dependencies or python_lock
    )
    finding(
        "build-reproducibility",
        "PASS" if reproducible else "WARN",
        (
            "Dependency inputs have a lock or exact requirement"
            if reproducible
            else "Dependencies are declared without a detected lock or exact requirement"
        ),
    )

    has_node = "package.json" in files and _safe_file_marker(root, "package.json")
    has_python = any(
        item in files and _safe_file_marker(root, item)
        for item in ("pyproject.toml", "requirements.txt", "setup.py")
    ) or any(item.endswith(".py") for item in test_files)
    node_version = any(
        item in files and _safe_file_marker(root, item)
        for item in (".node-version", ".nvmrc", ".tool-versions")
    ) or isinstance(package.get("engines"), dict)
    python_version = any(
        item in files and _safe_file_marker(root, item)
        for item in (".python-version", ".tool-versions")
    )
    pyproject_text = _bounded_text(root, "pyproject.toml")
    if pyproject_text is not None:
        python_version = python_version or "requires-python" in pyproject_text
    environment_clear = (not has_node or node_version) and (
        not has_python or python_version
    )
    finding(
        "environment",
        "PASS" if environment_clear else "WARN",
        (
            "Detected runtime versions are constrained"
            if environment_clear
            else "A detected runtime has no version constraint"
        ),
    )

    source_dirs = [
        name
        for name in ("src", "app", "lib")
        if _safe_directory_marker(root, name)
    ]
    structure_clear = bool(source_dirs and test_files)
    finding(
        "repository-structure",
        "PASS" if structure_clear else "WARN",
        (
            f"Source directories {source_dirs} and tests are discoverable"
            if structure_clear
            else "Source and test structure is incomplete or ambiguous"
        ),
    )

    probes = (config or {}).get("runtime_probes", [])
    failed_probes = [item["type"] for item in probes if item["status"] == "FAIL"]
    passed_probes = [item["type"] for item in probes if item["status"] == "PASS"]
    if failed_probes:
        probe_status = "FAIL"
        probe_message = f"Failed runtime probes: {', '.join(failed_probes)}"
    elif probes and len(passed_probes) == len(probes):
        probe_status = "PASS"
        probe_message = f"{len(probes)} runtime probe(s) passed"
    elif probes:
        probe_status = "WARN"
        states = ", ".join(sorted({item["status"] for item in probes}))
        probe_message = f"Runtime probe evidence is not complete: {states}"
    else:
        probe_status = "WARN"
        probe_message = "No runtime or observability probe is declared"
    finding(
        "observability",
        probe_status,
        probe_message,
    )

    ci_present = any(
        (
            item.startswith(".github/workflows/")
            or item in ("azure-pipelines.yml", ".gitlab-ci.yml")
        )
        and _safe_file_marker(root, item)
        for item in files
    )
    finding(
        "ci",
        "PASS" if ci_present else "WARN",
        "CI configuration found" if ci_present else "No CI configuration found",
    )

    finding(
        "automation",
        "PASS" if configured_checks and ci_present else "WARN",
        (
            "Accepted checks and CI automation are present"
            if configured_checks and ci_present
            else "Accepted checks and CI automation are not both present"
        ),
    )

    finding(
        "local-setup",
        "PASS" if has_readme and reproducible and environment_clear else "WARN",
        (
            "Local setup has documentation, reproducible dependencies, and runtime constraints"
            if has_readme and reproducible and environment_clear
            else "Local setup documentation, dependency locks, or runtime constraints are incomplete"
        ),
    )

    manual_markers = []
    for item in sorted(files):
        if not _safe_file_marker(root, item):
            continue
        name_marker = (
            "manual-only" in item.lower()
            or Path(item).name.lower().startswith("manual")
        )
        content_marker = False
        if Path(item).suffix.lower() in {".md", ".rst", ".txt"}:
            text = _bounded_text(root, item)
            content_marker = bool(
                text
                and any(
                    phrase in text.lower()
                    for phrase in ("run manually", "by hand", "manual-only")
                )
            )
        if name_marker or content_marker:
            manual_markers.append(item)
    finding(
        "manual-workflows",
        "WARN" if manual_markers else "PASS",
        (
            f"Potential manual-only workflow markers: {', '.join(manual_markers[:5])}"
            if manual_markers
            else "No manual-only workflow marker detected"
        ),
    )

    overall = "NEEDS_ATTENTION" if any(item["status"] == "FAIL" for item in findings) else "READY"
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": utc_now(),
        "project_root": str(root),
        "overall": overall,
        "findings": findings,
    }


def _project_config_from_discovery(
    root: Path,
    discovery: dict[str, Any],
    locale: str = "en",
) -> dict[str, Any]:
    protected = [
        "AGENTS.md",
        ".harness/project.json",
        ".harness/PROJECT_CONSTITUTION.md",
    ]
    for name in (
        "package-lock.json",
        "pnpm-lock.yaml",
        "yarn.lock",
        "bun.lock",
        "bun.lockb",
        "uv.lock",
        "poetry.lock",
        "Pipfile.lock",
    ):
        if (root / name).is_file():
            protected.append(name)

    selected_stack_packs = []
    probe_owners: dict[str, list[str]] = {}
    for stack in discovery["stacks"]:
        identifier = stack["id"]
        for probe in stack["runtime_probe_types"]:
            probe_owners.setdefault(probe, []).append(identifier)
        selected_stack_packs.append(
            {
                "id": identifier,
                "version": stack["pack_version"],
                "guidance": (
                    f".harness/stack-packs/{identifier}/GUIDANCE.zh-CN.md"
                    if locale == "zh-CN"
                    else f".harness/stack-packs/{identifier}/GUIDANCE.md"
                ),
                "runtime_probe_types": stack["runtime_probe_types"],
                "references": stack["references"],
                "conflicts": stack["conflicts"],
            }
        )

    return {
        "schema_version": SCHEMA_VERSION,
        "project_name": root.name,
        "checks": [],
        "proposed_checks": discovery["proposed_checks"],
        "protected_paths": protected,
        "generated_paths": [".harness/runs"],
        "runtime_probes": [
            {
                "type": probe,
                "stack_packs": sorted(owners),
                "status": "PROPOSED",
            }
            for probe, owners in sorted(probe_owners.items())
        ],
        "selected_stack_packs": selected_stack_packs,
    }


def _render_constitution(
    root: Path,
    discovery: dict[str, Any],
    project_config: dict[str, Any],
    locale: str = "en",
) -> str:
    stack_names = ", ".join(item["id"] for item in discovery["stacks"]) or "UNKNOWN"
    proposed = discovery["proposed_checks"]
    commands = "\n".join(
        f"- **{item['id']}**: `{json.dumps(item['command'], ensure_ascii=False)}` — proposed from {item['evidence']}"
        for item in proposed
    ) or "- No executable command was discovered; an accepted validation path is required before READY."
    protected = "\n".join(
        f"- `{item}`" for item in project_config["protected_paths"]
    )
    generated = "\n".join(
        f"- `{item}`" for item in project_config["generated_paths"]
    )
    guidance = "\n".join(
        f"- [{item['id']}]({item['guidance']}) — probes: "
        + (", ".join(item["runtime_probe_types"]) or "none")
        + "; references: "
        + (", ".join(item["references"]) or "none")
        for item in project_config["selected_stack_packs"]
    ) or "- No Stack Pack guidance matched."
    architecture_candidates = [
        item
        for item in (
            "README.md",
            "ARCHITECTURE.md",
            "docs/ARCHITECTURE.md",
            "docs/architecture.md",
        )
        if _safe_file_marker(root, item)
    ]
    architecture = "\n".join(
        f"- [{item}](../{item})" for item in architecture_candidates
    ) or "- No architecture document detected; create one before an L3 architecture change."
    if locale == "zh-CN":
        commands_zh = "\n".join(
            f"- **{item['id']}**：`{json.dumps(item['command'], ensure_ascii=False)}` — proposed 建议来源：{item['evidence']}"
            for item in proposed
        ) or "- 未发现可执行命令；在达到 READY 前必须配置 accepted validation checks（已接受验证检查）。"
        guidance_zh = "\n".join(
            f"- [{item['id']}]({item['guidance'].replace('GUIDANCE.md', 'GUIDANCE.zh-CN.md')})"
            f" — probes 运行时探针：{', '.join(item['runtime_probe_types']) or '无'}；"
            f"references 参考：{', '.join(item['references']) or '无'}"
            for item in project_config["selected_stack_packs"]
        ) or "- 没有匹配的 stack guidance（技术栈指南）。"
        return f"""# 项目宪法 / Project Constitution

状态：ACTIVE — 生成证据必须与项目变更一起审阅。

## Project

- Name: {root.name}（名称）
- Goal 目标来源：仓库 README 或任务验收合同
- Stack 检测到的技术栈：{stack_names}

## Supported commands

{commands_zh}

## Protected paths

{protected}

Accepted validation commands（已接受验证命令）不得 modify（修改）这些 protect（受保护）路径；MAHO 会把变化记录为失败。

## Generated paths

{generated}

## Stack guidance and runtime probes

{guidance_zh}

Probe（探针）类型是必须考虑的 requirements（要求），不是运行时已经通过的声明。

## Security and authority boundary

- Native sandbox、approval、permission 和 authority 仍是执行边界。
- 未获明确授权时，不得处理 secret 或 credential，不得 push、deploy、publish 或变更 account。
- 被拒绝或不可用的操作必须记录为 NOT RUN，不得绕过 enforcement（强制控制）。

## Required evidence

- 将完成声明映射到已配置检查和边界相关验证。
- 只使用 PASS、FAIL 或 INCONCLUSIVE；未运行检查绝不算通过。
- 保留未解决工作和已知基线失败。

## Architecture pointers

{architecture}
"""
    return f"""# Project Constitution\n\nStatus: ACTIVE — generated evidence must be reviewed with project changes.\n\n## Project\n\n- Name: {root.name}\n- Goal source: repository README or task Acceptance Contract\n- Detected stacks: {stack_names}\n\n## Supported commands\n\n{commands}\n\n## Protected paths\n\n{protected}\n\nAccepted validation commands must not modify these paths. The Harness records a protected-path change as validation failure.\n\n## Generated paths\n\n{generated}\n\n## Stack guidance and runtime probes\n\n{guidance}\n\nProbe types are requirements to consider, not claims that runtime behavior already passed.\n\n## Security and authority boundary\n\n- Project commands are trusted code and remain subject to native sandbox and approval enforcement.\n- Do not push, deploy, publish, change accounts, handle real secrets, or cross the resolved repository root without explicit authority.\n- Report a denied or unavailable action as NOT RUN; do not route around enforcement.\n\n## Required evidence\n\n- Map completion claims to configured checks and boundary-specific validation.\n- Report PASS, FAIL, or INCONCLUSIVE; never treat an unrun check as PASS.\n- Preserve unresolved work and known baseline failures.\n\n## Architecture pointers\n\n{architecture}\n"""


def bootstrap_plan(
    root: Path,
    discovery: dict[str, Any] | None = None,
    *,
    locale: str = "en",
) -> dict[str, Any]:
    discovery = discovery or discover(root)
    files = [
        ".harness/project.json",
        ".harness/DISCOVERY.json",
        ".harness/READINESS.json",
        ".harness/PROJECT_CONSTITUTION.md",
        ".harness/AGENTS_SNIPPET.md",
    ]
    guidance_name = "GUIDANCE.zh-CN.md" if locale == "zh-CN" else "GUIDANCE.md"
    files.extend(
        f".harness/stack-packs/{item['id']}/{guidance_name}"
        for item in discovery["stacks"]
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "mode": "dry-run",
        "project_root": str(root),
        "would_create": [item for item in files if not (root / item).exists()],
        "would_preserve": [item for item in files if (root / item).exists()],
        "existing_agents": (root / "AGENTS.md").exists(),
        "proposed_checks": discovery["proposed_checks"],
        "note": (
            "Use --apply to create only missing MAHO files. Existing files are never overwritten."
            if locale == "en"
            else "使用 --apply 只创建缺失的 MAHO 文件，绝不覆盖现有文件。"
        ),
    }


def apply_bootstrap(
    root: Path,
    *,
    install_agents: bool = False,
    locale: str = "en",
) -> dict[str, Any]:
    if locale not in {"en", "zh-CN"}:
        raise HarnessError(f"unsupported locale: {locale}")
    discovery = discover(root)
    harness_dir = _safe_directory(root, ".harness")
    project_config = _project_config_from_discovery(root, discovery, locale)
    files: dict[str, bytes] = {
        "project.json": _json_bytes(project_config),
        "DISCOVERY.json": _json_bytes(discovery),
        "PROJECT_CONSTITUTION.md": _render_constitution(
            root, discovery, project_config, locale
        ).encode(),
        "AGENTS_SNIPPET.md": (
            b"# MAHO integration snippet\n\nRead `.harness/PROJECT_CONSTITUTION.md` before changing this repository.\n"
            if locale == "en"
            else "# MAHO 集成片段\n\n修改本仓库前，请阅读 `.harness/PROJECT_CONSTITUTION.md`。\n".encode()
        ),
    }
    outcomes = {name: write_new(harness_dir / name, content) for name, content in files.items()}

    guidance_outcomes: dict[str, str] = {}
    for stack in discovery["stacks"]:
        identifier = stack["id"]
        source = Path(stack["guidance_source"])
        destination_name = "GUIDANCE.md"
        if locale == "zh-CN":
            localized_source = source.with_name("GUIDANCE.zh-CN.md")
            if localized_source.is_file():
                source = localized_source
                destination_name = "GUIDANCE.zh-CN.md"
        destination = contained_path(
            root,
            f".harness/stack-packs/{identifier}/{destination_name}",
        )
        guidance_outcomes[identifier] = write_new(destination, source.read_bytes())

    agents_outcome = "not-requested"
    if install_agents:
        agents_path = root / "AGENTS.md"
        if agents_path.exists() or agents_path.is_symlink():
            agents_outcome = "preserved-existing"
        else:
            agents_outcome = write_new(
                agents_path,
                (
                    b"# Project instructions\n\nRead `.harness/PROJECT_CONSTITUTION.md` before changing this repository.\n"
                    if locale == "en"
                    else "# 项目说明\n\n修改本仓库前，请阅读 `.harness/PROJECT_CONSTITUTION.md`。\n".encode()
                ),
            )

    post_bootstrap_readiness = readiness(root, discovery)
    outcomes["READINESS.json"] = write_new(
        harness_dir / "READINESS.json",
        _json_bytes(post_bootstrap_readiness),
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "mode": "apply",
        "project_root": str(root),
        "files": outcomes,
        "agents": agents_outcome,
        "stack_guidance": guidance_outcomes,
        "next": (
            "Review proposed checks and copy accepted entries into checks before validation."
            if locale == "en"
            else "审阅建议检查，并在验证前将认可条目复制到 checks。"
        ),
    }


def _validate_command(command: Any) -> list[str]:
    if not isinstance(command, list) or not command:
        raise HarnessError("check.command must be a non-empty array")
    if not all(isinstance(item, str) and item for item in command):
        raise HarnessError("check.command entries must be non-empty strings")
    executable = Path(command[0]).name.lower()
    if executable in SHELL_EXECUTABLES and any(item.lower() in SHELL_CODE_FLAGS for item in command[1:3]):
        raise HarnessError("shell code flags are prohibited; commit a project script and execute it directly")
    for index, item in enumerate(command):
        lowered = item.lower()
        name = lowered.split("=", 1)[0]
        if name in SENSITIVE_ARGUMENT_NAMES:
            raise HarnessError(
                f"secret-bearing command arguments are prohibited: {name}; use task-scoped credential tooling"
            )
        if index > 0 and any(pattern.search(item) for pattern in LIKELY_TOKEN_PATTERNS):
            raise HarnessError(
                "command contains a likely credential; secrets must not be stored in Harness configuration"
            )
    return command


def _normalize_declared_paths(root: Path, data: dict[str, Any], field: str) -> list[Path]:
    values = data.get(field)
    if not isinstance(values, list) or not values:
        raise HarnessError(f"project configuration {field} must be a non-empty array")
    normalized: list[Path] = []
    seen: set[str] = set()
    for index, value in enumerate(values):
        if not isinstance(value, str) or not value:
            raise HarnessError(f"{field}[{index}] must be a non-empty string")
        raw = Path(value)
        if raw.is_absolute() or ".." in raw.parts:
            raise HarnessError(f"{field}[{index}] must be a contained relative path")
        lexical = root / raw
        if field == "protected_paths":
            current = root
            for part in raw.parts[:-1]:
                current /= part
                if current.is_symlink():
                    raise HarnessError(
                        f"{field}[{index}] has a symlinked parent: {current.relative_to(root)}"
                    )
        resolved = contained_path(root, value)
        path = lexical if field == "protected_paths" else resolved
        relative = str((root / raw).relative_to(root))
        if relative in seen:
            raise HarnessError(f"duplicate {field} path: {relative}")
        seen.add(relative)
        normalized.append(path)
    return normalized


def _validate_stack_selection(root: Path, value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise HarnessError("selected_stack_packs must be an array")
    normalized = []
    seen: set[str] = set()
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise HarnessError(f"selected_stack_packs[{index}] must be an object")
        required = {
            "id",
            "version",
            "guidance",
            "runtime_probe_types",
            "references",
            "conflicts",
        }
        if set(item) != required:
            raise HarnessError(
                f"selected_stack_packs[{index}] fields must be {sorted(required)}"
            )
        identifier = item["id"]
        if not isinstance(identifier, str) or not PACK_ID_PATTERN.fullmatch(identifier):
            raise HarnessError(f"selected_stack_packs[{index}] has invalid id")
        if identifier in seen:
            raise HarnessError(f"duplicate selected stack pack: {identifier}")
        seen.add(identifier)
        if (
            not isinstance(item["version"], int)
            or isinstance(item["version"], bool)
            or item["version"] < 1
        ):
            raise HarnessError(f"selected stack pack {identifier} has invalid version")
        guidance = contained_path(root, item["guidance"], require_exists=True)
        if not guidance.is_file():
            raise HarnessError(f"selected stack pack {identifier} guidance is missing")
        for field in ("runtime_probe_types", "references", "conflicts"):
            if not isinstance(item[field], list) or not all(
                isinstance(entry, str) and entry for entry in item[field]
            ):
                raise HarnessError(
                    f"selected stack pack {identifier} field {field} must be a string array"
                )
        normalized.append({**item, "guidance_path": guidance})
    selected_ids = {item["id"] for item in normalized}
    for item in normalized:
        for conflict in item["conflicts"]:
            if conflict in selected_ids:
                raise HarnessError(
                    f"selected stack pack conflict: {item['id']} conflicts with {conflict}"
                )
    return normalized


def _validate_runtime_probes(value: Any, selected_ids: set[str]) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise HarnessError("runtime_probes must be an array")
    normalized = []
    seen: set[str] = set()
    for index, probe in enumerate(value):
        if not isinstance(probe, dict) or set(probe) != {
            "type",
            "stack_packs",
            "status",
        }:
            raise HarnessError(f"runtime_probes[{index}] has invalid fields")
        probe_type = probe["type"]
        owners = probe["stack_packs"]
        status = probe["status"]
        if not isinstance(probe_type, str) or not probe_type or probe_type in seen:
            raise HarnessError(f"runtime_probes[{index}] has invalid or duplicate type")
        if not isinstance(owners, list) or not owners or not all(
            isinstance(owner, str) and owner in selected_ids for owner in owners
        ):
            raise HarnessError(f"runtime probe {probe_type} has invalid stack owners")
        if status not in {"PROPOSED", "ACCEPTED", "PASS", "FAIL", "INCONCLUSIVE"}:
            raise HarnessError(f"runtime probe {probe_type} has invalid status")
        seen.add(probe_type)
        normalized.append(probe)
    return normalized


def _validate_proposed_checks(root: Path, value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise HarnessError("project configuration proposed_checks must be an array")
    seen: set[str] = set()
    for index, check in enumerate(value):
        if not isinstance(check, dict):
            raise HarnessError(f"proposed check {index} must be an object")
        unknown = set(check) - PROPOSED_CHECK_ALLOWED_FIELDS
        if unknown:
            raise HarnessError(
                f"proposed check {index} has unknown fields: {', '.join(sorted(unknown))}"
            )
        identifier = check.get("id")
        if not isinstance(identifier, str) or not identifier.strip():
            raise HarnessError(f"proposed check {index} requires a non-empty id")
        if identifier in seen:
            raise HarnessError(f"duplicate proposed check id: {identifier}")
        seen.add(identifier)
        _validate_command(check.get("command"))
        cwd = check.get("cwd", ".")
        if not isinstance(cwd, str) or not contained_path(root, cwd, require_exists=True).is_dir():
            raise HarnessError(f"proposed check {identifier} has invalid cwd")
        required = check.get("required", True)
        if not isinstance(required, bool):
            raise HarnessError(f"proposed check {identifier} required must be boolean")
        timeout = check.get("timeout_seconds", 900)
        if not isinstance(timeout, int) or isinstance(timeout, bool) or not 1 <= timeout <= MAX_TIMEOUT_SECONDS:
            raise HarnessError(f"proposed check {identifier} has invalid timeout")
        if "evidence" in check and (
            not isinstance(check["evidence"], str) or not check["evidence"]
        ):
            raise HarnessError(f"proposed check {identifier} has invalid evidence")
        if "stack_pack" in check and (
            not isinstance(check["stack_pack"], str) or not check["stack_pack"]
        ):
            raise HarnessError(f"proposed check {identifier} has invalid stack_pack")
    return value


def load_project_config(root: Path, path: Path | None = None) -> dict[str, Any]:
    config_path = path or root / ".harness/project.json"
    config_path = contained_path(root, config_path, require_exists=True)
    data = read_json(config_path)
    if not isinstance(data, dict) or data.get("schema_version") != SCHEMA_VERSION:
        raise HarnessError(f"project configuration requires schema_version {SCHEMA_VERSION}")
    missing = PROJECT_REQUIRED_FIELDS - data.keys()
    unknown = data.keys() - PROJECT_REQUIRED_FIELDS
    if missing:
        raise HarnessError(f"project configuration is missing: {', '.join(sorted(missing))}")
    if unknown:
        raise HarnessError(f"project configuration has unknown fields: {', '.join(sorted(unknown))}")
    if not isinstance(data["project_name"], str) or not data["project_name"].strip():
        raise HarnessError("project_name must be a non-empty string")
    proposed_checks = _validate_proposed_checks(root, data["proposed_checks"])

    protected_paths = _normalize_declared_paths(root, data, "protected_paths")
    generated_paths = _normalize_declared_paths(root, data, "generated_paths")
    protected_relative = {str(path.relative_to(root)) for path in protected_paths}
    protected_boundary_relative = protected_relative | {
        str(contained_path(root, value).relative_to(root))
        for value in data["protected_paths"]
    }
    generated_relative = {str(path.relative_to(root)) for path in generated_paths}
    generated_boundary_relative = generated_relative | {
        str((root / Path(value)).relative_to(root))
        for value in data["generated_paths"]
    }
    overlap = {
        (protected, generated)
        for protected in protected_boundary_relative
        for generated in generated_boundary_relative
        if Path(protected) == Path(generated)
        or Path(protected) in Path(generated).parents
        or Path(generated) in Path(protected).parents
    }
    if overlap:
        raise HarnessError(
            "protected_paths and generated_paths overlap: "
            + ", ".join(
                f"{protected} <> {generated}"
                for protected, generated in sorted(overlap)
            )
        )
    selected_stack_packs = _validate_stack_selection(
        root, data["selected_stack_packs"]
    )
    runtime_probes = _validate_runtime_probes(
        data["runtime_probes"],
        {item["id"] for item in selected_stack_packs},
    )
    checks = data.get("checks")
    if not isinstance(checks, list):
        raise HarnessError("project configuration checks must be an array")
    seen: set[str] = set()
    normalized: list[dict[str, Any]] = []
    for index, check in enumerate(checks):
        if not isinstance(check, dict):
            raise HarnessError(f"check {index} must be an object")
        unknown = set(check) - CHECK_ALLOWED_FIELDS
        if unknown:
            raise HarnessError(
                f"check {index} has unknown fields: {', '.join(sorted(unknown))}"
            )
        identifier = check.get("id")
        if not isinstance(identifier, str) or not identifier.strip():
            raise HarnessError(f"check {index} requires a non-empty id")
        if identifier in seen:
            raise HarnessError(f"duplicate check id: {identifier}")
        seen.add(identifier)
        command = _validate_command(check.get("command"))
        cwd_value = check.get("cwd", ".")
        if not isinstance(cwd_value, str):
            raise HarnessError(f"check {identifier} cwd must be a string")
        cwd = contained_path(root, cwd_value, require_exists=True)
        if not cwd.is_dir():
            raise HarnessError(f"check {identifier} cwd is not a directory")
        timeout = check.get("timeout_seconds", 900)
        if not isinstance(timeout, int) or isinstance(timeout, bool) or not 1 <= timeout <= MAX_TIMEOUT_SECONDS:
            raise HarnessError(f"check {identifier} timeout_seconds must be 1..{MAX_TIMEOUT_SECONDS}")
        required = check.get("required", True)
        if not isinstance(required, bool):
            raise HarnessError(f"check {identifier} required must be boolean")
        normalized.append(
            {
                "id": identifier,
                "command": command,
                "cwd": cwd,
                "cwd_relative": str(cwd.relative_to(root)) or ".",
                "timeout_seconds": timeout,
                "required": required,
            }
        )
    return {
        **data,
        "checks": normalized,
        "proposed_checks": proposed_checks,
        "protected_path_objects": protected_paths,
        "generated_path_objects": generated_paths,
        "selected_stack_packs": selected_stack_packs,
        "runtime_probes": runtime_probes,
        "config_path": str(config_path),
    }


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _command_evidence(command: list[str]) -> dict[str, Any]:
    serialized = json.dumps(command, ensure_ascii=False, separators=(",", ":")).encode()
    return {
        "command_executable": Path(command[0]).name,
        "command_argument_count": len(command) - 1,
        "command_argv_sha256": _digest(serialized),
    }


def _ancestor_symlink_bytes(path: Path, root: Path) -> bytes:
    state = bytearray()
    current = root
    for part in path.relative_to(root).parts[:-1]:
        current /= part
        if current.is_symlink():
            state.extend(str(current.relative_to(root)).encode())
            state.extend(b"\0")
            state.extend(os.fsencode(os.readlink(current)))
            state.extend(b"\0")
    return bytes(state)


def _stream_protected_file(
    digest: Any,
    path: Path,
    label: str,
    budget: _ProtectedSnapshotBudget,
) -> None:
    """Hash one regular file incrementally without following a final symlink."""
    try:
        metadata = os.stat(path, follow_symlinks=False)
    except OSError as exc:
        raise ProtectedSnapshotError(
            f"cannot stat protected file {label}: {type(exc).__name__}",
            budget.stats(),
        ) from exc
    if not stat.S_ISREG(metadata.st_mode):
        raise ProtectedSnapshotError(
            f"protected entry changed type while snapshotting: {label}",
            budget.stats(),
        )
    budget.preflight_file(metadata.st_size, label)
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise ProtectedSnapshotError(
            f"cannot open protected file {label}: {type(exc).__name__}",
            budget.stats(),
        ) from exc
    file_bytes = 0
    try:
        with os.fdopen(descriptor, "rb") as stream:
            descriptor = -1
            while True:
                budget.check_elapsed()
                remaining_file = MAX_PROTECTED_SNAPSHOT_FILE_BYTES - file_bytes
                remaining_total = (
                    MAX_PROTECTED_SNAPSHOT_TOTAL_BYTES - budget.bytes_hashed
                )
                read_size = min(
                    PROTECTED_SNAPSHOT_CHUNK_BYTES,
                    remaining_file + 1,
                    remaining_total + 1,
                )
                if read_size <= 0:
                    budget._limit_error(
                        f"protected snapshot byte budget exhausted at {label}"
                    )
                chunk = stream.read(read_size)
                if not chunk:
                    break
                if len(chunk) > remaining_file:
                    budget._limit_error(
                        "protected snapshot file exceeds "
                        f"{MAX_PROTECTED_SNAPSHOT_FILE_BYTES} bytes: {label}"
                    )
                if len(chunk) > remaining_total:
                    budget._limit_error(
                        "protected snapshot total file bytes exceed "
                        f"{MAX_PROTECTED_SNAPSHOT_TOTAL_BYTES}: {label}"
                    )
                digest.update(chunk)
                file_bytes += len(chunk)
                budget.bytes_hashed += len(chunk)
    except ProtectedSnapshotError:
        raise
    except OSError as exc:
        raise ProtectedSnapshotError(
            f"cannot read protected file {label}: {type(exc).__name__}",
            budget.stats(),
        ) from exc
    finally:
        if descriptor >= 0:
            os.close(descriptor)
    digest.update(b"\0file-size\0")
    digest.update(str(file_bytes).encode())
    digest.update(b"\0")
    budget.files_hashed += 1


def _scan_protected_directory(
    directory: Path,
    snapshot_root: Path,
    depth: int,
    budget: _ProtectedSnapshotBudget,
) -> list[tuple[str, Path, str, int]]:
    """Return one bounded, sorted lexical directory level without recursion."""
    records: list[tuple[str, Path, str, int]] = []
    try:
        with os.scandir(directory) as iterator:
            for entry in iterator:
                child = Path(entry.path)
                relative = child.relative_to(snapshot_root).as_posix()
                child_depth = depth + 1
                budget.add_entry(child_depth, relative)
                if entry.is_symlink():
                    kind = "symlink"
                elif entry.is_dir(follow_symlinks=False):
                    kind = "directory"
                elif entry.is_file(follow_symlinks=False):
                    kind = "file"
                else:
                    kind = "other"
                records.append((entry.name, child, kind, child_depth))
                budget.check_elapsed()
    except ProtectedSnapshotError:
        raise
    except OSError as exc:
        label = directory.relative_to(snapshot_root).as_posix() or "."
        raise ProtectedSnapshotError(
            f"cannot scan protected directory {label}: {type(exc).__name__}",
            budget.stats(),
        ) from exc
    records.sort(key=lambda item: item[0])
    return records


def _update_protected_directory_digest(
    digest: Any,
    path: Path,
    root: Path,
    budget: _ProtectedSnapshotBudget,
) -> None:
    """Hash a protected lexical tree iteratively under explicit budgets."""
    stack = list(reversed(_scan_protected_directory(path, path, 0, budget)))
    while stack:
        _, child, kind, depth = stack.pop()
        budget.check_elapsed()
        relative = child.relative_to(path).as_posix()
        digest.update(os.fsencode(relative))
        digest.update(b"\0")
        if kind == "symlink":
            digest.update(b"symlink\0")
            try:
                digest.update(os.fsencode(os.readlink(child)))
                resolved = child.resolve(strict=True)
            except OSError:
                digest.update(b"\0BROKEN\0")
                continue
            digest.update(b"\0")
            if is_within(root, resolved):
                digest.update(b"CONTAINED\0")
                digest.update(os.fsencode(resolved.relative_to(root).as_posix()))
                digest.update(b"\0")
            else:
                digest.update(b"ESCAPES\0")
        elif kind == "directory":
            digest.update(b"directory\0")
            children = _scan_protected_directory(child, path, depth, budget)
            stack.extend(reversed(children))
        elif kind == "file":
            digest.update(b"file\0")
            _stream_protected_file(digest, child, relative, budget)
        else:
            digest.update(b"other\0")


def _snapshot_path(
    path: Path,
    root: Path,
    budget: _ProtectedSnapshotBudget,
) -> str:
    budget.check_elapsed()
    ancestor_state = _ancestor_symlink_bytes(path, root)
    if not path.is_symlink():
        try:
            resolved = path.resolve(strict=False)
        except OSError:
            return _digest(b"UNRESOLVED\0" + ancestor_state)
        if not is_within(root, resolved):
            return _digest(b"ESCAPES\0" + ancestor_state)
    if not path.exists() and not path.is_symlink():
        return _digest(b"MISSING\0" + ancestor_state) if ancestor_state else "MISSING"
    if path.is_symlink():
        budget.add_entry(0, path.relative_to(root).as_posix())
        digest = hashlib.sha256()
        digest.update(ancestor_state)
        digest.update(b"symlink\0")
        try:
            digest.update(os.fsencode(os.readlink(path)))
            resolved = path.resolve(strict=True)
        except OSError:
            digest.update(b"\0BROKEN")
            return digest.hexdigest()
        digest.update(b"\0")
        if not is_within(root, resolved):
            digest.update(b"ESCAPES")
            return digest.hexdigest()
        digest.update(str(resolved.relative_to(root)).encode())
        digest.update(b"\0")
        digest.update(_snapshot_path(resolved, root, budget).encode())
        return digest.hexdigest()
    digest = hashlib.sha256()
    digest.update(ancestor_state)
    if path.is_file():
        budget.add_entry(0, path.relative_to(root).as_posix())
        digest.update(b"file\0")
        _stream_protected_file(
            digest,
            path,
            path.relative_to(root).as_posix(),
            budget,
        )
        return digest.hexdigest()
    if path.is_dir():
        budget.add_entry(0, path.relative_to(root).as_posix())
        digest.update(b"directory\0")
        _update_protected_directory_digest(digest, path, root, budget)
        return digest.hexdigest()
    return "OTHER"


def _snapshot_protected_paths(
    paths: list[Path],
    root: Path,
) -> tuple[dict[str, str], dict[str, int | float]]:
    budget = _ProtectedSnapshotBudget()
    snapshots: dict[str, str] = {}
    try:
        for path in paths:
            snapshots[str(path.relative_to(root))] = _snapshot_path(
                path, root, budget
            )
    except ProtectedSnapshotError as exc:
        if not exc.stats:
            exc.stats = budget.stats()
        raise
    return snapshots, budget.stats()


def run_validation(root: Path, config_path: Path | None = None) -> tuple[dict[str, Any], int]:
    config = load_project_config(root, config_path)
    snapshot_limits = _ProtectedSnapshotBudget.limits()
    try:
        protected_before, protected_before_stats = _snapshot_protected_paths(
            config["protected_path_objects"], root
        )
    except ProtectedSnapshotError as exc:
        report = {
            "schema_version": SCHEMA_VERSION,
            "generated_at": utc_now(),
            "project_root": str(root),
            "config_path": config["config_path"],
            "overall": "INCONCLUSIVE",
            "checks": [],
            "protected_path_changes": [],
            "protected_snapshot": {
                "status": "INCONCLUSIVE",
                "phase": "before",
                "error": str(exc),
                "limits": snapshot_limits,
                "stats": exc.stats,
            },
            "raw_output_policy": "stdout/stderr and raw argv are hashed but not persisted",
        }
        return report, 2
    results: list[dict[str, Any]] = []
    for check in config["checks"]:
        started = utc_now()
        try:
            completed = subprocess.run(
                check["command"],
                cwd=check["cwd"],
                capture_output=True,
                check=False,
                timeout=check["timeout_seconds"],
            )
            status = "PASS" if completed.returncode == 0 else "FAIL"
            result = {
                "id": check["id"],
                "status": status,
                "required": check["required"],
                "cwd": check["cwd_relative"],
                "exit_code": completed.returncode,
                "started_at": started,
                "finished_at": utc_now(),
                "stdout_bytes": len(completed.stdout),
                "stderr_bytes": len(completed.stderr),
                "stdout_sha256": _digest(completed.stdout),
                "stderr_sha256": _digest(completed.stderr),
                "output_stored": False,
                **_command_evidence(check["command"]),
            }
        except subprocess.TimeoutExpired as exc:
            stdout = exc.stdout or b""
            stderr = exc.stderr or b""
            result = {
                "id": check["id"],
                "status": "FAIL",
                "required": check["required"],
                "cwd": check["cwd_relative"],
                "exit_code": None,
                "started_at": started,
                "finished_at": utc_now(),
                "error": "timeout",
                "stdout_bytes": len(stdout),
                "stderr_bytes": len(stderr),
                "stdout_sha256": _digest(stdout),
                "stderr_sha256": _digest(stderr),
                "output_stored": False,
                **_command_evidence(check["command"]),
            }
        except OSError as exc:
            result = {
                "id": check["id"],
                "status": "FAIL",
                "required": check["required"],
                "cwd": check["cwd_relative"],
                "exit_code": None,
                "started_at": started,
                "finished_at": utc_now(),
                "error": f"process error: {exc}",
                "stdout_bytes": 0,
                "stderr_bytes": 0,
                "stdout_sha256": _digest(b""),
                "stderr_sha256": _digest(b""),
                "output_stored": False,
                **_command_evidence(check["command"]),
            }
        results.append(result)

    protected_after_stats: dict[str, int | float] = {}
    protected_snapshot_error: ProtectedSnapshotError | None = None
    try:
        protected_after, protected_after_stats = _snapshot_protected_paths(
            config["protected_path_objects"], root
        )
    except ProtectedSnapshotError as exc:
        protected_after = {}
        protected_snapshot_error = exc
    protected_path_changes = (
        []
        if protected_snapshot_error
        else sorted(
            path
            for path, before in protected_before.items()
            if protected_after[path] != before
        )
    )
    required = [item for item in results if item["required"]]
    if protected_snapshot_error:
        overall, exit_code = "FAIL", 1
    elif not required:
        overall, exit_code = "INCONCLUSIVE", 2
    elif (
        all(item["status"] == "PASS" for item in required)
        and not protected_path_changes
    ):
        overall, exit_code = "PASS", 0
    else:
        overall, exit_code = "FAIL", 1
    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": utc_now(),
        "project_root": str(root),
        "config_path": config["config_path"],
        "overall": overall,
        "checks": results,
        "protected_path_changes": protected_path_changes,
        "protected_snapshot": (
            {
                "status": "FAIL",
                "phase": "after",
                "error": str(protected_snapshot_error),
                "limits": snapshot_limits,
                "before": protected_before_stats,
                "stats": protected_snapshot_error.stats,
            }
            if protected_snapshot_error
            else {
                "status": "PASS",
                "limits": snapshot_limits,
                "before": protected_before_stats,
                "after": protected_after_stats,
            }
        ),
        "raw_output_policy": "stdout/stderr and raw argv are hashed but not persisted",
    }
    return report, exit_code


def default_validation_output(
    root: Path, config_path: Path | None = None
) -> Path:
    config = load_project_config(root, config_path)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = writable_path(
        root,
        config["generated_path_objects"][0] / timestamp / "validation.json",
    )
    if path.exists() or path.is_symlink():
        raise HarnessError(
            f"refusing to overwrite existing output: {path.relative_to(root)}"
        )
    return path


def generated_output_path(
    root: Path,
    value: str | Path,
    config_path: Path | None = None,
) -> Path:
    """Resolve a new explicit output under a configured generated path."""
    config = load_project_config(root, config_path)
    path = writable_path(root, value)
    if path.exists() or path.is_symlink():
        raise HarnessError(f"refusing to overwrite existing output: {value!s}")
    if not any(
        path == generated or is_within(generated, path)
        for generated in config["generated_path_objects"]
    ):
        raise HarnessError(
            f"output is not inside a configured generated path: {value!s}"
        )
    return path


def context_audit(root: Path) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    candidates = [
        ("AGENTS.md", 12 * 1024, 200),
        (".harness/PROJECT_CONSTITUTION.md", 8 * 1024, 150),
        (".harness/AGENTS_SNIPPET.md", 2 * 1024, 40),
    ]
    files = _relative_file_set(root)
    config_path = root / ".harness/project.json"
    if config_path.is_file():
        try:
            config = load_project_config(root, config_path)
            candidates.extend(
                (
                    str(item["guidance_path"].relative_to(root)),
                    6 * 1024,
                    120,
                )
                for item in config["selected_stack_packs"]
            )
        except HarnessError as exc:
            findings.append(
                {
                    "path": ".harness/project.json",
                    "status": "FAIL",
                    "error": str(exc),
                }
            )
    candidates.extend(
        (item, 6 * 1024, 120)
        for item in sorted(files)
        if item.startswith(".agents/skills/") and item.endswith("/SKILL.md")
    )
    candidates = list(dict.fromkeys(candidates))
    skill_names: dict[str, str] = {}
    skill_descriptions: dict[str, str] = {}
    skill_description_tokens: dict[str, set[str]] = {}
    context_bytes = 0
    for relative, byte_budget, line_budget in candidates:
        lexical_path = root / relative
        if not lexical_path.exists() and not lexical_path.is_symlink():
            continue
        try:
            path = contained_path(root, relative, require_exists=True)
        except HarnessError as exc:
            findings.append({"path": relative, "status": "FAIL", "error": str(exc)})
            continue
        if not path.is_file():
            findings.append({"path": relative, "status": "FAIL", "error": "not a regular file"})
            continue
        try:
            data = path.read_bytes()
        except OSError as exc:
            findings.append({"path": relative, "status": "FAIL", "error": str(exc)})
            continue
        context_bytes += len(data)
        if relative.startswith(".agents/skills/"):
            text = data.decode("utf-8", errors="replace")
            name_match = re.search(r"^name:\s*([a-z0-9-]+)\s*$", text, re.MULTILINE)
            description_match = re.search(
                r"^description:\s*(.+?)\s*$", text, re.MULTILINE
            )
            if not name_match or not description_match:
                findings.append(
                    {
                        "path": relative,
                        "status": "FAIL",
                        "error": "Skill frontmatter requires name and description",
                    }
                )
            else:
                name = name_match.group(1)
                description = description_match.group(1).strip().lower()
                if name in skill_names:
                    findings.append(
                        {
                            "path": relative,
                            "status": "FAIL",
                            "error": f"duplicate Skill name also used by {skill_names[name]}",
                        }
                    )
                if description in skill_descriptions:
                    findings.append(
                        {
                            "path": relative,
                            "status": "WARN",
                            "error": (
                                "duplicate Skill trigger description also used by "
                                f"{skill_descriptions[description]}"
                            ),
                        }
                    )
                skill_names[name] = relative
                skill_descriptions[description] = relative
                skill_description_tokens[relative] = set(
                    re.findall(r"[a-z0-9]+", description)
                )
        lines = data.count(b"\n") + (0 if data.endswith(b"\n") else 1)
        status = "WARN" if len(data) > byte_budget or lines > line_budget else "PASS"
        findings.append(
            {
                "path": relative,
                "status": status,
                "bytes": len(data),
                "lines": lines,
                "byte_budget": byte_budget,
                "line_budget": line_budget,
            }
        )
    skill_paths = sorted(skill_description_tokens)
    for index, left in enumerate(skill_paths):
        for right in skill_paths[index + 1 :]:
            left_tokens = skill_description_tokens[left]
            right_tokens = skill_description_tokens[right]
            union = left_tokens | right_tokens
            if min(len(left_tokens), len(right_tokens)) < 4 or not union:
                continue
            similarity = len(left_tokens & right_tokens) / len(union)
            if similarity >= 0.75:
                findings.append(
                    {
                        "path": f"{left} <> {right}",
                        "status": "WARN",
                        "error": "highly overlapping Skill trigger descriptions",
                        "jaccard_similarity": round(similarity, 3),
                    }
                )
    catalog_status = (
        "WARN"
        if len(skill_names) > 12 or context_bytes > 64 * 1024
        else "PASS"
    )
    findings.append(
        {
            "path": "context-catalog",
            "status": catalog_status,
            "skill_count": len(skill_names),
            "total_bytes": context_bytes,
            "skill_warning_threshold": 12,
            "total_byte_warning_threshold": 64 * 1024,
        }
    )
    discovery_path = root / ".harness/DISCOVERY.json"
    if discovery_path.is_file():
        try:
            discovery = read_json(discovery_path)
            conflicts = discovery.get("conflicts", []) if isinstance(discovery, dict) else []
            findings.append(
                {
                    "path": ".harness/DISCOVERY.json",
                    "status": "FAIL" if conflicts else "PASS",
                    "active_stack_conflicts": conflicts,
                }
            )
        except HarnessError as exc:
            findings.append(
                {
                    "path": ".harness/DISCOVERY.json",
                    "status": "FAIL",
                    "error": str(exc),
                }
            )
    if any(item["status"] == "FAIL" for item in findings):
        overall = "FAIL"
    elif any(item["status"] == "WARN" for item in findings):
        overall = "WARN"
    else:
        overall = "PASS"
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": utc_now(),
        "project_root": str(root),
        "overall": overall,
        "findings": findings,
        "note": "Budgets are maintainability warnings, not correctness limits.",
    }


def copy_core_skills(root: Path) -> dict[str, str]:
    source_root = runtime_asset_root() / "skills"
    if not source_root.is_dir():
        raise HarnessError("Harness skills directory is missing")
    destination_root = _safe_directory(root, ".agents/skills")
    outcomes: dict[str, str] = {}
    for skill_dir in sorted(
        path
        for path in source_root.iterdir()
        if path.is_dir() and (path / "SKILL.md").is_file()
    ):
        if skill_dir.is_symlink() or any(path.is_symlink() for path in skill_dir.rglob("*")):
            raise HarnessError(f"refusing symlink in source Skill: {skill_dir.name}")
        target_dir = contained_path(root, destination_root / skill_dir.name)
        if target_dir.exists() or target_dir.is_symlink():
            outcomes[skill_dir.name] = "preserved-existing"
            continue
        shutil.copytree(skill_dir, target_dir, symlinks=False)
        outcomes[skill_dir.name] = "created"
    return outcomes
