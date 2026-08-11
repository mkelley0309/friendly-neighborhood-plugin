#!/usr/bin/env bash
# Friendly Neighborhood — observation deck (fallback combined view).
#
# The real 3-pane deck is the VS Code task "Observation Deck" (Terminal -> Run Task),
# which opens one colored tail pane per group. This script is the portable fallback:
# it follows all three streams in a single terminal, labeled by group.
#
# Usage:  bash scripts/observe.sh            # follow all three
#         bash scripts/observe.sh spideys    # follow one group
set -u
ROOT="${WORKSPACE_ROOT:-$PWD}"
LOGDIR="$ROOT/.claude/logs/agents"
mkdir -p "$LOGDIR"
for g in spideys support villains; do : >> "$LOGDIR/$g.log"; done

# One of the three deck streams only — catches a typo (which would otherwise hang
# on tail -F of a stream that never appears) and keeps the arg to a known name.
case "${1:-}" in
  ""|spideys|support|villains) ;;
  *) echo "observe.sh: unknown group '$1' (pick: spideys | support | villains)" >&2; exit 2 ;;
esac

if [ "${1:-}" != "" ]; then
  exec tail -n 200 -F "$LOGDIR/$1.log"
fi

echo "🕷  Friendly Neighborhood — observation deck (combined). Ctrl-C to stop."
echo "    For separate colored panes, run the VS Code task: Terminal → Run Task → Observation Deck"
echo
exec tail -n 60 -F "$LOGDIR/spideys.log" "$LOGDIR/support.log" "$LOGDIR/villains.log"
