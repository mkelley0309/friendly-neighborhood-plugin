# Distillers

Curation recipes: `knowledge/sources/` and `knowledge/perspective/` → `knowledge/vault/`. One subdirectory per source, plus one shared `perspective/` distiller for first-party input. Invoked via the `knowledge` skill (`/harness-core:knowledge distill`) or directly.

```
distillers/
  CLAUDE.md          ← this file
  _example-source/   ← template recipe showing the pattern; copy and rename for real sources
  perspective/       ← perspective/{domain}/ → vault/{content-appropriate subtree}
  staging/           ← candidate notes awaiting Peer Reviewer admission
  queue/             ← Scout work queue (signal files)
```

---

## What a Distiller Owns

Each `distillers/{source}/` contains:

- `recipe.md` — curation contract: what maps where, what gets summarized vs. passed through, how `index.md` hubs are built, link/frontmatter conventions
- `vault-layout.md` — target vault hierarchy for this source (optional but recommended for large sources)
- Optional: `prompts/` — reusable prompt snippets for subagents doing curation
- Optional: `schema.md` — frontmatter/tag conventions specific to this distiller's outputs

Distillers are **knowledge, not code**. No Python. Deterministic transformation belongs in `projects/`.

---

## How Distillation Runs

1. Read source manifest — know what upstream pages exist
2. Read vault layout from `recipe.md`
3. Diff: what vault notes exist vs. what source content warrants a note
4. Delegate curation to capable subagents per section (each returns a vault-ready note)
5. Write/update vault notes via `obsidian-cli` or Write tool
6. Write/refresh `index.md` hubs as curation progresses

Incremental by default. Full rebuild is possible but not the norm.

---

## Silo Discipline

**Each source distiller is scoped to exactly one source and one vault subtree.** It knows nothing about the rest of the vault.

- Wiki-links produced by a distiller are intra-silo only
- Cross-subtree links are never authored by a distiller

Cross-referencing is a separate concern, deferred until enough silos exist.

**Exception — the perspective distiller.** First-party input is classified by content, not bound to one subtree, so the perspective distiller may write to whichever vault concept subtree fits each note. It still produces only intra-silo wiki-links within whichever subtree a note lands in; cross-subtree linking remains Cartographer's job.

---

## Contract

- Distillers may read from `sources/{name}/` and `perspective/{domain}/` freely
- Distillers never edit `sources/` or `perspective/` files
- Distillers write only to `vault/`, using paths defined in `recipe.md`
- Re-running against unchanged input is a no-op (idempotent)

---

## Wikilink Convention (Binding)

All vault-writing agents must follow these rules without exception:

- **Vault root is `knowledge/vault/`.** Obsidian resolves wikilinks from that root — not from the filesystem root or any parent.
- **Never include `vault/` as a prefix.** Write `[[domain-knowledge/concept]]`, not `[[vault/domain-knowledge/concept]]`.
- **Verify cross-subtree targets before writing.** If you are linking to a note outside the subtree you are currently writing, confirm the target path exists (Glob or Read check) before writing the link. Do not assume path structure — a directory you expect may not exist or may be named differently.
- **Correct:** `[[domain-knowledge/concept]]`, `[[reference/glossary/term]]`
- **Wrong:** `[[vault/domain-knowledge/concept]]`, `[[domain-knowledge/nonexistent-subdir/concept]]` (phantom subdirectory)

---

## Cross-Distiller Frontmatter Contract

All distiller-produced vault notes must include these six fields. No exceptions.

```yaml
note_type: vault-note
source_path: <relative path under sources/>
source_url: <original URL>
synced_at: <ISO date of last sync>
distilled_at: <ISO date of distillation run>
tags: [vendor/<slug>, ...]   # at minimum one vendor tag
confidence: high             # distiller default; downgrade to medium/low if warranted
```

**Raw source notes** (docs-sync output, pre-distillation) use a different schema:

```yaml
note_type: vendor-documentation
source_url: <original URL>
synced_at: <ISO date>
tags: [vendor/<slug>, raw]
```

Raw source notes live in `knowledge/sources/` only. If `note_type: vendor-documentation` appears in `vault/`, it has not been curated and must be reprocessed.

**First-party vault notes** (distilled from `perspective/`) use the six-field contract with two changes — `provenance: first-party`, `source_path` points into `perspective/`, `source_url: na`, and `confidence` ceilings at `medium` (raise to `high` only if a source corroborates):

```yaml
note_type: vault-note
provenance: first-party
source_path: perspective/{domain}/{note}.md
source_url: na
synced_at: <captured_at of the perspective note>
distilled_at: <ISO date of distillation run>
tags: [perspective/{domain}, ...]
confidence: medium
```

**Raw perspective notes** (pre-distillation, first-party input) use the perspective schema and live in `knowledge/perspective/` only:

```yaml
note_type: perspective
domain: <perspective/{domain}>
captured_at: <ISO date>
origin: <"direct" | workstream name | "harvested-from: sources/{path}">
tags: [perspective/{domain}, ...]
```

**Silo discipline applies to source distillers only.** Each source distiller is scoped to one source and one vault subtree. Two roles are exempt: Cartographer (operates post-curation across subtrees) and the perspective distiller (classifies first-party input by content, so it has no fixed source→subtree mapping). See `knowledge/AGENTS.md`.

---

## Adding a Distiller

1. Copy `distillers/_example-source/` to `distillers/{source-name}/`
2. Edit `recipe.md` — map your source paths to vault paths, define subtree target
3. Optionally add `vault-layout.md` — target vault tree diagram
4. Register the new source in `knowledge/CLAUDE.md` under "Current sources"
5. Add action files to your skill's actions directory and register in the skill routing table if using the `knowledge` skill
