#!/usr/bin/env python3
"""Rotation (recurring work) state management — no phase machine, no LLM.

A rotation is work defined by its *recurrence*, not its size: refresh docs into the
knowledge base, drain the cleanup queue, report status across objectives, auto-lint.
It may be task-sized or workstream-sized. What makes it a rotation is that it runs
again.

Two things follow from that, and both are why it needs its own record:

  * it does not "complete" — it is active, paused, retired, or abandoned
  * each run should make the next run cheaper, which is what the self-improvement
    diary is for. A rotation that never improves is a subscription, not a rotation.
"""

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
ROTATIONS_DIR = WORKSPACE / "control-plane" / "rotations"
PORTFOLIO_INDEX = ROTATIONS_DIR / "index.md"

TERMINAL = ("retired", "abandoned")

# ── helpers ───────────────────────────────────────────────────────────────────

def die(msg):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)

def today():
    return date.today().strftime("%Y-%m-%d")

def kebab_ok(name):
    return bool(re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name))

def rotation_dir(name):
    if not kebab_ok(name):
        die(f"invalid rotation name '{name}' — must be kebab-case (a-z, 0-9, hyphens); no path separators")
    p = ROTATIONS_DIR / name
    if not p.exists():
        die(f"rotation '{name}' not found at {p}")
    return p

def read_index(name):
    p = rotation_dir(name) / "index.md"
    if not p.exists():
        die(f"index.md not found for '{name}'")
    return p, p.read_text(encoding="utf-8")

def fm_get(text, field):
    m = re.search(rf"^{re.escape(field)}:[^\S\n]*([^\r\n]+)", text, re.MULTILINE)
    return m.group(1).strip().strip('"') if m else None

def fm_set(text, field, value):
    # `\s*` would cross the newline, so setting an EMPTY field ("last_run:") captured
    # the following line into the match and overwrote it. Horizontal whitespace only.
    return re.sub(rf"^({re.escape(field)}:)[^\S\n]*[^\r\n]*$", f"\\g<1> {value}",
                  text, flags=re.MULTILINE, count=1)

def md_cell(s):
    """Escape pipes so a cell can never corrupt the row it sits in."""
    return (s or "").replace("|", "\\|").strip()

SEPARATOR_RE = re.compile(r"^\|[\s\-|]+\|$")

def ensure_portfolio_index():
    if not PORTFOLIO_INDEX.exists():
        ROTATIONS_DIR.mkdir(parents=True, exist_ok=True)
        PORTFOLIO_INDEX.write_text(
            "---\nnote_type: portfolio-index\nscope: rotations\n---\n\n"
            "# Rotations\n\n"
            "Recurring work, scheduled or on demand. See [`_log.md`](_log.md) for everything closed.\n\n"
            "## Active\n\n"
            "| Rotation | Purpose | Trigger | Runs | Last run |\n"
            "|---|---|---|---|---|\n\n"
            "## Closed\n\n"
            "| Rotation | Purpose | Outcome | Closed |\n"
            "|---|---|---|---|\n",
            encoding="utf-8",
        )

def parse_index_rows(text):
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
        if SEPARATOR_RE.match(line):
            after_sep = True
            continue
        if after_sep and line.startswith("|") and "*(none yet)*" not in line:
            rows.append(line)
    return rows

def _set_row_cell(name, idx, value):
    """Rewrite one cell of a rotation's Active row without disturbing the others."""
    if not PORTFOLIO_INDEX.exists():
        return
    p = PORTFOLIO_INDEX.read_text(encoding="utf-8")
    def repl(m):
        cells = m.group(0).rstrip("\n").split("|")
        if len(cells) > idx:
            cells[idx] = f" {value} "
        return "|".join(cells) + "\n"
    PORTFOLIO_INDEX.write_text(
        re.sub(rf"\|\s*\[{re.escape(name)}\][^\n]+\n", repl, p, count=1), encoding="utf-8")

# ── commands ──────────────────────────────────────────────────────────────────

def cmd_list(_args):
    if not PORTFOLIO_INDEX.exists():
        die(f"portfolio index not found: {PORTFOLIO_INDEX}")
    for line in parse_index_rows(PORTFOLIO_INDEX.read_text(encoding="utf-8")):
        print(line)


def cmd_create(args):
    name = args.name
    if not kebab_ok(name):
        die(f"invalid rotation name '{name}' — must be kebab-case (a-z, 0-9, hyphens); no path separators")
    dest = ROTATIONS_DIR / name
    if dest.exists():
        die(f"'{name}' already exists")

    parent   = args.parent or "null"
    title    = args.title or name.replace("-", " ").title()
    trigger  = args.trigger or "on-demand"
    today_s  = today()
    parent_q = f'"{parent}"' if parent != "null" else "null"
    parent_link = "—"
    if parent != "null":
        _rel = parent if "/" in parent else f"objectives/{parent}"
        parent_link = f"[{_rel}](../../{_rel}/index.md)"

    index_md = f"""---
rotation: {name}
status: active
trigger: "{trigger}"
parent: {parent_q}
started: {today_s}
last_run:
runs: 0
closed:
outcome:
tags: [rotation/{name}]
---

# {title}

## Purpose

*What recurs, and why it is worth recurring. One run = one complete pass of the
job. A rotation is defined by repetition, not by size — this may be as small as a
lint pass or as large as a full research refresh.*

## Trigger

**{trigger}**

*Scheduled (an interval or cron) or on-demand (a signal, a queue depth, a request).
If scheduled, name the schedule. If on-demand, name what makes someone reach for it.*

## Guardrails

*A rotation runs unattended, so say what should stop it and ask for a human:*

- [ ] The gate is NO-GO and a run cannot clear it
- [ ] The run would delete or overwrite something outside its declared scope
- [ ] Two consecutive runs make no progress
- [ ] Input volume is far outside the normal range

## Run Log

*One row per run, appended by `rotation.py run`. Newest first. **Spawned** names the
task or workstream a run launched, when the run was big enough to warrant one — that
child follows its own lifecycle and closes into its own log, not this one.*

| # | Date | What it did | Spawned | Gate |
|---|---|---|---|---|

## Self-Improvement Diary

*The point of a rotation. After each run, one line on what would make the **next**
run cheaper, safer, or more accurate — a step to automate, a check to add, a
manual approval to remove. A rotation that never improves is a subscription.*

*When an entry here recurs, stop writing it down and go fix it: promote it into
this rotation's own procedure, a tool, or a skill.*

## Working Notes

*`_working/` holds scratch for runs that need handoff points the way a workstream
does — research pulls, drafts, intermediate files. Throwaway by default. Anything
durable belongs in `outputs/`, the vault, or a project before the rotation closes.*

## Outcome

*Filled at close. Why it was retired (the job is done, automated away, or no longer
needed) or abandoned (it stopped mattering). For an abandoned rotation this is the
most valuable line in the file.*

## Cross-links

- **Parent:** {parent_link}
"""

    dest.mkdir(parents=True)
    (dest / "index.md").write_text(index_md, encoding="utf-8")
    (dest / "_working").mkdir()
    (dest / "_working" / ".gitkeep").write_text("", encoding="utf-8")
    print(f"created: {dest / 'index.md'}")

    ensure_portfolio_index()
    portfolio = PORTFOLIO_INDEX.read_text(encoding="utf-8")
    new_row = f"| [{name}]({name}/index.md) | *add purpose* | {md_cell(trigger)} | 0 | — |"
    out, in_active, inserted = [], False, False
    for line in portfolio.splitlines():
        if line.startswith("## Active"):
            in_active = True
        elif line.startswith("## "):
            in_active = False
        if in_active and "*(none yet)*" in line:
            continue
        out.append(line)
        if in_active and not inserted and SEPARATOR_RE.match(line):
            out.append(new_row)
            inserted = True
    PORTFOLIO_INDEX.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"updated: {PORTFOLIO_INDEX}")


def cmd_status(args):
    _, text = read_index(args.name)
    for field in ("rotation", "status", "trigger", "parent", "started",
                  "runs", "last_run", "closed", "outcome"):
        print(f"{field:<10} {fm_get(text, field) or '—'}")


def cmd_run(args):
    """Record one run. Without this a rotation leaves no trail and cannot improve."""
    idx_path, text = read_index(args.name)
    status = fm_get(text, "status")
    if status != "active":
        die(f"rotation '{args.name}' is {status}, not active — resume it first")

    runs    = int(fm_get(text, "runs") or 0) + 1
    today_s = today()
    text = fm_set(fm_set(text, "runs", str(runs)), "last_run", today_s)

    spawned = md_cell(args.spawned) or "—"
    if args.spawned and "/" in args.spawned:
        spawned = f"[{md_cell(args.spawned)}](../../{md_cell(args.spawned)}/index.md)"
    row = f"| {runs} | {today_s} | {md_cell(args.note)} | {spawned} | {md_cell(args.gate or '—')} |"
    lines, out, in_log, placed = text.splitlines(), [], False, False
    for line in lines:
        if line.startswith("## Run Log"):
            in_log = True
        elif line.startswith("## ") and in_log and not placed:
            out.append(row)
            placed, in_log = True, False
        out.append(line)
        if in_log and not placed and SEPARATOR_RE.match(line):
            out.append(row)
            placed = True
    if not placed:
        out.append(row)
    text = "\n".join(out) + "\n"

    if args.learned:
        text = re.sub(r"(## Self-Improvement Diary\n)",
                      f"\\g<1>\n- **Run {runs} ({today_s}).** {args.learned}\n",
                      text, count=1)
    idx_path.write_text(text, encoding="utf-8")

    _set_row_cell(args.name, 4, str(runs))
    _set_row_cell(args.name, 5, today_s)
    print(f"run {runs} recorded: {args.name}")
    if not args.learned:
        print("note: no --learned given. If this run taught you nothing about making the "
              "next one better, that is worth noticing.")


def cmd_pause(args):
    idx_path, text = read_index(args.name)
    idx_path.write_text(fm_set(text, "status", "paused"), encoding="utf-8")
    print(f"paused: {args.name}  (resume with: rotation.py resume {args.name})")


def cmd_resume(args):
    idx_path, text = read_index(args.name)
    idx_path.write_text(fm_set(text, "status", "active"), encoding="utf-8")
    print(f"active: {args.name}")


def _close(args, outcome):
    idx_path, text = read_index(args.name)
    today_s = today()
    text = fm_set(text, "status", outcome)
    text = fm_set(text, "closed", today_s)
    text = fm_set(text, "outcome", f'"{args.reason}"')
    idx_path.write_text(text, encoding="utf-8")

    if PORTFOLIO_INDEX.exists():
        portfolio = PORTFOLIO_INDEX.read_text(encoding="utf-8")
        row_match = re.search(rf"(\|\s*\[{re.escape(args.name)}\][^\n]+\n)", portfolio)
        if row_match:
            row = row_match.group(1)
            cells = [c.strip() for c in re.split(r"(?<!\\)\|", row.strip().strip("|"))]
            # The folder is deleted once the log entry is written, so a closed row
            # must not keep pointing at it. Repoint to the running log.
            name_cell = re.sub(rf"\[{re.escape(args.name)}\]\([^)]*\)",
                               f"[{args.name}](_log.md)", cells[0], count=1)
            purpose = cells[1] if len(cells) > 1 else ""
            closed_row = f"| {name_cell} | {purpose} | {outcome} | {today_s} |"
            moved, n = re.subn(r"(## Closed\n\n\|[^\n]+\n\|[-|]+\n)",
                               f"\\g<1>{closed_row}\n", portfolio, count=1)
            # Only drop the Active row once the Closed row is actually placed.
            if n:
                portfolio = moved.replace(row, "", 1)
            else:
                print("warning: no '## Closed' section in the portfolio index; "
                      "left the row under Active rather than dropping it")
            PORTFOLIO_INDEX.write_text(portfolio, encoding="utf-8")
    print(f"{outcome}: {args.name}")
    print("next: write the entry in control-plane/rotations/_log.md, then "
          f"python -B tools/rotation.py delete {args.name}")


def cmd_retire(args):
    _close(args, "retired")

def cmd_abandon(args):
    _close(args, "abandoned")

def cmd_delete(args):
    path = rotation_dir(args.name)
    work = path / "_working"
    leftovers = [p for p in work.rglob("*") if p.is_file() and p.name != ".gitkeep"] if work.exists() else []
    if leftovers and not args.force:
        print(f"error: {len(leftovers)} file(s) still in _working/ — rescue or discard them first:",
              file=sys.stderr)
        for p in leftovers[:10]:
            print(f"  {p.relative_to(path)}", file=sys.stderr)
        die("re-run with --force to delete anyway")
    shutil.rmtree(path)
    print(f"deleted: {path}")

# ── main ──────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description="Rotation state management — recurring work")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list", help="List active rotations")

    c = sub.add_parser("create", help="Create a new rotation")
    c.add_argument("name")
    c.add_argument("--parent", help="objectives/<name> or workstreams/<name>")
    c.add_argument("--title")
    c.add_argument("--trigger", help='e.g. "weekly", "nightly 02:00", "on-demand"')

    s = sub.add_parser("status", help="Show rotation state")
    s.add_argument("name")

    r = sub.add_parser("run", help="Record one run")
    r.add_argument("name")
    r.add_argument("--note", required=True, help="what this run did")
    r.add_argument("--gate", help="gate result (GO / NO-GO / n/a)")
    r.add_argument("--learned", help="what would make the next run better")
    r.add_argument("--spawned", help="task or workstream this run launched, "
                                     "e.g. tasks/refresh-fynapse-docs or workstreams/vault-reindex")

    p = sub.add_parser("pause", help="Pause without closing")
    p.add_argument("name")
    rs = sub.add_parser("resume", help="Resume a paused rotation")
    rs.add_argument("name")

    rt = sub.add_parser("retire", help="Close: the job is done or automated away")
    rt.add_argument("name")
    rt.add_argument("--reason", required=True)

    a = sub.add_parser("abandon", help="Close: it stopped mattering")
    a.add_argument("name")
    a.add_argument("--reason", required=True)

    d = sub.add_parser("delete", help="Delete the folder (after logging)")
    d.add_argument("name")
    d.add_argument("--force", action="store_true", help="delete even with files in _working/")

    args = ap.parse_args()
    {"list": cmd_list, "create": cmd_create, "status": cmd_status, "run": cmd_run,
     "pause": cmd_pause, "resume": cmd_resume, "retire": cmd_retire,
     "abandon": cmd_abandon, "delete": cmd_delete}[args.cmd](args)


if __name__ == "__main__":
    main()
