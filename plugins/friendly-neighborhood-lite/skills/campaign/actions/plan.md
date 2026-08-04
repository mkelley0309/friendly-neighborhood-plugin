# Action: Plan

> **Phase council** (QRDPIV: P) — consult only when the concern is live (full map in `/friendly-neighborhood-lite:creed`): driver `miguel`; counsel `jameson`; watch villains `kingpin`, `mysterio`.

Produce the executable plan. Output: `plan.md`. The plan must be self-contained — an implementer must not need to read any prior artifact to execute it.

## Steps

1. Read `research.md`, and `design.md` if it exists. Also `request.md` if QRDPIV.
2. Write `plan.md` using the template in `framework-templates.md`. Frontmatter: `note_type: workstream-plan`.
3. If plan defines worktrees, write each `worktree-{nn}.md` in the same session. Each must be fully self-contained.
4. Present plan to user. Do not advance to implement until they confirm.
5. On confirmation:

```bash
python -B tools/workstream.py advance <name> implement
```

## Quality checks before writing

- Every step has a concrete output, not just an action.
- Scope "Out" excludes things someone might assume are in.
- Completion criteria are verifiable — not "done" but "file X exists and passes Y".
- Worktrees are truly independent of each other.
- Steps that should delegate are annotated: `→ delegate: Sonnet subagent | Haiku subagent | projects/{name}`.

**Claude Code:** delegate plan drafting to a Sonnet subagent when plan has >3 phases or >10 steps.
