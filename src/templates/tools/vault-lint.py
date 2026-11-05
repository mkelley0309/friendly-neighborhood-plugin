#!/usr/bin/env python3
"""vault-lint — static linter for the Obsidian knowledge vault. Stdlib only.

Scans `knowledge/vault/`. Report-only by default; `fix` applies only safe,
enumerated auto-fixes (never deletes, never migrates cross-tree links).
Audit reports of record live in `knowledge/audits/`; the end-to-end process
(gate before applying, editorial handling of C8/C9) is the knowledge skill's
`audit` action.

Vault root resolves from $WORKSPACE_ROOT, falling back to the current working
directory. Concept subtrees are auto-discovered as the top-level folders under
`vault/` (excluding `_graph/` and dotfolders); override with --subtrees.
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path, PurePosixPath
from urllib.parse import unquote

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

WORKSPACE = Path(os.environ.get("WORKSPACE_ROOT", os.getcwd()))
VAULT = WORKSPACE / "knowledge" / "vault"

# Top-level vault folders that hold concept notes. Populated at startup by
# discover_subtrees(), or overridden with --subtrees.
# _graph is the cross-cutting concept layer and is EXEMPT as a link target.
CONCEPT_SUBTREES = set()


def discover_subtrees():
    """Top-level folders under VAULT that hold concept notes.

    Everything directly under `vault/` is a concept subtree except the `_graph/`
    concept layer and dotfolders (.obsidian, .trash). Keeping this discovered
    rather than hardcoded is what makes the linter layout-agnostic — no vault's
    folder names are baked in.
    """
    if not VAULT.is_dir():
        return set()
    return {
        d.name for d in VAULT.iterdir()
        if d.is_dir() and d.name != "_graph" and not d.name.startswith(".")
    }

# note_type values that are structural/navigation (exempt from C4 zero-outbound check)
NAV_TYPES = {"vault-index", "navigation", "hub"}

# C15 note-shape rules. Scope is path-prefix based (relative to VAULT); excluded
# prefixes get no C15 findings at all. Set both to fit your vault's taxonomy.
# SHAPE_SEVERITY is the severity of the in-scope R1–R3 findings: "warn" reports
# them; "fail" makes `check` exit 1 (set it once existing notes are backfilled).
SHAPE_SCOPE_PREFIXES = ("domain-knowledge/",)
SHAPE_EXCLUDE_PREFIXES = ()
SHAPE_SEVERITY = "warn"
CONTENTS_MIN_LINES = 100
CONTENTS_MIN_H2 = 3
SPLIT_WARN_LINES = 500
SUMMARY_MAX_CHARS = 250

# C16 anchor integrity. Broken anchors are ANCHOR_SEVERITY everywhere except
# under ANCHOR_WARN_PREFIXES: list imported mirrors here when their anchors are
# opaque upstream IDs that no local heading can satisfy. Those report as warn.
ANCHOR_SEVERITY = "fail"
ANCHOR_WARN_PREFIXES = ()

# C17 requirement-hub integrity (`requirements:` / `note_type: requirement`).
# Self-gating: vaults without requirement hubs get no findings.
REQUIREMENT_SEVERITY = "fail"
REQUIREMENT_PREFIX = "_graph/requirements/"
REQUIREMENT_FIELDS = ("requirement", "standard", "issuer", "jurisdictions", "aliases", "derived_from", "as_of")
# Where a standard applies, not who issued it. Empty accepts any value; list your
# fixed set here to have C17 R3 enforce it.
JURISDICTIONS = set()
PLACEHOLDER_VALUES = {"TBD", "TODO", "?", "UNKNOWN"}

# Meta files that may live in the vault but are NOT vault notes (AI-instruction /
# harness files) — exempt from all note-level checks (e.g. C1 note_type).
NON_NOTE_FILES = {"CLAUDE.md", "AGENTS.md"}

# ── helpers ──────────────────────────────────────────────────────────────────

def die(msg):
    """Print an error to stderr and exit with status 1."""
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


def iter_notes():
    """Yield every *.md file under VAULT, recursively, excluding hidden dirs
    (.obsidian, .trash) and non-note meta files (CLAUDE.md, AGENTS.md)."""
    for p in VAULT.rglob("*.md"):
        if p.name in NON_NOTE_FILES:
            continue
        if any(part.startswith(".") for part in p.relative_to(VAULT).parts):
            continue
        yield p


def parse_frontmatter(text):
    """
    Return (frontmatter_dict, body_str).

    Parses a leading YAML-ish --- block. Supports:
      key: value          → str
      key: [a, b, c]      → list[str]
      key:                → list[str]  (block list, as Obsidian writes it)
        - a
    Missing or malformed block → ({}, full_text).
    """
    if text and text[0] == "﻿":
        text = text[1:]  # tolerate a leading UTF-8 BOM
    if not text.startswith("---"):
        return {}, text

    # Find the closing ---
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text

    fm_block = text[3:end].strip()
    body = text[end + 4:].lstrip("\n")

    fm = {}
    block_key = None
    for line in fm_block.splitlines():
        item = re.match(r"^[ \t]*-[ \t]+(.*)$", line)
        if item and block_key is not None:
            if not isinstance(fm[block_key], list):
                fm[block_key] = []
            val = item.group(1).strip().strip('"').strip("'")
            if val:
                fm[block_key].append(val)
            continue
        block_key = None
        if ":" not in line:
            continue
        key, _, raw_val = line.partition(":")
        key = key.strip()
        raw_val = raw_val.strip()

        if raw_val.startswith("[") and raw_val.endswith("]"):
            # Simple inline list: [a, b, c]
            inner = raw_val[1:-1]
            items = [x.strip().strip('"').strip("'") for x in inner.split(",") if x.strip()]
            fm[key] = items
        else:
            fm[key] = raw_val.strip('"').strip("'")
            if not raw_val and not line[:1].isspace():
                block_key = key  # a following `- item` run makes this a list

    return fm, body


def note_subtree(path):
    """Return the first path segment of the note relative to VAULT."""
    try:
        rel = path.relative_to(VAULT)
    except ValueError:
        return ""
    parts = rel.parts
    return parts[0] if len(parts) > 1 else ""


def iter_wikilinks(body, frontmatter):
    """
    Yield (raw_target, location) for every [[...]] reference.

    location values:
      "related"     — link appears under a ## Related heading
      "body"        — link appears before ## Related (or no ## Related exists)
      "frontmatter" — slug from the `related:` frontmatter list

    Alias (`|...`) and heading anchor (`#...`) are stripped from targets.
    """
    # Frontmatter related: list
    fm_related = frontmatter.get("related", [])
    if isinstance(fm_related, str):
        fm_related = [fm_related]
    for slug in fm_related:
        slug = slug.strip()
        if slug:
            yield slug, "frontmatter"

    # Body links: track whether we are inside a ## Related section, and skip
    # fenced code blocks (```/~~~) and inline code spans so JSON/code samples
    # like [["account": "111"]] are not mistaken for wikilinks.
    in_related = False
    in_fence = False
    for line in body.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue

        heading_match = re.match(r"^(#{1,6})\s+(.*)", line)
        if heading_match:
            level = len(heading_match.group(1))
            title = heading_match.group(2).strip()
            if level <= 2 and title.lower() == "related":
                in_related = True
            elif level <= 2:
                in_related = False

        line = re.sub(r"`[^`]*`", "", line)  # drop inline code spans
        for raw in re.findall(r"\[\[([^\]]+)\]\]", line):
            # Strip alias: [[target|alias]] → target. Obsidian wikilinks inside
            # markdown tables escape the pipe as `\|`, so split leaves a trailing
            # backslash on the path — strip it (on Windows it becomes a path sep
            # and breaks resolution).
            raw = raw.split("|")[0]
            # Strip heading anchor: [[target#section]] → target
            raw = raw.split("#")[0].strip().rstrip("\\").strip()
            if raw:
                yield raw, "related" if in_related else "body"


def build_slug_index():
    """
    Build a dict: basename-without-.md → list of vault-relative path strings.

    Used to resolve bare [[slug]] wikilinks.
    """
    index: dict[str, list[str]] = {}
    for note in iter_notes():
        rel = note.relative_to(VAULT).as_posix()
        slug = note.stem  # filename without .md
        index.setdefault(slug, []).append(rel)
    return index


def resolve_target(raw, slug_index, source_dir=None):
    """
    Attempt to resolve a raw wikilink target.

    Rules:
      - If raw ends with .base OR matches an existing *.base file → resolved (whitelisted).
      - If raw contains '/' → treat as vault-relative path; check VAULT/raw.md or VAULT/raw/index.md.
        If that fails and source_dir is given, retry relative to the linking note's folder
        (Obsidian resolves e.g. [[criteria/index]] against the note's own directory).
      - Else → slug lookup in slug_index; check each candidate path on disk.

    `source_dir` is the vault-relative POSIX directory of the note that owns the link.
    Returns (resolved_path_or_None, ambiguous_bool).
    resolved_path_or_None is a vault-relative POSIX string or None.
    """
    raw = raw.strip()

    # .base whitelist
    if raw.endswith(".base"):
        return (raw, False)
    # Check if there's a *.base file matching the bare name
    if not raw.endswith(".md") and "/" not in raw:
        base_candidates = list(VAULT.rglob(f"{raw}.base"))
        if base_candidates:
            return (raw, False)

    if "/" in raw:
        # Vault-relative path resolution
        candidate_md = VAULT / (raw + ".md")
        candidate_index = VAULT / raw / "index.md"
        if candidate_md.exists():
            return (raw + ".md", False)
        if candidate_index.exists():
            return (raw + "/index.md", False)
        # Source-relative resolution (relative to the linking note's own folder)
        if source_dir:
            rel_md = VAULT / source_dir / (raw + ".md")
            rel_index = VAULT / source_dir / raw / "index.md"
            if rel_md.exists():
                return ((PurePosixPath(source_dir) / (raw + ".md")).as_posix(), False)
            if rel_index.exists():
                return ((PurePosixPath(source_dir) / raw / "index.md").as_posix(), False)
        return (None, False)

    # Source-relative bare reference (e.g. [[index]] = the local folder's index,
    # [[sibling]] = a sibling note) — try before the global slug index, which would
    # otherwise resolve an ambiguous bare name to an arbitrary first match.
    if source_dir:
        cand_md = VAULT / source_dir / (raw + ".md")
        cand_idx = VAULT / source_dir / raw / "index.md"
        if cand_md.exists():
            return ((PurePosixPath(source_dir) / (raw + ".md")).as_posix(), False)
        if cand_idx.exists():
            return ((PurePosixPath(source_dir) / raw / "index.md").as_posix(), False)

    # Slug resolution
    hits = slug_index.get(raw, [])
    if not hits:
        return (None, False)
    if len(hits) == 1:
        return (hits[0], False)
    # Multiple hits = ambiguous but technically resolved
    return (hits[0], True)


# ── checks ───────────────────────────────────────────────────────────────────

def check_c1(path, fm, body):
    """
    C1 — Required frontmatter fields by note_type.

    All notes need `note_type`.
    `vault-note` additionally needs: source_path, source_url, synced_at,
    distilled_at, confidence, tags.
    `knowledge` type does NOT require tags.
    Auto-fix: vault-note missing source_url → add `source_url: na`.
    """
    findings = []
    note_type = fm.get("note_type", "")

    if not note_type:
        findings.append({
            "check": "C1",
            "path": path.relative_to(VAULT).as_posix(),
            "detail": "missing note_type",
            "auto_fixable": False,
        })
        return findings

    if note_type == "vault-note":
        required = ["source_path", "source_url", "synced_at", "distilled_at", "confidence", "tags"]
        for field in required:
            if field not in fm:
                fix = field == "source_url"
                findings.append({
                    "check": "C1",
                    "path": path.relative_to(VAULT).as_posix(),
                    "detail": f"vault-note missing field: {field}",
                    "auto_fixable": fix,
                })

    return findings


def check_c2(path, fm, body):
    """
    C2 — note_type misplacement / bad values.

    Flag: note_type in {vendor-documentation, perspective} (illegal in vault).
    Flag: note_type == 'index' → auto-fix to 'vault-index'.
    Flag: index.md typed 'vault-note' without source_url AND distilled_at → auto-fix to 'vault-index'.
    """
    findings = []
    note_type = fm.get("note_type", "")
    rel = path.relative_to(VAULT).as_posix()

    illegal = {"vendor-documentation", "perspective"}
    if note_type in illegal:
        findings.append({
            "check": "C2",
            "path": rel,
            "detail": f"illegal note_type in vault: {note_type}",
            "auto_fixable": False,
        })

    if note_type == "index":
        findings.append({
            "check": "C2",
            "path": rel,
            "detail": "note_type: index → should be vault-index",
            "auto_fixable": True,
        })

    if path.name == "index.md" and note_type == "vault-note":
        if "source_url" not in fm and "distilled_at" not in fm:
            findings.append({
                "check": "C2",
                "path": rel,
                "detail": "index.md typed vault-note but lacks source_url and distilled_at; likely vault-index",
                "auto_fixable": True,
            })

    return findings


def check_c3(path, fm, body, slug_index):
    """
    C3 — Obsidian-phantom wikilinks. A link greys out in Obsidian unless it is a
    full vault-relative path (VAULT/raw.md or VAULT/raw/index.md) or a UNIQUE
    basename. Source-relative links, `..` relative links, and ambiguous basenames
    are flagged (Obsidian does not resolve them reliably). `.base` targets are
    whitelisted. Auto-fix ONLY the prefix-truncation case.
    """
    findings = []
    rel = path.relative_to(VAULT).as_posix()
    source_dir = PurePosixPath(rel).parent.as_posix()

    for raw, loc in iter_wikilinks(body, fm):
        if raw.endswith(".base"):
            continue
        # `..` relative links never resolve in Obsidian → always a phantom.
        if ".." in raw.split("/"):
            reason = "uses `..` — Obsidian does not resolve relative wikilinks"
        else:
            # Otherwise use Obsidian-like resolution (full path, source-relative
            # suffix, or basename). Resolved → not a phantom.
            resolved, _ambig = resolve_target(raw, slug_index, source_dir)
            if resolved is not None:
                continue
            reason = "no matching note"

        fixable = False
        for subtree in CONCEPT_SUBTREES:
            prefixed = f"{subtree}/{raw}"
            r2, _ = resolve_target(prefixed, slug_index)
            if r2 is not None:
                fixable = True
                break

        findings.append({
            "check": "C3",
            "path": rel,
            "detail": f"phantom wikilink [[{raw}]] — {reason} (location: {loc})",
            "auto_fixable": fixable,
        })

    return findings


def check_c4(path, fm, body):
    """
    C4 — Zero-outbound-link notes (no [[...]] anywhere).

    Excludes index/hub/navigation note_types.
    """
    findings = []
    note_type = fm.get("note_type", "")
    if note_type in NAV_TYPES:
        return findings

    # Check body + frontmatter related list for any wikilinks
    all_links = list(iter_wikilinks(body, fm))
    if not all_links:
        findings.append({
            "check": "C4",
            "path": path.relative_to(VAULT).as_posix(),
            "detail": "no outbound wikilinks",
            "auto_fixable": False,
        })

    return findings


def check_c5(path, fm, body):
    """
    C5 — Wikilinks prefixed with vault/ (always wrong).

    Auto-fix: strip the vault/ prefix.
    """
    findings = []
    rel = path.relative_to(VAULT).as_posix()

    for raw, loc in iter_wikilinks(body, fm):
        if raw.startswith("vault/"):
            findings.append({
                "check": "C5",
                "path": rel,
                "detail": f"vault/-prefixed wikilink [[{raw}]] (location: {loc})",
                "auto_fixable": True,
            })

    return findings


def check_c6(slug_index):
    """
    C6 — Directories under VAULT with no index.md.

    Auto-fix: create a stub index.md with note_type: navigation.
    EXCEPTION: _graph directory is exempt.
    """
    findings = []

    for dirpath in VAULT.rglob("*"):
        if not dirpath.is_dir():
            continue
        # Exempt _graph at any depth
        rel = dirpath.relative_to(VAULT)
        if "_graph" in rel.parts:
            continue
        # Skip Obsidian system dirs and any hidden dot-directory (.obsidian, .trash, etc.)
        if any(p.startswith(".") for p in rel.parts):
            continue
        if not (dirpath / "index.md").exists():
            findings.append({
                "check": "C6",
                "path": rel.as_posix() + "/",
                "detail": "directory has no index.md",
                "auto_fixable": True,
            })

    return findings


def check_c7(path, fm, body):
    """
    C7 — provenance: first-party notes with confidence: high and no corroborated_by.

    Report only.
    """
    findings = []
    if (
        fm.get("provenance") == "first-party"
        and fm.get("confidence") == "high"
        and "corroborated_by" not in fm
    ):
        findings.append({
            "check": "C7",
            "path": path.relative_to(VAULT).as_posix(),
            "detail": "first-party/high confidence note lacks corroborated_by",
            "auto_fixable": False,
        })
    return findings


def check_c8(path, fm, body, slug_index):
    """
    C8 — Cross-tree relationship outside _graph.

    A wikilink whose resolved target's subtree ∈ CONCEPT_SUBTREES and ≠
    the source note's subtree, in ANY location.
    Exempt: target subtree _graph; intra-subtree links.
    """
    findings = []
    src_subtree = note_subtree(path)
    rel = path.relative_to(VAULT).as_posix()
    source_dir = PurePosixPath(rel).parent.as_posix()

    # _graph hubs are the sanctioned home for cross-tree relationships — they are
    # SUPPOSED to link out to every concept subtree. Never flag a _graph-source link.
    if src_subtree == "_graph":
        return findings

    for raw, loc in iter_wikilinks(body, fm):
        resolved, _ = resolve_target(raw, slug_index, source_dir)
        if resolved is None:
            continue  # unresolved — C3 catches this

        # Determine the resolved note's subtree
        parts = Path(resolved).parts
        target_subtree = parts[0] if len(parts) > 1 else ""

        if target_subtree == "_graph":
            continue  # exempt
        if target_subtree not in CONCEPT_SUBTREES:
            continue  # not a concept subtree — not a C8 violation
        if target_subtree == src_subtree:
            continue  # intra-subtree — fine

        findings.append({
            "check": "C8",
            "path": rel,
            "detail": (
                f"cross-tree link [[{raw}]] → {target_subtree}/ "
                f"(source: {src_subtree}/, location: {loc})"
            ),
            "auto_fixable": False,
        })

    return findings


def check_c9(path, fm, body):
    """
    C9 — Personalization/ownership fields.

    Flag: authored_by_me (any value), owner == 'me', key literally 'mine'.
    Do NOT flag author: <any value>.
    """
    findings = []
    rel = path.relative_to(VAULT).as_posix()

    if "authored_by_me" in fm:
        findings.append({
            "check": "C9",
            "path": rel,
            "detail": f"authored_by_me: {fm['authored_by_me']} (needs manual conversion)",
            "auto_fixable": False,
        })
    if fm.get("owner") == "me":
        findings.append({
            "check": "C9",
            "path": rel,
            "detail": "owner: me",
            "auto_fixable": False,
        })
    if "mine" in fm:
        findings.append({
            "check": "C9",
            "path": rel,
            "detail": f"key 'mine' present: {fm['mine']}",
            "auto_fixable": False,
        })

    return findings


def check_c10(path, fm, body):
    """C10 — _graph concept-hub list links missing a rationale (bare links)."""
    findings = []
    if fm.get("note_type") != "concept" or "_graph" not in path.parts:
        return findings
    rel = path.relative_to(VAULT).as_posix()
    in_fence = False
    for line in body.splitlines():
        s = line.lstrip()
        if s.startswith("```") or s.startswith("~~~"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        # A list item carrying a wikilink should also carry a rationale. Strip the
        # list marker and all wikilinks; if almost no prose remains, it's a bare link.
        if re.match(r"^\s*[-*]\s", line) and "[[" in line:
            rest = re.sub(r"\[\[[^\]]*\]\]", "", line)
            rest = re.sub(r"^\s*[-*]\s*", "", rest).strip(" —–-:.\t")
            if len(rest) < 10:
                m = re.search(r"\[\[([^\]|]+)", line)
                tgt = m.group(1) if m else "?"
                findings.append({
                    "check": "C10",
                    "path": rel,
                    "detail": f"concept-hub link without rationale: [[{tgt}]]",
                    "auto_fixable": False,
                })
    return findings


def check_c11(path, fm, body):
    """C11 — _graph concept hub missing required concept-node frontmatter."""
    findings = []
    if fm.get("note_type") != "concept" or "_graph" not in path.parts:
        return findings
    rel = path.relative_to(VAULT).as_posix()
    for field in ("concept", "aliases", "related_concepts"):
        if not fm.get(field):
            findings.append({
                "check": "C11",
                "path": rel,
                "detail": f"concept hub missing frontmatter field: {field}",
                "auto_fixable": False,
            })
    return findings


_C13_HEDGE_RE = re.compile(
    r"\barguably\b|\bsome would say\b|\bit could be argued\b",
    re.IGNORECASE,
)


def check_c13(path, fm, body):
    """
    C13 — declared confidence vs hedged prose.

    Flag a note whose frontmatter asserts ``confidence: high`` while its body
    carries a term from the closed hedge list (``arguably`` / ``some would say``
    / ``it could be argued``). It reports a frontmatter/prose contradiction for
    human review, not a confirmed defect.

    Exclusion: verbatim external mirrors — a note carrying a real ``source_url``
    (present and not na/none) — where a hedge is the source author's device, not
    internal negotiated hedging.

    Report only. Never auto-fixable: the resolution is a human choice among
    strengthening the prose, downgrading confidence, or adding corroborated_by.
    """
    findings = []
    if fm.get("confidence") != "high":
        return findings
    src = str(fm.get("source_url", "")).strip().lower()
    if src and src not in ("na", "none"):
        return findings
    terms = sorted({m.group(0).lower() for m in _C13_HEDGE_RE.finditer(body)})
    if not terms:
        return findings
    shown = ", ".join(f"'{t}'" for t in terms[:3])
    findings.append({
        "check": "C13",
        "path": path.relative_to(VAULT).as_posix(),
        "detail": f"confidence: high but body hedges: {shown}",
        "auto_fixable": False,
    })
    return findings


def _shape_scan(lines):
    """
    Scan body lines for the C15 heading structure. Fence-aware (```/~~~ toggle);
    the `## Contents` block (through the line before the next H2) is excluded.

    Returns dict:
      entries         — generated Contents bullet lines (H2 `- t`, H3 `  - t`)
      h2_count        — H2 headings excluding Contents
      first_is_contents — first H2 of the body is `## Contents`
      span            — (start, end) of the existing Contents block, or None
      anchor          — line index of the first non-Contents H2, or None
    """
    entries = []
    h2_count = 0
    first_h2 = None
    start = end = anchor = None
    in_contents = False
    in_fence = False
    for i, line in enumerate(lines):
        stripped = line.lstrip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if line.startswith("## "):
            title = line[3:].rstrip()
            if first_h2 is None:
                first_h2 = title
            if title == "Contents" and start is None:
                start, in_contents = i, True
                continue
            if in_contents:
                end, in_contents = i, False
            if anchor is None:
                anchor = i
            h2_count += 1
            entries.append(f"- {title}")
        elif in_contents:
            continue
        elif line.startswith("### ") and h2_count:
            entries.append(f"  - {line[4:].rstrip()}")
    if in_contents:
        end = len(lines)
    return {
        "entries": entries,
        "h2_count": h2_count,
        "first_is_contents": first_h2 == "Contents",
        "span": (start, end) if start is not None else None,
        "anchor": anchor,
    }


def _contents_block(entries):
    """Generated Contents block: heading, blank, bullets, one trailing blank."""
    return ["## Contents", ""] + entries + [""]


def _shape_scope(rel):
    """'excluded' | 'in' | 'out' for a vault-relative posix path."""
    if rel.startswith(SHAPE_EXCLUDE_PREFIXES):
        return "excluded"
    if rel.startswith(SHAPE_SCOPE_PREFIXES):
        return "in"
    return "out"


def check_c15(path, fm, body, text):
    """
    C15 — note shape for long-form guides.

    R1 (in scope): summary present, <=SUMMARY_MAX_CHARS, no wikilink, written
       double-quoted. Report-only.
    R2: long note (>CONTENTS_MIN_LINES lines, >=CONTENTS_MIN_H2 H2s) whose first
       H2 is not `## Contents`. Fixable in scope; warn-only out of scope.
    R3 (in scope): R2 applies and the Contents block is stale. Fixable.
    R4 (everywhere but excluded): note over SPLIT_WARN_LINES lines — split
       candidate. Always warn, report-only.
    """
    rel = path.relative_to(VAULT).as_posix()
    scope = _shape_scope(rel)
    if scope == "excluded":
        return []
    findings = []

    def add(detail, sev, fixable=False):
        findings.append({
            "check": "C15", "path": rel, "detail": detail,
            "auto_fixable": fixable, "severity": sev,
        })

    n_lines = len(text.splitlines())

    if scope == "in":
        summary = fm.get("summary", "")
        if not isinstance(summary, str) or not summary.strip():
            add("R1: missing summary", SHAPE_SEVERITY)
        else:
            if len(summary) > SUMMARY_MAX_CHARS:
                add(f"R1: summary >{SUMMARY_MAX_CHARS} chars", SHAPE_SEVERITY)
            if "[[" in summary:
                add("R1: summary contains wikilink", SHAPE_SEVERITY)
            raw = next((l.partition(":")[2].strip() for l in text.splitlines()[1:]
                        if l.startswith("summary:")), "")
            if not (len(raw) >= 2 and raw.startswith('"') and raw.endswith('"')):
                add("R1: summary not double-quoted", SHAPE_SEVERITY)

    lines = body.splitlines()
    scan = _shape_scan(lines)
    if n_lines > CONTENTS_MIN_LINES and scan["h2_count"] >= CONTENTS_MIN_H2:
        if not scan["first_is_contents"]:
            add("R2: missing Contents", SHAPE_SEVERITY if scope == "in" else "warn",
                fixable=(scope == "in"))
        if scope == "in" and scan["span"]:
            s, e = scan["span"]
            have = [l.rstrip() for l in lines[s:e]]
            if have != _contents_block(scan["entries"]):
                add("R3: Contents out of date", SHAPE_SEVERITY, fixable=True)

    if n_lines > SPLIT_WARN_LINES:
        add(f"R4: split candidate ({n_lines} lines)", "warn")
    return findings


def _fix_c15_text(text):
    """Return text with a regenerated Contents block placed before the first
    non-Contents H2, or None if the note is not eligible. Keeps newline style."""
    nl = "\r\n" if "\r\n" in text else "\n"
    lines = text.split(nl)
    body_start = 0
    if lines and lines[0].lstrip("﻿").startswith("---"):
        for i in range(1, len(lines)):
            if lines[i].startswith("---"):
                body_start = i + 1
                break
        else:
            return None
    head, body = lines[:body_start], lines[body_start:]
    scan = _shape_scan(body)
    if len(text.splitlines()) <= CONTENTS_MIN_LINES or scan["h2_count"] < CONTENTS_MIN_H2:
        return None
    if scan["span"]:
        s, e = scan["span"]
        body = body[:s] + body[e:]
        scan = _shape_scan(body)
    a = scan["anchor"]
    body = body[:a] + _contents_block(scan["entries"]) + body[a:]
    return nl.join(head + body)


_HEADING_RE = re.compile(r"^#{1,6}[ \t]+(.*?)(?:[ \t]+#+)?[ \t]*$")
_MD_SELF_ANCHOR_RE = re.compile(r"\]\(#([^)]*)\)")


def _anchor_slug(s):
    """Heading slug: lowercase, spaces to hyphens, drop everything but word chars and '-'."""
    return re.sub(r"[^\w\-]", "", s.lower().replace(" ", "-"))


def _note_anchors(rel, cache):
    """(exact heading texts, heading slugs, body text) of a vault note. Fence-aware;
    frontmatter excluded. Cached per run in `cache`."""
    if rel not in cache:
        text = (VAULT / rel).read_text(encoding="utf-8", errors="replace")
        _, body = parse_frontmatter(text)
        heads, fence = [], False
        for line in body.splitlines():
            if line.lstrip().startswith(("```", "~~~")):
                fence = not fence
                continue
            if fence:
                continue
            m = _HEADING_RE.match(line)
            if m:
                heads.append(m.group(1).strip())
        cache[rel] = (set(heads), {_anchor_slug(h) for h in heads}, body)
    return cache[rel]


def _anchor_resolves(rel, anchor, cache):
    """True if every `#`-separated part of `anchor` names a heading in `rel` (exact
    text or same slug), or, for `^id`, a block ID present in the note."""
    exact, slugs, body = _note_anchors(rel, cache)
    if anchor.startswith("^"):
        return re.search(r"(?m)(?:^|\s)\^" + re.escape(anchor[1:]) + r"[ \t]*$", body) is not None
    return all(p in exact or _anchor_slug(p) in slugs
               for p in (x.strip() for x in anchor.split("#")) if p)


def iter_anchored_links(body):
    """
    Yield (target, anchor) in file order for `[[target#anchor|alias]]` and
    `[text](#anchor)` links. target '' means the note itself (`[[#x]]`,
    `](#x)`). Skips fenced code and inline code spans; `](#x)` is URL-decoded.
    """
    in_fence = False
    for line in body.splitlines():
        if line.lstrip().startswith(("```", "~~~")):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        line = re.sub(r"`[^`]*`", "", line)
        hits = []
        for m in re.finditer(r"\[\[([^\]]*)\]\]", line):
            left = m.group(1).replace("\\|", "|").split("|", 1)[0]
            if "#" not in left:
                continue
            target, _, anchor = left.partition("#")
            hits.append((m.start(), target.strip().rstrip("\\").strip(),
                         anchor.strip().rstrip("\\").strip()))
        for m in _MD_SELF_ANCHOR_RE.finditer(line):
            hits.append((m.start(), "", unquote(m.group(1)).strip()))
        for _, t, a in sorted(hits):
            yield t, a


def check_c16(path, body, slug_index, cache):
    """
    C16 — anchor integrity. A heading or block anchor (`[[t#Heading]]`,
    `[[#Heading]]`, `[x](#heading)`, `[[t#^block]]`) must match a heading in the
    resolved target by exact text or slug, or a block ID. Links whose target does
    not resolve are left to C3. Severity: ANCHOR_SEVERITY, or warn for sources
    under ANCHOR_WARN_PREFIXES. Report-only.
    """
    rel = path.relative_to(VAULT).as_posix()
    source_dir = PurePosixPath(rel).parent.as_posix()
    sev = "warn" if rel.startswith(ANCHOR_WARN_PREFIXES) else ANCHOR_SEVERITY
    findings = []
    for target, anchor in iter_anchored_links(body):
        if not anchor:
            continue
        if target:
            resolved, _ambig = resolve_target(target, slug_index, source_dir)
            if not resolved or not resolved.endswith(".md") or not (VAULT / resolved).is_file():
                continue
        else:
            resolved = rel
        if not _anchor_resolves(resolved, anchor, cache):
            findings.append({
                "check": "C16", "path": rel,
                "detail": f"broken anchor [[{target}#{anchor}]] — no matching heading in {resolved}",
                "auto_fixable": False, "severity": sev,
            })
    return findings


_BLOCK_ID_RE = re.compile(r"(?:^|\s)\^([\w-]+)[ \t]*$")


def build_requirement_alias_index():
    """{casefolded alias: [hub rel paths]} over every `note_type: requirement` note."""
    index: dict[str, list[str]] = {}
    root = VAULT / REQUIREMENT_PREFIX
    if not root.is_dir():
        return index
    for p in sorted(root.rglob("*.md")):
        fm, _ = parse_frontmatter(p.read_text(encoding="utf-8", errors="replace"))
        if fm.get("note_type") != "requirement":
            continue
        aliases = fm.get("aliases") or []
        for a in ([aliases] if isinstance(aliases, str) else aliases):
            if a.strip():
                index.setdefault(a.strip().casefold(), []).append(p.relative_to(VAULT).as_posix())
    return index


def _wikilink_target(item):
    """`[[t#a|x]]` → (t, a); None if the item is not one whole wikilink."""
    m = re.fullmatch(r"\[\[([^\[\]]+)\]\]", item.strip())
    if not m:
        return None
    target, _, anchor = m.group(1).split("|", 1)[0].partition("#")
    return target.strip(), anchor.strip()


def check_c17(path, fm, body, slug_index, cache, alias_index):
    """
    C17 — requirement-hub integrity. Self-gates on a `requirements:` key or
    `note_type: requirement`.
      R1  each `requirements:` entry is one wikilink resolving under _graph/requirements/
      R2  its anchor, if any, is a `^id` that resolves (heading anchors are findings)
      R3  hub has REQUIREMENT_FIELDS, lives at _graph/requirements/req-<requirement>.md,
          every `jurisdictions` value is in JURISDICTIONS (when set), and every `derived_from`
          entry resolves
      R4  hub block IDs are unique and start with `<requirement>-`
      R5  no alias is claimed by two hubs
    Severity: REQUIREMENT_SEVERITY. Report-only.
    """
    is_hub = fm.get("note_type") == "requirement"
    if not (is_hub or "requirements" in fm):
        return []
    rel = path.relative_to(VAULT).as_posix()
    source_dir = PurePosixPath(rel).parent.as_posix()
    findings = []

    def add(rule, detail):
        findings.append({"check": "C17", "path": rel, "detail": f"{rule}: {detail}",
                         "auto_fixable": False, "severity": REQUIREMENT_SEVERITY})

    def as_list(v):
        return [v] if isinstance(v, str) and v else (v or [])

    for item in as_list(fm.get("requirements")):
        parsed = _wikilink_target(item)
        if parsed is None:
            add("R1", f"malformed requirements entry {item!r} (one [[wikilink]] per entry, no commas inside)")
            continue
        target, anchor = parsed
        resolved, _ = resolve_target(target, slug_index, source_dir)
        if not resolved or not resolved.startswith(REQUIREMENT_PREFIX):
            add("R1", f"requirements entry [[{target}]] does not resolve to a hub under {REQUIREMENT_PREFIX}")
            continue
        if anchor and not anchor.startswith("^"):
            add("R2", f"requirements entry [[{target}#{anchor}]] uses a heading anchor; use #^id")
        elif anchor and not _anchor_resolves(resolved, anchor, cache):
            add("R2", f"requirements entry [[{target}#{anchor}]] — no block ID {anchor} in {resolved}")

    if is_hub:
        missing = [k for k in REQUIREMENT_FIELDS if not fm.get(k)]
        if missing:
            add("R3", f"hub missing field(s): {', '.join(missing)}")
        placeholder = [k for k in REQUIREMENT_FIELDS
                       if isinstance(fm.get(k), str) and fm[k].strip().upper() in PLACEHOLDER_VALUES]
        if placeholder:
            add("R3", f"hub field(s) hold a placeholder: {', '.join(placeholder)}")
        bad_j = [j for j in as_list(fm.get("jurisdictions")) if JURISDICTIONS and j not in JURISDICTIONS]
        if bad_j:
            add("R3", f"jurisdictions value(s) not in the fixed set: {', '.join(map(str, bad_j))}")
        req = fm.get("requirement", "")
        if req and rel != f"{REQUIREMENT_PREFIX}req-{req}.md":
            add("R3", f"hub path should be {REQUIREMENT_PREFIX}req-{req}.md")
        for item in as_list(fm.get("derived_from")):
            parsed = _wikilink_target(item)
            if parsed is None or not resolve_target(parsed[0], slug_index, source_dir)[0]:
                add("R3", f"derived_from entry {item!r} does not resolve")

        seen, fence = set(), False
        for line in body.splitlines():
            if line.lstrip().startswith(("```", "~~~")):
                fence = not fence
                continue
            m = None if fence else _BLOCK_ID_RE.search(line)
            if not m:
                continue
            bid = m.group(1)
            if bid in seen:
                add("R4", f"duplicate block ID ^{bid}")
            seen.add(bid)
            if req and not bid.startswith(f"{req}-"):
                add("R4", f"block ID ^{bid} does not start with {req}-")

        for a in as_list(fm.get("aliases")):
            owners = alias_index.get(a.strip().casefold(), [])
            others = [o for o in owners if o != rel]
            if others:
                add("R5", f"alias {a!r} also claimed by {', '.join(others)}")

    return findings


def check_c12(slug_index):
    """C12 — index navigation completeness. A folder's index.md should link to every
    child NOTE; a subfolder counts as covered if the index links ANY path under it
    (a primary note or the subfolder index). Report-only."""
    findings = []
    for idx in sorted(VAULT.rglob("index.md")):
        rel = idx.relative_to(VAULT)
        if "_graph" in rel.parts or any(p.startswith(".") for p in rel.parts):
            continue
        d = idx.parent
        text = idx.read_text(encoding="utf-8", errors="replace")
        linked = set()
        for raw in re.findall(r"\[\[([^\]]+)\]\]", text):
            t = raw.split("|")[0].split("#")[0].strip().rstrip("\\").strip()
            if t:
                linked.add(t)
        missing = []
        for f in sorted(d.glob("*.md")):
            if f.name == "index.md":
                continue
            full = f.relative_to(VAULT).as_posix()[:-3]
            if full not in linked and f.stem not in linked:
                missing.append(full)
        for sub in sorted(x for x in d.iterdir() if x.is_dir() and not x.name.startswith(".")):
            subrel = sub.relative_to(VAULT).as_posix()
            if not any(l == subrel or l.startswith(subrel + "/") or l == sub.name for l in linked):
                missing.append(subrel + "/")
        for m in missing:
            findings.append({
                "check": "C12",
                "path": rel.as_posix(),
                "detail": f"index does not link child: {m}",
                "auto_fixable": False,
            })
    return findings


def check_c14():
    """
    C14 — Doubled directory segment: a directory whose name equals its
    immediate parent directory's name (e.g. `documentation/documentation/`).

    Report-only: a merge with potential index.md collisions is not a safe
    mechanical operation of the kind this tool's existing auto-fixes perform.
    EXCEPTION: _graph directory is exempt.
    """
    findings = []

    for dirpath in VAULT.rglob("*"):
        if not dirpath.is_dir():
            continue
        # Exempt _graph at any depth
        rel = dirpath.relative_to(VAULT)
        if "_graph" in rel.parts:
            continue
        # Skip Obsidian system dirs and any hidden dot-directory (.obsidian, .trash, etc.)
        if any(p.startswith(".") for p in rel.parts):
            continue
        if dirpath.name == dirpath.parent.name:
            findings.append({
                "check": "C14",
                "path": rel.as_posix() + "/",
                "detail": f"directory name equals parent directory name: {dirpath.name}",
                "auto_fixable": False,
            })

    return findings


# ── runner ───────────────────────────────────────────────────────────────────

def run_checks(restrict_check=None):
    """
    Run all checks (or a single check if restrict_check is set).
    Returns list of finding dicts.
    """
    if not VAULT.exists():
        die(f"VAULT not found: {VAULT}")

    slug_index = build_slug_index()
    anchor_cache = {}
    alias_index = build_requirement_alias_index()
    all_findings = []

    # Per-file checks (C1–C5, C7–C11, C13, C15–C17)
    for note in iter_notes():
        try:
            text = note.read_text(encoding="utf-8", errors="replace")
        except Exception as exc:
            # Treat unreadable file as C1 finding rather than crashing
            all_findings.append({
                "check": "C1",
                "path": note.relative_to(VAULT).as_posix(),
                "detail": f"unreadable file: {exc}",
                "auto_fixable": False,
            })
            continue

        # Treat empty / no-frontmatter notes gracefully
        fm, body = parse_frontmatter(text)

        checks_map = {
            "C1": lambda: check_c1(note, fm, body),
            "C2": lambda: check_c2(note, fm, body),
            "C3": lambda: check_c3(note, fm, body, slug_index),
            "C4": lambda: check_c4(note, fm, body),
            "C5": lambda: check_c5(note, fm, body),
            "C7": lambda: check_c7(note, fm, body),
            "C8": lambda: check_c8(note, fm, body, slug_index),
            "C9": lambda: check_c9(note, fm, body),
            "C10": lambda: check_c10(note, fm, body),
            "C11": lambda: check_c11(note, fm, body),
            "C13": lambda: check_c13(note, fm, body),
            "C15": lambda: check_c15(note, fm, body, text),
            "C16": lambda: check_c16(note, body, slug_index, anchor_cache),
            "C17": lambda: check_c17(note, fm, body, slug_index, anchor_cache, alias_index),
        }

        for cid, fn in checks_map.items():
            if restrict_check and restrict_check != cid:
                continue
            all_findings.extend(fn())

    # Directory-level checks C6, C12
    if not restrict_check or restrict_check == "C6":
        all_findings.extend(check_c6(slug_index))
    if not restrict_check or restrict_check == "C12":
        all_findings.extend(check_c12(slug_index))
    if not restrict_check or restrict_check == "C14":
        all_findings.extend(check_c14())

    return all_findings


# ── fix helpers ───────────────────────────────────────────────────────────────

def _note_title(md_path):
    """First H1 heading of a note, else a humanized filename."""
    try:
        for line in md_path.read_text(encoding="utf-8", errors="replace").splitlines():
            m = re.match(r"^#\s+(.+)", line.strip())
            if m:
                return m.group(1).strip()
    except Exception:
        pass
    return md_path.stem.replace("-", " ").title()


def build_index_stub(dir_path):
    """Directory-mapping index.md: breadcrumb to the parent index + a Children list
    of the folder's subfolders and notes. An index's job is to map its directory
    tree (concept relationships live in _graph, not here). Top-level subtree roots
    use note_type: hub; deeper folders use note_type: navigation."""
    title = dir_path.name.replace("-", " ").title()
    ntype = "hub" if dir_path.parent == VAULT else "navigation"
    lines = ["---", f"note_type: {ntype}", "tags: [navigation]", "---", "", f"# {title}", ""]
    if dir_path.parent != VAULT:
        prel = dir_path.parent.relative_to(VAULT).as_posix()
        ptitle = dir_path.parent.name.replace("-", " ").title()
        lines += [f"> Part of: [[{prel}/index|{ptitle}]]", ""]
    subdirs = sorted(d for d in dir_path.iterdir() if d.is_dir() and not d.name.startswith("."))
    notes = sorted(f for f in dir_path.iterdir()
                   if f.is_file() and f.suffix == ".md" and f.name != "index.md")
    if subdirs or notes:
        lines += ["## Children", ""]
        for d in subdirs:
            drel = d.relative_to(VAULT).as_posix()
            lines.append(f"- [[{drel}/index|{d.name.replace('-', ' ').title()}]]")
        for f in notes:
            frel = f.relative_to(VAULT).as_posix()[:-3]  # strip .md
            lines.append(f"- [[{frel}|{_note_title(f)}]]")
    return "\n".join(lines).rstrip() + "\n"


def apply_fix(finding, slug_index):
    """
    Apply an auto-fixable finding in place. Returns True if a change was made.
    Idempotent: re-running produces no further changes.
    """
    cid = finding["check"]
    rel = finding["path"]

    # C6: create stub index.md for a directory
    if cid == "C6":
        dir_rel = rel.rstrip("/")
        dir_path = VAULT / dir_rel
        index_path = dir_path / "index.md"
        if index_path.exists():
            return False  # already fixed
        index_path.write_text(build_index_stub(dir_path), encoding="utf-8")
        return True

    # All other fixes operate on .md files
    if rel.endswith("/"):
        return False
    note_path = VAULT / rel
    if not note_path.exists():
        return False

    # C15 R2/R3: regenerate Contents. Works on raw bytes so newline style and the
    # trailing newline survive; R1/R4 are never fixable.
    if cid == "C15":
        if not finding["detail"].startswith(("R2", "R3")) or _shape_scope(rel) != "in":
            return False
        raw = note_path.read_bytes().decode("utf-8", errors="replace")
        new = _fix_c15_text(raw)
        if new is None or new == raw:
            return False
        note_path.write_bytes(new.encode("utf-8"))
        return True

    text = note_path.read_text(encoding="utf-8", errors="replace")
    original = text

    if cid == "C1":
        # Add source_url: na to vault-note missing it
        if "vault-note missing field: source_url" in finding["detail"]:
            if "source_url:" not in text:
                text = re.sub(
                    r"^(note_type:\s*vault-note)",
                    r"\1\nsource_url: na",
                    text, count=1, flags=re.MULTILINE
                )

    elif cid == "C2":
        if "note_type: index" in finding["detail"] and "likely vault-index" not in finding["detail"]:
            text = re.sub(
                r"^(note_type:\s*)index\s*$",
                r"\1vault-index",
                text, count=1, flags=re.MULTILINE
            )
        elif "likely vault-index" in finding["detail"]:
            text = re.sub(
                r"^(note_type:\s*)vault-note\s*$",
                r"\1vault-index",
                text, count=1, flags=re.MULTILINE
            )

    elif cid == "C3":
        # Prefix-truncation fix: [[slug]] → [[subtree/slug]]
        m = re.search(r"\[\[([^\]]+)\]\]", finding["detail"])
        if m:
            raw = m.group(1)
            for subtree in CONCEPT_SUBTREES:
                prefixed = f"{subtree}/{raw}"
                r2, _ = resolve_target(prefixed, slug_index)
                if r2 is not None:
                    # Alias-aware: rewrite [[raw]] and [[raw|Alias]] (incl. the
                    # markdown-table escaped pipe [[raw\|Alias]]), preserving the alias.
                    text = re.sub(
                        r"\[\[" + re.escape(raw) + r"(\\?\|[^\]]*)?\]\]",
                        lambda mm: f"[[{prefixed}{mm.group(1) or ''}]]",
                        text,
                    )
                    break

    elif cid == "C5":
        # Strip vault/ prefix
        m = re.search(r"\[\[vault/([^\]]+)\]\]", finding["detail"])
        if m:
            full_raw = "vault/" + m.group(1)
            stripped = m.group(1)
            text = text.replace(f"[[{full_raw}]]", f"[[{stripped}]]")

    if text != original:
        note_path.write_text(text, encoding="utf-8")
        return True

    return False


# ── commands ──────────────────────────────────────────────────────────────────

def cmd_check(args):
    """check subcommand — report only, no mutation."""
    restrict = args.check if hasattr(args, "check") else None
    findings = _filter_findings(run_checks(restrict_check=restrict),
                                restrict, getattr(args, "prefix", None))
    failing = any(f.get("severity") == "fail" for f in findings)

    if args.json:
        print(json.dumps(findings, ensure_ascii=False, indent=2))
        if failing:
            sys.exit(1)
        return

    # Human-readable report
    print(f"VAULT-LINT  vault=knowledge/vault/  mode=check")
    print()

    # Per-check counts
    from collections import Counter
    counts = Counter(f["check"] for f in findings)
    for cid in ["C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C9", "C10", "C11", "C12", "C13", "C14", "C15", "C16", "C17"]:
        if not restrict or restrict == cid:
            n = counts.get(cid, 0)
            print(f"  {cid}: {n} finding{'s' if n != 1 else ''}")

    print()
    for f in findings:
        tag = f"[{f['check']}][{f['severity']}]" if "severity" in f else f"[{f['check']}]"
        print(f"  {tag} {f['path']}: {f['detail']}")

    fixable = sum(1 for f in findings if f["auto_fixable"])
    print()
    print(f"Total: {len(findings)} finding(s), {fixable} auto-fixable.")
    if failing:
        sys.exit(1)


def _filter_findings(findings, check=None, prefix=None):
    """Keep findings matching --check ID and --prefix P (path startswith)."""
    return [f for f in findings
            if (not check or f["check"] == check)
            and (not prefix or f["path"].startswith(prefix))]


def cmd_fix(args):
    """fix subcommand — apply auto-fixable findings only. Idempotent."""
    restrict = getattr(args, "check", None)
    findings = _filter_findings(run_checks(restrict_check=restrict),
                                restrict, getattr(args, "prefix", None))
    fixable = [f for f in findings if f["auto_fixable"]]

    if not fixable:
        print("Nothing to fix.")
        return

    # Rebuild slug index after each write so prefix-truncation fixes stay accurate
    slug_index = build_slug_index()
    changed = 0
    for f in fixable:
        if apply_fix(f, slug_index):
            print(f"  fixed [{f['check']}] {f['path']}: {f['detail']}")
            changed += 1
        else:
            print(f"  skip  [{f['check']}] {f['path']}: already correct")

    print(f"\nApplied {changed} fix(es).")


def cmd_reindex(args):
    """Regenerate hollow-stub index.md files (no child links and no subsections) as
    directory-mapping indexes. Rich, hand-authored indexes are left untouched."""
    count = 0
    for idx in sorted(VAULT.rglob("index.md")):
        rel = idx.relative_to(VAULT)
        if "_graph" in rel.parts or any(p.startswith(".") for p in rel.parts):
            continue
        _fm, body = parse_frontmatter(idx.read_text(encoding="utf-8", errors="replace"))
        nonblank = [l for l in body.splitlines() if l.strip()]
        # Hollow stub == empty body or a lone heading line. Never clobber prose indexes.
        is_hollow = len(nonblank) <= 1 and (not nonblank or nonblank[0].lstrip().startswith("#"))
        if is_hollow:
            idx.write_text(build_index_stub(idx.parent), encoding="utf-8")
            print(f"  reindexed {rel.as_posix()}")
            count += 1
    print(f"\nReindexed {count} hollow index stub(s).")


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    global CONCEPT_SUBTREES

    p = argparse.ArgumentParser(description="Vault linter — static checks for knowledge/vault/")
    p.add_argument(
        "--subtrees",
        metavar="A,B,C",
        help="Comma-separated concept subtrees (default: auto-discover top-level "
             "folders under vault/, excluding _graph/)",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    s_check = sub.add_parser("check", help="Report findings without mutating files")
    s_check.add_argument("--json", action="store_true", help="Emit findings as JSON list")
    s_check.add_argument("--check", metavar="ID", help="Restrict to one check ID (e.g. C8)")

    s_check.add_argument("--prefix", metavar="P", help="Restrict to paths starting with P (vault-relative)")

    s_fix = sub.add_parser("fix", help="Apply auto-fixable findings only")
    s_fix.add_argument("--check", metavar="ID", help="Fix only this check ID (e.g. C15)")
    s_fix.add_argument("--prefix", metavar="P", help="Fix only paths starting with P (vault-relative)")
    sub.add_parser("reindex", help="Regenerate hollow-stub index.md files as directory maps")

    args = p.parse_args()

    if not VAULT.is_dir():
        die(f"vault not found at {VAULT} — set WORKSPACE_ROOT or run from the workspace root")

    if args.subtrees:
        CONCEPT_SUBTREES = {s.strip() for s in args.subtrees.split(",") if s.strip()}
    else:
        CONCEPT_SUBTREES = discover_subtrees()
    if not CONCEPT_SUBTREES:
        die(f"no concept subtrees found under {VAULT} — create at least one, or pass --subtrees")

    {
        "check":   cmd_check,
        "fix":     cmd_fix,
        "reindex": cmd_reindex,
    }[args.cmd](args)


if __name__ == "__main__":
    main()
