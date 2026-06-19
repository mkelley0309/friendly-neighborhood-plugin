---
name: loop
description: Run a workstream autonomously over many iterations using Claude Code's native /loop and schedule. Use for long-running work that shouldn't be babysat step by step — iterate until the gate passes, drain a queue, watch a CI run, or run scheduled maintenance. Sets up the loop with hard stop-conditions and the deterministic gate as the go/no-go each pass.
---

# Loop — autonomous long-running work

Some work runs longer than your patience: iterate-until-green, drain a backlog, poll an external job, scheduled upkeep. This hands that to a **bounded, self-checking loop** so you don't babysit every step.

It does **not** reinvent looping — it wires Claude Code's built-ins:

- **`/loop [interval] <command>`** — recurring or self-paced repetition. Omit the interval to let the model pace itself; give one (e.g. `/loop 5m …`) to poll on a clock.
- **`schedule`** — cron-style routines for time-based autonomous runs (nightly, hourly).

The **workstream** is the unit of work; its `index.md` + `workstream-notes.md` carry state across iterations, so each pass resumes where the last left off.

## Protocol

1. **Frame the loop as a bounded workstream.** One iteration = one small, complete unit (advance a step, process one queue item, re-run the gate). If an iteration can't finish in a turn, it's too big — shrink it.
2. **Define hard stop-conditions up front.** Autonomous is not infinite. Stop when: the gate passes, a max-iteration count is hit, no progress is made twice in a row, or a blocker appears. Write them into the workstream's `index.md`.
3. **Make the gate the go/no-go.** Each pass ends with `python -B tools/gate.py run` — if it's GO and the stop-condition is met, end the loop; if NO-GO, do the next bounded unit (or stop if stuck).
4. **Run it.** `/loop <interval?> /harness-core:workstream` (or the specific step), or set a `schedule` routine for time-based runs.
5. **Log every pass** to `workstream-notes` so the trail survives across iterations and sessions.

## Auto-improvement loops

A special loop type: take a **component** (a skill, a CLI, a doc) and iterate it toward its *best self* — with success criteria drawn from the component's own **intent** and the workspace's contracts (the constitution + `.claude/rules`), never a generic metric.

**The loop:** intent → criteria → review → improve → gate → terminate.

1. **Intent + criteria.** State what the component is *for*, then derive its success criteria from that intent + the contracts (semantic density, proportional ceremony, progressive disclosure, honest framing, accurate machinery).
2. **Review + improve.** Diagnose what's actually weak, then apply the fix with **minimum force** — fix what's wrong, don't over-rewrite or gold-plate what isn't.
3. **Gate.** Run the deterministic gate each pass (`python -B tools/gate.py run`, plus `validate --strict` / `py_compile` where they apply). GO, or fix and re-gate.
4. **Terminate** when the gate is GO **and** returns diminish. "No improvement found" is a valid, honest pass — don't manufacture change, and stop before over-polishing.

Run it like any loop: `/loop /harness-core:loop` over a component list, one component per pass.

## Safety in autonomous mode (no human in the loop)

The guardrails matter *more* here, because nobody's watching each step:

- **The gate decides** — `tools/gate.py` is the deterministic go/no-go; never assume done.
- **Hard safety still enforced** — the `.claude/settings.json` deny-list blocks destructive ops even unattended.
- **Watch the cost** — cheap-per-pass × many iterations adds up; keep each pass lean and cap the iteration count.

A loop is patient, cheap, bounded, and self-checking — not a daemon that burns tokens forever.
