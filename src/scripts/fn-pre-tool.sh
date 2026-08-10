#!/usr/bin/env bash
# PreToolUse — spider-sense. Logs every tool call; on a destructive/irreversible
# pattern, asks for confirmation (advisory). The enforced deny-list in
# .claude/settings.json is the hard backstop; this is the tingle before the hit.
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "${DIR}/fn-common.sh"

INPUT="$(fn_read_input)"
TOOL_NAME="$(fn_json_str "${INPUT}" tool_name)"
[ -z "${TOOL_NAME}" ] && TOOL_NAME="unknown"
SPEAKER="$(fn_speaker "${INPUT}")"
fn_log "${SPEAKER} > ${TOOL_NAME}"

# Danger patterns (case-insensitive). Matched against the raw input JSON, which
# includes the command/args. Advisory only — surfaces a confirmation.
DANGER='rm[[:space:]]+-[a-z]*[rf]|git[[:space:]]+push[[:space:]]+[^"]*(--force|-f )|git[[:space:]]+reset[[:space:]]+--hard|git[[:space:]]+clean[[:space:]]+-[a-z]*f|DROP[[:space:]]+(TABLE|DATABASE)|TRUNCATE[[:space:]]+TABLE|DELETE[[:space:]]+FROM[^"]*;|mkfs|dd[[:space:]]+if=|chmod[[:space:]]+(-R[[:space:]]+)?777|>[[:space:]]*/dev/sd|:\(\)[[:space:]]*\{|curl[^"|]*\|[[:space:]]*(sudo[[:space:]]+)?(ba)?sh|wget[^"|]*\|[[:space:]]*(ba)?sh'

if printf '%s' "${INPUT}" | grep -iqE "${DANGER}"; then
  fn_log "${SPEAKER} ! spider-sense tingles: ${TOOL_NAME} looks dangerous"
  REASON="Spider-sense tingling: this looks destructive or irreversible. Confirm it is intended and minimum-force (smallest change that does the job). If a villain would approve, reconsider."
  printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"ask","permissionDecisionReason":"%s"}}\n' "${REASON}"
  exit 0
fi

exit 0
