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
      workstream-notes.md   ← self-learning ledger (every phase appends)
      _working/             ← throwaway scratch
    _log/
      YYYY-MM-DD-{name}.md  ← durable summary after cleanup
  patrols/                  ← lightweight units (often iterations against a mission)
    index.md              ← portfolio index of active patrols
    {name}/
      index.md            ← patrol record (assignment, checklist, handoff, lessons)
  outputs/                  ← durable artifacts produced by missions (never deleted)
    index.md              ← index of all outputs, organized by mission
    {mission-name}/       ← one folder per mission that produced artifacts
      {artifact files}    ← slides, documents, configs, generated content, etc.
```

---

## The Three Tiers

**Intake** = unstructured capture. Ideas, notes, partial thoughts land here before triage. Lifecycle: `capture → triage → promote or discard`. Promoted items become responsibilities, missions, or patrols; discarded leave no trace.

**Responsibilities** (objectives, top tier) = the long-lived "why" — a role, a measured annual objective, a career goal. Carry structured progress tracking: Key Results, milestones, linked missions, a review cadence, health, and an append-only decisions log. One folder per responsibility. Lifecycle: `active` → `complete`; folders never deleted (the decisions log is the durable value). Driven by `objective.py`.

**Missions** (workstreams, middle tier) = complex work that spans multiple sessions and handoffs, run through the heavy **QRDPIV** lifecycle. On cleanup the folder is deleted *after* a durable log entry is written to `workstreams/_log/`. A mission may be parented to a responsibility, or be standalone. Driven by `workstream.py`.

**Patrols** (bottom tier) = lightweight, often-repeatable units — add a source, refresh data, lint an area, or run one iteration against a mission. A patrol carries *proportional* admin only (assignment, checklist, handoff, lessons) — no phase machine, no progressive distillation. If a patrol grows (multiple sessions, real research, design decisions), **promote it to a mission**. Driven by `patrol.py`.

**Outputs** = durable artifacts produced during mission implementation. Written to `outputs/{mission-name}/` — never inside the mission folder. This guarantees cleanup (which deletes the mission folder) cannot destroy produced artifacts. The `outputs/` tree is permanent.

---

## Three-Tier Hierarchy

```
responsibility (objective)        ← long-lived strategy, measured
    └── mission (workstream)      ← heavy QRDPIV lifecycle, multi-session
            └── patrol               ← lightweight unit / iteration
```

- A patrol's `parent` may be `workstreams/{name}`, `objectives/{name}`, or `null`.
- A mission's `parent` may be `objectives/{name}` or `null`.
- Responsibilities are the top tier; they are never children of another artifact.

---

## Session Entry

1. Read this rule (auto-loaded when working on control-plane files)
2. Read `objectives/index.md`, `workstreams/index.md`, and `patrols/index.md`
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
