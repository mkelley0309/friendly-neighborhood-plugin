# Friendly Neighborhood — a Claude Code harness, in two editions

This repository is a **Claude Code plugin marketplace**. It ships one opinionated workflow + knowledge harness, themed or not — install exactly one.

```bash
claude plugin marketplace add mkelley0309/friendly-neighborhood-plugin
claude plugin install <edition>@friendly-neighborhood
```

| Edition (`<edition>`) | Theme | What it is |
|---|---|---|
| [`harness-core`](plugins/harness-core) | none | The capabilities, none of the costume. Three-tier orchestration (`objective → workstream → assignment`) + knowledge-vault pipeline, observational hooks, statusline, scaffolder. Original naming, **no agent personas**. |
| [`friendly-neighborhood`](plugins/friendly-neighborhood) | full | The whole show: a **38-character cast** (6 real delegations, 4 zero-spawn registers, 26 dissent lenses), contextual phase-council, screenplay output, a live per-character observation deck, themes, and all three moral mechanics. |

Both share the same spine: a QRDBIV/RBIV lifecycle (objective/responsibility → workstream/campaign → assignment/mission, plus cadence/patrol for recurring work) with progressive distillation, a peer-reviewed knowledge vault, deterministic Python CLIs for state, and a `*:init-workspace` / `*:origin-story` scaffolder that drops a working, domain-neutral harness into your project. They differ only in how much theme rides on top — see [D24] in the harness-consolidation workstream's design log for why a third, roster-reduced "lite" tier was dropped: post-consolidation the cast is lens/register data applied on demand, not 32 separate agent definitions, so a curated roster no longer saves meaningful standing cost.

## Which one?

- **Just want the workflow + knowledge system?** → `harness-core`.
- **Want the full character-driven experience** (dissent lenses, screenplay logs, the cast)? → `friendly-neighborhood`.

## Requirements

**Python 3.8+** (stdlib only — no `pip`) for the orchestration CLIs; **bash** for hooks/statusline (Git Bash on Windows; degrades gracefully if absent); **Obsidian** optional for vault UX.

## License & disclaimer

Original code: MIT — see [LICENSE](LICENSE). The themed edition is an **unofficial, noncommercial Spider-Man fan homage** — not affiliated with or endorsed by Marvel/Disney, and it ships no Marvel artwork or logos. See [NOTICE](NOTICE). `harness-core` contains no themed content.
