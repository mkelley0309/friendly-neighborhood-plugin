# Action: Questions

Turn an ambiguous request into a precise spec. Output: `request.md`.

## Steps

1. Read `index.md` — what's already known?
2. Ask the 2–4 most decision-critical unknowns in **one message**: scope boundary, done definition, constraints, what's explicitly out. Wait for answers.
3. Write `request.md` using the template in `framework-templates.md`. Frontmatter: `note_type: workstream-artifact`, `workstream: {name}`, `tags: [workstream/{name}]`.
4. Advance phase:

```bash
python -B tools/workstream.py advance <name> research
```

Next: `actions/research.md`.
