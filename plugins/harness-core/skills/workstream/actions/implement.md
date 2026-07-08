# Action: Implement

Execute the plan step by step.

## Artifact destination

**Any file a workstream produces for use beyond the workstream itself** (slides, documents, configs, reports, generated content) must be written to `control-plane/outputs/{workstream-name}/`, not inside the workstream folder. This is non-negotiable — the workstream folder is deleted at cleanup, so anything written there is at risk.

Working files (`_working/`), process artifacts (`plan.md`, `research.md`, `design.md`), and the `index.md` anchor belong in the workstream folder. Everything the workstream *produces* belongs in `outputs/`.

After writing output files: update `control-plane/outputs/index.md` to add a row for this workstream if one doesn't already exist.

## Session start

Read `index.md` and `plan.md`. Confirm `workstream_health: healthy`. If not, load `actions/assess.md`.

`workstream-notes.md` already exists (created at initiate; see SKILL.md → *Workstream Notes (Self-Learning)*). If it doesn't, create it from the template in `framework-templates.md`.

Populate the **Step Status Log** table in `workstream-notes.md` with one row per plan step before beginning execution.

## Execution loop

**One subagent per step — no exceptions.** Every plan step is delegated to its own subagent. Main context does not execute step logic directly. This keeps main context clean across multi-phase workstreams and ensures each step is scoped and independently verifiable.

For each step:

1. Brief a subagent with only the context needed for that step (plan step text, relevant file paths, expected output). Do not pass the full plan or prior step outputs unless the step explicitly requires them.
2. Subagent reports status only — confirmation that output exists and key observations. It does not return full file contents to main context.
3. Update `workstream-notes.md` after each step:
   - Mark the step row in the Step Status Log (✓ / ✗ / blocked)
   - Append any challenge, discrepancy, or unexpected finding to the Challenges & Discrepancies section, prefixed `[implement]`
   - Append any permission or settings suggestion to the Permission / Settings Suggestions section
4. If blocked: stop immediately. Document the blocker in `workstream-notes.md` and surface it to the user.

## Delegation (Claude Code)

- `→ delegate: Sonnet subagent` — multi-step investigations, drafting, domain work. Return ≤400 words.
- `→ delegate: Haiku subagent` — template filling, bounded file ops, status checks. Return ≤200 words.
- `→ delegate: projects/{name}` — invoke the project's CLI entrypoint per its CLAUDE.md.

Main context receives only the step status confirmation and any distilled findings needed to brief the next step. Never pull raw file contents into main context.

**Agent scoping (default) — see SKILL.md → Subagent Delegation and `_addenda/claude-code.md` → Directory Scoping.** Every step-agent is scoped to a **single subtree** (reads + writes within it). Cross-boundary work stays with the orchestrator: `control-plane` deploys the right agent per subtree and passes distilled artifacts between them — e.g. a **knowledge agent** scoped to `knowledge/vault/` for vault lookups, a **design agent** scoped to `projects/<name>/`, an **implementation agent** in a **worktree** of the project repo. Brief each with the **absolute path** of its own subtree. Isolation: directory-scoped prompts for non-git subtrees; worktree isolation for code inside a git repo; **never `isolation: "worktree"` from `control-plane/`** (not a git repo).

**When briefing subagents that write vault notes:** include this wikilink rule verbatim in the brief: *"Vault root is `knowledge/vault/`. Write all wikilinks relative to that root — never include `vault/` as a prefix (wrong: `[[vault/domain-knowledge/payments]]`; correct: `[[domain-knowledge/payments]]`). Before writing any wikilink to a path outside the subtree you are currently authoring, verify the target exists with a Glob or Read check. Do not assume directory structure."*

**Concurrency rule:** Steps the plan marks `[parallelizable]` may run concurrently up to your configured budget (`max_concurrent_agents`, default 2; set during `init-workspace`); all other steps run sequentially. Every subagent must be scoped to complete in a single turn — if a step is too large, break it into smaller steps before spawning.

## Phase transition

When all steps and completion criteria are `[x]`:

```bash
python -B tools/workstream.py advance <name> validate
```

Load `actions/validate.md`. Verification and adversarial QA happen there — do not advance to complete from implement.
