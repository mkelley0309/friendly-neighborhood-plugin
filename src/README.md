# src/ — canonical plugin source

Single source of truth for both shipped editions (`harness-core`,
`friendly-neighborhood` — [D24] dropped the third, `friendly-neighborhood-lite`, since the
roster axis collapsed to binary once the cast became lens/register data rather than 32 separate
agent definitions). `build/generate.py` (plan 3.5) reads this tree plus
`vocabulary/data-model.yml`, `vocabulary/display.yml`, and `editions/{core,full}.yml`, and emits
each edition into `build/_generated/{name}/` (`python -B build/generate.py`); `build/difflint.py`
reports discrepancies against the currently-shipped `plugins/{name}/` trees, which remain the
reproduction reference and are not overwritten automatically — promote fixes by hand (or script)
after reviewing the diff, per the pattern used throughout the 5.1/5.2/5.3 backfill.

## Canonical source per directory

Where an edition's content is a superset or the only faithful copy, that
edition was used as the copy source. This is a provenance note, not a claim
that the copy is generation-ready as-is — see **Known gaps** below.

| `src/` path | Copied from | Why |
|---|---|---|
| `skills/{workstream,objective,assignment,cadence,knowledge,init-workspace}/` | `plugins/harness-core/skills/*` | Untethemed — content already matches the PINNED identifiers, no substitution needed to read it |
| `skills/{church-bell,creed,spider-sense,symbiote}/` | `plugins/friendly-neighborhood/skills/*` | Themed-only; full is the roster superset |
| `agents/*.md` | `plugins/friendly-neighborhood/agents/` | Pre-Phase-4 provenance note (32 files); superseded by the Phase 4 gate — canonical source is now `src/agents/` (6 real delegations) + `src/lenses/` (26) + `src/registers/` (4), not a copy from `plugins/*` at all |
| `hooks/hooks.json` | `plugins/harness-core/hooks/` | Confirmed byte-identical across both editions (`diff -rq`) |
| `scripts/*` | `plugins/friendly-neighborhood/scripts/` | **3.4 line-diffed against core/lite** (`_working/script-divergence.md`): divergence is vocabulary substitution plus blocks gated by `features:` flags already in `editions/*.yml` (`observation_deck`, `doctrine_skills`) — no roster-count-dependent logic, no revision to 3.3 needed. Full's copy carries the superset of feature-gated blocks; the generator must strip them per edition (see gap below) |
| `templates/` (all except `.vscode/`, `.claude/scripts/`, `CLAUDE.md`) | `plugins/harness-core/templates/` | Untethemed, pinned folder names |
| `templates/.vscode/` | `plugins/friendly-neighborhood/templates/.vscode/` | Full-only feature (`observation_deck`/`vscode_workspace` in `editions/full.yml`) |
| `templates/.claude/scripts/` (`roster-colors.sh`, `roster-log.sh`, `observe.sh`) | `plugins/friendly-neighborhood/templates/.claude/scripts/` | Observation-deck narration — full-only (`observation_deck`); gated in `build_templates()` the same way as `.vscode/`. **5.1 backfill**: this directory was entirely absent from `src/` before — the generator could not reproduce it for any edition, silently dropping the feature the moment `build/_generated/*` was ever promoted into `plugins/*`. `roster-colors.sh`'s `roster_group()` also needed the 5 new 4e.1 lens names added (`jackal`/`chameleon`/`silver-sable`/`spider-slayers`/`tinkerer` → villains). **`observation-deck-roster-rename` (2026-08-13)**: renamed `agent-colors.sh`/`agent-log.sh`/`agent_group()`/`agent_paint()`/`.claude/logs/agents/` to `roster-*` — "agent" now names only `src/agents/`'s 5 files, but the deck also narrates registers and dissent lenses |
| `templates/CLAUDE.md` | folded from `plugins/harness-core/templates/{constitution.md,_addenda/claude-code.md}` (structural preamble: Layout/Session/Context/Boundaries/Session Locus/Subagent Delegation) + `plugins/friendly-neighborhood/templates/CLAUDE.md` (themed doctrine body: Operating Principles onward) | **5.1 backfill**: `constitution.md` + `_addenda/claude-code.md` were the pre-Phase-2a.2 three-file pointer pattern Workspace itself already folded away; `src/templates/CLAUDE.md` still had it, and its themed doctrine body was leaking unstripped into every edition including `harness-core` (confirmed: generated `harness-core` output contained "Agent Venom"/"Silk"/`web-crawl`, a direct violation of `editions/core.yml`'s "no theme"). Fixed by folding the structural preamble into one `CLAUDE.md` per Workspace's current shape (including its [C1] pruning of concurrency caps/per-model budgets — restored as a short paragraph here since, unlike Workspace, `init-workspace`'s onboarding step actually edits this content) and gating the themed doctrine body behind `<!-- FEATURE:themed_doctrine:start/end -->`, keyed off `vocab.themed` rather than a real `editions/*.yml` entry (no edition needs to toggle it independently of `display: none` vs. `spider-man`) |
| `output-styles/friendly-neighborhood.md` | `plugins/friendly-neighborhood/` | Full's copy includes the screenplay section; lite's is a reduced variant (`output_style_screenplay: false` in `editions/lite.yml`) — **not yet reconciled, see gaps** |
| `themes/` | `plugins/friendly-neighborhood/` | Full-only feature |

## Resolved at 5.1 (harness-consolidation backfill)

Phases 0.5–2 of the `harness-consolidation` workstream restructured `Workspace/` itself (one root
`CLAUDE.md`, `.claude/rules/*.md`, `_harness/` and `outputs/` at the workspace root, a Python
statusline, `_now.md` deleted) — but nothing in the original plan carried those same structural
changes into this scaffold, since `src/templates/` was copied from the **pre-restructure** shipped
trees at 3.3, before any of Phase 1/2's work landed. Backfilled at 5.1: `templates/_now.md`
deleted; `templates/constitution.md` + `templates/_addenda/` folded into `templates/CLAUDE.md`
(see provenance table above); `templates/control-plane/outputs/` moved to `templates/outputs/`;
`templates/_harness/friction.md` added (seeded empty, unlike Workspace's live ledger);
`templates/.claude/statusline.sh` replaced with `templates/.claude/statusline.py` (ported from
Workspace's own — fully portable, no Workspace-specific paths). `templates/.claude/settings.json`
gained `Edit`/`Write` allow entries for `_harness/**` and `outputs/**` and lost the now-dead
`_now.md` entries. Six files with scattered `_addenda/claude-code.md`/`constitution.md`
cross-references (`scripts/fn-session-start.sh`, `scripts/scaffold.py`,
`skills/init-workspace/SKILL.md`, `skills/workstream/SKILL.md`,
`skills/workstream/actions/implement.md`, `skills/workstream/framework.md`,
`templates/.claude/rules/{control-plane,projects}.md`) were repointed at the new locations.
Promoted directly into `plugins/*` (narrow, self-contained changes — not the broader
`build/_generated/*` → `plugins/*` promotion this same pass found still missing; see the
`build_marketplace_json()`-adjacent note in `build/README.md` and the workstream friction log).

## Known gaps — deferred to 3.4/3.5/3.6, not resolved by this copy

- **Tier skill action files are not vocabulary-only diffs from their themed
  counterparts.** Word-substituting `campaign/actions/plan.md` back to
  `workstream` vocabulary and diffing against
  `harness-core/skills/workstream/actions/plan.md` leaves exactly one
  residual block: a `**Phase council**` line naming the edition's own agent
  roster. The generator needs a mechanism to inject that block for themed
  editions (sourced from each edition's roster, not stored as static src
  content) — this file's copy of the tier skills carries **core's** content
  only, without that block. 3.5 must design the injection, not assume the
  src copy is complete as shipped.
- **`output-styles/friendly-neighborhood.md`**: full and lite are not a
  strict superset/subset — lite's file omits the "Format: the script"
  section outright rather than being generatable from full's copy by simple
  truncation-by-flag (confirmed: `diff` shows the missing block is
  contiguous and toggleable, but this has not been verified against every
  other line in the file). Treat `output_style_screenplay` as a real
  section-inclusion flag to implement in 3.5, not decoration.
- **`scripts/*`**: 3.4 resolved the vocabulary-vs-logic question (see table
  above) — divergence is vocabulary plus feature-flag-gated blocks, not
  roster-dependent logic, so `editions/*.yml` needs no revision. The
  generator (3.5) still needs the conditional-block-injection mechanism
  described below (same shape as the phase-council injection) to strip the
  `observation_deck` and `doctrine_skills` blocks for editions where those
  flags are false, since `src/` currently holds full's superset copy.
- **Doctrine skill content (`church-bell`, `creed`, `spider-sense`,
  `symbiote`) between lite and full**: confirmed to differ (`diff -rq`,
  see `_working/generation-diff-triage.md`) but not yet line-diffed for
  vocabulary-only vs. real content drift. Full's copy is what's in `src/`
  today; lite's version has not been reconciled.

See `control-plane/workstreams/harness-consolidation/_working/generation-diff-triage.md`
(in the `Workspace/` root repo) for the running list of discrepancies this
restructuring has surfaced.
