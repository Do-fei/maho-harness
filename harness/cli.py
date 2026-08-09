"""Command-line interface for MAHO."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from . import __version__
from .adapters import (
    AGENT_ADAPTERS,
    VERIFIED_AGENT_IDS,
    install_agent_skills,
    plan_agent_skills,
)
from .core import (
    HarnessError,
    apply_bootstrap,
    bootstrap_plan,
    contained_path,
    context_audit,
    copy_core_skills,
    default_validation_output,
    discover,
    generated_output_path,
    readiness,
    resolve_project,
    run_validation,
    write_json,
)
from .presentation import render_init_receipt


def emit(data: Any) -> None:
    print(json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="maho",
        description="MAHO — Model-Agnostic Harness for Outcomes",
    )
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    parser.add_argument(
        "--locale",
        choices=("en", "zh-CN"),
        default="en",
        help="human output and installed Skill language",
    )
    parser.add_argument("--no-color", action="store_true", help="disable ANSI color")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser(
        "init",
        help="preview or install MAHO without overwriting existing files",
    )
    init_parser.add_argument("project", nargs="?", default=".")
    init_parser.add_argument("--apply", action="store_true", help="apply the reviewed plan")
    init_parser.add_argument("--yes", action="store_true", help="confirm non-interactively")
    init_parser.add_argument(
        "--agent",
        action="append",
        choices=("all", *AGENT_ADAPTERS),
        help="target agent; repeat for more than one; all selects verified adapters only (default: codex)",
    )

    discover_parser = subparsers.add_parser("discover", help="inspect stack and validation signals")
    discover_parser.add_argument("project", nargs="?", default=".")
    discover_parser.add_argument("--output", help="write JSON inside the project")

    bootstrap_parser = subparsers.add_parser("bootstrap", help="plan or create missing Harness files")
    bootstrap_parser.add_argument("project", nargs="?", default=".")
    bootstrap_parser.add_argument("--apply", action="store_true", help="create missing files")
    bootstrap_parser.add_argument("--install-agents", action="store_true", help="create AGENTS.md only when absent")
    bootstrap_parser.add_argument("--install-skills", action="store_true", help="copy core Skills without overwriting")

    readiness_parser = subparsers.add_parser("readiness", help="audit repository agent readiness")
    readiness_parser.add_argument("project", nargs="?", default=".")
    readiness_parser.add_argument("--output", help="write JSON inside the project")

    validate_parser = subparsers.add_parser("validate", help="run accepted checks without a shell")
    validate_parser.add_argument("project", nargs="?", default=".")
    validate_parser.add_argument("--config", help="configuration path inside the project")
    validate_parser.add_argument("--output", help="result path inside the project")

    context_parser = subparsers.add_parser("context-audit", help="check always-on context budgets")
    context_parser.add_argument("project", nargs="?", default=".")
    context_parser.add_argument("--output", help="write JSON inside the project")
    return parser


def _optional_write(root: Path, output: str | None, data: Any) -> None:
    if not output:
        return
    path = generated_output_path(root, output)
    write_json(path, data)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        root = resolve_project(args.project)
        if args.command == "init":
            requested_agents = args.agent or ["codex"]
            agent_ids = (
                list(VERIFIED_AGENT_IDS)
                if "all" in requested_agents
                else requested_agents
            )
            if args.apply and not args.yes:
                if not sys.stdin.isatty():
                    raise HarnessError("--apply requires --yes in a non-interactive terminal")
                prompt = (
                    "Apply this no-overwrite plan? [y/N] "
                    if args.locale == "en"
                    else "确认应用这份零覆盖安装计划？[y/N] "
                )
                if input(prompt).strip().lower() not in {"y", "yes"}:
                    raise HarnessError("installation cancelled")
            bootstrap = (
                apply_bootstrap(root, install_agents=True, locale=args.locale)
                if args.apply
                else bootstrap_plan(root, locale=args.locale)
            )
            skills = (
                install_agent_skills(root, agent_ids, locale=args.locale)
                if args.apply
                else plan_agent_skills(root, agent_ids, locale=args.locale)
            )
            result = {
                "schema_version": 1,
                "mode": "apply" if args.apply else "dry-run",
                "project_root": str(root),
                "agents": agent_ids,
                "locale": args.locale,
                "bootstrap": bootstrap,
                "skills": skills,
                "release_tiers": skills["release_tiers"],
                "overwritten": 0,
            }
            if args.json:
                emit(result)
            else:
                print(render_init_receipt(result, locale=args.locale))
            return 0
        if args.command == "discover":
            result = discover(root)
            _optional_write(root, args.output, result)
            emit(result)
            return 0
        if args.command == "bootstrap":
            if (args.install_agents or args.install_skills) and not args.apply:
                raise HarnessError("--install-agents and --install-skills require --apply")
            result = apply_bootstrap(root, install_agents=args.install_agents) if args.apply else bootstrap_plan(root)
            if args.apply and args.install_skills:
                result["skills"] = copy_core_skills(root)
            emit(result)
            return 0
        if args.command == "readiness":
            result = readiness(root)
            _optional_write(root, args.output, result)
            emit(result)
            return 0 if result["overall"] == "READY" else 1
        if args.command == "validate":
            config_path = contained_path(root, args.config, require_exists=True) if args.config else None
            output_path = (
                generated_output_path(root, args.output, config_path)
                if args.output
                else default_validation_output(root, config_path)
            )
            result, exit_code = run_validation(root, config_path)
            write_json(output_path, result)
            result["output_path"] = str(output_path.relative_to(root))
            emit(result)
            return exit_code
        if args.command == "context-audit":
            result = context_audit(root)
            _optional_write(root, args.output, result)
            emit(result)
            return 1 if result["overall"] == "FAIL" else 0
        raise HarnessError(f"unknown command: {args.command}")
    except HarnessError as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
