# Changelog

All notable changes to this plugin are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/); versions follow [SemVer](https://semver.org/).

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
