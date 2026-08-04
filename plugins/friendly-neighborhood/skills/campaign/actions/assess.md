# Action: Assess

## Read state (tool)

```bash
python -B tools/workstream.py status <name>
python -B tools/workstream.py next <name>
```

Portfolio: `python -B tools/workstream.py list`

## Health responses

| Health | Response |
|---|---|
| `healthy` | Proceed — load next phase action file. |
| `under-shaped` | Do not execute plan. Load `actions/questions.md` to reshape. |
| `needs-questions` | Load `actions/questions.md`. |
| `needs-design` | Load `actions/design.md`. |
| `blocked` | Resolve dependency. Run `python -B tools/workstream.py unblock <name>` when clear. |
| `stale` | Verify plan is still valid before continuing. |

## Phase → next action

| Phase | Next |
|---|---|
| `questions` | `actions/questions.md` |
| `research` | `actions/research.md` |
| `design` | `actions/design.md` |
| `plan` | `actions/plan.md` (draft) or `actions/implement.md` (execute) |
| `implement` | `actions/implement.md` |
| `validate` | `actions/validate.md` |
| `complete` | `actions/cleanup.md` |
