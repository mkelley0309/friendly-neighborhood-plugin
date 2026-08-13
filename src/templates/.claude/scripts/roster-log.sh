#!/usr/bin/env bash
# Friendly Neighborhood — roster observation logger.
#
# Agents, registers, and dissent lenses narrate their work to a themed, color-coded
# stream that the observation deck (3 VS Code tail panes) displays. One line per
# significant action — not raw tokens. Spider-variants flip to the BLACK SUIT
# palette while a symbiote is worn.
#
# Usage:
#   roster-log.sh <name> "<message>"      append one themed line to the caller's stream
#   roster-log.sh <name> --suit-on        wear the symbiote (black-suit palette ON)
#   roster-log.sh <name> --suit-off       shed the symbiote (back to native colors)
#
# Streams land in $WORKSPACE_ROOT/.claude/logs/roster/{spideys,support,villains}.log
# Resolves workspace root from $WORKSPACE_ROOT, else current dir.
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=roster-colors.sh
. "$HERE/roster-colors.sh"

ROOT="${WORKSPACE_ROOT:-$PWD}"
LOGDIR="$ROOT/.claude/logs/roster"
SUITDIR="$LOGDIR/.suit"
mkdir -p "$LOGDIR" "$SUITDIR"

who="${1:-}"; shift || true
[ -z "$who" ] && { echo "usage: roster-log.sh <name> \"<message>\" | --suit-on | --suit-off" >&2; exit 2; }
who="$(printf '%s' "$who" | tr '[:upper:]' '[:lower:]')"
# Plain roster name only — the name builds .suit/$who paths (write + rm), so a
# slash or dot here would be a write/delete-anywhere primitive. Reject, don't sanitize.
case "$who" in *[!a-z0-9-]*|"") echo "roster-log: invalid name '$who' (a-z, 0-9, hyphens only)" >&2; exit 2 ;; esac

group="$(roster_group "$who")"
log="$LOGDIR/${group}.log"
ts="$(date '+%H:%M:%S')"

# ── symbiote toggle ────────────────────────────────────────────────────────────
case "${1:-}" in
  --suit-on)
    if [ "$group" != "spideys" ]; then
      echo "roster-log: only spideys can wear the symbiote ('$who' is $group)" >&2; exit 1
    fi
    : > "$SUITDIR/$who"
    printf '%b%s  %-11s %s%b\n' "$SUIT_PAINT" "$ts" "$who" "[ symbiote on — black suit ]" "$RESET" >> "$log"
    exit 0 ;;
  --suit-off)
    rm -f "$SUITDIR/$who"
    printf '%b%s  %-11s%b %s\n' "$(roster_paint "$who")" "$ts" "$who" "$RESET" "( church bell — suit shed )" >> "$log"
    exit 0 ;;
esac

msg="$*"
[ -z "$msg" ] && { echo "usage: roster-log.sh <name> \"<message>\"" >&2; exit 2; }

# ── black-suit override while the symbiote flag is set ───────────────────────────
if [ -f "$SUITDIR/$who" ]; then
  printf '%b%s  %-11s [BLACK SUIT] %s%b\n' "$SUIT_PAINT" "$ts" "$who" "$msg" "$RESET" >> "$log"
else
  printf '%b%s  %-11s%b %s\n' "$(roster_paint "$who")" "$ts" "$who" "$RESET" "$msg" >> "$log"
fi
