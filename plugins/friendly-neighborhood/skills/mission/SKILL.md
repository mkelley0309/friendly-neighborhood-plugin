---
name: mission
description: A lightweight unit of work — a small, often repeatable mission done under a campaign or standalone (add a source, refresh data, lint an area, one iteration against a campaign). Trigger for quick work that doesn't warrant the full campaign lifecycle. A mission tracks itself lightly — its mission, a handoff to other missions, lessons learned — just enough admin, no heavy distillation.
---

# Mission — a lightweight work unit

A mission is the smallest tracked unit: a quick, often repeatable piece of work. *Add a source to the pipeline. Refresh one source's data. Lint an area. Run one iteration against a campaign.* If the work is complex, multi-session, or needs handoffs across phases, it isn't a mission — open a **campaign** (`/friendly-neighborhood:campaign`) and run the full lifecycle.

**Proportional admin — this is the whole point.** A mission carries *just enough* tracking to be resumable, handed off, and learned from, and no more. Don't impose workstream-grade progressive distillation on a one-shot job: at this size the overhead costs more than it's worth. A small unit that simply *understands its mission* and records the few things worth keeping beats a heavyweight ceremony.

## Lifecycle (light)

1. **Create + state the mission.** `python -B tools/mission.py create <name> [--parent workstreams/<name>|objectives/<obj>] [--title]`. Write the **mission** in its `index.md` — what you understand the job to be, in a sentence or two. That understanding is the mission's real value.
2. **Do the work**, keeping the checklist current.
3. **Validate — don't close on faith.** Run the gate (`python -B tools/gate.py run`) or otherwise confirm it actually worked, then `python -B tools/mission.py validate <name>`. Claiming done without checking wastes the next person's time.
4. **Capture handoff + lessons (one line each, if any).** If another mission picks up from here, write a one-line **handoff**. If you learned something worth repeating or avoiding, write a one-line **lesson**. That's the entire ledger — skip what doesn't apply.
5. **Note any harness friction (usually none).** If the *framework* got in your way — a tool that misbehaved, an instruction that was wrong, an access scope too narrow — add one line under **Friction**. See *Friction vs. Lessons* below.
6. **Rescue, log, complete, delete.** Move anything durable out of the folder (artifacts to `outputs/`, vault content to `knowledge/vault/`, sources to `intake/_archive/`), write a dated entry in `control-plane/missions/_log.md` — *was / produced / carried forward / handoff* — then `python -B tools/mission.py complete <name>` and `python -B tools/mission.py delete <name>`. **The folder does not survive completion.** Verify the log entry before deleting.

## When to promote

If a mission starts to grow — multiple sessions, real research, design decisions, cross-phase handoffs — **stop and promote it to a campaign**: open a campaign and make this mission its first iteration. Promote rather than bloat a mission into a pseudo-campaign.

## The record (kept light)

While the mission is open, its `index.md` holds, *proportionally*: the **Mission** (what it is), a **Checklist**, a **Handoff** line (for the next mission), **Lessons** (worth keeping), and **Friction** (how the harness performed). Any section a given mission doesn't need, leave empty.

**That file is working state, not the archive.** At completion it collapses into one dated entry in `control-plane/missions/_log.md` and the folder is deleted. So the question at close is always *what would someone need six months from now* — usually the mission, what came out, and the one lesson. Rarely the checklist. Anything that is a real artifact rather than a record belongs in `outputs/`, the vault, or a project **before** the folder goes.

## Friction vs. Lessons

Two different things, and conflating them is what bloats a record:

- **Lessons** are about *this work* — "the API paginates at 100, not 50."
- **Friction** is about *the harness* — "`mission.py validate` gave no output on success, so I couldn't tell it had run." These are how the framework itself is performing.

The test: **would this still be true and useful on a completely unrelated mission?** If yes it is friction; if it names the subject matter it is a lesson.

Both are too big for the mission record alone, and both get carried out at completion for the same reason — a thing noticed once inside one folder will not be noticed twice:

- Lessons → `control-plane/missions/_log.md`, the running mission log, one row per completed mission.
- Unresolved friction → `control-plane/_harness/friction.md`, the cross-run harness ledger. Record the rule, not the incident. Most missions produce none.

In both ledgers **recurrence is the signal**. An entry appearing twice has outgrown the log and belongs in a skill, a tool, or a checklist.
