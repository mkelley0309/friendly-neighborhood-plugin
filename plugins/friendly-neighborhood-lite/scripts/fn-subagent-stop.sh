#!/usr/bin/env bash
# SubagentStop — the church bell. Confirms control returned to baseline when a
# subagent finishes. If the finished subagent was a SYMBIOTE (an escalated self-clone,
# tagged with "symbiote" in its task), it rings audibly: the borrowed power is off.
# Non-blocking; exits 0. (Miguel the architect is not a symbiote and is not flagged.)
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "${DIR}/fn-common.sh"

INPUT="$(fn_read_input)"
SPEAKER="$(fn_speaker "${INPUT}")"
fn_log "${SPEAKER} exits — back to baseline"

# A symbiote clone tags itself with "symbiote" in its spawned task. Ring loudly on return.
if printf '%s' "${INPUT}" | grep -qi 'symbiote'; then
  fn_log "(church bell) the symbiote is off — ${SPEAKER} returns to baseline"
  printf '{"systemMessage":"Church bell: the symbiote is off, back to baseline. Log what the escalation cost."}\n'
fi

exit 0
