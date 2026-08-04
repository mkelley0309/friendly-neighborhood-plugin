---
name: mission
description: A lightweight unit of work — a small, often repeatable task done under a campaign or standalone (add a source, refresh data, lint an area, one iteration against a campaign). Trigger for quick work that doesn't warrant the full campaign lifecycle. A mission tracks itself lightly — its assignment, a handoff to other missions, lessons learned — just enough admin, no heavy distillation.
---

# Mission — a lightweight work unit

A mission is the smallest tracked unit: a quick, often repeatable task. *Add a source to the curation pipeline. Refresh one source's data. Lint a vault area. Run one iteration against a campaign.* If the work is complex, multi-session, or needs handoffs across phases, it isn't a mission — open a **campaign** (`/friendly-neighborhood-lite:campaign`) and run the full lifecycle.

**Proportional admin — this is the whole point.** A mission carries *just enough* tracking to be resumable, handed off, and learned from, and no more. Don't impose campaign-grade progressive distillation on a one-shot task: at this size the overhead — and the lossy, sometimes-inaccurate nature of distillation — costs more than it's worth. A small unit that simply *understands its assignment* and records the few things worth keeping beats a heavyweight ceremony.

## Lifecycle (light)

1. **Create + state the assignment.** `python -B tools/mission.py create <name> [--parent workstreams/<campaign>|objectives/<obj>] [--title]`. Write the **assignment** in its `index.md` — what you understand the job to be, in a sentence or two. That understanding is the mission's real value.
2. **Do the work**, keeping the checklist current. Pick a driver that fits: `peter` (general), `noir` (a debug or surgical pass).
3. **Validate — don't close on faith.** Run the gate (`python -B tools/gate.py run`) or otherwise confirm it actually worked, then `python -B tools/mission.py validate <name>`. Claiming done without checking is Mysterio.
4. **Capture handoff + lessons + friction (one line each, if any).** If another mission picks up from here, write a one-line **handoff**. If you learned something worth repeating or avoiding, write a one-line **lesson**. If the *harness* got in your way, write a one-line **friction**. Skip what doesn't apply.
5. **Resolve every checkbox.** A completed mission must contain no `- [ ]`. Frontmatter `status` is the *portfolio* signal, but an unchecked box is a *file-level* signal, and anything reading checkboxes rather than frontmatter keeps reporting a closed mission as live work. Tick it, or delete it and state the outcome as prose — never tick something that did not happen.
6. **Rescue anything durable.** The folder is deleted at step 8, so sweep it first: produced artifacts to `control-plane/outputs/{name}/`, vault content to `knowledge/vault/`, source material to `intake/_archive/`, code to `projects/{name}/`. Most missions hold nothing but their own `index.md`, but the one that does is the one that loses primary evidence.
7. **Write the log entry** in `control-plane/missions/_log.md`, newest first, as a dated section — *Was / Produced / Carried forward / Handoff*. **This is the durable record**, since the folder does not survive. Keep it proportional, but not so thin the work becomes unreconstructable.
8. **Complete, then delete.** `python -B tools/mission.py complete <name>` then `python -B tools/mission.py delete <name>`. Verify the log entry exists before deleting.

## When to promote

If a mission starts to grow — multiple sessions, real research, design decisions, cross-phase handoffs — **stop and promote it to a campaign**: open a campaign and make this mission its first iteration. Promote rather than bloat a mission into a pseudo-campaign. Promote *before* completing, since completing deletes the folder.

## The record (kept light)

While the mission is open, its `index.md` holds, *proportionally*: the **Assignment** (what it is), a **Checklist**, a **Handoff** line (for the next mission), **Lessons** (worth keeping), and **Friction** (how the harness performed). Any section a given mission doesn't need, leave empty.

**That file is working state, not the archive.** At completion it collapses into one dated entry in `control-plane/missions/_log.md` and the folder is deleted. So the question at close is always *what would someone need six months from now* — usually the assignment, what came out, and the one lesson. Rarely the checklist.

## Friction vs. Lessons

Two different things, and conflating them is what bloats a record:

- **Lessons** are about *this work* — "the API paginates at 100, not 50."
- **Friction** is about *the harness* — "`mission.py validate` gave no output on success, so I couldn't tell it had run."

The test: **would this still be true and useful on a completely unrelated mission?** If yes it is friction; if it names the subject matter it is a lesson.

Both are too big for the mission record alone, and both get carried out at completion for the same reason — a thing noticed once inside one folder will not be noticed twice:

- Lessons → `control-plane/missions/_log.md`, the running log, one entry per completed mission.
- Unresolved friction → `control-plane/_harness/friction.md`, the cross-run harness ledger. Record the rule, not the incident. Most missions produce none.

In both ledgers **recurrence is the signal**. An entry appearing twice has outgrown the log and belongs in a skill, a tool, or a checklist.
