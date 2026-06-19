# Action: Complete Responsibility

Close out a responsibility. Load this file only.

## Key Difference From Patrol Cleanup

**Responsibility folders are NEVER deleted.** Completion is a status change and a summary entry, not a cleanup. The folder, its `index.md`, and its decisions log persist indefinitely — they are the record for review.

## When to Run

- All Success Criteria met (verify each explicitly)
- All Definition of Done conditions satisfied
- User confirms they are ready to close

If any child mission or patrol is still active, do not close the responsibility — either complete or explicitly abandon those first.

## Steps

### 1. Verify completion against Success Criteria

Read `control-plane/objectives/{name}/index.md`. For each item in Success Criteria, confirm it's actually met. If any are not: stop, report the gap, do not close.

### 2. Check linked missions and patrols

Run `python -B tools/objective.py status {name}` — the Missions section lists linked workstreams. Any active workstream (mission or patrol) tied to this responsibility must be resolved first: completed, or explicitly abandoned with a decision logged.

### 3. Write a Completion Summary section

Use the Edit tool to append a new top-level section to the responsibility's `index.md`, immediately before the `## Related Notes` section (or at the end if no Related Notes). The structured sections (Key Results, Milestones, Missions) remain in place — they are the completion record.

```markdown
## Completion Summary

**Completed:** {YYYY-MM-DD}

### Outcome

{2–4 sentences on what was achieved vs. the Responsibility statement. Honest — if scope changed, say so.}

### Success Criteria Resolution

- ✅ {criterion} — {how it was met}
- ✅ {criterion} — {how it was met}

### What Lives On After Close

{Where the work continues — systems folder, ongoing operational workflow, spawned responsibilities, etc.}

### Lessons Learned

{What to carry into future responsibilities. Honest.}
```

### 4. Update frontmatter

Run:

```
python -B tools/objective.py complete {name}
```

Or edit frontmatter directly:

```yaml
status: complete           # was: active
completed: {YYYY-MM-DD}    # add this field
```

Do NOT remove other frontmatter fields. Do NOT truncate the decisions log.

### 5. Update portfolio index

In `control-plane/objectives/index.md`:

- Remove the row from Active table
- Add to Complete table:

```markdown
| [{name}]({name}/index.md) | {one-line description} | {YYYY-MM-DD} | {1-line key outcome} |
```

### 6. Report

Tell the user:
- Responsibility closed, folder retained at `control-plane/objectives/{name}/`
- Decisions log preserved
- Completion summary written
- Any child mission or patrol logs that reference this responsibility remain valid

Remind them: the folder is not deleted. It is referenced in future review cycles.
