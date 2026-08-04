---
name: stakeout
description: Recurring work — scheduled or on demand. Refresh sources into the knowledge base, drain a cleanup queue, report status across the portfolio, auto-lint, watch a CI run. Use when the defining feature of the work is that it runs again, whether it is small like a patrol or large enough to need mission-style handoffs. Tracks its own runs, carries a self-improvement diary so each run makes the next one cheaper, and retires or is abandoned rather than completing.
---

# Stakeout — work that runs again

The third thing that can be spawned under an objective, beside a **patrol** (bounded, single-session) and a **mission** (multi-session, subagent handoffs).

**A stakeout is defined by its recurrence, not its size.** Refreshing documentation into the vault, draining the knowledge cleanup queue, reporting status across objectives, auto-linting, watching a job. One stakeout may be as small as a lint pass and another as large as a full research refresh. That difference does not matter. What matters is that it runs again.

It does **not** reinvent scheduling — it wires Claude Code's built-ins:

- **`/loop [interval] <command>`** — recurring or self-paced repetition within a session.
- **`schedule`** — cron-style routines for time-based autonomous runs.

Those are *mechanisms*. The stakeout is the *container*: the folder that remembers what happened last time so the next run is better than the last.

## Why it gets a folder

Two things follow from recurrence, and neither fits in a patrol or a mission:

- **It does not complete.** A stakeout is `active`, `paused`, `retired` (the job is done or automated away) or `abandoned` (it stopped mattering). "Complete" is not a state it reaches.
- **Each run should make the next one cheaper**, which is what the self-improvement diary is for. A stakeout that never improves is a subscription.

## Inline, or spawned

A stakeout does **not** have to contain the work it triggers. Each run picks its own shape:

- **Inline** — the run is small and self-contained (a lint pass, a status roll-up). Do it in place, using `_working/` for scratch if it needs any. Nothing else is created.
- **Spawned** — the run is substantial enough to deserve its own record, so it launches a **patrol** (bounded, single-session) or a **mission** (multi-session, subagent handoffs) with `--parent stakeouts/{name}`. That child then runs its own lifecycle, closes into its own log, and deletes its own folder. Record it with `stakeout.py run <name> --spawned patrols/<child>` (or `workstreams/<child>`), which links it from the run log.

This is what keeps a stakeout from swelling into a parallel project system. **The stakeout folder holds the recurrence — the trigger, the guardrails, the run log, the diary. It does not have to hold the work.** A quarterly refresh that turns into a real research effort should spawn a mission, not grow a `research.md` inside the stakeout.

Spawning is also how a stakeout stays honest about size. If run after run spawns a mission, the recurring part is just a scheduler, and that is fine — that is exactly what a stakeout is for.

## Lifecycle

1. **Open it.** `python -B tools/stakeout.py create <name> [--parent objectives/<name>] [--trigger "weekly"|"nightly 02:00"|"on-demand"]`. State the **purpose** and name the **trigger** — if it is scheduled, say the schedule; if on demand, say what makes someone reach for it.
2. **Fill in the guardrails before the first run.** A stakeout runs unattended, so say what should stop it and ask for a human. The template ships four: the gate is NO-GO and a run cannot clear it, the run would touch something outside its declared scope, two consecutive runs make no progress, input volume is far outside normal. Add the ones specific to this stakeout and delete none.
3. **Run it**, by hand, via `/loop`, or on a `schedule` routine.
4. **Record every run.** `python -B tools/stakeout.py run <name> --note "what it did" --gate GO|NO-GO --learned "what would make the next run better" [--spawned patrols/<child>]`. `--learned` is the one that matters. If a run genuinely taught you nothing, that is worth noticing rather than papering over.
5. **Pause when it is not needed** rather than abandoning it — `stakeout.py pause` / `resume`. A paused stakeout keeps its diary.

## Closing

A stakeout ends **retired** or **abandoned**, and both get logged. Retirement because the stakeout automated itself out of a job is a success, and the entry should say so.

1. **Rescue anything durable** before the folder goes: artifacts to `control-plane/outputs/{name}/`, vault content to `knowledge/vault/`, code to `projects/{name}/`. `delete` refuses while `_working/` still holds files, so clear it deliberately.
2. **Close it.** `stakeout.py retire <name> --reason "..."` or `stakeout.py abandon <name> --reason "..."`. Both require a reason.
3. **Write the entry** in `control-plane/stakeouts/_log.md`: what recurred and on what trigger, how it ran, how it ended, and what is carried forward — most usefully whatever the diary accumulated that outlives the stakeout.
4. **Delete.** `stakeout.py delete <name>`. Verify the log entry exists first.

## The diary is the point

Ordinary lessons go in the log at close. The **diary** is different: it is written *during* the stakeout's life, addressed to the next run, and it is the only reason a recurring job gets cheaper instead of just repeating.

**When a diary entry recurs, stop writing it down and go fix it** — promote it into the stakeout's own procedure, a tool, or a skill. A diary that says the same thing three times is a backlog item, not a diary.

## Safety in unattended runs

The guardrails matter *more* here, because nobody is watching each run:

- **The gate decides** — `tools/gate.py` is the deterministic go/no-go; never assume done.
- **Hard safety still enforced** — the `.claude/settings.json` deny-list blocks destructive ops even unattended.
- **Watch the cost** — cheap-per-run × many runs adds up. Keep each run lean, and pause a stakeout that is not earning its tokens.
- **Report friction** — where a run needed correction, or asked for approval repeatedly, append the rule to `control-plane/_harness/friction.md`. High approval rates on a recurring job are the clearest signal that setup needs fixing.
