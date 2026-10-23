# Action: Validate

Confirm the workstream's outputs are real before closing. A workstream does not advance to cleanup on faith.

## Steps

### 1. Run the deterministic gate

```bash
python -B tools/gate.py run
```

This executes your defined checks (tests, lint, types — set them once with `gate.py init`) and returns a hard GO / NO-GO by exit code. Also acceptable: the `/verify` or `/run` skill, or the project's test command from its `CLAUDE.md`. If the project genuinely has no automated checks, say so explicitly and verify behavior by an observable alternative — never skip silently.

Record the result (command run, exit code, what passed or failed) in `validate.md` — that is the work record. Only record it in `friction-log.md` if the *gate itself* misbehaved (no checks configured, the skill gave no usable instruction, the runner failed for reasons unrelated to the deliverables).

**If GO on a row-based deliverable** (inventory, tracker, table): still spot-check ≥10 rows by hand, sampled across the table, and record them in `validate.md`. Count and required-field gates miss content defects — self-referencing evidence, pointers to unrendered columns.

**If NO-GO:** stop. Document the failures in `validate.md` and surface them to the user. Return to `actions/implement.md` to remediate, then re-run the gate.

### 2. Adversarial QA

By default, hand the gate result and the workstream's completion criteria (from `blueprint.md`) to a Sonnet subagent with the prompt: "Red-team these deliverables against every completion criterion — find anything claimed done but not actually verified."

The subagent returns findings to main context (≤400 words). Record sign-off or objections in `validate.md`.

**Main-context fallback.** If this session operates under a policy that forbids unrequested subagent spawns, run the same adversarial pass directly in main context instead — genuinely argue against your own completion claims, criterion by criterion, rather than restating them as done. The point of the subagent is adversarial distance from the work just finished; approximate that distance deliberately if a fresh context isn't available.

**If objections are raised:** resolve them before proceeding. Unresolved objections block advance to cleanup.

### 3. Security red-team (when applicable)

If the workstream's changes touch auth, secrets, input handling, or any external-facing
surface, spawn `dissent` with `lens: cat` — the security red-team — before advancing. Her whole
job is to find the open window; if she finds one, close it and re-run this step before
proceeding.

Record sign-off or findings in `validate.md`. If the change genuinely doesn't touch any of the
above surfaces, skip this step and say so explicitly — don't skip silently.

### 4. Advance phase

Only when the gate is GO **and** adversarial QA signs off:

```bash
python -B tools/workstream.py complete <name>
```

Load `actions/cleanup.md`.
