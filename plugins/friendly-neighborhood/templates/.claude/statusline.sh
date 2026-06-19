#!/usr/bin/env bash
# Friendly Neighborhood statusline — surfaces harness state.
# Reads session JSON on stdin; scans control-plane for the active mission + tier counts.
# Project-relative: lands in the scaffolded workspace and is wired by .claude/settings.json.
set -u

INPUT="$(cat 2>/dev/null || true)"

# Workspace: prefer cwd from the session JSON, else current dir.
WS="$(printf '%s' "$INPUT" | grep -oE '"cwd"[[:space:]]*:[[:space:]]*"[^"]*"' | head -n1 | sed -E 's/.*"cwd"[[:space:]]*:[[:space:]]*"([^"]*)".*/\1/')"
[ -z "$WS" ] && WS="$PWD"
CP="$WS/control-plane"

OUT="FN"

# Active mission + phase (first active workstream).
if [ -d "$CP/workstreams" ]; then
  for f in "$CP"/workstreams/*/index.md; do
    [ -f "$f" ] || continue
    if grep -qiE '^status:[[:space:]]*active' "$f"; then
      name="$(grep -oiE '^workstream:[[:space:]]*[^[:space:]]+' "$f" | head -n1 | sed -E 's/^[^:]*:[[:space:]]*//')"
      phase="$(grep -oiE '^workstream_phase:[[:space:]]*[^[:space:]]+' "$f" | head -n1 | sed -E 's/^[^:]*:[[:space:]]*//')"
      OUT="$OUT | mission:${name:-?}/${phase:-?}"
      break
    fi
  done
fi

# Counts: active responsibilities (objectives), missions (workstreams), patrols.
count_active() {
  local dir="$1" n=0
  if [ -d "$dir" ]; then
    n="$(grep -rliE '^status:[[:space:]]*active' "$dir"/*/index.md 2>/dev/null | wc -l | tr -d ' ')"
  fi
  printf '%s' "${n:-0}"
}
RESP="$(count_active "$CP/objectives")"
MISS="$(count_active "$CP/workstreams")"
PTRL="$(count_active "$CP/patrols")"
OUT="$OUT | ${RESP} resp / ${MISS} missions / ${PTRL} patrols"

printf '%s' "$OUT"
