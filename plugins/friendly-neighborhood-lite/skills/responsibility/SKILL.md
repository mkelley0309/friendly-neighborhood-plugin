---
name: responsibility
description: >
  Manages the lifecycle of a responsibility in control-plane/objectives/ — a long-lived,
  review-cycle-measured objective with structured progress tracking: Key Results (with
  targets), milestones, linked missions (workstreams), a review cadence, a health signal,
  and an append-only decisions log. With great power comes great responsibility: this is
  the strategic container that outlasts any individual patrol or mission beneath it.
  Trigger when the user references a formal responsibility, a review-cycle goal, or wants
  to capture a strategic objective that will span multiple missions or patrols. Also
  trigger when asked about responsibility status, when KRs or milestones need updating,
  when decisions should be logged against a responsibility, or when a responsibility is
  closing out.
---

# Responsibility Skill

## What Is a Responsibility

A long-lived objective measured in the formal review cycle. Distinguishing traits:

- **Spans multiple missions and patrols** — the responsibility is the strategic container; missions are mid-horizon coordinators; patrols are the tactical executions
- **Structured progress tracking** — Key Results with numeric targets, a milestones checklist, linked workstreams (child missions), a review cadence, and a health signal make progress legible at any review
- **Retained after completion** — the decisions log is often more valuable than the outcome
- **One folder per responsibility**, never deleted, lives at `control-plane/objectives/{name}/`

Not a mission (those coordinate a cluster of patrols under a bounded goal). Not a patrol (those have defined completion states and are deleted on cleanup).

## Three-Tier Awareness

```
responsibility  (control-plane/objectives/)
  └── mission   (control-plane/workstreams/)   ← child missions are workstreams
        └── patrol  (control-plane/patrols/)
```

A responsibility may own child missions directly, child patrols directly, or both. When creating related work, choose the right tier: missions for multi-patrol efforts; patrols for single-thread execution. Child missions are linked via `link-mission` (which takes a workstream name).

## Session Entry — Always Run First

1. Read `control-plane/CLAUDE.md`
2. Read `control-plane/objectives/index.md`
3. If a specific responsibility is in scope, read its `index.md`
4. Identify the current action from the table below
5. Load **only** that action file

## Action Routing

| Situation | Load |
|---|---|
| New responsibility — nothing exists yet | `actions/initiate.md` |
| Existing responsibility — review status, update KRs/milestones/health | `actions/review.md` |
| Logging a decision against an existing responsibility | `actions/log-decision.md` |
| Responsibility is closing out | `actions/complete.md` |

## `index.md` Frontmatter

```yaml
objective: kebab-case-name
status: active | complete
health: on-track | at-risk | blocked | stale
cadence: "monthly" | "bi-weekly" | "quarterly" | ...
created: YYYY-MM-DD
completed: YYYY-MM-DD          # set at close; folder retained
tags: [objective, ...]
note_type: objective
```

## `index.md` Sections

- **Responsibility** — what and why, in 1–2 paragraphs
- **Key Results** — table of measurable results with targets and current values (managed via `add-kr` / `update-kr`)
- **Milestones** — checklist of concrete checkpoints (managed via `add-milestone` / `check-milestone`)
- **Missions** — list of linked workstreams advancing this responsibility (managed via `link-mission`)
- **Success Criteria** — how we'll know this is done
- **Dependencies** — what this responsibility requires from elsewhere
- **Key Decisions Log** — append-only table (Decision | Rationale | Date). **Never truncated.**
- **Definition of Done** — completion criteria
- **Related Notes** — links to parent strategy, dependent responsibilities

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
python -B tools/objective.py link-mission <name> <workstream-name>
python -B tools/objective.py log-decision <name> "<decision>" "<rationale>"
python -B tools/objective.py complete <name>
```

## Relationship to Missions and Patrols

Missions that execute toward a responsibility are workstreams linked via `link-mission <objective> <workstream>` (idempotent). When a mission or patrol closes, any lessons learned that inform strategy should be reflected in the responsibility's decisions log.

## Guiding Principle

Responsibilities are the **strategic memory**. The decisions log outlives the work. Keep it honest, keep it dated, never rewrite history.
