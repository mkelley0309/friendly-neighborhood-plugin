---
name: cadence
description: Recurring work — scheduled or on demand. Refresh sources into the knowledge base, drain a cleanup queue, report status across the portfolio, auto-lint, watch a CI run. Use when the defining feature of the work is that it runs again, whether it is small like an assignment or large enough to need workstream-style handoffs. Tracks its own runs, carries a self-improvement diary so each run makes the next one cheaper, and retires or is abandoned rather than completing.
---

# Cadence — work that runs again

The third thing that can be spawned under an objective, beside a **assignment** (bounded, single-session) and a **workstream** (multi-session, subagent handoffs).

**A cadence is defined by its recurrence, not its size.** Refreshing documentation into the vault, draining the knowledge cleanup queue, reporting status across objectives, auto-linting, watching a job. One cadence may be as small as a lint pass and another as large as a full research refresh. That difference does not matter. What matters is that it runs again.

It does **not** reinvent scheduling — it wires Claude Code's built-ins:

- **`/loop [interval] <command>`** — recurring or self-paced repetition within a session.
- **`schedule`** — cron-style routines for time-based autonomous runs.
- **`/goal <condition>`** — keep taking turns until a stated condition holds, then stop. Requires Claude Code v2.1.139+. Use it for a run with a verifiable end state (drain the queue until it is empty, iterate until the gate reports GO) rather than for a run that repeats on a clock.

Those are *mechanisms*, and picking between them is the whole choice: **`/loop` repeats on a clock, `schedule` repeats on a calendar, `/goal` repeats until something is true.** The cadence is the *container* around whichever you pick: the folder that remembers what happened last time so the next run is better than the last.

> **`/goal` has a constraint worth designing around.** Its evaluator judges the condition against what Claude has *surfaced in the conversation* — it does not run commands or read files itself. So `"the gate passes"` is only a usable condition if the run actually prints the gate result. Write conditions the run's own output can demonstrate, and have each pass echo the evidence. It also needs an accepted trust dialog and is unavailable when `disableAllHooks` or `allowManagedHooksOnly` is set, so a cadence that depends on it should say so in its Guardrails.

## Why it gets a folder

Two things follow from recurrence, and neither fits in an assignment or a workstream:

- **It does not complete.** A cadence is `active`, `paused`, `retired` (the job is done or automated away) or `abandoned` (it stopped mattering). "Complete" is not a state it reaches.
- **Each run should make the next one cheaper**, which is what the self-improvement diary is for. A cadence that never improves is a subscription.

## Inline, or spawned

A cadence does **not** have to contain the work it triggers. Each run picks its own shape:

- **Inline** — the run is small and self-contained (a lint pass, a status roll-up). Do it in place, using `_working/` for scratch if it needs any. Nothing else is created.
- **Spawned** — the run is substantial enough to deserve its own record, so it launches a **assignment** (bounded, single-session) or a **workstream** (multi-session, subagent handoffs) with `--parent cadences/{name}`. That child then runs its own lifecycle, closes into its own log, and deletes its own folder. Record it with `cadence.py run <name> --spawned assignments/<child>` (or `workstreams/<child>`), which links it from the run log.

This is what keeps a cadence from swelling into a parallel project system. **The cadence folder holds the recurrence — the trigger, the guardrails, the run log, the diary. It does not have to hold the work.** A quarterly refresh that turns into a real research effort should spawn a workstream, not grow a `research.md` inside the cadence.

Spawning is also how a cadence stays honest about size. If run after run spawns a workstream, the recurring part is just a scheduler, and that is fine — that is exactly what a cadence is for.

## Spawn is not promotion

Two different relationships, and conflating them produces a cadence that is really a workstream in disguise:

- **Spawn — downward, many times.** The cadence is already running and delegates one run's work to a child. `cadence.py run <name> --spawned assignments/<child>`.
- **Promotion — upward, once.** An assignment or workstream turns out to be worth repeating, so it *becomes* a cadence. `cadence.py create <name> --from assignments/<origin>`. The originating work still closes normally into its own log, and the cadence is a new record pointing back at what proved the case, not a continuation of it.

The test: **is the recurring thing already established, or is this the moment it became recurring?** The first is a spawn, the second is a promotion. A cadence created by promotion starts at zero runs like any other — the work that proved it does not count as run 1, because it closed under its own tier.

## Lifecycle

1. **Open it.** `python -B tools/cadence.py create <name> [--parent objectives/<name>] [--trigger "weekly"|"nightly 02:00"|"on-demand"]`. State the **purpose** and name the **trigger** — if it is scheduled, say the schedule; if on demand, say what makes someone reach for it.
2. **Fill in the guardrails before the first run.** A cadence runs unattended, so say what should stop it and ask for a human. The template ships four: the gate is NO-GO and a run cannot clear it, the run would touch something outside its declared scope, two consecutive runs make no progress, input volume is far outside normal. Add the ones specific to this cadence and delete none.
3. **Run it**, by hand, via `/loop`, or on a `schedule` routine.
4. **Record every run.** `python -B tools/cadence.py run <name> --note "what it did" --gate GO|NO-GO --learned "what would make the next run better" [--spawned assignments/<child>]`. `--learned` is the one that matters. If a run genuinely taught you nothing, that is worth noticing rather than papering over.
5. **Pause when it is not needed** rather than abandoning it — `cadence.py pause` / `resume`. A paused cadence keeps its diary.

## Closing

A cadence ends **retired** or **abandoned**, and both get logged. Retirement because the cadence automated itself out of a job is a success, and the entry should say so.

1. **Rescue anything durable** before the folder goes: artifacts to `control-plane/outputs/{name}/`, vault content to `knowledge/vault/`, code to `projects/{name}/`. `delete` refuses while `_working/` still holds files, so clear it deliberately.
2. **Close it.** `cadence.py retire <name> --reason "..."` or `cadence.py abandon <name> --reason "..."`. Both require a reason.
3. **Write the entry** in `control-plane/cadences/_log.md`: what recurred and on what trigger, how it ran, how it ended, and what is carried forward — most usefully whatever the diary accumulated that outlives the cadence.
4. **Delete.** `cadence.py delete <name>`. Verify the log entry exists first.

## The diary is the point

Ordinary lessons go in the log at close. The **diary** is different: it is written *during* the cadence's life, addressed to the next run, and it is the only reason a recurring job gets cheaper instead of just repeating.

**When a diary entry recurs, stop writing it down and go fix it** — promote it into the cadence's own procedure, a tool, or a skill. A diary that says the same thing three times is a backlog item, not a diary.

## Safety in unattended runs

The guardrails matter *more* here, because nobody is watching each run:

- **The gate decides** — `tools/gate.py` is the deterministic go/no-go; never assume done.
- **Hard safety still enforced** — the `.claude/settings.json` deny-list blocks destructive ops even unattended.
- **Watch the cost** — cheap-per-run × many runs adds up. Keep each run lean, and pause a cadence that is not earning its tokens.
- **Report friction** — where a run needed correction, or asked for approval repeatedly, append the rule to `control-plane/_harness/friction.md`. High approval rates on a recurring job are the clearest signal that setup needs fixing.
