# Action: Scout

Session-start health check for the web-archive pipeline. Reads the distiller queue, verifies referenced sources, registers first-party perspective inputs, updates queue status, and surfaces stale staging items.

## When to run

- **Default:** At the start of every session involving the `web-archive` skill — run Scout before any other action
- **On-demand:** When the user says "scout the queue", "check pending signals", or "run Scout"

---

## Steps

### 1. Read the queue for pending signals

Read all files in `knowledge/distillers/queue/`.

For each file, check its frontmatter `status` field:
- Collect all items where `status: pending`
- Skip items where `status: processing` or `status: done`

If there are no pending items, skip to Step 4 (stale staging scan).

---

### 2. For each pending item: verify source and update status to processing

Process each pending queue item in order.

**2a. Mark status as processing**

Update the queue file's frontmatter:

```yaml
status: processing
```

Write the updated file to `knowledge/distillers/queue/{item}.md`.

**2b. Identify the source slug**

Extract the source slug from the queue signal's `research_path` or `target_vault_subtrees`. Derive the source slug (e.g., the folder name under `knowledge/sources/`).

**2c. Verify the source**

A source passes verification if ALL of the following are true:

1. **Source folder exists:** `knowledge/sources/{source-slug}/` is present
2. **Manifest exists:** `knowledge/sources/{source-slug}/_manifest.md` exists and is readable
3. **Provenance frontmatter is present:** At least one source note in `knowledge/sources/{source-slug}/` carries a `source:` frontmatter field (sample check — read the manifest, not every note)

If the source passes all three checks, the verification result is `verified`.
If any check fails, the verification result is `stale` and note which check failed in the record body.

**2d. Write or update the verification record**

Write to `knowledge/sources/verified/{source-slug}.md`:

```yaml
---
note_type: verification-record
source: <source slug>
source_path: sources/<source-slug>/
verified_at: <ISO datetime, e.g. 2026-05-12T09:00:00>
verified_by: Scout
manifest_path: sources/<source-slug>/_manifest.md
note_count: <N from manifest, or "unknown" if manifest unreadable>
status: verified | stale
---

<If status is stale, describe which check failed and why.>
<If status is verified, omit the body or write a one-line confirmation.>
```

If a verification record already exists for this source slug, overwrite it with the updated `verified_at` and current `status`.

---

### 3. Mark each processed item done

After writing the verification record for a queue item, update its status:

```yaml
status: done
```

Write the updated file to `knowledge/distillers/queue/{item}.md`.

Do not delete queue files — they serve as a processing log.

---

### 4. Scan staging for stale items

Read the file list in `knowledge/distillers/staging/` (filenames and modification times only — do not read file contents).

An item is **stale** if its last modification time is more than 14 days before today's date.

For each stale item, record:
- File name
- Age in days (calculated from mtime to today)

Do not delete, modify, or move any staging files.

---

### 4b. Register perspective inputs

`perspective/` is a first-party raw-input zone, peer to `sources/`. List the domain folders:

```
knowledge/perspective/{domain}/
```

For each domain, check whether its notes have been distilled into the vault yet. A perspective note is **undistilled** if no vault note carries `provenance: first-party` with a `source_path` pointing at it. (Sample-check: grep the vault for `provenance: first-party` and compare `source_path` values against the perspective files present.)

Surface undistilled perspective domains as candidates for a Distill pass. Do not distill them — Scout only flags.

Do not modify perspective files in this step. (The only writes Scout makes to `perspective/` are auto-routed first-party content per Step 4c.)

### 4c. Auto-route first-party content found while scouting

If, while reading a queue signal or a verified source during this pass, you encounter content that is clearly first-party opinion/view rather than externally authoritative (see the opinion-vs-source heuristic in `knowledge/AGENTS.md`), write it to `knowledge/perspective/{domain}/{note}.md` using the perspective input schema and record it for the report. Do not push first-party content into the source pipeline.

This is the only path by which Scout writes outside `distillers/queue/`.

---

### 5. Report summary

After completing all steps, report to the user:

```
Scout pass complete.

Queue:
  - Pending found: <N>
  - Processed this pass: <N>
  - Sources verified: <list of source slugs>
  - Sources stale/failed: <list, or "none">

Perspective:
  - Domains: <list of perspective/{domain} folders>
  - Undistilled (candidates for Distill): <list, or "none">
  - Auto-routed this pass: <list of perspective/{domain}/{note}.md written, or "none">

Staging:
  - Stale items (>14 days): <N>
  <If N > 0, list each: "{filename}" — {age} days old>
  <If N = 0, write "None.">

Next recommended action: <one of: Harvest, Distill, "Distill perspective/{domain}", or "Queue is clear — no action needed">
```

If any source failed verification, highlight it clearly and state which check failed so the user can diagnose before Harvest runs.

---

### 6. Append breadcrumb if queue was non-empty

If at least one pending item was found and processed during this pass, append a breadcrumb entry to the queue index or the last processed queue file body (do not create a new file for this). The breadcrumb is a one-line note in the file body:

```
Scout processed <YYYY-MM-DD>: verified <source slug>, status set to done.
```

This ensures the queue file self-documents when it was last touched.

---

## Allowed writes

| Path | Allowed operation |
|---|---|
| `knowledge/distillers/queue/{item}.md` | Update `status` field (pending → processing → done); append breadcrumb |
| `knowledge/sources/verified/{source-slug}.md` | Write or overwrite verification record |
| `knowledge/perspective/{domain}/{note}.md` | Write auto-routed first-party content only (Step 4c) |

## Do NOT write to

- `knowledge/vault/` or any subtree of it
- `knowledge/distillers/staging/` (read mtime only)
- `knowledge/sources/{source-slug}/` beyond reading manifest
- `knowledge/perspective/` beyond Step 4c auto-routing (registration in Step 4b is read-only)
- `control-plane/` or any patrol path
- Any path not listed in the allowed writes table above

---

## Notes

- Scout does not invoke Harvest or Distill. It only prepares the queue state and surfaces what needs attention.
- A `stale` verification result does not block the queue item from being marked done — it flags a problem for the user to resolve before running Harvest.
- If a queue file's `research_path` points to a control-plane patrol, Scout reads only enough to identify the source slug — it does not read or summarize the research content.
