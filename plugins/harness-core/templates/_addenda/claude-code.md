# Claude Code Addendum

Extends `constitution.md`. Claude Code-specific capabilities only.

---

## Hooks

Observational — never gatekeep. Scripts in `.claude/hooks/`, wired via `.claude/settings.local.json`.

| Event | Script | Action |
|---|---|---|
| PreToolUse | `pre-run.sh` | log tool call to session log |
| PostToolUse | `post-run.sh` | log result; write `recovery-*.md` on failure |
| Stop | `on-stop.sh` | write session snapshot |

---

## Skills

Slash commands in `.claude/skills/`. Progressive disclosure — invoking a skill loads only the relevant action file, not the full skill.

Key skills:
- `workstream` — manage complex multi-session work through the heavy QRDPIV lifecycle
- `objective` — manage a long-lived, review-cycle objective (Key Results, milestones, decisions log)
- `task` — handle a lightweight unit or one iteration against a workstream (proportional admin)
- `knowledge` — knowledge pipeline: scout, harvest, distill, cartograph
- `loop` — native autonomous looping for recurring or polling work
- `init-workspace` — workspace initialization and onboarding

**Obsidian vault skills** (OPTIONAL — external install, not bundled): `obsidian-cli`, `obsidian-markdown`, `obsidian-bases`, `json-canvas`, `defuddle`. Install globally via `npx skills add kepano/obsidian-skills -g -a claude-code`. These are the default interface for `knowledge/vault/`. No MCP server — the `obsidian` CLI binary backs `obsidian-cli`. Update via `npx skills update -g`.

---

## Subagent Delegation

### Topology — how the pieces fit

**Mental model: the main context is the shared brain; subagents are limbs.** Subagents are *isolated* — each gets only the prompt you hand it and returns a single final message; none can see another's working context or build on it live. There is no "team that deliberates over one shared context." Delegation is always: *fan a limb out, bring back something distilled, integrate in the brain.*

Three patterns, by where the work sits:

| Where | Pattern | Shape |
|---|---|---|
| **Across phases** (Q→R→D→P→I→V→Cleanup) | Sequential, **fresh context**, artifact handoff | Each phase hands the next a *distilled artifact* (`research.md`, `design.md`, `plan.md`) — not a conversation. The next phase reads the artifact in a clean window. This is what keeps a multi-session workstream coherent and cheap. |
| **Within a phase** (research passes, multi-angle review) | **Bounded parallel fan-out** → independent return → main reconciles | Spawn the needed limbs, each on its own slice or angle, up to your concurrency budget. They run concurrently and **cannot see each other**. |
| **Synthesis, decisions, cross-artifact reconciliation** | **Stays in main context — never delegated** | Only the brain holds the whole picture. |

**Why not "agent teams sharing one context":** handing N agents the same large context in parallel pays that cost N times for N *independent* takes — that's just fan-out, and reconciliation still happens in one place. True debate is possible but expensive (rounds of fan-out → summarize → targeted rebuttal); reserve it for a genuinely contested fork, not as a default. One fan-out + reconcile, at most one targeted second round, captures nearly all the value.

**The discipline that makes fan-out work:** raw subagent output goes to **disk** (`_working/`), then a **separate distillation subagent in fresh context** reads only those files and writes the artifact; the main context reads only the artifact, never the raw passes. (Full protocol in the `workstream` skill.)

**Foreground vs background:** background subagents run *non-interactive* — they can't answer a permission prompt and will stall silently on gated paths (e.g. `.claude/`), and they share your account session limit. Use foreground subagents for write-heavy delegation; reserve background for read/gather work you'll reconcile later.

### Model tiers

Replace model IDs below with the current Sonnet and current Haiku identifiers as models change.

| Profile | Model | Examples |
|---|---|---|
| Complex, ambiguous | current Sonnet | research, plan drafting, multi-step investigation |
| Simple, bounded | current Haiku | status checks, file moves, format conversion, lookups |
| Decisions / synthesis | Main context | never delegate |

Sonnet may spawn Haiku for sub-tasks. Main context may spawn Haiku directly.

### Concurrency Budget

**Concurrency budget — up to 2 subagents in flight at once by default.** This is a *soft budget* you set during `init-workspace` (raise it if your machine and quota allow) — a cost/coordination guideline, not a safety cap. Main context tracks how many are running.

Default behavior is **sequential**: spawn one subagent, wait for it to return, then spawn the next. Run several in parallel only when both conditions are met, and only up to your budget:
1. Tasks are truly independent — no shared file writes, no ordering dependency.
2. Each completes in a single turn given its scope.

**Completion guarantee.** Every subagent spawned must be able to finish its task in one turn. If a task is too large to complete in a single turn, break it into smaller bounded tasks first — do not spawn it and hope it finishes. A subagent that stalls mid-task leaves the workstream in an unstable state requiring manual recovery.

**Checkpoint before the budget bites.** No agent watches the live token/session budget — the runtime owns it and does not expose it mid-turn, so nothing can *warn* you that a turn is about to run out. Guard it **structurally** instead: keep turns bounded (above), and at clean phase/step boundaries write state to disk (`index.md` + `workstream-notes.md`) *before* continuing. A session-limit hit then degrades to a **resume**, never lost work — the same way the `loop` skill carries state across sessions.

**Token budget.** Every subagent prompt must include a return-size bound:
- Haiku: `"Return in under 200 words."`
- Sonnet: `"Return in under 400 words."` (distillation passes: `"Return in under 300 words."`)

### Directory Scoping

Scope every subagent to a subtree. In the agent prompt, always include:

1. **Root**: `Work within \`<subtree>/\` only.`
2. **Contract**: `Read \`.claude/rules/<subtree>.md\` before acting.` (This is the source of truth; the subtree's `CLAUDE.md` is a thin pointer to it.)
3. **Boundary**: `Do not read or write outside \`<subtree>/\`.`

| Task type | Scope to |
|---|---|
| Execution work | `projects/<name>/` |
| Planning / coordination | `control-plane/` |
| Knowledge ingestion | `knowledge/sources/` |
| Curation / synthesis | `knowledge/vault/` |
| Prompt asset work | `prompts/` |
| Tool / script work | `tools/` |

Cross-subtree work (e.g., planning + execution) stays in main context — never delegate cross-boundary tasks to a single subagent.
