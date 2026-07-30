# Action: Design

> **Phase council** (QRDPIV: D) — consult only when the concern is live (full map in `/friendly-neighborhood-lite:creed`): driver `miguel`; counsel `jameson`; watch villains `kingpin`, `mysterio`.

Resolve decisions before planning. Covers two kinds, either or both: **architectural design** (how it works) and **structure outline** (what the deliverable is shaped like). Output: `design.md`, and `outline.md` when the deliverable structure warrants its own artifact.

## When to run

- **Architectural design** — research surfaced architectural decisions, data model choices, or structural constraints where two implementers would make different calls without explicit guidance.
- **Structure outline** — the deliverable's own structure needs agreement before planning: a document's section order and argument spine, a vault layout, an API shape, a deck's narrative arc. Skip only when the structure is obvious.

Skip the phase entirely only if research is sufficient to plan directly.

## Steps

### Architectural design

1. Read `research.md` — focus on Decisions Implied and Open Questions.
2. For each decision: evaluate options, make a call, document rationale. Surface to user if tradeoffs are significant.
3. Write `design.md` using the template in `framework-templates.md`. Frontmatter: `note_type: workstream-artifact`, `workstream: {name}`, `tags: [workstream/{name}]`.

### Structure outline

1. Derive the deliverable's structure from `research.md` and the request — sections, order, what each part must carry.
2. **Get explicit user agreement on the structure before planning against it.** A rich initial brief encodes *content coverage*, not necessarily optimal *sequence* for the target reader — separate "what to include" from "how to order it".
3. Record governing decisions as `[D]` entries so downstream drafting has one authoritative source. Where a `[D]` supersedes something in `research.md`, say so explicitly — the outline wins.
4. Write to `outline.md` when the structure is substantial enough to be referenced repeatedly during implement; otherwise fold it into `design.md` as a Structure section. Same frontmatter as above.

### Close the phase

```bash
python -B tools/workstream.py advance <name> plan
```

**Claude Code:** for decisions requiring multi-option analysis, delegate per-option evaluation to Sonnet subagents and synthesize in main context.

Next: `actions/plan.md`.
