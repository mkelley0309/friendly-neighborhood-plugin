---
description: Operating contract for the knowledge subtree — shared data layer with sources, perspective, vault, and distillers.
paths: ["knowledge/**"]
---

# Knowledge Layer

Shared data layer. Two raw-input zones feed one curated zone, with a deliberate wall between input and output.

```
knowledge/
  CLAUDE.md      ← thin pointer (contract is here)
  sources/       ← raw EXTERNAL truth (append-only, traceable, system-synced)
  perspective/   ← raw FIRST-PARTY truth (your experience, views, judgment — uniquely yours)
  vault/         ← curated Obsidian knowledge (reshaped, enriched, navigable)
  distillers/    ← curation recipes: sources/ + perspective/ → vault/
```

`sources/` and `perspective/` are peers: both are raw input the pipeline distills into `vault/`. They differ only in origin. `sources/` is what the world says (verifiable against an external artifact). `perspective/` is what *you* say (first-party, experiential, not externally verifiable). The vault is the single curated output zone — perspective is **not** mirrored into a `vault/perspective/` subtree; its distilled output lands wherever in the vault concept hierarchy it fits best.

See [`vault-conventions.md`](vault-conventions.md) before reading or writing under `vault/`.

---

## Sources

Raw system truth. Written verbatim by fetchers and pipelines under `projects/`. Each feed gets its own subdirectory: `sources/{name}/`.

Rules:
- One subdirectory per producing project
- No curation, wiki-links, breadcrumbs, `index.md` hubs, or hand-edits
- Provenance frontmatter only: `note_type`, `source`, `source_url`, `synced_at`, `vendor`
- Full re-syncs are destructive within a source folder — that's the contract
- Always traceable to origin

Current sources:

*Register your sources here — one entry per feed, e.g.:*
- `sources/{source-name}/` — maintained by `projects/docs-sync/{source-name}/`

---

## Vault

Curated, Obsidian-backed knowledge. Reshaped, enriched, cross-linked. Written deliberately.

Access (default, in priority order):
1. `obsidian-cli` skill — wraps the `obsidian` CLI (`obsidian vault`, `obsidian search`, `obsidian append`, etc.); use for all read/write/search against the vault
2. `obsidian-markdown` skill — Obsidian-flavored Markdown authoring (wikilinks, callouts, frontmatter, embeds)
3. `obsidian-bases` skill — `.base` files (views, filters, formulas)
4. `json-canvas` skill — `.canvas` files
5. `defuddle` skill — clean-markdown extraction from web pages into the vault
6. Direct filesystem (Read/Write/Glob/Grep) — fallback for bulk ops only

Vault target: `knowledge/vault/` (set `VAULT_PATH` env var or update your tool config to point here). Follow `vault-conventions.md`: wiki-links, `index.md` hubs, `note_type` frontmatter.

Rules:
- Reorganize, summarize, enrich freely
- Maintain references back to source when curating from `sources/`
- No duplication of raw source content — link or summarize, don't copy
- Confidential terms never leave vault in external-facing work

---

## Perspective

Raw first-party truth — your experience, interpretation, and judgment. This is the layer that makes the vault uniquely yours; no external source can supply it. Each domain gets its own subdirectory: `perspective/{domain}/`.

Content is captured here when it is first-person and experiential rather than externally authoritative: named-persona day-in-the-life narratives, before-state rituals, what lands wrong with practitioners, positioning judgment, counter-claim landmines, and field intelligence you gathered and interpreted yourself.

Rules:
- One subdirectory per domain: `perspective/{domain}/`
- Treated by the pipeline **exactly like a source**: raw input, passed through light review, then distilled into the vault
- Retained after distillation (like `sources/`) — it is the first-party record of origin; never deleted by cleanup
- Distilled output goes to the most appropriate vault concept subtree — **never** `vault/perspective/`
- Provenance frontmatter marks it first-party: `note_type: perspective`, `domain`, `captured_at`, `origin`, `tags: [perspective/{domain}]`
- Content lands here three ways: authored directly, surfaced from workstream research by Synthesizer, or auto-routed by Scout/Harvester when they detect first-party views inside otherwise-external material (see `AGENTS.md`)

Perspective is raw input, not the curated layer — keep it faithful to your own voice; the vault is where it becomes navigable.

---

## Distillers

Recipes for turning `sources/` and `perspective/` into `vault/` content. Invoke via the `knowledge` skill or directly from `knowledge/distillers/`. See `distillers/CLAUDE.md`.

---

## Boundaries

- Projects write to `sources/` (via their own entry points)
- `perspective/` is written by you, by Synthesizer (from workstream research), or by Scout/Harvester auto-routing detected first-party views
- Distillers read `sources/` and `perspective/`, write to `vault/`
- Nothing writes to `vault/` automatically — hand-curation is fine, auto-generation is not (every vault write still passes Peer Review)
- Control-plane reads all three; writes to none directly

---

Sources = external truth (raw, faithful). Perspective = first-party truth (raw, yours). Vault = usable knowledge (curated, linked). Distillers = the bridge (deliberate, repeatable).
