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

def fm_get(text, field):
    m = re.search(rf"^{re.escape(field)}:\s*(.+)$", text, re.MULTILINE)
    return m.group(1).strip().strip('"') if m else None

def fm_set(text, field, value):
    """Set an existing frontmatter field. Adds field before closing --- if absent."""
    if re.search(rf"^{re.escape(field)}:", text, re.MULTILINE):
        return re.sub(
            rf"^({re.escape(field)}:\s*).*$",
            f"\\g<1>{value}",
            text, flags=re.MULTILINE, count=1
        )
    # Insert before the closing --- of frontmatter
    return re.sub(r"^(---\s*\n)", f"{field}: {value}\n\\g<1>", text, count=1,
                  flags=re.MULTILINE)

def fm_add_field_after(text, after_field, new_field, value):
    """Insert a new frontmatter field after another field (no-op if already present)."""
    if re.search(rf"^{re.escape(new_field)}:", text, re.MULTILINE):
        return text  # already present
    return re.sub(
        rf"^({re.escape(after_field)}:.*$)",
        f"\\g<1>\n{new_field}: {value}",
        text, flags=re.MULTILINE, count=1
    )

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

def replace_section(text, header, new_section_text):
    """Replace an existing section (header through next header) with new_section_text."""
    lines = text.splitlines(keepends=True)
    s, e = _section_bounds(text, header)
    if s is None:
        # Append before the last section (## Related Notes) or at end
        text += "\n" + new_section_text
        return text
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
    in_active = False
    after_sep = False
    for line in PORTFOLIO_INDEX.read_text(encoding="utf-8").splitlines():
        if line.startswith("## Active"):
            in_active, after_sep = True, False
            continue
        if line.startswith("## "):
            in_active = False
            continue
        if not in_active:
            continue
        if re.match(r"^\|[\s\-|]+\|$", line):
            after_sep = True
            continue
        if after_sep and line.startswith("|") and "*(none yet)*" not in line:
            print(line)


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
        print(f"\nworkstreams ({len(workstreams)}):")
        for m in workstreams:
            print(f"  {m['workstream']}")
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

    index_md = f"""---
objective: {name}
status: active
health: on-track
cadence: quarterly
created: {today_s}
tags: [objective]
---

# {title} — Objective Context

## Objective

*What this is and why it matters. Tie to strategy where relevant.*

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
    out, in_active, inserted = [], False, False
    for line in portfolio.splitlines():
        if line.startswith("## Active"):
            in_active = True
        elif line.startswith("## "):
            in_active = False
        if in_active and "*(none yet)*" in line:
            continue
        out.append(line)
        if in_active and not inserted and re.match(r"^\|[\s\-|]+\|$", line):
            out.append(new_row)
            inserted = True
    portfolio = "\n".join(out) + "\n"
    PORTFOLIO_INDEX.write_text(portfolio, encoding="utf-8")
    print(f"updated: {PORTFOLIO_INDEX}")


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
    valid = {"on-track", "at-risk", "blocked", "stale"}
    if args.value not in valid:
        die(f"health must be one of: {', '.join(sorted(valid))}")
    idx_path, idx_text = read_index(args.name)
    idx_text = fm_set(idx_text, "health", args.value)
    idx_path.write_text(idx_text, encoding="utf-8")
    print(f"health set: {args.value}")


def cmd_set_cadence(args):
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


def cmd_link_workstream(args):
    idx_path, idx_text = read_index(args.objective)
    rows = _parse_workstreams(idx_text)
    # Normalise: bare name → workstreams/<name>
    ref = args.workstream if "/" in args.workstream else f"workstreams/{args.workstream}"
    if any(r["workstream"] == ref for r in rows):
        print(f"already linked: {ref}")
        return
    rows.append({"workstream": ref, "status": "active",
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
    s.add_argument("workstream")

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
    }[args.cmd](args)


if __name__ == "__main__":
    main()
