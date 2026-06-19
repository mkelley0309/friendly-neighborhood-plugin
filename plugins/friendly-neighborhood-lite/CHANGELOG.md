# Changelog

All notable changes to this plugin are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/); versions follow [SemVer](https://semver.org/).

## [0.2.0] — 2026-06-19

### Changed
- **Tier vocabulary:** eliminated the "initiative" tier; the internal tiers are now objective → workstream → task (themed: responsibility → mission → patrol), with ceremony sized to the tier.

### Fixed
- **Agent discovery:** flattened the roster into a single `agents/` directory. Claude Code discovers plugin agents from `agents/*.md` and does **not** recurse into subfolders, so the prior `agents/{spideys,support,villains}/` layout left the 7-agent roster undiscovered.
- `log-decision` documented with positional arguments (`<name> "<decision>" "<rationale>"`) to match the CLI — the earlier `--decision`/`--rationale` flags never existed.
- `objective.py` no longer crashes when first run in a bare workspace (creates the portfolio index on demand).

### Security
- Closed an **in-process path-traversal class** that the deny-list and spider-sense hook structurally cannot catch: crafted (non-kebab) names could write or delete files outside the intended tree via the state CLIs (`objective`/`workstream`/`patrol`). All now reject any name that isn't plain kebab-case.
- `gate.py` rejects a check with an empty command (previously a vacuous PASS — a gate that verified nothing).

## [0.1.0] — 2026-06-06

Initial release. The lean themed edition.

### Added
- Three-tier orchestration: **responsibility** (objective), **mission** (initiative), **patrol** (workstream) with backing CLIs.
- Knowledge-vault pipeline (**web-archive**): scout → harvest → distill → cartograph → sync.
- A **tiny Spider-cast** (7 agents): drivers `peter`, `miguel`, `noir` (spideys); advisor `jameson` (support); villain critics `carnage`, `mysterio`, `kingpin` (villains).
- Three mechanics: the Everyman budget, the symbiote (escalation that returns to baseline), and the villain dissent council (a critic's *approval* is the alarm).
- Skills: patrol, responsibility, mission, web-archive, creed, spider-sense, symbiote, church-bell, origin-story.
- Observational hooks (logging/recovery/snapshot) plus spider-sense (PreToolUse) and church-bell (SubagentStop).
- Character voices for the roster, and screenplay-style hook logs (`PETER > Bash`, `=== Scene opens ===`, church-bell on exit).
- A statusline.
- `NOTICE` + README disclaimer: unofficial, noncommercial Marvel homage; ships no Marvel art/logos.
- `origin-story` workspace scaffolder bundling a domain-neutral harness in `templates/`.

> The full 32-agent cast, the contextual phase-council, the live observation deck, and the color themes live in the `friendly-neighborhood` edition.
