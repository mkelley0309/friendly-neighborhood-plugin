# Workspace Contract

*Base contract for all tools and models. All harness instruction files are addenda to this.*

**Semantic density:** Use the shortest word that preserves meaning. Imperative voice. No hedging. Prefer tables over prose, bullets over paragraphs.

---

## Layout

```
_now.md              current priorities
constitution.md      this file
.claude/rules/       path-scoped rules (auto-loaded per subtree)
control-plane/       orchestration: objectives, workstreams, tasks, logs
projects/            execution workers
knowledge/           sources/ (raw) · vault/ (curated) · distillers/
prompts/             reusable prompt assets
tools/               scripts and CLIs
personal/            private context — stakeholders, accounts, career; never leaves
```

Each subtree's contract auto-loads via a path-scoped rule in `.claude/rules/`; scoped subagents should read the relevant rule before acting. Each subtree also keeps a thin `CLAUDE.md` pointer for tools that don't support rules.

---

## Session

1. Read `_now.md`
2. Subtree contracts auto-load via `.claude/rules/` when you open files in that subtree — no manual step needed. If working outside Claude Code, read the subtree's `CLAUDE.md` pointer and follow it to `.claude/rules/<subtree>.md`.
3. If a workstream, objective, or task is in scope, read its `index.md`
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

## Operating Principles

The opinions that make this harness what it is. Most are tuned for serious, long-horizon, knowledge-heavy work — on a quick throwaway task, some are overhead you should skip. Match the ceremony to the size of the work.

1. **Three tiers of work.** *Objective* = the long-lived "why" — a role, a measured annual objective, a career goal — with structured progress tracking (Key Results, milestones, decisions log). *Workstream* = complex multi-session work with a defined completion state, run through the QRDPIV/RPIV lifecycle. *Task* = a lightweight, often-repeatable unit with proportional admin only (assignment, checklist, handoff, lessons). Strategy, execution, and lightweight iteration each keep their own durable state.

2. **Progressive distillation — proportional.** At every handoff, compress to a dense artifact and hand that to a fresh context, not the raw history. Keeps understanding high and tokens low across long work — but it's overhead on short work. A one-session workstream distills lightly; a multi-week workstream distills hard. Distillation is lossy, so distill for the next phase's needs, not to a generic summary.

3. **Progressive disclosure — including the vault.** Load the minimum for the next decision: skills route to action-files on demand, rules load per subtree, and the knowledge vault is navigated hub → note, never bulk-loaded. Fetch detail when you need it, not before.

4. **Curated self-learning — gated, not auto.** Lessons land in workstream-notes every phase and are reviewed at cleanup; research with lasting value is staged for the vault and admitted only by peer review. The harness gets smarter over time, but nothing rewrites itself unsupervised — silent drift is the failure we design against.

5. **Determinism for the repeatable.** If you'll do a task more than once, turn it into a script or tool the first or second time. Don't re-spend tokens reasoning out what a deterministic CLI can do for free forever. The control-plane CLIs embody this principle.

6. **Honest gates.** Hard, measurable concerns — tests pass/fail, lint/type errors, token spend vs. budget, deny-list hits — go through the deterministic gate (`tools/gate.py`), which exits GO or NO-GO. Soft, contextual judgments stay qualitative and are recorded in workstream-notes. There are few blanket "don't" rules: cost is computed from live signals, not a pre-listed catalog of prohibitions.

7. **Lean orchestration.** Cheapest capability that does the job; spawn only the agents whose concern is live; concurrency is a budget you set, not a free-for-all.

> **Foundations** — solid, expected, not claimed as novel: a workspace scaffolder, observational logging + recovery, an enforced deny-list, a verification gate before any workstream closes (`tools/gate.py`), and native autonomous looping (`/loop` + `schedule`, via the `loop` skill) for long-running work.

---

## Principles

- intent → decompose → delegate → synthesize (never implement at orchestration layer)
- Questions cheap; under-shaped work expensive
- Orient before acting · distill before advancing · log before deleting
