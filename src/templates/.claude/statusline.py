#!/usr/bin/env python3
"""Friendly Neighborhood statusline — surfaces harness state.

Reads the session JSON Claude Code pipes on stdin, finds the active workstream
(if any) and its phase, and counts active items per portfolio tier.

Per design [D19]: Python replaces the prior Bash implementation to remove the
Git Bash dependency. Context-window usage is deliberately omitted — probe P3
(harness-consolidation workstream, 2026-08-10) resolved NEGATIVE: `statusLine`
does not fire at all in the VSCode extension host, which is this harness's
only environment, so no raw stdin sample was ever captured and no field name
for context usage was ever confirmed. If a future session runs Claude Code in
a raw terminal and captures a sample, add it here using the confirmed field.
"""

import json
import re
import sys
from pathlib import Path

STATUS_ACTIVE = re.compile(r"^status:\s*active\s*$", re.IGNORECASE | re.MULTILINE)


def read_cwd_from_stdin() -> str | None:
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return None
    return data.get("cwd")


def count_active(dir_path: Path) -> int:
    if not dir_path.is_dir():
        return 0
    count = 0
    for index_file in dir_path.glob("*/index.md"):
        try:
            text = index_file.read_text(encoding="utf-8")
        except OSError:
            continue
        if STATUS_ACTIVE.search(text):
            count += 1
    return count


def active_workstream(workstreams_dir: Path) -> str | None:
    if not workstreams_dir.is_dir():
        return None
    for index_file in sorted(workstreams_dir.glob("*/index.md")):
        try:
            text = index_file.read_text(encoding="utf-8")
        except OSError:
            continue
        if not STATUS_ACTIVE.search(text):
            continue
        name_match = re.search(r"^workstream:\s*(\S+)", text, re.MULTILINE)
        phase_match = re.search(r"^workstream_phase:\s*(\S+)", text, re.MULTILINE)
        name = name_match.group(1) if name_match else "?"
        phase = phase_match.group(1) if phase_match else "?"
        return f"workstream:{name}/{phase}"
    return None


def main() -> None:
    cwd = read_cwd_from_stdin()
    workspace = Path(cwd) if cwd else Path.cwd()
    control_plane = workspace / "control-plane"

    parts = []
    ws_status = active_workstream(control_plane / "workstreams")
    if ws_status:
        parts.append(ws_status)

    objectives = count_active(control_plane / "objectives")
    workstreams = count_active(control_plane / "workstreams")
    assignments = count_active(control_plane / "assignments")
    cadences = count_active(control_plane / "cadences")
    parts.append(
        f"{objectives} objectives / {workstreams} workstreams / "
        f"{assignments} assignments / {cadences} cadences"
    )

    print(" | ".join(parts))


if __name__ == "__main__":
    main()
