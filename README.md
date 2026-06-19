# Friendly Neighborhood — a Claude Code harness, in three editions

This repository is a **Claude Code plugin marketplace**. It ships one opinionated workflow + knowledge harness at **three levels of theming** — install exactly one.

```bash
claude plugin marketplace add mkelley0309/friendly-neighborhood-plugin
claude plugin install <edition>@friendly-neighborhood
```

| Edition (`<edition>`) | Theme | What it is |
|---|---|---|
| [`harness-core`](plugins/harness-core) | none | The capabilities, none of the costume. Three-tier orchestration (`objective → workstream → task`) + knowledge-vault pipeline, observational hooks, statusline, scaffolder. Original naming, **no agent personas**. |
| [`friendly-neighborhood-lite`](plugins/friendly-neighborhood-lite) | light | The harness + the Spider-Man skin and voice, a **tiny roster** (peter, miguel, noir, jameson + a few critics), and the three mechanics. No full cast, screenplay, themes, or phase-council. |
| [`friendly-neighborhood`](plugins/friendly-neighborhood) | full | The whole show: **32-agent Spider-cast**, the 14-villain dissent council, contextual phase-council, screenplay output, a live per-character observation deck, themes, and all three moral mechanics. |

All three share the same spine: a QRDPIV/RPIV mission lifecycle (objective → workstream/mission → task/patrol) with progressive distillation, a peer-reviewed knowledge vault, deterministic Python CLIs for state, and a `*:init-workspace` / `*:origin-story` scaffolder that drops a working, domain-neutral harness into your project. They differ only in how much theme rides on top.

## Which one?

- **Just want the workflow + knowledge system?** → `harness-core`.
- **Want it fun but lean?** → `friendly-neighborhood-lite`.
- **Want the full character-driven experience** (dissent council, screenplay logs, the cast)? → `friendly-neighborhood`.

## Requirements

**Python 3.8+** (stdlib only — no `pip`) for the orchestration CLIs; **bash** for hooks/statusline (Git Bash on Windows; degrades gracefully if absent); **Obsidian** optional for vault UX.

## License & disclaimer

Original code: MIT — see [LICENSE](LICENSE). The two themed editions are an **unofficial, noncommercial Spider-Man fan homage** — not affiliated with or endorsed by Marvel/Disney, and they ship no Marvel artwork or logos. See [NOTICE](NOTICE). `harness-core` contains no themed content.
