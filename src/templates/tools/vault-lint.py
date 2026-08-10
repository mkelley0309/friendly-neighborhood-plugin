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
    for line in fm_block.splitlines():
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


# ── runner ───────────────────────────────────────────────────────────────────

def run_checks(restrict_check=None):
    """
    Run all checks (or a single check if restrict_check is set).
    Returns list of finding dicts.
    """
    if not VAULT.exists():
        die(f"VAULT not found: {VAULT}")

    slug_index = build_slug_index()
    all_findings = []

    # Per-file checks (C1–C5, C7–C9)
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
    findings = run_checks(restrict_check=restrict)

    if args.json:
        print(json.dumps(findings, ensure_ascii=False, indent=2))
        return

    # Human-readable report
    print(f"VAULT-LINT  vault=knowledge/vault/  mode=check")
    print()

    # Per-check counts
    from collections import Counter
    counts = Counter(f["check"] for f in findings)
    for cid in ["C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C9", "C10", "C11", "C12"]:
        if not restrict or restrict == cid:
            n = counts.get(cid, 0)
            print(f"  {cid}: {n} finding{'s' if n != 1 else ''}")

    print()
    for f in findings:
        print(f"  [{f['check']}] {f['path']}: {f['detail']}")

    fixable = sum(1 for f in findings if f["auto_fixable"])
    print()
    print(f"Total: {len(findings)} finding(s), {fixable} auto-fixable.")


def cmd_fix(args):
    """fix subcommand — apply auto-fixable findings only. Idempotent."""
    findings = run_checks()
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

    sub.add_parser("fix", help="Apply auto-fixable findings only")
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
