# distillers/queue/

Signal files for pending Scout and Harvester work. Written by the `campaign` skill's research action when a research phase completes. Consumed by Scout at session start.

---

## Queue File Schema

One file per signal: `queue/{campaign}-{YYYYMMDD}.md`

```yaml
---
signal: research-complete
workstream: <kebab-case campaign name>
research_path: control-plane/workstreams/<name>/research.md
target_vault_subtrees: [<list of vault subtrees>]
queued_at: <ISO datetime>
status: pending | processing | done
---
```

Body: optional context or notes for Scout (what the research phase covered, classification hints).

---

## Status Transitions

```
pending → processing → done
```

- `pending` — signal written; Scout has not yet processed it
- `processing` — Scout has started processing; updated at start of Scout pass
- `done` — Scout has verified the source and updated staging; processing complete

Scout processes one pending item per invocation. Multiple pending items are processed sequentially.

---

## Retention

Done files stay in `queue/` for 30 days, which allows audit and rollback if a distillation pass produces unexpected vault writes.

After that, Scout moves them to `queue/_archive/` (`actions/scout.md` Step 4a). Archived signals are the processing log: they are never deleted, and Scout does not read them. `pending` and `processing` signals are never archived.

---

## on-stop Integration

At session end, the on-stop hook checks this directory for any file with `status: pending`. If found, it appends a reminder line to the recovery breadcrumb so the next session start surfaces the pending work.
