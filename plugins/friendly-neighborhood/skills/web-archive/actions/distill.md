# Action: Distill

Recipe-driven curation of a named source into the vault. Reads the distiller recipe and source content, delegates per-section curation to Sonnet subagents, and routes every candidate through Peer Reviewer admission before any vault write.

## When to run

- User requests distillation of a named source: "distill [source name]", "curate [source] into the vault", "update vault from [source]"
- User requests distillation of first-party perspective: "distill perspective", "distill perspective/[domain]", "pull my perspective notes into the vault"
- Post-sync: after a source-sync run updates `knowledge/sources/`, distill to propagate changes to vault
- A queue signal exists with `status: processing` pointing at a source with an existing distiller recipe

Do not run before Scout has verified the source. If the queue signal is still `pending`, run Scout first.

---

## Distiller Routing Table

Source-to-subtree mappings are defined per-source in that source's `recipe.md`. To determine which recipe and vault subtree(s) to use for a given source:

1. Identify the source slug (e.g., the folder name under `knowledge/sources/` or what the user named)
2. Read the recipe at `knowledge/distillers/{source-slug}/recipe.md`
3. The recipe specifies the primary and secondary target vault subtrees

If the user names a source not present in `knowledge/distillers/`, stop and ask for clarification — do not invent a recipe path.

**Perspective is first-party input, not an external source.** When the target is `perspective` (or a specific `perspective/{domain}`), follow **Perspective Mode** below — it overrides Steps 2–3 (no manifest, no fixed target) and adjusts the frontmatter and Peer Review checks. All other steps (staging, per-candidate Peer Review, hub rebuilds, idempotency) are unchanged.

---

## File-Path Gate

| Direction | Allowed paths |
|---|---|
| Read | `knowledge/sources/{source-slug}/`, `knowledge/perspective/{domain}/`, `knowledge/distillers/{source-slug}/recipe.md`, `knowledge/distillers/perspective/recipe.md`, `knowledge/vault/{target-subtree}/` (existence checks only) |
| Write (staging) | `knowledge/distillers/staging/` |
| Write (vault) | `knowledge/vault/{target-subtree}/` — only via Peer Reviewer ADMIT |
| Write (review) | `knowledge/distillers/staging/{slug}-review.md` (Peer Reviewer subagent only) |

**Never write to `sources/` or `perspective/`. Never write directly to `vault/` — all vault writes must follow an explicit Peer Reviewer ADMIT decision.**

---

## Perspective Mode (first-party input)

Triggered when the target is `perspective` or `perspective/{domain}`. The perspective distiller treats `knowledge/perspective/` exactly like a source — raw input, light Peer Review, distilled into the vault — with these overrides. Read `knowledge/distillers/perspective/recipe.md` first.

**Overrides Step 2 (manifest):** Perspective has no `_manifest.md`. Instead, enumerate the input files directly:
- `perspective` → all `knowledge/perspective/{domain}/*.md` (skip `index.md`)
- `perspective/{domain}` → all `knowledge/perspective/{domain}/*.md` for that domain

**Overrides Step 3 (diff):** Each perspective note is often multi-concept (personas, before-state, interpretive notes, domain flags, counter-claim landmines). Treat each standalone **section** as a candidate concept; split per the single-concept rule. Idempotency: skip a section if a vault note with matching `provenance: first-party` and `source_path` exists and its `distilled_at` ≥ the perspective note's `captured_at`.

**Overrides target selection:** There is no fixed source→subtree mapping. Classify each candidate by content:
- Persona / day-in-the-life / before-state / practitioner pain → `vault/domain-knowledge/`
- Positioning judgment / counter-claim landmines / what-lands-wrong → `vault/market-positioning/`
- Capability interpretation / product-shaped views → `vault/reference/`
- Ambiguous → choose the subtree with the most semantically-adjacent notes; if genuinely unclear, stage and ask the user. **Never** `vault/perspective/`.

**Overrides frontmatter** (curation subagents emit this instead of the source schema):
```yaml
---
note_type: vault-note
provenance: first-party
source_path: perspective/{domain}/{note}.md
source_url: na
synced_at: <captured_at copied from the perspective note>
distilled_at: {today}
tags: [perspective/{domain}, ...]
confidence: medium
---
```

**Preserve voice:** Do not sand first-party judgment into neutral source prose — the interpretive stance is the value. Drop only workstream-specific scaffolding (links to a specific drill-in or `research-{module}.md`).

**Peer Review additions** (state these in the per-candidate briefing): require `provenance: first-party` and a `source_path` under `perspective/` — REJECT if absent (a first-party note without provenance is indistinguishable from source content). Confidence ceilings at `medium`; downgrade `high` unless an external source corroborates. On semantic dedup against an existing source-distilled note, MERGE but keep the first-party interpretive layer.

The perspective input note is **retained** after distillation — never delete or modify it.

---

## Steps

### 1. Read the distiller recipe

Read the recipe file for the target source:

```
knowledge/distillers/{source-slug}/recipe.md
```

The recipe is the contract for this distiller. Extract:

- Source path (where raw pages live under `knowledge/sources/`)
- Target vault path(s) and section mapping
- What distillation adds (wiki-links, hubs, frontmatter normalization)
- What distillation drops or summarizes
- Index hub template
- Any run mode instructions (full / delta / hub-only)

If no recipe exists for the named source, stop and report: "No recipe found at `knowledge/distillers/{source-slug}/recipe.md`. Add a recipe before running Distill."

### 2. Read the source manifest

Read the source manifest to determine the full scope of available pages:

```
knowledge/sources/{source-slug}/_manifest.md
```

The manifest lists every page currently mirrored from upstream. Extract:
- All source page paths
- `synced_at` timestamps per page (used for idempotency check in Step 3)
- Total page count

### 3. Diff — determine what to curate

For each source page in the manifest:

**Skip if** the corresponding vault note already exists AND its `distilled_at` date is newer than or equal to the source page's `synced_at` date. This is the idempotency guard — re-running against unchanged source is a no-op for those pages.

**Include if** any of the following:
- No corresponding vault note exists at the target path
- Vault note exists but `distilled_at` is older than source `synced_at` (source updated since last distillation)
- Run mode is `full` (explicit user request for full rebuild)

Map each included source page to its target vault path using the recipe's mapping strategy. Group included pages by recipe section.

If the diff produces zero pages to curate, report "Distill: no-op — all vault notes are current with source" and stop.

### 4. Delegate curation to Sonnet subagents

For each recipe section with pages to curate, dispatch a Sonnet subagent. Run sections in parallel where the recipe confirms sections are independent (most distillers: all sections are parallel-safe).

Batch no more than 3–4 source pages per subagent. If a section has more pages than fit in one batch, dispatch multiple subagents for that section sequentially (preserve order for hub coherence).

**Each subagent receives:**

```
You are a Distiller subagent for the knowledge pipeline.

Source: {source-slug}
Section: {section-name}
Pages to curate: {list of source page paths}
Target vault path: {target vault path for this section}

Recipe excerpt (mapping + what to add/drop):
{paste the relevant portion of recipe.md for this section}

Frontmatter schema — all 6 fields required on every output note:
---
note_type: vault-note
source_path: <relative path under sources/ — e.g. sources/{source-slug}/section/overview.md>
source_url: <original URL from source frontmatter>
synced_at: <ISO date copied from source page synced_at>
distilled_at: {today's ISO date — YYYY-MM-DD}
tags: [vendor/{source-slug}, ...]
confidence: high
---

Instructions:
- Produce one vault-ready note per source page.
- Each note must be self-contained: a reader landing cold must understand the concept.
- Include a ## Related section with at least one [[wiki-link]] to a related concept in the same section or subtree.
- Rewrite root-relative source links to Obsidian wiki-links.
- Wikilink rule: vault root is `knowledge/vault/`. Write links relative to that root — never include `vault/` as a prefix. Wrong: `[[vault/domain-knowledge/payments]]`. Correct: `[[domain-knowledge/payments]]`. Only link to paths you have confirmed exist; do not guess directory structure.
- Drop: navigation chrome, boilerplate headers, repeated fragments, stubs, deprecated pages.
- Return each note as a fenced markdown block labeled with its slug. Do not write files — return content only.
- Total output must be ≤2000 tokens.
```

Collect the returned note content from each subagent. Each returned note is one staging candidate.

### 5. Write candidates to staging

For each note returned by curation subagents, determine its slug:
- Slug = kebab-case of the H1 title (lowercase, hyphens, no special characters)
- Slug must be unique within this distill run

Write each candidate to:

```
knowledge/distillers/staging/{slug}.md
```

If a `{slug}.md` already exists in staging from a previous incomplete session, read it before writing — do not blindly overwrite. If the existing staging note has a newer `distilled_at` than what the subagent produced, keep the existing file.

Do not create subdirectories inside `staging/`. Do not write to vault at this step.

### 6. Invoke Peer Reviewer subagent for each candidate

Invoke one Peer Reviewer subagent per candidate, individually. Do not batch candidates into a single Peer Reviewer subagent. Run up to 4 Peer Reviewer subagents in parallel for throughput, but each subagent evaluates exactly one candidate.

---

## Peer Reviewer Briefing

Embed this block verbatim as the subagent prompt. Replace `{slug}` and `{target-path}` with actual values.

```
You are Peer Reviewer. Evaluate this vault candidate for admission.

Candidate: {slug}.md
Target vault path: {target-path}/{slug}.md

Checks:
1. Semantic density — does the note encode a single complete, self-contained concept? If <150 words and confidence is not `low`, flag it.
2. Single-concept rule — does the note cover exactly one concept? If multiple: REJECT with split instruction.
3. Outbound links — count `[[` occurrences in body. If 0: REJECT (isolated node). If 1: ADMIT with annotation.
4. Dedup:
   a. Slug conflict: does `vault/{target-path}/{slug}.md` already exist? → REJECT: exact duplicate.
   b. Semantic conflict: does an existing note in the target subtree cover the same concept? → MERGE.
5. Confidence — verify field is present and set correctly:
   - `high` if distiller-produced with verified synced source
   - `low` if stub or no synced_at

Write decision to `knowledge/distillers/staging/{slug}-review.md`:
---
note_type: peer-review
candidate: staging/{slug}.md
decision: ADMIT | REJECT | MERGE
reviewed_at: {ISO datetime}
---
Rationale + (on ADMIT) target vault path. You may NOT write to vault/.
```

---

### 7. Process Peer Reviewer decisions

After each Peer Reviewer subagent completes, read its review file at `knowledge/distillers/staging/{slug}-review.md`.

**On ADMIT:**
1. Move `knowledge/distillers/staging/{slug}.md` to `vault/{target-path}/{slug}.md` (exact path from review)
2. Delete `knowledge/distillers/staging/{slug}.md`
3. Delete `knowledge/distillers/staging/{slug}-review.md`
4. Record slug and vault path in the admitted list

**On REJECT:**
1. Leave `knowledge/distillers/staging/{slug}.md` in staging
2. Leave `knowledge/distillers/staging/{slug}-review.md` in staging
3. Record slug and one-line rationale in the rejected list

**On MERGE:**
1. Leave both staging files in staging
2. Record slug, target note path, and merge instruction in the pending-merge list
3. Surface the merge instruction to the user — do not perform the merge automatically

### 8. Rebuild index.md hubs in affected vault subtrees

After all candidates are processed, rebuild the `index.md` hub for each vault subtree that received admitted notes.

For each affected section folder:

1. Read all `.md` files in the section folder (excluding `index.md` itself)
2. Produce an updated `index.md` using the recipe's Index Hub Template
3. Write the updated `index.md` to `vault/{target-path}/{section}/index.md`

If the recipe specifies a top-level hub, rebuild it last after all section hubs are complete.

Do not rebuild hubs for sections where no notes were admitted in this run — those hubs are already current.

---

## Silo Discipline

Each distill run is scoped to exactly one source slug and that source's concept-domain subtree(s) per the recipe. Do not write to any other vault subtrees.

Wiki-links produced by curation subagents are intra-silo only — they may link to notes within the same concept-domain subtree. Cross-subtree links (e.g. a `vault/domain-knowledge/` note linking to `vault/reference/`) are never authored by Distill. Cross-subtree link enrichment is Cartographer's responsibility.

**Link-target validation (MANDATORY — prevents phantom nodes / wrong paths).** Before a curation subagent writes any `[[target]]` wiki-link (or a slug in `related:` frontmatter), it must verify the target resolves to an existing note with a Glob/Read check. Do NOT guess a sub-path (e.g. `…/topic/overview`) when the real note is the leaf (`…/topic`); for a short target, confirm exactly one note has that basename. If the target does not exist, do not write the link — point at the correct existing note or omit it. A wiki-link to a nonexistent path renders as a greyed phantom node and spawns a blank stub on click.

If a curation subagent returns a note that logically belongs in a different subtree than the recipe specifies, write it to staging and flag it in the report. Do not re-route it to an out-of-scope subtree — ask the user.

---

## Idempotency

- Pages where the vault note's `distilled_at` >= source `synced_at` are skipped (Step 3)
- Re-running Distill against an unchanged source produces zero new candidates and zero writes
- If staging already contains a `{slug}.md` from a previous incomplete run, read before writing (Step 5)
- Hub rebuilds are always idempotent — the hub reflects current vault state at the time of the run

---

## Invariants

- Never edit or delete any file under `knowledge/sources/` or `knowledge/perspective/`
- Never write directly to `vault/` — every vault write must follow an explicit Peer Reviewer ADMIT
- Every admitted note must carry all 6 required frontmatter fields (`note_type`, `source_path`, `source_url`, `synced_at`, `distilled_at`, `tags`) plus `confidence`. Source-distilled notes default to `confidence: high`; perspective-distilled notes add `provenance: first-party` and ceiling at `confidence: medium`
- Peer Reviewer is always invoked per-candidate, never in batch
- Curation subagents return content only — they do not write files
- Hub writes are the only vault writes not gated by Peer Review (hubs are structural, not curated content)

---

## Report Format

After all candidates are processed and hubs rebuilt, report:

```
Distill complete — {source-slug}

Source manifest: {N} pages total
Pages diffed: {N} (skipped {N} as current)
Pages curated: {N}

Candidates staged: {N}
  Admitted to vault: {N}
    {list of vault paths, one per line}
  Rejected (in staging): {N}
    {slug} — {one-line rationale}
    ...
  Pending merge (in staging): {N}
    {slug} → merge into {target note path}
    ...

Index hubs rebuilt: {N}
  {list of hub paths, one per line}
```

If a curation subagent returned a note flagged for re-routing (wrong subtree), list it separately under "Flagged for re-routing" with the subagent's rationale.

If the run was a no-op (all pages current), state: "Distill: no-op — {N} pages checked, all vault notes current."
