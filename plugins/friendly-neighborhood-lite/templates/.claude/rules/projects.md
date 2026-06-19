---
description: Operating contract for the projects subtree — isolated execution workers invoked by the control plane.
paths: ["projects/**"]
---

# Projects — Worker Layer

Isolated execution workers. Each project is self-contained, domain-specific, invoked by the control plane.

---

## Layout

```
projects/
  CLAUDE.md           ← thin pointer (contract is here)
  {project-name}/
    CLAUDE.md         ← project contract (tech stack, tests, outputs)
    {project files}
```

---

## Worker Contract

Every project `CLAUDE.md` must declare:

1. **Purpose** — what it does and why
2. **Invocation** — how the control plane calls it (CLI entrypoint, script, etc.)
3. **Inputs** — files, arguments, config
4. **Outputs** — where results land (typically `knowledge/sources/{project-name}/`)
5. **Test approach** — how to verify correctness; commands to run
6. **Dependencies** — runtimes, packages, external services
7. **Boundaries** — what this project will NOT do

---

## Execution Rules

- **Projects execute; projects do not orchestrate.** Cross-project coordination belongs in control-plane.
- **Projects write to `knowledge/sources/`**, not directly to `knowledge/vault/`.
- **Projects own their test strategy.** Control-plane validates intent, not test approach.
- **Projects are isolated.** Cross-project data flows through `knowledge/sources/` or explicit control-plane coordination.

---

## When to Create a Project

Create when:
- Work has repeated execution value (runs more than once or in multiple contexts)
- Has a stable input/output contract
- Is domain-specific enough to warrant isolated tooling or tests

Do not create for:
- One-off workstream deliverables (those are workstream artifacts)
- Generic utilities with no stable contract (those are `tools/`)
- Pure knowledge tasks (those are `knowledge/` work)

---

## Subagent Delegation

Projects may use subagents during execution. For model selection, see `_addenda/claude-code.md` (Claude Code) or the tool's equivalent. Distill subagent outputs before integrating into main context.

---

## Testing Standards

- Each project declares how to run tests in its `CLAUDE.md`
- Definition of Done requires tests passing
- Test output should be parseable (exit codes, structured output)
- Flaky tests are bugs — do not normalize retries
