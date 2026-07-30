# Action: Cartograph

Add **intra-subtree** wiki-links to existing notes' Related sections (with `related:` frontmatter), and record **cross-subtree** connections in `vault/_graph/` concept hubs — **never** as direct cross-subtree `Related:` links.

## When to run

- User-invoked only. Never runs automatically.
- Typical triggers: mission cleanup, finishing a distillation batch, user says "cross-link these notes", "run Cartographer", "map relationships in X subtree"
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
| Write — concept hubs | Create or update `vault/_graph/*.md` |

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

**Link-target validation (MANDATORY — prevents phantom nodes).** Before writing ANY `[[target]]` wiki-link, verify the target resolves to an existing note. For a full vault-path target, confirm `vault/{target}.md` exists with a Glob/Read check — do NOT guess a sub-path (e.g. `…/topic/overview`) when the real note is the leaf (`…/topic`). For a short target, confirm exactly one note has that basename. If the target does not exist, do not write the link — point at the correct note or skip it. The same rule applies to slugs in `related:` frontmatter. A wiki-link to a nonexistent path renders as a greyed phantom node and spawns a blank stub on click.

**Route by subtree (MANDATORY).** If source and target are in the **same subtree**, write a `Related:` link (a, b below). If they are in **different subtrees**, do **not** write a direct `Related:` link — record the connection in a `vault/_graph/{concept}` hub instead (Step 5). Cartographer never authors branch-to-branch `Related:` links across subtrees.

For each approved (validated) **intra-subtree** link pair (source → target):

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

### 5. Update or create `_graph/` concept hubs

This is **the** mechanism for cross-subtree connections (not direct `Related:` links). For every approved link pair whose source and target live in **different subtrees** — and for any cross-cutting theme that surfaces across two or more subtrees — record the relationship in the relevant `vault/_graph/{concept}.md` concept hub, with a rationale. `_graph/` is the semantic concept layer and the single home for cross-tree relationships.

**Concept-node schema (create):**

```markdown
---
note_type: concept
concept: <slug>
aliases: [synonyms a searcher would use]
tags: [knowledge, graph, concept/<slug>]
related_concepts: [other hub slugs]
---

# {Concept}

**What it is.** {2–3 sentence definition.}

**Why it matters.** {what the reader gains from it.}

## Related concepts
- [[_graph/{other-concept}|Other Concept]] — why the two concepts relate.

## Evidence & supporting material
### {Role heading: How it works / Positioning / Domain application / …}
- [[{subtree}/{note-slug}|Note Title]] — one-line rationale.
```

**Update format:** add the note under the right role heading with a rationale, and add cross-concept edges under `## Related concepts`. **Every link MUST carry a `— rationale`** (a bare link is a defect — `vault-lint` check C10). Do not remove or reorder existing entries.

One hub per concept; kebab-case slugs (e.g. `vault/_graph/concept-name.md`). See `vault/_graph/index.md` for the full schema and the maintained hub list.

---

### 6. Report changes

After all writes complete, report:

| Category | Count | Details |
|---|---|---|
| Notes modified | N | list of paths |
| Links added | N | list of (source → target) pairs |
| Frontmatter fields added | N | list of notes where `related:` was added or extended |
| `_graph/` concept hubs created | N | list of new hub files |
| `_graph/` concept hubs updated | N | list of updated hub files |

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
