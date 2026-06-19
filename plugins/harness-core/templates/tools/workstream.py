#!/usr/bin/env python3
"""Workstream state management — QRDPIV phase machine, no LLM."""

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
WORKSTREAMS_DIR = WORKSPACE / "control-plane" / "workstreams"
PORTFOLIO_INDEX = WORKSTREAMS_DIR / "index.md"

VALID_PHASES = [
    "questions", "research", "design", "plan",
    "implement", "validate", "complete", "cleanup",
]

PHASE_NEXT = {
    "questions":  "actions/questions.md  → advance: workstream advance <name> research",
    "research":   "actions/research.md   → advance: workstream advance <name> design|plan",
    "design":     "actions/design.md     → advance: workstream advance <name> plan",
    "plan":       "actions/plan.md       → advance: workstream advance <name> implement",
    "implement":  "actions/implement.md  → check steps: workstream check-step <name> \"<step>\"",
    "validate":   "actions/validate.md   → advance: workstream advance <name> complete",
    "complete":   "actions/cleanup.md    → archive: workstream archive <name> --log-date YYYY-MM-DD",
    "cleanup":    "actions/cleanup.md    → delete: workstream delete <name>",
}

# rpiv framework starts at research (clear-spec: no questions/design)
FRAMEWORK_START = {
    "qrdpiv": "questions",
    "rpiv":   "research",
}

# ── helpers ───────────────────────────────────────────────────────────────────

def die(msg):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)

def today():
    return date.today().strftime("%Y-%m-%d")

def kebab_ok(name):
    return bool(re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name))

def init_dir(name):
    if not kebab_ok(name):
        die(f"invalid workstream name '{name}' — must be kebab-case (a-z, 0-9, hyphens); no path separators")
    p = WORKSTREAMS_DIR / name
    if not p.exists():
        die(f"workstream '{name}' not found at {p}")
    return p

def read_index(name):
    p = init_dir(name) / "index.md"
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

def status_row_set(text, field, value):
    """Update a value cell in | Field | Value | table rows."""
    return re.sub(
        rf"\|\s*{re.escape(field)}\s*\|\s*[^|]*\|",
        f"| {field} | {value} |",
        text, count=1
    )

def ensure_portfolio_index():
    if not PORTFOLIO_INDEX.exists():
        WORKSTREAMS_DIR.mkdir(parents=True, exist_ok=True)
        PORTFOLIO_INDEX.write_text(
            "# Workstreams\n\n"
            "## Active\n\n"
            "| Workstream | Description | Framework | Phase | Health | Parent |\n"
            "|---|---|---|---|---|---|\n\n"
            "## Recently Completed\n\n"
            "| Workstream | Description | Completed |\n"
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


def cmd_status(args):
    _, text = read_index(args.name)
    for field, key in [
        ("workstream",        "workstream"),
        ("framework",         "framework"),
        ("phase",             "workstream_phase"),
        ("health",            "workstream_health"),
        ("step",              "current_step"),
        ("status",            "status"),
        ("started",           "started"),
        ("completed",         "completed"),
        ("parent",            "parent"),
    ]:
        val = fm_get(text, key) or "—"
        print(f"{field:<12} {val}")

    m = re.search(r"## Child Tasks\n\n[^\n]+\n[^\n]+\n((?:\|[^\n]+\n)*)", text)
    if m:
        rows = [r for r in m.group(1).strip().splitlines() if r.strip()]
        if rows:
            print(f"\nchild tasks ({len(rows)} total):")
            for row in rows:
                print(f"  {row.strip()}")


def cmd_next(args):
    _, text = read_index(args.name)
    phase  = fm_get(text, "workstream_phase")
    health = fm_get(text, "workstream_health")
    step   = fm_get(text, "current_step")

    print(f"workstream: {args.name}")
    print(f"phase:      {phase}  health: {health}")
    if step and step != "—":
        print(f"step:       {step}")

    if health == "blocked":
        m = re.search(r"\|\s*Blocker\s*\|\s*([^|]+)\|", text)
        blocker = m.group(1).strip() if m else "unknown"
        print(f"\nBLOCKED: {blocker}")
        print(f"resolve dependency, then: python -B tools/workstream.py unblock {args.name}")
        return

    print(f"\nnext: {PHASE_NEXT.get(phase, 'unknown phase')}")


def cmd_create(args):
    name = args.name
    if not kebab_ok(name):
        die(f"name must be kebab-case (lowercase letters, digits, hyphens): '{name}'")

    dest = WORKSTREAMS_DIR / name
    if dest.exists():
        die(f"'{name}' already exists")

    fw      = args.framework
    parent  = args.parent or "null"
    title   = args.title or name.replace("-", " ").title()
    phase   = FRAMEWORK_START[fw]
    today_s = today()
    parent_q = f'"{parent}"' if parent != "null" else "null"
    if parent != "null":
        _rel = parent if "/" in parent else f"objectives/{parent}"
        parent_link = f"[{_rel}](../../{_rel}/index.md)"
    else:
        parent_link = "—"

    artifact_table = ""
    if fw == "qrdpiv":
        artifact_table = """
## QRDPIV Artifact Status

| Step | Artifact | Status |
|---|---|---|
| Questions | `request.md` | Not started |
| Research — Knowledge | `_working/research-knowledge-*.md` | Not started |
| Research — Web | `_working/research-web-*.md` | Not started |
| Research — Codebase | `_working/research-code-*.md` | Not started |
| Research — Distillation | `research.md` | Not started |
| Design | `design.md` | Not started |
| Plan | `plan.md` | Not started |
| Implement | `worktree-{nn}.md` | Not started |
| Validate | `validate.md` | Not started |
"""
    elif fw == "rpiv":
        artifact_table = """
## RPIV Artifact Status

| Step | Artifact | Status |
|---|---|---|
| Research | `research.md` | Not started |
| Plan | `plan.md` | Not started |
| Implement | `worktree-{nn}.md` | Not started |
| Validate | `validate.md` | Not started |
"""

    index_md = f"""---
workstream: {name}
framework: {fw}
workstream_phase: {phase}
workstream_health: healthy
current_step: "—"
status: active
started: {today_s}
completed:
parent: {parent_q}
tags: [workstream/{name}]
---

# {title}

## Workstream Status

| Field | Value |
|---|---|
| Phase | {phase} |
| Health | healthy |
| Current Step | — |
| Blocker | — |
| Last Active | {today_s} |

*One paragraph: what this workstream is and what it will deliver.*
{artifact_table}
## Child Tasks

| Task | Linked |
|---|---|

## Cross-links

- **Parent:** {parent_link}
"""

    dest.mkdir(parents=True)
    (dest / "index.md").write_text(index_md, encoding="utf-8")
    print(f"created: {dest / 'index.md'}")

    ensure_portfolio_index()
    portfolio = PORTFOLIO_INDEX.read_text(encoding="utf-8")
    if parent != "null":
        rel = parent if "/" in parent else f"objectives/{parent}"
        parent_col = f"[{rel}](../{rel}/index.md)"
    else:
        parent_col = "—"
    new_row = f"| [{name}]({name}/index.md) | *add description* | {fw.upper()} | {phase} | healthy | {parent_col} |"
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
    print(f"next: python -B tools/workstream.py next {name}")


def cmd_link(args):
    workstream = args.workstream
    task       = args.task

    idx_path, idx_text = read_index(workstream)

    task_section = re.search(r"## Child Tasks\n\n[^\n]+\n[^\n]+\n((?:\|[^\n]+\n)*)", idx_text)
    if task_section:
        existing = task_section.group(1)
        if re.search(rf"\|\s*{re.escape(task)}\s*\|", existing):
            print(f"already linked: {task} → {workstream}")
            return

    new_row = f"| {task} | {today()} |"
    idx_text = re.sub(
        r"(## Child Tasks\n\n\|[^\n]+\n\|[-|]+\n(?:\|[^\n]+\n)*)",
        f"\\g<1>{new_row}\n",
        idx_text
    )
    idx_path.write_text(idx_text, encoding="utf-8")
    print(f"linked: {task} → {workstream}")


def cmd_check_step(args):
    ws        = init_dir(args.name)
    plan_path = ws / "plan.md"
    if not plan_path.exists():
        die("plan.md not found")

    lines = plan_path.read_text(encoding="utf-8").splitlines()
    query = args.step

    match_idx = next(
        (i for i, l in enumerate(lines) if "[ ]" in l and query in l),
        None
    )
    if match_idx is None:
        die(f"unchecked step not found: '{query}'")

    print(f"checked: {lines[match_idx].strip()}")
    lines[match_idx] = lines[match_idx].replace("[ ]", "[x]", 1)
    plan_path.write_text("\n".join(lines), encoding="utf-8")

    next_steps = [l for l in lines[match_idx + 1:] if "[ ]" in l]
    next_step = re.sub(r"^[-*]\s*\[\s*\]\s*", "", next_steps[0].strip()) if next_steps else "—"

    idx_path, idx_text = read_index(args.name)
    idx_text = fm_set(idx_text, "current_step", f'"{next_step}"')
    idx_text = status_row_set(idx_text, "Current Step", next_step)
    idx_text = status_row_set(idx_text, "Last Active", today())
    idx_path.write_text(idx_text, encoding="utf-8")
    print(f"next step: {next_step}")


def cmd_advance(args):
    phase = args.phase
    if phase not in VALID_PHASES:
        die(f"invalid phase. valid: {', '.join(VALID_PHASES)}")

    idx_path, idx_text = read_index(args.name)
    old_phase = fm_get(idx_text, "workstream_phase")

    idx_text = fm_set(idx_text, "workstream_phase", phase)
    idx_text = status_row_set(idx_text, "Phase", phase)
    idx_text = status_row_set(idx_text, "Last Active", today())

    if phase == "implement":
        plan_path = init_dir(args.name) / "plan.md"
        if plan_path.exists():
            m = re.search(r"^[-*]\s*\[\s*\]\s*(.+)$", plan_path.read_text(encoding="utf-8"), re.MULTILINE)
            if m:
                first = m.group(1).strip()
                idx_text = fm_set(idx_text, "current_step", f'"{first}"')
                idx_text = status_row_set(idx_text, "Current Step", first)

    idx_path.write_text(idx_text, encoding="utf-8")

    portfolio = PORTFOLIO_INDEX.read_text(encoding="utf-8")
    portfolio = re.sub(
        rf"(\|\s*\[{re.escape(args.name)}\][^|]+\|[^|]+\|[^|]+\|)\s*{re.escape(old_phase or '')}\s*(\|)",
        f"\\g<1> {phase} \\2",
        portfolio
    )
    PORTFOLIO_INDEX.write_text(portfolio, encoding="utf-8")
    print(f"advanced: {args.name}  {old_phase} → {phase}")


def cmd_block(args):
    idx_path, idx_text = read_index(args.name)
    idx_text = fm_set(idx_text, "workstream_health", "blocked")
    idx_text = status_row_set(idx_text, "Health", "blocked")
    idx_text = status_row_set(idx_text, "Blocker", args.reason)
    idx_text = status_row_set(idx_text, "Last Active", today())
    idx_path.write_text(idx_text, encoding="utf-8")
    print(f"blocked: {args.name}  reason: {args.reason}")


def cmd_unblock(args):
    idx_path, idx_text = read_index(args.name)
    idx_text = fm_set(idx_text, "workstream_health", "healthy")
    idx_text = status_row_set(idx_text, "Health", "healthy")
    idx_text = status_row_set(idx_text, "Blocker", "—")
    idx_text = status_row_set(idx_text, "Last Active", today())
    idx_path.write_text(idx_text, encoding="utf-8")
    print(f"unblocked: {args.name}")


def cmd_complete(args):
    idx_path, idx_text = read_index(args.name)
    today_s = today()
    idx_text = fm_set(idx_text, "workstream_phase", "complete")
    idx_text = fm_set(idx_text, "current_step", '"—"')
    idx_text = fm_set(idx_text, "completed", today_s)
    idx_text = fm_set(idx_text, "status", "complete")
    idx_text = status_row_set(idx_text, "Phase", "complete")
    idx_text = status_row_set(idx_text, "Current Step", "—")
    idx_text = status_row_set(idx_text, "Last Active", today_s)
    idx_path.write_text(idx_text, encoding="utf-8")
    print(f"marked complete: {args.name}")
    print(f"next: write log entry → python -B tools/workstream.py archive {args.name} --log-date {today_s}")


def cmd_archive(args):
    log_date    = args.log_date or today()
    description = args.description or "*add description*"
    name        = args.name

    portfolio = PORTFOLIO_INDEX.read_text(encoding="utf-8")
    portfolio = re.sub(rf"\|\s*\[{re.escape(name)}\][^\n]+\n", "", portfolio)

    new_row = f"| [{log_date}-{name}](_log/{log_date}-{name}.md) | {description} | {log_date} |"
    portfolio = re.sub(
        r"(## Recently Completed\n\n\|[^\n]+\n\|[-|]+\n)",
        f"\\g<1>{new_row}\n",
        portfolio
    )
    PORTFOLIO_INDEX.write_text(portfolio, encoding="utf-8")
    print(f"archived: {name} → _log/{log_date}-{name}.md")
    print(f"next: python -B tools/workstream.py delete {name}")


def cmd_delete(args):
    path = init_dir(args.name)
    shutil.rmtree(path)
    print(f"deleted: {path}")


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser(description="Workstream state management — QRDPIV")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list", help="List active workstreams")

    for name_cmd in ("status", "next", "complete", "unblock", "delete"):
        s = sub.add_parser(name_cmd)
        s.add_argument("name")

    s = sub.add_parser("create", help="Create a new workstream")
    s.add_argument("name", help="Workstream name (kebab-case)")
    s.add_argument("--framework", choices=["qrdpiv", "rpiv"], default="qrdpiv",
                   help="qrdpiv (default, all phases) or rpiv (clear-spec: research→plan→implement→validate)")
    s.add_argument("--parent", metavar="objectives/<name>",
                   help="Parent path, e.g. objectives/my-objective")
    s.add_argument("--title", help="Human-readable title (defaults to title-cased name)")

    s = sub.add_parser("link", help="Register a child task under this workstream")
    s.add_argument("workstream", help="Workstream name")
    s.add_argument("task", help="Task name to link")

    s = sub.add_parser("check-step", help="Tick a plan.md checkbox and advance current_step")
    s.add_argument("name")
    s.add_argument("step", help="Substring matching the unchecked step text")

    s = sub.add_parser("advance", help="Advance workstream to the next phase")
    s.add_argument("name")
    s.add_argument("phase", choices=VALID_PHASES)

    s = sub.add_parser("block", help="Mark workstream blocked")
    s.add_argument("name")
    s.add_argument("reason")

    s = sub.add_parser("archive", help="Move workstream from Active to Recently Completed in portfolio")
    s.add_argument("name")
    s.add_argument("--log-date")
    s.add_argument("--description")

    args = p.parse_args()
    {
        "list":       cmd_list,
        "status":     cmd_status,
        "next":       cmd_next,
        "create":     cmd_create,
        "link":       cmd_link,
        "check-step": cmd_check_step,
        "advance":    cmd_advance,
        "block":      cmd_block,
        "unblock":    cmd_unblock,
        "complete":   cmd_complete,
        "archive":    cmd_archive,
        "delete":     cmd_delete,
    }[args.cmd](args)


if __name__ == "__main__":
    main()
