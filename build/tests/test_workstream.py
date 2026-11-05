#!/usr/bin/env python3
"""Tests for workstream.py â€” the check-step defects that made the CLI
untrustworthy enough that agents hand-maintained a parallel status table.

Runs against src/templates/tools by default. Set VAULT_LINT_TOOLS to a generated
edition's templates/tools directory to test that copy instead (build/README.md).

Run:  python -B build/tests/test_workstream.py
Stdlib only (unittest) â€” no pytest dependency.
"""

import os
import sys
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, os.environ.get("VAULT_LINT_TOOLS", str(_REPO / "src" / "templates" / "tools")))

import workstream  # noqa: E402


class TestStepMatching(unittest.TestCase):
    """Substring matching made '1.1' silently tick '1.10'."""

    STEP_1_1 = "- [ ] **1.1** Write a failing test â†’ *output: red test*"
    STEP_1_10 = "- [ ] **1.10** Tenth step â†’ *output: thing*"
    STEP_11_1 = "- [ ] **11.1** Eleventh phase â†’ *output: thing*"

    def test_number_query_does_not_match_longer_number(self):
        self.assertFalse(workstream.step_matches(self.STEP_1_10, "1.1"))

    def test_number_query_does_not_match_wider_prefix(self):
        self.assertFalse(workstream.step_matches(self.STEP_11_1, "1.1"))

    def test_number_query_matches_its_own_step(self):
        self.assertTrue(workstream.step_matches(self.STEP_1_1, "1.1"))
        self.assertTrue(workstream.step_matches(self.STEP_1_10, "1.10"))
        self.assertTrue(workstream.step_matches(self.STEP_11_1, "11.1"))

    def test_non_numeric_query_falls_back_to_substring(self):
        self.assertTrue(workstream.step_matches(self.STEP_1_1, "failing test"))
        self.assertFalse(workstream.step_matches(self.STEP_1_1, "passing test"))

    def test_number_cited_inside_another_step_does_not_match(self):
        # '1.1' errored as ambiguous because step 6.3's text cites "the 1.1 baseline"
        cites = "- [ ] 6.3: Full sweep. Record per-check counts vs the 1.1 baseline"
        self.assertFalse(workstream.step_matches(cites, "1.1"))
        self.assertTrue(workstream.step_matches("- [ ] 1.1: Baseline", "1.1"))

    def test_leading_token_formats(self):
        for line in ("- [ ] 1.1: Baseline", "- [ ] **1.1** Baseline", "* [ ] 1.1 Baseline"):
            self.assertTrue(workstream.step_matches(line, "1.1"), line)

    def test_anywhere_mode_keeps_whole_token_rule(self):
        line = "- [ ] Step (ref 1.1) do it"
        self.assertFalse(workstream.step_matches(line, "1.1"))
        self.assertTrue(workstream.step_matches(line, "1.1", leading_only=False))
        self.assertFalse(workstream.step_matches("- [ ] ref 1.10", "1.1", leading_only=False))


class TestWriteKeepingEol(unittest.TestCase):
    """advance (write_text â†’ CRLF) and check-step (write_bytes â†’ LF) flipped
    the same index file's line endings back and forth."""

    def setUp(self):
        import tempfile
        self.dir = Path(tempfile.mkdtemp())

    def _roundtrip(self, raw):
        p = self.dir / "f.md"
        p.write_bytes(raw)
        text = p.read_text(encoding="utf-8")  # universal newlines â†’ LF
        workstream.write_keeping_eol(p, text.replace("old", "new"))
        return p.read_bytes()

    def test_crlf_file_stays_crlf(self):
        out = self._roundtrip(b"a: old\r\nb\r\n")
        self.assertEqual(out, b"a: new\r\nb\r\n")

    def test_lf_file_stays_lf(self):
        out = self._roundtrip(b"a: old\nb\n")
        self.assertEqual(out, b"a: new\nb\n")

    def test_new_file_gets_lf(self):
        p = self.dir / "new.md"
        workstream.write_keeping_eol(p, "x\ny\n")
        self.assertEqual(p.read_bytes(), b"x\ny\n")


class TestMarkdownCell(unittest.TestCase):
    """An unescaped pipe in step text split the status row into extra cells."""

    def test_pipe_is_escaped(self):
        self.assertEqual(workstream.md_cell("a | b"), "a \\| b")

    def test_newline_collapsed(self):
        self.assertNotIn("\n", workstream.md_cell("a\nb"))


class TestStatusRowSet(unittest.TestCase):
    INDEX = """| Field | Value |
|---|---|
| Phase | implement |
| Current Step | â€” |
| Last Active | 2026-01-01 |
"""

    def test_sets_value(self):
        out = workstream.status_row_set(self.INDEX, "Current Step", "**1.2** Fix it")
        self.assertIn("| Current Step | **1.2** Fix it |", out)

    def test_value_with_pipe_stays_one_row(self):
        out = workstream.status_row_set(self.INDEX, "Current Step", "**1.4** a | b")
        row = [l for l in out.splitlines() if "Current Step" in l][0]
        # A two-cell row has three delimiters: | cell | cell |
        self.assertEqual(
            row.count("|") - row.count("\\|"), 3,
            f"row must stay a two-cell row: {row!r}",
        )
        self.assertIn("\\|", row, "the pipe inside the value must be escaped")

    def test_repairs_an_already_corrupted_row(self):
        corrupted = self.INDEX.replace(
            "| Current Step | â€” |",
            "| Current Step | â€” | orphaned fragment from an earlier write |",
        )
        out = workstream.status_row_set(corrupted, "Current Step", "clean")
        self.assertIn("| Current Step | clean |", out)
        self.assertNotIn("orphaned fragment", out)

    def test_does_not_touch_other_rows(self):
        out = workstream.status_row_set(self.INDEX, "Current Step", "x")
        self.assertIn("| Phase | implement |", out)
        self.assertIn("| Last Active | 2026-01-01 |", out)

    def test_value_with_backslash_escape_sequences(self):
        # A step's text naming a Windows path (e.g. "..\vault-mcp-server\server.mjs")
        # or a regex-looking fragment (e.g. "\s") must not be interpreted as a
        # re.sub replacement escape sequence -- it previously raised
        # `re.error: bad escape \U` / `\s` because the value was passed as a
        # plain string replacement rather than a callable. Recurred 3x on
        # vault-rag-mcp-server (2026-09-06/07) before being fixed.
        value = r"path C:\Users\test\vault-mcp-server\server.mjs with \s and \U escape-like sequences"
        out = workstream.status_row_set(self.INDEX, "Current Step", value)
        self.assertIn(f"| Current Step | {value} |", out)


class TestYamlDoubleQuoted(unittest.TestCase):
    def test_quote_escaped(self):
        self.assertEqual(workstream.yaml_dq('say "hi"'), 'say \\"hi\\"')

    def test_backslash_escaped_before_quote(self):
        self.assertEqual(workstream.yaml_dq("a\\b"), "a\\\\b")


if __name__ == "__main__":
    os.environ.setdefault("WORKSPACE_ROOT", str(Path(__file__).resolve().parent.parent))
    unittest.main(verbosity=2)
