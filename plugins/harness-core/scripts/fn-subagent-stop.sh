#!/usr/bin/env bash
# SubagentStop — observational logging when a subagent finishes.
# Non-blocking; exits 0.
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "${DIR}/fn-common.sh"

fn_read_input >/dev/null 2>&1  # drain stdin if any (ignored)
fn_log "SUBAGENT-STOP subagent returned"

exit 0
