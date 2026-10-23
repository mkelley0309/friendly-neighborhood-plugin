# build/ — the generator (plan 3.5)

`build/generate.py` reads `src/` + `vocabulary/{data-model,display}.yml` +
`editions/{core,full}.yml`, and emits each edition into
`build/_generated/{plugin-name}/`. `build/difflint.py` compares that output
against the currently-shipped `plugins/{edition}/` trees and writes
`build/difflint-report.md`.

**Two editions, not three** — [D24] dropped `friendly-neighborhood-lite`: the roster axis
collapsed to binary (`0`/full-cast) once the cast became lens/register data instead of 32
separate agent definitions, so a curated-roster tier no longer earns its cost. Historical
sections below still reference `lite` where they document *why* a decision was made at the time —
left as written rather than scrubbed, per this repo's own "history stays as written" policy.

`build/phase-council.yml` is **no longer read by the generator** (plan
4b.2) — it's kept on disk as a reference fixture only. See "Phase council
generation" below.

**Neither script touches `plugins/*`.** That tree is the byte-reproduction
reference target for step 3.6 (a separate step, not this one) — it stays
untouched so a human can diff against it.

**Exception (plan 5.1):** `build_marketplace_json()` writes directly to the
live `.claude-plugin/marketplace.json` at repo root — that file isn't part
of the `plugins/*` byte-reproduction pipeline (it isn't per-edition, and
nothing in `src/` sources it), so there's no staging copy to diff against.
It overlays each plugin's `description` from `editions/{name}.yml`
`plugin.description` — the same text already promoted into each shipped
`plugin.json` — onto the existing file, preserving `name`/`owner`/
`metadata`/`source`/`version`. `difflint.py`'s `check_marketplace()` verifies
the result matches `editions/*.yml` word-for-word.

**Known gap, found at 5.1, not fixed here:** `build/_generated/*` (the
canonical `src/`-derived output) has never been promoted into `plugins/*` —
no plan step schedules that copy. `plugins/friendly-neighborhood/agents/`
still ships the pre-Phase-4 32-file roster (14 separate villain agents,
inverted dissent polarity) while `src/agents/` has 6 files and the
lens/register carrier model. Because of this, 5.1's README fixes are scoped
to facts that are wrong **relative to what's actually shipped in `plugins/*`
today** (the `objective → workstream → task` tier-arrow bug, the lite
edition's stale "no phase-council" claim) — not to the future state
`src/` already describes. Rewriting README prose to describe the
lens/register architecture before `plugins/*` actually ships it would trade
one drift for another. The promotion itself needs its own step (byte-diff
`build/_generated/*` against `plugins/*` one more time, classify every
remaining discrepancy the way 3.6 did, then copy) before any README can
honestly describe the new cast — flagged in the workstream's friction log
rather than attempted here.

Run:

```
python build/generate.py
python build/difflint.py
```

## How it works

1. Load `vocabulary/data-model.yml` (pinned identifiers), `vocabulary/display.yml`
   (templated vocabulary), and the edition's own `editions/{name}.yml`.
2. Build a `Vocab` object per edition — three substitution tables:
   - **non-pinned tiers** (`assignment`/`cadence`): full identifier swap
     (folder, CLI filename, frontmatter key, prose — all together), no guards,
     safe to run on path segments and file content alike.
   - **pinned tiers** (`objective`/`workstream`): prose-only swap, heavily
     guarded (see "The pinned-word guards" below) so a folder name, CLI
     filename, or frontmatter key is never corrupted.
   - **non-tier skill self-references** (`init-workspace`/`knowledge`):
     narrow patterns only (`name:`, `# Skill:`, `` /plugin:skill ``, `` `skill` ``)
     — never a blanket word substitution, since "knowledge" and "init" are
     common English/code words. Runs in **both directions** depending on
     which core edition a given `src/` file was copied from (see
     "Bidirectional skill substitution" below).
3. Copy each src subtree through its dedicated `build_*` function (tier
   skills, non-tier skills, doctrine skills, agents, scripts, templates,
   output-styles, themes, hooks, plugin.json).
4. Write to `build/_generated/{plugin.name}/`.

## The marker convention

Two forms, both meaning "this block exists only when a named feature is
on":

- Shell/Python: `# FEATURE:<flag>:start` … `# FEATURE:<flag>:end`
- Markdown: `<!-- FEATURE:<flag>:start -->` … `<!-- FEATURE:<flag>:end -->`

`<flag>` is a key from the edition's `features:` map in `editions/*.yml`
(`observation_deck`, `doctrine_skills` — list-truthiness, i.e. non-empty
list counts as "on"). `strip_markers()` in `generate.py` removes the block
verbatim (nothing added, nothing removed beyond the marker lines themselves)
when the flag is off, and removes only the marker lines (keeping the body)
when it's on.

**Blank-line spacing quirk, worth knowing before adding a new marker:**
because the strip is a literal "remove exactly this span," a block that
sits between two blank lines when present must have ITS OWN leading blank
line moved to be the *first line of the body*, not left outside the
markers — otherwise dropping the block leaves two blank lines stacked (kept
case) or none at all (EOF case). See `src/scripts/fn-session-start.sh`
(mid-file case) and `src/scripts/fn-common.sh` (EOF case) for the two
worked examples; both are one-line adjustments once you see the pattern.

Markers were added to: `src/scripts/fn-session-start.sh`,
`fn-subagent-stop.sh`, `fn-common.sh` (the last wasn't in the original scope
of three gaps handed off, but is the exact same mechanism and closes a real
lite-vs-full diff — see Known Gaps for the other `fn-*.sh` files that were
**not** similarly fixed), `scaffold.py` (partially — see below), and
`src/output-styles/friendly-neighborhood.md`.

**5.1 addition:** `build_templates()` (used for the general `templates/` tree, as opposed to
`copy_file_substituted()` used for skills/output-styles/doctrine-skills) only ever stripped
`.py`/`.sh` markers with `MARKER_RE_SH` — it had no path for `.md` markers with `MARKER_RE_MD` at
all, unlike `copy_file_substituted()` which already branched on `src.suffix`. Extended to match,
and used immediately for `templates/CLAUDE.md`'s new `themed_doctrine` marker (see
`src/README.md`'s provenance table) — a synthetic feature key derived from `vocab.themed` rather
than a real `editions/*.yml` entry, since no edition needs to toggle it independently of the
display axis.

`settings.json` does **not** use markers (JSON has no comment syntax) — its
two observation-deck-gated permission lines are added/removed by
`build_settings_json()` working on the parsed JSON structure directly.

## scaffold.py's bespoke core branch

`src/scripts/scaffold.py` is copied from **full** (the themed superset), so
its self-references (`` `origin-story` ``, `/friendly-neighborhood:...`)
are already themed-named; the reverse substitution (see "Bidirectional
skill substitution") turns them back into `init-workspace`/etc. for core.
That covers everything **except** the "Next steps" onboarding block: core's
version doesn't just omit two lines (the marker-gated `doctrine_skills`
creed line and `observation_deck` watch-your-agents line) — its remaining
"Start work: …" line is different prose entirely (different tier order,
different descriptors, different skill list) because core's onboarding
copy was hand-authored separately, not derived from full's by any
substitution rule. `build_scripts_scaffold_special()` special-cases this:
for `display: none` editions it regex-replaces the whole `print(...)` call
with core's literal, verbatim text. This is the one place the generator
hardcodes edition-specific prose rather than deriving it — flagged here
rather than building a more general mechanism for a single occurrence.

**Gotcha found and fixed along the way:** `re.sub()`'s *string* replacement
form interprets `\n` as an actual newline (not the literal two-character
sequence `\`+`n` the generated `.py` source needs inside its own string
literals) — the fix was passing a replacement **function** instead of a
string, which bypasses that escape processing entirely.

## Bidirectional skill substitution

`src/skills/{init-workspace,knowledge}/` is copied from **core** (see
`src/README.md`), so themed editions need core-name → themed-name.
`src/scripts/*` is copied from **full**, so core needs the **reverse**,
themed-name → core-name. `Vocab.skill_pairs` is built once in both
directions; `apply()` picks the direction from `self.themed`. Missing this
direction was the single biggest bug during development — it silently
produced e.g. `origin-story` inside `harness-core`'s own scaffold.py
docstring, which would have been very confusing to debug downstream.

## The pinned-word guards

`objective`/`workstream` prose substitution (`_sub_pinned_word`) skips a
match when it's:

- a bare frontmatter key at true line start (`objective:`) — the pinned key
  itself, never renamed;
- immediately followed by `.py` — a pinned CLI filename;
- immediately followed by `-` and not part of a `{word-name}` placeholder —
  a compound value like `note_type: workstream-plan`, except a documentation
  placeholder like `{workstream-name}` which legitimately becomes
  `{campaign-name}`;
- the entire content of a bare quoted literal, `"objective"`/`"objectives"`
  — a path/key literal, e.g. inside a `parent: "objectives/{name}"` value;
- immediately followed by `/` — a bare folder-name usage in an ASCII tree
  listing (`  objectives/   <- comment`), as opposed to *preceded* by `/`
  (`control-plane/objectives/`), which the pattern's lookbehind already
  excludes from matching at all.

Each of these was found empirically by generating output, diffing against
`plugins/friendly-neighborhood/`, and checking whether the residual
difference was a shipped bug (my output correct, theirs a known
`workstream:`→`campaign:`-style corruption already documented in
`vocabulary/display.yml`'s header) or a generator bug (mine wrong). Several
rounds of this surfaced additional real, live instances of exactly the
corruption `vocabulary/data-model.yml`'s header warns about — e.g.
`plugins/friendly-neighborhood/skills/campaign/SKILL.md` literally says
"Manages the full lifecycle of a campaign in `control-plane/campaigns/`" —
the real folder is (and must stay) `control-plane/workstreams/`. My
generated output gets this right; the shipped file doesn't. That's a
`bug-to-fix-everywhere` candidate for 3.6, not something I patched in
`plugins/*` (out of scope, read-only reference tree).

## External filenames

`EXTERNAL_FILENAMES` in `generate.py` lists workspace tools the plugin names but does not ship
(they live in the user's own `tools/`), so their on-disk name is fixed. `Vocab.apply()` masks
them before any substitution and restores them after, so `cadence-run.ps1` never becomes
`patrol-run.ps1`. Shipped tier files (`cadence.py` -> `patrol.py`) are renamed with their own
file and stay out of this list. Add a name here whenever src/ references an unshipped file
containing a tier or skill word.

## The `cadence` counter-landmine

`vocabulary/data-model.yml`'s header calls this out by name: the word
"cadence" has two unrelated meanings in this corpus —

1. the **cadence tier** itself (folder `cadences/`, CLI `cadence.py`,
   frontmatter key `cadence`/`patrol`) — this one fully renames to `patrol`
   for lite/full, no guard needed (it's a non-pinned tier, same as
   `assignment`/`mission`);
2. an **unrelated review-frequency field** on objective/responsibility items
   (`cadence: quarterly`, "a review cadence", `set-cadence`) — this one must
   **never** rename, in any edition, because a responsibility's own
   frontmatter key is always `cadence` (there is no "patrol" field on an
   objective — `patrol` is a different tier entirely).

Both meanings use the identical bare word, so this can't be solved by a
folder/CLI/frontmatter-key guard the way `objective`/`workstream` are
guarded — it needs semantic disambiguation. Two mechanisms handle the
confirmed cases:

- **File-level exemption** (`skip_nonpinned={"cadence"}`): applied to
  `templates/tools/objective.py` and the entire `skills/objective/` tree.
  Empirically, every "cadence" occurrence in those files is meaning #2 —
  confirmed by grepping every hit before adding the exemption, not assumed.
- **Per-occurrence guards** (`_apply_nonpinned_guarded`, `cadence`-only):
  skip when preceded by "review " ("a review cadence"), when it's a bare
  frontmatter key at line start, when preceded by "set-" or "milestones, "
  (CLI-example tokens and list phrasing), or when it's a bare `<cadence>`
  placeholder in a CLI usage example.

**This is not proven exhaustive.** It was tuned against every file that
currently contains the word "cadence" in `src/` (nine files, sampled and
verified individually), but a future edit introducing a new mixed-context
sentence could still misfire either direction (wrongly renaming the
unrelated field, or wrongly protecting a real tier mention). Treat any
`cadence`/`patrol` discrepancy in `build/difflint-report.md` as worth a
manual look, not an automatic pass.

## Known gaps — discovered during 3.5, not fixed

Numbering is stable across removals — closed records
(`build/diff-classification.md`) cite these item numbers. A removed item
leaves a gap rather than shifting the rest.

These surfaced empirically (by diffing generated output against shipped
`plugins/*`) and are real, but fixing them would mean either inventing new
content (not this step's job) or building a materially bigger mechanism
than the three gaps this step was scoped to close. Flagged for 3.6 to
classify, per the plan's own instruction to report rather than guess at a
fix.

1. **`fn-common.sh`, `fn-post-tool.sh`, `fn-pre-tool.sh`, `fn-stop.sh`
   diverge between core and themed by more than vocabulary or the two named
   feature flags.** Core's copies don't just omit the observation-deck code
   — they lack the entire `fn_speaker` acting-persona mechanism, use
   different log message text, and (`fn-pre-tool.sh`) core has no
   spider-sense danger-pattern check at all. This is a "does this concept
   exist in this edition" axis (roughly, `display: none` vs `spider-man`)
   that's bigger than a marker block — it would need its own content-fork
   mechanism to generate, not just strip. `fn-common.sh`'s **one** clean,
   markable difference (the observation-deck struct/functions) was fixed;
   the rest of that file's and its three siblings' core-vs-themed
   divergence is left as-is (src holds full's content; core's generated
   output differs from core's shipped copy in the ways described).
   `fn-session-start.sh` and `fn-subagent-stop.sh` are fully closed (byte-
   identical to shipped for both editions).

3. **`mission`/`patrol` skills are structurally different from
   `assignment`/`cadence`, not just renamed.** `src/skills/assignment/` (and
   `cadence/`) has an `actions/` subfolder (`complete.md`, `initiate.md`);
   the shipped themed `mission`/`patrol` skills are single-file (`SKILL.md`
   only — content presumably inlined by hand). The generator faithfully
   reproduces the `actions/` structure under the renamed folder, which
   difflint reports as "added" files relative to shipped. Restructuring
   `assignment`'s content to match would be real authoring work, not
   mechanical generation.

4. **`templates/.claude/rules/secret-identity.md` and
   `templates/secret-identity/CLAUDE.md`'s intro paragraph are bespoke
   themed prose, not a mechanical rename of `personal.md`.** The folder
   rename and the `CLAUDE.md` cross-reference line are handled correctly
   (verified byte-identical for the reference-line case); the rules file's
   header/H1/intro/closing line are hand-authored ("What's behind the
   mask — Peter Parker's life, not Spider-Man's...") and confirmed
   identical between lite and full, but not derivable from `personal.md` by
   any substitution rule. Generated output uses substituted `personal.md`
   content; shipped uses the bespoke version.

5. **Top-level plugin metadata files** (`CHANGELOG.md`, `LICENSE`,
   `README.md`, `NOTICE`) live directly under `plugins/{edition}/` and were
   never part of `src/`'s scope (not mentioned anywhere in `src/README.md`'s
   provenance table). The generator doesn't produce them; difflint reports
   them as "removed."

7. **`plugin.json`'s `author` object formatting is cosmetically different**
   (shipped: `{ "name": "Matt" }` on one line; generated: pretty-printed
   across three). `ensure_ascii=False` was added so unicode arrows (→) come
   through literally rather than as `\uXXXX` escapes, closing the one
   *substantive* difference; the remaining one is pure `json.dumps`
   indentation style, not content.

8. **Extensive, already-known hand-drift inside shipped doc/skill prose**
   beyond simple vocabulary — e.g. `templates/.claude/rules/control-plane.md`,
   `tools.md`, `skills/responsibility/actions/review.md`, and
   `skills/responsibility/SKILL.md` all have sentences that differ in
   wording, not just tier vocabulary, between what the generator produces
   (word-substituted from the untethemed canonical prose) and what's
   currently shipped (independently hand-edited over time — e.g. "campaigns
   are mid-horizon coordinators" vs. the generator's "the heavy lifecycle
   units"). This is exactly the drift this whole restructuring exists to
   eliminate going forward; it will show as many "changed" entries in
   `build/difflint-report.md` and is 3.6's reconciliation work, not
   something to paper over here.

9. **The `.py` CLI files' (`objective.py`, `workstream.py`) prose
   substitution is regex-guarded, not code-aware.** It was verified by
   sampling actual generated output against shipped files and fixing every
   discrepancy found this way (see the pinned-word-guards and
   cadence-counter-landmine sections above for the specific bugs this
   caught), but it is not a parser — a sufficiently unusual line could
   still misfire. Re-run `python build/generate.py && python build/difflint.py`
   after any `src/templates/tools/*.py` edit and check the diff before
   trusting it blindly.

## Phase council generation (plan 4b.2)

The `> **Phase council** ...` line injected into each `workstream`-tier
action file (`skills/{workstream-tier}/actions/{questions,research,design,
plan,implement,validate,cleanup}.md`) used to come from `build/phase-
council.yml`: two flat, fully pre-formatted strings per phase (one for
`roster: 7`, one for `roster: 32`), read verbatim by `inject_phase_council()`.
That scaled to exactly the two rosters that happened to exist; a third
roster would have needed its own third hardcoded string with no shared
derivation at all.

**What changed:** `src/lenses/*.md` and `src/registers/*.md` frontmatter now
carries a `phases:` **mapping** (`{phase: role}`, role one of `driver` /
`counsel` / `watch`) instead of a bare phase list. `build/generate.py` gained
`PHASE_COUNCIL_FULL` / `PHASE_COUNCIL_LITE` (structured per-phase driver/
counsel/watch data, still living in `generate.py` itself — see below for
why), `render_phase_council_line()` (the shared formatter, including the
`counsel none` / singular-`watch villain` edge cases), and
`validate_phase_council_tables()` (run once from `main()`, dies loudly on
drift). The `/{plugin-slug}:creed` reference is now built from the edition's
own `plugin.name` at render time — closes `phase-council.yml`'s documented
"COUPLING CAVEAT" (a second roster-7 or roster-32 edition under a different
plugin name no longer needs its own copy of these strings).

**Why the tables are still static, not purely derived from frontmatter +
roster filtering**, investigated and confirmed empirically before deciding:

- **Order and inline annotations aren't recoverable from a per-character
  `{phase: role}` map.** They're hand-authored prose with no discoverable
  formula — e.g. `design.md` and `blueprint.md` list the identical 4 watch
  villains (`octavius`, `vulture`, `kraven`, `kingpin`) in two different
  orders. Kept as `PHASE_COUNCIL_FULL`'s literal ordering + `(annotation)`
  text, extracted verbatim from `phase-council.yml`'s `full` lines.
- **A naive "any roster member whose frontmatter phase+role matches" filter
  regresses full's own byte-reproduction.** This same step (4b.2) added
  `phases:` frontmatter to four lenses (`scorpion`, `venom`, `ham`, `punk`)
  that were never previously routed into any phase council. Filtering
  full's 32-member roster by frontmatter alone would newly pull them into
  `implement`/`validate`/`design`/`plan`, which doesn't match shipped
  output. `PHASE_COUNCIL_FULL`'s explicit membership boundary is what keeps
  those four out, exactly as shipped.
- **Lite's watch/counsel lists are hand-curated padding, not a roster
  filter of full's list.** Lite's roster has only 3 villains (`carnage`,
  `kingpin`, `mysterio`) and 1 support character (`jameson`), reused across
  phases well outside any one character's own natural relevance — e.g.
  `kingpin` watches `questions` in lite despite `questions` not being in
  kingpin's own `phases:` frontmatter (kingpin's full-edition role is
  `research`/`design`/`plan` only). Filtering `PHASE_COUNCIL_FULL` by lite
  roster membership leaves `questions`/`implement` watch empty or short,
  which doesn't match shipped lite output either. Confirmed non-formulaic
  the same way as full's ordering (`research.md` and `design.md` both reuse
  `kingpin`+`mysterio` in opposite order). Kept as its own static table,
  `PHASE_COUNCIL_LITE`, verbatim from `phase-council.yml`'s `lite` lines.
- **Driver clause + trailer sentence** (both editions) are kept as literal
  strings per phase — "driver" vs "drivers", `/` vs `,` separators, and
  inline routing notes ("route each step to the right Spider-variant — see
  Delegation") have no roster-membership logic to derive from.

**What genuinely IS wired to frontmatter, and what that buys:**
`validate_phase_council_tables()` cross-checks every non-delegation name in
`PHASE_COUNCIL_FULL` against that character's own lens/register `phases:`
frontmatter (dies if they disagree), and every `PHASE_COUNCIL_LITE` name
against `vocabulary/display.yml`'s `roster.lite` (dies if it names someone
out of roster — the structural guarantee that makes the zero-leakage grep
check pass by construction, not just by the current table's contents
happening to be correct). A lens file's role changing, or a roster changing,
without the corresponding table update now fails the build instead of
silently reproducing a stale line.

**Delegations** (`silk`, `noir`, `miguel`, `gwen`, `ned`) are real subagents,
not lens/register carriers in this workstream's model — they're skipped by
the frontmatter cross-check (no `phases:` frontmatter by design) and their
driver/counsel role per phase lives only inside `PHASE_COUNCIL_FULL`/`_LITE`,
extracted directly from `phase-council.yml`'s full-edition lines, per the
plan step's explicit instruction not to invent a frontmatter mechanism for
them.

**`build/phase-council.yml`'s fate:** kept on disk, unread by the generator,
as the original byte-checked-against-shipped reference the tables above were
transcribed from — useful for a future re-verification pass, not a live
input. Its header comments describing itself as the generator's input are
now stale (superseded by this section); left as historical record rather
than rewritten, since the file is no longer live code and 3.6-style
"reproduce then classify" isn't warranted for a fixture nothing reads.

Verified: `python build/generate.py && python build/difflint.py` produces
**zero** `difflint-report.md` entries under any of `harness-core`,
`friendly-neighborhood-lite`, `friendly-neighborhood` for any `Phase
council` line (i.e. no regression from the two-hardcoded-string mechanism
this replaced), and grepping every generated `friendly-neighborhood-lite`
action file's `Phase council` line for the 22 characters outside lite's
7-person roster (per known-gap #1's "Deferred to Phase 4" list) returns zero
hits.

## Line endings

`plugins/*` is checked out with CRLF for most files (`.gitattributes`:
`* text=auto`, Windows checkout) while `generate.py` always writes LF.
`difflint.py` normalizes `\r\n` → `\n` on both sides before comparing, so
this is never reported as a discrepancy — it isn't one.
