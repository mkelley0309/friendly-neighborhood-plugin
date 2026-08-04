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

Create `friction-log.md` in the new campaign folder from the template in `framework-templates.md`. Every phase appends to it — but only about how the *harness* performed, never about the work itself (see SKILL.md → *Friction Log*). Expect it to stay empty on a clean run.

## Intake provenance

If this campaign was promoted from one or more `intake/` items, record them in the campaign `index.md` frontmatter so cleanup can archive them:

```yaml
intake_source: ["intake/{item}.md", ...]   # omit if not promoted from intake
```

Leave the intake file(s) in place — they are **not** deleted at promotion. Cleanup moves them to `intake/_archive/`.

## Hand off

- QRDPIV → `actions/questions.md`
- RPIV → `actions/research.md`
