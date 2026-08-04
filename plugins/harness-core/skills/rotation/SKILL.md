---
name: rotation
description: Recurring work — scheduled or on demand. Refresh sources into the knowledge base, drain a cleanup queue, report status across the portfolio, auto-lint, watch a CI run. Use when the defining feature of the work is that it runs again, whether it is small like a task or large enough to need workstream-style handoffs. Tracks its own runs, carries a self-improvement diary so each run makes the next one cheaper, and retires or is abandoned rather than completing.
---

# Rotation — work that runs again

The third thing that can be spawned under an objective, beside a **task** (bounded, single-session) and a **workstream** (multi-session, subagent handoffs).

**A rotation is defined by its recurrence, not its size.** Refreshing documentation into the vault, draining the knowledge cleanup queue, reporting status across objectives, auto-linting, watching a job. One rotation may be as small as a lint pass and another as large as a full research refresh. That difference does not matter. What matters is that it runs again.

It does **not** reinvent scheduling — it wires Claude Code's built-ins:

- **`/loop [interval] <command>`** — recurring or self-paced repetition within a session.
- **`schedule`** — cron-style routines for time-based autonomous runs.

Those are *mechanisms*. The rotation is the *container*: the folder that remembers what happened last time so the next run is better than the last.

## Why it gets a folder

Two things follow from recurrence, and neither fits in a task or a workstream:

- **It does not complete.** A rotation is `active`, `paused`, `retired` (the job is done or automated away) or `abandoned` (it stopped mattering). "Complete" is not a state it reaches.
- **Each run should make the next one cheaper**, which is what the self-improvement diary is for. A rotation that never improves is a subscription.

## Inline, or spawned

A rotation does **not** have to contain the work it triggers. Each run picks its own shape:

- **Inline** — the run is small and self-contained (a lint pass, a status roll-up). Do it in place, using `_working/` for scratch if it needs any. Nothing else is created.
- **Spawned** — the run is substantial enough to deserve its own record, so it launches a **task** (bounded, single-session) or a **workstream** (multi-session, subagent handoffs) with `--parent rotations/{name}`. That child then runs its own lifecycle, closes into its own log, and deletes its own folder. Record it with `rotation.py run <name> --spawned tasks/<child>` (or `workstreams/<child>`), which links it from the run log.

This is what keeps a rotation from swelling into a parallel project system. **The rotation folder holds the recurrence — the trigger, the guardrails, the run log, the diary. It does not have to hold the work.** A quarterly refresh that turns into a real research effort should spawn a workstream, not grow a `research.md` inside the rotation.

Spawning is also how a rotation stays honest about size. If run after run spawns a workstream, the recurring part is just a scheduler, and that is fine — that is exactly what a rotation is for.

## Lifecycle

1. **Open it.** `python -B tools/rotation.py create <name> [--parent objectives/<name>] [--trigger "weekly"|"nightly 02:00"|"on-demand"]`. State the **purpose** and name the **trigger** — if it is scheduled, say the schedule; if on demand, say what makes someone reach for it.
2. **Fill in the guardrails before the first run.** A rotation runs unattended, so say what should stop it and ask for a human. The template ships four: the gate is NO-GO and a run cannot clear it, the run would touch something outside its declared scope, two consecutive runs make no progress, input volume is far outside normal. Add the ones specific to this rotation and delete none.
3. **Run it**, by hand, via `/loop`, or on a `schedule` routine.
4. **Record every run.** `python -B tools/rotation.py run <name> --note "what it did" --gate GO|NO-GO --learned "what would make the next run better" [--spawned tasks/<child>]`. `--learned` is the one that matters. If a run genuinely taught you nothing, that is worth noticing rather than papering over.
5. **Pause when it is not needed** rather than abandoning it — `rotation.py pause` / `resume`. A paused rotation keeps its diary.

## Closing

A rotation ends **retired** or **abandoned**, and both get logged. Retirement because the rotation automated itself out of a job is a success, and the entry should say so.

1. **Rescue anything durable** before the folder goes: artifacts to `control-plane/outputs/{name}/`, vault content to `knowledge/vault/`, code to `projects/{name}/`. `delete` refuses while `_working/` still holds files, so clear it deliberately.
2. **Close it.** `rotation.py retire <name> --reason "..."` or `rotation.py abandon <name> --reason "..."`. Both require a reason.
3. **Write the entry** in `control-plane/rotations/_log.md`: what recurred and on what trigger, how it ran, how it ended, and what is carried forward — most usefully whatever the diary accumulated that outlives the rotation.
4. **Delete.** `rotation.py delete <name>`. Verify the log entry exists first.

## The diary is the point

Ordinary lessons go in the log at close. The **diary** is different: it is written *during* the rotation's life, addressed to the next run, and it is the only reason a recurring job gets cheaper instead of just repeating.

**When a diary entry recurs, stop writing it down and go fix it** — promote it into the rotation's own procedure, a tool, or a skill. A diary that says the same thing three times is a backlog item, not a diary.

## Safety in unattended runs

The guardrails matter *more* here, because nobody is watching each run:

- **The gate decides** — `tools/gate.py` is the deterministic go/no-go; never assume done.
- **Hard safety still enforced** — the `.claude/settings.json` deny-list blocks destructive ops even unattended.
- **Watch the cost** — cheap-per-run × many runs adds up. Keep each run lean, and pause a rotation that is not earning its tokens.
- **Report friction** — where a run needed correction, or asked for approval repeatedly, append the rule to `control-plane/_harness/friction.md`. High approval rates on a recurring job are the clearest signal that setup needs fixing.
