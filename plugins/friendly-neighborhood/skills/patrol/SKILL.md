---
name: patrol
description: A lightweight unit of work — a small, often repeatable task done under a mission or standalone (add a source, refresh data, lint an area, one iteration against a mission). Trigger for quick work that doesn't warrant the full mission lifecycle. A patrol tracks itself lightly — its assignment, a handoff to other patrols, lessons learned — just enough admin, no heavy distillation.
---

# Patrol — a lightweight work unit

A patrol is the smallest tracked unit: a quick, often repeatable task. *Add a source to the curation pipeline. Refresh one source's data. Lint a vault area. Run one iteration against a mission.* If the work is complex, multi-session, or needs handoffs across phases, it isn't a patrol — open a **mission** (`/friendly-neighborhood:mission`) and run the full lifecycle.

**Proportional admin — this is the whole point.** A patrol carries *just enough* tracking to be resumable, handed off, and learned from, and no more. Don't impose mission-grade progressive distillation on a one-shot task: at this size the overhead — and the lossy, sometimes-inaccurate nature of distillation — costs more than it's worth. A small unit that simply *understands its assignment* and records the few things worth keeping beats a heavyweight ceremony.

## Lifecycle (light)

1. **Create + state the assignment.** `python -B tools/patrol.py create <name> [--parent workstreams/<mission>|objectives/<obj>] [--title]`. Write the **assignment** in its `index.md` — what you understand the job to be, in a sentence or two. That understanding is the patrol's real value.
2. **Do the work**, keeping the checklist current. Pick a driver that fits: `peter` (general), `miles` (a surgical change), `noir` (a debug pass), `silk` (a lookup), `ben-reilly` (a small refactor).
3. **Validate — don't close on faith.** Run the gate (`python -B tools/gate.py run`) or otherwise confirm it actually worked, then `python -B tools/patrol.py validate <name>`. Claiming done without checking is Mysterio.
4. **Capture handoff + lessons (one line each, if any).** If another patrol picks up from here, write a one-line **handoff**. If you learned something worth repeating or avoiding, write a one-line **lesson**. That's the entire ledger — skip what doesn't apply.
5. **Complete.** `python -B tools/patrol.py complete <name>`.

## When to promote

If a patrol starts to grow — multiple sessions, real research, design decisions, cross-phase handoffs — **stop and promote it to a mission**: open a mission and make this patrol its first iteration. Promote rather than bloat a patrol into a pseudo-mission.

## The record (kept light)

A patrol's `index.md` holds, *proportionally*: the **Assignment** (what it is), a **Checklist**, a **Handoff** line (for the next patrol), and **Lessons** (worth keeping). Any section a given patrol doesn't need, leave empty.
