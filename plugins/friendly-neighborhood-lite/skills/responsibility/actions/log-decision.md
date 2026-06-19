# Action: Log a Decision

Append an entry to a responsibility's Key Decisions Log. Load this file only.

## When to Run

A decision has been made — by the user, in conversation, or via a mission or patrol outcome — that:
- Affects how this responsibility will be pursued
- Closes off an alternative path
- Would be useful context for future-you at review time

**The decisions log is the durable value of a responsibility.** Err on the side of logging. With great power comes great responsibility — and great responsibility demands an honest record.

## Steps

### 1. Confirm the decision

If the user hasn't stated the decision explicitly as such, restate it and confirm:

> "Just to confirm — you've decided {X}, because {Y}. Log that?"

### 2. Read the responsibility `index.md`

Read `control-plane/objectives/{name}/index.md`. Locate the Key Decisions Log table.

### 3. Append a new row

Use the Edit tool to append one row to the table. **Never rewrite history** — only add. If a decision reverses an earlier one, log the reversal as a new row with a rationale that references the prior decision.

Format:

```markdown
| {Decision in 1 sentence} | {Rationale — what it enables or trades off} | {YYYY-MM-DD} |
```

Keep each cell short. Decision ≤ 15 words; rationale ≤ 25 words. If more context is needed, reference a mission log entry, patrol log entry, or related note.

You may also run:

```
python -B tools/objective.py log-decision {name} "{decision}" "{rationale}"
```

### 4. Update `tags` if warranted

If the decision introduces a new concept worth surfacing (new domain, new tool, new constraint), add a tag to the frontmatter.

### 5. Cross-link (optional)

If the decision came from a mission or patrol (workstream), reference that entry in the Related Notes section:

```markdown
- [Mission — {name}](../../workstreams/{name}/index.md) — decision surfaced here
- [Patrol log — {date}-{name}](../../workstreams/_log/{date}-{name}.md) — decision surfaced here
```

### 6. Confirm to user

Tell the user: decision logged at `{date}`, row appended to the Key Decisions Log.

Do not summarize the whole responsibility afterward — the log is the record.
