---
name: patrol
description: Recurring work — scheduled or on demand. Refresh sources into the knowledge base, drain a cleanup queue, report status across the portfolio, auto-lint, watch a CI run. Use when the defining feature of the work is that it runs again, whether it is small like a mission or large enough to need workstream-style handoffs. Tracks its own runs, carries a self-improvement diary so each run makes the next one cheaper, and retires or is abandoned rather than completing.
---

# Patrol — work that runs again

The third thing that can be spawned under a responsibility, beside a **mission** (bounded, single-session) and a **campaign** (multi-session, subagent handoffs).

**A patrol is defined by its recurrence, not its size.** Refreshing documentation into the vault, draining the knowledge cleanup queue, reporting status across responsibilities, auto-linting, watching a job. One patrol may be as small as a lint pass and another as large as a full research refresh. That difference does not matter. What matters is that it runs again.

It does **not** reinvent scheduling — it wires Claude Code's built-ins:

- **`/loop [interval] <command>`** — recurring or self-paced repetition within a session.
- **`schedule`** — cron-style routines for time-based autonomous runs.
- **`/goal <condition>`** — keep taking turns until a stated condition holds, then stop. Requires Claude Code v2.1.139+. Use it for a run with a verifiable end state (drain the queue until it is empty, iterate until the gate reports GO) rather than for a run that repeats on a clock.

Those are *mechanisms*, and picking between them is the whole choice: **`/loop` repeats on a clock, `schedule` repeats on a calendar, `/goal` repeats until something is true.** The patrol is the *container* around whichever you pick: the folder that remembers what happened last time so the next run is better than the last.

> **`/goal` has a constraint worth designing around.** Its evaluator judges the condition against what Claude has *surfaced in the conversation* — it does not run commands or read files itself. So `"the gate passes"` is only a usable condition if the run actually prints the gate result. Write conditions the run's own output can demonstrate, and have each pass echo the evidence. It also needs an accepted trust dialog and is unavailable when `disableAllHooks` or `allowManagedHooksOnly` is set, so a patrol that depends on it should say so in its Guardrails.

## Why it gets a folder

Two things follow from recurrence, and neither fits in a mission or a campaign:

- **It does not complete.** A patrol is `active`, `paused`, `retired` (the job is done or automated away) or `abandoned` (it stopped mattering). "Complete" is not a state it reaches.
- **Each run should make the next one cheaper**, which is what the self-improvement diary is for. A patrol that never improves is a subscription.

## Inline, or spawned

A patrol does **not** have to contain the work it triggers. Each run picks its own shape:

- **Inline** — the run is small and self-contained (a lint pass, a status roll-up). Do it in place, using `_working/` for scratch if it needs any. Nothing else is created.
- **Spawned** — the run is substantial enough to deserve its own record, so it launches a **mission** (bounded, single-session) or a **campaign** (multi-session, subagent handoffs) with `--parent patrols/{name}`. That child then runs its own lifecycle, closes into its own log, and deletes its own folder. Record it with `patrol.py run <name> --spawned missions/<child>` (or `workstreams/<child>`), which links it from the run log.

This is what keeps a patrol from swelling into a parallel project system. **The patrol folder holds the recurrence — the trigger, the guardrails, the run log, the diary. It does not have to hold the work.** A quarterly refresh that turns into a real research effort should spawn a campaign, not grow a `research.md` inside the patrol.

Spawning is also how a patrol stays honest about size. If run after run spawns a campaign, the recurring part is just a scheduler, and that is fine — that is exactly what a patrol is for.

## Spawn is not promotion

Two different relationships, and conflating them produces a patrol that is really a campaign in disguise:

- **Spawn — downward, many times.** The patrol is already running and delegates one run's work to a child. `patrol.py run <name> --spawned missions/<child>`.
- **Promotion — upward, once.** A mission or campaign turns out to be worth repeating, so it *becomes* a patrol. `patrol.py create <name> --from missions/<origin>`. The originating work still closes normally into its own log, and the patrol is a new record pointing back at what proved the case, not a continuation of it.

The test: **is the recurring thing already established, or is this the moment it became recurring?** The first is a spawn, the second is a promotion. A patrol created by promotion starts at zero runs like any other — the work that proved it does not count as run 1, because it closed under its own tier.

## Lifecycle

1. **Open it.** `python -B tools/patrol.py create <name> [--parent objectives/<name>] [--trigger "weekly"|"nightly 02:00"|"on-demand"]`. State the **purpose** and name the **trigger** — if it is scheduled, say the schedule; if on demand, say what makes someone reach for it.
2. **Fill in the guardrails before the first run.** A patrol runs unattended, so say what should stop it and ask for a human. The template ships four: the gate is NO-GO and a run cannot clear it, the run would touch something outside its declared scope, two consecutive runs make no progress, input volume is far outside normal. Add the ones specific to this patrol and delete none.
3. **Run it**, by hand, via `/loop`, or on a `schedule` routine.
4. **Record every run.** `python -B tools/patrol.py run <name> --note "what it did" --gate GO|NO-GO --learned "what would make the next run better" [--spawned missions/<child>]`. `--learned` is the one that matters. If a run genuinely taught you nothing, that is worth noticing rather than papering over.
5. **Pause when it is not needed** rather than abandoning it — `patrol.py pause` / `resume`. A paused patrol keeps its diary.

## Closing

A patrol ends **retired** or **abandoned**, and both get logged. Retirement because the patrol automated itself out of a job is a success, and the entry should say so.

1. **Rescue anything durable** before the folder goes: artifacts to `control-plane/outputs/{name}/`, vault content to `knowledge/vault/`, code to `projects/{name}/`. `delete` refuses while `_working/` still holds files, so clear it deliberately.
2. **Close it.** `patrol.py retire <name> --reason "..."` or `patrol.py abandon <name> --reason "..."`. Both require a reason.
3. **Write the entry** in `control-plane/patrols/_log.md`: what recurred and on what trigger, how it ran, how it ended, and what is carried forward — most usefully whatever the diary accumulated that outlives the patrol.
4. **Delete.** `patrol.py delete <name>`. Verify the log entry exists first.

## The diary is the point

Ordinary lessons go in the log at close. The **diary** is different: it is written *during* the patrol's life, addressed to the next run, and it is the only reason a recurring job gets cheaper instead of just repeating.

**When a diary entry recurs, stop writing it down and go fix it** — promote it into the patrol's own procedure, a tool, or a skill. A diary that says the same thing three times is a backlog item, not a diary.

## Safety in unattended runs

The guardrails matter *more* here, because nobody is watching each run:

- **The gate decides** — `tools/gate.py` is the deterministic go/no-go; never assume done.
- **Hard safety still enforced** — the `.claude/settings.json` deny-list blocks destructive ops even unattended.
- **Watch the cost** — cheap-per-run × many runs adds up. Keep each run lean, and pause a patrol that is not earning its tokens.
- **Report friction** — where a run needed correction, or asked for approval repeatedly, append the rule to `control-plane/_harness/friction.md`. High approval rates on a recurring job are the clearest signal that setup needs fixing.

## Local unattended trigger (Windows Task Scheduler)

`schedule` (cloud cron routines) can't see local-only paths — no cloud routine can read or write a workspace that only exists on one machine's disk. When a patrol's trigger needs to fire against local-only content, the unattended mechanism is a **Windows Task Scheduler task running `claude -p` headless**, not `schedule`. Say so explicitly in the patrol's Trigger section.

This has a sharp, silent failure mode if built ad hoc: on a machine where `claude` on `PATH` resolves through the VS Code extension shim (`~/.local/bin/claude`, a Bash script with a shebang line), PowerShell's `&` call operator cannot execute it — a shebang script is not a Win32 application. The failure can be *completely silent*: a 0-byte log, Task Scheduler reporting exit code 0, and no trace anywhere that a run was ever attempted. A patrol can go weeks believing it's running when it never has.

**Do not write a bespoke `run.ps1` that calls `& claude` directly.** Every local-trigger patrol's `run.ps1` must be a thin wrapper delegating to a shared `tools/cadence-run.ps1` helper (the name stays `cadence-run.ps1` even in this edition — it's a tool, not a themed artifact), which:

- invokes the shim through Git Bash by its **full resolved path** — never bare `bash` on `PATH`, which resolves to the WSL launcher (a different environment where `claude` isn't on `PATH` at all)
- writes to a timestamped log under the patrol's `_working/`
- checks the log is non-empty and the exit code is 0 after the run, and if either check fails, writes a `FAILED-*.flag` file and exits non-zero — so a no-op run leaves visible evidence instead of masquerading as success

A patrol's own `run.ps1` should do nothing but resolve its prompt file and call the helper:

```powershell
$workspace = "C:\Users\<you>\Workspace"
& (Join-Path $workspace "tools\cadence-run.ps1") `
    -CadenceName "<patrol-name>" `
    -PromptFile (Join-Path $workspace "control-plane\patrols\<patrol-name>\prompt.md") `
    -WorkspaceRoot $workspace
```

Two things this does **not** fix, and both need a deliberate decision when wiring the Task Scheduler task, not a default:

- **Logon type.** `LogonType=Interactive` (the New-ScheduledTaskPrincipal default when authored in-session) only fires if the user already has an active interactive session at trigger time — on a laptop, that's a real gap at midnight/overnight. `LogonType=S4U` runs whether logged on or not (no stored password) and survives a locked screen, but changing a task's principal requires an elevated/admin session — expect this step to need the user, not the agent.
- **Sleep/wake.** Neither logon type fires while the OS itself is asleep. `WakeToRun` would, but forcing a laptop to wake unattended (e.g. in a bag) is a physical-safety tradeoff — treat this as the user's call, never a silent default.
