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

Then read the most recent entry in `control-plane/objectives/{name}/reviews/`. This is what makes a review a comparison rather than a snapshot — `update-kr` overwrites `current` in place, so the dated entries are the only record of trajectory.

Also read any linked missions' `index.md` for tactical status.

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

This is idempotent — safe to run even if already linked. Linked workstreams should also carry `parent: "objectives/{name}"` in their own frontmatter; the link is not a substitute for that.

### 5. Update health

Assess health based on KR trajectory, milestone progress, and open blockers:

```
python -B tools/objective.py health {name} <on-track|at-risk|blocked|stale>
```

- **on-track** — KRs advancing at expected pace, no significant blockers
- **at-risk** — KRs lagging or a blocker exists but isn't critical-path yet
- **blocked** — a hard blocker is preventing progress on a critical KR
- **stale** — no meaningful activity since last review; may need re-scoping

Distinguish *unstarted* from *obstructed*. A responsibility whose own text calls a deliverable the most unblocked next step is `at-risk`, not `blocked`.

### 6. Log any decisions

If the review surfaced decisions — priority shifts, scope changes, trade-offs made — log them:

```
python -B tools/objective.py log-decision {name} "{decision}" "{rationale}"
```

Or load `actions/log-decision.md` for the full decision-logging flow.

### 7. Record the review

A cadence-driven review that leaves no trace cannot be compared against next time:

```
python -B tools/objective.py review {name}
```

This scaffolds `reviews/YYYY-MM-DD.md` pre-filled with the KR values, milestones, missions, and health you just set. It does not modify `index.md`.

Complete the parts the tool cannot generate:

- **Health Assessment** — the call *and its evidence*. Cite a line in `index.md`, a linked mission, or a decision entry. A health value with no evidence is an assertion, and the generated placeholder says so; leaving it produces a file that looks complete and says nothing.
- **Movement Since Last Review** — what changed against the previous entry, what did not, and why. This is the section the folder exists for.
- **Decisions Taken** — carry anything material into the append-only `## Key Decisions Log` as well.

Skip this only for a passing status question. If cadence prompted the review, record it.

### 8. Report to user

```
Responsibility: {name}
Status:         {active | complete}
Health:         {on-track | at-risk | blocked | stale}
Cadence:        {cadence} — next review: {approximate date}
Created:        {created date}
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
- **Are KRs tracking?** If current values haven't moved since the last update date, flag stale KRs. Compare against the previous `reviews/` entry — `update-kr` overwrites `current` in place, so the dated entries are the only record of trajectory.
- **Are KRs meaningful?** If a KR can't be updated with a real current value, it may need to be rewritten.
- **Are there KRs at all, and should there be?** A responsibility with no Key Results is legitimate if it is discovery-stage or gated and the decisions log says so. It is a problem if the KRs were simply never derived. Check which — and if a Success Criterion states no count, threshold, or baseline, leave it as prose and log the gap. **A KR with an invented target is worse than no KR.**
- **Are linked missions active and aligned?** Workstreams listed under Missions should be making progress and should carry `parent: "objectives/{name}"`. Orphaned or misaligned work is a signal; linked missions that are themselves `blocked` or `stale` are another.
- **Are blockers accumulating?** If health is `blocked` or `stale` for more than one review cycle, suggest re-scoping.
- **Is the decisions log current?** Gaps between the last decision date and active work suggest undocumented choices — surface this.

## Recommended Next Actions

Based on the review, recommend one of:

- **Continue** — status is clear, tactical work proceeds. Point the user at the relevant mission or patrol.
- **Open a mission** — if new coordinated work is needed, suggest `/friendly-neighborhood:mission`, then `link-mission`.
- **Update KRs** — `python -B tools/objective.py update-kr {name} "<result>" "<current>"`.
- **Check a milestone** — `python -B tools/objective.py check-milestone {name} "<text>"`.
- **Link a delivered mission** — `python -B tools/objective.py link-mission {name} workstreams/_log/<entry> --status complete`. A responsibility showing "(none yet)" despite delivered work misreports its own state.
- **Log a decision** — if the user's conversation surfaced a decision worth capturing, load `actions/log-decision.md`.
- **Close out** — if success criteria are met or the responsibility is being retired, load `actions/complete.md`.
- **Re-scope** — if the responsibility has drifted, suggest reviewing and updating Success Criteria / Definition of Done sections and resetting KRs via `add-kr`.

## Portfolio-Level Review

If asked to review all responsibilities: run `python -B tools/objective.py list` then read `control-plane/objectives/index.md` and visit each active responsibility's `index.md`. Produce a concise roll-up — one line per responsibility with health signal, KR summary, and top blocker if any.
