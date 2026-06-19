# Action: Review Objective

Assess an objective's state and surface status for the user. Load this file only.

## Steps

1. Run `python -B tools/objective.py status {name}` and read the output
2. Read `control-plane/objectives/{name}/index.md` — frontmatter and all sections
3. Read any child workstreams' `index.md` for tactical status
4. Report to user:

```
Objective:          {name}
Status:             {active | complete}
Health:             {on-track | at-risk | blocked | stale}
Cadence:            {review cadence}
Created:            {created date}
Key Results:        {count} total — show current/target for each
Milestones:         {done}/{total} complete
Active workstreams: {list child workstreams}
Recent decisions:   {last 1–3 entries from Key Decisions Log}
Open dependencies:  {unresolved items from Dependencies section}
```

## Assessment Questions

Answer these implicitly in the report, or raise explicitly if the user is asking for advice:

- **Is the objective still well-shaped?** If the success criteria look obsolete or the definition of done has drifted, flag it.
- **Are workstreams aligned?** Child workstreams should have `parent: "objectives/{name}"`. Orphaned or misaligned work is a signal.
- **Are KRs tracking?** If current values haven't moved since the last update date, flag stale KRs.
- **Are blockers accumulating?** If multiple child workstreams are `blocked` or `stale`, the objective itself may need re-scoping.
- **Is the decisions log current?** Gaps between the last decision date and active work suggest undocumented choices.

## Recommended Next Actions

Based on the review, recommend one of:

- **Continue** — status is clear, tactical work proceeds. Point the user at the relevant workstream.
- **Open a workstream** — suggest the `workstream` skill with `parent: "objectives/{name}"`.
- **Update KRs** — `python -B tools/objective.py update-kr {name} "<result>" "<current>"`.
- **Check a milestone** — `python -B tools/objective.py check-milestone {name} "<text>"`.
- **Log a decision** — if the user's conversation surfaced a decision worth capturing, load `actions/log-decision.md`.
- **Close out** — if success criteria are met or the objective is being retired, load `actions/complete.md`.
- **Re-scope** — if the objective has drifted, suggest reviewing and updating the Success Criteria / Definition of Done sections via direct editing.

## Portfolio-Level Review

If asked to review all objectives: run `python -B tools/objective.py list` then read `control-plane/objectives/index.md` and visit each active objective's `index.md`. Produce a concise roll-up — one line per objective with current status and top blocker if any.
