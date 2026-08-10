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

# Observation deck: make sure the three streams exist (so the VS Code "Observation
# Deck" task can tail them) and clear any STALE black-suit flag — a symbiote that
# ended without a church-bell must not leave an agent stuck in the suit next session.
mkdir -p "${FN_AGENTS_DIR}/.suit" 2>/dev/null || true
for _s in spideys support villains; do : >> "${FN_AGENTS_DIR}/${_s}.log" 2>/dev/null || true; done
rm -f "${FN_AGENTS_DIR}"/.suit/* 2>/dev/null || true

MSG="Friendly Neighborhood: minimum force, lean budget. Symbiote off."

# Python present? (the orchestration CLIs need it)
if ! command -v python3 >/dev/null 2>&1 && ! command -v python >/dev/null 2>&1 && ! command -v py >/dev/null 2>&1; then
  MSG="${MSG} (Heads up: Python 3 not found - patrol/responsibility/mission CLIs need it.)"
fi

# Emit as a non-blocking system message.
printf '{"systemMessage":"%s"}\n' "${MSG}"
exit 0
