---
name: workstream
description: >
  Manages the full lifecycle of a workstream in control-plane/workstreams/ —
  initiation, questions, research, design, plan, implement, validate, cleanup.
  A workstream is the heavy, formal lifecycle for complex multi-session, multi-handoff
  work: open one when the work is too big for a task (too many sessions, too many
  handoffs, or too much structural risk to leave untracked). Trigger whenever
  someone describes an undertaking with that level of complexity. Also trigger when
  asking about workstream status, continuing existing work, or signaling completion.
  When in doubt, trigger — the Questions step is cheap; under-shaped work is expensive.
---

# Workstream Skill

## Session Entry — Always Run First

1. Read `control-plane/CLAUDE.md`
2. Read `control-plane/workstreams/index.md`
3. If a specific workstream is in scope, read its `index.md`
4. Identify the current phase and health
5. Identify the current action from the table below
6. Load **only** that action file — nothing else
7. State phase, health, and intended action to the user before proceeding

**What NOT to load at session entry:** Do not read research files, design.md, plan.md, or any `_working/` files during session entry. These are loaded only when the action explicitly requires them (e.g., implement loads plan.md to check step status; a research step loads its source files). Assess and cleanup never need research files.

## Action Routing

| Situation | Load |
|---|---|
| New workstream — nothing exists yet | `actions/initiate.md` |
| Existing workstream — need to understand state or advise | `actions/assess.md` |
| QRDPIV Questions step — refining an ambiguous request | `actions/questions.md` |
| Research step — running distillation passes | `actions/research.md` |
| Design step — architectural decisions | `actions/design.md` |
| Plan step — producing `plan.md` | `actions/plan.md` |
| Implement step — executing against `plan.md` or worktrees | `actions/implement.md` |
| Validate step — gate run + adversarial QA before closing | `actions/validate.md` |
| Workstream complete — writing log, deleting files | `actions/cleanup.md` |

## Framework at a Glance

**QRDPIV** (default): Questions → Research → Design? → Plan → Implement → Validate → Cleanup
**RPIV** (clear-spec): Research → Plan → Implement → Validate → Cleanup

Default to QRDPIV. Questions are cheap; under-shaped plans are expensive.

**Research is mandatory.** There is no shortcut from Questions or Initiate to Design or Plan without a `research.md`. Even when the user provides source material directly, that material must be written to `_working/` and distilled through the research protocol before proceeding.

## Research Protocol (Non-Negotiable)

Every research phase follows these rules — no exceptions:

1. **Each pass writes to disk first.** Subagent pass findings go to `_working/research-{type}-{n}.md` before anything else. Raw pass output is never consumed by main context.
2. **Distillation runs in a fresh context.** A separate distillation subagent reads only `_working/` files and writes `research.md`. It has no access to the conversation or pass instructions.
3. **Main context reads only `research.md`.** Not `_working/` files, not pass summaries — only the distilled output.
4. **Passes run before distillation.** All pass files must exist on disk before distillation begins. Parallel passes are encouraged; sequential distillation is required.

These rules enforce progressive distillation, structured handoffs to clean context windows, limited token usage, and semantic density — the properties that make a workstream coherent across multiple sessions.

## Workstream Notes (Self-Learning) — Every Phase

Each workstream keeps one `workstream-notes.md` in its folder. It is the self-learning ledger and is **not** implement-only — every phase contributes:

- **Created at initiate** from the template in `framework-templates.md`.
- **Appended by every phase.** Whenever a phase hits a challenge, discrepancy, friction in the workflow itself, or a lesson worth repeating/avoiding, append it to `workstream-notes.md` with a phase prefix (`[questions]`, `[research]`, `[design]`, `[plan]`, `[implement]`, `[validate]`, `[cleanup]`). Permission/settings suggestions go in their section.
- **Implement adds** the per-step Step Status Log (see `actions/implement.md`).
- **Reviewed at cleanup** — surfaced to the user and distilled into the log entry's "What Worked / Lessons Learned" section.

## What Is a Workstream

Heavy, formal, multi-session work with a defined completion state and a cleanup step that deletes the folder. A workstream links child **tasks** when parallel tracks need independent execution. Not: long-lived measured objectives (those are `objectives/`), single-session quick work (those are tasks), generic utilities (those are `tools/`), or project code (those are `projects/`).

## Child Tasks and Parent Objectives

Workstreams can link child tasks and have a parent at one tier:

- **Child Tasks** — the workstream's `index.md` maintains a roster of child task links.
- **Objective** (`parent: "objectives/{name}"`) — a review-cycle-measured strategic objective.

If the user describes work that should be tied to an objective and none exists, suggest creating it first via the `objective` skill.

## Framework Reference

Operational schemas and state transitions live in `framework.md`. Load it when creating or updating any workstream file.

Templates (index.md, request.md, research.md, design.md, plan.md, log entry) live in `framework-templates.md`. Load it **only** when you are about to fill in a new artifact — not during session entry, assess, or implement continuation.

## Subagent Delegation

Per workspace `CLAUDE.md`:
- **Sonnet subagents** for research passes, plan drafting, design analysis
- **Haiku subagents** for template filling, bounded lookups, file moves
- Never delegate synthesis, decisions, or cross-artifact reconciliation — those stay in main context

**Agent scoping (default).** Every subagent is **scoped to a single subtree** — it reads and writes within that subtree only. Cross-boundary work is the orchestrator's job: `control-plane` (main context) coordinates by deploying the **right agent per subtree** and passing distilled artifacts between them — never sending one agent across the boundary. (See `_addenda/claude-code.md` → Directory Scoping.)

- **Scope + absolute path.** Open each brief with `Work within <absolute-subtree-path>/ only`, using the absolute path of the agent's own subtree (agents don't resolve sibling top-level subtrees by glob).
- **Isolation by scope:** directory-scoped prompts for non-git subtrees (`control-plane/`, `knowledge/`); **worktree isolation** for code work inside a git-repo project. Never `isolation: "worktree"` from `control-plane/` (not a git repo).
- **Orchestrate from `control-plane/`** — don't relocate the session into a project. A build that needs vault knowledge → deploy a **knowledge agent** scoped to `knowledge/vault/`, then brief the project agent with its distilled result; code work → an **implementation agent** in a **worktree** of the project repo.

## Guiding Principles

Orient → shape → execute → validate → distill → log → delete. At every transition, something becomes smaller and more useful.

**Progressive distillation:** Raw findings compress to pass files. Pass files compress to `research.md`. Research compresses to design decisions. Design compresses to plan steps. Plan compresses to a log entry. Nothing flows forward at full density.

**Structured handoffs:** Each phase transition hands off an artifact, not a conversation. The next phase reads the artifact, not what was said. Clean context windows are a feature — they enforce that the artifact carries all necessary information.
