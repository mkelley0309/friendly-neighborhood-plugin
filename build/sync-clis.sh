#!/usr/bin/env bash
# Keep the shared CLI tools aligned across the three editions.
#
# Canonical source = the FULL edition (plugins/friendly-neighborhood).
#
# CLI topology after the corrected tier model (objective -> workstream/mission -> task/patrol):
#
#   Shared, byte-identical in ALL THREE editions : gate.py, setup-keys.ps1
#   Themed pair, byte-identical FULL <-> LITE     : workstream.py, patrol.py, objective.py
#   Core variants (un-themed, NOT overwritten)    : workstream.py (un-themed prose),
#                                                   objective.py (links child "workstream", not
#                                                   "mission" — un-themed child-tier vocabulary),
#                                                   task.py (un-themed + RENAMED counterpart
#                                                   of full/patrol.py — different filename)
#
# Run from anywhere:  bash build/sync-clis.sh
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
FULL="$ROOT/plugins/friendly-neighborhood/templates/tools"
LITE="$ROOT/plugins/friendly-neighborhood-lite/templates/tools"
CORE="$ROOT/plugins/harness-core/templates/tools"

THEMED_CLIS="workstream.py patrol.py objective.py gate.py setup-keys.ps1"  # full -> lite (identical)
CORE_SHARED="gate.py setup-keys.ps1"                                       # full -> core (identical)

echo "Syncing FULL -> LITE (all themed CLIs)…"
for f in $THEMED_CLIS; do cp "$FULL/$f" "$LITE/$f"; done

echo "Syncing FULL -> CORE (shared generic CLIs only)…"
for f in $CORE_SHARED; do cp "$FULL/$f" "$CORE/$f"; done

# Verify the files that must be identical really are.
fail=0
for f in $THEMED_CLIS; do diff -q "$FULL/$f" "$LITE/$f" >/dev/null || { echo "  DRIFT lite/$f"; fail=1; }; done
for f in $CORE_SHARED; do diff -q "$FULL/$f" "$CORE/$f" >/dev/null || { echo "  DRIFT core/$f"; fail=1; }; done

# Surface the intentional core divergences so logic changes aren't missed.
for v in workstream.py objective.py; do
  if [ -f "$CORE/$v" ] && ! diff -q "$FULL/$v" "$CORE/$v" >/dev/null; then
    n=$(diff "$FULL/$v" "$CORE/$v" | grep -c '^[<>]' || true)
    echo "  NOTE core/$v diverges from full by ${n} line(s) (expected: un-themed vocabulary)."
    echo "       If you changed its LOGIC in full, hand-apply that change to core/$v."
  fi
done
if [ -f "$CORE/task.py" ]; then
  echo "  NOTE core/task.py is the un-themed, RENAMED counterpart of full/patrol.py."
  echo "       If you changed patrol.py LOGIC in full, hand-apply it to core/task.py."
fi

if [ "$fail" = 0 ]; then echo "Shared CLIs in sync."; else echo "Sync check FAILED — investigate drift above."; exit 1; fi
