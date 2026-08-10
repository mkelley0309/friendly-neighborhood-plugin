#!/usr/bin/env python3
"""build/generate.py — plan 3.5 generator.

Reads canonical `src/` + `vocabulary/{data-model,display}.yml` +
`editions/{core,lite,full}.yml` + `build/phase-council.yml`, and emits each
edition into `build/_generated/{plugin-name}/`.

Does NOT touch `plugins/*` — that tree is the byte-reproduction reference
target for step 3.6, read-only from here.

See `build/README.md` for the marker convention and known gaps.
"""
from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
OUT_ROOT = ROOT / "build" / "_generated"
EDITIONS_DIR = ROOT / "editions"
VOCAB_DIR = ROOT / "vocabulary"

EDITION_NAMES = ["core", "lite", "full"]


def load_yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def die(msg: str) -> None:
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


# ── Marker-block stripping (shell/python "# FEATURE:x:start/:end", markdown
#    "<!-- FEATURE:x:start/end -->") ─────────────────────────────────────────

# Strip exactly the marker lines and everything between (nothing more, nothing
# less). Where the surrounding blank-line spacing needs to differ between the
# kept and dropped cases (e.g. a block that sits between two blank lines when
# present, but should collapse to a single blank line when absent), the blank
# line lives as the BODY's own first line inside the markers rather than
# outside them — see src/scripts/fn-session-start.sh and fn-common.sh for the
# two concrete cases (documented in build/README.md).
MARKER_RE_SH = re.compile(
    r"[ \t]*# FEATURE:(\w+):start[ \t]*\n(.*?)[ \t]*# FEATURE:\1:end[ \t]*\n?",
    re.DOTALL,
)
MARKER_RE_MD = re.compile(
    r"[ \t]*<!-- FEATURE:(\w+):start -->[ \t]*\n(.*?)<!-- FEATURE:\1:end -->[ \t]*\n?",
    re.DOTALL,
)


def strip_markers(text: str, features: dict, marker_re: re.Pattern) -> str:
    """Remove marker blocks whose named feature is falsy; unwrap (keep content,
    drop the marker lines) the ones that are truthy. `features` truthiness for
    `doctrine_skills` is "list non-empty"; everything else is a plain bool.
    """

    def feature_on(name: str) -> bool:
        val = features.get(name, False)
        if isinstance(val, list):
            return len(val) > 0
        return bool(val)

    def repl(m: re.Match) -> str:
        name, body = m.group(1), m.group(2)
        return body if feature_on(name) else ""

    # Nested markers of the SAME name don't occur; different names can nest
    # (observation_deck inside doctrine_skills in fn-subagent-stop.sh), so run
    # repeatedly until stable.
    prev = None
    while prev != text:
        prev = text
        text = marker_re.sub(repl, text)
    return text


# ── Vocabulary substitution ─────────────────────────────────────────────────


def case_like(sample: str, word: str) -> str:
    if sample.isupper():
        return word.upper()
    if sample[:1].isupper():
        return word[:1].upper() + word[1:]
    return word


def pluralize(word: str) -> str:
    if word.endswith("y") and word[-2:-1] not in "aeiou":
        return word[:-1] + "ies"
    return word + "s"


def fix_articles(text: str, target_words: set[str]) -> str:
    """Fix 'a'/'an' immediately before one of our just-substituted target
    words (mission, campaign, responsibility, patrol, ...) whose leading
    sound flips relative to the core word it replaced (assignment -> mission
    is the concrete case: vowel-leading -> consonant-leading). Scoped to a
    known word list rather than a blanket grammar fixer, so it never touches
    unrelated prose the substitution pass didn't produce.
    """
    if not target_words:
        return text
    alt = "|".join(re.escape(w) for w in sorted(target_words, key=len, reverse=True))
    pattern = re.compile(rf"\b(an?)\s+({alt})\b", re.IGNORECASE)

    def repl(m: re.Match) -> str:
        article, word = m.group(1), m.group(2)
        needs_an = bool(re.match(r"^[aeiouAEIOU]", word))
        correct = "an" if needs_an else "a"
        if article.lower() == correct:
            return m.group(0)
        fixed = correct.capitalize() if article[0].isupper() else correct
        return f"{fixed} {word}"

    return pattern.sub(repl, text)


class Vocab:
    """Builds and applies the display-vocabulary substitution for one edition."""

    def __init__(self, data_model: dict, display: dict, edition: dict):
        self.data_model = data_model
        self.display = display
        self.edition = edition
        self.display_axis = edition["display"]  # 'none' | 'spider-man'
        self.themed = self.display_axis != "none"
        self.plugin_name = edition["plugin"]["name"]

        # non-pinned tiers (assignment, cadence): full identifier swap, safe
        # to apply unconditionally including folder/frontmatter/cli contexts.
        self.nonpinned_pairs = []  # (core_word, edition_word)
        for tier, spec in data_model["tiers"].items():
            if spec.get("pinned"):
                continue
            core_id = spec["identifier"]
            ed_key = "core" if self.display_axis == "none" else (
                "lite" if edition["roster"] == 7 else "full"
            )
            # editions map's own identifier IS the frontmatter_key/folder/cli
            # base word (folder/cli/frontmatter_key share one word per tier).
            ed_word = spec["editions"][ed_key]["frontmatter_key"]
            if core_id != ed_word:
                self.nonpinned_pairs.append((core_id, ed_word))

        # pinned tiers (objective, workstream): prose-only swap, core word ->
        # themed display word, guarded against folder/cli/frontmatter-key use.
        self.pinned_pairs = []  # (core_word, themed_word)
        if self.themed:
            for tier, spec in data_model["tiers"].items():
                if not spec.get("pinned"):
                    continue
                disp = display["tiers"][tier]
                if disp["core"] != disp["themed"]:
                    self.pinned_pairs.append((disp["core"], disp["themed"]))

        # non-tier skill renames (init-workspace/knowledge), narrow patterns
        # only. Populated in BOTH directions regardless of display axis:
        # `src/skills/{init-workspace,knowledge}/` is sourced from core (see
        # src/README.md), so themed editions need core-name -> themed-name;
        # `src/scripts/*` is sourced from full (already themed-named), so
        # core needs the REVERSE, themed-name -> core-name. `apply()` below
        # picks the direction per self.themed.
        self.skill_pairs = []  # (core_name, themed_name)
        for _skill, disp in display["skills"].items():
            if disp["core"] != disp["themed"]:
                self.skill_pairs.append((disp["core"], disp["themed"]))

    # -- pinned-tier guarded prose substitution --
    def _sub_pinned_word(self, text: str, core_word: str, themed_word: str) -> str:
        # Match singular or plural, case-insensitive, word-boundary.
        pattern = re.compile(rf"(?<![\w/\"]){re.escape(core_word)}(s)?\b", re.IGNORECASE)

        def repl(m: re.Match) -> str:
            match_text = m.group(0)
            plural = m.group(1) is not None
            start, end = m.span()
            # Guard: frontmatter-key pattern "word:" at start of a line.
            line_start = text.rfind("\n", 0, start) + 1
            if text[start:end + 1].endswith(":") and text[line_start:start] == "":
                return match_text
            # Guard: frontmatter-key pattern shown inline as an example,
            # e.g. "Frontmatter: `note_type: ...`, `workstream: {name}`,
            # `tags: ...`" — backtick immediately before, colon immediately
            # after. Same intent as the line-start guard above but for a key
            # example quoted inline rather than in a fenced code block.
            if start > 0 and text[start - 1] == "`" and end < len(text) and text[end] == ":":
                return match_text
            # Guard: immediately followed by ".py" (CLI filename).
            if text[end:end + 3] == ".py":
                return match_text
            # Guard: immediately followed by "-" (compound identifier, e.g.
            # `note_type: workstream-plan` — a pinned value, not prose) —
            # EXCEPT a `{word-name}` placeholder token, which is ordinary
            # prose describing a naming convention and should substitute
            # (e.g. `{workstream-name}` -> `{campaign-name}`).
            if end < len(text) and text[end] == "-" and not (start > 0 and text[start - 1] == "{"):
                return match_text
            # Guard: bare quoted literal "word" or "words" (path/key literal).
            if start > 0 and text[start - 1] == '"' and end < len(text) and text[end] == '"':
                return match_text
            # Guard: immediately followed by "/" — a bare folder-name usage
            # (e.g. an ASCII tree listing "  objectives/   <- comment"), as
            # opposed to preceded by "/" (already guarded above via the
            # pattern's lookbehind) for a path like "control-plane/objectives/".
            if end < len(text) and text[end] == "/":
                return match_text
            repl_word = pluralize(themed_word) if plural else themed_word
            return case_like(match_text, repl_word)

        return pattern.sub(repl, text)

    def apply_nonpinned(self, text: str) -> str:
        """Full identifier swap — no guards: non-pinned tiers (assignment,
        cadence) change their folder/CLI/frontmatter-key identically
        everywhere, including bare path segments and `.py` filenames
        (assignment.py -> mission.py, templates/control-plane/assignments/ ->
        .../missions/). Safe to run on a path segment string, not just prose —
        a path never carries the "cadence" counter-landmine ambiguity below.
        """
        for core_word, ed_word in self.nonpinned_pairs:
            pattern = re.compile(rf"\b{re.escape(core_word)}(s)?\b", re.IGNORECASE)
            text = pattern.sub(
                lambda m, w=ed_word: case_like(m.group(0), pluralize(w) if m.group(1) else w),
                text,
            )
        return text

    def _apply_nonpinned_guarded(self, text: str, core_word: str, ed_word: str) -> str:
        """Same swap as apply_nonpinned, but for PROSE BODY content, with
        guards for `cadence` specifically — vocabulary/data-model.yml's
        documented counter-landmine: the bare word also names an UNRELATED
        objective/responsibility frontmatter field (review frequency), which
        must never become `patrol`. Guards cover the confirmed cases (see
        build/README.md "Known gaps — the cadence counter-landmine"):
        `review cadence`, a bare `cadence:` frontmatter key, `set-cadence`/
        `<cadence>` CLI-example tokens, and `milestones, cadence` listings.
        Residual risk is real and documented, not fully eliminated.
        """
        if core_word != "cadence":
            pattern = re.compile(rf"\b{re.escape(core_word)}(s)?\b", re.IGNORECASE)
            return pattern.sub(
                lambda m, w=ed_word: case_like(m.group(0), pluralize(w) if m.group(1) else w),
                text,
            )

        pattern = re.compile(r"\bcadence(s)?\b", re.IGNORECASE)

        def repl(m: re.Match) -> str:
            match_text = m.group(0)
            start, end = m.span()
            before = text[max(0, start - 12):start]
            after = text[end:end + 1]
            line_start = text.rfind("\n", 0, start) + 1
            if text[line_start:start] == "" and after == ":":
                return match_text  # bare frontmatter key -> unrelated field
            if re.search(r"review\s*$", before, re.IGNORECASE):
                return match_text  # "(a) review cadence"
            if re.search(r"(set-|milestones,\s*)$", before, re.IGNORECASE):
                return match_text  # "set-cadence" CLI token / "milestones, cadence" list
            if before.endswith("<") and after == ">":
                return match_text  # "<cadence>" bare CLI-example placeholder
            plural = m.group(1) is not None
            repl_word = pluralize(ed_word) if plural else ed_word
            return case_like(match_text, repl_word)

        return pattern.sub(repl, text)

    def apply(self, text: str, skip_nonpinned: frozenset = frozenset()) -> str:
        """`skip_nonpinned` lets a caller exempt an entire file from a
        specific non-pinned tier's substitution — used for
        `templates/tools/objective.py`, which (confirmed empirically, see
        build/README.md) uses "cadence" EXCLUSIVELY for the unrelated
        review-frequency field, never the tier; the per-occurrence guards in
        `_apply_nonpinned_guarded` don't reliably cover dense code contexts
        (dict keys, f-strings, variable names), so that file gets a wholesale
        exemption instead of relying on the guards alone.
        """
        target_words = set()
        for core_word, ed_word in self.nonpinned_pairs:
            if core_word in skip_nonpinned:
                continue
            target_words.add(ed_word)
            target_words.add(pluralize(ed_word))
            text = self._apply_nonpinned_guarded(text, core_word, ed_word)
        for core_word, themed_word in self.pinned_pairs:
            text = self._sub_pinned_word(text, core_word, themed_word)
            target_words.add(themed_word)
            target_words.add(pluralize(themed_word))
        text = fix_articles(text, target_words)
        # narrow skill self-reference patterns — direction depends on which
        # way this edition needs to go (see skill_pairs comment above).
        for core_name, themed_name in self.skill_pairs:
            frm, to = (core_name, themed_name) if self.themed else (themed_name, core_name)
            text = re.sub(rf"(name:\s*){re.escape(frm)}\b", lambda m, t=to: m.group(1) + t, text)
            text = re.sub(rf"(# Skill:\s*){re.escape(frm)}\b", lambda m, t=to: m.group(1) + t, text)
            text = re.sub(rf"(/[\w.-]+:){re.escape(frm)}\b", lambda m, t=to: m.group(1) + t, text)
            # bare backtick-quoted self-reference, e.g. "the `origin-story` skill"
            text = re.sub(rf"`{re.escape(frm)}`", f"`{to}`", text)
            if self.themed and core_name == "knowledge":
                text = text.replace("Manage the knowledge pipeline", "Manage the web-archive pipeline")
            elif not self.themed and core_name == "knowledge":
                text = text.replace("Manage the web-archive pipeline", "Manage the knowledge pipeline")
            if self.themed and core_name == "init-workspace":
                text = text.replace("# init-workspace — scaffold your workspace", "# Origin Story — scaffold your workspace")
            elif not self.themed and core_name == "init-workspace":
                text = text.replace("# Origin Story — scaffold your workspace", "# init-workspace — scaffold your workspace")
        # plugin-slug substitution for doctrine/tier skill self-refs copied from full
        if self.plugin_name != "friendly-neighborhood":
            text = text.replace("/friendly-neighborhood:", f"/{self.plugin_name}:")
        return text


# ── File-tree helpers ───────────────────────────────────────────────────────


def copy_file_substituted(src: Path, dst: Path, vocab: Vocab, marker_features: dict | None = None):
    dst.parent.mkdir(parents=True, exist_ok=True)
    try:
        text = src.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        shutil.copy2(src, dst)
        return
    text = vocab.apply(text)
    if marker_features is not None:
        if src.suffix == ".md":
            text = strip_markers(text, marker_features, MARKER_RE_MD)
        else:
            text = strip_markers(text, marker_features, MARKER_RE_SH)
    dst.write_text(text, encoding="utf-8", newline="\n")


def copy_tree_substituted(src_dir: Path, dst_dir: Path, vocab: Vocab, marker_features: dict | None = None,
                           skip_names=("__pycache__",)):
    for root, dirs, files in list_walk(src_dir, skip_names):
        rel = Path(root).relative_to(src_dir)
        for name in files:
            copy_file_substituted(Path(root) / name, dst_dir / rel / name, vocab, marker_features)


def list_walk(src_dir: Path, skip_names):
    import os
    for root, dirs, files in os.walk(src_dir):
        dirs[:] = [d for d in dirs if d not in skip_names]
        yield root, dirs, files


# ── Tier skill directory rename ─────────────────────────────────────────────

TIER_SRC_DIRS = {
    "objective": SRC / "skills" / "objective",
    "workstream": SRC / "skills" / "workstream",
    "assignment": SRC / "skills" / "assignment",
    "cadence": SRC / "skills" / "cadence",
}


def tier_dest_name(tier: str, vocab: Vocab, data_model: dict, display: dict) -> str:
    spec = data_model["tiers"][tier]
    if spec.get("pinned"):
        return display["tiers"][tier]["themed"] if vocab.themed else tier
    ed_key = "core" if not vocab.themed else ("lite" if vocab.edition["roster"] == 7 else "full")
    return spec["editions"][ed_key]["frontmatter_key"]


def inject_phase_council(text: str, filename: str, roster_key: str, phase_council: dict) -> str:
    entry = phase_council.get("workstream", {}).get(filename)
    if not entry or roster_key not in entry:
        return text
    line = entry[roster_key]
    # Insert right after the H1 title + its trailing blank line.
    m = re.match(r"(# [^\n]*\n\n)", text)
    if not m:
        return text
    insert_at = m.end()
    return text[:insert_at] + line + "\n\n" + text[insert_at:]


def build_tier_skills(edition: dict, vocab: Vocab, data_model: dict, display: dict,
                       phase_council: dict, skills_dest: Path):
    roster = edition["roster"]
    roster_key = "lite" if roster == 7 else ("full" if roster == 32 else None)
    for tier, src_dir in TIER_SRC_DIRS.items():
        dest_name = tier_dest_name(tier, vocab, data_model, display)
        dest_dir = skills_dest / dest_name
        for root, _dirs, files in list_walk(src_dir, ("__pycache__",)):
            rel = Path(root).relative_to(src_dir)
            for name in files:
                src_file = Path(root) / name
                dst_file = dest_dir / rel / name
                dst_file.parent.mkdir(parents=True, exist_ok=True)
                text = src_file.read_text(encoding="utf-8")
                # objective/*'s "cadence" is confirmed (build/README.md) to
                # be exclusively the unrelated review-frequency field within
                # this tier's own skill files, never the cadence/patrol tier.
                skip_nonpinned = frozenset({"cadence"}) if tier == "objective" else frozenset()
                text = vocab.apply(text, skip_nonpinned=skip_nonpinned)
                if (
                    tier == "workstream"
                    and edition["features"].get("phase_council")
                    and roster_key
                    and rel == Path("actions")
                ):
                    text = inject_phase_council(text, name, roster_key, phase_council)
                dst_file.write_text(text, encoding="utf-8", newline="\n")


# ── Non-tier skills (init-workspace/knowledge) ──────────────────────────────

NONTIER_SRC_DIRS = {
    "init-workspace": SRC / "skills" / "init-workspace",
    "knowledge": SRC / "skills" / "knowledge",
}


def build_nontier_skills(edition: dict, vocab: Vocab, display: dict, skills_dest: Path):
    for skill, src_dir in NONTIER_SRC_DIRS.items():
        disp = display["skills"][skill]
        dest_name = disp["themed"] if vocab.themed else disp["core"]
        copy_tree_substituted(src_dir, skills_dest / dest_name, vocab)


# ── Themed-only doctrine skills ─────────────────────────────────────────────

DOCTRINE_SRC_DIRS = {
    name: SRC / "skills" / name for name in ("church-bell", "creed", "spider-sense", "symbiote")
}


def build_doctrine_skills(edition: dict, vocab: Vocab, skills_dest: Path):
    wanted = set(edition["features"].get("doctrine_skills") or [])
    for name, src_dir in DOCTRINE_SRC_DIRS.items():
        if name in wanted:
            copy_tree_substituted(src_dir, skills_dest / name, vocab)


# ── Agents ───────────────────────────────────────────────────────────────────


def build_agents(edition: dict, vocab: Vocab, display: dict, dest_root: Path):
    roster = edition["roster"]
    if roster == 0:
        return
    names = display["roster"]["lite"] if roster == 7 else display["roster"]["full"]
    agents_src = SRC / "agents"
    dest = dest_root / "agents"
    for name in names:
        src_file = agents_src / f"{name}.md"
        if not src_file.exists():
            print(f"  warning: agent '{name}' listed in roster but missing at {src_file}", file=sys.stderr)
            continue
        copy_file_substituted(src_file, dest / f"{name}.md", vocab)


# ── Scripts ──────────────────────────────────────────────────────────────────


def build_scripts(edition: dict, vocab: Vocab, dest_root: Path):
    src_dir = SRC / "scripts"
    dest = dest_root / "scripts"
    features = edition["features"]
    for f in src_dir.iterdir():
        if f.is_file():
            copy_file_substituted(f, dest / f.name, vocab, marker_features=features)


# ── Templates ────────────────────────────────────────────────────────────────


def build_templates(edition: dict, vocab: Vocab, display: dict, dest_root: Path):
    src_dir = SRC / "templates"
    dest = dest_root / "templates"
    features = edition["features"]
    folder_disp = display["folders"]["personal"]

    for root, dirs, files in list_walk(src_dir, ("__pycache__",)):
        root_path = Path(root)
        rel = root_path.relative_to(src_dir)
        if rel.parts[:1] == (".vscode",) and not features.get("vscode_workspace"):
            dirs[:] = []
            continue
        # rename templates/personal/ -> templates/secret-identity/ for themed
        rel_parts = list(rel.parts)
        if vocab.themed and rel_parts and rel_parts[0] == "personal":
            rel_parts[0] = folder_disp["themed"]
        # non-pinned tier folder rename (assignments->missions, cadences->patrols)
        # applies to EVERY path segment, everywhere under templates/ — not just
        # control-plane/ — since it's the same identifier swap as the CLI
        # filename and frontmatter key (data-model.yml `pinned: false`).
        rel_parts = [vocab.apply_nonpinned(part) for part in rel_parts]
        rel_dest = Path(*rel_parts) if rel_parts else Path(".")
        for name in files:
            src_file = root_path / name
            # rename .claude/rules/personal.md -> secret-identity.md for themed
            dest_name = name
            if vocab.themed and rel.parts == (".claude", "rules") and name == "personal.md":
                dest_name = f"{folder_disp['themed']}.md"
            dest_name = vocab.apply_nonpinned(dest_name)
            dst_file = dest / rel_dest / dest_name

            if name == "settings.json":
                build_settings_json(src_file, dst_file, vocab, features)
                continue

            marker_features = features if src_file.suffix in (".py", ".sh") else None
            text = None
            try:
                text = src_file.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                dst_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_file, dst_file)
                continue
            skip_nonpinned = frozenset({"cadence"}) if (rel.parts == ("tools",) and name == "objective.py") else frozenset()
            text = vocab.apply(text, skip_nonpinned=skip_nonpinned)
            if marker_features is not None:
                text = strip_markers(text, marker_features, MARKER_RE_SH)
            if vocab.themed and rel.parts == (".claude", "rules") and name == "personal.md":
                text = text.replace('paths: ["personal/**"]', f'paths: ["{folder_disp["themed"]}/**"]')
            dst_file.parent.mkdir(parents=True, exist_ok=True)
            dst_file.write_text(text, encoding="utf-8", newline="\n")


def build_settings_json(src_file: Path, dst_file: Path, vocab: Vocab, features: dict):
    data = json.loads(src_file.read_text(encoding="utf-8"))
    allow = data["permissions"]["allow"]
    # apply non-pinned CLI-filename substitution (assignment.py -> mission.py etc.)
    allow = [vocab.apply(a) for a in allow]
    if not features.get("observation_deck"):
        allow = [a for a in allow if "agent-log.sh" not in a and "observe.sh" not in a]
    data["permissions"]["allow"] = allow
    dst_file.parent.mkdir(parents=True, exist_ok=True)
    dst_file.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


# ── Output styles ────────────────────────────────────────────────────────────


def build_output_styles(edition: dict, vocab: Vocab, dest_root: Path):
    if not edition["features"].get("output_style"):
        return
    src_dir = SRC / "output-styles"
    dest = dest_root / "output-styles"
    features = edition["features"]
    for f in src_dir.iterdir():
        if f.is_file():
            copy_file_substituted(f, dest / f.name, vocab, marker_features=features)


# ── Themes ───────────────────────────────────────────────────────────────────


def build_themes(edition: dict, dest_root: Path):
    if not edition["features"].get("themes"):
        return
    shutil.copytree(SRC / "themes", dest_root / "themes", dirs_exist_ok=True)


# ── Hooks ────────────────────────────────────────────────────────────────────


def build_hooks(dest_root: Path):
    dest = dest_root / "hooks"
    dest.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SRC / "hooks" / "hooks.json", dest / "hooks.json")


# ── plugin.json ──────────────────────────────────────────────────────────────


def build_plugin_json(edition: dict, dest_root: Path):
    plugin = edition["plugin"]
    existing_path = ROOT / "plugins" / plugin["name"] / ".claude-plugin" / "plugin.json"
    base = {}
    if existing_path.exists():
        base = json.loads(existing_path.read_text(encoding="utf-8"))
    base["name"] = plugin["name"]
    base["displayName"] = plugin["displayName"]
    base["description"] = " ".join(plugin["description"].split())
    dest = dest_root / ".claude-plugin"
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "plugin.json").write_text(json.dumps(base, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


# ── scaffold.py bespoke "Next:" block (core's onboarding copy is genuinely
#    bespoke prose, not derivable from the themed template by any marker —
#    see build/README.md) ────────────────────────────────────────────────────

def build_scripts_scaffold_special(edition: dict, vocab: Vocab, dest_root: Path):
    """scaffold.py needs bespoke core handling beyond generic marker stripping
    (see build/README.md) — handled here as a small override after the generic
    copy_file_substituted / marker pass already ran in build_scripts.
    """
    dst = dest_root / "scripts" / "scaffold.py"
    if not dst.exists():
        return
    text = dst.read_text(encoding="utf-8")
    if edition["display"] == "none":
        text = text.replace(
            'print(f"\\n  Friendly Neighborhood - workspace scaffolded into: {dst}\\n")',
            'print(f"\\n  Harness Core - workspace scaffolded into: {dst}\\n")',
        )
        # Replace the whole Next-steps print(...) call body with core's literal copy.
        pattern = re.compile(r'print\(\s*"\\n  Next:\\n".*?\)\n', re.DOTALL)
        replacement = (
            "print(\n"
            '        "\\n  Next:\\n"\n'
            '        "    1. Open constitution.md - the base contract.\\n"\n'
            '        "    2. The subtree contracts auto-load via .claude/rules/ when you work in each area.\\n"\n'
            '        "    3. Start work: /harness-core:workstream (a complex effort), "\n'
            '        "/harness-core:objective (a long-lived goal), "\n'
            '        "/harness-core:assignment (a lightweight unit), "\n'
            '        "or /harness-core:knowledge (knowledge pipeline).\\n"\n'
            "    )\n"
        )
        # NB: use a replacement function, not a string — re.sub's string-template
        # path interprets `\n` etc. as escapes and would corrupt the literal
        # `\n` sequences the generated .py source needs to contain.
        text = pattern.sub(lambda _m: replacement, text, count=1)
    dst.write_text(text, encoding="utf-8", newline="\n")


# ── Main per-edition build ──────────────────────────────────────────────────


def build_edition(name: str, data_model: dict, display: dict, phase_council: dict):
    edition = load_yaml(EDITIONS_DIR / f"{name}.yml")
    vocab = Vocab(data_model, display, edition)
    dest_root = OUT_ROOT / edition["plugin"]["name"]
    if dest_root.exists():
        shutil.rmtree(dest_root)
    dest_root.mkdir(parents=True)

    skills_dest = dest_root / "skills"
    build_tier_skills(edition, vocab, data_model, display, phase_council, skills_dest)
    build_nontier_skills(edition, vocab, display, skills_dest)
    build_doctrine_skills(edition, vocab, skills_dest)
    build_agents(edition, vocab, display, dest_root)
    build_scripts(edition, vocab, dest_root)
    build_scripts_scaffold_special(edition, vocab, dest_root)
    build_templates(edition, vocab, display, dest_root)
    build_output_styles(edition, vocab, dest_root)
    build_themes(edition, dest_root)
    build_hooks(dest_root)
    build_plugin_json(edition, dest_root)

    print(f"  built {edition['plugin']['name']} -> {dest_root.relative_to(ROOT)}")


def main():
    data_model = load_yaml(VOCAB_DIR / "data-model.yml")
    display = load_yaml(VOCAB_DIR / "display.yml")
    phase_council = load_yaml(ROOT / "build" / "phase-council.yml")

    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    for name in EDITION_NAMES:
        build_edition(name, data_model, display, phase_council)
    print("generate.py: done")


if __name__ == "__main__":
    main()
