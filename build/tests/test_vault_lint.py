#!/usr/bin/env python3
"""Tests for the vault-lint.py template. Stdlib only (unittest).

Runs against src/templates/tools by default. Set VAULT_LINT_TOOLS to a generated
edition's templates/tools directory to test that copy instead (build/README.md).

Run:  python -B build/tests/test_vault_lint.py
"""

import argparse
import contextlib
import importlib.util
import io
import os
import sys
import tempfile
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent.parent
_TOOLS_DIR = Path(os.environ.get("VAULT_LINT_TOOLS", _REPO / "src" / "templates" / "tools"))
_spec = importlib.util.spec_from_file_location("vault_lint", _TOOLS_DIR / "vault-lint.py")
vault_lint = importlib.util.module_from_spec(_spec)
sys.modules["vault_lint"] = vault_lint
_spec.loader.exec_module(vault_lint)


# ── pure parsing helpers — no vault on disk needed ─────────────────────────────

class TestParseFrontmatter(unittest.TestCase):
    def test_parses_scalar_and_list_fields(self):
        text = "---\nnote_type: knowledge\ntags: [a, b, c]\n---\n\nBody.\n"
        fm, body = vault_lint.parse_frontmatter(text)
        self.assertEqual(fm["note_type"], "knowledge")
        self.assertEqual(fm["tags"], ["a", "b", "c"])
        self.assertEqual(body, "Body.\n")

    def test_no_frontmatter_returns_empty_dict(self):
        fm, body = vault_lint.parse_frontmatter("# Just a note\n\nNo frontmatter here.\n")
        self.assertEqual(fm, {})
        self.assertIn("Just a note", body)

    def test_unterminated_frontmatter_returns_empty_dict(self):
        fm, body = vault_lint.parse_frontmatter("---\nnote_type: knowledge\n\nno closing fence\n")
        self.assertEqual(fm, {})

    def test_quoted_values_unquoted(self):
        fm, _ = vault_lint.parse_frontmatter('---\nconfidence: "high"\n---\n')
        self.assertEqual(fm["confidence"], "high")

    def test_leading_bom_tolerated(self):
        text = "﻿---\nnote_type: knowledge\n---\nBody.\n"
        fm, _ = vault_lint.parse_frontmatter(text)
        self.assertEqual(fm["note_type"], "knowledge")


class TestIterWikilinks(unittest.TestCase):
    def test_body_link_before_related_is_body_location(self):
        body = "Some prose [[target-note]] here.\n"
        links = list(vault_lint.iter_wikilinks(body, {}))
        self.assertEqual(links, [("target-note", "body")])

    def test_link_under_related_heading_is_related_location(self):
        body = "Prose.\n\n## Related\n\n- [[a-note]]\n"
        links = list(vault_lint.iter_wikilinks(body, {}))
        self.assertIn(("a-note", "related"), links)

    def test_frontmatter_related_list_yielded(self):
        links = list(vault_lint.iter_wikilinks("no links in body", {"related": ["x", "y"]}))
        self.assertIn(("x", "frontmatter"), links)
        self.assertIn(("y", "frontmatter"), links)

    def test_alias_stripped(self):
        links = list(vault_lint.iter_wikilinks("[[target|Display Name]]", {}))
        self.assertEqual(links, [("target", "body")])

    def test_heading_anchor_stripped(self):
        links = list(vault_lint.iter_wikilinks("[[target#Some Section]]", {}))
        self.assertEqual(links, [("target", "body")])

    def test_fenced_code_block_links_ignored(self):
        body = "```\n[[not-a-real-link]]\n```\n\n[[real-link]]\n"
        links = list(vault_lint.iter_wikilinks(body, {}))
        self.assertEqual(links, [("real-link", "body")])

    def test_inline_code_span_links_ignored(self):
        body = "See `[[not-a-link]]` but also [[real-link]].\n"
        links = list(vault_lint.iter_wikilinks(body, {}))
        self.assertEqual(links, [("real-link", "body")])

    def test_related_scope_ends_at_next_heading(self):
        body = "## Related\n\n- [[a]]\n\n## Notes\n\n- [[b]]\n"
        links = list(vault_lint.iter_wikilinks(body, {}))
        self.assertIn(("a", "related"), links)
        self.assertIn(("b", "body"), links)


# ── checks needing a real vault on disk ─────────────────────────────────────────

class VaultTestCase(unittest.TestCase):
    """Build a small synthetic vault per test and point the module's globals at it."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.vault = Path(self._tmp.name) / "vault"
        self.vault.mkdir()
        self._orig_vault = vault_lint.VAULT
        self._orig_subtrees = vault_lint.CONCEPT_SUBTREES
        vault_lint.VAULT = self.vault
        self.addCleanup(self._restore)

    def _restore(self):
        vault_lint.VAULT = self._orig_vault
        vault_lint.CONCEPT_SUBTREES = self._orig_subtrees

    def write(self, rel_path, content):
        p = self.vault / rel_path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return p

    def discover(self):
        vault_lint.CONCEPT_SUBTREES = vault_lint.discover_subtrees()


class TestResolveTarget(VaultTestCase):
    def test_base_extension_whitelisted(self):
        resolved, ambiguous = vault_lint.resolve_target("some.base", {})
        self.assertEqual(resolved, "some.base")
        self.assertFalse(ambiguous)

    def test_vault_relative_path_resolves(self):
        self.write("alpha/note-b.md", "---\nnote_type: knowledge\n---\n")
        resolved, _ = vault_lint.resolve_target("alpha/note-b", {})
        self.assertEqual(resolved, "alpha/note-b.md")

    def test_unresolvable_path_returns_none(self):
        resolved, _ = vault_lint.resolve_target("alpha/nonexistent", {})
        self.assertIsNone(resolved)

    def test_unique_slug_resolves(self):
        slug_index = {"note-a": ["alpha/note-a.md"]}
        resolved, ambiguous = vault_lint.resolve_target("note-a", slug_index)
        self.assertEqual(resolved, "alpha/note-a.md")
        self.assertFalse(ambiguous)

    def test_ambiguous_slug_flagged(self):
        slug_index = {"dup": ["alpha/dup.md", "beta/dup.md"]}
        resolved, ambiguous = vault_lint.resolve_target("dup", slug_index)
        self.assertIsNotNone(resolved)
        self.assertTrue(ambiguous)

    def test_source_relative_bare_reference_resolves_before_global_slug(self):
        self.write("alpha/sibling.md", "---\nnote_type: knowledge\n---\n")
        slug_index = {"sibling": ["beta/sibling.md"]}  # a decoy elsewhere in the vault
        resolved, ambiguous = vault_lint.resolve_target("sibling", slug_index, source_dir="alpha")
        self.assertEqual(resolved, "alpha/sibling.md")
        self.assertFalse(ambiguous)


class TestCheckC1(VaultTestCase):
    def test_missing_note_type_flagged(self):
        p = self.write("alpha/a.md", "---\ntags: [x]\n---\n")
        fm, body = vault_lint.parse_frontmatter(p.read_text(encoding="utf-8"))
        findings = vault_lint.check_c1(p, fm, body)
        self.assertEqual(len(findings), 1)
        self.assertIn("missing note_type", findings[0]["detail"])

    def test_vault_note_missing_source_url_is_auto_fixable(self):
        p = self.write(
            "alpha/a.md",
            "---\nnote_type: vault-note\nsource_path: x\nsynced_at: 2026-01-01\n"
            "distilled_at: 2026-01-01\nconfidence: high\ntags: [x]\n---\n",
        )
        fm, body = vault_lint.parse_frontmatter(p.read_text(encoding="utf-8"))
        findings = vault_lint.check_c1(p, fm, body)
        self.assertEqual(len(findings), 1)
        self.assertTrue(findings[0]["auto_fixable"])
        self.assertIn("source_url", findings[0]["detail"])

    def test_knowledge_type_does_not_require_tags(self):
        p = self.write("alpha/a.md", "---\nnote_type: knowledge\n---\n")
        fm, body = vault_lint.parse_frontmatter(p.read_text(encoding="utf-8"))
        self.assertEqual(vault_lint.check_c1(p, fm, body), [])


class TestCheckC2(VaultTestCase):
    def test_illegal_note_type_flagged(self):
        p = self.write("alpha/a.md", "---\nnote_type: perspective\n---\n")
        fm, body = vault_lint.parse_frontmatter(p.read_text(encoding="utf-8"))
        findings = vault_lint.check_c2(p, fm, body)
        self.assertEqual(len(findings), 1)
        self.assertFalse(findings[0]["auto_fixable"])

    def test_index_note_type_auto_fixable_to_vault_index(self):
        p = self.write("alpha/a.md", "---\nnote_type: index\n---\n")
        fm, body = vault_lint.parse_frontmatter(p.read_text(encoding="utf-8"))
        findings = vault_lint.check_c2(p, fm, body)
        self.assertEqual(len(findings), 1)
        self.assertTrue(findings[0]["auto_fixable"])

    def test_bare_index_md_typed_vault_note_flagged(self):
        p = self.write("alpha/index.md", "---\nnote_type: vault-note\n---\n")
        fm, body = vault_lint.parse_frontmatter(p.read_text(encoding="utf-8"))
        findings = vault_lint.check_c2(p, fm, body)
        self.assertEqual(len(findings), 1)
        self.assertIn("likely vault-index", findings[0]["detail"])


class TestCheckC3(VaultTestCase):
    def test_phantom_link_flagged(self):
        p = self.write("alpha/a.md", "---\nnote_type: knowledge\n---\n\n[[nonexistent]]\n")
        fm, body = vault_lint.parse_frontmatter(p.read_text(encoding="utf-8"))
        findings = vault_lint.check_c3(p, fm, body, {})
        self.assertEqual(len(findings), 1)
        self.assertIn("phantom wikilink", findings[0]["detail"])

    def test_resolvable_link_not_flagged(self):
        self.write("alpha/b.md", "---\nnote_type: knowledge\n---\n")
        p = self.write("alpha/a.md", "---\nnote_type: knowledge\n---\n\n[[alpha/b]]\n")
        fm, body = vault_lint.parse_frontmatter(p.read_text(encoding="utf-8"))
        slug_index = vault_lint.build_slug_index()
        findings = vault_lint.check_c3(p, fm, body, slug_index)
        self.assertEqual(findings, [])

    def test_dotdot_relative_link_always_phantom(self):
        p = self.write("alpha/a.md", "---\nnote_type: knowledge\n---\n\n[[../beta/b]]\n")
        fm, body = vault_lint.parse_frontmatter(p.read_text(encoding="utf-8"))
        findings = vault_lint.check_c3(p, fm, body, {})
        self.assertEqual(len(findings), 1)
        self.assertIn("does not resolve relative", findings[0]["detail"])

    def test_prefix_truncated_link_auto_fixable(self):
        """[[sub/note-b]] missing its 'alpha/' subtree prefix — unresolved as written,
        but resolvable once a concept-subtree prefix is tried, so it must come back
        auto-fixable rather than a plain unfixable phantom."""
        self.write("alpha/sub/note-b.md", "---\nnote_type: knowledge\n---\n")
        p = self.write("beta/a.md", "---\nnote_type: knowledge\n---\n\n[[sub/note-b]]\n")
        fm, body = vault_lint.parse_frontmatter(p.read_text(encoding="utf-8"))
        vault_lint.CONCEPT_SUBTREES = {"alpha", "beta"}
        slug_index = vault_lint.build_slug_index()
        findings = vault_lint.check_c3(p, fm, body, slug_index)
        self.assertEqual(len(findings), 1)
        self.assertTrue(findings[0]["auto_fixable"])


class TestCheckC4(VaultTestCase):
    def test_no_outbound_links_flagged(self):
        p = self.write("alpha/a.md", "---\nnote_type: knowledge\n---\n\nNo links here.\n")
        fm, body = vault_lint.parse_frontmatter(p.read_text(encoding="utf-8"))
        findings = vault_lint.check_c4(p, fm, body)
        self.assertEqual(len(findings), 1)

    def test_hub_note_type_exempt(self):
        p = self.write("alpha/index.md", "---\nnote_type: hub\n---\n\nNo links here.\n")
        fm, body = vault_lint.parse_frontmatter(p.read_text(encoding="utf-8"))
        self.assertEqual(vault_lint.check_c4(p, fm, body), [])

    def test_note_with_link_not_flagged(self):
        p = self.write("alpha/a.md", "---\nnote_type: knowledge\n---\n\n[[alpha/b]]\n")
        fm, body = vault_lint.parse_frontmatter(p.read_text(encoding="utf-8"))
        self.assertEqual(vault_lint.check_c4(p, fm, body), [])


class TestCheckC5(VaultTestCase):
    def test_vault_prefixed_link_flagged_and_fixable(self):
        p = self.write("alpha/a.md", "---\nnote_type: knowledge\n---\n\n[[vault/alpha/b]]\n")
        fm, body = vault_lint.parse_frontmatter(p.read_text(encoding="utf-8"))
        findings = vault_lint.check_c5(p, fm, body)
        self.assertEqual(len(findings), 1)
        self.assertTrue(findings[0]["auto_fixable"])

    def test_unprefixed_link_not_flagged(self):
        p = self.write("alpha/a.md", "---\nnote_type: knowledge\n---\n\n[[alpha/b]]\n")
        fm, body = vault_lint.parse_frontmatter(p.read_text(encoding="utf-8"))
        self.assertEqual(vault_lint.check_c5(p, fm, body), [])


class TestCheckC6(VaultTestCase):
    def test_directory_without_index_flagged(self):
        self.write("alpha/sub/note.md", "---\nnote_type: knowledge\n---\n")
        findings = vault_lint.check_c6({})
        paths = [f["path"] for f in findings]
        self.assertIn("alpha/sub/", paths)

    def test_directory_with_index_not_flagged(self):
        self.write("alpha/index.md", "---\nnote_type: hub\n---\n")
        self.write("alpha/sub/index.md", "---\nnote_type: navigation\n---\n")
        self.write("alpha/sub/note.md", "---\nnote_type: knowledge\n---\n")
        findings = vault_lint.check_c6({})
        self.assertEqual(findings, [])

    def test_graph_directory_exempt(self):
        self.write("_graph/deep/note.md", "---\nnote_type: concept\n---\n")
        findings = vault_lint.check_c6({})
        self.assertEqual(findings, [])


class TestCheckC8(VaultTestCase):
    def setUp(self):
        super().setUp()
        vault_lint.CONCEPT_SUBTREES = {"alpha", "beta"}

    def test_cross_tree_link_flagged(self):
        self.write("beta/target.md", "---\nnote_type: knowledge\n---\n")
        p = self.write("alpha/a.md", "---\nnote_type: knowledge\n---\n\n[[beta/target]]\n")
        fm, body = vault_lint.parse_frontmatter(p.read_text(encoding="utf-8"))
        slug_index = vault_lint.build_slug_index()
        findings = vault_lint.check_c8(p, fm, body, slug_index)
        self.assertEqual(len(findings), 1)

    def test_intra_subtree_link_not_flagged(self):
        self.write("alpha/target.md", "---\nnote_type: knowledge\n---\n")
        p = self.write("alpha/a.md", "---\nnote_type: knowledge\n---\n\n[[alpha/target]]\n")
        fm, body = vault_lint.parse_frontmatter(p.read_text(encoding="utf-8"))
        slug_index = vault_lint.build_slug_index()
        self.assertEqual(vault_lint.check_c8(p, fm, body, slug_index), [])

    def test_graph_source_exempt(self):
        self.write("beta/target.md", "---\nnote_type: knowledge\n---\n")
        p = self.write("_graph/hub.md", "---\nnote_type: concept\n---\n\n[[beta/target]]\n")
        fm, body = vault_lint.parse_frontmatter(p.read_text(encoding="utf-8"))
        slug_index = vault_lint.build_slug_index()
        self.assertEqual(vault_lint.check_c8(p, fm, body, slug_index), [])


class TestCheckC9(VaultTestCase):
    def test_authored_by_me_flagged(self):
        p = self.write("alpha/a.md", "---\nnote_type: knowledge\nauthored_by_me: true\n---\n")
        fm, body = vault_lint.parse_frontmatter(p.read_text(encoding="utf-8"))
        findings = vault_lint.check_c9(p, fm, body)
        self.assertEqual(len(findings), 1)

    def test_owner_me_flagged(self):
        p = self.write("alpha/a.md", "---\nnote_type: knowledge\nowner: me\n---\n")
        fm, body = vault_lint.parse_frontmatter(p.read_text(encoding="utf-8"))
        self.assertEqual(len(vault_lint.check_c9(p, fm, body)), 1)

    def test_author_field_not_flagged(self):
        """Distinct from owner/authored_by_me/mine — author: <name> is legitimate."""
        p = self.write("alpha/a.md", "---\nnote_type: knowledge\nauthor: Jane\n---\n")
        fm, body = vault_lint.parse_frontmatter(p.read_text(encoding="utf-8"))
        self.assertEqual(vault_lint.check_c9(p, fm, body), [])


class TestCheckC13(VaultTestCase):
    """C13 — declared confidence: high vs hedged body prose."""

    def _run(self, rel, content):
        p = self.write(rel, content)
        fm, body = vault_lint.parse_frontmatter(p.read_text(encoding="utf-8"))
        return p, vault_lint.check_c13(p, fm, body)

    def test_high_confidence_with_arguably_flagged(self):
        _, findings = self._run(
            "alpha/a.md",
            "---\nnote_type: knowledge\nconfidence: high\n---\n\nThis arguably matters.\n",
        )
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["check"], "C13")
        self.assertFalse(findings[0]["auto_fixable"])

    def test_high_confidence_with_multiword_phrase_flagged(self):
        _, findings = self._run(
            "alpha/b.md",
            "---\nnote_type: knowledge\nconfidence: high\n---\n\nIt could be argued otherwise.\n",
        )
        self.assertEqual(len(findings), 1)

    def test_medium_confidence_not_flagged(self):
        _, findings = self._run(
            "alpha/c.md",
            "---\nnote_type: knowledge\nconfidence: medium\n---\n\nThis arguably matters.\n",
        )
        self.assertEqual(findings, [])

    def test_no_confidence_field_not_flagged(self):
        _, findings = self._run(
            "alpha/d.md",
            "---\nnote_type: knowledge\n---\n\nThis arguably matters.\n",
        )
        self.assertEqual(findings, [])

    def test_high_confidence_no_hedge_not_flagged(self):
        _, findings = self._run(
            "alpha/e.md",
            "---\nnote_type: knowledge\nconfidence: high\n---\n\nThis is a plain claim.\n",
        )
        self.assertEqual(findings, [])

    def test_external_mirror_with_source_url_excluded(self):
        _, findings = self._run(
            "alpha/f.md",
            "---\nnote_type: vault-note\nconfidence: high\n"
            "source_url: https://example.com/post\n---\n\nThis arguably matters.\n",
        )
        self.assertEqual(findings, [])

    def test_source_url_na_still_flagged(self):
        _, findings = self._run(
            "alpha/g.md",
            "---\nnote_type: vault-note\nconfidence: high\nsource_url: na\n---\n\nArguably so.\n",
        )
        self.assertEqual(len(findings), 1)

    def test_hedge_only_in_frontmatter_not_flagged(self):
        _, findings = self._run(
            "alpha/h.md",
            "---\nnote_type: knowledge\nconfidence: high\nsummary: arguably the best\n---\n\nPlain body.\n",
        )
        self.assertEqual(findings, [])

    def test_apply_fix_refuses_c13_even_when_flag_falsified(self):
        p = self.write(
            "alpha/i.md",
            "---\nnote_type: knowledge\nconfidence: high\n---\n\nThis arguably matters.\n",
        )
        before = p.read_text(encoding="utf-8")
        finding = {"check": "C13", "path": "alpha/i.md",
                   "detail": "confidence: high but body hedges: 'arguably'",
                   "auto_fixable": True}  # deliberately falsified
        changed = vault_lint.apply_fix(finding, {})
        self.assertFalse(changed)
        self.assertEqual(p.read_text(encoding="utf-8"), before)

    def test_registered_in_run_checks(self):
        self.write("alpha/index.md", "---\nnote_type: hub\n---\n")
        self.write("alpha/a.md",
                   "---\nnote_type: knowledge\nconfidence: high\n---\n\nThis arguably matters.\n")
        self.discover()
        findings = vault_lint.run_checks(restrict_check="C13")
        self.assertTrue(findings)
        self.assertTrue(all(f["check"] == "C13" for f in findings))


class TestApplyFix(VaultTestCase):
    def test_c6_creates_index(self):
        self.write("alpha/sub/note.md", "---\nnote_type: knowledge\n---\n")
        finding = {"check": "C6", "path": "alpha/sub/"}
        changed = vault_lint.apply_fix(finding, {})
        self.assertTrue(changed)
        self.assertTrue((self.vault / "alpha" / "sub" / "index.md").exists())

    def test_c6_is_idempotent(self):
        self.write("alpha/sub/note.md", "---\nnote_type: knowledge\n---\n")
        finding = {"check": "C6", "path": "alpha/sub/"}
        vault_lint.apply_fix(finding, {})
        changed_again = vault_lint.apply_fix(finding, {})
        self.assertFalse(changed_again)

    def test_c1_adds_source_url_na(self):
        p = self.write("alpha/a.md", "---\nnote_type: vault-note\n---\n")
        finding = {"check": "C1", "path": "alpha/a.md",
                   "detail": "vault-note missing field: source_url"}
        changed = vault_lint.apply_fix(finding, {})
        self.assertTrue(changed)
        self.assertIn("source_url: na", p.read_text(encoding="utf-8"))

    def test_c5_strips_vault_prefix(self):
        p = self.write("alpha/a.md", "---\nnote_type: knowledge\n---\n\n[[vault/alpha/b]]\n")
        finding = {"check": "C5", "path": "alpha/a.md",
                   "detail": "vault/-prefixed wikilink [[vault/alpha/b]] (location: body)"}
        changed = vault_lint.apply_fix(finding, {})
        self.assertTrue(changed)
        text = p.read_text(encoding="utf-8")
        self.assertIn("[[alpha/b]]", text)
        self.assertNotIn("[[vault/alpha/b]]", text)


class TestRunChecks(VaultTestCase):
    def test_smoke_across_a_small_vault(self):
        self.write("alpha/index.md", "---\nnote_type: hub\n---\n")
        self.write("alpha/a.md", "---\nnote_type: knowledge\n---\n\n[[alpha/nonexistent]]\n")
        self.discover()
        findings = vault_lint.run_checks()
        checks_seen = {f["check"] for f in findings}
        self.assertIn("C3", checks_seen, "the phantom link in alpha/a.md must surface")

    def test_restrict_check_limits_to_one_id(self):
        self.write("alpha/index.md", "---\nnote_type: hub\n---\n")
        self.write("alpha/a.md", "---\nnote_type: knowledge\n---\n\n[[alpha/nonexistent]]\n")
        self.discover()
        findings = vault_lint.run_checks(restrict_check="C4")
        self.assertTrue(all(f["check"] == "C4" for f in findings))


if __name__ == "__main__":
    os.environ.setdefault("WORKSPACE_ROOT", str(Path(__file__).resolve().parent.parent))
    unittest.main(verbosity=2)
