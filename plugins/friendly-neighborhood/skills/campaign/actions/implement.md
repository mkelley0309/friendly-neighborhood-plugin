# Action: Implement

> **Phase council** (QRDPIV: I) — consult only when the concern is live (full map in `/friendly-neighborhood:creed`): driver `peter` / `miles` (route each step to the right Spider-variant — see Delegation); counsel `ned`; watch villains `carnage`, `cat` (security), `rhino`, `osborn`. Functional validation happens in `validate` — `gwen` drives it, with `mysterio` and `cat` on watch.

Execute the plan step by step.

## Artifact destination

**Any file a mission produces for use beyond the mission itself** (slides, documents, configs, reports, generated content) must be written to `control-plane/outputs/{mission-name}/`, not inside the mission folder. This is non-negotiable — the mission folder is deleted at cleanup, so anything written there is at risk.

Working files (`_working/`), process artifacts (`plan.md`, `research.md`, `design.md`), and the `index.md` anchor belong in the mission folder. Everything the mission *produces* belongs in `outputs/`.

After writing output files: update `control-plane/outputs/index.md` to add a row for this mission if one doesn't already exist.

## Session start

Read `index.md` and `plan.md`. Confirm `workstream_health: healthy`. If not, load `actions/assess.md`.

`friction-log.md` already exists (created at initiate; see SKILL.md → *Friction Log*). If it doesn't, create it from the template in `framework-templates.md`.

Do **not** build a step-status table anywhere. `plan.md` checkboxes and `index.md` `current_step` are the progress record, and `check-step` maintains both together.

## Execution loop

**One subagent per step — no exceptions.** Every plan step is delegated to its own subagent. Main context does not execute step logic directly. This keeps main context clean across multi-phase missions and ensures each step is scoped and independently verifiable.

For each step:

1. Brief a subagent with only the context needed for that step (plan step text, relevant file paths, expected output). Do not pass the full plan or prior step outputs unless the step explicitly requires them.
2. Subagent reports status only — confirmation that output exists and key observations. It does not return full file contents to main context.
3. Tick the step — this is the only progress write:

   ```bash
   python -B tools/workstream.py check-step <name> "<step number>"
   ```

   Accepts a step number (`1.4`) or a distinctive substring. It ticks the `plan.md` checkbox and advances `index.md` `current_step` in one operation, so the two cannot drift. An ambiguous query is rejected rather than guessed at.

4. Append to `friction-log.md` **only** if the harness itself got in the way — a tool that misbehaved, an instruction that was wrong or contradictory, an access scope that was too narrow. Prefix `[implement]`. A finding about the subject matter is not friction; it belongs in the work artifact. Most steps produce no entry.
5. If blocked: stop immediately. Record the blocker with `workstream.py block <name> "<reason>"`, and surface it to the user.

## Delegation (Claude Code)

- `→ delegate: Sonnet subagent` — multi-step investigations, drafting, domain work. Return ≤400 words.
- `→ delegate: Haiku subagent` — template filling, bounded file ops, status checks. Return ≤200 words.
- `→ delegate: projects/{name}` — invoke the project's CLI entrypoint per its CLAUDE.md.

**Route each step to the right Spider-variant** (`subagent_type` = the agent): `miles` for minimal-diff / surgical changes · `ben-reilly` for refactors & de-duplication · `noir` for debugging / root-cause · `silk` for lookups & recall · `peter` for general work. Fall back to a plain Sonnet/Haiku subagent only when no specialist fits. (`gwen` is the Validate-phase tester, not an implement-step coder — route to her at `validate`, not here.)

Main context receives only the step status confirmation and any distilled findings needed to brief the next step. Never pull raw file contents into main context.

**NEVER use `isolation: "worktree"` in Agent calls from `control-plane/`.** `control-plane/` is not a git repository; worktree isolation requires either a git repo or `WorktreeCreate` hooks — neither is configured. Use directory-scoped prompts (`Work within <subtree>/ only`) for isolation instead. This applies even when the Agent tool schema shows `isolation` as an available parameter.

**When briefing subagents that write vault notes:** include this wikilink rule verbatim in the brief: *"Vault root is `knowledge/vault/`. Write all wikilinks relative to that root — never include `vault/` as a prefix (wrong: `[[vault/domain-knowledge/payments]]`; correct: `[[domain-knowledge/payments]]`). Before writing any wikilink to a path outside the subtree you are currently authoring, verify the target exists with a Glob or Read check. Do not assume directory structure."*

**Concurrency rule:** Steps the plan marks `[parallelizable]` may run concurrently up to your configured budget (`max_concurrent_agents`, default 2; set during `origin-story`); all other steps run sequentially. Every subagent must be scoped to complete in a single turn — if a step is too large, break it into smaller steps before spawning.

## Phase transition

When all steps and completion criteria are `[x]`:

```bash
python -B tools/workstream.py advance <name> validate
```

Load `actions/validate.md`. Verification and adversarial QA happen there — do not advance to complete from implement.
