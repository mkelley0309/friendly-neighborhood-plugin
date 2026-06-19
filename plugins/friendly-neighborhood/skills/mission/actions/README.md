# Mission Action Files

One file per phase. Load **only** the one matching the current situation — do not load the whole directory.

Routing table lives in `../SKILL.md`.

| Action | When to load |
|---|---|
| `initiate.md` | New mission — create folder, `index.md`, frontmatter, parent link |
| `assess.md` | Existing mission — orient, report phase/health, recommend next step |
| `questions.md` | QRDPIV Questions step — shape ambiguous request into `request.md` |
| `research.md` | Research step — run knowledge/web/codebase passes, distill to `research.md` |
| `design.md` | Design step — architectural decisions before planning |
| `plan.md` | Plan step — produce executable `plan.md` with steps and completion criteria |
| `implement.md` | Implement step — execute the plan; check off steps; update `index.md` |
| `validate.md` | Validate step — run gate + adversarial QA before closing |
| `cleanup.md` | Mission complete — write log, delete folder, update portfolio index |
