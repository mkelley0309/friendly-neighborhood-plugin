---
name: stakeout
description: Run a patrol autonomously over many iterations — a long, patient watch — using Claude Code's native /loop and schedule. Use for long-running work that shouldn't be babysat step by step — iterate until the gate passes, drain a queue, watch a CI run, or run scheduled maintenance. Sets up the loop with hard stop-conditions and the verification gate as the go/no-go each pass.
---

# Stakeout — the long autonomous watch

Some work runs longer than your patience: iterate-until-green, drain a backlog, poll an external job, scheduled upkeep. A stakeout hands that to a **bounded, self-checking loop** so you don't babysit every step.

This skill does **not** reinvent looping — it wires Claude Code's built-ins:

- **`/loop [interval] <command>`** — recurring or self-paced repetition. Omit the interval to let the model pace itself; give one (e.g. `/loop 5m …`) to poll on a clock.
- **`schedule`** — cron-style routines for time-based autonomous runs (nightly, hourly).

The **patrol** is the unit of work; its `index.md` + `workstream-notes.md` carry state across iterations, so each pass picks up where the last left off.

## Protocol

1. **Frame the loop as a bounded patrol.** One iteration = one small, complete unit (advance a step, process one queue item, re-run the gate). If an iteration can't finish in a turn, it's too big — shrink it.
2. **Define hard stop-conditions up front.** Autonomous is not infinite. Stop when: the gate passes, a max-iteration count is hit, no progress is made twice in a row, or a blocker appears. Write them into the patrol's `index.md`.
3. **Make the gate the go/no-go.** Each pass ends by running `python -B tools/gate.py run` — if it's GO and the stop-condition is met, end the loop; if NO-GO, do the next bounded unit (or stop if stuck).
4. **Run it.** `/loop <interval?> /friendly-neighborhood:patrol` (or the specific step), or set a `schedule` routine for time-based runs.
5. **Log every pass** to `workstream-notes` so the trail survives across iterations and sessions.

## Auto-improvement loops

A special loop type: take a **component** (a skill, an agent, a CLI, a doc) and iterate it toward its *best self* — with success criteria drawn from the component's own **intent** and this harness's **creed**, never a generic metric.

**The loop:** intent → criteria → review → improve → gate → terminate.

1. **Intent + criteria.** State what the component is *for*, then derive its success criteria from that intent + the creed (semantic density, proportional ceremony, progressive disclosure, honest framing, accurate machinery — specialized per component type).
2. **Review + improve.** `noir` diagnoses what's actually weak; `ben-reilly` applies the fix *without over-rewriting* (his standing guardrail). Minimum force — fix what's wrong, don't gold-plate what isn't.
3. **Gate.** Run the deterministic gate each pass (`python -B tools/gate.py run`, plus `validate --strict` / `py_compile` where they apply). GO, or fix and re-gate.
4. **Terminate** when the gate is GO **and** no high-confidence dissent remains **and** returns diminish. "No improvement found" is a valid, honest pass — don't manufacture change.

**The council that keeps the loop honest** (full map in `/friendly-neighborhood:creed`):

- `lizard` — **diminishing returns.** When another pass is just over-polishing, his approval is the signal to stop.
- `kraven` — **wrong direction.** When the loop has drifted off the component's real intent onto a side-target, he'd approve — re-aim or stop.
- `mysterio` — **unverified improvement.** Never call a component "better" without the gate confirming it.

Run it like any stakeout: `/loop /friendly-neighborhood:stakeout` over a component list, one component per pass.

## Safety in autonomous mode (no human in the loop)

The guardrails matter *more* here, because nobody's watching each step:

- **The gate decides** — `tools/gate.py` is the deterministic go/no-go; never "feel" done (that's Mysterio).
- **Hard safety still enforced** — spider-sense (`PreToolUse`) + the deny-list block destructive ops even unattended.
- **The symbiote stays capped** — escalation is turn-limited per pass; the church bell kills a runaway clone.
- **Watch the cost** — Everyman budget × many iterations is how **Kingpin** wins. Keep each pass cheap; cap iterations.
- **Villains on watch:** `venom` (escalating every pass), `carnage` (destructive unattended), `kingpin` (token burn over the long run), `mysterio` (declaring done without the gate).

A stakeout is patient, cheap, bounded, and self-checking — not a daemon that burns tokens forever.
