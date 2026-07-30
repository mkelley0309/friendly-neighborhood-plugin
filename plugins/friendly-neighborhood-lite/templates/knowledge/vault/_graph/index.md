---
note_type: vault-index
tags: [knowledge, graph]
---

# Vault Graph — Concept Layer

`_graph/` is the vault's **semantic concept layer**: the single home for cross-tree relationships and the substrate that concept/semantic search lands on. Each hub is a **concept node** (`note_type: concept`) capturing *what a concept is*, *why it matters*, *how it relates to other concepts* (with the reason for each relationship), and the evidence across the vault that supports it — grouped by role, every link carrying a rationale.

Hubs are optimized for discovery: `aliases` carry the synonyms a reader would search for, `concept/<slug>` tags face the concept, and `related_concepts` encodes the concept web declaratively.

## Concept-node schema

```yaml
---
note_type: concept
concept: <slug>
aliases: [synonyms a searcher would use]
tags: [knowledge, graph, concept/<slug>]
related_concepts: [other hub slugs]
---
```

Body:

```markdown
# {Concept}

**What it is.** {2–3 sentence definition.}

**Why it matters.** {what the reader gains from it.}

## Related concepts
- [[_graph/{other-concept}|Other Concept]] — why the two concepts relate.

## Evidence & supporting material
### {Role heading: How it works / Positioning / Domain application / …}
- [[{subtree}/{note-slug}|Note Title]] — one-line rationale.
```

Role headings under `## Evidence & supporting material` are yours to define — group by the *kind* of support a note provides, not by the subtree it happens to live in.

## Concept hubs

<!-- One line per hub. Add as Cartographer creates them. -->

- *(none yet — hubs are created by the knowledge skill's `cartograph` action)*

## How the concept layer is maintained

- **Cross-tree relationships live here, not inline.** A note in one concept subtree must NOT link directly to a note in a *different* concept subtree. The relationship is authored into the relevant hub's `## Related concepts` or `## Evidence` with a rationale. Notes link **up** to their hub(s) — `[[_graph/<concept>]]` targets are always allowed — and via `related: [<concept>]` frontmatter.
- **Intra-tree links stay inline** in the note body and `## Related` section as normal.
- **Hubs are curator-maintained** (Cartographer role / the knowledge skill's `cartograph` action), never extended by source distillers. When a distillation surfaces a cross-tree connection, route it to Cartographer rather than appending a cross-subtree link in a note.
- **Every hub link carries a rationale.** A bare link is a defect (`vault-lint` C10).
- **Validate before linking.** A wiki-link to a nonexistent path renders as a greyed phantom node and spawns a blank stub on click (`vault-lint` C3).

See `knowledge/AGENTS.md` (Cartographer contract) and `knowledge/vault-conventions.md` (concept schema) for the governing rules, and `tools/vault-lint.py` / `knowledge/audits/` for enforcement.
