import json
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from harness.cli import main as cli_main
from harness.core import (
    HarnessError,
    apply_bootstrap,
    bootstrap_plan,
    contained_path,
    context_audit,
    copy_core_skills,
    discover,
    load_project_config,
    load_stack_packs,
    readiness,
    resolve_project,
    run_validation,
)


class HarnessCoreTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name).resolve()

    def tearDown(self):
        self.temporary.cleanup()

    def write_json(self, relative, data):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data), encoding="utf-8")
        return path

    def write_config(self, checks):
        return self.write_json(
            ".harness/project.json",
            {
                "schema_version": 1,
                "project_name": "fixture",
                "checks": checks,
                "proposed_checks": [],
                "protected_paths": ["AGENTS.md"],
                "generated_paths": [".harness/runs"],
                "runtime_probes": [],
                "selected_stack_packs": [],
            },
        )

    def init_git(self):
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)

    def assert_validation_schema_surface(self, report):
        schema = json.loads(
            (Path(__file__).parents[1] / "schemas/validation.schema.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertTrue(set(schema["required"]) <= set(report))
        self.assertTrue(set(report) <= set(schema["properties"]))
        snapshot_schema = schema["properties"]["protected_snapshot"]
        self.assertTrue(set(snapshot_schema["required"]) <= set(report["protected_snapshot"]))
        self.assertTrue(
            set(report["protected_snapshot"]) <= set(snapshot_schema["properties"])
        )

    def test_resolve_project_requires_directory(self):
        file_path = self.root / "file.txt"
        file_path.write_text("x", encoding="utf-8")
        with self.assertRaises(HarnessError):
            resolve_project(file_path)

    def test_contained_path_rejects_escape(self):
        with self.assertRaisesRegex(HarnessError, "escapes project root"):
            contained_path(self.root, "../outside.json")

    def test_discovery_detects_node_next_and_electron(self):
        self.write_json(
            "package.json",
            {
                "scripts": {"test": "node --test", "build": "next build"},
                "dependencies": {"next": "1.0.0"},
                "devDependencies": {"electron": "1.0.0"},
            },
        )
        (self.root / "pnpm-lock.yaml").write_text("lockfileVersion: 9", encoding="utf-8")
        (self.root / "tsconfig.json").write_text("{}", encoding="utf-8")
        result = discover(self.root)
        self.assertEqual(
            ["electron", "nextjs", "node-typescript"],
            [item["id"] for item in result["stacks"]],
        )
        commands = {item["id"]: item["command"] for item in result["proposed_checks"]}
        self.assertEqual(["pnpm", "run", "test"], commands["test"])
        self.assertEqual(["pnpm", "run", "build"], commands["build"])

    def test_discovery_detects_python_and_fastapi(self):
        (self.root / "pyproject.toml").write_text(
            '[project]\ndependencies = ["fastapi"]\n', encoding="utf-8"
        )
        tests = self.root / "tests"
        tests.mkdir()
        (tests / "test_api.py").write_text("", encoding="utf-8")
        result = discover(self.root)
        self.assertEqual(["fastapi", "python"], [item["id"] for item in result["stacks"]])
        self.assertEqual(
            ["python3", "-m", "unittest", "discover", "-s", "tests"],
            result["proposed_checks"][0]["command"],
        )

    def test_discovery_does_not_read_package_symlink_outside_project(self):
        outside = self.root.parent / f"{self.root.name}-package.json"
        outside.write_text('{"dependencies":{"next":"1"}}', encoding="utf-8")
        try:
            (self.root / "package.json").symlink_to(outside)
            result = discover(self.root)
            self.assertEqual([], result["stacks"])
            self.assertTrue(any("escapes project root" in item for item in result["warnings"]))
        finally:
            (self.root / "package.json").unlink()
            outside.unlink()

    def test_bootstrap_dry_run_writes_nothing(self):
        plan = bootstrap_plan(self.root)
        self.assertEqual("dry-run", plan["mode"])
        self.assertFalse((self.root / ".harness").exists())

    def test_bootstrap_preserves_existing_agents(self):
        agents = self.root / "AGENTS.md"
        agents.write_text("user-owned\n", encoding="utf-8")
        result = apply_bootstrap(self.root, install_agents=True)
        self.assertEqual("preserved-existing", result["agents"])
        self.assertEqual("user-owned\n", agents.read_text(encoding="utf-8"))
        self.assertTrue((self.root / ".harness/project.json").is_file())
        second = apply_bootstrap(self.root, install_agents=True)
        self.assertTrue(all(value == "preserved" for value in second["files"].values()))

    def test_bootstrap_can_explicitly_create_agents_when_absent(self):
        result = apply_bootstrap(self.root, install_agents=True)
        self.assertEqual("created", result["agents"])
        self.assertIn("PROJECT_CONSTITUTION", (self.root / "AGENTS.md").read_text(encoding="utf-8"))

    def test_bootstrap_copies_only_matched_stack_guidance(self):
        self.write_json(
            "package.json",
            {
                "dependencies": {"next": "1", "react": "1"},
                "scripts": {"test": "node --test"},
            },
        )
        result = apply_bootstrap(self.root, install_agents=True)
        self.assertEqual(
            {"nextjs", "node-typescript", "react"},
            set(result["stack_guidance"]),
        )
        self.assertTrue(
            (self.root / ".harness/stack-packs/react/GUIDANCE.md").is_file()
        )
        self.assertFalse(
            (self.root / ".harness/stack-packs/electron/GUIDANCE.md").exists()
        )
        constitution = (
            self.root / ".harness/PROJECT_CONSTITUTION.md"
        ).read_text(encoding="utf-8")
        self.assertIn("stack-packs/react/GUIDANCE.md", constitution)
        self.assertNotIn("TODO", constitution)

    def test_bootstrap_stores_post_configuration_readiness(self):
        apply_bootstrap(self.root, install_agents=True)
        stored = json.loads(
            (self.root / ".harness/READINESS.json").read_text(encoding="utf-8")
        )
        statuses = {item["id"]: item["status"] for item in stored["findings"]}
        self.assertEqual("PASS", statuses["configuration"])
        self.assertEqual("FAIL", statuses["validation-path"])

    def test_bootstrap_rejects_harness_symlink_outside_project(self):
        outside = self.root.parent / f"{self.root.name}-outside"
        outside.mkdir()
        try:
            (self.root / ".harness").symlink_to(outside, target_is_directory=True)
            with self.assertRaisesRegex(HarnessError, "escapes project root"):
                apply_bootstrap(self.root)
        finally:
            if (self.root / ".harness").is_symlink():
                (self.root / ".harness").unlink()
            outside.rmdir()

    def test_bootstrap_rejects_non_file_collision(self):
        collision = self.root / ".harness/project.json"
        collision.mkdir(parents=True)
        with self.assertRaisesRegex(HarnessError, "non-file collision"):
            apply_bootstrap(self.root)

    def test_skill_install_preserves_existing_skill(self):
        skill = self.root / ".agents/skills/harness-discovery/SKILL.md"
        skill.parent.mkdir(parents=True)
        skill.write_text("user-owned", encoding="utf-8")
        result = copy_core_skills(self.root)
        self.assertEqual("preserved-existing", result["harness-discovery"])
        self.assertEqual("user-owned", skill.read_text(encoding="utf-8"))
        self.assertEqual("created", result["acceptance-contract"])
        self.assertNotIn("zh-CN", result)
        self.assertFalse((self.root / ".agents/skills/zh-CN").exists())

    def test_config_rejects_cwd_escape(self):
        self.write_config(
            [{"id": "bad", "command": [sys.executable, "--version"], "cwd": ".."}]
        )
        with self.assertRaisesRegex(HarnessError, "escapes project root"):
            load_project_config(self.root)

    def test_config_rejects_shell_code(self):
        self.write_config([{"id": "bad", "command": ["sh", "-c", "true"]}])
        with self.assertRaisesRegex(HarnessError, "shell code flags are prohibited"):
            load_project_config(self.root)

    def test_config_rejects_secret_bearing_argument(self):
        self.write_config(
            [
                {
                    "id": "bad",
                    "command": ["tool", "--api-key", "dummy-value"],
                }
            ]
        )
        with self.assertRaisesRegex(HarnessError, "secret-bearing command arguments"):
            load_project_config(self.root)

    def test_config_rejects_duplicate_ids(self):
        self.write_config(
            [
                {"id": "same", "command": [sys.executable, "--version"]},
                {"id": "same", "command": [sys.executable, "--version"]},
            ]
        )
        with self.assertRaisesRegex(HarnessError, "duplicate check id"):
            load_project_config(self.root)

    def test_config_rejects_unknown_nested_check_field(self):
        self.write_config(
            [
                {
                    "id": "bad",
                    "command": [sys.executable, "--version"],
                    "unexpected": True,
                }
            ]
        )
        with self.assertRaisesRegex(HarnessError, "unknown fields"):
            load_project_config(self.root)

    def test_config_rejects_unknown_nested_proposed_check_field(self):
        path = self.write_config([])
        config = json.loads(path.read_text(encoding="utf-8"))
        config["proposed_checks"] = [
            {
                "id": "bad-proposal",
                "command": [sys.executable, "--version"],
                "cwd": ".",
                "required": True,
                "timeout_seconds": 10,
                "unexpected": True,
            }
        ]
        path.write_text(json.dumps(config), encoding="utf-8")
        with self.assertRaisesRegex(HarnessError, "unknown fields"):
            load_project_config(self.root)

    def test_config_rejects_ancestor_overlap_between_boundaries(self):
        path = self.write_config([])
        config = json.loads(path.read_text(encoding="utf-8"))
        config["protected_paths"] = [".harness"]
        config["generated_paths"] = [".harness/runs"]
        path.write_text(json.dumps(config), encoding="utf-8")
        with self.assertRaisesRegex(HarnessError, "overlap"):
            load_project_config(self.root)

    def test_config_rejects_protected_path_with_symlinked_parent(self):
        alternate = self.root / "alternate"
        alternate.mkdir()
        (alternate / "guide.md").write_text("same\n", encoding="utf-8")
        (self.root / "docs").symlink_to(alternate, target_is_directory=True)
        path = self.write_config([])
        config = json.loads(path.read_text(encoding="utf-8"))
        config["protected_paths"] = ["docs/guide.md"]
        path.write_text(json.dumps(config), encoding="utf-8")

        with self.assertRaisesRegex(HarnessError, "symlinked parent"):
            load_project_config(self.root)

    def test_selected_stack_pack_version_constraint_matches_schema(self):
        schema = json.loads(
            (Path(__file__).parents[1] / "schemas/project.schema.json").read_text(
                encoding="utf-8"
            )
        )
        minimum = schema["properties"]["selected_stack_packs"]["items"][
            "properties"
        ]["version"]["minimum"]
        self.assertEqual(1, minimum)
        guidance = self.root / ".harness/stack-packs/demo/GUIDANCE.md"
        guidance.parent.mkdir(parents=True)
        guidance.write_text("# Demo\n", encoding="utf-8")
        path = self.write_config([])
        config = json.loads(path.read_text(encoding="utf-8"))
        config["selected_stack_packs"] = [
            {
                "id": "demo",
                "version": minimum - 1,
                "guidance": ".harness/stack-packs/demo/GUIDANCE.md",
                "runtime_probe_types": [],
                "references": [],
                "conflicts": [],
            }
        ]
        path.write_text(json.dumps(config), encoding="utf-8")

        with self.assertRaisesRegex(HarnessError, "invalid version"):
            load_project_config(self.root)

    def test_validation_passes_required_direct_command(self):
        self.write_config(
            [
                {
                    "id": "pass",
                    "command": [sys.executable, "-c", "print('not persisted')"],
                    "required": True,
                }
            ]
        )
        report, exit_code = run_validation(self.root)
        self.assertEqual(0, exit_code)
        self.assertEqual("PASS", report["overall"])
        self.assertFalse(report["checks"][0]["output_stored"])
        self.assertNotIn("stdout", report["checks"][0])
        self.assertNotIn("stderr", report["checks"][0])
        self.assertNotIn("command", report["checks"][0])
        self.assertIn("command_argv_sha256", report["checks"][0])
        self.assert_validation_schema_surface(report)

    def test_validation_fails_required_and_ignores_optional_for_overall(self):
        self.write_config(
            [
                {
                    "id": "required",
                    "command": [sys.executable, "-c", "raise SystemExit(4)"],
                    "required": True,
                },
                {
                    "id": "optional",
                    "command": [sys.executable, "-c", "raise SystemExit(3)"],
                    "required": False,
                },
            ]
        )
        report, exit_code = run_validation(self.root)
        self.assertEqual(1, exit_code)
        self.assertEqual("FAIL", report["overall"])

    def test_validation_without_required_check_is_inconclusive(self):
        self.write_config(
            [
                {
                    "id": "optional",
                    "command": [sys.executable, "-c", "raise SystemExit(0)"],
                    "required": False,
                }
            ]
        )
        report, exit_code = run_validation(self.root)
        self.assertEqual(2, exit_code)
        self.assertEqual("INCONCLUSIVE", report["overall"])

    def test_validation_fails_when_command_changes_protected_path(self):
        agents = self.root / "AGENTS.md"
        agents.write_text("protected\n", encoding="utf-8")
        self.write_config(
            [
                {
                    "id": "mutates-guidance",
                    "command": [
                        sys.executable,
                        "-c",
                        "from pathlib import Path; Path('AGENTS.md').write_text('changed')",
                    ],
                    "required": True,
                }
            ]
        )
        report, exit_code = run_validation(self.root)
        self.assertEqual(1, exit_code)
        self.assertEqual("FAIL", report["overall"])
        self.assertEqual(["AGENTS.md"], report["protected_path_changes"])

    def test_validation_detects_protected_symlink_retarget_with_same_content(self):
        first = self.root / "guidance-a.md"
        second = self.root / "guidance-b.md"
        first.write_text("same\n", encoding="utf-8")
        second.write_text("same\n", encoding="utf-8")
        protected = self.root / "AGENTS.md"
        protected.symlink_to(first)
        self.write_config(
            [
                {
                    "id": "retarget",
                    "command": [
                        sys.executable,
                        "-c",
                        "from pathlib import Path; p=Path('AGENTS.md'); p.unlink(); p.symlink_to('guidance-b.md')",
                    ],
                    "required": True,
                }
            ]
        )

        report, exit_code = run_validation(self.root)

        self.assertEqual(1, exit_code)
        self.assertEqual("FAIL", report["overall"])
        self.assertEqual(["AGENTS.md"], report["protected_path_changes"])

    def test_validation_detects_new_symlink_in_protected_path_parent(self):
        docs = self.root / "docs"
        alternate = self.root / "alternate"
        docs.mkdir()
        alternate.mkdir()
        (docs / "guide.md").write_text("same\n", encoding="utf-8")
        (alternate / "guide.md").write_text("same\n", encoding="utf-8")
        path = self.write_config(
            [
                {
                    "id": "replace-parent",
                    "command": [
                        sys.executable,
                        "-c",
                        "from pathlib import Path; p=Path('docs'); p.rename('docs-old'); p.symlink_to('alternate', target_is_directory=True)",
                    ],
                    "required": True,
                }
            ]
        )
        config = json.loads(path.read_text(encoding="utf-8"))
        config["protected_paths"] = ["docs/guide.md"]
        path.write_text(json.dumps(config), encoding="utf-8")

        report, exit_code = run_validation(self.root)

        self.assertEqual(1, exit_code)
        self.assertEqual("FAIL", report["overall"])
        self.assertEqual(["docs/guide.md"], report["protected_path_changes"])

    def test_validation_detects_protected_parent_retarget_outside_project(self):
        docs = self.root / "docs"
        docs.mkdir()
        (docs / "guide.md").write_text("inside\n", encoding="utf-8")
        with tempfile.TemporaryDirectory() as outside_directory:
            outside = Path(outside_directory).resolve()
            (outside / "guide.md").write_text("outside secret\n", encoding="utf-8")
            path = self.write_config(
                [
                    {
                        "id": "escape-parent",
                        "command": [
                            sys.executable,
                            "-c",
                            (
                                "from pathlib import Path; p=Path('docs'); "
                                "p.rename('docs-old'); "
                                f"p.symlink_to({str(outside)!r}, target_is_directory=True)"
                            ),
                        ],
                        "required": True,
                    }
                ]
            )
            config = json.loads(path.read_text(encoding="utf-8"))
            config["protected_paths"] = ["docs/guide.md"]
            path.write_text(json.dumps(config), encoding="utf-8")

            report, exit_code = run_validation(self.root)

        self.assertEqual(1, exit_code)
        self.assertEqual("FAIL", report["overall"])
        self.assertEqual(["docs/guide.md"], report["protected_path_changes"])

    def test_validation_detects_nested_directory_symlink_retarget(self):
        protected = self.root / "protected"
        first = self.root / "target-a"
        second = self.root / "target-b"
        protected.mkdir()
        first.mkdir()
        second.mkdir()
        (first / "same.txt").write_text("same\n", encoding="utf-8")
        (second / "same.txt").write_text("same\n", encoding="utf-8")
        (protected / "linkdir").symlink_to("../target-a", target_is_directory=True)
        path = self.write_config(
            [
                {
                    "id": "retarget-child",
                    "command": [
                        sys.executable,
                        "-c",
                        (
                            "from pathlib import Path; p=Path('protected/linkdir'); "
                            "p.unlink(); p.symlink_to('../target-b', target_is_directory=True)"
                        ),
                    ],
                    "required": True,
                }
            ]
        )
        config = json.loads(path.read_text(encoding="utf-8"))
        config["protected_paths"] = ["protected"]
        path.write_text(json.dumps(config), encoding="utf-8")

        report, exit_code = run_validation(self.root)

        self.assertEqual(1, exit_code)
        self.assertEqual("FAIL", report["overall"])
        self.assertEqual(["protected"], report["protected_path_changes"])

    def test_validation_detects_nested_directory_symlink_escape_without_reading_outside(self):
        protected = self.root / "protected"
        inside = self.root / "target-a"
        protected.mkdir()
        inside.mkdir()
        (inside / "same.txt").write_text("inside\n", encoding="utf-8")
        (protected / "linkdir").symlink_to("../target-a", target_is_directory=True)
        with tempfile.TemporaryDirectory() as outside_directory:
            outside = Path(outside_directory).resolve()
            outside_file = outside / "secret.txt"
            outside_file.write_text("must not be read\n", encoding="utf-8")
            path = self.write_config(
                [
                    {
                        "id": "escape-child",
                        "command": [
                            sys.executable,
                            "-c",
                            (
                                "from pathlib import Path; p=Path('protected/linkdir'); "
                                "p.unlink(); "
                                f"p.symlink_to({str(outside)!r}, target_is_directory=True)"
                            ),
                        ],
                        "required": True,
                    }
                ]
            )
            config = json.loads(path.read_text(encoding="utf-8"))
            config["protected_paths"] = ["protected"]
            path.write_text(json.dumps(config), encoding="utf-8")
            original_read_bytes = Path.read_bytes

            def guarded_read_bytes(candidate):
                if candidate == outside_file:
                    raise AssertionError("outside target content was read")
                return original_read_bytes(candidate)

            with patch.object(Path, "read_bytes", guarded_read_bytes):
                report, exit_code = run_validation(self.root)

        self.assertEqual(1, exit_code)
        self.assertEqual("FAIL", report["overall"])
        self.assertEqual(["protected"], report["protected_path_changes"])

    def test_validation_detects_created_empty_protected_directory(self):
        protected = self.root / "protected"
        protected.mkdir()
        path = self.write_config(
            [
                {
                    "id": "create-empty-directory",
                    "command": [
                        sys.executable,
                        "-c",
                        "from pathlib import Path; Path('protected/empty').mkdir()",
                    ],
                    "required": True,
                }
            ]
        )
        config = json.loads(path.read_text(encoding="utf-8"))
        config["protected_paths"] = ["protected"]
        path.write_text(json.dumps(config), encoding="utf-8")

        report, exit_code = run_validation(self.root)

        self.assertEqual(1, exit_code)
        self.assertEqual("FAIL", report["overall"])
        self.assertEqual(["protected"], report["protected_path_changes"])

    def test_validation_detects_removed_empty_protected_directory(self):
        protected = self.root / "protected"
        empty = protected / "empty"
        empty.mkdir(parents=True)
        path = self.write_config(
            [
                {
                    "id": "remove-empty-directory",
                    "command": [
                        sys.executable,
                        "-c",
                        "from pathlib import Path; Path('protected/empty').rmdir()",
                    ],
                    "required": True,
                }
            ]
        )
        config = json.loads(path.read_text(encoding="utf-8"))
        config["protected_paths"] = ["protected"]
        path.write_text(json.dumps(config), encoding="utf-8")

        report, exit_code = run_validation(self.root)

        self.assertEqual(1, exit_code)
        self.assertEqual("FAIL", report["overall"])
        self.assertEqual(["protected"], report["protected_path_changes"])

    def test_protected_file_snapshot_streams_in_bounded_chunks(self):
        protected = self.root / "protected.bin"
        protected.write_bytes(b"abcdefgh")
        path = self.write_config(
            [
                {
                    "id": "pass",
                    "command": [sys.executable, "-c", "raise SystemExit(0)"],
                    "required": True,
                }
            ]
        )
        config = json.loads(path.read_text(encoding="utf-8"))
        config["protected_paths"] = ["protected.bin"]
        path.write_text(json.dumps(config), encoding="utf-8")
        original_read_bytes = Path.read_bytes

        def guarded_read_bytes(candidate):
            if candidate == protected:
                raise AssertionError("protected file was read into one Path buffer")
            return original_read_bytes(candidate)

        with patch.object(Path, "read_bytes", guarded_read_bytes), patch(
            "harness.core.PROTECTED_SNAPSHOT_CHUNK_BYTES", 3
        ):
            report, exit_code = run_validation(self.root)

        self.assertEqual(0, exit_code)
        self.assertEqual("PASS", report["overall"])
        self.assertEqual(8, report["protected_snapshot"]["before"]["bytes_hashed"])
        self.assertEqual(8, report["protected_snapshot"]["after"]["bytes_hashed"])

    def test_protected_snapshot_entry_budget_stops_before_checks(self):
        protected = self.root / "protected"
        protected.mkdir()
        (protected / "one.txt").write_text("one\n", encoding="utf-8")
        marker = self.root / "command-ran"
        path = self.write_config(
            [
                {
                    "id": "must-not-run",
                    "command": [
                        sys.executable,
                        "-c",
                        "from pathlib import Path; Path('command-ran').write_text('ran')",
                    ],
                    "required": True,
                }
            ]
        )
        config = json.loads(path.read_text(encoding="utf-8"))
        config["protected_paths"] = ["protected"]
        path.write_text(json.dumps(config), encoding="utf-8")

        with patch("harness.core.MAX_PROTECTED_SNAPSHOT_ENTRIES", 1):
            report, exit_code = run_validation(self.root)

        self.assertEqual(2, exit_code)
        self.assertEqual("INCONCLUSIVE", report["overall"])
        self.assertEqual([], report["checks"])
        self.assertEqual("before", report["protected_snapshot"]["phase"])
        self.assertFalse(marker.exists())
        self.assert_validation_schema_surface(report)

    def test_protected_snapshot_post_run_budget_failure_fails_closed(self):
        protected = self.root / "protected"
        protected.mkdir()
        path = self.write_config(
            [
                {
                    "id": "create-entry",
                    "command": [
                        sys.executable,
                        "-c",
                        "from pathlib import Path; Path('protected/new.txt').write_text('new')",
                    ],
                    "required": True,
                }
            ]
        )
        config = json.loads(path.read_text(encoding="utf-8"))
        config["protected_paths"] = ["protected"]
        path.write_text(json.dumps(config), encoding="utf-8")

        with patch("harness.core.MAX_PROTECTED_SNAPSHOT_ENTRIES", 1):
            report, exit_code = run_validation(self.root)

        self.assertEqual(1, exit_code)
        self.assertEqual("FAIL", report["overall"])
        self.assertEqual("PASS", report["checks"][0]["status"])
        self.assertEqual("after", report["protected_snapshot"]["phase"])
        self.assert_validation_schema_surface(report)

    def test_protected_snapshot_depth_budget_is_iterative_and_explicit(self):
        protected = self.root / "protected"
        (protected / "one" / "two").mkdir(parents=True)
        path = self.write_config([])
        config = json.loads(path.read_text(encoding="utf-8"))
        config["protected_paths"] = ["protected"]
        path.write_text(json.dumps(config), encoding="utf-8")

        with patch("harness.core.MAX_PROTECTED_SNAPSHOT_DEPTH", 1):
            report, exit_code = run_validation(self.root)

        self.assertEqual(2, exit_code)
        self.assertEqual("INCONCLUSIVE", report["overall"])
        self.assertIn("depth exceeds", report["protected_snapshot"]["error"])

    def test_protected_snapshot_per_file_budget_is_explicit(self):
        protected = self.root / "protected.bin"
        protected.write_bytes(b"four")
        path = self.write_config([])
        config = json.loads(path.read_text(encoding="utf-8"))
        config["protected_paths"] = ["protected.bin"]
        path.write_text(json.dumps(config), encoding="utf-8")

        with patch("harness.core.MAX_PROTECTED_SNAPSHOT_FILE_BYTES", 3):
            report, exit_code = run_validation(self.root)

        self.assertEqual(2, exit_code)
        self.assertEqual("INCONCLUSIVE", report["overall"])
        self.assertIn("file exceeds", report["protected_snapshot"]["error"])

    def test_protected_snapshot_total_byte_budget_is_shared(self):
        protected = self.root / "protected"
        protected.mkdir()
        (protected / "one.bin").write_bytes(b"one")
        (protected / "two.bin").write_bytes(b"two")
        path = self.write_config([])
        config = json.loads(path.read_text(encoding="utf-8"))
        config["protected_paths"] = ["protected"]
        path.write_text(json.dumps(config), encoding="utf-8")

        with patch("harness.core.MAX_PROTECTED_SNAPSHOT_TOTAL_BYTES", 5):
            report, exit_code = run_validation(self.root)

        self.assertEqual(2, exit_code)
        self.assertEqual("INCONCLUSIVE", report["overall"])
        self.assertIn("total file bytes", report["protected_snapshot"]["error"])

    def test_protected_snapshot_elapsed_budget_is_explicit(self):
        (self.root / "AGENTS.md").write_text("protected\n", encoding="utf-8")
        self.write_config([])

        with patch("harness.core.MAX_PROTECTED_SNAPSHOT_SECONDS", -1.0):
            report, exit_code = run_validation(self.root)

        self.assertEqual(2, exit_code)
        self.assertEqual("INCONCLUSIVE", report["overall"])
        self.assertIn("time budget", report["protected_snapshot"]["error"])

    def test_readiness_has_no_vendor_score_and_requires_checks(self):
        self.init_git()
        apply_bootstrap(self.root, install_agents=True)
        initial = readiness(self.root)
        self.assertEqual("NEEDS_ATTENTION", initial["overall"])
        self.assertNotIn("score", initial)
        config = json.loads((self.root / ".harness/project.json").read_text(encoding="utf-8"))
        config["checks"] = [
            {
                "id": "undocumented-version-check",
                "command": [sys.executable, "--version"],
                "required": True,
            }
        ]
        (self.root / "README.md").write_text(
            "prefixundocumented-version-checksuffix\n", encoding="utf-8"
        )
        (self.root / ".harness/project.json").write_text(json.dumps(config), encoding="utf-8")
        accepted = readiness(self.root)
        statuses = {item["id"]: item["status"] for item in accepted["findings"]}
        self.assertEqual("READY", accepted["overall"])
        self.assertEqual("WARN", statuses["command-documentation"])

    def test_readiness_rejects_empty_constitution(self):
        apply_bootstrap(self.root, install_agents=True)
        (self.root / ".harness/PROJECT_CONSTITUTION.md").write_text(
            "", encoding="utf-8"
        )
        result = readiness(self.root)
        statuses = {item["id"]: item["status"] for item in result["findings"]}
        self.assertEqual("FAIL", statuses["project-guidance"])
        self.assertEqual("NEEDS_ATTENTION", result["overall"])

    def test_readiness_rejects_incomplete_or_placeholder_constitution(self):
        apply_bootstrap(self.root, install_agents=True)
        constitution = self.root / ".harness/PROJECT_CONSTITUTION.md"
        candidates = (
            "# Project Constitution\n\n## Scope\nOnly this repository.\n",
            constitution.read_text(encoding="utf-8") + "\nTBD\n",
        )
        for text in candidates:
            with self.subTest(prefix=text[:30]):
                constitution.write_text(text, encoding="utf-8")
                result = readiness(self.root)
                statuses = {
                    item["id"]: item["status"] for item in result["findings"]
                }
                self.assertEqual("FAIL", statuses["project-guidance"])
                self.assertEqual("NEEDS_ATTENTION", result["overall"])

    def test_readiness_rejects_long_section_filler_constitution(self):
        apply_bootstrap(self.root, install_agents=True)
        sections = "\n\n".join(
            f"{heading}\n\n" + ("abcde " * 12)
            for heading in (
                "## Project",
                "## Supported commands",
                "## Protected paths",
                "## Generated paths",
                "## Stack guidance and runtime probes",
                "## Security and authority boundary",
                "## Required evidence",
            )
        )
        (self.root / ".harness/PROJECT_CONSTITUTION.md").write_text(
            f"# Project Constitution\n\n{sections}\n", encoding="utf-8"
        )

        result = readiness(self.root)
        statuses = {item["id"]: item["status"] for item in result["findings"]}
        self.assertEqual("FAIL", statuses["project-guidance"])
        self.assertEqual("NEEDS_ATTENTION", result["overall"])

    def test_readiness_probe_status_is_not_presence_check(self):
        self.write_json("package.json", {"scripts": {"test": "node --test"}})
        apply_bootstrap(self.root, install_agents=True)
        path = self.root / ".harness/project.json"
        config = json.loads(path.read_text(encoding="utf-8"))
        self.assertTrue(config["runtime_probes"])

        for status, expected in (
            ("PROPOSED", "WARN"),
            ("ACCEPTED", "WARN"),
            ("INCONCLUSIVE", "WARN"),
            ("PASS", "PASS"),
            ("FAIL", "FAIL"),
        ):
            for probe in config["runtime_probes"]:
                probe["status"] = status
            path.write_text(json.dumps(config), encoding="utf-8")
            result = readiness(self.root)
            statuses = {item["id"]: item["status"] for item in result["findings"]}
            self.assertEqual(expected, statuses["observability"])
            if status == "FAIL":
                self.assertEqual("NEEDS_ATTENTION", result["overall"])

    def test_context_audit_warns_without_failing_correctness(self):
        harness_dir = self.root / ".harness"
        harness_dir.mkdir()
        (harness_dir / "PROJECT_CONSTITUTION.md").write_text("x\n" * 200, encoding="utf-8")
        result = context_audit(self.root)
        self.assertEqual("WARN", result["overall"])
        self.assertIn("not correctness limits", result["note"])

    def test_context_audit_rejects_agents_symlink_outside_project(self):
        outside = self.root.parent / f"{self.root.name}-agents.md"
        outside.write_text("outside", encoding="utf-8")
        try:
            (self.root / "AGENTS.md").symlink_to(outside)
            result = context_audit(self.root)
            self.assertEqual("FAIL", result["overall"])
            self.assertIn("escapes project root", result["findings"][0]["error"])
        finally:
            (self.root / "AGENTS.md").unlink()
            outside.unlink()

    def test_context_audit_includes_selected_stack_guidance(self):
        self.write_json("package.json", {"scripts": {"test": "node --test"}})
        apply_bootstrap(self.root, install_agents=True)
        guidance = self.root / ".harness/stack-packs/node-typescript/GUIDANCE.md"
        guidance.write_text("x" * 7000, encoding="utf-8")

        result = context_audit(self.root)

        finding = next(
            item
            for item in result["findings"]
            if item["path"] == ".harness/stack-packs/node-typescript/GUIDANCE.md"
        )
        self.assertEqual("WARN", finding["status"])
        catalog = next(
            item for item in result["findings"] if item["path"] == "context-catalog"
        )
        self.assertGreaterEqual(catalog["total_bytes"], 7000)

    def test_context_audit_warns_on_highly_overlapping_skill_triggers(self):
        descriptions = (
            "Use when reviewing secure release deployment changes",
            "Use when reviewing secure release deployment plans",
        )
        for index, description in enumerate(descriptions):
            path = self.root / f".agents/skills/skill-{index}/SKILL.md"
            path.parent.mkdir(parents=True)
            path.write_text(
                f"---\nname: skill-{index}\ndescription: {description}\n---\n",
                encoding="utf-8",
            )
        result = context_audit(self.root)
        self.assertTrue(
            any(
                item.get("error") == "highly overlapping Skill trigger descriptions"
                for item in result["findings"]
            )
        )

    def test_cli_rejects_output_path_outside_project(self):
        apply_bootstrap(self.root, install_agents=True)
        outside = self.root.parent / f"{self.root.name}-output.json"
        try:
            exit_code = cli_main(["discover", str(self.root), "--output", "../" + outside.name])
            self.assertEqual(2, exit_code)
            self.assertFalse(outside.exists())
        finally:
            if outside.exists():
                outside.unlink()

    def test_cli_refuses_to_write_through_output_symlink(self):
        apply_bootstrap(self.root, install_agents=True)
        real = self.root / "README.md"
        real.write_text("user-owned", encoding="utf-8")
        link = self.root / ".harness/runs/output.json"
        link.parent.mkdir(parents=True)
        link.symlink_to(real)
        exit_code = cli_main(
            ["discover", str(self.root), "--output", ".harness/runs/output.json"]
        )
        self.assertEqual(2, exit_code)
        self.assertEqual("user-owned", real.read_text(encoding="utf-8"))

    def test_cli_refuses_user_file_overwrite_and_undeclared_output(self):
        apply_bootstrap(self.root, install_agents=True)
        readme = self.root / "README.md"
        readme.write_text("user-owned\n", encoding="utf-8")
        exit_code = cli_main(
            ["discover", str(self.root), "--output", "README.md"]
        )
        self.assertEqual(2, exit_code)
        self.assertEqual("user-owned\n", readme.read_text(encoding="utf-8"))

    def test_cli_rejects_invalid_validation_output_before_running_checks(self):
        apply_bootstrap(self.root, install_agents=True)
        config_path = self.root / ".harness/project.json"
        config = json.loads(config_path.read_text(encoding="utf-8"))
        config["checks"] = [
            {
                "id": "must-not-run",
                "command": [
                    sys.executable,
                    "-c",
                    "from pathlib import Path; Path('executed').write_text('yes')",
                ],
                "cwd": ".",
                "required": True,
                "timeout_seconds": 10,
            }
        ]
        config_path.write_text(json.dumps(config), encoding="utf-8")
        readme = self.root / "README.md"
        readme.write_text("user-owned\n", encoding="utf-8")

        exit_code = cli_main(
            ["validate", str(self.root), "--output", "README.md"]
        )

        self.assertEqual(2, exit_code)
        self.assertFalse((self.root / "executed").exists())
        self.assertEqual("user-owned\n", readme.read_text(encoding="utf-8"))

    def test_cli_allows_new_output_only_under_generated_path(self):
        apply_bootstrap(self.root, install_agents=True)
        output = ".harness/runs/manual/discovery.json"
        self.assertEqual(
            0,
            cli_main(["discover", str(self.root), "--output", output]),
        )
        self.assertTrue((self.root / output).is_file())
        self.assertEqual(
            2,
            cli_main(["discover", str(self.root), "--output", output]),
        )

    def test_cli_default_validation_uses_configured_generated_path(self):
        apply_bootstrap(self.root, install_agents=True)
        config_path = self.root / ".harness/project.json"
        config = json.loads(config_path.read_text(encoding="utf-8"))
        config["checks"] = [
            {
                "id": "version",
                "command": [sys.executable, "--version"],
                "cwd": ".",
                "required": True,
                "timeout_seconds": 10,
            }
        ]
        config["generated_paths"] = ["generated-evidence"]
        config_path.write_text(json.dumps(config), encoding="utf-8")

        self.assertEqual(0, cli_main(["validate", str(self.root)]))
        outputs = list((self.root / "generated-evidence").glob("*/validation.json"))
        self.assertEqual(1, len(outputs))
        self.assertFalse((self.root / ".harness/runs").exists())

    def test_cli_rejects_default_output_collision_before_running_checks(self):
        apply_bootstrap(self.root, install_agents=True)
        config_path = self.root / ".harness/project.json"
        config = json.loads(config_path.read_text(encoding="utf-8"))
        config["checks"] = [
            {
                "id": "must-not-run",
                "command": [
                    sys.executable,
                    "-c",
                    "from pathlib import Path; Path('executed').write_text('yes')",
                ],
                "cwd": ".",
                "required": True,
                "timeout_seconds": 10,
            }
        ]
        config_path.write_text(json.dumps(config), encoding="utf-8")
        fixed = datetime(2026, 8, 8, 12, 0, tzinfo=timezone.utc)
        output = self.root / ".harness/runs/20260808T120000Z/validation.json"
        output.parent.mkdir(parents=True)
        output.write_text("user-owned\n", encoding="utf-8")

        with patch("harness.core.datetime") as mocked_datetime:
            mocked_datetime.now.return_value = fixed
            exit_code = cli_main(["validate", str(self.root)])

        self.assertEqual(2, exit_code)
        self.assertFalse((self.root / "executed").exists())
        self.assertEqual("user-owned\n", output.read_text(encoding="utf-8"))

    def test_cli_context_audit_returns_nonzero_on_fail(self):
        outside = self.root.parent / f"{self.root.name}-outside-agents.md"
        outside.write_text("outside", encoding="utf-8")
        try:
            (self.root / "AGENTS.md").symlink_to(outside)
            self.assertEqual(1, cli_main(["context-audit", str(self.root)]))
        finally:
            (self.root / "AGENTS.md").unlink()
            outside.unlink()

    def test_discovery_reports_matched_pack_conflicts(self):
        (self.root / "README.md").write_text("fixture", encoding="utf-8")
        pack_root = self.root / "packs"
        for identifier, conflict in (("alpha", "beta"), ("beta", "alpha")):
            directory = pack_root / identifier
            directory.mkdir(parents=True)
            (directory / "GUIDANCE.md").write_text(
                f"# {identifier}\n", encoding="utf-8"
            )
            (directory / "pack.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "id": identifier,
                        "name": identifier.title(),
                        "version": 1,
                        "detect_any": ["README.md"],
                        "detect_all": [],
                        "candidate_checks": [],
                        "runtime_probe_types": ["process"],
                        "references": ["https://example.invalid"],
                        "conflicts": [conflict],
                    }
                ),
                encoding="utf-8",
            )
        result = discover(self.root, pack_root)
        self.assertEqual([{"left": "alpha", "right": "beta"}], result["conflicts"])
        self.assertTrue(any("conflict" in item for item in result["warnings"]))

    def test_stack_pack_loader_rejects_path_traversal_marker(self):
        pack_root = self.root / "packs"
        pack_dir = pack_root / "bad"
        pack_dir.mkdir(parents=True)
        pack = {
            "schema_version": 1,
            "id": "bad",
            "name": "Bad",
            "version": 1,
            "detect_any": ["../secret"],
            "detect_all": [],
            "candidate_checks": [],
            "runtime_probe_types": [],
            "references": [],
            "conflicts": [],
        }
        (pack_dir / "pack.json").write_text(json.dumps(pack), encoding="utf-8")
        with self.assertRaisesRegex(HarnessError, "unsafe marker"):
            load_stack_packs(pack_root)

    def test_stack_pack_loader_rejects_shell_candidate(self):
        pack_root = self.root / "packs"
        pack_dir = pack_root / "bad"
        pack_dir.mkdir(parents=True)
        pack = {
            "schema_version": 1,
            "id": "bad",
            "name": "Bad",
            "version": 1,
            "detect_any": ["README.md"],
            "detect_all": [],
            "candidate_checks": [
                {
                    "id": "bad",
                    "when_any": ["README.md"],
                    "command": ["sh", "-c", "true"],
                    "cwd": ".",
                    "required": True,
                    "timeout_seconds": 10,
                }
            ],
            "runtime_probe_types": [],
            "references": [],
            "conflicts": [],
        }
        (pack_dir / "pack.json").write_text(json.dumps(pack), encoding="utf-8")
        with self.assertRaisesRegex(HarnessError, "shell code flags are prohibited"):
            load_stack_packs(pack_root)


if __name__ == "__main__":
    unittest.main()
