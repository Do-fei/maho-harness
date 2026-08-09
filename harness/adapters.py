"""Thin, no-overwrite adapters for Agent Skills compatible clients."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any, Iterable

from .core import HarnessError, contained_path, runtime_asset_root


AGENT_ADAPTERS: dict[str, dict[str, str]] = {
    "codex": {
        "name": "Codex",
        "command": "codex",
        "skill_root": ".agents/skills",
        "release_tier": "verified",
        "evidence": "local-current-convention",
        "docs": "https://developers.openai.com/codex/skills",
    },
    "cursor": {
        "name": "Cursor",
        "command": "cursor-agent",
        "skill_root": ".agents/skills",
        "release_tier": "verified",
        "evidence": "official-docs",
        "docs": "https://cursor.com/docs/skills",
    },
    "factory-droid": {
        "name": "Factory/Droid",
        "command": "droid",
        "skill_root": ".factory/skills",
        "release_tier": "verified",
        "evidence": "official-docs",
        "docs": "https://docs.factory.ai/cli/configuration/skills",
    },
    "claude-code": {
        "name": "Claude Code",
        "command": "claude",
        "skill_root": ".claude/skills",
        "release_tier": "verified",
        "evidence": "official-docs",
        "docs": "https://code.claude.com/docs/en/skills",
    },
    "kilo-code": {
        "name": "Kilo Code",
        "command": "kilo",
        "skill_root": ".agents/skills",
        "release_tier": "verified",
        "evidence": "official-docs",
        "docs": "https://kilo.ai/docs/customize/skills",
    },
    "kimi-code": {
        "name": "Kimi Code",
        "command": "kimi",
        "skill_root": ".agents/skills",
        "release_tier": "verified",
        "evidence": "official-docs",
        "docs": "https://www.kimi.com/code/docs/en/kimi-code-cli/customization/skills.html",
    },
    "gemini-cli": {
        "name": "Gemini CLI",
        "command": "gemini",
        "skill_root": ".agents/skills",
        "release_tier": "experimental",
        "evidence": "official-docs",
        "docs": "https://geminicli.com/docs/cli/using-agent-skills/",
    },
    "opencode": {
        "name": "OpenCode",
        "command": "opencode",
        "skill_root": ".agents/skills",
        "release_tier": "verified",
        "evidence": "official-docs",
        "docs": "https://opencode.ai/docs/skills",
    },
    "roo-code": {
        "name": "Roo Code",
        "command": "roo",
        "skill_root": ".roo/skills",
        "release_tier": "experimental",
        "evidence": "archived-primary-source",
        "docs": "https://github.com/RooCodeInc/Roo-Code",
    },
    "github-copilot": {
        "name": "GitHub Copilot",
        "command": "copilot",
        "skill_root": ".agents/skills",
        "release_tier": "experimental",
        "evidence": "official-docs",
        "docs": "https://docs.github.com/en/copilot/concepts/agents/about-agent-skills",
    },
}

VERIFIED_AGENT_IDS = tuple(
    identifier
    for identifier, adapter in AGENT_ADAPTERS.items()
    if adapter["release_tier"] == "verified"
)
EXPERIMENTAL_AGENT_IDS = tuple(
    identifier
    for identifier, adapter in AGENT_ADAPTERS.items()
    if adapter["release_tier"] == "experimental"
)
SUPPORTED_LOCALES = {"en", "zh-CN"}


def agent_release_tiers(agent_ids: Iterable[str]) -> dict[str, list[str]]:
    identifiers = normalize_agent_ids(agent_ids)
    return {
        "verified": [
            identifier
            for identifier in identifiers
            if AGENT_ADAPTERS[identifier]["release_tier"] == "verified"
        ],
        "experimental": [
            identifier
            for identifier in identifiers
            if AGENT_ADAPTERS[identifier]["release_tier"] == "experimental"
        ],
    }


def normalize_agent_ids(agent_ids: Iterable[str]) -> list[str]:
    identifiers = list(dict.fromkeys(agent_ids))
    unknown = sorted(set(identifiers) - set(AGENT_ADAPTERS))
    if unknown:
        raise HarnessError(
            "unknown agent(s): "
            + ", ".join(unknown)
            + "; choose from "
            + ", ".join(AGENT_ADAPTERS)
        )
    if not identifiers:
        raise HarnessError("at least one agent is required")
    return identifiers


def _skill_source_root(locale: str) -> Path:
    if locale not in SUPPORTED_LOCALES:
        raise HarnessError(f"unsupported locale: {locale}")
    root = runtime_asset_root() / "skills"
    return root if locale == "en" else root / "zh-CN"


def _skill_sources(locale: str) -> list[Path]:
    source_root = _skill_source_root(locale)
    if not source_root.is_dir():
        raise HarnessError(f"MAHO {locale} skill catalog is missing")
    sources = sorted(
        path
        for path in source_root.iterdir()
        if path.is_dir() and (path / "SKILL.md").is_file()
    )
    if not sources:
        raise HarnessError(f"MAHO {locale} skill catalog is empty")
    for source in sources:
        if source.is_symlink() or any(item.is_symlink() for item in source.rglob("*")):
            raise HarnessError(f"refusing symlink in source Skill: {source.name}")
    return sources


def _target_records(
    root: Path,
    agent_ids: Iterable[str],
    locale: str,
) -> list[dict[str, Any]]:
    identifiers = normalize_agent_ids(agent_ids)
    sources = _skill_sources(locale)
    records: dict[str, dict[str, Any]] = {}
    for identifier in identifiers:
        adapter = AGENT_ADAPTERS[identifier]
        skill_root = adapter["skill_root"]
        for source in sources:
            relative = f"{skill_root}/{source.name}"
            record = records.setdefault(
                relative,
                {
                    "path": relative,
                    "source": source,
                    "agents": [],
                },
            )
            record["agents"].append(identifier)
    return [records[key] for key in sorted(records)]


def plan_agent_skills(
    root: Path,
    agent_ids: Iterable[str],
    *,
    locale: str = "en",
) -> dict[str, Any]:
    identifiers = normalize_agent_ids(agent_ids)
    records = _target_records(root, identifiers, locale)
    items = []
    for record in records:
        lexical = root / record["path"]
        status = "would-preserve" if lexical.exists() or lexical.is_symlink() else "would-create"
        items.append(
            {
                "path": record["path"],
                "agents": record["agents"],
                "status": status,
            }
        )
    return {
        "mode": "dry-run",
        "locale": locale,
        "agents": identifiers,
        "release_tiers": agent_release_tiers(identifiers),
        "items": items,
        "summary": {
            "would_create": sum(item["status"] == "would-create" for item in items),
            "would_preserve": sum(item["status"] == "would-preserve" for item in items),
            "overwritten": 0,
        },
    }


def _ensure_safe_parent(root: Path, relative: str) -> Path:
    lexical = root / relative
    current = root
    for part in Path(relative).parts[:-1]:
        current = current / part
        if current.is_symlink():
            raise HarnessError(f"refusing install through symlinked directory: {current.relative_to(root)}")
    parent = lexical.parent
    parent.mkdir(parents=True, exist_ok=True)
    contained_path(root, parent, require_exists=True)
    return lexical


def install_agent_skills(
    root: Path,
    agent_ids: Iterable[str],
    *,
    locale: str = "en",
) -> dict[str, Any]:
    identifiers = normalize_agent_ids(agent_ids)
    records = _target_records(root, identifiers, locale)
    items = []
    for record in records:
        target = _ensure_safe_parent(root, record["path"])
        if target.exists() or target.is_symlink():
            status = "preserved-existing"
        else:
            try:
                shutil.copytree(record["source"], target, symlinks=False)
                status = "created"
            except FileExistsError:
                status = "preserved-existing"
        skill_file = target / "SKILL.md"
        usable = (
            target.is_dir()
            and not target.is_symlink()
            and skill_file.is_file()
            and not skill_file.is_symlink()
        )
        items.append(
            {
                "path": record["path"],
                "agents": record["agents"],
                "status": status,
                "usable": usable,
            }
        )
    unusable = sum(not item["usable"] for item in items)
    return {
        "mode": "apply",
        "locale": locale,
        "agents": identifiers,
        "release_tiers": agent_release_tiers(identifiers),
        "items": items,
        "summary": {
            "created": sum(item["status"] == "created" for item in items),
            "preserved": sum(item["status"] == "preserved-existing" for item in items),
            "skipped": 0,
            "overwritten": 0,
            "unusable": unusable,
            "install_check": "PASS" if unusable == 0 else "WARN",
        },
    }
