# Action: Audit (vault-lint)

Run the static vault linter, interpret findings, gate before mutating, apply only safe auto-fixes, and store the report of record in `knowledge/audits/`. Audits keep the vault structurally consistent, internally navigable, and free of the drift that accumulates as notes are admitted over time.

## When to run

- User says "audit the vault", "lint the vault", "check vault health / consistency", "run vault-lint".
- Before the vault is shared, or before a large batch is admitted.
- Periodically as hygiene (structure drift, phantom links, cross-tree links escaping `_graph`).

## Tool

`tools/vault-lint.py` — stdlib Python, scans `knowledge/vault/`. Report-only by default; `fix` applies **only** safe, enumerated auto-fixes (never deletes, never migrates cross-tree links).

```
python tools/vault-lint.py check             # human report
python tools/vault-lint.py check --json      # structured findings
python tools/vault-lint.py check --check C8  # single check
python tools/vault-lint.py fix               # apply safe auto-fixes
```

Vault root resolves from `WORKSPACE_ROOT` (defaults to the current working directory). Concept subtrees are auto-discovered as the top-level folders under `vault/` (excluding `_graph/`); override with `--subtrees a,b,c` if your layout needs it.

## Checks

| | Check | Auto-fixable |
|---|---|---|
| C1 | Required frontmatter fields present | yes (`source_url: na`) |
| C2 | `note_type` present and valid | yes |
| C3 | Unresolved wiki-links (phantom nodes) | partial (prefix truncation) |
| C4 | Zero-outbound-link notes (informational) | no |
| C5 | Links carrying a redundant `vault/` prefix | yes |
| C6 | Folder missing its `index.md` | yes (stub) |
| C7 | First-party notes exceeding the `confidence` ceiling | no |
| C8 | Cross-tree links authored outside `_graph/` | no — editorial |
| C9 | Ownership/personalization fields (never flags `author:` credits) | no — editorial |
| C10 | Concept-hub links missing a `— rationale` | no |
| C11 | Concept-hub frontmatter schema | no |
| C12 | Hub/index completeness | no |

## Steps

1. **Scan.** Run `check --json`; summarize per-check counts.
2. **Sanity-check the counts before trusting them.** Sample findings per check and verify against disk — resolver false-positives, escaped-pipe `\|` links, code-fenced `[[`, and `_graph`-sourced links are all known traps. Never present raw counts you have not spot-checked.
3. **Render the report** to `knowledge/audits/vault-lint-YYYY-MM-DD.md`, grouped by defect class, every affected path listed, each item tagged auto-fix / manual / confirm-delete. Add a row to `knowledge/audits/index.md`.
4. **GATE.** Present the report to the user before ANY mutation. Call out deletions and cross-tree migrations explicitly. Do not proceed without an explicit go/no-go.
5. **Apply safe auto-fixes** with `fix` (C1, C2, C3 prefix-truncation, C5, C6).
6. **Editorial items are NOT auto-fixed:**
   - **C8 cross-tree** → migrate into `_graph/` concept hubs (a rationale per link, plus concept-to-concept edges), then prune from the source note. This is Cartographer work — see `actions/cartograph.md`.
   - **C9 ownership fields** → convert ownership framing to a plain `author:` credit (keep the person as author; drop the "mine" framing).
   - **Deletions / missing-file content** → confirm with the user; open an intake item for genuinely-missing linked notes.
7. **Verify.** Re-run `check`; confirm the intended classes are clean and the preservation boundary (`provenance: first-party`, `perspective/*`, `author:` credits, `_graph`-targeted links) is intact.

## Boundaries

- Read/scan `knowledge/vault/`; write reports to `knowledge/audits/` only.
- `fix` never deletes and never performs C8 migration — those stay human/editorial.
- Never flag or strip legitimate `author:` credits or the perspective/first-party layer.
- Audit does not admit notes, distill, or cross-link. It reports; Cartographer and the distillers act.
