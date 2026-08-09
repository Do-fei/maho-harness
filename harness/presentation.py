"""Accessible, dependency-free terminal presentation for MAHO."""

from __future__ import annotations

from typing import Any


FULL_LOGO = r"""                 |
             |\  |\
             | \ | \
             |  \|  \
             |   |   \
             |___|____\
                 |
           ______|_______
       ~~~\_____________/~~~

              M A H O
 Model-Agnostic Harness for Outcomes
          Proof before done."""

COMPACT_LOGO = r"""       |\
  MAHO |_\___
  ~~~~\_____/~~~~"""

_TEXT = {
    "en": {
        "plan": "INSTALLATION PLAN",
        "receipt": "INSTALLATION RECEIPT",
        "project": "Project",
        "agents": "Agents",
        "verified": "Verified",
        "experimental": "Experimental",
        "experimental_warning": "Warning: Experimental adapters have not passed real-client acceptance for this release.",
        "locale": "Language",
        "created": "Created",
        "preserved": "Preserved",
        "skipped": "Skipped",
        "overwritten": "Overwritten",
        "verify": "Install check",
        "dry": "No files were changed. Review the plan, then run again with --apply --yes.",
        "applied": "MAHO was installed without overwriting existing files.",
        "next": "Next",
        "next_command": "maho readiness .",
    },
    "zh-CN": {
        "plan": "安装预览",
        "receipt": "安装回执",
        "project": "项目",
        "agents": "智能体",
        "verified": "已验证",
        "experimental": "实验性",
        "experimental_warning": "注意：实验性适配器尚未通过本版本的真实客户端验收。",
        "locale": "语言",
        "created": "已创建",
        "preserved": "已保留",
        "skipped": "已跳过",
        "overwritten": "已覆盖",
        "verify": "安装检查",
        "dry": "未修改任何文件。确认预览后，使用 --apply --yes 再次运行。",
        "applied": "MAHO 已完成安装，未覆盖任何现有文件。",
        "next": "下一步",
        "next_command": "maho readiness .",
    },
}


def render_init_receipt(result: dict[str, Any], *, locale: str) -> str:
    text = _TEXT[locale]
    dry_run = result["mode"] == "dry-run"
    bootstrap = result["bootstrap"]
    skills = result["skills"]["summary"]
    if dry_run:
        created = len(bootstrap.get("would_create", [])) + skills["would_create"]
        preserved = len(bootstrap.get("would_preserve", [])) + skills["would_preserve"]
        skipped = 0
    else:
        outcomes = bootstrap.get("files", {})
        created = sum(value == "created" for value in outcomes.values()) + skills["created"]
        preserved = sum("preserved" in value for value in outcomes.values()) + skills["preserved"]
        created += int(bootstrap.get("agents") == "created")
        preserved += int("preserved" in bootstrap.get("agents", ""))
        created += sum(value == "created" for value in bootstrap.get("stack_guidance", {}).values())
        preserved += sum(
            "preserved" in value
            for value in bootstrap.get("stack_guidance", {}).values()
        )
        skipped = skills.get("skipped", 0)
    heading = text["plan"] if dry_run else text["receipt"]
    verification = "NOT RUN" if dry_run else skills.get("install_check", "WARN")
    release_tiers = result.get("release_tiers", {})
    verified = release_tiers.get("verified", result["agents"])
    experimental = release_tiers.get("experimental", [])
    lines = [
        FULL_LOGO,
        "",
        f"-- {heading} " + "-" * max(1, 55 - len(heading)),
        f"{text['project']:<18} {result['project_root']}",
        f"{text['agents']:<18} {', '.join(result['agents'])}",
        f"{text['verified']:<18} {', '.join(verified) or '-'}",
        f"{text['experimental']:<18} {', '.join(experimental) or '-'}",
        f"{text['locale']:<18} {result['locale']}",
        "",
        f"{text['created']:<18} {created}",
        f"{text['preserved']:<18} {preserved}",
        f"{text['skipped']:<18} {skipped}",
        f"{text['overwritten']:<18} 0",
        f"{text['verify']:<18} {verification}",
        "",
    ]
    if experimental:
        lines.extend([text["experimental_warning"], ""])
    lines.extend(
        [
            text["dry"] if dry_run else text["applied"],
            f"{text['next']}: {text['next_command']}",
        ]
    )
    return "\n".join(lines)
