# Action: Blueprint

> **Phase council** (Relay: B) — consult only when the concern is live (full map in `/friendly-neighborhood:creed`): driver `miguel`; counsel `uncle-ben`, `aunt-may`, `madame-web`; watch villains `octavius`, `kraven`, `kingpin`, `vulture`.

Produce the executable blueprint. Output: `blueprint.md`. The blueprint must be self-contained — an implementer must not need to read any prior artifact to execute it.

## Steps

1. Read `research.md`, and `design.md` if it exists. Also `request.md` if Payload Relay. `research.md` sections listed in `design.md`'s Data Inputs are planned payload — Blueprint's row-data source, not a reason to re-derive or re-open research.
2. Write `blueprint.md` using the template in `framework-templates.md`. Frontmatter: `note_type: workstream-blueprint`.
3. If the blueprint defines worktrees, write each `worktree-{nn}.md` in the same session. Each must be fully self-contained.
4. Present the blueprint to user. Do not advance to implement until they confirm.
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
- Every design decision a step cites ("per D-B") is inlined in the blueprint — state the decision, not just its ID. A bare citation forces implement to read `design.md`, breaking self-containment.
- Every count or row total a step states ("143 rows from K-D") is checked against its source table before presenting. Count the table's rows; footnote or prose-only items are not rows. A wrong count forces implement to invent or drop rows.

**Claude Code:** delegate blueprint drafting to a Sonnet subagent when the blueprint has >3 phases or >10 steps.
