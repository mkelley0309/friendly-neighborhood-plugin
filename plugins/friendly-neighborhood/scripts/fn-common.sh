#!/usr/bin/env bash
# Shared helpers for Friendly Neighborhood hooks.
# Resolves the workspace (NOT the plugin dir) and the daily log path.
# Sourced by the other fn-*.sh scripts. Observational — never gatekeep.

set -u

# Workspace = where Claude Code was launched. CLAUDE_PROJECT_DIR if the runtime
# provides it to the hook env; otherwise fall back to the current directory.
FN_WS="${CLAUDE_PROJECT_DIR:-$PWD}"
FN_LOG_DIR="${FN_WS}/.claude/logs"
mkdir -p "${FN_LOG_DIR}" 2>/dev/null || true

FN_DATE="$(date +%Y-%m-%d 2>/dev/null || echo unknown)"
FN_TS="$(date -Iseconds 2>/dev/null || date +%Y-%m-%dT%H:%M:%S%z 2>/dev/null || echo now)"
FN_LOG="${FN_LOG_DIR}/session-${FN_DATE}.log"

# Observation deck — themed per-agent streams the operator can tail (full edition).
FN_AGENTS_DIR="${FN_LOG_DIR}/agents"
FN_DECK="${FN_WS}/.claude/scripts/agent-log.sh"   # scaffolded workspace copy

# Read all of stdin (hook input JSON), best-effort.
fn_read_input() { cat 2>/dev/null || true; }

# Extract a top-level JSON string field by name without jq.
# usage: fn_json_str "$INPUT" tool_name
fn_json_str() {
  printf '%s' "$1" \
    | grep -oE "\"$2\"[[:space:]]*:[[:space:]]*\"[^\"]*\"" \
    | head -n1 \
    | sed -E "s/.*\"$2\"[[:space:]]*:[[:space:]]*\"([^\"]*)\".*/\1/" \
    || true
}

fn_log() { printf '[%s] %s\n' "${FN_TS}" "$1" >> "${FN_LOG}" 2>/dev/null || true; }

# Best-effort acting persona for screenplay-style logs: a subagent's name if the hook
# input carries one, otherwise the default persona. Returned in CAPS, namespace stripped.
fn_speaker() {
  local input="$1" name
  name="$(printf '%s' "$input" | grep -oE '"(subagent_type|agent_type|agent|subagent|persona)"[[:space:]]*:[[:space:]]*"[^"]*"' | head -n1 | sed -E 's/.*:[[:space:]]*"([^"]*)".*/\1/' || true)"
  [ -z "$name" ] && name="${CLAUDE_PLUGIN_OPTION_DEFAULT_PERSONA:-peter}"
  name="${name##*:}"   # strip a namespace like spideys:peter
  printf '%s' "$name" | tr '[:lower:]' '[:upper:]'
}

# Lowercase, namespace-stripped agent name (for deck stream / suit-flag filenames).
fn_speaker_lc() { fn_speaker "$1" | tr '[:upper:]' '[:lower:]'; }

# Append one themed line to the agent's observation-deck stream (best-effort, never fails).
# Pass WORKSPACE_ROOT explicitly so the logger writes to the workspace, not the hook's cwd.
# usage: fn_deck <agent> <message...>
fn_deck() {
  [ -f "${FN_DECK}" ] || return 0
  local n="$1"; shift
  WORKSPACE_ROOT="${FN_WS}" bash "${FN_DECK}" "$n" "$*" >/dev/null 2>&1 || true
}

# Force-shed any black suit for an agent (clears the symbiote flag the deck reads).
# usage: fn_suit_off <agent>
fn_suit_off() {
  case "$1" in *[!a-z0-9-]*|"") return 0 ;; esac   # plain agent name only — no path traversal in the rm
  rm -f "${FN_AGENTS_DIR}/.suit/${1}" 2>/dev/null || true
}
