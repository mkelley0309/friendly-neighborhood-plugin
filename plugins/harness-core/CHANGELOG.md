# Changelog

All notable changes to this plugin are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/); versions follow [SemVer](https://semver.org/).

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
