#!/usr/bin/env bash
# PreToolUse — observational logging only. Non-blocking: always exits 0.
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "${DIR}/fn-common.sh"

INPUT="$(fn_read_input)"
TOOL_NAME="$(fn_json_str "${INPUT}" tool_name)"
[ -z "${TOOL_NAME}" ] && TOOL_NAME="unknown"

fn_log "PRE  tool=${TOOL_NAME}"

exit 0
