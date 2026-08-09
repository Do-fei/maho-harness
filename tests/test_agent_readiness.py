import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from harness.core import apply_bootstrap, discover, readiness


class AgentReadinessTests(unittest.TestCase):
    def test_agent_hostile_repository_reports_missing_validation_and_guidance(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            (root / "manual-only.txt").write_text(
                "Run the undocumented release steps by hand.",
                encoding="utf-8",
            )
            (root / "requirements.txt").write_text(
                "fastapi>=0.100\n", encoding="utf-8"
            )
            (root / "app").mkdir()
            (root / "app/main.py").write_text("value = 1\n", encoding="utf-8")
            (root / "RUNBOOK.md").write_text(
                "Run manually with a teammate's local environment.\n",
                encoding="utf-8",
            )

            result = readiness(root)

        statuses = {item["id"]: item["status"] for item in result["findings"]}
        self.assertEqual("NEEDS_ATTENTION", result["overall"])
        self.assertEqual("WARN", statuses["documentation"])
        self.assertEqual("FAIL", statuses["project-guidance"])
        self.assertEqual("FAIL", statuses["configuration"])
        self.assertEqual("FAIL", statuses["validation-path"])
        self.assertEqual("WARN", statuses["command-documentation"])
        self.assertEqual("PASS", statuses["stack-discovery"])
        self.assertEqual("PASS", statuses["stack-conflicts"])
        self.assertEqual("WARN", statuses["testability"])
        self.assertEqual("WARN", statuses["build-reproducibility"])
        self.assertEqual("WARN", statuses["environment"])
        self.assertEqual("WARN", statuses["repository-structure"])
        self.assertEqual("WARN", statuses["observability"])
        self.assertEqual("WARN", statuses["ci"])
        self.assertEqual("WARN", statuses["automation"])
        self.assertEqual("WARN", statuses["local-setup"])
        self.assertEqual("WARN", statuses["manual-workflows"])

    def test_agent_friendly_repository_covers_all_readiness_dimensions(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            (root / "README.md").write_text("# Friendly\n", encoding="utf-8")
            (root / ".python-version").write_text("3.12\n", encoding="utf-8")
            (root / "setup.py").write_text("name = 'fixture'\n", encoding="utf-8")
            (root / "app").mkdir()
            (root / "app/main.py").write_text(
                "def ready(): return True\n", encoding="utf-8"
            )
            (root / "tests").mkdir()
            (root / "tests/test_ready.py").write_text(
                "import unittest\n\n"
                "class T(unittest.TestCase):\n"
                "    def test_ready(self): self.assertTrue(True)\n",
                encoding="utf-8",
            )
            workflow = root / ".github/workflows/test.yml"
            workflow.parent.mkdir(parents=True)
            workflow.write_text("name: test\n", encoding="utf-8")
            apply_bootstrap(root, install_agents=True)
            config_path = root / ".harness/project.json"
            config = json.loads(config_path.read_text(encoding="utf-8"))
            config["checks"] = [
                {
                    key: item[key]
                    for key in (
                        "id",
                        "command",
                        "cwd",
                        "required",
                        "timeout_seconds",
                    )
                }
                for item in config["proposed_checks"]
            ]
            config["proposed_checks"] = []
            for probe in config["runtime_probes"]:
                probe["status"] = "PASS"
            config_path.write_text(json.dumps(config), encoding="utf-8")

            result = readiness(root)

        statuses = {item["id"]: item["status"] for item in result["findings"]}
        self.assertEqual("READY", result["overall"])
        for identifier in (
            "documentation",
            "project-guidance",
            "configuration",
            "validation-path",
            "command-documentation",
            "stack-discovery",
            "stack-conflicts",
            "testability",
            "build-reproducibility",
            "environment",
            "repository-structure",
            "observability",
            "ci",
            "automation",
            "local-setup",
            "manual-workflows",
        ):
            with self.subTest(identifier=identifier):
                self.assertEqual("PASS", statuses[identifier])

    def test_readiness_does_not_follow_dependency_symlink_outside_repository(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "repo"
            root.mkdir()
            outside = Path(directory) / "outside-requirements.txt"
            outside.write_text("secret-package==1.0\n", encoding="utf-8")
            (root / "requirements.txt").symlink_to(outside)

            result = readiness(root)

        statuses = {item["id"]: item["status"] for item in result["findings"]}
        self.assertEqual("PASS", statuses["build-reproducibility"])

    def test_agent_unknown_stack_repository_warns_stack_discovery(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            (root / "notes.txt").write_text("unknown repository\n", encoding="utf-8")

            result = readiness(root)

        statuses = {item["id"]: item["status"] for item in result["findings"]}
        self.assertEqual("WARN", statuses["stack-discovery"])
        self.assertEqual("PASS", statuses["stack-conflicts"])

    def test_agent_conflicting_stack_packs_fail_readiness(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            (root / "README.md").write_text("fixture\n", encoding="utf-8")
            pack_root = root / "packs"
            for identifier, conflict in (("alpha", "beta"), ("beta", "alpha")):
                pack = pack_root / identifier
                pack.mkdir(parents=True)
                (pack / "GUIDANCE.md").write_text(
                    f"# {identifier}\n", encoding="utf-8"
                )
                (pack / "pack.json").write_text(
                    json.dumps(
                        {
                            "schema_version": 1,
                            "id": identifier,
                            "name": identifier.title(),
                            "version": 1,
                            "detect_any": ["README.md"],
                            "detect_all": [],
                            "candidate_checks": [],
                            "runtime_probe_types": [],
                            "references": [],
                            "conflicts": [conflict],
                        }
                    ),
                    encoding="utf-8",
                )
            discovery = discover(root, pack_root)

            result = readiness(root, discovery)

        statuses = {item["id"]: item["status"] for item in result["findings"]}
        self.assertEqual("FAIL", statuses["stack-conflicts"])
        self.assertEqual("NEEDS_ATTENTION", result["overall"])


if __name__ == "__main__":
    unittest.main()
