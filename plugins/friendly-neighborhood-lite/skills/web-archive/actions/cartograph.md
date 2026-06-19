# Action: Cartograph

Add cross-vault wiki-links to existing vault notes' Related sections, create or update `vault/_graph/` cross-cutting indexes, and add `related:` frontmatter to existing notes.

## When to run

- User-invoked only. Never runs automatically.
- Typical triggers: patrol cleanup, finishing a distillation batch, user says "cross-link these notes", "run Cartographer", "map relationships in X subtree"
- Never triggered by Scout, Harvester, or Peer Reviewer

---

## Silo exemption

Cartographer is not a distiller. It operates post-curation and is explicitly exempt from distiller silo discipline. It may read across vault subtree boundaries.

---

## File-Path Gate

| Direction | Allowed paths |
|---|---|
| Read | `vault/` (any subtree) |
| Write — existing notes | Append to `## Related` section; add `related:` frontmatter field |
| Write — indexes | Create or update `vault/_graph/*.md` |

**Never:**
- Create new content notes in distiller-owned subtrees
- Delete any note
- Modify note body content beyond the `## Related` section
- Touch `sources/` or `distillers/`

---

## Scope clarification

Cartographer does not self-select scope. Before reading any vault content, the user must specify:

- Which subtree(s) to cross-link (e.g., `vault/domain-knowledge/`, `vault/reference/`), OR
- Which concept(s) or theme(s) to graph, OR
- An explicit note list

If scope is ambiguous, stop and ask. Do not proceed on guessed scope.

---

## Steps

### 1. Confirm scope with user

Restate the scope as you understand it. Wait for explicit confirmation before reading vault content. Example:

> "I'll read notes under `vault/domain-knowledge/` and `vault/reference/` and surface cross-links around the specified themes. Proceed?"

---

### 2. Read vault notes in scope

Read each note in the confirmed scope. For large scopes (more than ~15 notes), delegate reading to Sonnet subagents — one per subtree. Each subagent returns a structured list:

```
note: <note-slug>
path: vault/{subtree}/{note-slug}.md
concepts: [<concept-slug>, ...]
candidate_links: [(<target-slug>, "<one-line reason>"), ...]
```

Each subagent response must be ≤400 words. The main context collects all lists before deciding which links to write.

---

### 3. Identify relationships worth linking

For each candidate link, apply the quality bar:

**Write the link if:**
- The concepts are substantively related (not just sharing a keyword)
- A reader of the source note would genuinely benefit from knowing the target note exists
- The relationship is navigational, not merely associative

**Do not write the link if:**
- The only connection is a shared term used differently in each note
- The target note is already linked in the source note's body
- The link would duplicate an existing `## Related` entry

Build a deduplicated link plan before writing anything.

---

### 4. Write links and frontmatter

For each approved link pair (source → target):

#### a. Related section

Locate `## Related` in the source note. If present, append the new entry. If absent, create the section after the main body (before any footer `---`):

```markdown
## Related

- [[target-slug|Target Title]] — one-line reason for the link
```

Append format (section already exists):

```markdown
- [[target-slug|Target Title]] — one-line reason for the link
```

Do not reorder or reformat existing entries.

#### b. Frontmatter `related:` field

If `related:` is absent from frontmatter, add it:

```yaml
related: [target-slug]
```

If `related:` already exists as a list, append the slug without duplicating:

```yaml
related: [existing-slug, target-slug]
```

Do not touch any other frontmatter field.

---

### 5. Update or create `_graph/` indexes

For any cross-cutting theme that surfaces across two or more subtrees, create or update `vault/_graph/{topic}.md`.

**Create format:**

```markdown
---
note_type: graph-index
topic: <slug>
tags: [knowledge, graph]
---

# {Topic} — Cross-Vault Index

Notes across the vault related to this concept:

- [[note-slug|Note Title]] (`vault/{subtree}/`) — one-line summary
```

**Update format:** append new entries to the list; do not remove or reorder existing entries.

One index file per cross-cutting topic. Use kebab-case slugs for file names (e.g., `vault/_graph/topic-name.md`).

---

### 6. Report changes

After all writes complete, report:

| Category | Count | Details |
|---|---|---|
| Notes modified | N | list of paths |
| Links added | N | list of (source → target) pairs |
| Frontmatter fields added | N | list of notes where `related:` was added or extended |
| `_graph/` indexes created | N | list of new index files |
| `_graph/` indexes updated | N | list of updated index files |

If no links met the quality bar, say so explicitly and explain why.

---

## Subagent delegation pattern

For scopes larger than ~15 notes, use parallel Sonnet subagents:

1. Split scope by subtree
2. Dispatch one subagent per subtree with instructions to read notes and return the structured list (note, concepts, candidate links) in ≤400 words
3. Wait for all subagents to return
4. Merge lists in main context; deduplicate candidates across subtrees
5. Apply quality bar centrally; build final link plan
6. Execute all writes in main context (not delegated)

Writes are never delegated. Only reading and candidate generation are delegated.

---

## Quality bar summary

| Write the link | Do not write the link |
|---|---|
| Substantively related concepts | Shared keyword used differently |
| Reader of source benefits from knowing target | Target already linked in note body |
| Genuine navigational value | Would duplicate an existing Related entry |
