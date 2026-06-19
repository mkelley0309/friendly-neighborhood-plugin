---
name: web-archive
description: Manage the web-archive pipeline — a knowledge system that scouts pending signals, harvests and stages candidates, distills sources and first-party perspective into the Web (your linked vault of notes), cartographs cross-vault links, and syncs upstream sources. Use when you want to pull web content or notes into your personal knowledge base, check what's queued for processing, or enrich existing vault notes with cross-links.
---

# Skill: web-archive

Governs the full `knowledge/` pipeline: source verification, candidate staging, vault admission, cross-vault enrichment, and upstream sync. Two raw-input zones feed one curated vault: `sources/` (external truth) and `perspective/` (first-party truth — the user's own experience, views, and judgment). Each action maps to one agent role defined in `knowledge/AGENTS.md`.

The vault is **the Web** — a growing network of linked notes that is uniquely yours.

## When to use

- User says "scout the queue", "check pending signals", "run Scout"
- User says "harvest from sources", "stage candidates", "run Harvester"
- User says "distill [a source]", "curate [a source] into the vault", "update vault from sources"
- User says "distill perspective", "pull my perspective notes into the vault"
- User says "cartograph the vault", "add cross-links", "run Cartographer"
- User says "sync sources", "refresh docs", "run docs-sync"
- After a mission's research phase completes and a queue signal has been written
- Content surfaces that is the user's own opinion/view/experience — auto-route it to `perspective/{domain}/` (it becomes pipeline input)

## When NOT to use

- Reading sources for a one-off research pass (read directly — no pipeline needed)
- Hand-writing original vault notes not derived from any source or perspective (write via Obsidian directly)
- Mission planning, design, or implementation (those are mission skill concerns)

## Action routing

Load exactly one action file per invocation.

| Intent | Action file |
|---|---|
| Session-start queue check, source + perspective verification, stale staging review | `actions/scout.md` |
| Classify verified sources, write staging candidates, auto-route first-party content to perspective | `actions/harvest.md` |
| Recipe-driven distillation of a source — or `perspective/{domain}` — into vault | `actions/distill.md` |
| Add cross-vault wiki-links and update `_graph/` indexes | `actions/cartograph.md` |
| Refresh upstream sources via your source-sync mechanism, write queue signal | `actions/sync.md` |

## Two raw-input zones

The pipeline distills from two peers; classify input before routing it (opinion-vs-source heuristic in `knowledge/AGENTS.md`):

- **`sources/`** — external truth (verifiable against a published artifact). Distilled with `confidence: high`, carries `source_url`.
- **`perspective/`** — first-party truth (the user's experience, views, judgment; not externally verifiable). The layer that makes the Web uniquely theirs. Distilled with `provenance: first-party`, `confidence: medium` ceiling, `source_path` into `perspective/`, landing at the content-appropriate vault subtree (never `vault/perspective/`).

When Scout/Harvester/Synthesizer encounter first-party views inside otherwise-external material, they **auto-route** the interpretive part to `perspective/{domain}/` and report — they never silently consume it into the source pipeline.

## Invariants

- Scout runs before Harvest. Harvest runs before Distill (for queue-driven flows).
- Nothing writes to `vault/` without passing Peer Reviewer admission.
- Distillers write to concept-domain subtrees, not vendor-named subtrees; perspective never gets a `vault/perspective/` subtree — its output lands at the content-appropriate concept subtree.
- Cartographer is the only agent that crosses vault subtree boundaries.
- `sources/` and `perspective/` are never modified by a distill/cartograph pass — both are raw input, retained after distillation.
- Source-distilled notes carry the six required frontmatter fields; perspective-distilled notes carry the same six plus `provenance: first-party` (see `knowledge/distillers/CLAUDE.md`).

## Vault taxonomy

The Web uses concept-domain subtrees. A typical starting layout:

- `vault/domain-knowledge/` — field-level domain expertise
- `vault/reference/` — reference material and how-to guides
- `vault/_graph/` — cross-cutting index notes (Cartographer-owned)

Subtrees are fully customizable per domain. Each source's `recipe.md` defines the source→subtree mapping for that source.

## Related

- Agent role definitions + opinion-vs-source heuristic + auto-routing protocol: `knowledge/AGENTS.md`
- Vault admission contract: `knowledge/vault-conventions.md`
- Distiller contracts: `knowledge/distillers/CLAUDE.md`
- Perspective distiller recipe: `knowledge/distillers/perspective/recipe.md`
- First-party zone conventions: `knowledge/perspective/index.md`
- Upstream source sync: a source-sync skill **you provide** (e.g. `docs-sync`) — what to pull is domain-specific, so the harness bundles none; any skill or script that writes raw content into `knowledge/sources/{source}/` and updates its `_manifest.md` fills this role. Invoked by `actions/sync.md`.
- Queue signals: `knowledge/distillers/queue/`
- Staging: `knowledge/distillers/staging/`
