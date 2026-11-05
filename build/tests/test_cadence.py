#!/usr/bin/env python3
"""Tests for cadence.py delete. Stdlib only (unittest).

_working/ holds a .gitignore once cadence-run.ps1 has run, so delete must treat
it like .gitkeep and stay blocked by anything else.

Runs against src/templates/tools by default. Set VAULT_LINT_TOOLS to a generated
edition's templates/tools directory to test that copy instead (build/README.md).
Themed editions rename the CLI to patrol.py, and its folder to control-plane/patrols.

Run:  python -B build/tests/test_cadence.py
"""

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent.parent
_TOOLS_DIR = Path(os.environ.get("VAULT_LINT_TOOLS", _REPO / "src" / "templates" / "tools"))
_CLI = next(p for p in (_TOOLS_DIR / "cadence.py", _TOOLS_DIR / "patrol.py") if p.exists())
NAME = "demo"


class TestDelete(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.workspace = Path(tmp.name)
        self.cli("create", NAME)
        self.path = next((self.workspace / "control-plane").glob(f"*/{NAME}"))
        self.work = self.path / "_working"

    def cli(self, *args, check=True):
        env = dict(os.environ, WORKSPACE_ROOT=str(self.workspace), PYTHONIOENCODING="utf-8")
        result = subprocess.run([sys.executable, "-B", str(_CLI), *args], env=env,
                                capture_output=True, encoding="utf-8")
        if check:
            self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def add(self, *names):
        for name in names:
            target = self.work / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("x\n", encoding="utf-8")

    def assert_blocked(self, listed):
        result = self.cli("delete", NAME, check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(self.path.exists())
        self.assertIn("1 file(s) still in _working/", result.stderr)
        self.assertIn(listed, result.stderr)
        self.assertNotIn(".gitignore", result.stderr)

    def test_gitkeep_alone_does_not_block(self):
        self.assertTrue((self.work / ".gitkeep").exists())
        self.cli("delete", NAME)
        self.assertFalse(self.path.exists())

    def test_gitkeep_and_gitignore_do_not_block(self):
        self.add(".gitignore")
        self.cli("delete", NAME)
        self.assertFalse(self.path.exists())

    def test_run_log_still_blocks(self):
        self.add(".gitignore", "run-2026-01-01-000000.log")
        self.assert_blocked("run-2026-01-01-000000.log")

    def test_failed_flag_still_blocks(self):
        self.add(".gitignore", "FAILED-2026-01-01-000000.flag")
        self.assert_blocked("FAILED-2026-01-01-000000.flag")

    def test_nested_file_still_blocks(self):
        self.add(".gitignore", "scratch/notes.md")
        self.assert_blocked("notes.md")

    def test_force_deletes_despite_leftovers(self):
        self.add(".gitignore", "notes.md")
        self.cli("delete", NAME, "--force")
        self.assertFalse(self.path.exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
