#!/usr/bin/env python3
"""Patrol (light unit) state management — lightweight, no phase machine, no LLM."""

import argparse
import os
import re
import shutil
import sys
from datetime import date
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

WORKSPACE = Path(os.environ.get("WORKSPACE_ROOT") or os.getcwd()).resolve()
PATROLS_DIR = WORKSPACE / "control-plane" / "patrols"
PORTFOLIO_INDEX = PATROLS_DIR / "index.md"

# ── helpers ───────────────────────────────────────────────────────────────────

def die(msg):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)

def today():
    return date.today().strftime("%Y-%m-%d")

def kebab_ok(name):
    return bool(re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name))

def patrol_dir(name):
    if not kebab_ok(name):
        die(f"invalid patrol name '{name}' — must be kebab-case (a-z, 0-9, hyphens); no path separators")
    p = PATROLS_DIR / name
    if not p.exists():
        die(f"patrol '{name}' not found at {p}")
    return p

def read_index(name):
    p = patrol_dir(name) / "index.md"
    if not p.exists():
        die(f"index.md not found for '{name}'")
    return p, p.read_text(encoding="utf-8")

def fm_get(text, field):
    m = re.search(rf"^{re.escape(field)}:[^\S\n]*([^\r\n]+)", text, re.MULTILINE)
    return m.group(1).strip().strip('"') if m else None

def fm_set(text, field, value):
    return re.sub(
        rf"^({re.escape(field)}:\s*).*$",
        f"\\g<1>{value}",
        text, flags=re.MULTILINE, count=1
    )

def ensure_portfolio_index():
    if not PORTFOLIO_INDEX.exists():
        PATROLS_DIR.mkdir(parents=True, exist_ok=True)
        PORTFOLIO_INDEX.write_text(
            "# Patrols\n\n"
            "## Active\n\n"
            "| Patrol | Description | Parent | Started |\n"
            "|---|---|---|---|\n\n"
            "## Complete\n\n"
            "| Patrol | Description | Completed |\n"
            "|---|---|---|\n",
            encoding="utf-8",
        )

# ── commands ──────────────────────────────────────────────────────────────────

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


def cmd_create(args):
    name   = args.name
    if not kebab_ok(name):
        die(f"invalid patrol name '{name}' — must be kebab-case (a-z, 0-9, hyphens); no path separators")
    dest   = PATROLS_DIR / name
    if dest.exists():
        die(f"'{name}' already exists")

    parent  = args.parent or "null"
    title   = args.title or name.replace("-", " ").title()
    today_s = today()
    parent_q = f'"{parent}"' if parent != "null" else "null"
    if parent != "null":
        _rel = parent if "/" in parent else f"workstreams/{parent}"
        parent_link = f"[{_rel}](../../{_rel}/index.md)"
    else:
        parent_link = "—"

    index_md = f"""---
patrol: {name}
status: active
parent: {parent_q}
started: {today_s}
completed:
validated:
tags: [patrol/{name}]
---

# {title}

## Assignment

*What this patrol is — what you understand the job to be, in a sentence or two. This understanding is the patrol's real value.*

## Checklist

- [ ] *step placeholder*

## Handoff

*One line for the next patrol, if anyone picks up from here.*

## Lessons

*One line worth repeating or avoiding, if you learned something.*

## Cross-links

- **Parent:** {parent_link}
"""

    dest.mkdir(parents=True)
    (dest / "index.md").write_text(index_md, encoding="utf-8")
    print(f"created: {dest / 'index.md'}")

    ensure_portfolio_index()
    portfolio = PORTFOLIO_INDEX.read_text(encoding="utf-8")
    if parent != "null":
        rel = parent if "/" in parent else f"workstreams/{parent}"
        parent_col = f"[{rel}](../{rel}/index.md)"
    else:
        parent_col = "—"
    new_row = f"| [{name}]({name}/index.md) | *add description* | {parent_col} | {today_s} |"
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


def cmd_status(args):
    _, text = read_index(args.name)
    for field, key in [
        ("patrol",     "patrol"),
        ("status",     "status"),
        ("parent",     "parent"),
        ("started",    "started"),
        ("completed",  "completed"),
        ("validated",  "validated"),
    ]:
        val = fm_get(text, key) or "—"
        print(f"{field:<12} {val}")


def cmd_validate(args):
    idx_path, idx_text = read_index(args.name)
    today_s = today()
    if re.search(r"^validated:[^\S\n]*([^\r\n]+)", idx_text, re.MULTILINE):
        idx_text = fm_set(idx_text, "validated", today_s)
    else:
        # Insert validated field after completed field
        idx_text = re.sub(
            r"^(completed:.*)$",
            f"\\g<1>\nvalidated: {today_s}",
            idx_text, flags=re.MULTILINE, count=1
        )
    idx_path.write_text(idx_text, encoding="utf-8")
    print(f"validated: {args.name}  date: {today_s}")


def cmd_complete(args):
    idx_path, idx_text = read_index(args.name)
    today_s = today()
    idx_text = fm_set(idx_text, "status", "complete")
    if re.search(r"^completed:[^\S\n]*([^\r\n]+)", idx_text, re.MULTILINE):
        idx_text = fm_set(idx_text, "completed", today_s)
    else:
        idx_text = re.sub(
            r"^(status:.*)$",
            f"\\g<1>\ncompleted: {today_s}",
            idx_text, flags=re.MULTILINE, count=1
        )
    idx_path.write_text(idx_text, encoding="utf-8")

    # Move from Active to Complete in portfolio
    portfolio = PORTFOLIO_INDEX.read_text(encoding="utf-8")
    row_match = re.search(rf"(\|\s*\[{re.escape(args.name)}\][^\n]+\n)", portfolio)
    if row_match:
        row = row_match.group(1)
        portfolio = portfolio.replace(row, "", 1)
        completed_row = re.sub(r"\|\s*[\d-]+\s*\|$", f"| {today_s} |", row.rstrip())
        portfolio = re.sub(
            r"(## Complete\n\n\|[^\n]+\n\|[-|]+\n)",
            f"\\g<1>{completed_row}\n",
            portfolio, count=1
        )
    PORTFOLIO_INDEX.write_text(portfolio, encoding="utf-8")
    print(f"completed: {args.name}")


def cmd_delete(args):
    path = patrol_dir(args.name)
    shutil.rmtree(path)
    print(f"deleted: {path}")


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser(description="Patrol state management — lightweight")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list", help="List active patrols")

    s = sub.add_parser("create", help="Create a new patrol")
    s.add_argument("name", help="Patrol name (kebab-case)")
    s.add_argument("--parent", metavar="workstreams/<name>|objectives/<name>",
                   help="Parent path, e.g. workstreams/my-workstream")
    s.add_argument("--title", help="Human-readable title (defaults to title-cased name)")

    for name_cmd in ("status", "validate", "complete", "delete"):
        s = sub.add_parser(name_cmd)
        s.add_argument("name")

    args = p.parse_args()
    {
        "list":     cmd_list,
        "create":   cmd_create,
        "status":   cmd_status,
        "validate": cmd_validate,
        "complete": cmd_complete,
        "delete":   cmd_delete,
    }[args.cmd](args)


if __name__ == "__main__":
    main()
