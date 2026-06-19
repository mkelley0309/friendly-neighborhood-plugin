# Action: Initiate

## Decisions (LLM)

1. **Name** — propose `kebab-case-name`, confirm before creating anything.
2. **Framework** — QRDPIV unless spec is clear, well-scoped, single-domain → RPIV.
3. **Parent** — check `control-plane/objectives/index.md`; standalone if no match. If strategic work warrants a responsibility that doesn't exist yet, suggest creating it first via the `responsibility` skill.

## Scaffold (tool)

```bash
python -B tools/workstream.py create <name> [--framework rpiv] [--parent objectives/<name>] [--title "Title"]
```

A parent responsibility is recorded as `parent: "objectives/{name}"` in the created `index.md`.

Fill in the one-paragraph description in the created `index.md`.

## Self-learning ledger

Create `workstream-notes.md` in the new mission folder from the template in `framework-templates.md`. Every phase appends to it (see SKILL.md → *Mission Notes (Self-Learning)*).

## Intake provenance

If this mission was promoted from one or more `intake/` items, record them in the mission `index.md` frontmatter so cleanup can archive them:

```yaml
intake_source: ["intake/{item}.md", ...]   # omit if not promoted from intake
```

Leave the intake file(s) in place — they are **not** deleted at promotion. Cleanup moves them to `intake/_archive/`.

## Hand off

- QRDPIV → `actions/questions.md`
- RPIV → `actions/research.md`
