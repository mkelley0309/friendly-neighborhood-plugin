# Action: Harvest

Read verified sources, classify content by concept-domain subtree, write candidate notes to staging, and invoke Peer Reviewer for each candidate before vault admission.

## When to run

- After Scout has verified sources and updated queue signal status to `processing`
- User says "harvest from sources", "stage candidates", "run Harvester"
- A queue signal exists at `knowledge/distillers/queue/` with `status: processing`

Do not run before Scout. Scout confirms source availability and transitions the signal; Harvester depends on that confirmation.

---

## File-Path Gate

| Direction | Allowed paths |
|---|---|
| Read | `knowledge/sources/verified/`, `knowledge/perspective/`, `knowledge/distillers/queue/` |
| Write | `knowledge/distillers/staging/`; `knowledge/perspective/{domain}/{note}.md` (auto-routed first-party content only) |

**Never write to `vault/` directly.** Never modify `sources/`.

---

## Steps

### 1. Read the queue signal

Read the queue signal file that Scout set to `processing`:

```
knowledge/distillers/queue/{signal-file}.md
```

Extract:
- `signal` — type of work (`research-complete` or `sync-complete`)
- `workstream` — originating workstream name (if research-driven)
- `research_path` — path to the workstream's `research.md` (if research-driven; null for sync-driven)
- `target_vault_subtrees` — list of vault subtrees this source maps to
- Source slug — derive from signal filename or body context

### 2. Identify and read the verified source

Locate the verified source for this signal. Verified sources live at:

```
knowledge/sources/verified/{source-slug}.md
```

Read the full source file. This is the only reading input — do not read from `sources/` subfolders directly.

If the signal is research-driven (`research_path` is non-null), also read the referenced `research.md` to understand context and priority hints.

**Distiller-to-vault mapping:** Source-to-subtree mappings are defined per-source in that source's `recipe.md`. Read the relevant recipe at `knowledge/distillers/{source-slug}/recipe.md` to determine the correct target subtree(s) for each source slug.

### 2b. Classify each chunk — source vs. first-party

Before producing any vault candidate, classify what you are reading (opinion-vs-source heuristic in `knowledge/AGENTS.md`).

A chunk is **first-party** when it shows: first-person experiential framing, evaluative/interpretive judgment, named-persona narratives or before-state rituals, positioning judgment or counter-claim landmines, or field intelligence the user gathered and interpreted. Most `sources/` content is authoritative, but interpretive commentary can be embedded — especially in field-intel-style sources.

For each first-party chunk:
1. Auto-route it to `knowledge/perspective/{domain}/{note}.md` using the perspective input schema:

   ```yaml
   ---
   note_type: perspective
   domain: <pick from content topic; reuse an existing perspective/{domain} folder when one fits>
   captured_at: <today's ISO date>
   origin: "harvested-from: <source path>"
   tags: [perspective/{domain}, ...]
   ---
   ```
2. Do **not** stage it as a vault candidate here — perspective content reaches the vault through the perspective distiller, not the source harvest flow.
3. Record it for the report (Step `Report Format` → "Auto-routed to perspective").

If a single chunk mixes a verifiable fact and the user's read of it, split: the fact continues as a vault candidate; the interpretation routes to perspective.

Everything that is **not** first-party continues to Step 3.

### 3. Identify concepts worth capturing

Scan the remaining (authoritative) source content. A concept is worth capturing when it:

- Encodes a **complete, self-contained idea** that can be understood independently
- Has **vault-generic value** — useful beyond the immediate source context
- Maps to a **single concept** (not a bundle of multiple independent ideas)
- Would be worth linking to from other vault notes

Skip: navigation elements, table-of-contents pages, stub content without substance, and exact duplicates of already-staged candidates in this session.

### 4. Produce a candidate note per concept

For each qualifying concept:

**Slug:** `kebab-case-concept-name` — matches the note's H1 title (lowercase, hyphens, no special characters)

**Frontmatter (required — all six fields):**

```yaml
---
note_type: vault-note
source_path: <relative path under sources/ — e.g. sources/{source-slug}/section/overview.md>
source_url: <original URL from source frontmatter>
synced_at: <ISO date copied from source frontmatter synced_at field>
distilled_at: <today's ISO date — YYYY-MM-DD>
tags: [vendor/<slug>, ...]
confidence: medium
---
```

- `confidence` is always `medium` for Harvester-produced candidates (never upgrade to `high` — that is Distiller privilege)
- `confidence` must be `low` for stubs (<150 words)
- Tags must include at least one `vendor/<slug>` tag matching the source
- Add semantic tags as appropriate

**Body requirements:**
- Write the note as if it were already in the vault — a reader landing here cold must understand the concept without reading surrounding notes
- Include a `## Related` section at the bottom with at least one `[[wiki-link]]` to a related concept (required for Peer Reviewer ADMIT)
- Use Obsidian wiki-links (`[[slug|Display Text]]`) for intra-vault references
- Use markdown links only for URLs outside the vault

**Example candidate structure:**

```markdown
---
note_type: vault-note
source_path: sources/{source-slug}/section/concept-overview.md
source_url: https://example.com/section/concept-overview
synced_at: 2026-05-10
distilled_at: 2026-05-12
tags: [vendor/{source-slug}, domain-knowledge]
confidence: medium
---

# Concept Name

{Concept explanation — complete, self-contained, ≥150 words for non-stub.}

## Related

- [[related-concept|Related Concept]] — parent concept
- [[downstream-dependency|Downstream Dependency]] — downstream dependency
```

### 5. Write each candidate to staging

Write each candidate to:

```
knowledge/distillers/staging/{slug}.md
```

Do not write to any other path. Do not create subdirectories inside `staging/`.

After writing all candidates for the source, proceed immediately to Step 6.

### 6. Invoke Peer Reviewer subagent for each candidate

Invoke a Peer Reviewer subagent for **each candidate individually**. Use the verbatim briefing below.

---

## Peer Reviewer Briefing

> Use this block verbatim as the subagent prompt. Replace `{slug}` with the actual candidate slug.

```
You are Peer Reviewer. Your job is admission gating for a vault candidate in staging.

Read the candidate at: knowledge/distillers/staging/{slug}.md

Apply these checks in order:

1. SEMANTIC DENSITY
   Does the note encode a single complete concept? Count the word count of the body (excluding frontmatter).
   - If <150 words AND confidence is not `low`: downgrade confidence to `low` in your review annotation. Do not auto-REJECT for word count alone — a focused stub at confidence:low may still ADMIT.
   - If <150 words AND confidence is already `low`: proceed normally.

2. SINGLE-CONCEPT RULE
   Does the note cover exactly one concept? A concept is distinct if it can be linked to, searched for, and understood in isolation.
   - If the note bundles two or more independent concepts: REJECT. In the rationale, name each concept and provide split instructions — one note per concept, linking to each other via [[wiki-link]] in ## Related.

3. OUTBOUND LINKS
   Count `[[` occurrences in the note body (not frontmatter).
   - If 0: REJECT. Reason: "isolated node — add at least one [[wiki-link]] in ## Related before admission."
   - If 1: ADMIT (if other checks pass) with annotation: "Only one outbound link. Recommend adding additional links during Cartographer pass."
   - If ≥2: no annotation needed.

4. DEDUP CHECK
   a. Slug conflict: Does `vault/{target-path}/{slug}.md` already exist?
      - If yes: REJECT. Reason: exact duplicate — slug already present in vault at that path.
   b. Semantic conflict: Does a note in the target subtree cover the same concept under a different slug?
      - If yes: MERGE. Provide the target note path and a merge instruction describing which content to integrate.
      - Use concept title similarity as the signal — if the existing note's H1 maps to the same concept, that is a semantic conflict.

5. CONFIDENCE FIELD
   Verify `confidence` is present in frontmatter.
   - Harvester-produced notes must be `medium` (or `low` for stubs). If missing: REJECT with reason "confidence field absent".
   - If confidence is `high`: downgrade to `medium` and note this in the review — Harvester is not permitted to set high confidence.

Determine the target vault path from the source recipe: read `knowledge/distillers/{source-slug}/recipe.md` to find the correct source→subtree mapping for this candidate.

Write your decision to: knowledge/distillers/staging/{slug}-review.md

Use this exact frontmatter:

---
note_type: peer-review
candidate: staging/{slug}.md
decision: ADMIT | REJECT | MERGE
reviewed_at: <ISO datetime — YYYY-MM-DDTHH:MM:SS>
---

Body format:

**Decision:** ADMIT / REJECT / MERGE

**Rationale:** [Explanation of decision. Reference the specific check(s) that determined the outcome.]

**Target vault path:** [For ADMIT: full target path, e.g. vault/domain-knowledge/concept-name.md. For MERGE: path of existing note to merge into. For REJECT: omit.]

**Action required:** [For ADMIT: "Orchestrating agent moves staging/{slug}.md to {target path}; delete both staging files." For REJECT/MERGE: "Staging files remain. User resolves."]

You may NOT write to vault/ directly. The move instruction is for the orchestrating agent — you only write the review file.
```

---

### 7. Process Peer Reviewer decisions

After each Peer Reviewer subagent completes, read the review file at `knowledge/distillers/staging/{slug}-review.md`.

**On ADMIT:**
1. Move `knowledge/distillers/staging/{slug}.md` to `vault/{target-path}/{slug}.md` (path specified in review)
2. Delete `knowledge/distillers/staging/{slug}.md`
3. Delete `knowledge/distillers/staging/{slug}-review.md`
4. Record as admitted in the session report

**On REJECT:**
1. Leave `knowledge/distillers/staging/{slug}.md` in place
2. Leave `knowledge/distillers/staging/{slug}-review.md` in place
3. Record as rejected in the session report with the rationale summary

**On MERGE:**
1. Leave both staging files in place
2. Record as pending merge in the session report with the target note path
3. Surface the merge instruction to the user — do not perform the merge automatically

### 8. Update queue signal status

After all candidates have been processed (admitted, rejected, or queued for merge), update the queue signal file:

```yaml
status: done
```

Update the field in-place. Do not alter other fields or the body.

---

## Report Format

After all candidates are processed, report:

```
Harvest complete — {source-slug}

Sources read: {source file path}
Auto-routed to perspective: {N} — {list of perspective/{domain}/{note}.md, with one-line reason each, or "none"}
Candidates staged: {N}
  Admitted to vault: {N} — {list of vault paths}
  Rejected (in staging): {N} — {list of slugs with one-line rationale each}
  Pending merge (in staging): {N} — {list of slugs with target note path each}

Queue signal: {signal-file}.md → status: done
```

If any first-party content was auto-routed to perspective, note that it is now distillable input — recommend `Distill perspective/{domain}` as a follow-up.

If no candidates were identified from the source, state that explicitly and explain why (e.g. "Source contains only navigation stubs; no concept-dense content found").

---

## Notes

- Harvester never upgrades confidence. Only Peer Reviewer can downgrade it.
- If a candidate fails on multiple Peer Reviewer checks, the review lists all failures — do not stop at the first.
- If staging already contains a `{slug}.md` from a previous incomplete session, read it before writing — do not blindly overwrite.
- The Peer Reviewer is always invoked per-candidate, never in batch. Each subagent reads one candidate and writes one review file.
- Scout must have set the queue signal to `processing` before Harvest runs. If the signal is still `pending`, run Scout first.
