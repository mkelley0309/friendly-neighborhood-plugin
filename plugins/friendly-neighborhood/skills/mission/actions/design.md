# Action: Design

> **Phase council** (QRDPIV: D) — consult only when the concern is live (full map in `/friendly-neighborhood:creed`): driver `miguel`; counsel `uncle-ben`, `aunt-may`, `mj`, `madame-web`; watch villains `octavius`, `vulture`, `kraven`, `kingpin`.

Resolve architectural and structural decisions before planning. Output: `design.md`.

## When to run

Run when research surfaced architectural decisions, data model choices, or structural constraints where two implementers would make different calls without explicit guidance. Skip only if research is sufficient to plan directly.

## Steps

1. Read `research.md` — focus on Decisions Implied and Open Questions.
2. For each decision: evaluate options, make a call, document rationale. Surface to user if tradeoffs are significant.
3. Write `design.md` using the template in `framework-templates.md`. Frontmatter: `note_type: workstream-artifact`, `workstream: {name}`, `tags: [workstream/{name}]`.
4. Advance phase:

```bash
python -B tools/workstream.py advance <name> plan
```

**Claude Code:** for decisions requiring multi-option analysis, delegate per-option evaluation to Sonnet subagents and synthesize in main context.

Next: `actions/plan.md`.
