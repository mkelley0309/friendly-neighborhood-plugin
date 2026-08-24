---
name: campaign
description: >
  Manages the full lifecycle of a campaign in control-plane/workstreams/ —
  initiation, questions, research, design, blueprint, implement, validate, cleanup.
  A campaign is the heavy, formal lifecycle for complex multi-session, multi-handoff
  work: open one when the work is too big for a mission (too many sessions, too many
  handoffs, or too much structural risk to leave untracked). Trigger whenever
  someone describes an undertaking with that level of complexity. Also trigger when
  asking about campaign status, continuing existing work, or signaling completion.
  When in doubt, trigger — the Questions step is cheap; under-shaped work is expensive.
---

# Campaign Skill

## Session Entry — Always Run First

1. Read `control-plane/CLAUDE.md`
2. Read `control-plane/workstreams/index.md`
3. If a specific campaign is in scope, read its `index.md`
4. Identify the current phase and health
5. Identify the current action from the table below
6. Load **only** that action file — nothing else
7. State phase, health, and intended action to the user before proceeding

**What NOT to load at session entry:** Do not read research files, design.md, blueprint.md, or any `_working/` files during session entry. These are loaded only when the action explicitly requires them (e.g., implement loads blueprint.md to check step status; a research step loads its source files). Assess and cleanup never need research files.

## Action Routing

| Situation | Load |
|---|---|
| New campaign — nothing exists yet | `actions/initiate.md` |
| Existing campaign — need to understand state or advise | `actions/assess.md` |
| Payload Relay Questions step — refining an ambiguous request | `actions/questions.md` |
| Research step — running distillation passes | `actions/research.md` |
| Design step — architectural decisions | `actions/design.md` |
| Blueprint step — producing `blueprint.md` | `actions/blueprint.md` |
| Implement step — executing against `blueprint.md` or worktrees | `actions/implement.md` |
| Validate step — gate run + adversarial QA before closing | `actions/validate.md` |
| Campaign complete — writing log, deleting files | `actions/cleanup.md` |

## Framework at a Glance

**Payload Relay** (default): Questions → Research → Design? → Blueprint → Implement → Validate → Cleanup
**Short Relay** (clear-spec): Research → Blueprint → Implement → Validate → Cleanup

Default to Payload Relay. Questions are cheap; under-shaped blueprints are expensive.

**Research is mandatory.** There is no shortcut from Questions or Initiate to Design or Blueprint without a `research.md`. Even when the user provides source material directly, that material must be written to `_working/` and distilled through the research protocol before proceeding.

## Research Protocol (Non-Negotiable)

Every research phase follows these rules — no exceptions:

1. **Each pass writes to disk first.** Subagent pass findings go to `_working/research-{type}-{n}.md` before anything else. Raw pass output is never consumed by main context.
2. **Distillation runs in a fresh context.** A separate distillation subagent reads only `_working/` files and writes `research.md`. It has no access to the conversation or pass instructions.
3. **Main context reads only `research.md`.** Not `_working/` files, not pass summaries — only the distilled output.
4. **Passes run before distillation.** Run passes **sequentially, one at a time** — a stalled or half-written pass file leaves the campaign in an unrecoverable state, and certainty of completion outranks speed. All pass files must exist on disk before distillation begins, and distillation is itself a single sequential step.

These rules enforce progressive distillation, structured handoffs to clean context windows, limited token usage, and semantic density — the properties that make a campaign coherent across multiple sessions.

## Friction Log — Every Phase

Each campaign keeps one `friction-log.md` in its folder. It records **how well the harness performed**, never what the work found.

- **Created at initiate** from the template in `framework-templates.md`.
- **Appended by every phase**, prefixed `[questions]` `[research]` `[design]` `[blueprint]` `[implement]` `[validate]` `[cleanup]`.
- **Reviewed at cleanup** — surfaced to the user, distilled into the log entry, and any unresolved generalizable entry appended to `control-plane/_harness/friction.md`.

### The inclusion test

> **Would this note still be true and useful on a completely unrelated campaign?**

If yes, it belongs here. If it names the subject matter, it belongs in the work artifact instead.

| Belongs in `friction-log.md` | Belongs elsewhere |
|---|---|
| "Vault read scope was too narrow for the research pass" | A finding *from* that pass → `research.md` |
| "`actions/research.md` names an agent that has no Write tool" | A defect in the code under study → `research.md` |
| "`SKILL.md` and the action file contradict each other" | A design decision taken → `design.md` |
| "The CLI resolves the wrong root when run from a subfolder" | Step 1.4 is done → `blueprint.md` (via `check-step`) |

**Record the rule, not the incident.** "Diff before you copy — the plugin can be ahead" is the entry; the file you clobbered is a clause of evidence, not a paragraph.

### Why the scope is narrow

This is the only artifact that legitimately crosses every phase boundary. That privilege is affordable *only* because its scope is small and fixed. Let it also carry what the work found and it becomes the cross-phase accumulator that progressive distillation exists to prevent — every phase then reads every prior phase's findings, which is exactly the context pollution the handoff model is built to stop.

Progress tracking is **not** its job. `blueprint.md` checkboxes and `index.md` `current_step` are maintained together by `workstream.py check-step`; a third hand-maintained tracker rots and then lies.

## What Is a Campaign

Heavy, formal, multi-session work with a defined completion state and a cleanup step that deletes the folder. A campaign links child **missions** when parallel tracks need independent execution. Not: long-lived measured responsibilities (those are `objectives/`), single-session quick work (those are missions), generic utilities (those are `tools/`), or project code (those are `projects/`).

## Child Missions and Parent Responsibilities

Campaigns can link child missions and have a parent at one tier:

- **Child Missions** — the campaign's `index.md` maintains a roster of child mission links.
- **Responsibility** (`parent: "objectives/{name}"`) — a checkpoint-cycle-measured strategic responsibility.

If the user describes work that should be tied to a responsibility and none exists, suggest creating it first via the `responsibility` skill.

## Asides — work that comes up mid-campaign

Something always comes up mid-phase: a dependency needs unblocking, a harness defect needs correcting, the cartograph needs a run, or related work surfaces that should happen later. **Doing it inline is the expensive mistake.** The remediation drags its own research, its own dead ends and its own errors into a context window that progressive distillation exists to keep clean, and the campaign never fully recovers that space.

Spawn it instead:

```bash
python -B tools/workstream.py aside <campaign> <mission-name> \
    --reason "what came up" \
    --kind dependency|harness|knowledge|followup \
    [--blocking]
```

This creates the mission parented to the campaign, writes its own context into it (why it exists, which phase it came from, whether the campaign is waiting on it), adds a roster row, and — with `--blocking` — sets the campaign to `blocked` with the mission named as the blocker.

**Then run it in a separate session.** That is the entire point. The aside gets its own context window, does its work, and closes into `missions/_log.md` under its own tier.

- **`--blocking`** — the campaign cannot proceed. Come back and run `workstream.py unblock <name> --by <mission>`. **Resume from the campaign's own artifacts.** Do not re-read the aside's record on the way back in, or you have re-imported exactly what you paid a session to keep out.
- **without `--blocking`** — the campaign continues in parallel. The roster row is a promise to do it, not a dependency.

The test for whether something is an aside: **would working on it now put material in this context that the rest of this campaign does not need?** If yes, spawn it. A one-line fix is not an aside. A dependency chase is.

## Framework Reference

Operational schemas and state transitions live in `framework.md`. Load it when creating or updating any campaign file.

Templates (index.md, request.md, research.md, design.md, blueprint.md, log entry) live in `framework-templates.md`. Load it **only** when you are about to fill in a new artifact — not during session entry, assess, or implement continuation.

## Subagent Delegation

Per workspace `CLAUDE.md`:
- **Sonnet subagents** for research passes, blueprint drafting, design analysis
- **Haiku subagents** for template filling, bounded lookups, file moves
- Never delegate synthesis, decisions, or cross-artifact reconciliation — those stay in main context

**Agent scoping (default).** Every subagent is **scoped to a single subtree** — it reads and writes within that subtree only. Cross-boundary work is the orchestrator's job: `control-plane` (main context) coordinates by deploying the **right agent per subtree** and passing distilled artifacts between them — never sending one agent across the boundary. (See root `CLAUDE.md` → Subagent Delegation.)

- **Scope + absolute path.** Open each brief with `Work within <absolute-subtree-path>/ only`, using the absolute path of the agent's own subtree (agents don't resolve sibling top-level subtrees by glob).
- **Isolation by scope:** directory-scoped prompts for non-git subtrees (`control-plane/`, `knowledge/`); **worktree isolation** for code work inside a git-repo project. Never `isolation: "worktree"` from `control-plane/` (not a git repo).
- **Orchestrate from `control-plane/`** — don't relocate the session into a project. A build that needs vault knowledge → deploy a **knowledge agent** scoped to `knowledge/vault/`, then brief the project agent with its distilled result; code work → an **implementation agent** in a **worktree** of the project repo.

## Guiding Principles

Orient → shape → execute → validate → distill → log → delete. At every transition, something becomes smaller and more useful.

**Progressive distillation:** Raw findings compress to pass files. Pass files compress to `research.md`. Research compresses to design decisions. Design compresses to blueprint steps. Blueprint compresses to a log entry. Nothing flows forward at full density.

**Structured handoffs:** Each phase transition hands off an artifact, not a conversation. The next phase reads the artifact, not what was said. Clean context windows are a feature — they enforce that the artifact carries all necessary information.
