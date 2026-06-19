---
name: task
description: A lightweight unit of work — a small, often repeatable task done under a workstream or standalone (add a source, refresh data, lint an area, one iteration against a workstream). Trigger for quick work that doesn't warrant the full workstream lifecycle. A task tracks itself lightly — its assignment, a handoff to other tasks, lessons learned — just enough admin, no heavy distillation.
---

# Task — a lightweight work unit

A task is the smallest tracked unit: a quick, often repeatable piece of work. *Add a source to the pipeline. Refresh one source's data. Lint an area. Run one iteration against a workstream.* If the work is complex, multi-session, or needs handoffs across phases, it isn't a task — open a **workstream** (`/harness-core:workstream`) and run the full lifecycle.

**Proportional admin — this is the whole point.** A task carries *just enough* tracking to be resumable, handed off, and learned from, and no more. Don't impose workstream-grade progressive distillation on a one-shot job: at this size the overhead costs more than it's worth. A small unit that simply *understands its assignment* and records the few things worth keeping beats a heavyweight ceremony.

## Lifecycle (light)

1. **Create + state the assignment.** `python -B tools/task.py create <name> [--parent workstreams/<name>|objectives/<obj>] [--title]`. Write the **assignment** in its `index.md` — what you understand the job to be, in a sentence or two. That understanding is the task's real value.
2. **Do the work**, keeping the checklist current.
3. **Validate — don't close on faith.** Run the gate (`python -B tools/gate.py run`) or otherwise confirm it actually worked, then `python -B tools/task.py validate <name>`. Claiming done without checking wastes the next person's time.
4. **Capture handoff + lessons (one line each, if any).** If another task picks up from here, write a one-line **handoff**. If you learned something worth repeating or avoiding, write a one-line **lesson**. That's the entire ledger — skip what doesn't apply.
5. **Complete.** `python -B tools/task.py complete <name>`.

## When to promote

If a task starts to grow — multiple sessions, real research, design decisions, cross-phase handoffs — **stop and promote it to a workstream**: open a workstream and make this task its first iteration. Promote rather than bloat a task into a pseudo-workstream.

## The record (kept light)

A task's `index.md` holds, *proportionally*: the **Assignment** (what it is), a **Checklist**, a **Handoff** line (for the next task), and **Lessons** (worth keeping). Any section a given task doesn't need, leave empty.
