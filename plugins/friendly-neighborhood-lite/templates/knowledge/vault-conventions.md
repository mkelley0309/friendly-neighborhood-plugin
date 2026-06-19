---
note_type: conventions
tags: [knowledge, vault]
---

# Vault Conventions

> Scope: this document governs `knowledge/vault/` only. It lives under `knowledge/` because it's a knowledge-layer concern, not a workspace-wide one. Outside the vault (e.g. `control-plane/`, `projects/`), plain markdown with markdown-relative links is used. The `index.md` convention is shared.

---

## Vault Taxonomy

Top-level directory structure (generic starter set):

```
vault/
  domain-knowledge/  ← industry, regulatory, and domain context (not product-specific)
    {expandable — structure emerges from content}
  reference/         ← curated reference material: standards, specs, glossaries
    {expandable}
  _graph/            ← Cartographer cross-cutting indexes; never browsed directly
```

> **These are example subtrees — rename or add to fit your domain.**
> For example:
> - A GTM team might use `company/`, `product/`, `market-positioning/`
> - A research team might use `literature/`, `experiments/`, `concepts/`
> - A software team might use `architecture/`, `adr/`, `runbooks/`
>
> Subtrees marked `{expandable}` are extended at classification time, not pre-created.

Key rules:

- One subtree may be designated as the only place where exact-copy source material is admitted (e.g. `reference/`). All other subtrees require synthesis and semantic density.
- `_graph/` is Cartographer-owned. Human editors do not write here.

---

## Folder Notes: `index.md` per folder

Every meaningful folder in the vault has an `index.md` that:

- **Is the folder's entry point** — orientation, purpose, when to read it
- **Lists child notes** as wiki-links with one-line summaries
- **Resolves as a Folder Note** in Obsidian via the Folder Notes plugin (the folder itself becomes clickable and opens this file)

`index.md` is the folder entry-point convention. Why:
- Obsidian-native (Mintlify/Nextra/Docusaurus also standardized on `index.md`)
- Unambiguous semantics: "this is the orientation for this folder"
- No collision with Claude Code's `CLAUDE.md` (those have distinct jobs — `CLAUDE.md` is AI-only; `index.md` is human + AI)

### Hub `index.md` template

```markdown
---
note_type: hub        # or: documentation-hub, section-hub, etc.
tags: [...]
---

# {Folder / Section Title}

{One paragraph: what this folder covers, when to read it.}

## Children

- [[{child-slug}|{Title}]] — {one-line summary}
- ...

## Related

- {links to parent hubs, related vault areas, or external references}
```

---

## Frontmatter

Every vault note carries frontmatter. Minimum fields:

```yaml
note_type: <hub|documentation|decision|concept|reference|...>
tags: [<at-least-one>]
```

Type-specific fields are defined per `note_type` — see the relevant distiller recipe (for derived notes) or section hub (for hand-written notes).

### Common `note_type` values

| `note_type` | Purpose |
|---|---|
| `hub` | Folder-level orientation (lives in `index.md`) |
| `documentation-hub` | Hub for a curated documentation section |
| `documentation` | A curated documentation page (from a source) |
| `vendor-documentation` | Raw vendor doc (only valid in `sources/` — if it appears in `vault/`, it's been curated and should be `documentation`) |
| `perspective` | Raw first-party note (only valid in `perspective/` — if it appears in `vault/`, it's been distilled and should be `vault-note` with `provenance: first-party`) |
| `decision` | A captured decision with rationale |
| `concept` | A domain concept or glossary entry |
| `reference` | External-facing reference material |
### Provenance fields (for distilled notes)

Notes curated from `knowledge/sources/` must track provenance:

```yaml
source_path: sources/{source-name}/{original rel path}.md
source_url: {original URL}
synced_at: YYYY-MM-DD       # copied from source frontmatter
distilled_at: YYYY-MM-DD    # when this curation was written
```

Notes distilled from first-party `knowledge/perspective/` add `provenance: first-party`, point `source_path` into `perspective/`, set `source_url: na`, and ceiling at `confidence: medium`:

```yaml
provenance: first-party
source_path: perspective/{domain}/{note}.md
source_url: na
synced_at: YYYY-MM-DD       # captured_at of the perspective note
distilled_at: YYYY-MM-DD
confidence: medium
```

---

## Semantic Density

A vault note must encode a complete, self-contained concept that can be understood without reading surrounding notes. A reader landing on any note cold should leave with a coherent understanding of the concept — not a fragment requiring cross-referencing to be meaningful.

Stub notes (<150 words) are permitted only with `confidence: low`. Stubs are placeholders, not permanent states — they signal that a concept has been identified but not yet fully developed.

Notes produced by Distillers and Harvester are expected to meet density requirements before admission. The Peer Reviewer enforces this gate.

---

## Single-Concept Rule

One note per concept. A note that covers multiple distinct concepts must be split before admission.

A concept is distinct when it has an independent identity — it can be linked to, searched for, and understood in isolation. If removing one concept from a note would leave the other concept complete and coherent, they belong in separate notes.

Splitting guidance:
- Create a note per concept with its own slug and frontmatter.
- Link the split notes to each other via `[[...]]` in their `## Related` sections.
- Replace the original combined note with a disambiguation hub if both concepts share a common term, or delete it if it was redundant.

The Peer Reviewer rejects notes that bundle multiple independent concepts and provides split instructions.

---

## Minimum Outbound Links

Hard minimum: ≥1 outbound wiki-link (`[[...]]`) required for admission. Isolated nodes (0 outbound links) are rejected by the Peer Reviewer.

Recommended: ≥2 outbound links for non-stub notes (soft convention, not blocking).

**Enforcement:** Peer Reviewer counts `[[` occurrences in note body. If 0 → REJECT with reason "isolated node — add at least one wiki-link before admission." If 1 → ADMIT with annotation recommending additional links.

**Exception:** Exact-copy notes (e.g. in a designated reference subtree) may have 0 outbound links if the source contains no linkable concepts. Must be flagged `confidence: low` if isolated.

---

## Deduplication Policy

Peer Reviewer is responsible for dedup detection at staging.

Protocol:

1. Extract note slug and concept title from candidate.
2. Check `vault/` for slug conflict: if a file at the same path exists → REJECT: exact duplicate.
3. Check concept overlap: compare candidate title against existing note titles in target subtree. If title similarity is high (same concept, different phrasing) → MERGE: provide target path and merge instruction.
4. On ADMIT: note moves from staging to vault.
5. On REJECT/MERGE: note remains in staging with `{note}-review.md` annotation.

---

## Confidence Schema

Every vault note carries a `confidence` frontmatter field.

Allowed values: `high | medium | low`

Trigger table:

| Condition | Confidence |
|---|---|
| Distiller-produced from verified synced source (has `synced_at`) | `high` |
| Harvester-produced, source URL verified (has `source_url` + `synced_at`) | `medium` |
| Stub note (<150 words) | `low` |
| No `synced_at` (unverified source) | `low` |
| Peer Reviewer flags uncertainty explicitly | `low` |

Defaults: Distillers default to `high`. Harvester defaults to `medium`. Stubs must be `low`. Peer Reviewer may downgrade but may not upgrade.

---

## Related Section Convention

Every non-hub vault note should have a `## Related` section at the bottom (before any footers). This is where Cartographer appends wiki-links. Format:

```markdown
## Related

- [[concept-slug|Concept Title]] — one-line reason for the link
```

Cartographer may create this section if absent. Human authors should include it when writing notes. The section must appear after the main body — never interrupt the content.

---

## Writing into the Vault (Admission Gate)

The pipeline is the only sanctioned path into the vault:

1. **Distillation** — via the `web-archive` skill, reading from `knowledge/sources/` or `knowledge/perspective/`. All distiller-produced notes must pass Peer Reviewer admission before writing. Perspective-distilled notes are marked `provenance: first-party` and land at the content-appropriate concept subtree (never `vault/perspective/`).
2. **Harvester → Peer Reviewer** — Harvester stages candidates; Peer Reviewer applies admission criteria (semantic density, single-concept, outbound links, dedup) before ADMIT. First-party content Harvester encounters is auto-routed to `perspective/` instead of staged.
3. **Hand-authoring** — direct edits via Obsidian or filesystem tools. Hand-authored notes are exempt from the queue but must still comply with all conventions in this document. Peer Review is strongly recommended.

Nothing else writes to the vault. Sync scripts never write here — they write to `knowledge/sources/` and stop. `perspective/` is raw input, not vault — it is retained, never auto-mirrored into the vault.

---

## Wiki-links, not markdown links

Inside the vault, use Obsidian wiki-links: `[[note-name]]` or `[[note-name|Display Text]]`.

- Wiki-links are Obsidian's first-class citizen — graph view, backlinks, and rename-safety depend on them
- Use markdown links only when pointing **outside** the vault (to `control-plane/`, `projects/`, external URLs)

---

## Confidentiality

- Internal codenames and sensitive terms **never leave the vault** in external-facing work
- Tag sensitive content with `sensitivity/internal` or `sensitivity/confidential` so filters can exclude it
- Sources folder (`knowledge/sources/`) has no confidentiality filtering — it mirrors upstream verbatim. Confidentiality enforcement happens at curation time.

---

## Tags

- Use hierarchical tags: `domain/{name}`, `vendor/{name}`, `workstream/{name}`, `objective/{name}`
- Leaf-level descriptive tags also fine: `api`, `onboarding`, `troubleshooting`
- Avoid tag sprawl — prefer reusing existing tags over coining new ones

---

## Path and filename conventions

- `kebab-case.md` for filenames
- Folders also kebab-case
- Filename stem matches the H1 title (case-insensitive)
- Never embed spaces or special characters in vault paths

---

## What does NOT live in the vault

- Raw vendor documentation → `knowledge/sources/`
- Scripts, code, executable artifacts → `projects/` or `tools/`
- Workstream scratch → `control-plane/workstreams/{name}/_working/`
- Workstream logs → `control-plane/workstreams/_log/` (retained, but outside the vault)
- Objectives → `control-plane/objectives/{name}/index.md` (outside the vault by design — control-plane state, not knowledge)

The sanctioned distillation path into the vault is via the `web-archive` skill.

---

## No breadcrumb footers

Don't embed breadcrumb footers — Obsidian's backlinks panel and graph handle upward navigation. If a note needs an explicit "up one level" link, use the frontmatter `parent:` field or a one-line `> Part of: [[parent-hub]]` callout at the top.
