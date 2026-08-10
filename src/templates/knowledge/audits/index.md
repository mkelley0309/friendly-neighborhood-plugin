---
note_type: index
scope: audits
---

# Vault Audits

Reports of record from `tools/vault-lint.py`. One report per audit pass; nothing here is deleted — the history is how structural drift is tracked over time.

Run via the knowledge skill's `audit` action, which gates on your approval before any mutation.

## Reports

| Date | Report | Findings at scan | Applied | Notes |
|---|---|---|---|---|
| *(none yet)* | | | | |

## Conventions

- Report path: `knowledge/audits/vault-lint-YYYY-MM-DD.md`
- Optional raw findings alongside it: `vault-lint-YYYY-MM-DD.findings.json`
- Each report groups findings by defect class, lists every affected path, and tags each item **auto-fix** / **manual** / **confirm-delete**.
- Counts are spot-checked against disk before being published — the linter's resolver has known false-positive traps (escaped-pipe `\|` links, code-fenced `[[`, `_graph`-sourced links).
