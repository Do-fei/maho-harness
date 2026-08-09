"""Build hook that bundles MAHO's dependency-free runtime assets."""

from pathlib import Path
from shutil import copytree

from setuptools import setup
from setuptools.command.build_py import build_py as _build_py


ROOT = Path(__file__).resolve().parent
ASSET_DIRECTORIES = ("schemas", "skills", "stack-packs", "templates")


class build_py(_build_py):
    def run(self) -> None:
        super().run()
        destination = Path(self.build_lib) / "harness/assets"
        for name in ASSET_DIRECTORIES:
            copytree(ROOT / name, destination / name, dirs_exist_ok=True)


setup(cmdclass={"build_py": build_py})
