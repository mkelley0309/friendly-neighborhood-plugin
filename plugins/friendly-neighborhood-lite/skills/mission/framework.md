# Mission Framework Reference

Operational reference for mission state, routing, and artifact rules. Load this file when creating or updating any mission file.

Templates (index.md, request.md, research.md, design.md, plan.md, log entry) live in `framework-templates.md` — load that file only when filling in a new artifact.

---

## Frontmatter Schemas

### `index.md` — primary status anchor

```yaml
workstream: kebab-case-name
framework: rpiv | qrdpiv
workstream_phase: questions | research | design | plan | implement | validate | complete | cleanup
workstream_health: healthy | needs-questions | needs-design | under-shaped | blocked | stale
current_step: "Phase N — Step X: description"   # only during plan/implement; omit otherwise
status: active | complete | paused | abandoned
started: YYYY-MM-DD
completed: YYYY-MM-DD                            # set when cleanup log entry is filed
parent: null | "objectives/{name}"
intake_source: ["intake/{item}.md", ...]        # only if promoted from intake; archived at cleanup
tags: [workstream/{name}]
```

### Supporting files (`research.md`, `plan.md`, `design.md`, etc.)

```yaml
note_type: workstream-plan | workstream-research | workstream-artifact
workstream: kebab-case-name
tags: [workstream/{name}]
```

### Log entries (`_log/YYYY-MM-DD-{name}.md`)

```yaml
note_type: workstream-log
workstream: kebab-case-name
framework: rpiv | qrdpiv
completed: YYYY-MM-DD
parent: null | "objectives/{name}"
tags: [workstream/{name}]
```

---

## Artifact Destination Rule

| Artifact type | Destination |
|---|---|
| Working scratch | `workstreams/{name}/_working/` — deleted at cleanup |
| Process artifacts | `workstreams/{name}/` — `plan.md`, `research.md`, `design.md`, `workstream-notes.md`, `index.md` — deleted at cleanup |
| Promoting intake item | leave in `intake/` during the patrol; cleanup moves it to `intake/_archive/` |
| **Produced outputs** | **`outputs/{name}/` — permanent, never deleted by cleanup** |
| Vault additions | `knowledge/vault/` |
| Reusable prompts | `prompts/templates/` or `prompts/workflows/` |
| Code | `projects/{name}/` |
| Durable log | `workstreams/_log/YYYY-MM-DD-{name}.md` — permanent |

**Produced outputs** = anything the patrol creates for use beyond the patrol: slides, documents, configs, reports, generated content. Write these to `outputs/{name}/` during implement, then add a row to `outputs/index.md`.

---

## `workstream_phase` Transition Map

```
questions  →  research      (after request.md written)
research   →  design        (after research.md written; if design needed)
research   →  plan          (after research.md written; if no design needed)
design     →  plan          (after design.md written)
plan       →  implement     (when execution begins)
implement  →  validate      (when all plan.md checkboxes checked)
validate   →  complete      (when gate is GO and jameson signs off)
complete   →  cleanup       (when log entry is being written)
cleanup    →  (done)        (after log filed, outputs verified in outputs/, folder deleted)
```

---

## Research Pass Selection

| Patrol type | Knowledge | Web | Codebase |
|---|---|---|---|
| Knowledge maintenance / reorg | ✓ | — | — |
| Content generation (GTM, narrative) | ✓ | ✓ | — |
| Build project (greenfield) | ✓ | ✓ | — |
| Build project (extending existing) | ✓ | ✓ | ✓ |
| Competitive / external research | ✓ | ✓ | — |
| Initial system setup | ✓ | — | — |
| Research with deliverable | ✓ | ✓ | — |

---

## Subagent Delegation Within Actions

- **Research passes** → Sonnet subagent per pass (knowledge, web, codebase), run **sequentially one at a time**. Each returns only the distilled findings (≤200 words).
- **Plan drafting** → Sonnet subagent when plan has >3 phases or >10 steps. (≤400 words back to main context.)
- **Template filling, file renames, status checks** → Haiku subagent. (≤200 words back to main context.)
- **Cleanup file deletions** → confirm with user first; do not delegate destructive ops.

**Concurrency budget: up to your configured limit in flight** (`max_concurrent_agents`, default 2; set during `origin-story`). Default behavior is sequential. See `_addenda/claude-code.md` for the full rule.
