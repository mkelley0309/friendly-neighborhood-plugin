# 🕷 Friendly Neighborhood

> A measured, quippy, ethical Claude Code harness. *Great power, great responsibility, lean token budget.*

Friendly Neighborhood packages a real, working harness as a Claude Code plugin — re-themed after a certain wall-crawler. Install it, scaffold a workspace, and you get an **opinionated operating system for serious, long-horizon, knowledge-heavy work**. The names are flavor; the *opinions* are the point. Full operating doctrine: `/friendly-neighborhood:creed`.

---

## What makes it different (and why that's good)

The defensible opinions — not "it has agents," which everyone has:

- **Progressive distillation, proportional.** At every handoff, work is compressed to a dense artifact and handed to a *fresh context window* — keeping understanding high and tokens low across long, multi-session work. (Light on a quick task; hard on a multi-week mission. It's lossy, so you distill for the next phase's needs.)
- **A real knowledge architecture** — `sources/` (external truth) and `perspective/` (your first-party views) as *peers*, distilled into a curated `vault/` only by **peer-reviewed admission**, navigated progressively (hub → note). Not a dump-and-retrieve store; a curated, auditable, navigable knowledge base.
- **A decision mechanic that doesn't fake precision** — *hard, measurable* concerns (tests, lint, budget, deny-list hits) go through a **deterministic gate** (`tools/gate.py`, exit-code GO/NO-GO); *soft* ones (over-engineering, scope creep, wrong target) are flagged by **villains who affirmatively detect failure modes** and weighed as an honest, *recorded* judgment. Few "don't" rules — cost is computed from live signals, not a catalog of prohibitions.
- **Three tiers of work** — `responsibility` (the long-lived why: a role, an annual objective, a career goal), `mission` (complex, multi-session, multi-handoff), `patrol` (a single work unit) — each with durable, auditable state.
- **Curated self-learning** — lessons captured every phase, knowledge grown from research, but **gated** (peer review + human sign-off) so it gets smarter without drifting.
- **The symbiote** — disciplined, turn-limited model escalation that always returns to baseline.

## The cast & the foundations

- **A Spider-cast of agents** — 11 drivers, 7 advisors ("angels on your shoulder"), and a 14-villain dissent council ("devils") whose *approval is the alarm* — spawned **contextually per phase**, never all at once.
- **Foundations** (solid and expected — not claimed as novel): a workspace scaffolder, observational logging + recovery, an enforced safety deny-list + spider-sense (`PreToolUse`), a verification gate before a mission closes, **native autonomous looping** (`/loop` + `schedule`, via `stakeout`), a live per-character observation deck (VS Code), a warm accountable output style, and a statusline.

---

## Requirements

| Requirement | For | Notes |
|---|---|---|
| **Claude Code** | everything | the host. |
| **Python 3.8+** | the orchestration CLIs (patrol/responsibility/mission) | **stdlib only** — no `pip install`. Use whatever launcher you have (`python3`, `python`, or `py`). `origin-story` checks for it and tells you how to install if missing. |
| **bash** | hooks + statusline | built-in on macOS/Linux; on Windows use Git Bash. If absent, hooks/statusline simply no-op — the enforced safety (deny-list) still works. |
| **Obsidian** *(optional)* | nicer vault UX | the vault is plain markdown; Obsidian only adds graph/wikilink/Bases tooling. Install the kepano skills separately if you want it: `npx skills add kepano/obsidian-skills -g -a claude-code`. |

---

## Install

```bash
claude plugin marketplace add mkelley0309/friendly-neighborhood-plugin
claude plugin install friendly-neighborhood@friendly-neighborhood
```

Then, in any project where you want the harness:

```
/friendly-neighborhood:origin-story
```

This scaffolds a working, domain-neutral workspace (constitution, the three-tier control-plane, an empty knowledge vault, the portable CLIs, and auto-loading `.claude/rules/` contracts). It **never overwrites** existing files and is safe to re-run.

> Watch the cost: `claude plugin details friendly-neighborhood` shows the always-on vs. on-invoke footprint. Keeping the always-on total lean is the whole point.

---

## Skills

Invoke as `/friendly-neighborhood:<name>`.

| Skill | What it does |
|---|---|
| `creed` | Loads the operating doctrine (great power / great responsibility, the Everyman budget, the three mechanics, the powers vocabulary). |
| `origin-story` | Scaffolds a fresh workspace from the bundled templates. Run this first. |
| `responsibility` | A long-lived, review-cycle objective with structured tracking — Key Results, milestones, linked missions, cadence, health, and an append-only decisions log. |
| `mission` | Complex, multi-session work run through the heavy **QRDPIV** lifecycle (questions → research → design → plan → implement → validate → cleanup; or **RPIV** when the spec is clear). May link child patrols. |
| `patrol` | A lightweight unit or one iteration against a mission — proportional admin only (assignment, checklist, handoff, lessons). Promote to a mission if it grows. |
| `web-archive` | The knowledge pipeline + linked vault: scout → harvest → distill → cartograph → sync. |
| `spider-sense` | A manual pre-flight danger check before a risky operation (companion to the automatic hook). |
| `symbiote` | Borrowed power — a **spidey** spawns a higher-powered clone of *itself* for a hard sub-task, hard-capped by turns. |
| `church-bell` | Kills the symbiote — de-escalate on a villain dissent or turn overrun, confirm baseline, log the cost. |

> The "powers" (web-crawl = search, wall-crawl = map the codebase, thwip = hop between files, leap-of-faith = commit to a judgment call, …) are **vocabulary** documented in `creed`, not separate skills — adding skills you never use is Kingpin behavior (paying tokens for nothing).

---

## Agents

Assigned by **function**, not vibe. Model/effort tiers implement the Everyman budget.

The cast splits three ways, mirroring the dissent council — **spideys** (drivers), **support** (advisors), **villains** (critics). All live in `agents/`; the grouping is carried by the creed, `agent_group`, and the three observation-deck streams.

**Spideys** (the drivers; **all are symbiote-eligible**): `peter` (default/home base) · `silk` (recall & lookups, eidetic memory) · `noir` (debugging & root-cause) · `miles` (minimal-diff / surgical fixes) · `peni` (builder — fans out SP//dr units across worktrees) · `gwen` (functional testing & validation) · `ham` (adversarial validation — catches passes that are *right by accident*) · `ben-reilly` (refactors & dedup, drift-flagged) · `jessica` (root-cause investigation on failures) · `punk` (anti-ceremony dissent — over-built *process*) · `miguel` (**the architect** — opus plan-mode; his native opus isn't a symbiote, but he can escalate *effort* as one).

**Support** (advisors): `robbie` (constructive interviewer — origin-story onboarding + design questions) · `uncle-ben` (the conscience — *should* we?) · `aunt-may` (scope & sustainability) · `mj` (the real user need) · `ned` (ops & logistics) · `jameson` (devil's-advocate grilling of poorly-shaped work) · `madame-web` (sees clearly, updates the plan on new evidence).

**Dissent council (villains — agreement is the alarm):** `osborn` (ends-justify-means) · `octavius` (over-engineering) · `venom` (escalating out of want, not need) · `sandman` (under-shaped / formless work) · `lizard` (over-researching) · `electro` (fragile / cascading change) · `mysterio` (unvalidated "done") · `cat` (weak security — Black Cat loves an open window) · `kraven` (wrong target) · `rhino` (brute force over elegance) · `vulture` (won't update on new evidence) · `scorpion` (spite / bad faith) · `carnage` (needless destruction) · `kingpin` (token greed). Read-only critics — they judge, they never edit.

Invoke a villain to red-team: `/agents` → pick one, or route a review to it. **If it approves, reconsider.**

---

## Observation deck (VS Code)

Watch your agents work in real time, each in their character colors. The main window stays the screenplay of the main context; three extra panes show the cast at work:

- **Spideys** — one color per driver (peter red+blue · miles black+red · gwen white+hot-pink · noir monochrome · miguel 2099-blue · ben-reilly scarlet · silk magenta). A spidey wearing the **symbiote** flips to the **black suit** (white-on-black) until the church bell sheds it.
- **Support** — one minimalist, muted stream (`robbie`, `jameson`, and the advisors log only when they actually weigh in).
- **Villains** — a palette each (mysterio purple · venom black+white+red · electro electric-yellow · kingpin white-on-slate · cat platinum-on-plum · …); a villain's line is the dissent worth seeing.

**Open it:** Terminal → Run Task → **🕷 Observation Deck** (wired by the scaffolded `.vscode/tasks.json`). Outside VS Code, `bash .claude/scripts/observe.sh` follows all three in one terminal.

**How it works:** each agent narrates one line per significant step via `.claude/scripts/agent-log.sh`, routed to `.claude/logs/agents/{spideys,support,villains}.log` in that character's color; the `SubagentStop` hook posts exits and auto-sheds the suit. Granularity is per-action — Claude Code subagents don't stream raw tokens — so the deck reads as "who's doing what right now." **Full edition only.**

---

## The three mechanics, briefly

- **Everyman budget** — baseline personas run `haiku`/`sonnet` at low–medium effort; `opus`/high is reserved for `miguel` and justified per use. Audit the always-on cost with `claude plugin details`.
- **Symbiote** — `/friendly-neighborhood:symbiote` lets an agent spawn a clone of *itself* with an escalated model (e.g. sonnet→opus), same role/tools/memory, hard-bounded by `symbiote_max_turns` (the corruption meter, default 8). `/friendly-neighborhood:church-bell` is the kill switch — it terminates the clone if it trips a villain dissent (about to do damage) or overruns; the `SubagentStop` hook confirms the return to baseline. (Miguel is *not* a symbiote — opus is his native architect level.) The [observation deck](#observation-deck-vs-code) shows the suited spidey in the **black suit** while it's on.
- **Dissent** — on-demand by default (invoke a villain). To run it *passively* every turn (costs tokens), add a `Stop` hook of type `prompt` that flags only when a villain would approve — see [Customization](#customization).

---

## Memory model

The harness's memory is **explicit and auditable**, not implicit:

- **Knowledge vault** (`web-archive`) = long-term **semantic** memory.
- **Control-plane logs + the decisions log + workstream-notes** = **episodic** memory.
- **constitution + `.claude/rules/`** = **procedural** memory.

It also uses Claude Code's native **agent memory** (`memory: project` on the stateful drivers `peter` and `silk`). Claude Code's **auto-memory** is complementary and optional — leave it on for lightweight personal preferences if you like; the harness doesn't depend on it.

---

## Permissions

The scaffold's `.claude/settings.json` ships a **balanced** posture: it allows routine harness operations (reads, the CLIs, `mkdir`, read-only recon, and scoped writes to `control-plane/` + `knowledge/`) and **denies** an enforced backstop (`rm -rf`, force-push, reads of `.env`/secrets). Spider-sense adds an advisory tingle on top. Tune it to taste — `projects/` writes are intentionally left to prompt.

---

## Customization

- **Default persona, symbiote cap, passive dissent** — set via the plugin's `userConfig` (`default_persona`, `symbiote_max_turns`, `dissent_passive`).
- **Enable passive dissent** — add a `Stop` hook of type `prompt` to your settings that runs the just-finished turn past the villain council and speaks up *only* when one would approve. It's off by default because it costs tokens every turn (the recursive budget tension is real).
- **Rename anything** — the names are flavor; the machinery (CLI commands, frontmatter keys) is stable underneath, so renaming skills/agents is cosmetic.

---

## License & disclaimer

Original code: MIT — see [LICENSE](LICENSE).

**Unofficial fan project.** Spider-Man and all related characters are © & ™ Marvel Characters, Inc. / The Walt Disney Company. This project is a noncommercial, transformative homage — **not** affiliated with, endorsed by, or sponsored by Marvel or Disney, and it ships no Marvel artwork, logos, or copyrighted text. See [NOTICE](NOTICE).

🕸 *Your friendly neighborhood harness. Do the right thing with the minimum force necessary.*
