# Workspace Contract

*Base contract for all tools and models. All harness instruction files are addenda to this.*

**Semantic density:** Use the shortest word that preserves meaning. Imperative voice. No hedging. Prefer tables over prose, bullets over paragraphs.

---

## Layout

```
_now.md              current priorities
constitution.md      this file
.claude/rules/       path-scoped rules (auto-loaded per subtree)
control-plane/       orchestration: objectives, workstreams (missions), patrols, logs
projects/            execution workers
knowledge/           sources/ (raw) · vault/ (curated) · distillers/
prompts/             reusable prompt assets
tools/               scripts and CLIs
secret-identity/     private context — behind the mask; never leaves
```

Each subtree's contract auto-loads via a path-scoped rule in `.claude/rules/`; scoped subagents should read the relevant rule before acting. Each subtree also keeps a thin `CLAUDE.md` pointer for tools that don't support rules.

---

## Session

1. Read `_now.md`
2. Subtree contracts auto-load via `.claude/rules/` when you open files in that subtree — no manual step needed. If working outside Claude Code, read the subtree's `CLAUDE.md` pointer and follow it to `.claude/rules/<subtree>.md`.
3. If an objective, workstream, or patrol is in scope, read its `index.md`
4. **State scope and next action before proceeding**

---

## Context

- Load minimum context for the next decision
- Keep main context under 40% of window; distill before continuing past 60%
- `_working/` is scratch — never read by main context

---

## Distillation

Every phase boundary: raw → distilled artifact → durable log.

| Phase | From | To |
|---|---|---|
| In-session | `_working/` | `research.md` / `design.md` / `plan.md` |
| Workstream implement | plan step execution | `control-plane/outputs/{workstream-name}/` (never inside workstream folder) |
| Workstream close | workstream folder | `control-plane/workstreams/_log/YYYY-MM-DD-{name}.md` |
| Objective decisions | session | objective `index.md` → Key Decisions Log (append-only) |

---

## Logs

| Type | Path |
|---|---|
| Runtime | `.claude/logs/session-YYYY-MM-DD.log` |
| Workstream | `control-plane/workstreams/_log/YYYY-MM-DD-{name}.md` |
| Objective | objective `index.md` → Key Decisions Log (append-only, never truncated) |
| Workstream outputs | `control-plane/outputs/{workstream-name}/` — permanent; never deleted |

---

## Boundaries

| Subtree | Role | Must not |
|---|---|---|
| `control-plane/` | plan, coordinate | execute domain logic |
| `projects/` | execute | orchestrate across projects |
| `knowledge/sources/` | raw data (pipeline-written) | curate |
| `knowledge/vault/` | curated, Obsidian-backed (access via `obsidian-cli` + kepano skills, not MCP) | accept raw data |
| `prompts/` | reusable assets | execute in place |
| `tools/` | capability primitives | contain domain logic |

When in doubt: planning → control-plane · execution → projects · data → knowledge.

---

## Safety

- No delete or overwrite without explicit instruction
- Prefer additive, reversible changes
- Stay in current directory scope unless in control-plane

---

## Orchestration

Subagent spawning is tool-dependent. See tool addendum for capability.

| Tool | Agent support | Subtree scoping method |
|---|---|---|
| Claude Code | Native (Agent tool) | Scope each agent to one subtree via prompt; `.claude/rules/<subtree>.md` auto-loads as the contract |
| Codex | None | Launch from target directory instead |
| Gemini CLI | None | Launch from target directory instead |
| OpenCode | None | Launch from target directory instead |

---

## Principles

- intent → decompose → delegate → synthesize (never implement at orchestration layer)
- Questions cheap; under-shaped work expensive
- Orient before acting · distill before advancing · log before deleting
