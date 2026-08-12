# Workspace Contract

*Base contract for this workspace.*

**Semantic density:** shortest word that preserves meaning, imperative voice, no hedging, tables/bullets over prose.

---

## Layout

```
CLAUDE.md         this file
control-plane/    orchestration: objectives, workstreams, assignments, cadences
projects/         execution workers (independent git repos)
knowledge/        sources/ (raw) · vault/ (curated) · distillers/
prompts/          reusable prompt assets
tools/            scripts and CLIs
personal/         private context — stakeholders, accounts, career; never leaves
_harness/         harness self-improvement ledger (permanent, never deleted)
outputs/          durable workstream artifacts (permanent, never deleted)
```

Each subtree has its own instruction file — read it before working in that subtree. Each subtree's
contract auto-loads via a path-scoped rule in `.claude/rules/`; scoped subagents should read the
relevant rule before acting. Each subtree also keeps a thin `CLAUDE.md` pointer for tools that
don't support rules.

---

## Session

1. Read the subtree instruction file for the work in scope
2. If a workstream, objective, or assignment is in scope, read its `index.md`
3. State scope and next action before proceeding

---

## Context and Distillation

- `_working/` is scratch — never read by main context
- Keep main context under 40% of window; distill before continuing past 60%
- Every phase boundary distills raw → durable artifact, never leaves it in scratch:

| Phase | From | To |
|---|---|---|
| In-session | `_working/` | `research.md` / `design.md` / `blueprint.md` |
| Workstream implement | blueprint step execution | `outputs/{workstream-name}/` (never inside the workstream folder) |
| Workstream close | workstream folder | `control-plane/workstreams/_log/YYYY-MM-DD-{name}.md` |
| Objective decisions | session | objective `index.md` → Key Decisions Log (append-only) |

---

## Boundaries

| Subtree | Role | Must not |
|---|---|---|
| `control-plane/` | plan, coordinate | execute domain logic |
| `projects/` | execute | orchestrate across projects |
| `knowledge/sources/` | raw data (pipeline-written) | curate |
| `knowledge/vault/` | curated, Obsidian-backed — access via `obsidian-cli` + kepano skills, not MCP | accept raw data |
| `prompts/` | reusable assets | execute in place |
| `tools/` | capability primitives | contain domain logic |

When in doubt: planning → `control-plane/` · execution → `projects/` · data → `knowledge/`.

`projects/*` are independent git repos, gitignored from this root repo — see **Session Locus**
below before doing git-dependent work there.

No delete or overwrite without explicit instruction. Prefer additive, reversible changes.

---

## Session Locus

This workspace is the default launch root for all work. The harness does not relocate sessions or
spawn agents across roots — it **advises**, and the operator relocates or doesn't.

**MUST relocate** — before git-dependent work inside a nested repo (commits, branches, PRs,
`/code-review` on the working diff, worktree isolation), stop and advise relocating the session
into that repo's own directory. This is a **correctness** failure, not a preference: run from root
and the git tooling targets the *wrong repo* — it reports success while the real changes sit
untouched in the nested repo, uncommitted.

**CONSIDER relocating** — sustained single-subtree work where focus and blast radius matter (e.g.
a long `knowledge/` distillation run). Optimization only; staying at root is still correct, just
noisier.

**`isolation: "worktree"` is not a substitute for physically relocating the session.** A worktree
spawned by an agent running from a root-launched session derives from the **root repo**, not the
nested one — and a gitignored nested repo isn't checked out into that worktree at all, so work
briefed at it silently targets the wrong tree. Use `isolation: "worktree"` only when the session
issuing the spawn is **already launched inside** the nested repo; otherwise, relocate the session
itself first.

---

## Subagent Delegation

Scope every subagent to one subtree:

1. **Root**: `Work within \`<subtree>/\` only.`
2. **Contract**: `Read \`<subtree>/CLAUDE.md\` before acting.`
3. **Boundary**: `Do not read or write outside \`<subtree>/\`.`

Cross-subtree work (e.g. planning + execution) stays in main context — never delegate a
cross-boundary task to a single agent. When a task spans subtrees, deploy the right agent per
subtree and pass distilled artifacts between them.

**Concurrency budget: up to `max_concurrent_agents` subagents in flight at once** (default 2, set
during `init-workspace`) — a soft cost/coordination guideline, not a safety cap. Default behavior
is sequential: spawn one, wait for it to return, then spawn the next. Run several in parallel only
when the assignments are truly independent (no shared file writes, no ordering dependency) and
each completes in one turn.

**Model tiers:** complex/ambiguous work (research, plan drafting, multi-step investigation) →
current Sonnet; simple/bounded work (status checks, file moves, lookups) → current Haiku;
decisions and synthesis never delegate — main context only.

**Isolation:** directory-scoped prompts for non-git subtrees (`control-plane/`, `knowledge/`);
never set `isolation: "worktree"` with `control-plane/` as the base, since it is not a git repo.
See **Session Locus** above for the worktree-vs-relocation pitfall.

**Obsidian vault:** `obsidian-cli`, `obsidian-markdown`, `obsidian-bases`, `json-canvas`,
`defuddle` are the default interface for `knowledge/vault/` (installed globally via
`npx skills add kepano/obsidian-skills -g -a claude-code`, updated via `npx skills update -g`). No
MCP server backs it.

---

## Runtime Note

Orchestration CLIs require Python 3 (stdlib only) — invoke with whichever launcher is present:
`python3`, `python`, or `py`. Add `-B` to skip `__pycache__` bytecode generation.

## Memory Note

Memory here is **explicit and auditable**, not implicit: the **vault** is semantic memory, the
**control-plane logs / decisions log / friction-log** are episodic, **`CLAUDE.md` + `.claude/rules/`**
are procedural. Recall is deliberate; nothing is silently retained. (Native auto-memory is
complementary and optional.)
