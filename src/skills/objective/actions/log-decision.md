# Action: Log a Decision

Append an entry to an objective's Key Decisions Log. Load this file only.

## When to Run

A decision has been made — by the user, in conversation, or via a workstream outcome — that:
- Affects how this objective will be pursued
- Closes off an alternative path
- Would be useful context for future-you at review time

**The decisions log is the durable value of an objective.** Err on the side of logging.

## Steps

### 1. Confirm the decision

If the user hasn't stated the decision explicitly as such, restate it and confirm:

> "Just to confirm — you've decided {X}, because {Y}. Log that?"

### 2. Append a new row

Run:

```
python -B tools/objective.py log-decision {name} "{Decision in 1 sentence}" "{Rationale — what it enables or trades off}"
```

Or use the Edit tool to append one row to the Key Decisions Log table. **Never rewrite history** — only add. If a decision reverses an earlier one, log the reversal as a new row with a rationale that references the prior decision.

Format:

```markdown
| {Decision in 1 sentence} | {Rationale — what it enables or trades off} | {YYYY-MM-DD} |
```

Keep each cell short. Decision ≤ 15 words; rationale ≤ 25 words. If more context is needed, reference a workstream log entry or related note.

### 3. Cross-link (optional)

If the decision came from a workstream, reference that entry in the Related Notes section:

```markdown
- [Workstream log — {date}-{name}](../../workstreams/_log/{date}-{name}.md) — decision surfaced here
```

### 4. Confirm to user

Tell the user: decision logged at `{date}`, row appended to the Key Decisions Log.

Do not summarize the whole objective afterward — the log is the record.
