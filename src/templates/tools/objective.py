#!/usr/bin/env python3
"""Objective state management — deterministic bookkeeping, no LLM."""

import argparse
import os
import re
import sys
from datetime import date
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

WORKSPACE = Path(os.environ.get("WORKSPACE_ROOT") or os.getcwd()).resolve()
OBJECTIVES_DIR = WORKSPACE / "control-plane" / "objectives"
PORTFOLIO_INDEX = OBJECTIVES_DIR / "index.md"

# Ordered enums, mirroring workstream.py's VALID_PHASES. Kept as module constants
# so the CLI, its error messages, and any caller read from one definition.
VALID_HEALTH = ("on-track", "at-risk", "blocked", "stale")
VALID_CADENCE = ("weekly", "bi-weekly", "monthly", "quarterly", "semi-annual", "annual")

def die(msg):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)

def ensure_portfolio_index():
    """Create the objectives portfolio index if it's missing (header-agnostic insert anchors on the separator)."""
    if not PORTFOLIO_INDEX.exists():
        OBJECTIVES_DIR.mkdir(parents=True, exist_ok=True)
        PORTFOLIO_INDEX.write_text(
            "# Objectives\n\n"
            "## Active\n\n"
            "| Objective | Description | Status |\n"
            "|---|---|---|\n\n"
            "## Complete\n\n"
            "| Objective | Description | Completed | Key Outcome |\n"
            "|---|---|---|---|\n",
            encoding="utf-8",
        )

def today():
    return date.today().strftime("%Y-%m-%d")

def kebab_ok(name):
    return bool(re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name))

def obj_dir(name):
    if not kebab_ok(name):
        die(f"invalid objective name '{name}' — must be kebab-case (a-z, 0-9, hyphens); no path separators")
    p = OBJECTIVES_DIR / name
    if not p.exists():
        die(f"objective '{name}' not found at {p}")
    return p

def read_index(name):
    p = obj_dir(name) / "index.md"
    if not p.exists():
        die(f"index.md not found for '{name}'")
    return p, p.read_text(encoding="utf-8")

def _fm_bounds(text):
    """Line indices [start, end) of the frontmatter body, exclusive of both fences.

    Returns None when the file has no terminated frontmatter block. Every helper
    below scopes itself to this range: an unscoped `^field:` regex also matches a
    same-named line in the document body, so a read can return body text and a
    write can silently rewrite it.
    """
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].rstrip() != "---":
        return None
    for i in range(1, len(lines)):
        if lines[i].rstrip() == "---":
            return 1, i
    return None

def _line_parts(raw):
    """Split a raw line into (content, terminator), preserving CRLF vs LF."""
    content = raw.rstrip("\r\n")
    return content, raw[len(content):]

def fm_get(text, field):
    bounds = _fm_bounds(text)
    if not bounds:
        return None
    start, end = bounds
    lines = text.splitlines(keepends=True)
    pat = re.compile(rf"^{re.escape(field)}:\s*(.+)$")
    for i in range(start, end):
        m = pat.match(_line_parts(lines[i])[0])
        if m:
            return m.group(1).strip().strip('"')
    return None

def fm_set(text, field, value):
    """Set a frontmatter field, inserting before the closing --- when absent."""
    bounds = _fm_bounds(text)
    if not bounds:
        die("cannot set frontmatter field: file does not open with a terminated '---' fence")
    start, end = bounds
    lines = text.splitlines(keepends=True)
    pat = re.compile(rf"^({re.escape(field)}:\s*).*$")
    for i in range(start, end):
        content, term = _line_parts(lines[i])
        m = pat.match(content)
        if m:
            lines[i] = f"{m.group(1)}{value}{term}"
            return "".join(lines)
    term = _line_parts(lines[end - 1])[1] or "\n" if end > start else "\n"
    lines.insert(end, f"{field}: {value}{term}")
    return "".join(lines)

def fm_add_field_after(text, after_field, new_field, value):
    """Insert a new frontmatter field after another field (no-op if already present)."""
    bounds = _fm_bounds(text)
    if not bounds:
        return text
    start, end = bounds
    lines = text.splitlines(keepends=True)
    present = re.compile(rf"^{re.escape(new_field)}:")
    anchor = re.compile(rf"^{re.escape(after_field)}:")
    for i in range(start, end):
        if present.match(_line_parts(lines[i])[0]):
            return text  # already present
    for i in range(start, end):
        content, term = _line_parts(lines[i])
        if anchor.match(content):
            lines.insert(i + 1, f"{new_field}: {value}{term or chr(10)}")
            return "".join(lines)
    return text  # anchor field absent — leave unchanged

# ---------------------------------------------------------------------------
# Portfolio-index helpers (grouping-aware)
#
# The Active table may be split across ### subgroup headings, each with its own
# header + separator row. Anything that walks the table must reset per subgroup,
# or every subgroup's header row after the first is mistaken for a data row.
# ---------------------------------------------------------------------------

SEPARATOR_RE = re.compile(r"^\|[\s\-|]+\|$")

def parse_index_rows(text):
    """Return the data rows of the Active table, across all ### subgroups."""
    rows, in_active, after_sep = [], False, False
    for line in text.splitlines():
        if line.startswith("## Active"):
            in_active, after_sep = True, False
            continue
        if line.startswith("## "):
            in_active = False
            continue
        if not in_active:
            continue
        if line.startswith("### "):
            after_sep = False          # new subgroup — its header row follows
            continue
        if SEPARATOR_RE.match(line):
            after_sep = True
            continue
        if after_sep and line.startswith("|") and "*(none yet)*" not in line:
            rows.append(line)
    return rows

def index_insert_point(text, subgroup=None):
    """Line index just after the separator row of the Active table.

    With `subgroup`, targets that ### subgroup's separator; without, the first
    separator in Active. Returns None if no matching separator is found.
    """
    in_active, current = False, None
    for i, line in enumerate(text.splitlines()):
        if line.startswith("## Active"):
            in_active, current = True, None
            continue
        if line.startswith("## "):
            in_active = False
            continue
        if not in_active:
            continue
        if line.startswith("### "):
            current = line[4:].strip()
            continue
        if SEPARATOR_RE.match(line):
            if subgroup is None or (current and current.startswith(subgroup)):
                return i + 1
    return None

def normalize_workstream_ref(ref):
    """Bare name → workstreams/<name>; explicit paths (incl. _log/ entries) pass through."""
    return ref if "/" in ref else f"workstreams/{ref}"

def workstream_ref_exists(ref):
    """True if the reference resolves on disk, as a folder index or a _log/ entry."""
    base = WORKSPACE / "control-plane" / ref
    return (base / "index.md").exists() or base.exists() or base.with_suffix(".md").exists()

# ---------------------------------------------------------------------------
# Section helpers
# ---------------------------------------------------------------------------

def _section_bounds(text, header):
    """Return (start_line_idx, end_line_idx_exclusive) of a markdown section."""
    lines = text.splitlines(keepends=True)
    start = None
    for i, ln in enumerate(lines):
        if re.match(rf"^{re.escape(header)}\s*$", ln.rstrip()):
            start = i
            break
    if start is None:
        return None, None
    end = len(lines)
    for i in range(start + 1, len(lines)):
        if re.match(r"^#{1,6} ", lines[i]):
            end = i
            break
    return start, end

def section_text(text, header):
    s, e = _section_bounds(text, header)
    if s is None:
        return None
    return "".join(text.splitlines(keepends=True)[s:e])

TRAILING_SECTION = "## Related Notes"

def replace_section(text, header, new_section_text):
    """Replace an existing section (header through next header) with new_section_text.

    When the section is absent it is inserted immediately before ## Related Notes,
    which is canonically last. Appending to end of file would strand managed
    sections (Key Results, Milestones, Workstreams) below it.
    """
    lines = text.splitlines(keepends=True)
    s, e = _section_bounds(text, header)
    if s is None:
        anchor, _ = _section_bounds(text, TRAILING_SECTION)
        if anchor is None:
            return text + "\n" + new_section_text
        return "".join(lines[:anchor]) + new_section_text + "".join(lines[anchor:])
    return "".join(lines[:s]) + new_section_text + "".join(lines[e:])

# ---------------------------------------------------------------------------
# Key-Results helpers
# ---------------------------------------------------------------------------
KR_HEADER = "## Key Results"
KR_SEP    = "|---|---|---|---|"

def _parse_kr_table(text):
    """Return list of (result, current, target, updated) dicts."""
    sec = section_text(text, KR_HEADER)
    if not sec:
        return []
    rows = []
    in_table = False
    for ln in sec.splitlines():
        if re.match(r"^\|[\s\-|]+\|$", ln):
            in_table = True
            continue
        if in_table and ln.startswith("|"):
            parts = [c.strip() for c in ln.strip("|").split("|")]
            if len(parts) >= 4 and "*(none yet)*" not in parts[0]:
                rows.append({"result": parts[0], "current": parts[1],
                             "target": parts[2], "updated": parts[3]})
    return rows

def _render_kr_section(rows):
    lines = [f"{KR_HEADER}\n", "\n",
             "| Result | Current | Target | Updated |\n",
             "|---|---|---|---|\n"]
    if not rows:
        lines.append("| *(none yet)* | | | |\n")
    else:
        for r in rows:
            lines.append(f"| {r['result']} | {r['current']} | {r['target']} | {r['updated']} |\n")
    lines.append("\n")
    return "".join(lines)

# ---------------------------------------------------------------------------
# Milestone helpers
# ---------------------------------------------------------------------------
MS_HEADER = "## Milestones"

def _parse_milestones(text):
    """Return list of (done: bool, text: str)."""
    sec = section_text(text, MS_HEADER)
    if not sec:
        return []
    items = []
    for ln in sec.splitlines():
        m = re.match(r"^- \[(x| )\] (.+)$", ln)
        if m:
            items.append({"done": m.group(1) == "x", "text": m.group(2)})
    return items

def _render_milestone_section(items):
    lines = [f"{MS_HEADER}\n", "\n"]
    if not items:
        lines.append("*(none yet)*\n")
    else:
        for it in items:
            mark = "x" if it["done"] else " "
            lines.append(f"- [{mark}] {it['text']}\n")
    lines.append("\n")
    return "".join(lines)

# ---------------------------------------------------------------------------
# Workstreams helpers
# ---------------------------------------------------------------------------
WORKSTREAMS_HEADER = "## Workstreams"
WORKSTREAMS_SEP    = "|---|---|---|"

def _parse_workstreams(text):
    sec = section_text(text, WORKSTREAMS_HEADER)
    if not sec:
        return []
    rows = []
    in_table = False
    for ln in sec.splitlines():
        if re.match(r"^\|[\s\-|]+\|$", ln):
            in_table = True
            continue
        if in_table and ln.startswith("|"):
            parts = [c.strip() for c in ln.strip("|").split("|")]
            if len(parts) >= 3 and "*(none yet)*" not in parts[0]:
                rows.append({"workstream": parts[0], "status": parts[1], "linked": parts[2]})
    return rows

def _render_workstreams_section(rows):
    lines = [f"{WORKSTREAMS_HEADER}\n", "\n",
             "| Workstream | Status | Linked |\n",
             "|---|---|---|\n"]
    if not rows:
        lines.append("| *(none yet)* | | |\n")
    else:
        for r in rows:
            lines.append(f"| {r['workstream']} | {r['status']} | {r['linked']} |\n")
    lines.append("\n")
    return "".join(lines)

# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_list(_args):
    if not PORTFOLIO_INDEX.exists():
        die(f"portfolio index not found: {PORTFOLIO_INDEX}")
    for row in parse_index_rows(PORTFOLIO_INDEX.read_text(encoding="utf-8")):
        print(row)


def cmd_status(args):
    _, text = read_index(args.name)
    for field, key in [
        ("objective", "objective"), ("status", "status"), ("health", "health"),
        ("cadence", "cadence"), ("created", "created"), ("completed", "completed"),
    ]:
        val = fm_get(text, key)
        if val:
            print(f"{field:<12} {val}")

    # Key Results
    krs = _parse_kr_table(text)
    if krs:
        print(f"\nkey results ({len(krs)}):")
        for r in krs:
            print(f"  {r['result']:<40} {r['current']:>12} / {r['target']:<12} (updated {r['updated']})")
    else:
        print("\nkey results: (none)")

    # Milestones
    ms = _parse_milestones(text)
    done = sum(1 for m in ms if m["done"])
    total = len(ms)
    print(f"\nmilestones:  {done}/{total} done")
    for m in ms:
        mark = "x" if m["done"] else " "
        print(f"  [{mark}] {m['text']}")

    # Workstreams
    workstreams = _parse_workstreams(text)
    if workstreams:
        active = sum(1 for m in workstreams if m["status"] == "active")
        summary = f"{len(workstreams)}" + (f", {active} active" if active else "")
        print(f"\nworkstreams ({summary}):")
        for m in workstreams:
            print(f"  {m['workstream']:<58} {m['status']}")
    else:
        print("\nworkstreams:    (none)")

    # Recent decisions
    dec_m = re.search(r"## Key Decisions Log\n\n[^\n]+\n[^\n]+\n((?:\|[^\n]+\n)*)", text)
    if dec_m:
        rows = [r for r in dec_m.group(1).strip().splitlines() if "append-only" not in r]
        if rows:
            print(f"\nrecent decisions ({len(rows)} total):")
            for row in rows[-3:]:
                print(f"  {row.strip()}")


def cmd_create(args):
    name = args.name
    if not kebab_ok(name):
        die(f"invalid objective name '{name}' — must be kebab-case (a-z, 0-9, hyphens); no path separators")
    dest = OBJECTIVES_DIR / name
    if dest.exists():
        die(f"'{name}' already exists")

    title   = args.title or name.replace("-", " ").title()
    today_s = today()
    origin  = getattr(args, "origin", None) or ""
    origin_line = ""
    if origin:
        origin_line = (
            f"*Promoted from* [{origin}](../../{origin}/index.md)*, which outgrew its tier. "
            "That work keeps its original scope and closes itself out under this objective "
            "rather than being rewritten — the promotion gives it a parent, it does not "
            "change what it was for.*\n\n")

    index_md = f"""---
objective: {name}
status: active
health: on-track
cadence: quarterly
created: {today_s}
promoted_from: "{origin}"
tags: [objective]
---

# {title} — Objective Context

## Objective

{origin_line}*What this is and why it matters. Tie to strategy where relevant.*

## Success Criteria

- *concrete, verifiable criterion*

## Key Results

| Result | Current | Target | Updated |
|---|---|---|---|
| *(none yet)* | | | |

## Milestones

*(none yet)*

## Workstreams

| Workstream | Status | Linked |
|---|---|---|
| *(none yet)* | | |

## Dependencies

- *dependency name — what's needed, from whom, why*

## Key Decisions Log

| Decision | Rationale | Date |
|---|---|---|
| *(append-only; never truncated)* | | |

## Definition of Done

*Specific conditions under which this objective closes.*

## Related Notes

- *links to child workstreams, parent strategy, dependent objectives*
"""

    dest.mkdir(parents=True)
    (dest / "index.md").write_text(index_md, encoding="utf-8")
    print(f"created: {dest / 'index.md'}")

    ensure_portfolio_index()
    portfolio = PORTFOLIO_INDEX.read_text(encoding="utf-8")
    new_row = f"| [{name}]({name}/index.md) | *add description* | Active |"
    at = index_insert_point(portfolio, getattr(args, "group", None))
    if at is None:
        die(
            f"could not find an Active table separator in {PORTFOLIO_INDEX}"
            + (f" for subgroup '{args.group}'" if getattr(args, "group", None) else "")
        )
    lines = [ln for ln in portfolio.splitlines()
             if "*(none yet)*" not in ln or not ln.startswith("|")]
    # Re-resolve against the filtered list so the insert point stays correct.
    at = index_insert_point("\n".join(lines), getattr(args, "group", None))
    lines.insert(at, new_row)
    portfolio = "\n".join(lines) + "\n"
    PORTFOLIO_INDEX.write_text(portfolio, encoding="utf-8")
    print(f"updated: {PORTFOLIO_INDEX}")


def review_dir(name):
    return obj_dir(name) / "reviews"

def render_review(name, text, when):
    """Build a review entry from the objective's current tracked state.

    Read-only with respect to index.md — the review is a point-in-time snapshot,
    written alongside the anchor rather than appended to it. This is what gives
    KRs a history: `update-kr` overwrites `current` in place, so without a dated
    snapshot the trajectory is lost on every update.
    """
    krs = _parse_kr_table(text)
    milestones = _parse_milestones(text)
    workstreams = _parse_workstreams(text)
    health = fm_get(text, "health") or "—"
    cadence = fm_get(text, "cadence") or "—"
    done = sum(1 for m in milestones if m["done"])

    out = [
        "---",
        "note_type: objective-review",
        f"objective: {name}",
        f"review_date: {when}",
        f"health: {health}",
        f"cadence: {cadence}",
        f"tags: [objective/{name}, review]",
        "---",
        f"# {name} — Review {when}",
        "",
        f"Point-in-time snapshot. Health **{health}**, cadence **{cadence}**.",
        "",
        "## Key Results at Review",
        "",
    ]
    if krs:
        out += ["| Result | Current | Target | Last Updated |", "|---|---|---|---|"]
        out += [f"| {r['result']} | {r['current']} | {r['target']} | {r['updated']} |"
                for r in krs]
    else:
        out.append("*No Key Results set.* Record here why — a deliberately empty KR set "
                   "is a finding, not an omission.")
    out += ["", f"## Milestones — {done}/{len(milestones)} done", ""]
    out += ([f"- [{'x' if m['done'] else ' '}] {m['text']}" for m in milestones]
            or ["*(none)*"])
    out += ["", "## Workstreams", ""]
    out += ([f"- `{w['workstream']}` — {w['status']}" for w in workstreams]
            or ["*(none linked)*"])
    out += [
        "", "## Health Assessment", "",
        f"**{health}** — *state the evidence for this call; cite lines in `index.md` "
        "or a linked workstream. A health value without evidence is an assertion.*",
        "", "## Movement Since Last Review", "",
        "*What changed, what did not, and why. Compare against the previous entry in "
        "this folder.*",
        "", "## Decisions Taken", "",
        "*Anything decided at this review. Material decisions also belong in the "
        "objective's append-only `## Key Decisions Log`.*",
        "", "## Harness Friction", "",
        "*Only how the objective machinery performed this cycle — a command that "
        "misbehaved, an instruction that was wrong, a review step that could not be "
        "carried out. Not progress, not blockers on the work itself. Would it still "
        "be true for an unrelated objective? If not, it belongs above. Usually empty; "
        "carry anything unresolved to `control-plane/_harness/friction.md`.*",
        "", "## Next Review", "",
        f"*Per cadence `{cadence}`.*", "",
    ]
    return "\n".join(out)

def cmd_review(args):
    _, text = read_index(args.name)
    when = args.date or today()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", when):
        die(f"invalid date '{when}' — expected YYYY-MM-DD")
    rdir = review_dir(args.name)
    rdir.mkdir(parents=True, exist_ok=True)
    dest = rdir / f"{when}.md"
    if dest.exists() and not args.force:
        die(f"review already exists: {dest} — pass --force to overwrite")
    dest.write_text(render_review(args.name, text, when), encoding="utf-8")
    print(f"review written: {dest}")


def cmd_log_decision(args):
    idx_path, idx_text = read_index(args.name)
    new_row = f"| {args.decision} | {args.rationale} | {today()} |"
    idx_text = re.sub(
        r"(## Key Decisions Log\n\n\|[^\n]+\n\|[-|]+\n(?:\|[^\n]+\n)*)",
        f"\\g<1>{new_row}\n",
        idx_text
    )
    idx_path.write_text(idx_text, encoding="utf-8")
    print(f"logged: {args.decision}")


def cmd_complete(args):
    idx_path, idx_text = read_index(args.name)
    today_s = today()

    if "completed:" in idx_text:
        idx_text = fm_set(idx_text, "completed", today_s)
    else:
        idx_text = idx_text.replace("status: active", f"status: complete\ncompleted: {today_s}", 1)
    idx_text = fm_set(idx_text, "status", "complete")
    idx_path.write_text(idx_text, encoding="utf-8")

    portfolio = PORTFOLIO_INDEX.read_text(encoding="utf-8")
    portfolio = re.sub(
        rf"(\|\s*\[{re.escape(args.name)}\][^\n]+\|)\s*Active\s*\|",
        f"\\g<1> Complete |",
        portfolio
    )
    PORTFOLIO_INDEX.write_text(portfolio, encoding="utf-8")
    print(f"completed: {args.name}  (folder retained)")


def cmd_health(args):
    if args.value not in VALID_HEALTH:
        die(f"health must be one of: {', '.join(VALID_HEALTH)}")
    idx_path, idx_text = read_index(args.name)
    idx_text = fm_set(idx_text, "health", args.value)
    idx_path.write_text(idx_text, encoding="utf-8")
    print(f"health set: {args.value}")


def cmd_set_cadence(args):
    if args.cadence not in VALID_CADENCE:
        die(f"cadence must be one of: {', '.join(VALID_CADENCE)}")
    idx_path, idx_text = read_index(args.name)
    idx_text = fm_set(idx_text, "cadence", args.cadence)
    idx_path.write_text(idx_text, encoding="utf-8")
    print(f"cadence set: {args.cadence}")


def cmd_add_kr(args):
    idx_path, idx_text = read_index(args.name)
    rows = _parse_kr_table(idx_text)
    # Idempotent by result label
    if any(r["result"] == args.result for r in rows):
        die(f"KR already exists: {args.result}")
    rows.append({"result": args.result, "current": "—", "target": args.target,
                 "updated": today()})
    idx_text = replace_section(idx_text, KR_HEADER, _render_kr_section(rows))
    idx_path.write_text(idx_text, encoding="utf-8")
    print(f"added KR: {args.result}")


def cmd_update_kr(args):
    idx_path, idx_text = read_index(args.name)
    rows = _parse_kr_table(idx_text)
    found = False
    for r in rows:
        if r["result"] == args.result:
            r["current"] = args.current
            r["updated"] = today()
            found = True
            break
    if not found:
        die(f"KR not found: {args.result}")
    idx_text = replace_section(idx_text, KR_HEADER, _render_kr_section(rows))
    idx_path.write_text(idx_text, encoding="utf-8")
    print(f"updated KR: {args.result} → {args.current}")


def cmd_add_milestone(args):
    idx_path, idx_text = read_index(args.name)
    items = _parse_milestones(idx_text)
    if any(it["text"] == args.text for it in items):
        die(f"milestone already exists: {args.text}")
    items.append({"done": False, "text": args.text})
    idx_text = replace_section(idx_text, MS_HEADER, _render_milestone_section(items))
    idx_path.write_text(idx_text, encoding="utf-8")
    print(f"added milestone: {args.text}")


def cmd_check_milestone(args):
    idx_path, idx_text = read_index(args.name)
    items = _parse_milestones(idx_text)
    found = False
    for it in items:
        if it["text"] == args.text:
            it["done"] = True
            found = True
            break
    if not found:
        die(f"milestone not found: {args.text}")
    idx_text = replace_section(idx_text, MS_HEADER, _render_milestone_section(items))
    idx_path.write_text(idx_text, encoding="utf-8")
    print(f"checked milestone: {args.text}")


VALID_LINK_STATUSES = ("active", "complete", "paused", "abandoned")

def cmd_link_workstream(args):
    idx_path, idx_text = read_index(args.objective)
    rows = _parse_workstreams(idx_text)
    ref = normalize_workstream_ref(args.workstream)
    status = getattr(args, "status", None) or "active"
    if status not in VALID_LINK_STATUSES:
        die(f"invalid status '{status}' — must be one of: {', '.join(VALID_LINK_STATUSES)}")
    if not workstream_ref_exists(ref):
        die(f"workstream not found on disk: control-plane/{ref} — "
            "check the name, or pass an explicit path such as "
            "workstreams/_log/YYYY-MM-DD-name")
    if any(r["workstream"] == ref for r in rows):
        print(f"already linked: {ref}")
        return
    rows.append({"workstream": ref, "status": status,
                 "linked": today()})
    idx_text = replace_section(idx_text, WORKSTREAMS_HEADER, _render_workstreams_section(rows))
    idx_path.write_text(idx_text, encoding="utf-8")
    print(f"linked workstream: {ref}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    p = argparse.ArgumentParser(description="Objective state management")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list")

    for name_cmd in ("status", "complete"):
        s = sub.add_parser(name_cmd)
        s.add_argument("name")

    s = sub.add_parser("create")
    s.add_argument("name")
    s.add_argument("--title")
    s.add_argument("--from", dest="origin", metavar="PATH",
                   help="the workstream or cadence that outgrew its tier, e.g. "
                        "workstreams/vault-reindex. Records the promotion.")
    s.add_argument("--group",
                   help="### subgroup of the Active table to insert into "
                        "(e.g. 'Infrastructure Builds'); defaults to the first")

    s = sub.add_parser("review",
                       help="scaffold a dated review entry in objectives/<name>/reviews/")
    s.add_argument("name")
    s.add_argument("--date", help="review date (YYYY-MM-DD); defaults to today")
    s.add_argument("--force", action="store_true",
                   help="overwrite an existing entry for that date")

    s = sub.add_parser("log-decision")
    s.add_argument("name")
    s.add_argument("decision")
    s.add_argument("rationale")

    s = sub.add_parser("health")
    s.add_argument("name")
    s.add_argument("value")

    s = sub.add_parser("set-cadence")
    s.add_argument("name")
    s.add_argument("cadence")

    s = sub.add_parser("add-kr")
    s.add_argument("name")
    s.add_argument("result")
    s.add_argument("target")

    s = sub.add_parser("update-kr")
    s.add_argument("name")
    s.add_argument("result")
    s.add_argument("current")

    s = sub.add_parser("add-milestone")
    s.add_argument("name")
    s.add_argument("text")

    s = sub.add_parser("check-milestone")
    s.add_argument("name")
    s.add_argument("text")

    s = sub.add_parser("link-workstream")
    s.add_argument("objective")
    s.add_argument("workstream",
                   help="bare name, workstreams/<name>, or workstreams/_log/<entry>")
    s.add_argument("--status", choices=VALID_LINK_STATUSES, default="active",
                   help="link status (default: active)")

    args = p.parse_args()
    {
        "list":            cmd_list,
        "status":          cmd_status,
        "create":          cmd_create,
        "log-decision":    cmd_log_decision,
        "complete":        cmd_complete,
        "health":          cmd_health,
        "set-cadence":     cmd_set_cadence,
        "add-kr":          cmd_add_kr,
        "update-kr":       cmd_update_kr,
        "add-milestone":   cmd_add_milestone,
        "check-milestone": cmd_check_milestone,
        "link-workstream":    cmd_link_workstream,
        "review":             cmd_review,
    }[args.cmd](args)


if __name__ == "__main__":
    main()
