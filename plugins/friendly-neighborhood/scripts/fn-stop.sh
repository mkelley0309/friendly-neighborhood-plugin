#!/usr/bin/env bash
# Stop — session-end snapshot + knowledge-queue reminder.
# Non-blocking: always exit 0.
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "${DIR}/fn-common.sh"

fn_read_input >/dev/null 2>&1
fn_log "=== Scene ends ==="

QUEUE_DIR="${FN_WS}/knowledge/distillers/queue"
if [ -d "${QUEUE_DIR}" ]; then
  PENDING="$(grep -rl 'status: pending' "${QUEUE_DIR}" --exclude='README.md' 2>/dev/null || true)"
  if [ -n "${PENDING}" ]; then
    fn_log "KNOWLEDGE-QUEUE pending items — run /friendly-neighborhood:web-archive (scout) to process:"
    while IFS= read -r f; do
      [ -n "$f" ] && fn_log "  - $(basename "${f}")"
    done <<< "${PENDING}"
  fi
fi

exit 0
