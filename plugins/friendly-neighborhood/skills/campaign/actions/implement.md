# Action: Implement

> **Phase council** (Relay: I) — consult only when the concern is live (full map in `/friendly-neighborhood:creed`): driver `peter` / `miles` (route each step to the right Spider-variant — see Delegation); counsel `ned`; watch villains `carnage`, `cat` (security), `rhino`, `osborn`. Functional validation happens in `validate` — `gwen` drives it, with `mysterio` and `cat` on watch.

Execute the blueprint step by step.

## Artifact destination

**Any file a campaign produces for use beyond the campaign itself** (slides, documents, configs, reports, generated content) must be written to `control-plane/outputs/{campaign-name}/`, not inside the campaign folder. This is non-negotiable — the campaign folder is deleted at cleanup, so anything written there is at risk.

Working files (`_working/`), process artifacts (`blueprint.md`, `research.md`, `design.md`), and the `index.md` anchor belong in the campaign folder. Everything the campaign *produces* belongs in `outputs/`.

After writing output files: update `control-plane/outputs/index.md` to add a row for this campaign if one doesn't already exist.

## Session start

Read `index.md` and `blueprint.md`. Confirm `workstream_health: healthy`. If not, load `actions/assess.md`.

A step that consumes row data may read the `research.md` sections named in `design.md`'s Data Inputs — that is planned input, not escalation past `blueprint.md`.

`friction-log.md` already exists (created at initiate; see SKILL.md → *Friction Log*). If it doesn't, create it from the template in `framework-templates.md`.

Do **not** build a step-status table anywhere. `blueprint.md` checkboxes and `index.md` `current_step` are the progress record, and `check-step` maintains both together.

## Execution loop

**One subagent per step, by default.** Every blueprint step is delegated to its own subagent unless the fallback below applies. This keeps main context clean across multi-phase campaigns and ensures each step is scoped and independently verifiable.

**Main-context fallback.** If this session operates under a policy that forbids unrequested subagent spawns, execute the step directly in main context instead — brief yourself with the same scoped context a subagent would get (this step's text, the relevant file paths, the expected output) rather than pulling in the full blueprint or unrelated prior-step context. Still tick the step and still log friction per the rules below; the fallback changes who runs the step, not what gets recorded.

For each step:

1. Brief a subagent with only the context needed for that step (blueprint step text, relevant file paths, expected output). Do not pass the full blueprint or prior step outputs unless the step explicitly requires them.
2. Subagent reports status only — confirmation that output exists and key observations. It does not return full file contents to main context.
3. Tick the step — this is the only progress write:

   ```bash
   python -B tools/workstream.py check-step <name> "<step number>"
   ```

   Accepts a step number (`1.4`) or a distinctive substring. It ticks the `blueprint.md` checkbox and advances `index.md` `current_step` in one operation, so the two cannot drift. An ambiguous query is rejected rather than guessed at.

4. Append to `friction-log.md` **only** if the harness itself got in the way — a tool that misbehaved, an instruction that was wrong or contradictory, an access scope that was too narrow. Prefix `[implement]`. A finding about the subject matter is not friction; it belongs in the work artifact. Most steps produce no entry.
5. If blocked: stop immediately. Record the blocker with `workstream.py block <name> "<reason>"`, and surface it to the user.

## Delegation (Claude Code)

- `→ delegate: Sonnet subagent` — multi-step investigations, drafting, domain work. Return ≤400 words.
- `→ delegate: Haiku subagent` — template filling, bounded file ops, status checks. Return ≤200 words.
- `→ delegate: projects/{name}` — invoke the project's CLI entrypoint per its CLAUDE.md.

Main context receives only the step status confirmation and any distilled findings needed to brief the next step. Never pull raw file contents into main context.

**Agent scoping (default) — see SKILL.md → Subagent Delegation and root `CLAUDE.md` → Subagent Delegation.** Every step-agent is scoped to a **single subtree** (reads + writes within it). Cross-boundary work stays with the orchestrator: `control-plane` deploys the right agent per subtree and passes distilled artifacts between them — e.g. a **knowledge agent** scoped to `knowledge/vault/` for vault lookups, a **design agent** scoped to `projects/<name>/`, an **implementation agent** in a **worktree** of the project repo. Brief each with the **absolute path** of its own subtree. Isolation: directory-scoped prompts for non-git subtrees; worktree isolation for code inside a git repo; **never `isolation: "worktree"` from `control-plane/`** (not a git repo).

**When briefing subagents that write vault notes:** include this wikilink rule verbatim in the brief: *"Vault root is `knowledge/vault/`. Write all wikilinks relative to that root — never include `vault/` as a prefix (wrong: `[[vault/domain-knowledge/payments]]`; correct: `[[domain-knowledge/payments]]`). Before writing any wikilink to a path outside the subtree you are currently authoring, verify the target exists with a Glob or Read check. Do not assume directory structure."*

**Concurrency rule:** Steps the blueprint marks `[parallelizable]` may run concurrently up to your configured budget (`max_concurrent_agents`, default 2; set during `origin-story`); all other steps run sequentially. Every subagent must be scoped to complete in a single turn — if a step is too large, break it into smaller steps before spawning.

## Phase transition

When all steps and completion criteria are `[x]`:

```bash
python -B tools/workstream.py advance <name> validate
```

Load `actions/validate.md`. Verification and adversarial QA happen there — do not advance to complete from implement.
