---
description: Operating contract for the control-plane subtree — orchestration layer for objectives, workstreams, and assignments.
paths: ["control-plane/**"]
---

# Control Plane

The orchestration layer. Coordinates objectives, workstreams, and assignments; does not execute domain logic in place.

---

## Layout

```
control-plane/
  CLAUDE.md                 ← thin pointer (contract is here)
  intake/                   ← capture layer for unstructured input (pre-triage)
    index.md              ← intake conventions and lifecycle
    {item}.md             ← one file per captured idea or note
  objectives/               ← long-lived, review-cycle-measured objectives
    index.md              ← portfolio index of active objectives
    {name}/
      index.md            ← objective anchor (Key Results, milestones, workstreams, decisions log)
      {supporting files}    ← retained after completion; never deleted
  workstreams/              ← the heavy QRDPIV lifecycle: complex, multi-session work
    index.md              ← portfolio index of active workstreams
    {name}/
      index.md            ← workstream status anchor (phase, health)
      request.md | research.md | design.md | plan.md | worktree-{nn}.md
      friction-log.md       ← how the *harness* performed; never what the work found
      _working/             ← throwaway scratch
    _log/
      YYYY-MM-DD-{name}.md  ← durable summary after cleanup
  assignments/                    ← lightweight units (often iterations against a workstream)
    index.md              ← portfolio index of active assignments
    _log.md               ← durable record of every completed assignment; never deleted
    {name}/                 ← deleted at completion, once logged
      index.md            ← assignment record (assignment, checklist, handoff, lessons, friction)
  cadences/                ← recurring work, scheduled or on demand
    index.md              ← portfolio index of active cadences
    _log.md               ← durable record of every retired/abandoned cadence
    {name}/                 ← deleted at close, once logged
      index.md            ← purpose, trigger, guardrails, run log, self-improvement diary
      _working/             ← scratch, for runs needing workstream-style handoffs
  _harness/                 ← the harness's own feedback loop; never deleted
    friction.md           ← cross-run ledger of unresolved framework friction
  outputs/                  ← durable artifacts produced by workstreams (never deleted)
    index.md              ← index of all outputs, organized by workstream
    {workstream-name}/    ← one folder per workstream that produced artifacts
      {artifact files}    ← slides, documents, configs, generated content, etc.
```

---

## The Tiers

**Intake** = unstructured capture. Ideas, notes, partial thoughts land here before triage. Lifecycle: `capture → triage → promote or discard`. Promoted items become objectives, workstreams, or assignments; discarded leave no trace.

**Objectives** (top tier) = the long-lived "why" — a role, a measured annual objective, a career goal. Carry structured progress tracking: Key Results, milestones, linked workstreams, a review cadence, health, and an append-only decisions log. One folder per objective. Lifecycle: `active` → `complete`; folders never deleted (the decisions log is the durable value). Driven by `objective.py`.

**Workstreams** (middle tier) = complex work that spans multiple sessions and handoffs, run through the heavy **QRDPIV** lifecycle. On cleanup the folder is deleted *after* a durable log entry is written to `workstreams/_log/`. A workstream may be parented to an objective, or be standalone. Driven by `workstream.py`.

**Assignments** (bottom tier) = lightweight, often-repeatable units — add a source, refresh data, lint an area, or run one iteration against a workstream. An assignment carries *proportional* admin only (assignment, checklist, handoff, lessons) — no phase machine, no progressive distillation. If an assignment grows (multiple sessions, real research, design decisions), **promote it to a workstream**. Driven by `assignment.py`.

**Cadences** = work defined by its **recurrence**, not its size — refresh sources into the vault, drain a cleanup queue, report portfolio status, auto-lint. May be assignment-sized or workstream-sized; what makes it a cadence is that it runs again, scheduled or on demand. Carries a **self-improvement diary** so each run makes the next cheaper, and `_working/` for runs needing handoffs. Lifecycle: `active` → `paused` → `retired` (done or automated away) or `abandoned`; folder deleted once logged. Driven by `cadence.py`.

**Outputs** = durable artifacts produced during workstream implementation. Written to `outputs/{workstream-name}/` — never inside the workstream folder. This guarantees cleanup (which deletes the workstream folder) cannot destroy produced artifacts. The `outputs/` tree is permanent.

---

## Hierarchy

```
objective                     <- long-lived strategy, measured
    |-- workstream            <- heavy QRDPIV lifecycle, multi-session
    |       \-- assignment           <- spawned child unit
    |-- assignment                  <- lightweight unit, standalone
    \-- cadence              <- recurring; runs again, scheduled or on demand
            |-- assignment          <- spawned by a run
            \-- workstream    <- spawned by a bigger run
```

**This is a spawn graph, not a strict tree.** Tier is chosen by *shape*, not size:
**bounded and single-session** -> assignment, **multi-session with handoffs** -> workstream,
**it runs again** -> cadence.

A workstream spawns child assignments for parallel or repeatable sub-units. A cadence spawns whatever a
given run deserves: nothing at all for a small inline run, an assignment for a bounded one, a workstream for
one that needs real handoffs. **A spawned child runs its own lifecycle and closes into its own log**,
so the parent holds the coordination, not the work.

- An assignment's `parent` may be `workstreams/{name}`, `cadences/{name}`, `objectives/{name}`, or `null`.
- A workstream's `parent` may be `objectives/{name}`, `cadences/{name}`, or `null`.
- A cadence's `parent` may be `objectives/{name}` or `null`.
- Objectives are the top tier; they are never children of another artifact.

### Autonomy mechanisms (`/goal`, `/loop`, `schedule`)

These are **mechanisms, not tiers** — they say *how* a unit of work keeps going, and any tier can use them. Pick by what ends the work:

| Mechanism | Repeats until | Use at |
|---|---|---|
| `/goal <condition>` | a stated condition holds, then self-clears | assignment · a workstream phase · one cadence run |
| `/loop [interval]` | you stop it | a cadence run that polls |
| `schedule` | its cron says otherwise | a cadence trigger |

**`/goal` applies wherever the work has a verifiable end state inside a session.** That is an assignment ("the checklist is complete and the gate reported GO"), a workstream *phase* ("every plan step is checked"), or a *single* cadence run ("the queue is drained"). It does **not** apply to an objective, which is measured in review cycles against Key Results and deliberately outlives any session, nor to a cadence itself, which by definition never completes.

The evaluator judges the condition against **what has been surfaced in the conversation** — it does not run commands or read files — so a run must *print* its gate result for `"the gate passes"` to be usable. `/goal` also needs an accepted trust dialog and is unavailable under `disableAllHooks` or `allowManagedHooksOnly`, so anything depending on it should say so in its guardrails.

---

## Session Entry

1. Read this rule (auto-loaded when working on control-plane files)
2. Read `objectives/index.md`, `workstreams/index.md`, `assignments/index.md`, and `cadences/index.md`
3. If unstructured input needs triage, read `intake/index.md` first
4. If a specific item is in scope, read its `index.md`
5. Identify current phase (workstreams), review state (objectives), or assignment (assignments)
6. **State scope, phase/status, and intended next action before proceeding**

---

## Skill Routing (Claude Code)

| Situation | Skill |
|---|---|
| Unstructured input needing capture or triage | land in `intake/` first, then route |
| New or in-progress objective | `objective` |
| Complex multi-session work | `workstream` |
| Lightweight unit or iteration against a workstream | `assignment` |
| Work that runs again — scheduled or on demand | `cadence` |
| Read/write/search the Obsidian vault | `obsidian-cli` (primary) |
| Author Obsidian-flavored markdown (wikilinks, callouts, frontmatter) | `obsidian-markdown` |
| `.base` files (views, filters, formulas) | `obsidian-bases` |
| `.canvas` files | `json-canvas` |
| Extract clean markdown from web pages into vault | `defuddle` |

---

## Workstream Framework (QRDPIV)

**QRDPIV** (default): Questions → Research → Design → Plan → Implement → Validate → Cleanup
**RPIV** (spec already clear): Research → Plan → Implement → Validate → Cleanup

Questions are cheap. Under-shaped work is expensive. Use the full QRDPIV the moment ambiguity, cross-system scope, or missing constraints surface. **Validate** runs the deterministic gate (`gate.py`) plus adversarial QA before cleanup — nothing is called done on faith.

Phase mechanics, artifact templates, and action-file routing live in the `workstream` skill. Assignments do **not** use this framework — they are deliberately lightweight.

---

## State Models

### Workstream `index.md` frontmatter

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

### Assignment `index.md` frontmatter

```yaml
assignment: kebab-case-name
status: active | complete
parent: null | "workstreams/{name}" | "objectives/{name}"
started: YYYY-MM-DD
completed: YYYY-MM-DD
validated: YYYY-MM-DD
tags: [assignment/{name}]
```

An assignment's body holds, *proportionally*: **Assignment**, **Checklist**, **Handoff**, **Lessons**, **Cross-links**. Leave empty any section it doesn't need.

### Objective `index.md` frontmatter

```yaml
objective: kebab-case-name
status: active | complete
health: on-track | at-risk | blocked | stale
cadence: "<review cadence>"
created: YYYY-MM-DD
completed: YYYY-MM-DD
tags: [objective, ...]
```

Objectives carry a **Key Results** table, a **Milestones** checklist, a **Workstreams** roster (linked via `link-workstream`), and an append-only **Key Decisions Log** — never truncated.

---

## Delegation Model

1. Interpret request into a structured objective
2. Identify required capabilities and targets (`projects/`, `knowledge/`, `tools/`, external)
3. Decompose into discrete steps with owning targets
4. Delegate — use subagents where token budget justifies (see root `CLAUDE.md` for model selection)
5. Collect outputs; reconcile against plan
6. Validate completeness against original intent

---

## Boundaries

- Do not implement domain logic — delegate to `projects/`
- Do not write source data — belongs in `knowledge/sources/`
- Do not bypass project boundaries to "just fix it quickly"
- Maintain separation: planning here, execution in projects
