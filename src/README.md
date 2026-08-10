# src/ — canonical plugin source

Single source of truth for all three shipped editions (`harness-core`,
`friendly-neighborhood-lite`, `friendly-neighborhood`). `build/generate.py`
(plan 3.5) reads this tree plus `vocabulary/data-model.yml`,
`vocabulary/display.yml`, and `editions/{core,lite,full}.yml`, and emits
each edition into `plugins/{name}/`.

**This tree is not yet wired to a generator.** 3.3 moved canonical content
into place; `plugins/*` still ship as they did before this restructuring and
remain the byte-reproduction target for 3.6. Do not delete or hand-edit
`plugins/*` before 3.5/3.6 land.

## Canonical source per directory

Where an edition's content is a superset or the only faithful copy, that
edition was used as the copy source. This is a provenance note, not a claim
that the copy is generation-ready as-is — see **Known gaps** below.

| `src/` path | Copied from | Why |
|---|---|---|
| `skills/{workstream,objective,assignment,cadence,knowledge,init-workspace}/` | `plugins/harness-core/skills/*` | Untethemed — content already matches the PINNED identifiers, no substitution needed to read it |
| `skills/{church-bell,creed,spider-sense,symbiote}/` | `plugins/friendly-neighborhood/skills/*` | Themed-only; full is the roster superset |
| `agents/*.md` (32) | `plugins/friendly-neighborhood/agents/` | Full is the roster superset — lite's 7 are a subset by name (`vocabulary/display.yml` `roster.lite`) |
| `hooks/hooks.json` | `plugins/harness-core/hooks/` | Confirmed byte-identical across all three editions (`diff -rq`) |
| `scripts/*` | `plugins/friendly-neighborhood/scripts/` | **3.4 line-diffed against core/lite** (`_working/script-divergence.md`): divergence is vocabulary substitution plus blocks gated by `features:` flags already in `editions/*.yml` (`observation_deck`, `doctrine_skills`) — no roster-count-dependent logic, no revision to 3.3 needed. Full's copy carries the superset of feature-gated blocks; the generator must strip them per edition (see gap below) |
| `templates/` (all except `.vscode/`) | `plugins/harness-core/templates/` | Untethemed, pinned folder names |
| `templates/.vscode/` | `plugins/friendly-neighborhood/templates/.vscode/` | Full-only feature (`observation_deck`/`vscode_workspace` in `editions/full.yml`) |
| `output-styles/friendly-neighborhood.md` | `plugins/friendly-neighborhood/` | Full's copy includes the screenplay section; lite's is a reduced variant (`output_style_screenplay: false` in `editions/lite.yml`) — **not yet reconciled, see gaps** |
| `themes/` | `plugins/friendly-neighborhood/` | Full-only feature |

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
