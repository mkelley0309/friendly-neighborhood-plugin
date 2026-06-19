---
name: objective
description: >
  Manages the lifecycle of an objective in control-plane/objectives/ — a long-lived,
  review-cycle-measured objective with structured progress tracking: Key Results (with
  targets), milestones, linked workstreams, a review cadence, a health signal,
  and an append-only decisions log. This is the strategic container that outlasts
  any individual task or workstream beneath it.
  Trigger when the user references a formal objective, a review-cycle goal, or wants
  to capture a strategic objective that will span multiple workstreams or tasks. Also
  trigger when asked about objective status, when KRs or milestones need updating,
  when decisions should be logged against an objective, or when an objective is
  closing out.
---

# Objective Skill

## What Is an Objective

A long-lived goal measured in the formal review cycle. Distinguishing traits:

- **Spans multiple workstreams and tasks** — the objective is the strategic container; workstreams are the heavy lifecycle units; tasks are the lightweight executions
- **Structured progress tracking** — Key Results with numeric targets, a milestones checklist, linked workstreams, a review cadence, and a health signal make progress legible at any review
- **Retained after completion** — the decisions log is often more valuable than the outcome
- **One folder per objective**, never deleted, lives at `control-plane/objectives/{name}/`

Not a workstream (those have defined completion states and are deleted on cleanup). Not a task (those are lightweight single-thread executions).

## Three-Tier Awareness

```
objective   (control-plane/objectives/)
  └── workstream  (control-plane/workstreams/)   ← heavy QRDPIV lifecycle
        └── task  (control-plane/tasks/)          ← lightweight unit
```

An objective may own child workstreams directly, child tasks directly, or both. When creating related work, choose the right tier: workstreams for multi-phase efforts; tasks for single-thread execution. Child workstreams are linked via `link-workstream` (which takes a workstream name).

## Session Entry — Always Run First

1. Read `control-plane/CLAUDE.md`
2. Read `control-plane/objectives/index.md`
3. If a specific objective is in scope, read its `index.md`
4. Identify the current action from the table below
5. Load **only** that action file

## Action Routing

| Situation | Load |
|---|---|
| New objective — nothing exists yet | `actions/initiate.md` |
| Existing objective — review status, update KRs/milestones/health | `actions/review.md` |
| Logging a decision against an existing objective | `actions/log-decision.md` |
| Objective is closing out | `actions/complete.md` |

## `index.md` Frontmatter

```yaml
objective: kebab-case-name
status: active | complete
health: on-track | at-risk | blocked | stale
cadence: "monthly" | "bi-weekly" | "quarterly" | ...
created: YYYY-MM-DD
completed: YYYY-MM-DD          # set at close; folder retained
tags: [objective, ...]
```

## `index.md` Sections

- **Objective** — what and why, in 1–2 paragraphs
- **Key Results** — table of measurable results with targets and current values (managed via `add-kr` / `update-kr`)
- **Milestones** — checklist of concrete checkpoints (managed via `add-milestone` / `check-milestone`)
- **Workstreams** — list of linked workstreams advancing this objective (managed via `link-workstream`)
- **Success Criteria** — how we'll know this is done
- **Dependencies** — what this objective requires from elsewhere
- **Key Decisions Log** — append-only table (Decision | Rationale | Date). **Never truncated.**
- **Definition of Done** — completion criteria
- **Related Notes** — links to parent strategy, dependent objectives

## CLI Reference

```
python -B tools/objective.py create <name> --title "<Title>"
python -B tools/objective.py status <name>
python -B tools/objective.py health <name> <on-track|at-risk|blocked|stale>
python -B tools/objective.py set-cadence <name> "<cadence>"
python -B tools/objective.py add-kr <name> "<result>" "<target>"
python -B tools/objective.py update-kr <name> "<result>" "<current>"
python -B tools/objective.py add-milestone <name> "<text>"
python -B tools/objective.py check-milestone <name> "<text>"
python -B tools/objective.py link-workstream <objective> <workstream-name>
python -B tools/objective.py log-decision <name> "<decision>" "<rationale>"
python -B tools/objective.py complete <name>
```

## Relationship to Workstreams and Tasks

Workstreams that execute toward an objective are linked via `link-workstream <objective> <workstream>` (idempotent). When a workstream or task closes, any lessons learned that inform strategy should be reflected in the objective's decisions log.

## Guiding Principle

Objectives are the **strategic memory**. The decisions log outlives the work. Keep it honest, keep it dated, never rewrite history.
