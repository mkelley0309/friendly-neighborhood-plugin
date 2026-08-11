#!/usr/bin/env bash
# Friendly Neighborhood — agent observation logger.
#
# Agents narrate their work to a themed, color-coded stream that the observation
# deck (3 VS Code tail panes) displays. One line per significant action — not raw
# tokens. Spider-variants flip to the BLACK SUIT palette while a symbiote is worn.
#
# Usage:
#   agent-log.sh <agent> "<message>"      append one themed line to the agent's stream
#   agent-log.sh <agent> --suit-on        wear the symbiote (black-suit palette ON)
#   agent-log.sh <agent> --suit-off       shed the symbiote (back to native colors)
#
# Streams land in $WORKSPACE_ROOT/.claude/logs/agents/{spideys,support,villains}.log
# Resolves workspace root from $WORKSPACE_ROOT, else current dir.
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=agent-colors.sh
. "$HERE/agent-colors.sh"

ROOT="${WORKSPACE_ROOT:-$PWD}"
LOGDIR="$ROOT/.claude/logs/agents"
SUITDIR="$LOGDIR/.suit"
mkdir -p "$LOGDIR" "$SUITDIR"

agent="${1:-}"; shift || true
[ -z "$agent" ] && { echo "usage: agent-log.sh <agent> \"<message>\" | --suit-on | --suit-off" >&2; exit 2; }
agent="$(printf '%s' "$agent" | tr '[:upper:]' '[:lower:]')"
# Plain roster name only — the name builds .suit/$agent paths (write + rm), so a
# slash or dot here would be a write/delete-anywhere primitive. Reject, don't sanitize.
case "$agent" in *[!a-z0-9-]*|"") echo "agent-log: invalid agent name '$agent' (a-z, 0-9, hyphens only)" >&2; exit 2 ;; esac

group="$(agent_group "$agent")"
log="$LOGDIR/${group}.log"
ts="$(date '+%H:%M:%S')"

# ── symbiote toggle ────────────────────────────────────────────────────────────
case "${1:-}" in
  --suit-on)
    if [ "$group" != "spideys" ]; then
      echo "agent-log: only spideys can wear the symbiote ('$agent' is $group)" >&2; exit 1
    fi
    : > "$SUITDIR/$agent"
    printf '%b%s  %-11s %s%b\n' "$SUIT_PAINT" "$ts" "$agent" "[ symbiote on — black suit ]" "$RESET" >> "$log"
    exit 0 ;;
  --suit-off)
    rm -f "$SUITDIR/$agent"
    printf '%b%s  %-11s%b %s\n' "$(agent_paint "$agent")" "$ts" "$agent" "$RESET" "( church bell — suit shed )" >> "$log"
    exit 0 ;;
esac

msg="$*"
[ -z "$msg" ] && { echo "usage: agent-log.sh <agent> \"<message>\"" >&2; exit 2; }

# ── black-suit override while the symbiote flag is set ───────────────────────────
if [ -f "$SUITDIR/$agent" ]; then
  printf '%b%s  %-11s [BLACK SUIT] %s%b\n' "$SUIT_PAINT" "$ts" "$agent" "$msg" "$RESET" >> "$log"
else
  printf '%b%s  %-11s%b %s\n' "$(agent_paint "$agent")" "$ts" "$agent" "$RESET" "$msg" >> "$log"
fi
