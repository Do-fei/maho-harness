import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.build_public_release import ReleaseError, build_public_tree


class PublicReleaseTests(unittest.TestCase):
    def write_manifest(self, root: Path, *, roots=(), files=()) -> Path:
        path = root / "manifest.json"
        path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "include_roots": list(roots),
                    "include_files": list(files),
                    "excluded_internal_roots": [],
                }
            ),
            encoding="utf-8",
        )
        return path

    def test_public_candidate_has_resolved_release_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "public"
            result = build_public_tree(output)

            self.assertEqual("public-candidate", result["mode"])
            self.assertTrue((output / "NOTICE").is_file())
            self.assertIn("MAHO contributors", (output / "NOTICE").read_text(encoding="utf-8"))
            self.assertIn("Do-fei/maho-harness", (output / "pyproject.toml").read_text(encoding="utf-8"))

    def test_public_scan_fails_closed_on_release_placeholders(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            source = base / "source"
            source.mkdir()
            (source / "NOTICE").write_text(
                "Copyright 2026 [COPYRIGHT "
                "HOLDER TO BE CONFIRMED BEFORE PUBLIC RELEASE]\n",
                encoding="utf-8",
            )
            (source / "pyproject.toml").write_text(
                'Source = "https://github.com/'
                'OWNER/maho"\n',
                encoding="utf-8",
            )
            manifest = self.write_manifest(
                source,
                files=["NOTICE", "pyproject.toml"],
            )
            output = base / "public"

            with self.assertRaisesRegex(ReleaseError, "unresolved") as caught:
                build_public_tree(output, source=source, manifest_path=manifest)

            self.assertFalse(output.exists())
            self.assertIn("NOTICE: unresolved copyright holder", str(caught.exception))
            self.assertIn("pyproject.toml: unresolved repository owner", str(caught.exception))

    def test_private_beta_export_is_allowlisted_and_checksummed(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "public"
            result = build_public_tree(
                output,
                allow_private_beta_placeholders=True,
            )

            self.assertEqual("private-beta", result["mode"])
            self.assertEqual(0, result["overwritten"])
            self.assertTrue((output / "SHA256SUMS").is_file())
            self.assertTrue((output / "harness/cli.py").is_file())
            self.assertFalse((output / "reports").exists())
            self.assertFalse((output / "experiments").exists())
            self.assertNotIn("/Users/", (output / "SHA256SUMS").read_text(encoding="utf-8"))
            checksum_paths = {
                line.split("  ", 1)[1]
                for line in (output / "SHA256SUMS").read_text(encoding="utf-8").splitlines()
            }
            exported_paths = {
                path.relative_to(output).as_posix()
                for path in output.rglob("*")
                if path.is_file() and path.name != "SHA256SUMS"
            }
            self.assertEqual(exported_paths, checksum_paths)

    def test_include_root_symlink_is_rejected_before_output_creation(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            source = base / "source"
            external = base / "external"
            source.mkdir()
            external.mkdir()
            (external / "payload.txt").write_text("outside\n", encoding="utf-8")
            (source / "public").symlink_to(external, target_is_directory=True)
            manifest = self.write_manifest(source, roots=["public"])
            output = base / "output"

            with self.assertRaisesRegex(ReleaseError, "symlink"):
                build_public_tree(output, source=source, manifest_path=manifest)

            self.assertFalse(output.exists())

    def test_manifest_parent_and_absolute_paths_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            source = base / "source"
            source.mkdir()
            outside = base / "payload.txt"
            outside.write_text("outside\n", encoding="utf-8")
            for unsafe in (
                "../payload.txt",
                str(outside),
                "nested/./payload.txt",
                "nested//payload.txt",
                "nested\\payload.txt",
                "C:/payload.txt",
            ):
                with self.subTest(path=unsafe):
                    manifest = self.write_manifest(source, files=[unsafe])
                    output = base / f"output-{len(unsafe)}"
                    with self.assertRaisesRegex(ReleaseError, "unsafe include_files"):
                        build_public_tree(output, source=source, manifest_path=manifest)
                    self.assertFalse(output.exists())

    def test_failed_staged_export_leaves_no_partial_output(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            output = base / "public"

            with patch(
                "scripts.build_public_release._checksums",
                side_effect=OSError("simulated checksum failure"),
            ):
                with self.assertRaisesRegex(OSError, "simulated"):
                    build_public_tree(
                        output,
                        allow_private_beta_placeholders=True,
                    )

            self.assertFalse(output.exists())
            self.assertEqual([], list(base.glob(".public.staging-*")))


if __name__ == "__main__":
    unittest.main()
