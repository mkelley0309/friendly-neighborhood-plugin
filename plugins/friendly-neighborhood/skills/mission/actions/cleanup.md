# Action: Cleanup

> **Phase council** (QRDPIV: Cleanup) — consult only when the concern is live (full map in `/friendly-neighborhood:creed`): driver `peter`; counsel `ned`, `jameson`; watch villains `carnage`, `mysterio`.

Write the log entry, delete all working files, remove the folder.

## Steps

1. **Review `workstream-notes.md`** — read the mission's `workstream-notes.md` if it exists. This is the self-learning ledger accumulated across **all** phases, not just implement. Surface to the user:
   - Challenges, discrepancies, and process observations from any phase worth remembering — these feed the log entry's "What Worked / Lessons Learned" section
   - Any suggestions recorded in the Permission / Settings Suggestions section

   **Always ask before acting on suggestions.** Present each suggestion to the user and wait for explicit confirmation before making any changes to settings, permissions, or skill files. Do not implement suggestions silently as part of cleanup.

2. **Verify outputs are safe** before deleting anything:
   - Produced artifacts (slides, documents, configs, generated content) should already be in `control-plane/outputs/{name}/` — confirm they are there before proceeding. If they are still in the mission folder, move them now.
   - Vault content → `knowledge/vault/` via `web-archive` skill or `obsidian-mcp`
   - Reusable prompts → `prompts/templates/` or `prompts/workflows/`
   - Decisions relevant to parent responsibility → append via `python -B tools/objective.py log-decision <parent> "..." "..."`
   - Code → `projects/{name}/` per its CLAUDE.md

3. **Synthesizer (opt-in):** Scan `_working/` for files that may contain harvestable knowledge concepts — research pass files, distilled findings, structured summaries. Present a brief list to the user and ask: *"Should any of these be staged for vault candidacy?"* If the user confirms, write each approved candidate to `knowledge/distillers/staging/{mission}-{slug}-candidate.md`. Never write directly to vault — staging only. If the user declines, skip with no action.

4. **Cartographer (opt-in):** If this patrol produced any vault writes (via distillers or directly), ask the user: *"Should Cartographer run to update `_graph/` indexes and add `related:` links for new vault content?"* Invoke only on explicit confirmation; otherwise skip.

5. **Archive intake provenance** — if the mission `index.md` frontmatter lists `intake_source`, move each referenced file from `intake/` to `intake/_archive/` (create `_archive/` if absent), then update `intake/index.md` so the item is no longer listed as live intake. Do not delete intake files outright — archiving preserves the capture-to-promotion trace.

6. **Knowledge-queue gate (before any deletion)** — the mission folder holds the `_working/` research that `knowledge/distillers/queue/` signals point at. Once the folder is deleted, that material is unrecoverable for the pipeline. So before archiving/deleting:
   - Read `knowledge/distillers/queue/` for any signal where `workstream: {name}` (or whose `research_path` points into this mission) with `status: pending` or `status: processing`.
   - If any are unresolved, **stop and warn the user**: name the pending signal(s) and ask whether to (a) run the `/web-archive` pipeline now so the material is distilled/staged before deletion, or (b) explicitly discard them. Do not proceed to deletion until the user chooses.
   - On "run": invoke the `web-archive` skill to process the signal(s) to `done` (or to a staged candidate) first, then continue.
   - On "discard": mark the signal `status: done` with a one-line note that the source `_working/` was discarded at cleanup without distillation, then continue.
   - Record the outcome in the log entry's "Durable Artifacts" section.

7. **Write log entry** `control-plane/workstreams/_log/YYYY-MM-DD-{name}.md` using the template in `framework.md`. Verify the file exists (Read tool) before deleting anything.

8. **Archive and delete**:

```bash
python -B tools/workstream.py archive <name> --log-date YYYY-MM-DD --description "<one-line>"
python -B tools/workstream.py delete <name>
```

Log entries are never deleted. The folder is permanently removed.
