# Workstream Templates

Fill-in templates for workstream artifacts. Load this file only when creating a new artifact — do not load during session entry, assess, or implement unless you are about to write a new file.

---

## `index.md` Template

```markdown
# {Workstream Title}

## Workstream Status

| Field | Value |
|---|---|
| Phase | {workstream_phase} |
| Health | {workstream_health} |
| Current Step | — |
| Blocker | — |
| Last Active | YYYY-MM-DD |

{One paragraph: what this workstream is and what it delivers.}

## QRDPIV Artifact Status   ← include for QRDPIV; omit for RPIV

| Step | Artifact | Status |
|---|---|---|
| Questions | `request.md` | Not started |
| Research — Knowledge pass | `_working/research-knowledge-*.md` | Not started |
| Research — Web pass | `_working/research-web-*.md` | Not started |
| Research — Codebase pass | `_working/research-code-*.md` | Not started |
| Research — Distillation | `research.md` | Not started |
| Design | `design.md` | Not started |
| Plan | `plan.md` | Not started |
| Worktrees | `worktree-{nn}.md` | Not started |
| Validate | `validate.md` | Not started |

## Child Tasks

| Task | Linked |
|---|---|

## Cross-links

- **Parent Objective:** [objectives/{name}](../../objectives/{name}/index.md)   ← or omit if null
- {other relevant links}
```

---

## `request.md` Template

```markdown
# {Workstream Name} — Request

Refined specification produced at the QRDPIV Questions step. Replaces the original request as input to all downstream steps.

## Original Request

{Verbatim or paraphrased summary of what was asked}

## Clarifications

{Q&A from the Questions step — decisions made, scope confirmed}

## Refined Scope

**In:**
- {item}

**Out:**
- {item}

## Constraints and Assumptions

- {constraint or assumption}

## Success Definition

{How we'll know this workstream is done}
```

---

## `research.md` Template

```markdown
# {Workstream Name} — Research

Distilled from {n} knowledge pass(es), {n} web pass(es), {n} codebase pass(es). Self-contained — downstream steps do not read `_working/` files.

## Key Findings

### Knowledge

{Distilled vault/sources knowledge relevant to this workstream}

### Web

{Distilled external knowledge — standards, competitor info, technical refs}
← omit section if no web passes were run

### Codebase

{Distilled codebase knowledge — existing patterns, dependencies, constraints}
← omit section if no codebase passes were run

## Decisions Implied by Research

{Any decisions the research surfaces that need to be made in Design or Plan}

## Open Questions

{Anything research couldn't resolve — flags for Design or Questions follow-up}
```

---

## `design.md` Template

```markdown
# {Workstream Name} — Design

Architectural and structural decisions made before planning. Produced from `research.md` (and `request.md` if QRDPIV).

## Decision: {Title}

**Context:** {why this decision was needed}
**Options considered:** {what was evaluated}
**Decision:** {what was chosen}
**Rationale:** {why}

## Decision: {Title}

...

## Constraints Carried into Plan

{What the plan must respect — architectural boundaries, interfaces, limits}
```

---

## `plan.md` Template

```markdown
# {Workstream Name} — Plan

## Objective

{One sentence: what this workstream delivers}

## Scope

**In:** {item}, {item}
**Out:** {item}, {item}

## Steps

### Phase {N} — {Phase Name}   ← use phases for multi-phase work; skip for simple plans

- [ ] Step 1: {description} → *output: {what this step produces}*
- [ ] Step 2: {description} → *output: {what this step produces}*

### Phase {N+1} — {Phase Name}

- [ ] Step N: {description} → *output: {what this step produces}*

## Worktrees

{Describe parallel tracks if applicable, or omit section}

- `worktree-01.md` — {description of track 1}
- `worktree-02.md` — {description of track 2}

## Completion Criteria

- [ ] {verifiable criterion}
- [ ] {verifiable criterion}

## Cross-links

- {related objective, project, or knowledge section}
```

---

## `workstream-notes.md` Template

Created at initiate, appended by **every** phase, reviewed at cleanup. The self-learning ledger of the workstream — not implement-only.

```markdown
---
note_type: workstream-artifact
workstream: {name}
tags: [workstream/{name}]
---

# Workstream Notes — {name}

Running self-learning log across all phases. Each entry is tagged with the phase
that produced it (`[questions]`, `[research]`, `[design]`, `[plan]`, `[implement]`,
`[validate]`, `[cleanup]`). Reviewed at cleanup to surface durable lessons and any
permission / settings changes worth making permanent.

---

## Challenges & Discrepancies

*(append throughout — prefix each with its phase)*

---

## Process Observations & Self-Learning

*(what worked, what to repeat or avoid, friction in the workflow itself — prefix with phase)*

---

## Permission / Settings Suggestions

*(append throughout — prefix with phase)*

---

## Step Status Log   ← implement phase only

| Step | Status | Notes |
|---|---|---|
| {step} | — | |
```

---

## Log Entry Template (`_log/YYYY-MM-DD-{name}.md`)

```markdown
# Workstream Summary — {Workstream Title}

## What and Why

{What the workstream was and why it was initiated — 2–4 sentences}

## What Was Delivered

{Bullet list of concrete deliverables}

## Key Decisions

{Decisions made and rationale — the stuff worth remembering}

## What Worked / Lessons Learned

{Honest assessment — what to repeat, what to avoid}

## Durable Artifacts

{Links to outputs, knowledge notes, project files, or systems that persist after the workstream closes}
- Produced artifacts → `control-plane/outputs/{workstream-name}/` (slides, documents, configs, generated content)
- Vault additions → `knowledge/vault/` paths
- Code → `projects/{name}/` paths
← if none, write "None — {explanation}"

## Parent Objective

{Link to parent objective, or "None — standalone."}
```

---

## Portfolio Index Update Pattern

When adding to the Active table in `workstreams/index.md`:

```markdown
| [{name}]({name}/index.md) | {one-line description} | {QRDPIV\|RPIV} | {phase} | {health} | [objectives/{parent}](../objectives/{parent}/index.md) |
```

When moving to Recently Completed:

```markdown
| [{date}-{name}](_log/{date}-{name}.md) | {one-line description} | {YYYY-MM-DD} |
```
