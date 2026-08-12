---
name: responsibility
description: >
  Manages the lifecycle of a responsibility in control-plane/objectives/ — a long-lived,
  checkpoint-cycle-measured responsibility with structured progress tracking: Key Results (with
  targets), milestones, linked campaigns, a checkpoint cadence, a health signal,
  and an append-only decisions log. This is the strategic container that outlasts
  any individual mission or campaign beneath it.
  Trigger when the user references a formal responsibility, a checkpoint-cycle goal, or wants
  to capture a strategic responsibility that will span multiple campaigns or missions. Also
  trigger when asked about responsibility status, when KRs or milestones need updating,
  when decisions should be logged against a responsibility, or when a responsibility is
  closing out.
---

# Responsibility Skill

## What Is a Responsibility

A long-lived goal measured in the formal checkpoint cycle. Distinguishing traits:

- **Spans multiple campaigns and missions** — the responsibility is the strategic container; campaigns are the heavy lifecycle units; missions are the lightweight executions
- **Structured progress tracking** — Key Results with numeric targets, a milestones checklist, linked campaigns, a checkpoint cadence, and a health signal make progress legible at any checkpoint
- **Retained after completion** — the decisions log is often more valuable than the outcome
- **One folder per responsibility**, never deleted, lives at `control-plane/objectives/{name}/`

Not a campaign (those have defined completion states and are deleted on cleanup). Not a mission (those are lightweight single-thread executions).

## Three-Tier Awareness

```
responsibility   (control-plane/objectives/)
  └── campaign  (control-plane/workstreams/)   ← heavy QRDBIV lifecycle
        └── mission  (control-plane/missions/)          ← lightweight unit
```

A responsibility may own child campaigns directly, child missions directly, or both. When creating related work, choose the right tier: campaigns for multi-phase efforts; missions for single-thread execution. Child campaigns are linked via `link-campaign` (which takes a campaign name).

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
| Existing responsibility — checkpoint status, update KRs/milestones/health | `actions/checkpoint.md` |
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
tags: [responsibility, ...]
```

## `index.md` Sections

Canonical order — this is what `create` generates and what backfilled responsibilities follow:

1. **Responsibility** — what and why, in 1–2 paragraphs
2. **Success Criteria** — how we'll know this is done; prose, the fuller narrative
3. **Key Results** — table of measurable results with targets and current values (managed via `add-kr` / `update-kr`)
4. **Milestones** — checklist of concrete checkpoints (managed via `add-milestone` / `check-milestone`)
5. **Campaigns** — linked campaigns advancing this responsibility (managed via `link-campaign`)
6. *objective-specific sections* — Content Scope, Sequencing, Stakeholders, etc. Keep their own relative order.
7. **Dependencies** — what this responsibility requires from elsewhere
8. **Key Decisions Log** — append-only table (Decision | Rationale | Date). **Never truncated, never reordered.**
9. **Definition of Done** — completion criteria
10. **Related Notes** — links to parent strategy, dependent responsibilities. Always last.

The three managed sections sit **after** Success Criteria. When a managed section is absent, the tool inserts it immediately before `## Related Notes` rather than at end of file.

### Not everything is a Key Result

Key Results are for criteria that already imply a count, a state transition, or a verifiable artifact. Where a Success Criterion states no count, threshold, or baseline — including one that uses the word "measurable" without defining the measure — leave it as prose and log the gap in the Key Decisions Log. **A KR with an invented target is worse than no KR**, because it manufactures a progress signal nobody can trust.

The same applies to an entire responsibility: a discovery-stage or gated responsibility may legitimately carry no Key Results at all. Record why in the decisions log.

## Checkpoints

`cadence` mandates recurring checkpoints. Each checkpoint is a dated file in the responsibility's own folder, never appended to `index.md`:

```
objectives/{name}/
  index.md
  checkpoints/YYYY-MM-DD.md
```

```
python -B tools/objective.py checkpoint <name> [--date YYYY-MM-DD] [--force]
```

Snapshots current KRs, milestones, campaigns, and health into a new entry. It does not write to `index.md`. This is what gives Key Results a history — `update-kr` overwrites `current` in place, so without a dated snapshot the trajectory is lost on every update, and `health` can only ever be asserted rather than derived.

When filling a checkpoint, the health call must cite its evidence — a line in `index.md`, a linked campaign, a decision entry. A health value without evidence is an assertion.

## CLI Reference

```
python -B tools/objective.py create <name> --title "<Title>" [--group "<index subgroup>"]
python -B tools/objective.py status <name>
python -B tools/objective.py health <name> <on-track|at-risk|blocked|stale>
python -B tools/objective.py set-cadence <name> "<cadence>"
python -B tools/objective.py checkpoint <name> [--date YYYY-MM-DD] [--force]
python -B tools/objective.py add-kr <name> "<result>" "<target>"
python -B tools/objective.py update-kr <name> "<result>" "<current>"
python -B tools/objective.py add-milestone <name> "<text>"
python -B tools/objective.py check-milestone <name> "<text>"
python -B tools/objective.py link-campaign <responsibility> <campaign> [--status active|complete|paused|abandoned]
python -B tools/objective.py log-decision <name> "<decision>" "<rationale>"
python -B tools/objective.py complete <name>
```

## Relationship to Campaigns and Missions

Campaigns that execute toward a responsibility are linked via `link-campaign <responsibility> <campaign>` (idempotent — a duplicate link is a silent no-op). The target must resolve on disk; the command rejects a name that does not exist rather than recording a dangling link.

Completed campaigns are linked too, by their log path and with an explicit status:

```
python -B tools/objective.py link-campaign field-enablement \
    workstreams/_log/2026-05-22-fynapse-buy-v-build-insurance --status complete
```

A responsibility whose `## Campaigns` reads "(none yet)" despite delivered work misreports its own state, and `health` is judged partly on that. When a campaign or mission closes, link it, and reflect any strategy-relevant lessons in the responsibility's decisions log.

## Guiding Principle

Responsibilities are the **strategic memory**. The decisions log outlives the work. Keep it honest, keep it dated, never rewrite history.
