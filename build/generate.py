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
            # Guard: Python attribute access, e.g. `args.workstream` — the
            # matching argparse `add_argument("workstream", ...)` dest string
            # is already protected by the quoted-literal guard above, so
            # substituting the attribute-access form alone would desync the
            # two and raise AttributeError at runtime. Prose never has a
            # pinned word immediately preceded by "." with no space (a
            # sentence-final period is always followed by whitespace).
            if start > 0 and text[start - 1] == ".":
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

        Boundary is letters-only (not `\\b`, which treats `_` as a word char
        and so refuses to match inside `assignment_dir`/`ASSIGNMENTS_DIR`/
        `cadence_dir`/`CADENCES_DIR` — exactly the compound Python identifiers
        these tools use). A pinned word is never substituted here at all, so
        this boundary choice can't leak into pinned-tier code identifiers.
        """
        for core_word, ed_word in self.nonpinned_pairs:
            pattern = re.compile(rf"(?<![a-zA-Z]){re.escape(core_word)}(s)?(?![a-zA-Z])", re.IGNORECASE)
            text = pattern.sub(
                lambda m, w=ed_word: case_like(m.group(0), pluralize(w) if m.group(1) else w),
                text,
            )
        return text

    def _apply_nonpinned_guarded(self, text: str, core_word: str, ed_word: str,
                                  own_tier_file: bool = False) -> str:
        """Same swap as apply_nonpinned, but for PROSE BODY content, with
        guards for `cadence` specifically — vocabulary/data-model.yml's
        documented counter-landmine: the bare word also names an UNRELATED
        objective/responsibility frontmatter field (review frequency), which
        must never become `patrol`. Guards cover the confirmed cases (see
        build/README.md "Known gaps — the cadence counter-landmine"):
        `review cadence`, a bare `cadence:` frontmatter key, `set-cadence`/
        `<cadence>` CLI-example tokens, and `milestones, cadence` listings.
        Residual risk is real and documented, not fully eliminated.

        `own_tier_file`: True when processing the cadence tier's OWN home
        file (`templates/tools/cadence.py`) — there, a bare `cadence:` line
        is the tier's own identity field (must become `patrol:`), not the
        unrelated review-frequency field the guard below exists to protect.
        Same letters-only boundary as `apply_nonpinned`, for the same
        compound-identifier reason (`cadence_dir`, `CADENCES_DIR`).
        """
        if core_word != "cadence":
            pattern = re.compile(rf"(?<![a-zA-Z]){re.escape(core_word)}(s)?(?![a-zA-Z])", re.IGNORECASE)
            return pattern.sub(
                lambda m, w=ed_word: case_like(m.group(0), pluralize(w) if m.group(1) else w),
                text,
            )

        pattern = re.compile(r"(?<![a-zA-Z])cadence(s)?(?![a-zA-Z])", re.IGNORECASE)

        def repl(m: re.Match) -> str:
            match_text = m.group(0)
            start, end = m.span()
            before = text[max(0, start - 12):start]
            after = text[end:end + 1]
            line_start = text.rfind("\n", 0, start) + 1
            if not own_tier_file and text[line_start:start] == "" and after == ":":
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

    def apply(self, text: str, skip_nonpinned: frozenset = frozenset(), own_tier_file: bool = False) -> str:
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
            text = self._apply_nonpinned_guarded(
                text, core_word, ed_word,
                own_tier_file=(own_tier_file and core_word == "cadence"),
            )
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
        # symmetric case: pinned-tier + knowledge/init-workspace skill files are
        # sourced from harness-core (src/README.md provenance table) and hardcode
        # `/harness-core:` as their own slash-command prefix — themed editions
        # need that rewritten to their own plugin slug, and the bare "harness-core"
        # plugin-name mention in prose (e.g. "harness-core needs Python 3...")
        # rewritten to the edition's own displayName. Without this, themed output
        # ships `/harness-core:campaign` (wrong plugin, right skill name).
        if self.themed and self.plugin_name != "harness-core":
            text = text.replace("/harness-core:", f"/{self.plugin_name}:")
            text = re.sub(r"(?<![\w/-])harness-core(?![\w-])", self.edition["plugin"]["displayName"], text)
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


# ── Phase council (plan 4b.2) ───────────────────────────────────────────────
# Generates the "> **Phase council** ..." line injected into each
# workstream-tier action file from lens/register `phases:` frontmatter (role
# per phase) + roster membership, replacing the old mechanism that read two
# flat, pre-formatted strings straight out of build/phase-council.yml (one
# per roster, no shared derivation).
#
# What's genuinely DERIVED vs kept STATIC here — see build/README.md
# "Phase council generation" for the full rationale, condensed:
#  - Counsel/watch NAME MEMBERSHIP + ORDER + inline annotation for both
#    rosters are kept as static tables (PHASE_COUNCIL_FULL / _LITE) below,
#    extracted verbatim from build/phase-council.yml. Order and annotation
#    text are hand-authored prose, confirmed non-formulaic (design.md and
#    plan.md list the identical 4 watch villains in different orders; lite's
#    3 villains get reused across phases far outside any one villain's own
#    frontmatter — `kingpin` watches `questions` despite `questions` not
#    being in kingpin's own `phases:`). A naive "any roster member whose
#    frontmatter phase+role matches" filter also can't be used for full
#    without regressing byte-reproduction: it would newly pull in
#    scorpion/venom/ham/punk (four lenses added this same step, now carrying
#    their own `phases:` frontmatter) into phases they were never routed to.
#  - Driver clause + trailer sentence (both editions): static prose
#    (DRIVER/TRAILER embedded per phase) — "driver" vs "drivers", "/" vs ","
#    separators, inline routing notes have no roster-membership logic to
#    derive from.
#  - What IS genuinely wired to frontmatter: validate_phase_council_tables()
#    (called once from main()) cross-checks every non-delegation name in
#    PHASE_COUNCIL_FULL against that character's own lens/register `phases:`
#    frontmatter, and every PHASE_COUNCIL_LITE name against
#    vocabulary/display.yml's roster.lite — so an edit to a lens file's role,
#    or a roster change, that drifts out of sync with these tables fails the
#    build loudly instead of silently reproducing a stale line.
#  - The `/{plugin-slug}:creed` reference is now built from the edition's own
#    `plugin.name` at render time instead of being baked into the stored
#    string — removes the COUPLING CAVEAT build/phase-council.yml used to
#    document (a second roster-7 or roster-32 edition under a different
#    plugin name no longer needs its own copy of these strings).

PHASE_QRDPIV = {
    "questions.md": "Q",
    "research.md": "R",
    "design.md": "D",
    "plan.md": "P",
    "implement.md": "I",
    "validate.md": "V",
    "cleanup.md": "Cleanup",
}

# Delegations (real subagents, not lens/register carriers — see plan 4b.2
# framing) that appear as driver/counsel in phase-council lines. Skipped by
# validate_phase_council_tables()'s frontmatter cross-check since they carry
# no `phases:` frontmatter by design (scoped by tools:/disallowedTools:).
DELEGATION_NAMES = frozenset({"silk", "noir", "miguel", "gwen", "ned"})

PHASE_COUNCIL_FULL = {
    "questions.md": {
        "driver": "driver `peter`",
        "counsel": [("robbie", "constructive design questions"),
                    ("jameson", "devil's-advocate grilling of poorly-shaped work"),
                    ("mj", None), ("aunt-may", None)],
        "watch": [("sandman", "under-shaped/formless work"), ("kraven", None), ("osborn", None)],
        "trailer": "",
    },
    "research.md": {
        "driver": "drivers `silk` (recall/docs/codebase), `noir` (investigation)",
        "counsel": [("aunt-may", None), ("ned", None), ("madame-web", None)],
        "watch": [("lizard", None), ("vulture", None), ("kraven", None), ("kingpin", None)],
        "trailer": "",
    },
    "design.md": {
        "driver": "driver `miguel`",
        "counsel": [("uncle-ben", None), ("aunt-may", None), ("mj", None), ("madame-web", None)],
        "watch": [("octavius", None), ("vulture", None), ("kraven", None), ("kingpin", None)],
        "trailer": "",
    },
    "plan.md": {
        "driver": "driver `miguel`",
        "counsel": [("uncle-ben", None), ("aunt-may", None), ("madame-web", None)],
        "watch": [("octavius", None), ("kraven", None), ("kingpin", None), ("vulture", None)],
        "trailer": "",
    },
    "implement.md": {
        "driver": "driver `peter` / `miles` (route each step to the right Spider-variant — see Delegation)",
        "counsel": [("ned", None)],
        "watch": [("carnage", None), ("cat", "security"), ("rhino", None), ("osborn", None)],
        "trailer": " Functional validation happens in `validate` — `gwen` drives it, with `mysterio` and `cat` on watch.",
    },
    "validate.md": {
        "driver": "driver `gwen` (run it — test functionality against the criteria)",
        "counsel": [("jameson", "adversarial")],
        "watch": [("mysterio", "claiming done without proof — the exact failure this phase exists to catch"),
                  ("cat", "security holes left open"), ("electro", "fragile/cascading")],
        "trailer": "",
    },
    "cleanup.md": {
        "driver": "driver `peter`",
        "counsel": [("ned", None), ("jameson", None)],
        "watch": [("carnage", None), ("mysterio", None)],
        "trailer": "",
    },
}

PHASE_COUNCIL_LITE = {
    "questions.md": {
        "driver": "driver `peter`",
        "counsel": [("jameson", None)],
        "watch": [("mysterio", None), ("kingpin", None)],
        "trailer": "",
    },
    "research.md": {
        "driver": "drivers `peter` (recall/docs/codebase), `noir` (investigation)",
        "counsel": [("jameson", None)],
        "watch": [("mysterio", None), ("kingpin", None)],
        "trailer": "",
    },
    "design.md": {
        "driver": "driver `miguel`",
        "counsel": [("jameson", None)],
        "watch": [("kingpin", None), ("mysterio", None)],
        "trailer": "",
    },
    "plan.md": {
        "driver": "driver `miguel`",
        "counsel": [("jameson", None)],
        "watch": [("kingpin", None), ("mysterio", None)],
        "trailer": "",
    },
    "implement.md": {
        "driver": "driver `peter` (route each step to the right Spider-variant — see Delegation)",
        "counsel": [("jameson", None)],
        "watch": [("carnage", None), ("kingpin", None)],
        "trailer": " Verification and adversarial QA happen in `validate` — `jameson` and `mysterio` are the validate phase council.",
    },
    "validate.md": {
        "driver": "driver `jameson` (adversarial QA)",
        "counsel": [],
        "watch": [("mysterio", "claiming done without proof — the exact failure this phase exists to catch")],
        "trailer": "",
    },
    "cleanup.md": {
        "driver": "driver `peter`",
        "counsel": [("jameson", None)],
        "watch": [("carnage", None), ("mysterio", None)],
        "trailer": "",
    },
}


def _format_name_list(entries: list[tuple[str, str | None]]) -> str:
    return ", ".join(f"`{name}`" + (f" ({ann})" if ann else "") for name, ann in entries)


def render_phase_council_line(filename: str, council: dict, plugin_slug: str) -> str:
    entry = council[filename]
    qrdpiv = PHASE_QRDPIV[filename]
    counsel, watch = entry["counsel"], entry["watch"]
    counsel_clause = "none" if not counsel else _format_name_list(counsel)
    watch_label = "watch villain" if len(watch) == 1 else "watch villains"
    watch_clause = _format_name_list(watch)
    return (
        f"> **Phase council** (QRDPIV: {qrdpiv}) — consult only when the concern is live "
        f"(full map in `/{plugin_slug}:creed`): {entry['driver']}; counsel {counsel_clause}; "
        f"{watch_label} {watch_clause}.{entry['trailer']}"
    )


def load_lens_register_phase_roles() -> dict:
    """{character_name: {phase: role}} read from src/lenses/*.md and
    src/registers/*.md frontmatter — used only to cross-validate
    PHASE_COUNCIL_FULL stays in sync with each file's own declared role (see
    validate_phase_council_tables()), not as the direct source of the
    generated line's membership/order/annotations (see module comment above
    for why not).
    """
    roles = {}
    for d in (SRC / "lenses", SRC / "registers"):
        for f in sorted(d.glob("*.md")):
            text = f.read_text(encoding="utf-8")
            m = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
            if not m:
                continue
            fm = yaml.safe_load(m.group(1)) or {}
            phases = fm.get("phases")
            if isinstance(phases, dict):
                roles[fm["name"]] = phases
    return roles


def validate_phase_council_tables() -> None:
    """Fail loudly if PHASE_COUNCIL_FULL/_LITE have drifted out of sync with
    src/{lenses,registers}/*.md frontmatter or vocabulary/display.yml's
    roster.lite — see module comment above for what's checked and why.
    """
    roles = load_lens_register_phase_roles()
    for filename, entry in PHASE_COUNCIL_FULL.items():
        phase = filename[:-3]
        for role in ("counsel", "watch"):
            for name, _ann in entry[role]:
                if name in DELEGATION_NAMES:
                    continue
                got = (roles.get(name) or {}).get(phase)
                if got != role:
                    die(f"phase council drift: {filename} (full) lists '{name}' as {role}, "
                        f"but src/{{lenses,registers}}/{name}.md phases.{phase} = {got!r}")
    display = load_yaml(VOCAB_DIR / "display.yml")
    lite_roster = set(display["roster"]["lite"])
    for filename, entry in PHASE_COUNCIL_LITE.items():
        for role in ("counsel", "watch"):
            for name, _ann in entry[role]:
                if name not in lite_roster:
                    die(f"phase council drift: {filename} (lite) lists out-of-roster '{name}'")


def inject_phase_council(text: str, filename: str, roster_key: str, plugin_slug: str) -> str:
    council = PHASE_COUNCIL_LITE if roster_key == "lite" else PHASE_COUNCIL_FULL
    if filename not in council:
        return text
    line = render_phase_council_line(filename, council, plugin_slug)
    # Insert right after the H1 title + its trailing blank line.
    m = re.match(r"(# [^\n]*\n\n)", text)
    if not m:
        return text
    insert_at = m.end()
    return text[:insert_at] + line + "\n\n" + text[insert_at:]


def build_tier_skills(edition: dict, vocab: Vocab, data_model: dict, display: dict,
                       skills_dest: Path):
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
                    text = inject_phase_council(text, name, roster_key, edition["plugin"]["name"])
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
            in_tools = rel.parts == ("tools",)
            skip_nonpinned = frozenset({"cadence"}) if (in_tools and name == "objective.py") else frozenset()
            own_tier_file = in_tools and name == "cadence.py"
            text = vocab.apply(text, skip_nonpinned=skip_nonpinned, own_tier_file=own_tier_file)
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
    # `src/templates/.claude/settings.json` is copied from core (untethemed,
    # pinned folder names — see src/README.md) and so never carries the two
    # observation-deck permission lines at all; add them for editions where
    # the feature is on, rather than only ever removing them.
    deck_lines = [
        "Bash(bash .claude/scripts/agent-log.sh:*)",
        "Bash(bash .claude/scripts/observe.sh:*)",
    ]
    if features.get("observation_deck"):
        statusline_idx = next(
            (i for i, a in enumerate(allow) if "statusline.sh" in a), len(allow) - 1
        )
        for offset, line in enumerate(deck_lines):
            if line not in allow:
                allow.insert(statusline_idx + 1 + offset, line)
    else:
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
            '        "    3. The operating doctrine (principles, decision mechanic, vocabulary) is in CLAUDE.md and loads automatically.\\n"\n'
            '        "    4. Start work: /harness-core:workstream (a complex effort), "\n'
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


def build_edition(name: str, data_model: dict, display: dict):
    edition = load_yaml(EDITIONS_DIR / f"{name}.yml")
    vocab = Vocab(data_model, display, edition)
    dest_root = OUT_ROOT / edition["plugin"]["name"]
    if dest_root.exists():
        shutil.rmtree(dest_root)
    dest_root.mkdir(parents=True)

    skills_dest = dest_root / "skills"
    build_tier_skills(edition, vocab, data_model, display, skills_dest)
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
    validate_phase_council_tables()

    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    for name in EDITION_NAMES:
        build_edition(name, data_model, display)
    print("generate.py: done")


if __name__ == "__main__":
    main()
