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
cadence: weekly | bi-weekly | monthly | quarterly | semi-annual | annual
created: YYYY-MM-DD
completed: YYYY-MM-DD          # set at close; folder retained
tags: [objective, ...]
```

## `index.md` Sections

Canonical order — this is what `create` generates and what backfilled objectives follow:

1. **Objective** — what and why, in 1–2 paragraphs
2. **Success Criteria** — how we'll know this is done; prose, the fuller narrative
3. **Key Results** — table of measurable results with targets and current values (managed via `add-kr` / `update-kr`)
4. **Milestones** — checklist of concrete checkpoints (managed via `add-milestone` / `check-milestone`)
5. **Workstreams** — linked workstreams advancing this objective (managed via `link-workstream`)
6. *objective-specific sections* — Content Scope, Sequencing, Stakeholders, etc. Keep their own relative order.
7. **Dependencies** — what this objective requires from elsewhere
8. **Key Decisions Log** — append-only table (Decision | Rationale | Date). **Never truncated, never reordered.**
9. **Definition of Done** — completion criteria
10. **Related Notes** — links to parent strategy, dependent objectives. Always last.

The three managed sections sit **after** Success Criteria. When a managed section is absent, the tool inserts it immediately before `## Related Notes` rather than at end of file.

### Not everything is a Key Result

Key Results are for criteria that already imply a count, a state transition, or a verifiable artifact. Where a Success Criterion states no count, threshold, or baseline — including one that uses the word "measurable" without defining the measure — leave it as prose and log the gap in the Key Decisions Log. **A KR with an invented target is worse than no KR**, because it manufactures a progress signal nobody can trust.

The same applies to an entire objective: a discovery-stage or gated objective may legitimately carry no Key Results at all. Record why in the decisions log.

## Reviews

`cadence` mandates recurring review. Each review is a dated file in the objective's own folder, never appended to `index.md`:

```
objectives/{name}/
  index.md
  reviews/YYYY-MM-DD.md
```

```
python -B tools/objective.py review <name> [--date YYYY-MM-DD] [--force]
```

Snapshots current KRs, milestones, workstreams, and health into a new entry. It does not write to `index.md`. This is what gives Key Results a history — `update-kr` overwrites `current` in place, so without a dated snapshot the trajectory is lost on every update, and `health` can only ever be asserted rather than derived.

When filling a review, the health call must cite its evidence — a line in `index.md`, a linked workstream, a decision entry. A health value without evidence is an assertion.

## CLI Reference

```
python -B tools/objective.py create <name> --title "<Title>" [--group "<index subgroup>"]
python -B tools/objective.py status <name>
python -B tools/objective.py health <name> <on-track|at-risk|blocked|stale>
python -B tools/objective.py set-cadence <name> "<cadence>"
python -B tools/objective.py review <name> [--date YYYY-MM-DD] [--force]
python -B tools/objective.py add-kr <name> "<result>" "<target>"
python -B tools/objective.py update-kr <name> "<result>" "<current>"
python -B tools/objective.py add-milestone <name> "<text>"
python -B tools/objective.py check-milestone <name> "<text>"
python -B tools/objective.py link-workstream <objective> <workstream> [--status active|complete|paused|abandoned]
python -B tools/objective.py log-decision <name> "<decision>" "<rationale>"
python -B tools/objective.py complete <name>
```

## Relationship to Workstreams and Tasks

Workstreams that execute toward an objective are linked via `link-workstream <objective> <workstream>` (idempotent — a duplicate link is a silent no-op). The target must resolve on disk; the command rejects a name that does not exist rather than recording a dangling link.

Completed workstreams are linked too, by their log path and with an explicit status:

```
python -B tools/objective.py link-workstream field-enablement \
    workstreams/_log/2026-05-22-fynapse-buy-v-build-insurance --status complete
```

An objective whose `## Workstreams` reads "(none yet)" despite delivered work misreports its own state, and `health` is judged partly on that. When a workstream or task closes, link it, and reflect any strategy-relevant lessons in the objective's decisions log.

## Guiding Principle

Objectives are the **strategic memory**. The decisions log outlives the work. Keep it honest, keep it dated, never rewrite history.
