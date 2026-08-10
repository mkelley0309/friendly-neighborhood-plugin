---
description: Operating contract for the prompts subtree — reusable prompt assets (templates, workflows, experiments).
paths: ["prompts/**"]
---

# Prompts

Reusable prompt assets — referenced by skills, subagents, and control-plane delegation. Not executed in place.

```
prompts/
  CLAUDE.md        ← thin pointer (contract is here)
  templates/       ← parameterized skeletons (filled at invocation)
  workflows/       ← multi-step prompt sequences (ordered, with dependencies)
  experiments/     ← ad-hoc trials, not yet promoted
```

---

## Templates

Declare:
- **Purpose** — what output it produces
- **Slots** — placeholders the caller fills (e.g. `{workstream_name}`)
- **Caller** — subagent / skill / control-plane

One file per template: `templates/{name}.md`. Frontmatter declares slots.

---

## Workflows

Ordered sequences with explicit step dependencies. Declare:
- **Inputs**, **Steps** (ordered with prompts), **Outputs**, **Termination criteria**

One file or folder: `workflows/{name}.md` or `workflows/{name}/`.

---

## Experiments

Ad-hoc trials. Date-stamp: `experiments/YYYY-MM-DD-{slug}.md`. Document what was tried and learned. Promote successes to `templates/` or `workflows/`. Purge failures after ~3 months.

---

## Principles

- Authored once, invoked many times — optimize for reuse
- Reference knowledge, don't embed it — link to `knowledge/vault/` or `sources/`
- Template slots are explicit — no implicit context assumptions
