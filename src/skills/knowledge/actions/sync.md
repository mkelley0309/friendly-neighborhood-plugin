# Action: Sync

Refresh upstream sources via your **source-sync mechanism**, then write a queue signal so Scout knows new content is available.

> **What's a source-sync mechanism?** Any skill or script *you provide* that pulls a source's current content into `knowledge/sources/{source}/` and updates its `_manifest.md`. What to pull is domain-specific, so the harness bundles none — wire in your own (e.g. a `docs-sync` skill, a scraper, an API client, or a `git pull` of a docs repo).

## When to run

- User says "sync sources", "refresh docs", "pull the latest", or names a specific source
- Before a distillation pass when sources may be stale
- On a regular cadence to keep `knowledge/sources/` current

## Steps

### 1. Identify target sources

If the user named a specific source slug, use that. Otherwise sync all configured sources.

Configured sources are defined per-project. Check `knowledge/sources/` for existing source folders, or ask the user which sources to sync if the list is unclear.

### 2. Run the source-sync mechanism

Run your source-sync mechanism for each target source. It writes raw content to `knowledge/sources/{source}/` and updates that folder's `_manifest.md`.

It must write to `sources/` only — never to vault or staging paths.

### 3. Write queue signal

After the sync completes for each source, write a queue signal file:

**Path:** `knowledge/distillers/queue/{source-slug}-{YYYYMMDD}.md`

```yaml
---
signal: sync-complete
workstream: sync
research_path: null
target_vault_subtrees: [{target subtrees for this source — from the source's recipe.md}]
queued_at: {ISO datetime}
status: pending
---

Sync completed for {source-slug}. {N} pages updated per _manifest.md.
```

The target subtrees for each source are defined in that source's `recipe.md` at `knowledge/distillers/{source-slug}/recipe.md`. Read the recipe to populate `target_vault_subtrees` correctly.

### 4. Report

State: which sources were synced, how many pages updated per manifest, and how many queue signals written.

## Notes

- If the sync fails for a source, write the queue signal with `status: pending` and note the failure in the body — Scout will surface it.
- Do not invoke Scout, Harvester, or Distill automatically. The queue signal is the handoff; the user (or Scout at next session start) picks it up.
