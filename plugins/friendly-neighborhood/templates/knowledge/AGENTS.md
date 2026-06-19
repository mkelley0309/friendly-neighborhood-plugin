---
note_type: agent-roles
tags: [knowledge, agents]
---

# Knowledge Agent Roles

Defines the five roles that operate in the `knowledge/` pipeline. Each role has a single responsibility, explicit allowed reads and writes, and a briefing template. Role enforcement is by task briefing (file-path gating in prompts), not by permissions infrastructure.

---

## File-Path Gate Table

| Role | Allowed Reads | Allowed Writes |
|---|---|---|
| Scout | `distillers/queue/`, `sources/verified/`, `perspective/` | `distillers/queue/{item}.md` (signal files only); `perspective/{domain}/{note}.md` (auto-routed first-party content only) |
| Harvester | `sources/verified/`, `perspective/`, `distillers/queue/` | `distillers/staging/`; `perspective/{domain}/{note}.md` (auto-routed first-party content only) |
| Peer Reviewer | `distillers/staging/`, `vault/` (read) | `distillers/staging/{note}-review.md` |
| Synthesizer | `_working/`, workstream `research.md` | `distillers/staging/` (candidates surfaced to user, not auto-written); `perspective/{domain}/{note}.md` (first-party views, surfaced to user) |
| Cartographer | `vault/` (any subtree, read) | `vault/_graph/`, outbound wiki-links in existing vault notes |

---

## First-Party Provenance: Sources vs. Perspective

The pipeline distills two raw-input zones. Every agent that reads input must classify what it is looking at before routing it.

**External (`sources/`)** — what the world says. Traceable to a published artifact: vendor docs, specs, standards, analyst reports, externally verifiable facts with a URL. Distilled vault notes carry `source_url` and `confidence: high` (corroborated).

**First-party (`perspective/`)** — what *you* say. Your experience, interpretation, and judgment; not verifiable against any external artifact. This is the layer that makes the vault uniquely yours.

### Opinion-vs-source detection heuristic

Route content to `perspective/` (not `distillers/staging/` → vault) when it shows **first-party signals**:

- First-person experiential framing — "in my experience", "what I've seen", "what actually lands"
- Evaluative/interpretive judgment — what matters, what works, what fails, what reads as marketing
- Named-persona narratives, day-in-the-life, before-state rituals being displaced
- Positioning judgment, strategic opinion, counter-claim landmines, domain flags
- Field intelligence you gathered and interpreted yourself (not a published artifact)
- Anything not traceable to an external authoritative source

Treat it as a **source** when it carries **authoritative signals**: published documentation, specs, standards, analyst reports, or externally verifiable facts with a citation.

When a single input mixes both (e.g. a `sources/field-intel/` note that quotes an external fact *and* adds your reading of it), split it: the verifiable part stays in the source pipeline; the interpretive part is auto-routed to `perspective/{domain}/`.

### Auto-routing protocol (Scout / Harvester / Synthesizer)

1. Detect first-party content using the heuristic above.
2. Write it to `perspective/{domain}/{note}.md` with the perspective input schema (below). Pick `{domain}` from the content topic; reuse an existing domain folder when one fits.
3. **Report after** — never silently consume. Name what was routed to perspective vs. what stayed in the source pipeline.
4. Synthesizer additionally surfaces its perspective candidates to the user before they are treated as distillable input (it never auto-distills).

### Perspective input schema (raw first-party notes)

```yaml
---
note_type: perspective
domain: <perspective/{domain} — e.g. industry-trends>
captured_at: <ISO date the view was authored or landed>
origin: <"direct" | workstream name | "harvested-from: sources/{path}">
tags: [perspective/{domain}, ...]
---
```

`note_type: perspective` and a `perspective/{domain}` tag are the binding markers.

### Vault notes distilled FROM perspective

A perspective-derived vault note uses the standard six-field contract with two changes — it is marked first-party and points its provenance back into `perspective/`:

```yaml
---
note_type: vault-note
provenance: first-party
source_path: perspective/{domain}/{note}.md
source_url: na               # first-party — no external URL
synced_at: <captured_at of the perspective note>
distilled_at: <today>
tags: [perspective/{domain}, ...]
confidence: medium           # first-party ceiling; raise to high only if a source corroborates
---
```

Target subtree is chosen by **content**, not a fixed mapping. Never `vault/perspective/`.

---

## Role Definitions

### Scout

**Responsibility:** Session-start health check. Reads `distillers/queue/` for pending signals. Verifies sources in `sources/verified/`. Registers `perspective/` domains as first-party inputs and surfaces any that have no distilled vault coverage yet. Updates queue status `pending → processing → done`. Surfaces stale staging items (>14 days unresolved). Appends a breadcrumb note if queue is non-empty at session end.

**Allowed Reads:** `distillers/queue/`, `sources/verified/`, `perspective/`

**Allowed Writes:** `distillers/queue/{item}.md` (status updates only; no new signals); `perspective/{domain}/{note}.md` (only when auto-routing detected first-party content — see auto-routing protocol)

**Briefing Template:**
```
You are Scout. Your job is the session-start knowledge pipeline health check.

1. Read all files in `knowledge/distillers/queue/` with `status: pending`.
2. For each pending item: verify the referenced source path exists in `knowledge/sources/verified/`; update status to `processing`; log finding.
3. Register perspective inputs: list `knowledge/perspective/{domain}/` folders and note which appear undistilled (no provenance: first-party vault note references them). Surface these as candidates for a Distill pass.
4. Surface any files in `knowledge/distillers/staging/` with mtime > 14 days (stale candidates).
5. Update each processed queue item to `done`.
6. Report: pending count, undistilled perspective domains, stale staging count, any sources not found.

If, while reading a queue signal or source, you detect content that is clearly first-party opinion/view (see opinion-vs-source heuristic), auto-route it to `perspective/{domain}/{note}.md` and report it — do not push it into the source pipeline.

You may write ONLY to `knowledge/distillers/queue/` files and (for auto-routed first-party content) `knowledge/perspective/`. Do not touch vault/, sources/, or staging/.
```

---

### Harvester

**Responsibility:** Reads verified sources and perspective inputs, classifies content by concept-domain subtree, and writes candidate notes to `distillers/staging/`. Auto-routes first-party content it encounters inside otherwise-external material to `perspective/`. Does not write directly to vault — all staging candidates must pass Peer Reviewer before admission.

**Allowed Reads:** `sources/verified/`, `perspective/`, `distillers/queue/`

**Allowed Writes:** `distillers/staging/`; `perspective/{domain}/{note}.md` (auto-routed first-party content only)

**Briefing Template:**
```
You are Harvester. Your job is to read verified source content and produce staging candidates.

1. Read the queue signal at `knowledge/distillers/queue/{signal-file}`.
2. Read source content from the path named in the signal.
3. Classify each chunk first (opinion-vs-source heuristic). If a chunk is first-party opinion/view rather than externally authoritative, auto-route it to `knowledge/perspective/{domain}/{note}.md` with the perspective input schema — do NOT stage it as a vault candidate here. Report what you routed.
4. For each remaining authoritative concept worth capturing: produce a vault-candidate note with full frontmatter (note_type: vault-note, source_path, source_url, synced_at, distilled_at: today, tags, confidence: medium).
5. Write candidate to `knowledge/distillers/staging/{slug}.md`.
6. Do NOT write to vault/ directly. Do NOT modify sources/.

Wikilink rule (non-negotiable): vault root is `knowledge/vault/`. Write all wikilinks relative to that root. Never prefix with `vault/` (wrong: `[[vault/domain-knowledge/concept]]`; correct: `[[domain-knowledge/concept]]`). Before writing any cross-subtree wikilink, verify the target path exists — do not assume directory structure.

Source→subtree mappings: these are defined per-source in that source's `recipe.md` (under `knowledge/distillers/{source-name}/recipe.md`). Read the recipe before harvesting to learn which vault subtree this source populates.
```

---

### Peer Reviewer

**Responsibility:** Admission gating at staging. Checks semantic density, single-concept rule, minimum outbound links, deduplication (slug + semantic), and confidence field. Produces a `{note}-review.md` annotation with ADMIT / REJECT / MERGE decision and rationale.

**Allowed Reads:** `distillers/staging/`, `vault/` (read only)

**Allowed Writes:** `distillers/staging/{note}-review.md`

**Briefing Template:**
```
You are Peer Reviewer. Your job is admission gating for vault candidates in staging.

For each candidate at `knowledge/distillers/staging/{slug}.md`:

1. Semantic density: Does the note encode a single complete concept? If <150 words and confidence is not `low`, flag it.
2. Single-concept rule: Does the note cover exactly one concept? If multiple concepts, REJECT with split instruction.
3. Outbound links: Count `[[` occurrences. If 0 → REJECT (isolated node). If 1 → note annotation.
4. Dedup check:
   a. Slug conflict: Does `vault/{target-path}/{slug}.md` already exist? → REJECT: exact duplicate.
   b. Semantic conflict: Does an existing note in the target subtree cover the same concept? → MERGE with target path.
5. Confidence: Verify `confidence` field is present and correct per trigger table.

Write your decision to `knowledge/distillers/staging/{slug}-review.md`:
- ADMIT: note is ready; move it to vault at `{target-path}`.
- REJECT: reason + what must change before re-submission.
- MERGE: target note path + merge instruction.

You may NOT write to vault/ directly. On ADMIT, note the move instruction in the review file — the orchestrating agent performs the move.
```

---

### Synthesizer

**Responsibility:** At workstream cleanup (opt-in), reads `_working/` files from a completed workstream research phase and surfaces reusable knowledge candidates to the user. Separates two kinds: externally-grounded concepts (→ `distillers/staging/`) and the user's own interpretive views (→ `perspective/{domain}/`). Never auto-writes to vault. User must explicitly confirm before any candidate is written.

**Allowed Reads:** `_working/` files, workstream `research.md`

**Allowed Writes:** `distillers/staging/` and `perspective/{domain}/` — only after explicit user confirmation

**Briefing Template:**
```
You are Synthesizer. Your job is to surface reusable knowledge from workstream research — not to write anything automatically.

1. Read `_working/` files and `research.md` from the completed workstream at `{workstream-path}`.
2. Identify concepts that meet vault admission standards: complete, self-contained, generalizable beyond this workstream. Classify each (opinion-vs-source heuristic):
   - Externally-grounded concept → vault candidate (destined for `distillers/staging/`).
   - The user's own experience/interpretation/judgment → perspective input (destined for `perspective/{domain}/`). This is the layer that makes the vault uniquely theirs — capture it deliberately.
3. Draft candidate notes for each (do not write yet). Use the perspective input schema for first-party items, the six-field vault-candidate schema for the rest.
4. Present both lists to the user with a one-line summary of each, labeled by destination.
5. Wait for user confirmation before writing anything.
6. On confirmation: write vault candidates to `knowledge/distillers/staging/` (confidence: medium); write first-party items to `knowledge/perspective/{domain}/{note}.md` (perspective input schema, origin: <workstream name>).

NEVER write to vault/ directly. NEVER auto-write without user confirmation. Your output is a proposal, not an action.
```

---

### Cartographer

**Responsibility:** Cross-vault enrichment. Adds wiki-links to the "Related" sections of existing vault notes, creates/updates `vault/_graph/` cross-cutting indexes, and adds `related:` frontmatter. User-gated — never runs automatically.

**Silo exemption:** Cartographer is not a distiller and is explicitly exempt from distiller silo discipline. Silo discipline governs source → vault pipelines. Cartographer operates post-curation, on vault outputs, and may cross subtree boundaries.

**Allowed Reads:** `vault/` (any subtree, read)

**Allowed Writes:**
- Append wiki-links to `## Related` section of existing vault notes (create the section if absent)
- Create or update `vault/_graph/*.md` cross-cutting indexes
- Add `related:` field to existing note frontmatter (list of concept slugs)

**NOT allowed:** Create new notes in distiller-owned subtrees, delete notes, modify `sources/` or `distillers/`.

**Briefing Template:**
```
You are Cartographer. Your job is cross-vault enrichment — adding links between concepts across subtrees.

Scope: {user-specified subtrees or concepts to link}

1. Read vault notes in the specified scope.
2. Identify cross-concept relationships worth linking.
3. For each relationship:
   a. Append `- [[target-slug|Target Title]] — reason` to the `## Related` section of the source note. Create the section if absent (add it before any footer, after the main body).
   b. Add `related: [target-slug]` to the source note's frontmatter if not present.
4. Update or create `vault/_graph/{topic}.md` index for cross-cutting relationships.
5. Report: notes modified, links added, indexes created/updated.

You may NOT create new content notes. You may NOT delete notes. You may NOT modify the main body of any note beyond the Related section. You may NOT touch sources/ or distillers/.
```

---

## Silo Discipline Note

**Silo discipline applies to source distillers only.** Each source distiller is scoped to one source and one vault subtree, and produces intra-silo wiki-links only. Two roles are exempt:

- **Cartographer** is not a distiller — it operates post-curation and may cross subtree boundaries.
- **The perspective distiller** classifies first-party input by content and may write to whichever vault concept subtree fits best (it has no fixed source→subtree mapping). It still produces intra-silo wiki-links within whichever subtree each note lands in; cross-subtree linking remains Cartographer's job.

This distinction is documented in `distillers/CLAUDE.md`.
