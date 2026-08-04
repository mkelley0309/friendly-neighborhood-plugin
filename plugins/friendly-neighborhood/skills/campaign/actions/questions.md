# Action: Questions

> **Phase council** (QRDPIV: Q) — consult only when the concern is live (full map in `/friendly-neighborhood:creed`): driver `peter`; counsel `robbie` (constructive design questions), `jameson` (devil's-advocate grilling of poorly-shaped work), `mj`, `aunt-may`; watch villains `sandman` (under-shaped/formless work), `kraven`, `osborn`.

Turn an ambiguous request into a precise spec. Output: `request.md`.

## Steps

1. Read `index.md` — what's already known?
2. Ask the 2–4 most decision-critical unknowns in **one message**: scope boundary, done definition, constraints, what's explicitly out. Wait for answers. *If the request is badly under-shaped, spawn `robbie` to draw out the real requirements (constructive) and `jameson` to grill the framing (devil's advocate) before you commit to a spec.*
3. Write `request.md` using the template in `framework-templates.md`. Frontmatter: `note_type: workstream-artifact`, `workstream: {name}`, `tags: [workstream/{name}]`.
4. Advance phase:

```bash
python -B tools/workstream.py advance <name> research
```

Next: `actions/research.md`.
