#!/usr/bin/env bash
# SessionStart — budget/creed reminder + scaffold & Python preflight notice.
# Observational. Emits one concise systemMessage; always exits 0.
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "${DIR}/fn-common.sh"

fn_read_input >/dev/null 2>&1  # drain stdin if any (ignored)
fn_log "=== Scene opens: $(basename "${FN_WS}") ==="

# Only speak up in an actual harness workspace — never nag in unrelated projects.
if [ ! -f "${FN_WS}/constitution.md" ] && [ ! -d "${FN_WS}/control-plane" ]; then
  exit 0
fi

MSG="Friendly Neighborhood: minimum force, lean budget. Symbiote off."

# Python present? (the orchestration CLIs need it)
if ! command -v python3 >/dev/null 2>&1 && ! command -v python >/dev/null 2>&1 && ! command -v py >/dev/null 2>&1; then
  MSG="${MSG} (Heads up: Python 3 not found - patrol/responsibility/mission CLIs need it.)"
fi

# Emit as a non-blocking system message.
printf '{"systemMessage":"%s"}\n' "${MSG}"
exit 0
