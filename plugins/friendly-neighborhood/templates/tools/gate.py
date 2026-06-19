#!/usr/bin/env python3
"""gate.py — the deterministic verification gate.

The honest half of the decision mechanic: aggregate **measurable** signals into a
single go/no-go. No vibes, no laundered scores — just exit codes.

Define the checks once (a gate config), run them cheaply forever (principle:
determinism for the repeatable). Use it at the verification gate before a patrol
closes, or at any decision that hinges on hard facts.

    python -B tools/gate.py init                 # write a gate.json template
    python -B tools/gate.py run                   # run the checks in ./gate.json
    python -B tools/gate.py run --config path     # run a specific config
    python -B tools/gate.py run --check "tests=pytest -q" --check "lint=ruff check ."

Exit code 0 = all checks passed (GO). Exit code 1 = at least one failed (NO-GO).
Soft, contextual concerns (over-engineering, scope creep, wrong target) are NOT
for this tool — those stay qualitative judgments weighed against the creed.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

TEMPLATE = {
    "checks": [
        {"name": "tests", "command": "echo 'replace with your test command, e.g. pytest -q'"},
        {"name": "lint", "command": "echo 'replace with your lint command, e.g. ruff check .'"},
    ]
}


def load_checks(config: Path | None, cli_checks: list[str]) -> list[dict]:
    checks: list[dict] = []
    if cli_checks:
        for c in cli_checks:
            name, _, cmd = c.partition("=")
            if not cmd:
                print(f"error: --check must be name=command (got {c!r})", file=sys.stderr)
                raise SystemExit(2)
            checks.append({"name": name.strip(), "command": cmd.strip()})
        return checks
    path = config or Path("gate.json")
    if not path.exists():
        print(f"error: no checks given and {path} not found. Run `gate.py init` or pass --check.", file=sys.stderr)
        raise SystemExit(2)
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("checks", [])


def cmd_init(args) -> int:
    path = Path(args.config or "gate.json")
    if path.exists():
        print(f"{path} already exists — not overwriting.")
        return 0
    path.write_text(json.dumps(TEMPLATE, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {path} — edit the checks, then `gate.py run`.")
    return 0


def cmd_run(args) -> int:
    checks = load_checks(Path(args.config) if args.config else None, args.check or [])
    if not checks:
        print("error: gate has no checks.", file=sys.stderr)
        return 2
    for c in checks:
        if not c.get("command", "").strip():
            print(f"error: check {c.get('name', '?')!r} has an empty command - a gate cannot verify nothing.", file=sys.stderr)
            return 2
    results = []
    for c in checks:
        name, command = c.get("name", "?"), c.get("command", "")
        proc = subprocess.run(command, shell=True)
        ok = proc.returncode == 0
        results.append((name, ok, proc.returncode))

    width = max(len(n) for n, _, _ in results)
    print("\n  Gate results:")
    for name, ok, rc in results:
        mark = "PASS" if ok else f"FAIL (exit {rc})"
        print(f"    {name:<{width}}  {mark}")
    passed = all(ok for _, ok, _ in results)
    print(f"\n  Verdict: {'GO - all checks passed' if passed else 'NO-GO - fix the failures above'}\n")
    return 0 if passed else 1


def main() -> int:
    p = argparse.ArgumentParser(description="Deterministic verification gate over measurable signals.")
    sub = p.add_subparsers(dest="cmd", required=True)
    pi = sub.add_parser("init", help="Write a gate.json template")
    pi.add_argument("--config")
    pr = sub.add_parser("run", help="Run the gate checks; exit 0 = GO, 1 = NO-GO")
    pr.add_argument("--config", help="Path to a gate config (default: ./gate.json)")
    pr.add_argument("--check", action="append", help="Inline check as name=command (repeatable)")
    args = p.parse_args()
    return {"init": cmd_init, "run": cmd_run}[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
