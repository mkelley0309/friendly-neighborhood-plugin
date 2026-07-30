# Changelog

All notable changes to this plugin are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/); versions follow [SemVer](https://semver.org/).

## [0.3.0] — 2026-07-30

### Added
- **`audit` action** on the knowledge skill (`actions/audit.md`) — run the vault linter, sanity-check the counts against disk, render a report of record into `knowledge/audits/`, **gate on the user**, then apply only safe auto-fixes. Editorial classes (cross-tree migration, ownership fields, deletions) are never auto-applied.
- **`tools/vault-lint.py`** — stdlib-only static linter for the vault, 12 checks (C1–C12). Report-only by default; `fix` applies only safe, enumerated auto-fixes and never deletes or migrates cross-tree links. Vault root resolves from `$WORKSPACE_ROOT` (falls back to cwd); concept subtrees are auto-discovered from the top-level folders under `vault/`, with a `--subtrees` override — no vault layout is baked in.
- **`knowledge/vault/_graph/index.md`** — the concept-layer contract: concept-node schema, hub list, and the rules for how the layer is maintained.
- **`knowledge/audits/index.md`** — audit report register and conventions.

### Changed
- **`_graph/` is now the semantic concept layer, not a flat index.** Hubs are concept nodes (`note_type: concept`) with `aliases`, `related_concepts`, a definition, concept-to-concept edges that each state *why*, and evidence grouped under role headings. **Every hub link carries a `— rationale`; a bare link is a defect** (C10). Replaces the old `note_type: graph-index` bullet-list format.
- **Cross-tree linking is the concept layer's job, everywhere.** The rule now appears in the skill, the Cartographer contract (`knowledge/AGENTS.md`), the distiller contract (`knowledge/distillers/CLAUDE.md`), and `vault-conventions.md` — not just in the cartograph action. A note may always link *up* to a hub; it may never link sideways into another concept subtree. Enforced by C8.
- **Scout classifies queue signals before verifying them** (`actions/scout.md`). Source signals get source verification (2b–2d); workstream/research-complete signals get new **step 2e** instead — confirm the artifact still exists, route it to Harvest if it does, and close it as orphaned/source-lost if the workstream was cleaned up. Prevents source verification running against a path that was never a source, and stops dead signals sitting `pending` forever.
- **Scout no longer false-flags merged perspective notes as undistilled** (`actions/scout.md`). A perspective note counts as distilled if *any* of three references exist — `source_path:`, a `merged_sources:` entry, or a `Synthesized from:` body line — because multi-source notes name only their primary in `source_path`.
- **Design covers structure outline again** (`actions/design.md`, `framework-templates.md`). When QRSPI's separate Outline step was folded into Design, the *deliverable-structure* half was lost — Design only documented architectural decisions. It now covers both: architectural design (how it works) and structure outline (what the deliverable is shaped like — section order and argument spine, vault layout, API shape, deck arc), with an `outline.md` template restored and a `[D]` governing-decision convention so downstream drafting has one authoritative source.
- **Distiller link validation broadened** (`knowledge/distillers/CLAUDE.md`): verify *every* target before writing, not just cross-subtree ones, and never guess a sub-path when the real note is the leaf.

## [0.2.1] — 2026-07-08

### Changed
- **Agent scoping is now explicit and default** (`_addenda/claude-code.md` → Directory Scoping; workstream/mission skill). Each subagent is scoped to a single subtree — it reads and writes within that subtree only. `control-plane` is the orchestrator that spans boundaries by deploying the right agent per subtree — a knowledge agent to read/curate the vault, a design agent in the project, an implementation agent into a git-repo worktree — and passing distilled artifacts between them. Directory-scoped prompts isolate non-git subtrees; worktree isolation is used for code inside a git repo; never `isolation: "worktree"` from `control-plane/`.

### Fixed
- **Distillation** (`distill.md`): curation subagents now validate that every `[[target]]` wiki-link resolves to an existing note before writing it — prevents phantom nodes / wrong-path links.
- **Cartographer** (`cartograph.md`): cross-subtree connections are recorded in `vault/_graph/{topic}` hub indexes instead of direct branch-to-branch `Related:` links (which are now intra-subtree only); the same link-target validation is applied.

## [0.2.0] — 2026-06-19

### Changed
- **Tier vocabulary:** eliminated the "initiative" tier; the three tiers are now objective → workstream → task, with ceremony sized to the tier.

### Fixed
- `log-decision` documented with positional arguments (`<name> "<decision>" "<rationale>"`) to match the CLI.
- `objective.py` no longer crashes when first run in a bare workspace (creates the portfolio index on demand).

### Security
- Closed an **in-process path-traversal class** that the deny-list and safety hooks structurally cannot catch: crafted (non-kebab) names could write or delete files outside the intended tree via the state CLIs (`objective`/`workstream`/`task`). All now reject any name that isn't plain kebab-case.
- `gate.py` rejects a check with an empty command (previously a vacuous PASS — a gate that verified nothing).

## [0.1.0] — 2026-06-10

Initial release. The un-themed edition.

### Added
- Three-tier orchestration: **objective** → **initiative** → **workstream**, with backing Python CLIs and append-only lifecycles.
- Workstream QRSPI/RPI framework with mandatory progressive distillation, fresh-context research handoffs, and a verification gate before close.
- Knowledge-vault pipeline (**knowledge**): scout → harvest → distill → cartograph → sync, with peer-reviewed vault admission.
- Observational hooks (session/tool/stop logging + recovery breadcrumb on failure).
- A statusline surfacing the active workstream/phase and tier counts.
- `init-workspace` scaffolder bundling a complete, domain-neutral harness in `templates/`.
- Soft, configurable concurrency budget (`max_concurrent_agents`).

No agent personas, output style, or themes — see the `friendly-neighborhood-lite` / `friendly-neighborhood` editions for those.
