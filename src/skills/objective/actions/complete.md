# Action: Complete Objective

Close out an objective. Load this file only.

## Key Difference From Workstream Cleanup

**Objective folders are NEVER deleted.** Completion is a status change and a summary entry, not a cleanup. The folder, its `index.md`, and its decisions log persist indefinitely — they are the record for review.

## When to Run

- All Success Criteria met (verify each explicitly)
- All Definition of Done conditions satisfied
- User confirms they are ready to close

If any child workstream is still active, do not close the objective — either complete or explicitly abandon those first.

## Steps

### 1. Verify completion against Success Criteria

Read `control-plane/objectives/{name}/index.md`. For each item in Success Criteria, confirm it's actually met. If any are not: stop, report the gap, do not close.

### 2. Check child workstreams

Read `control-plane/workstreams/index.md` — any active workstream with `parent: "objectives/{name}"` must be resolved first (completed via `workstream` skill's cleanup or explicitly paused/abandoned).

### 3. Write a Completion Summary section

Use the Edit tool to append a new top-level section to the objective's `index.md`, immediately before the `## Related Notes` section (or at the end if no Related Notes):

```markdown
## Completion Summary

**Completed:** {YYYY-MM-DD}

### Outcome

{2–4 sentences on what was achieved vs. the Objective statement. Honest — if scope changed, say so.}

### Key Results Resolution

{For each KR, note the final value achieved vs. the target.}

### What Lives On After Close

{Where the work continues — systems, ongoing workflows, spawned objectives, etc.}

### Lessons Learned

{What to carry into future objectives. Honest.}
```

### 4. Update frontmatter

Run:

```
python -B tools/objective.py complete {name}
```

Do NOT remove other frontmatter fields. Do NOT truncate the decisions log.

### 5. Report

Tell the user:
- Objective closed, folder retained at `control-plane/objectives/{name}/`
- Decisions log preserved
- Completion summary written
- Any workstream logs that reference this objective remain valid

Remind them: the folder is not deleted. It is referenced in future review cycles.
