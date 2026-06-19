# 🕷 Friendly Neighborhood (Lite)

> The lean themed edition. *Great power, great responsibility, lean token budget.*

The bare-minimum Spider-Man harness built around real differentiators: a **three-tier work model** (responsibility → mission → patrol) with progressive distillation at every handoff, a **peer-reviewed knowledge vault pipeline**, and an **honest two-track decision mechanic** — hard signals run through a deterministic gate (`tools/gate.py`); soft signals get affirmative villain dissent and a recorded rationale, never a fake score. No full cast, no per-character screenplay, no themes, no phase-council. If you want the whole show, install **`friendly-neighborhood`** (full). If you want no theme at all, install **`harness-core`**.

## What's in it

- **Three-tier orchestration** — `responsibility` (long-lived why: role / annual objective / career goal) → `mission` (multi-session, multi-handoff) → `patrol` (single work unit), with backing CLIs and auditable lifecycles.
- **Progressive distillation** — every handoff compresses to a dense artifact; understanding stays high, tokens stay low.
- **Knowledge vault pipeline** (`web-archive`) — scout → harvest → distill → cartograph → sync, admitted only by peer review.
- **Decision mechanic** — hard concerns → `tools/gate.py` (deterministic gate, pass/fail); soft concerns → villain dissent + recorded judgment.
- **The symbiote** — turn-limited self-escalation (`symbiote_max_turns`), killed by the church bell on overrun or dissent.
- **A tiny roster (7 agents):** `peter` (driver), `miguel` (architect), `noir` (debugging), `jameson` (QA) · critics `carnage`, `mysterio`, `kingpin`.
- **The voice** — the Peter-Parker output style (register only; no per-character screenplay).
- Observational hooks + statusline + the `origin-story` scaffolder.
- **`stakeout`** — native autonomous looping (`/loop` + `schedule`) for long-running unattended work.

## Requirements & install

Same as the full edition — **Python 3** for the CLIs (stdlib only), bash for hooks, Obsidian optional.

```bash
claude plugin marketplace add mkelley0309/friendly-neighborhood-plugin
claude plugin install friendly-neighborhood-lite@friendly-neighborhood
# then, in your project:
/friendly-neighborhood-lite:origin-story
```

## License & disclaimer

MIT (original code) — see [LICENSE](LICENSE). **Unofficial fan project**; Spider-Man and related characters are © & ™ Marvel / Disney. Not affiliated or endorsed; ships no Marvel art or logos. See [NOTICE](NOTICE).
