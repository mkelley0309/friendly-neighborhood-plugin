#!/usr/bin/env bash
# PostToolUse — completion telemetry; on failure, drop a recovery breadcrumb.
# Non-blocking: always exit 0.
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "${DIR}/fn-common.sh"

INPUT="$(fn_read_input)"
TOOL_NAME="$(fn_json_str "${INPUT}" tool_name)"
[ -z "${TOOL_NAME}" ] && TOOL_NAME="unknown"

IS_ERROR="no"
if printf '%s' "${INPUT}" | grep -qE '"is_error"[[:space:]]*:[[:space:]]*true'; then
  IS_ERROR="yes"
fi

SPEAKER="$(fn_speaker "${INPUT}")"
STATUS="ok"; [ "${IS_ERROR}" = "yes" ] && STATUS="ERROR"
fn_log "${SPEAKER} > ${TOOL_NAME} (${STATUS})"

if [ "${IS_ERROR}" = "yes" ]; then
  RECOVERY="${FN_LOG_DIR}/recovery-${FN_DATE}.md"
  {
    printf '## %s - %s fumbled %s\n\n' "${FN_TS}" "${SPEAKER}" "${TOOL_NAME}"
    printf '```json\n%s\n```\n\n' "${INPUT}"
  } >> "${RECOVERY}" 2>/dev/null || true
fi

exit 0
