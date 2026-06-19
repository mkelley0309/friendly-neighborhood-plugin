#!/usr/bin/env python3
"""Friendly Neighborhood - workspace scaffolder.

Copies the bundled domain-neutral harness scaffold (plugin `templates/`) into the
target workspace WITHOUT overwriting anything that already exists. Pure stdlib so it
runs on any OS that has Python 3 - the plugin's one prerequisite.

Source : <plugin-root>/templates/   (derived from this file's location)
Target : $CLAUDE_PROJECT_DIR, else the current working directory.

Invoked by the `origin-story` skill. Safe to re-run - existing files are skipped.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path


def plugin_root() -> Path:
    # this file lives at <plugin-root>/scripts/scaffold.py
    return Path(__file__).resolve().parent.parent


def target_root() -> Path:
    return Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()).resolve()


def main() -> int:
    src = plugin_root() / "templates"
    dst = target_root()

    if not src.is_dir():
        print(f"error: templates not found at {src}", file=sys.stderr)
        return 1

    if src == dst or src in dst.parents:
        print("error: refusing to scaffold into the plugin's own directory.", file=sys.stderr)
        return 1

    created: list[str] = []
    skipped: list[str] = []

    for root, _dirs, files in os.walk(src):
        rel_dir = Path(root).relative_to(src)
        for name in files:
            rel = rel_dir / name
            target = dst / rel
            if target.exists():
                skipped.append(str(rel).replace(os.sep, "/"))
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((Path(root) / name).read_bytes())
            created.append(str(rel).replace(os.sep, "/"))

    print(f"\n  Friendly Neighborhood - workspace scaffolded into: {dst}\n")
    print(f"  created: {len(created)} file(s)   skipped (already present): {len(skipped)}")
    if created:
        preview = created[:12]
        for p in preview:
            print(f"    + {p}")
        if len(created) > len(preview):
            print(f"    ... and {len(created) - len(preview)} more")
    if skipped:
        print(f"  (left {len(skipped)} existing file(s) untouched - nothing overwritten)")

    print(
        "\n  Next:\n"
        "    1. Open constitution.md - the base contract.\n"
        "    2. The subtree contracts auto-load via .claude/rules/ when you work in each area.\n"
        "    3. Run /friendly-neighborhood-lite:creed to load the operating doctrine.\n"
        "    4. Start work: /friendly-neighborhood-lite:patrol (a mission), "
        "/friendly-neighborhood-lite:responsibility (a goal), or /friendly-neighborhood-lite:web-archive (knowledge).\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
