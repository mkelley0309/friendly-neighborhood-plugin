# Recipe: {source-name}

> Copy this file to `distillers/{your-source-name}/recipe.md` and fill in the placeholders.
> Delete this callout block when done.

---

## Source

- **Source directory:** `sources/{source-name}/`
- **Upstream origin:** {URL or description of where this content comes from}
- **Sync mechanism:** {how content is fetched — e.g., docs-sync script, manual export, API pull}
- **Source frontmatter key:** `vendor: {source-name}`

---

## Target Vault Subtree

All output from this distiller lands under:

```
vault/{target-subtree}/
```

Replace `{target-subtree}` with the vault subdirectory this source populates (e.g., `domain-knowledge/`, `reference/`, `product/`). Keep it to one primary subtree per distiller (silo discipline).

---

## Sections

List the major sections of this source and their vault mapping:

| Source path | Vault path | Treatment |
|---|---|---|
| `sources/{source-name}/getting-started/` | `vault/{target-subtree}/getting-started/` | summarize |
| `sources/{source-name}/reference/` | `vault/{target-subtree}/reference/` | pass-through |
| `sources/{source-name}/concepts/` | `vault/{target-subtree}/concepts/` | synthesize into concept notes |

Treatment options:
- **summarize** — condense to key points, add wiki-links
- **pass-through** — admit near-verbatim (only valid for designated reference subtrees)
- **synthesize** — extract one concept per note, rewrite for semantic density

---

## Index Hubs

List `index.md` files this distiller owns and must keep current:

- `vault/{target-subtree}/index.md` — top-level hub for this source's vault area
- `vault/{target-subtree}/{section}/index.md` — section hubs (add as needed)

---

## Frontmatter Defaults

All notes produced by this distiller carry:

```yaml
note_type: vault-note
tags: [vendor/{source-name}]
confidence: high
```

Plus the six required provenance fields (`source_path`, `source_url`, `synced_at`, `distilled_at`).

---

## Sync State

```
synced_at:    # date of last docs-sync run
distilled_at: # date of last distillation pass
```

Update these after each run.

---

## Notes

Any source-specific quirks, pagination rules, content exclusions, or known gaps go here.
