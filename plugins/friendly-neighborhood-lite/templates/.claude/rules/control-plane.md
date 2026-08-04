---
description: Operating contract for the control-plane subtree — orchestration layer for responsibilities, missions, and patrols.
paths: ["control-plane/**"]
---

# Control Plane

The orchestration layer. Coordinates responsibilities, missions, and patrols; does not execute domain logic in place.

---

## Layout

```
control-plane/
  CLAUDE.md                 ← thin pointer (contract is here)
  intake/                   ← capture layer for unstructured input (pre-triage)
    index.md              ← intake conventions and lifecycle
    {item}.md             ← one file per captured idea or note
  objectives/               ← long-lived, review-cycle-measured responsibilities
    index.md              ← portfolio index of active responsibilities
    {name}/
      index.md            ← responsibility anchor (Key Results, milestones, missions, decisions log)
      {supporting files}    ← retained after completion; never deleted
  workstreams/              ← missions: the heavy QRDPIV lifecycle
    index.md              ← portfolio index of active missions
    {name}/
      index.md            ← mission status anchor (phase, health)
      request.md | research.md | design.md | plan.md | worktree-{nn}.md
      friction-log.md       ← how the *harness* performed; never what the work found
      _working/             ← throwaway scratch
    _log/
      YYYY-MM-DD-{name}.md  ← durable summary after cleanup
  patrols/                  ← lightweight units (often iterations against a mission)
    index.md              ← portfolio index of active patrols
    _log.md               ← durable record of every completed patrol; never deleted
    {name}/
      index.md            ← patrol record (assignment, checklist, handoff, lessons, friction)
  stakeouts/                ← recurring work, scheduled or on demand
    index.md              ← portfolio index of active stakeouts
    _log.md               ← durable record of every retired/abandoned stakeout
    {name}/                 ← deleted at close, once logged
      index.md            ← purpose, trigger, guardrails, run log, self-improvement diary
      _working/             ← scratch, for runs needing mission-style handoffs
  _harness/                 ← the harness's own feedback loop; never deleted
    friction.md           ← cross-run ledger of unresolved framework friction
  outputs/                  ← durable artifacts produced by missions (never deleted)
    index.md              ← index of all outputs, organized by mission
    {mission-name}/       ← one folder per mission that produced artifacts
      {artifact files}    ← slides, documents, configs, generated content, etc.
```

---

## The Tiers

**Intake** = unstructured capture. Ideas, notes, partial thoughts land here before triage. Lifecycle: `capture → triage → promote or discard`. Promoted items become responsibilities, missions, or patrols; discarded leave no trace.

**Responsibilities** (objectives, top tier) = the long-lived "why" — a role, a measured annual objective, a career goal. Carry structured progress tracking: Key Results, milestones, linked missions, a review cadence, health, and an append-only decisions log. One folder per responsibility. Lifecycle: `active` → `complete`; folders never deleted (the decisions log is the durable value). Driven by `objective.py`.

**Missions** (workstreams, middle tier) = complex work that spans multiple sessions and handoffs, run through the heavy **QRDPIV** lifecycle. On cleanup the folder is deleted *after* a durable log entry is written to `workstreams/_log/`. A mission may be parented to a responsibility, or be standalone. Driven by `workstream.py`.

**Patrols** (bottom tier) = lightweight, often-repeatable units — add a source, refresh data, lint an area, or run one iteration against a mission. A patrol carries *proportional* admin only (assignment, checklist, handoff, lessons) — no phase machine, no progressive distillation. On completion the folder is deleted *after* a dated entry is written to `patrols/_log.md`, which is the durable record: rescue anything real to `outputs/`, the vault or a project first, since nothing else survives. If a patrol grows (multiple sessions, real research, design decisions), **promote it to a mission** — before completing, since completing deletes the folder. Driven by `patrol.py`.

**Stakeouts** = work defined by its **recurrence**, not its size — refresh sources into the vault, drain a cleanup queue, report portfolio status, auto-lint. May be patrol-sized or mission-sized; what makes it a stakeout is that it runs again, scheduled or on demand. Carries a **self-improvement diary** so each run makes the next cheaper, and `_working/` for runs needing handoffs. Lifecycle: `active` → `paused` → `retired` (done or automated away) or `abandoned`; folder deleted once logged. Driven by `stakeout.py`.

**Outputs** = durable artifacts produced during mission implementation. Written to `outputs/{mission-name}/` — never inside the mission folder. This guarantees cleanup (which deletes the mission folder) cannot destroy produced artifacts. The `outputs/` tree is permanent.

---

## Hierarchy

```
responsibility                <- long-lived strategy, measured
    |-- mission               <- heavy QRDPIV lifecycle, multi-session
    |       \-- patrol        <- spawned child unit
    |-- patrol                <- lightweight unit, standalone
    \-- stakeout              <- recurring; runs again, scheduled or on demand
            |-- patrol        <- spawned by a run
            \-- mission       <- spawned by a bigger run
```

**This is a spawn graph, not a strict tree.** Tier is chosen by *shape*, not size:
**bounded and single-session** -> patrol, **multi-session with handoffs** -> mission,
**it runs again** -> stakeout.

A mission spawns child patrols for parallel or repeatable sub-units. A stakeout spawns whatever a
given run deserves: nothing at all for a small inline run, a patrol for a bounded one, a mission for
one that needs real handoffs. **A spawned child runs its own lifecycle and closes into its own log**,
so the parent holds the coordination, not the work.

- A patrol's `parent` may be `missions/{name}`, `stakeouts/{name}`, `objectives/{name}`, or `null`.
- A mission's `parent` may be `objectives/{name}`, `stakeouts/{name}`, or `null`.
- A stakeout's `parent` may be `objectives/{name}` or `null`.
- Responsibilities are the top tier; they are never children of another artifact.

---

## Session Entry

1. Read this rule (auto-loaded when working on control-plane files)
2. Read `objectives/index.md`, `workstreams/index.md`, `patrols/index.md`, and `stakeouts/index.md`
3. If unstructured input needs triage, read `intake/index.md` first
4. If a specific item is in scope, read its `index.md`
5. Identify current phase (missions), review state (responsibilities), or assignment (patrols)
6. **State scope, phase/status, and intended next action before proceeding**

---

## Skill Routing (Claude Code)

| Situation | Skill |
|---|---|
| Unstructured input needing capture or triage | land in `intake/` first, then route |
| New or in-progress responsibility | `responsibility` |
| Complex multi-session work | `mission` |
| Lightweight unit or iteration against a mission | `patrol` |
| Work that runs again — scheduled or on demand | `stakeout` |
| Read/write/search the Obsidian vault | `obsidian-cli` (primary) |
| Author Obsidian-flavored markdown (wikilinks, callouts, frontmatter) | `obsidian-markdown` |
| `.base` files (views, filters, formulas) | `obsidian-bases` |
| `.canvas` files | `json-canvas` |
| Extract clean markdown from web pages into vault | `defuddle` |

---

## Mission Framework (QRDPIV)

**QRDPIV** (default): Questions → Research → Design → Plan → Implement → Validate → Cleanup
**RPIV** (spec already clear): Research → Plan → Implement → Validate → Cleanup

Questions are cheap. Under-shaped work is expensive. Use the full QRDPIV the moment ambiguity, cross-system scope, or missing constraints surface. **Validate** runs the deterministic gate (`gate.py`) plus adversarial QA before cleanup — nothing is called done on faith.

Phase mechanics, artifact templates, and action-file routing live in the `mission` skill. Patrols do **not** use this framework — they are deliberately lightweight.

---

## State Models

### Mission `index.md` frontmatter

```yaml
workstream: kebab-case-name
framework: rpiv | qrdpiv
workstream_phase: questions | research | design | plan | implement | validate | complete | cleanup
workstream_health: healthy | needs-questions | needs-design | under-shaped | blocked | stale
status: active | complete | paused | abandoned
started: YYYY-MM-DD
completed: YYYY-MM-DD
parent: null | "objectives/{name}"
```

### Patrol `index.md` frontmatter

```yaml
patrol: kebab-case-name
status: active | complete
parent: null | "workstreams/{name}" | "objectives/{name}"
started: YYYY-MM-DD
completed: YYYY-MM-DD
validated: YYYY-MM-DD
tags: [patrol/{name}]
```

A patrol's body holds, *proportionally*: **Assignment**, **Checklist**, **Handoff**, **Lessons**, **Cross-links**. Leave empty any section it doesn't need.

### Responsibility `index.md` frontmatter

```yaml
objective: kebab-case-name
status: active | complete
health: on-track | at-risk | blocked | stale
cadence: "<review cadence>"
created: YYYY-MM-DD
completed: YYYY-MM-DD
tags: [objective, ...]
```

Responsibilities carry a **Key Results** table, a **Milestones** checklist, a **Missions** roster (linked via `link-mission`), and an append-only **Key Decisions Log** — never truncated.

---

## Delegation Model

1. Interpret request into a structured responsibility
2. Identify required capabilities and targets (`projects/`, `knowledge/`, `tools/`, external)
3. Decompose into discrete steps with owning targets
4. Delegate — use subagents where token budget justifies (see `_addenda/claude-code.md` for model selection)
5. Collect outputs; reconcile against plan
6. Validate completeness against original intent

---

## Boundaries

- Do not implement domain logic — delegate to `projects/`
- Do not write source data — belongs in `knowledge/sources/`
- Do not bypass project boundaries to "just fix it quickly"
- Maintain separation: planning here, execution in projects
