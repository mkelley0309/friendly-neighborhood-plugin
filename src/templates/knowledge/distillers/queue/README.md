# distillers/queue/

Signal files for pending Scout and Harvester work. Written by the `workstream` skill's research action when a research phase completes. Consumed by Scout at session start.

---

## Queue File Schema

One file per signal: `queue/{workstream}-{YYYYMMDD}.md`

```yaml
---
signal: research-complete
workstream: <kebab-case workstream name>
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

Done files are retained for 30 days. They are never automatically deleted — manual cleanup only. The 30-day window allows audit and rollback if a distillation pass produces unexpected vault writes.

Scout surfaces items older than 30 days with `status: done` as candidates for manual deletion.

---

## on-stop Integration

At session end, the on-stop hook checks this directory for any file with `status: pending`. If found, it appends a reminder line to the recovery breadcrumb so the next session start surfaces the pending work.
