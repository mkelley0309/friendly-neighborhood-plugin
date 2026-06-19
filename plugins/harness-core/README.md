# Harness Core

> An opinionated workflow + knowledge harness for Claude Code. Cheap by default; distill at every phase boundary.

The **un-themed** edition: all the capabilities, none of the costume. If you want the Spider-Man skin, install **`friendly-neighborhood-lite`** (light) or **`friendly-neighborhood`** (full) from the same marketplace.

## What makes it different

Most harnesses track tasks. This one tracks *why the work exists* and enforces how it closes:

- **Three tiers, not a flat list.** Objective (the long-lived why — a role, an annual goal, a career goal, with Key Results and a decisions log) → Workstream (heavy QRDPIV lifecycle, multi-session) → Task (lightweight, proportional admin only). Each tier has durable state; objectives carry an append-only decisions log that survives completion.
- **Progressive distillation.** Every phase boundary produces a compressed artifact handed to a fresh context — light on short work, hard on long work. Keeps understanding high and token cost low across multi-session efforts.
- **Peer-reviewed knowledge pipeline.** New content is scouted, harvested, and staged; it enters the vault only by review. Nothing auto-updates itself. The vault grows by admission, not accumulation.
- **A deterministic gate.** Hard, measurable concerns — tests, lint, budget, deny-list — run through `tools/gate.py` (exit-code GO/NO-GO). Soft judgments stay qualitative and recorded. No workstream closes on faith.
- **Determinism for the repeatable.** Any task done twice becomes a script. The orchestration CLIs (`workstream`, `objective`, `task`) are this principle applied to the harness itself.

## What you get

- **Three-tier orchestration** — `objective` → `workstream` → `task` (long-lived goal → heavy QRDPIV lifecycle → lightweight unit), each with a backing Python CLI and an auditable lifecycle.
- **A knowledge-vault pipeline** (`knowledge`) — scout → harvest → distill → cartograph → sync, into a linked markdown vault. No database, no lock-in, no Obsidian required (it's just markdown).
- **Workstream lifecycle** — a QRDPIV/RPIV framework (questions → research → design → plan → implement → validate → cleanup) with mandatory progressive distillation, fresh-context research handoffs, and a verification gate before close.
- **Observational hooks** — session/tool/stop logging + a recovery breadcrumb on failure, to `.claude/logs/`.
- **A statusline** surfacing the active workstream + phase and tier counts.
- **A workspace scaffolder** (`init-workspace`) that drops a complete, domain-neutral harness into your project.
- **Token discipline** — cheap models/effort by default, a soft concurrency budget, and distillation at every phase boundary.

No agent personas, no output style, no themes.

## Requirements

| Requirement | For | Notes |
|---|---|---|
| **Python 3.8+** | the orchestration CLIs (`workstream`/`objective`/`task`) | **stdlib only** — no `pip install`. Use whatever launcher you have (`python3`, `python`, or `py`). Always invoke with `-B` to suppress bytecode: `python -B tools/workstream.py ...`. `init-workspace` checks for it. |
| **bash** | hooks + statusline | built-in on macOS/Linux; Git Bash on Windows. If absent, hooks/statusline simply no-op. |
| **Obsidian** *(optional)* | nicer vault UX | the vault is plain markdown; Obsidian only adds graph/wikilink/Bases tooling. |

## Install

```bash
claude plugin marketplace add mkelley0309/friendly-neighborhood-plugin
claude plugin install harness-core@friendly-neighborhood
# then, in your project:
/harness-core:init-workspace
```

## Skills

Invoke as `/harness-core:<name>`.

| Skill | What it does |
|---|---|
| `init-workspace` | Scaffolds a fresh workspace from the bundled templates. Run this first. |
| `workstream` | Heavy QRDPIV lifecycle (questions → research → design → plan → implement → validate → cleanup) for complex multi-session work. |
| `task` | Lightweight unit with proportional admin (assignment/checklist/handoff/lessons). Promote to a workstream if it grows. |
| `objective` | Long-lived, review-cycle goal with Key Results, milestones, linked workstreams, and an append-only decisions log. |
| `knowledge` | The knowledge pipeline + linked vault: scout → harvest → distill → cartograph → sync. |
| `loop` | Run a prompt or skill on a recurring interval; native autonomous looping for long-running or polling work. |

`tools/gate.py` — the deterministic verification gate; run with `python -B tools/gate.py run`. Exits GO (0) or NO-GO (1) based on hard measurable checks (tests, lint, budget, deny-list). Called by the workstream lifecycle at the validate phase before close.

## License

MIT — see [LICENSE](LICENSE).
