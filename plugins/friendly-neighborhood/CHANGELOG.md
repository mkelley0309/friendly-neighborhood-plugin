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

### Added
- **Six agents** (cast now 32): `peni` (builder — fans out one SP//dr unit per independent worktree, then reconciles), `ham` (adversarial validation — catches work that's "green for the wrong reason"), `jessica` (root-cause investigator), `punk` (anti-ceremony dissent) — spideys; `robbie` (origin-story interviewer + constructive design questions) — support; `cat` (Black Cat — security red-team whose delight is the alarm) — villain.
- **Live observation deck** (full edition only): each agent narrates one themed, color-coded line per significant step to per-group streams that three VS Code tail panes follow (spideys / support / villains). Per-character palettes, a black-suit override while a spidey wears the symbiote, and a portable single-terminal fallback (`observe.sh`). Scripts under `.claude/scripts/` (`agent-log.sh`, `agent-colors.sh`, `observe.sh`) plus the VS Code "Observation Deck" task.
- Phase-council wiring for the new agents: `peni` drives Implement and is a Patrol build specialist; `gwen` + `ham` co-own Validate; `jessica` and `punk` are cross-cutting triggers (summoned on failure / on over-built process).

### Changed
- **Tier vocabulary:** eliminated the "initiative" tier; the internal tiers are now objective → workstream → task (themed: responsibility → mission → patrol), with ceremony sized to the tier.
- **Role sharpening:** `gwen` is a first-class validation driver (runs the work rather than reasoning about it); `jameson` grills poorly-shaped work as devil's advocate; `sandman` detects under-shaped/formless work.
- Support advisors scoped read-only (`disallowedTools`) where their job is counsel, not edits; several villains run on `haiku` where dissent is cheap.

### Fixed
- **Agent discovery:** flattened the roster into a single `agents/` directory. Claude Code discovers plugin agents from `agents/*.md` and does **not** recurse into subfolders, so the prior `agents/{spideys,support,villains}/` layout left the entire cast undiscovered (`plugin details` reported 0 agents). The spideys/support/villains grouping is now carried by the creed, `agent_group`, and the three deck streams.
- `log-decision` documented with positional arguments (`<name> "<decision>" "<rationale>"`) to match the CLI — the earlier `--decision`/`--rationale` flags never existed.
- `objective.py` no longer crashes when first run in a bare workspace (creates the portfolio index on demand).

### Security
- Closed an **in-process path-traversal class** that the deny-list and spider-sense hook structurally cannot catch: crafted (non-kebab) names could write or delete files outside the intended tree via the state CLIs (`workstream`/`patrol`/`task`/`objective`), the hook helper `fn_suit_off`, and the deck logger `agent-log.sh` (which additionally exposed a truncating-write primitive). All now reject any name that isn't plain kebab-case.
- `gate.py` rejects a check with an empty command (previously a vacuous PASS — a gate that verified nothing).

## [0.1.0] — 2026-06-06

Initial release.

### Added
- Three-tier orchestration: **responsibility** (objective), **mission** (initiative), **patrol** (workstream) with backing CLIs.
- Knowledge-vault pipeline (**web-archive**): scout → harvest → distill → cartograph → sync.
- Spider-cast agent roster (three folders): 7 drivers (`spideys/`), 6 advisors (`support/`), 13 villain dissent reviewers (`villains/`).
- Contextual dissent: a phase-council map (creed) wires each phase to only the advisors/critics whose concern is live; each support advisor is the constructive counter to a villain.
- Three mechanics: the Everyman budget, the symbiote (escalation that returns to baseline), the villain dissent council.
- Skills: patrol, responsibility, mission, web-archive, creed, spider-sense, symbiote, church-bell, origin-story.
- Observational hooks (logging/recovery/snapshot) plus spider-sense (PreToolUse) and church-bell (SubagentStop).
- Screenplay output style: the session renders like a script (name-prefixed dialogue, code/data as exhibits), each of the 26 agents carries a distinct character voice, and the hooks write screenplay-style logs (`PETER > Bash`, `=== Scene opens ===`, church-bell on exit).
- Two themes (spidey / black-suit) and a statusline.
- `NOTICE` + README disclaimer: unofficial, noncommercial Marvel homage; ships no Marvel art/logos.
- `origin-story` workspace scaffolder bundling a domain-neutral harness in `templates/`.
