# Action: Review Responsibility

Conduct a structured review of a responsibility — honoring the cadence, updating progress tracking, and surfacing what needs attention. Load this file only.

## When to Run

- Scheduled review (cadence from frontmatter has elapsed)
- User asks for status or progress on a responsibility
- User wants to update KRs, check off milestones, or adjust health
- Portfolio-level roll-up requested

## Steps

### 1. Pull current state

Run:

```
python -B tools/objective.py status {name}
```

`status` now prints Key Results (with targets and current values), milestone done/total counts, and linked missions. Read the output, then also read `control-plane/objectives/{name}/index.md` for full context (frontmatter: `health:`, `cadence:`; all sections).

### 2. Update Key Results

For each KR where the current value has changed, run:

```
python -B tools/objective.py update-kr {name} "{result}" "{new-current-value}"
```

Update all KRs that have moved since the last review. Do not skip KRs that haven't changed — note them explicitly as unchanged in the report.

### 3. Check off completed milestones

For each milestone the user confirms is done:

```
python -B tools/objective.py check-milestone {name} "{exact milestone text}"
```

The text must match the milestone exactly as it appears in the index.

### 4. Link any new missions

If a new workstream has been spun up to advance this responsibility and isn't yet linked:

```
python -B tools/objective.py link-mission {name} {workstream-name}
```

This is idempotent — safe to run even if already linked.

### 5. Update health

Assess health based on KR trajectory, milestone progress, and open blockers:

```
python -B tools/objective.py health {name} <on-track|at-risk|blocked|stale>
```

- **on-track** — KRs advancing at expected pace, no significant blockers
- **at-risk** — KRs lagging or a blocker exists but isn't critical-path yet
- **blocked** — a hard blocker is preventing progress on a critical KR
- **stale** — no meaningful activity since last review; may need re-scoping

### 6. Log any decisions

If the review surfaced decisions — priority shifts, scope changes, trade-offs made — log them:

```
python -B tools/objective.py log-decision {name} "{decision}" "{rationale}"
```

Or load `actions/log-decision.md` for the full decision-logging flow.

### 7. Report to user

```
Responsibility: {name}
Health:         {on-track | at-risk | blocked | stale}
Cadence:        {cadence} — next review: {approximate date}
Key Results:
  - {result}: {current} / {target}   [{on track | lagging | met}]
Milestones:     {done}/{total} complete
Linked missions: {list of workstream names}
Recent decisions: {last 1–3 entries from Key Decisions Log}
Open dependencies: {unresolved items from Dependencies section}
```

## Assessment Questions

Answer these implicitly in the report, or raise explicitly if the user is asking for advice:

- **Is the responsibility still well-shaped?** If success criteria look obsolete or definition of done has drifted, flag it.
- **Are KRs meaningful?** If a KR can't be updated with a real current value, it may need to be rewritten.
- **Are linked missions active and aligned?** Workstreams listed under Missions should be making progress. Orphaned or stale missions are a signal.
- **Are blockers accumulating?** If health is `blocked` or `stale` for more than one review cycle, suggest re-scoping.
- **Is the decisions log current?** Gaps between the last decision date and active work suggest undocumented choices — surface this.

## Recommended Next Actions

Based on the review, recommend one of:

- **Continue** — status is clear, tactical work proceeds. Point the user at the relevant mission or patrol.
- **Open a mission** — if new coordinated work is needed, suggest `/friendly-neighborhood-lite:mission`, then `link-mission`.
- **Log a decision** — if the user's conversation surfaced a decision worth capturing, load `actions/log-decision.md`.
- **Close out** — if success criteria are met or the responsibility is being retired, load `actions/complete.md`.
- **Re-scope** — if the responsibility has drifted, suggest reviewing and updating Success Criteria / Definition of Done sections and resetting KRs via `add-kr`.

## Portfolio-Level Review

If asked to review all responsibilities: run `python -B tools/objective.py list` then read `control-plane/objectives/index.md` and visit each active responsibility's `index.md`. Produce a concise roll-up — one line per responsibility with health signal, KR summary, and top blocker if any.
