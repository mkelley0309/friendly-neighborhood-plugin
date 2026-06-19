# build/ — maintenance scripts

This repo is a **marketplace** with three editions under `plugins/`:

| Edition | Source of truth |
|---|---|
| `friendly-neighborhood` (full) | **canonical** — author changes here first |
| `friendly-neighborhood-lite` | a curated *trim* of full (themed) |
| `harness-core` | the *un-themed* edition (original naming, no personas/theme) |

## `sync-clis.sh`

Keeps the deterministic Python CLIs (`workstream.py`, `objective.py`, `initiative.py`, `setup-keys.ps1`) aligned across editions, since they're copied into each edition's `templates/tools/`.

```bash
bash build/sync-clis.sh
```

- **Full → Lite:** all four CLIs are byte-identical and are overwritten from full.
- **Full → Core:** only `objective.py` + `setup-keys.ps1` are identical (synced). `workstream.py` and `initiative.py` carry **un-themed vocabulary** in Core (a code comment / body strings), so they are *not* overwritten — the script prints how many lines diverge and reminds you to hand-apply any **logic** change to the Core variant.

## Editing guidance

- **Skills / agents / templates / hooks / docs** differ per edition by design (naming, flavor, roster) — edit each edition directly; there's no auto-sync for prose.
- **CLI logic** — change it in `full` first, then run `sync-clis.sh`; for `workstream.py`/`initiative.py`, also hand-apply the logic delta to `harness-core` (its wording is intentionally different).
- After any change, re-validate: `claude plugin validate ./plugins/<edition> --strict`.
