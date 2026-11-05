# Changelog

All notable changes to this plugin are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/); versions follow [SemVer](https://semver.org/).

## [0.5.1] — 2026-11-05

### Fixed
- **Run logs no longer dirty the tree.** `cadence-run.ps1` creates `_working/.gitignore` before each run, so a run's own commit no longer picks up a partial log that claude finishes writing at exit. Run logs are now local scratch and are not committed.
- **A killed run now leaves evidence.** `cadence-run.ps1` writes a `RUNNING-*.flag` before claude starts and removes it when claude exits. If Task Scheduler or a sleep kills the wrapper, the flag survives and the next run renames it to `FAILED-*.flag`, keeping its timestamp. The killed run's work may still have landed, so check its commits. A run that overlaps a live run renames that run's flag too, so check for overlap before treating a flag-only `FAILED` as a kill.
- `cadence.py delete` no longer counts `.gitignore` as a leftover in `_working/`.

### Upgrading
Existing workspaces keep their current `tools/` files, because the scaffolder never overwrites. To get these fixes, copy `tools/cadence-run.ps1` and `tools/cadence.py` from the plugin's `templates/` by hand. The new `.gitignore` does not untrack logs that were already committed, so run `git rm --cached "control-plane/cadences/*/_working/run-*.log"` once and commit the result.

## [0.5.0] — 2026-11-05

### Added
- **Vault-lint checks C13–C17 and C19.** C13 flags `confidence: high` with hedged prose. C14 flags doubled directories. C15 checks note shape (`summary`, `## Contents`, split candidates). C16 checks heading and block anchors. C17 checks requirement hubs. C19 checks `index.md` note types by folder depth and retires `> Part of:`. C18 is reserved.
- **Vault-lint is configurable by constants at the top of the file.** C15 scope defaults to `domain-knowledge/` at `warn`. `ANCHOR_WARN_PREFIXES` and `JURISDICTIONS` ship empty. C17 stays silent until a vault has requirement hubs.
- **`vault-lint check --prefix`, and `fix --check` / `--prefix`.** `check` now exits 1 on any `fail`-severity finding.
- **Optional requirement hubs**: schema in `_graph/index.md`, and `Mode: requirements` on the knowledge skill's `cartograph` action.
- **Queue and staging archives.** Scout moves `done` signals older than 30 days to `queue/_archive/`, and reports stale staging items with their state and next action. REJECT and MERGE now have defined end points. Adds `distillers/staging/README.md`.
- **`tools/cadence-run.ps1`**, a scaffolded helper for unattended local cadence runs through Windows Task Scheduler. It flags failures instead of failing silently, and `-PermissionFlag` is required.
- **Workstream action rules**: blueprint Data Inputs, chained research passes, the decisions-versus-data split in design, and a hand spot-check at validate for row-based deliverables.

### Changed
- **Renamed QRDBIV / RBIV to Payload Relay / Short Relay.** The enum values change from `qrdbiv` to `payload-relay` and from `rbiv` to `short-relay`. The tier docs now describe the tiers as one relay run at different lengths.
- **Index stubs emit `parent:` frontmatter** instead of `> Part of:`. Conventions drop `documentation-hub`.
- Distiller frontmatter gains `summary`.

### Fixed
- `workstream.py` keeps a file's line endings on every rewrite, and `check-step` matches a step's leading token, so a step citing `1.1` no longer matches.
- `workstream.py` no longer crashes on status values containing backslashes.
- Removed process residue from shipped prose.

### Upgrading
Existing workspaces keep their current `tools/` and `knowledge/` files, because the scaffolder never overwrites. To get the new linter, copy `tools/vault-lint.py` from the plugin's `templates/` by hand.

## [0.4.0] — 2026-08-13

### Changed
- **Single-source generation.** Both editions now generate from one canonical `src/` plus `vocabulary/{data-model,display}.yml` and `editions/*.yml` (`build/generate.py`), instead of being maintained as separately-drifting trees. `build/difflint.py` diffs generated output against shipped `plugins/*` on demand.
- **Two editions, not three.** Dropped `friendly-neighborhood-lite` — once the cast became lens/register data instead of 32 separate agent definitions, the curated-roster tier no longer earned its cost.
- **`review` → `checkpoint`** (objective action) and **`plan` → `blueprint`** (workstream-tier phase), including the CLI subcommand, frontmatter enum value, and filenames. Historical `reviews/*.md` and `_log/*.md` entries are unchanged.
- Allowlist now matches every shipped CLI exactly (`patrol.py` was shipped but unlisted); removed `Bash(cat|grep|find:*)`, which made the discouraged path the frictionless one.
- `marketplace.json` and both READMEs are now generated from `editions/*.yml`, not hand-written — closes a standing drift where published metadata described a vocabulary neither edition actually used.

### Fixed
- **Promotion gap**: this edition had drifted from `build/_generated/*` since the single-source rework began — stale `review`/`plan` action filenames, hand-drifted skill and template prose. Reconciled and promoted; this edition now matches generated output except a short documented exception list (hand-maintained top-level metadata, and `scripts/fn-*.sh`, where the generator still leaks themed content into this untethemed edition — a known generator gap recorded in `build/README.md`, not yet fixed).

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
- **Tier vocabulary:** eliminated the "initiative" tier; the three tiers are now objective → workstream → assignment, with ceremony sized to the tier.

### Fixed
- `log-decision` documented with positional arguments (`<name> "<decision>" "<rationale>"`) to match the CLI.
- `objective.py` no longer crashes when first run in a bare workspace (creates the portfolio index on demand).

### Security
- Closed an **in-process path-traversal class** that the deny-list and safety hooks structurally cannot catch: crafted (non-kebab) names could write or delete files outside the intended tree via the state CLIs (`objective`/`workstream`/`assignment`). All now reject any name that isn't plain kebab-case.
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
