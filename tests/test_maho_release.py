import contextlib
import io
import json
import re
import tempfile
import unittest
from pathlib import Path

from harness.adapters import (
    AGENT_ADAPTERS,
    EXPERIMENTAL_AGENT_IDS,
    VERIFIED_AGENT_IDS,
    install_agent_skills,
    plan_agent_skills,
)
from harness.cli import main
from harness.core import apply_bootstrap, load_project_config
from harness.presentation import FULL_LOGO, render_init_receipt
from harness import __version__


class MahoReleaseTests(unittest.TestCase):
    ROOT = Path(__file__).parents[1]

    def test_first_release_has_exactly_ten_named_adapters(self):
        self.assertEqual(
            {
                "claude-code",
                "codex",
                "cursor",
                "factory-droid",
                "gemini-cli",
                "github-copilot",
                "kilo-code",
                "kimi-code",
                "opencode",
                "roo-code",
            },
            set(AGENT_ADAPTERS),
        )

    def test_first_release_has_seven_verified_and_three_experimental_adapters(self):
        self.assertEqual(
            {
                "claude-code",
                "codex",
                "cursor",
                "factory-droid",
                "kilo-code",
                "kimi-code",
                "opencode",
            },
            set(VERIFIED_AGENT_IDS),
        )
        self.assertEqual(
            {"gemini-cli", "github-copilot", "roo-code"},
            set(EXPERIMENTAL_AGENT_IDS),
        )

    def test_agent_install_plan_is_dry_run_and_deduplicates_shared_root(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            result = plan_agent_skills(
                root,
                ["codex", "cursor", "kilo-code", "kimi-code"],
                locale="en",
            )

            self.assertEqual("dry-run", result["mode"])
            self.assertEqual(6, result["summary"]["would_create"])
            self.assertEqual(0, result["summary"]["would_preserve"])
            self.assertFalse((root / ".agents").exists())

    def test_agent_install_creates_chinese_skills_and_preserves_collision(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            collision = root / ".agents/skills/acceptance-contract"
            collision.mkdir(parents=True)
            marker = collision / "SKILL.md"
            marker.write_text("user-owned\n", encoding="utf-8")

            result = install_agent_skills(
                root,
                ["codex", "factory-droid", "claude-code", "roo-code"],
                locale="zh-CN",
            )

            self.assertEqual("apply", result["mode"])
            self.assertEqual("user-owned\n", marker.read_text(encoding="utf-8"))
            self.assertGreaterEqual(result["summary"]["created"], 20)
            self.assertEqual(1, result["summary"]["preserved"])
            for relative in (
                ".agents/skills/completion-evidence/SKILL.md",
                ".factory/skills/completion-evidence/SKILL.md",
                ".claude/skills/completion-evidence/SKILL.md",
                ".roo/skills/completion-evidence/SKILL.md",
            ):
                text = (root / relative).read_text(encoding="utf-8")
                self.assertIn("完成证据", text)

    def test_agent_install_warns_when_preserved_collision_is_not_a_skill(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            collision = root / ".agents/skills/completion-evidence"
            collision.mkdir(parents=True)

            result = install_agent_skills(root, ["codex"])

            item = next(
                entry
                for entry in result["items"]
                if entry["path"].endswith("completion-evidence")
            )
            self.assertEqual("preserved-existing", item["status"])
            self.assertFalse(item["usable"])
            self.assertEqual("WARN", result["summary"]["install_check"])
            self.assertEqual(1, result["summary"]["unusable"])

    def test_unknown_adapter_is_actionable_error(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "unknown agent"):
                plan_agent_skills(Path(directory).resolve(), ["imaginary-agent"])

    def test_chinese_bootstrap_produces_loadable_localized_runtime_assets(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            (root / "requirements.txt").write_text("fastapi>=0.100\n", encoding="utf-8")

            result = apply_bootstrap(root, install_agents=True, locale="zh-CN")
            config = load_project_config(root)

            self.assertEqual("apply", result["mode"])
            self.assertIn("修改本仓库前", (root / "AGENTS.md").read_text(encoding="utf-8"))
            self.assertIn("项目宪法", (root / ".harness/PROJECT_CONSTITUTION.md").read_text(encoding="utf-8"))
            self.assertTrue((root / ".harness/stack-packs/fastapi/GUIDANCE.zh-CN.md").is_file())
            self.assertEqual(
                ".harness/stack-packs/fastapi/GUIDANCE.zh-CN.md",
                next(item for item in config["selected_stack_packs"] if item["id"] == "fastapi")["guidance"],
            )

    def test_init_json_dry_run_does_not_write(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            with contextlib.redirect_stdout(io.StringIO()):
                exit_code = main(
                    [
                        "--json",
                        "--locale",
                        "en",
                        "init",
                        str(root),
                        "--agent",
                        "codex",
                    ]
                )
            self.assertEqual(0, exit_code)
            self.assertFalse((root / ".harness").exists())
            self.assertFalse((root / ".agents").exists())

    def test_init_all_selects_only_verified_adapters(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main(
                    [
                        "--json",
                        "--locale",
                        "en",
                        "init",
                        str(root),
                        "--agent",
                        "all",
                    ]
                )
            result = json.loads(stdout.getvalue())
            self.assertEqual(0, exit_code)
            self.assertEqual(list(VERIFIED_AGENT_IDS), result["agents"])
            self.assertEqual([], result["release_tiers"]["experimental"])

    def test_explicit_experimental_adapter_is_labeled_in_receipt(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main(
                    [
                        "--locale",
                        "zh-CN",
                        "init",
                        str(root),
                        "--agent",
                        "gemini-cli",
                    ]
                )
            self.assertEqual(0, exit_code)
            self.assertIn("实验性", stdout.getvalue())
            self.assertIn("尚未通过本版本的真实客户端验收", stdout.getvalue())

    def test_init_receipt_has_real_sailboat_and_explicit_zero_overwrites(self):
        receipt = render_init_receipt(
            {
                "mode": "dry-run",
                "project_root": "/tmp/example",
                "agents": ["codex"],
                "locale": "en",
                "bootstrap": {"would_create": [".harness/project.json"], "would_preserve": []},
                "skills": {"summary": {"would_create": 6, "would_preserve": 0}},
            },
            locale="en",
        )
        self.assertIn(FULL_LOGO, receipt)
        self.assertIn("Overwritten        0", receipt)
        self.assertIn("No files were changed", receipt)

    def test_public_release_manifest_is_machine_readable(self):
        manifest = self.ROOT / "release/public-manifest.json"
        data = json.loads(manifest.read_text(encoding="utf-8"))
        self.assertEqual(1, data["schema_version"])
        self.assertIn("assets", data["include_roots"])
        self.assertNotIn("reports", data["include_roots"])
        self.assertNotIn("experiments", data["include_roots"])

    def test_readmes_use_the_project_mark_without_app_or_direction_labels(self):
        banner = self.ROOT / "assets/brand/maho-readme-banner.png"
        mark = self.ROOT / "assets/brand/maho-project-mark.png"
        self.assertTrue(banner.is_file(), banner)
        self.assertTrue(mark.is_file(), mark)

        for name in ("README.md", "README.en.md", "README.zh-CN.md"):
            text = (self.ROOT / name).read_text(encoding="utf-8")
            self.assertIn("maho-readme-banner.png", text)
            self.assertIn("Future Apparatus Laboratory", text)
            self.assertNotIn("Nautical Laboratory", text)
            self.assertNotIn("航海实验室", text)
            self.assertNotIn("App Icon", text)
            self.assertNotIn("应用图标", text)

        english = (self.ROOT / "README.en.md").read_text(encoding="utf-8")
        chinese = (self.ROOT / "README.zh-CN.md").read_text(encoding="utf-8")
        trademarks = (self.ROOT / "TRADEMARKS.md").read_text(encoding="utf-8")
        trademarks_zh = (self.ROOT / "TRADEMARKS.zh-CN.md").read_text(encoding="utf-8")
        self.assertIn("original anime-style research engineer beside a sailboat", english)
        self.assertIn("原创二次元研究工程师站在帆船旁", chinese)
        self.assertIn("original artwork under `assets/brand/`", trademarks)
        self.assertIn("`assets/brand/` 下的原创插画", trademarks_zh)

    def test_public_docs_freeze_verified_and_experimental_release_scope(self):
        english_readme = (self.ROOT / "README.en.md").read_text(encoding="utf-8")
        chinese_readme = (self.ROOT / "README.zh-CN.md").read_text(encoding="utf-8")
        english_cli = (self.ROOT / "docs/en/CLI.md").read_text(encoding="utf-8")
        chinese_cli = (self.ROOT / "docs/zh-CN/CLI.md").read_text(encoding="utf-8")

        self.assertIn("all seven verified clients", english_readme)
        self.assertIn("七个已验证客户端", chinese_readme)
        self.assertIn("`--agent all` selects the seven verified clients only", english_cli)
        self.assertIn("`--agent all` 只选择七个已验证客户端", chinese_cli)

    def test_readmes_explain_governance_positioning_and_tradeoffs(self):
        overview = (self.ROOT / "README.md").read_text(encoding="utf-8")
        english = (self.ROOT / "README.en.md").read_text(encoding="utf-8")
        chinese = (self.ROOT / "README.zh-CN.md").read_text(encoding="utf-8")

        self.assertIn("Evidence-first engineering governance for coding agents", overview)
        self.assertIn("面向编程智能体的证据优先工程治理", overview)
        self.assertIn("How MAHO turns agent work into software engineering", overview)
        self.assertIn("MAHO 如何实现工程闭环", overview)
        self.assertIn("A concrete task", overview)
        self.assertIn("一个具体任务", overview)
        self.assertIn("Why teams keep MAHO in the repository", overview)
        self.assertIn("为什么 MAHO 值得留在仓库里", overview)

        for url in (
            "https://github.github.com/spec-kit/",
            "https://github.com/Fission-AI/OpenSpec",
            "https://github.com/bmad-code-org/BMAD-METHOD",
        ):
            self.assertIn(url, english)
            self.assertIn(url, chinese)

        self.assertIn("Where MAHO is weaker", english)
        self.assertIn("MAHO 当前的不足", chinese)
        self.assertIn("It is not a sandbox", english)
        self.assertIn("它不是安全沙箱", chinese)

    def test_readme_relative_links_resolve(self):
        for name in ("README.md", "README.en.md", "README.zh-CN.md"):
            text = (self.ROOT / name).read_text(encoding="utf-8")
            with self.subTest(name=name):
                for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
                    target = target.strip().split()[0].strip("<>")
                    if target.startswith(("http://", "https://", "#", "mailto:")):
                        continue
                    relative = target.split("#", 1)[0]
                    if relative:
                        self.assertTrue((self.ROOT / relative).exists(), target)

    def test_public_docs_are_ready_for_beta_publication(self):
        english_readme = (self.ROOT / "README.en.md").read_text(encoding="utf-8")
        chinese_readme = (self.ROOT / "README.zh-CN.md").read_text(encoding="utf-8")
        english_changelog = (self.ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        chinese_changelog = (self.ROOT / "CHANGELOG.zh-CN.md").read_text(encoding="utf-8")
        english_security = (self.ROOT / "SECURITY.md").read_text(encoding="utf-8")
        chinese_security = (self.ROOT / "SECURITY.zh-CN.md").read_text(encoding="utf-8")
        english_releasing = (self.ROOT / "docs/en/RELEASING.md").read_text(encoding="utf-8")
        chinese_releasing = (self.ROOT / "docs/zh-CN/RELEASING.md").read_text(encoding="utf-8")

        self.assertIn("first public Beta", english_readme)
        self.assertIn("首个公开 Beta", chinese_readme)
        self.assertNotIn("private-beta candidate", english_readme)
        self.assertNotIn("私测候选", chinese_readme)
        self.assertIn("0.1.0-beta.1 — 2026-08-14", english_changelog)
        self.assertIn("0.1.0-beta.1 — 2026-08-14", chinese_changelog)
        self.assertIn("current supported Beta line", english_security)
        self.assertIn("当前受支持的 Beta 版本线", chinese_security)
        self.assertIn("signed annotated tag", english_releasing)
        self.assertIn("带签名的附注标签", chinese_releasing)

    def test_publication_order_respects_github_visibility_boundary(self):
        english = (self.ROOT / "docs/en/RELEASING.md").read_text(encoding="utf-8")
        chinese = (self.ROOT / "docs/zh-CN/RELEASING.md").read_text(encoding="utf-8")

        self.assertIn("Keep the GitHub release as a Draft", english)
        self.assertIn("保持 GitHub Release 为 Draft", chinese)
        english_public = english.index("change repository visibility to public")
        english_reporting = english.index("enable and verify private vulnerability reporting")
        english_release = english.index("Publish and verify the GitHub prerelease")
        self.assertLess(english.index("Keep the GitHub release as a Draft"), english_public)
        self.assertLess(english_public, english_reporting)
        self.assertLess(english_reporting, english_release)

        chinese_public = chinese.index("将仓库转为公开")
        chinese_reporting = chinese.index("启用并验证私密漏洞报告")
        chinese_release = chinese.index("发布并验证 GitHub prerelease")
        self.assertLess(chinese.index("保持 GitHub Release 为 Draft"), chinese_public)
        self.assertLess(chinese_public, chinese_reporting)
        self.assertLess(chinese_reporting, chinese_release)

    def test_bilingual_public_surfaces_have_matching_pairs(self):
        root_pairs = (
            ("CHANGELOG.md", "CHANGELOG.zh-CN.md"),
            ("CONTRIBUTING.md", "CONTRIBUTING.zh-CN.md"),
            ("LICENSE", "LICENSE.zh-CN.md"),
            ("NOTICE", "NOTICE.zh-CN.md"),
            ("README.en.md", "README.zh-CN.md"),
            ("SECURITY.md", "SECURITY.zh-CN.md"),
            ("THIRD_PARTY_NOTICES.md", "THIRD_PARTY_NOTICES.zh-CN.md"),
            ("TRADEMARKS.md", "TRADEMARKS.zh-CN.md"),
        )
        for english_name, chinese_name in root_pairs:
            english = self.ROOT / english_name
            chinese = self.ROOT / chinese_name
            self.assertTrue(english.is_file(), english)
            self.assertTrue(chinese.is_file(), chinese)

        self.assertEqual(
            {path.name for path in (self.ROOT / "docs/en").glob("*.md")},
            {path.name for path in (self.ROOT / "docs/zh-CN").glob("*.md")},
        )
        self.assertEqual(
            {path.name for path in (self.ROOT / "templates").glob("*.md")},
            {path.name for path in (self.ROOT / "templates/zh-CN").glob("*.md")},
        )
        self.assertEqual(
            {path.parent.name for path in (self.ROOT / "skills").glob("*/SKILL.md")},
            {path.parent.name for path in (self.ROOT / "skills/zh-CN").glob("*/SKILL.md")},
        )
        for guidance in (self.ROOT / "stack-packs").glob("*/GUIDANCE.md"):
            self.assertTrue(guidance.with_name("GUIDANCE.zh-CN.md").is_file(), guidance)

    def test_package_and_runtime_versions_match(self):
        metadata = (self.ROOT / "pyproject.toml").read_text(encoding="utf-8")
        version_match = re.search(r'^version = "([^"]+)"$', metadata, re.MULTILINE)
        self.assertIsNotNone(version_match)
        self.assertEqual("0.1.0b1", __version__)
        self.assertEqual(__version__, version_match.group(1))
        self.assertIn("0.1.0-beta.1", (self.ROOT / "CHANGELOG.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
