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
cadence: weekly | bi-weekly | monthly | quarterly | semi-annual | annual
created: YYYY-MM-DD
completed: YYYY-MM-DD          # set at close; folder retained
tags: [objective, ...]
note_type: objective
```

## `index.md` Sections

Canonical order — this is what `create` generates and what backfilled responsibilities follow:

1. **Responsibility** — what and why, in 1–2 paragraphs
2. **Success Criteria** — how we'll know this is done; prose, the fuller narrative
3. **Key Results** — table of measurable results with targets and current values (managed via `add-kr` / `update-kr`)
4. **Milestones** — checklist of concrete checkpoints (managed via `add-milestone` / `check-milestone`)
5. **Missions** — linked missions advancing this responsibility (managed via `link-mission`)
6. *responsibility-specific sections* — Content Scope, Sequencing, Stakeholders, etc. Keep their own relative order.
7. **Dependencies** — what this responsibility requires from elsewhere
8. **Key Decisions Log** — append-only table (Decision | Rationale | Date). **Never truncated, never reordered.**
9. **Definition of Done** — completion criteria
10. **Related Notes** — links to parent strategy, dependent responsibilities. Always last.

The three managed sections sit **after** Success Criteria. When a managed section is absent, the tool inserts it immediately before `## Related Notes` rather than at end of file.

### Not everything is a Key Result

Key Results are for criteria that already imply a count, a state transition, or a verifiable artifact. Where a Success Criterion states no count, threshold, or baseline — including one that uses the word "measurable" without defining the measure — leave it as prose and log the gap in the Key Decisions Log. **A KR with an invented target is worse than no KR**, because it manufactures a progress signal nobody can trust.

The same applies to an entire responsibility: a discovery-stage or gated responsibility may legitimately carry no Key Results at all. Record why in the decisions log.

## Reviews

`cadence` mandates recurring review. Each review is a dated file in the responsibility's own folder, never appended to `index.md`:

```
objectives/{name}/
  index.md
  reviews/YYYY-MM-DD.md
```

```
python -B tools/objective.py review <name> [--date YYYY-MM-DD] [--force]
```

Snapshots current KRs, milestones, missions, and health into a new entry. It does not write to `index.md`. This is what gives Key Results a history — `update-kr` overwrites `current` in place, so without a dated snapshot the trajectory is lost on every update, and `health` can only ever be asserted rather than derived.

When filling a review, the health call must cite its evidence — a line in `index.md`, a linked mission, a decision entry. A health value without evidence is an assertion.

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
python -B tools/objective.py link-mission <name> <mission> [--status active|complete|paused|abandoned]
python -B tools/objective.py log-decision <name> "<decision>" "<rationale>"
python -B tools/objective.py complete <name>
```

## Relationship to Missions and Patrols

Missions that execute toward a responsibility are linked via `link-mission <responsibility> <mission>` (idempotent — a duplicate link is a silent no-op). The target must resolve on disk; the command rejects a name that does not exist rather than recording a dangling link.

Completed missions are linked too, by their log path and with an explicit status:

```
python -B tools/objective.py link-mission field-enablement \n    workstreams/_log/2026-05-22-example --status complete
```

A responsibility whose `## Missions` reads "(none yet)" despite delivered work misreports its own state, and `health` is judged partly on that.

## Guiding Principle

Responsibilities are the **strategic memory**. The decisions log outlives the work. Keep it honest, keep it dated, never rewrite history.
