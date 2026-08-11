# diff classification — step 3.6

Classifies every discrepancy in `build/difflint-report.md` (regenerated fresh after the 3.6
generator-bug fixes below) into:

- **bug-to-fix-everywhere** — generated (rule-correct) output is right; the shipped file has
  a real defect to fix next time it's touched.
- **genuine-edition-difference-as-config** — shipped legitimately differs because the
  generator hasn't been taught a real edition-specific feature yet; not a defect in either file.

Assembled from two independent classification passes (one per themed edition) plus a
harness-core pass, then corrected against the live generated output — one classifier claim
(`mission.py`'s compound identifiers were "already correct") turned out to be wrong on direct
inspection, which is why every finding below was re-verified rather than merged as-received.

## Generator defects found and fixed during this pass (no longer present in output)

Four of the raw findings weren't shipped-tree bugs or edition gaps at all — they were defects
in `build/generate.py` itself, now fixed (see the 3.6 commit for the full explanation of each):

1. **Runtime-crashing code**: pinned-word substitution had no guard against Python attribute
   access (`args.workstream`), desyncing it from the quote-guarded `argparse` dest string —
   would raise `AttributeError` in `workstream.py`'s `cmd_link`/`cmd_aside` and `objective.py`'s
   `cmd_link_workstream`. Fixed with a preceding-`.` guard.
2. **Compound identifiers silently never renamed**: `\b` word-boundary regex doesn't cross an
   underscore, so `ASSIGNMENTS_DIR`/`assignment_dir` and `CADENCES_DIR`/`cadence_dir` were never
   substituted in either non-pinned tier. Fixed with a letters-only boundary.
3. **`patrol.py`'s own `cadence: {name}` identity field** was being caught by the cadence
   counter-landmine guard meant only for `objective.py`'s unrelated review-frequency field, so
   generated output wrote `cadence: {name}` instead of `patrol: {name}` in its own home file.
   Fixed with an `own_tier_file` exemption.
4. **`/harness-core:` leaking into themed output**: the pinned-tier + `knowledge`/`init-workspace`
   skill files are sourced from `harness-core` and hardcode `/harness-core:` as their own
   slash-command prefix; the existing plugin-slug substitution only ran full→themed, not
   core→themed. Fixed with the symmetric case.

Also fixed: `build_settings_json` only ever removed the two `observation_deck` permission lines,
never added them — canonical `src/templates/.claude/settings.json` (copied from core) never had
them, so `full`'s `observation_deck: true` flag had nothing to add. Now inserts them when true.

**Verified, not asserted:** all four generated CLI files parse via `ast.parse`; zero
`harness-core` string remains in either themed edition's output; `patrol.py`'s identifiers and
frontmatter key are correct; `settings.json` matches shipped after CRLF normalization.

## Deferred to Phase 4, not a Phase 3 fix

- **`genuine-edition-difference-as-config` (severity: high, explicitly not a quick fix)** —
  `skills/{creed,symbiote,church-bell}/` are sourced from full (the 32-character roster
  superset) and reference the entire cast throughout — phase-council tables, cross-cutting
  advisor lists, auto-improvement-loop mentions. For `roster: 7` editions this leaks characters
  outside the edition's own roster (`silk`, `gwen`, `ham`, `robbie`, `jessica`, `punk`, `mj`,
  `aunt-may`, `ned`, `madame-web`, `vulture`, `kraven`, `osborn`, `sandman`, `lizard`,
  `octavius`, `scorpion`, `electro`, `venom`, `uncle-ben`, `cat`, `ben-reilly`, `peni` all
  appear in lite's generated `creed`/`symbiote`/`church-bell` output despite `plugin.json`'s own
  "Tiny roster only... no full cast" description). Shipped is arguably *more* correct here today
  (it correctly states "no other agents exist in this edition") than generated is. **This is
  plan Phase 4's own stated deliverable** — 4a.1 (21 lens data files with `phases:` frontmatter)
  and 4b.2 ("council tables generated from lens `phases:` frontmatter") — not a Phase 3
  mechanical-substitution bug. Left unfixed here deliberately; fixing it now would duplicate
  Phase 4 work with a throwaway mechanism before the real lens system exists.

## harness-core

### 1. Top-level plugin metadata files removed
**Classification:** genuine-edition-difference-as-config
**Files:** `CHANGELOG.md`, `LICENSE`, `README.md` (reported as "removed" — shipped only)
**Evidence:** Live directly under `plugins/harness-core/`, outside `src/`'s provenance table
(confirmed against `src/README.md`); the generator was never asked to produce them.

### 2. `plugin.json` author-object formatting
**Classification:** genuine-edition-difference-as-config
**Files:** `.claude-plugin/plugin.json`
**Evidence:** Diff is purely `"author": { "name": "Matt" }` (shipped, one line) vs.
pretty-printed three-line form (generated) — `json.dumps` indentation style only, no content
difference. Same cosmetic gap confirmed in all three editions.

### 3. `fn-*.sh` scripts missing the acting-persona / spider-sense mechanism entirely
**Classification:** genuine-edition-difference-as-config
**Files:** `scripts/fn-common.sh`, `scripts/fn-post-tool.sh`, `scripts/fn-pre-tool.sh`,
`scripts/fn-session-start.sh`, `scripts/fn-stop.sh`, `scripts/fn-subagent-stop.sh`
**Evidence:** Generated output adds the full `fn_speaker()` function, screenplay-style log
lines, and the spider-sense `DANGER` regex block in `fn-pre-tool.sh` — absent from shipped core
entirely, not just flag-gated. Bigger than a strippable marker block; needs its own
content-fork mechanism the generator doesn't have yet. Shipped core is correct as
minimal/undecorated; generator currently over-produces themed content for core.

## friendly-neighborhood-lite

### Added/removed — structural authoring gaps
**Classification:** genuine-edition-difference-as-config
- `skills/mission/actions/{complete,initiate}.md` (added, generated-only) — matches known gap
  #3: `assignment`/`cadence` have an `actions/` subfolder; shipped `mission`/`patrol` are
  hand-authored single-file `SKILL.md`s. Real authoring-structure difference.
- `CHANGELOG.md`, `LICENSE`, `NOTICE`, `README.md` (removed, shipped-only) — outside `src/`'s
  scope entirely, same as harness-core #1.

### `.claude-plugin/plugin.json`
- **bug-to-fix-everywhere** — description prose drift: shipped's wording has drifted from
  canonical over hand-edits (e.g. "no phase-council tables" while lite's shipped skills *do*
  ship phase-council lines — a pre-existing shipped-side self-contradiction).
- **genuine-edition-difference-as-config** — `author` object formatting, cosmetic only.

### Agent files — Voice/Observation-deck section
**Classification:** genuine-edition-difference-as-config
**Files:** `agents/{carnage,kingpin,mysterio,miguel,noir,peter}.md`
**Evidence:** Each shipped file is missing ~16–23 lines of `## Voice` + `## Observation deck`
content the generator adds. Same marker-mechanism gap as known gap #2, just not yet extended
to agent files.

### `agents/jameson.md`
**Classification:** bug-to-fix-everywhere
**Evidence:** Beyond the Voice/Observation-deck gap, the entire `description:` frontmatter and
body differ — shipped's old "adversarial QA / stress-tests before shipping" framing vs.
canonical's current "devil's advocate / grills poorly-shaped work" framing. Stale persona
content the canonical src has since evolved past.

### `scripts/scaffold.py`
**Classification:** bug-to-fix-everywhere
**Evidence:** Matches known gap #6 exactly — shipped's onboarding line omits the `campaign`
skill entirely and mislabels `mission` as "(a campaign)"; generated is correct and complete.

### `skills/campaign/*` — pinned-word corruption (folder/CLI names)
**Classification:** bug-to-fix-everywhere (grouped — this is the class README cites as its
worked example)
**Files:** `skills/campaign/SKILL.md`, `actions/cleanup.md`, `framework.md`,
`framework-templates.md`
**Evidence:** Shipped says `control-plane/campaigns/`, `campaign.py`, and "Child Missions and
Parent Objectives" where the pinned tier means these must read `control-plane/workstreams/`,
`workstream.py`, and "...Parent Responsibilities" — exactly the landmine
`vocabulary/data-model.yml`'s header describes. Also several `campaign`/`mission`/`objective`
vocabulary-drift instances in the framework templates ("Mission Status" → should read "Campaign
Status", table headers not updated post-rename).

### Persona-routing lines dropped in generated output
**Classification:** flagged separately — closest to genuine-edition-difference-as-config, but
generated may be the one that's wrong, not shipped
**Files:** `skills/campaign/actions/{implement,research,validate}.md`, `framework.md`
**Evidence:** Generated drops explicit routing to `peter`/`noir`/`jameson` (all *in* lite's own
7-person roster) in favor of generic "Sonnet subagent"/"Adversarial QA" phrasing. Unlike
stripping `gwen`/`ham`/`silk` (correctly absent from lite), stripping references to characters
who *are* in lite's roster looks like the generator over-genericizing persona routing
regardless of whether the character belongs to the edition — needs generator-side
verification before treating shipped as wrong here.

### `skills/creed/SKILL.md` — Council roster leakage
See "Deferred to Phase 4" above — this is the specific file most affected.

### Vocabulary/prose drift (grouped, simple)
**Classification:** bug-to-fix-everywhere
**Files:** `skills/{mission,patrol,origin-story}/SKILL.md`, `skills/responsibility/SKILL.md`
(stray `note_type: objective`, `tags: [objective,...]` should read `responsibility`),
`skills/spider-sense/SKILL.md`, `templates/.claude/rules/*.md`, `templates/constitution.md`,
`templates/control-plane/*/index.md`, `templates/knowledge/*`, `templates/tools/vault-lint.py`
**Evidence:** Consistent pattern — generated correctly substitutes the edition's own tier
vocabulary (`knowledge`→`web-archive` self-reference direction confirmed correct); shipped
retains pre-rename terms. One item (`vault-lint.py`'s `knowledge`/`web-archive` docstring
mention) flagged by the classifier for extra scrutiny — worth confirming it's a real skill
self-reference and not an unrelated `note_type` literal before fixing.

### Bespoke content richer in shipped than canonical
**Classification:** genuine-edition-difference-as-config
**Files:** `skills/responsibility/actions/{initiate,complete}.md`
**Evidence:** Shipped carries substantially more detailed, hand-authored content (full
shaping-questions script, verbatim frontmatter/section templates) than generated's terser
canonical version — genuine authoring depth beyond mechanical substitution, matching known gap
#8's pattern but in the direction of shipped being richer, not just differently worded.

### `templates/_addenda/claude-code.md`
**Classification:** mixed
- **genuine-edition-difference-as-config** — generated trims the "Key skills" bullet list and
  removes the "Dissent council"/"Symbiote" special-case callout; reads as intentional
  lite-specific trimming the canonical/full src hasn't been asked to model per-edition yet.
- **bug-to-fix-everywhere** — simple word-swap bugs layered on top (e.g. "sub-task" should read
  "sub-mission", "Task type" header should read "Mission type").

### `templates/.claude/statusline.sh`
**Classification:** bug-to-fix-everywhere, with one item needing a second look
**Evidence:** Shipped's script logic conflates "mission" and "workstream" labeling
(`RESP`/`MISS`/`PTRL` variables counting `objectives`/`workstreams`/`patrols` but labeling
workstreams "missions"). Generated is internally consistent. One caveat: generated's script
queries a `$CP/tasks` directory that doesn't exist in this control-plane layout (should
likely be `patrols`) — flag as a possible generator content bug worth a second look before
treating the whole file as a clean "shipped is stale" case.

## friendly-neighborhood (full)

### Added/removed — same structural gaps as lite
**Classification:** genuine-edition-difference-as-config
- `skills/mission/actions/{complete,initiate}.md` (added) — same `actions/` subfolder gap as
  lite.
- `CHANGELOG.md`, `LICENSE`, `NOTICE`, `README.md` (removed) — outside `src/` scope.
- `templates/.claude/scripts/{agent-colors,agent-log,observe}.sh` (removed, shipped-only) —
  back the observation-deck VS Code feature; `src/` has no scripts subtree for this mechanism
  yet, consistent with the Council-leakage gap above (observation-deck is bigger than the
  current marker system models).

### Vocabulary/reference bugs (grouped)
**Classification:** bug-to-fix-everywhere
**Files:** `agents/osborn.md` ("the objective seems worth it" should read "responsibility"),
`skills/campaign/SKILL.md` (same worked-example corruption as lite's), `skills/creed/SKILL.md`,
`skills/patrol/SKILL.md`, `skills/responsibility/*`, `templates/.claude/rules/*.md`,
`templates/CLAUDE.md`, `templates/constitution.md`, `templates/control-plane/*/index.md`,
`templates/knowledge/*`, `templates/tools/{patrol,workstream}.py` docstrings/help text,
`templates/_addenda/claude-code.md` — pervasive stale pre-rename vocabulary, same pattern as
lite's equivalent files.
Also: `templates/tools/vault-lint.py`'s `note_type` docstring mention — same "verify before
fixing" caveat as lite's copy.
`.claude-plugin/plugin.json` author-object formatting — cosmetic only, same as the other two
editions.

### Bespoke content present only in shipped
**Classification:** genuine-edition-difference-as-config
**Files:** `skills/campaign/actions/{implement,questions,research,validate}.md`, `framework.md`,
`skills/mission/SKILL.md`, `templates/_addenda/claude-code.md`
**Evidence:** Same shape as lite's persona-routing findings — shipped carries named
character-routing prose (`miles`/`ben-reilly`/`noir`/`silk`/`peter`/`gwen`/`robbie`/`jameson`/
`cat` security-red-team step) that generated's canonical prose is generic about. Full's roster
is 32, so — unlike lite — every character named here *is* in-roster; this is purely "canonical
src hasn't had this hand-authored routing detail merged back into it yet," a real authoring gap
matching known gap #8, not a roster-leakage problem.

### `skills/origin-story/SKILL.md`
**Classification:** genuine-edition-difference-as-config
**Evidence:** Shipped's onboarding interview (conducted by `robbie`, three structured
questions, observation-deck walkthrough) is bespoke hand-authored content beyond what
mechanical vocabulary substitution produces.

### `templates/.claude/rules/secret-identity.md`, `templates/secret-identity/CLAUDE.md`
**Classification:** genuine-edition-difference-as-config
**Evidence:** Confirmed by `src/README.md` known gap #4 — bespoke themed prose ("What's behind
the mask..."), not derivable from `personal.md` by substitution.

### `templates/constitution.md` — "Operating Principles" section
**Classification:** genuine-edition-difference-as-config (reverse direction — generated has
more than shipped)
**Evidence:** A 7-item doctrine list present in canonical/generated is entirely absent from
shipped — additive canonical content not yet hand-merged into the shipped constitution.

### `templates/.claude/settings.json` and its two backing scripts
**FIXED during this pass** — see "Generator defects found and fixed" above. No longer a
discrepancy.

---

Regenerated after all fixes: `harness-core` 0/3/7, `friendly-neighborhood-lite` 2/4/58,
`friendly-neighborhood` 2/7/49 (added/removed/changed). Frontmatter-key check: **PASS**.
