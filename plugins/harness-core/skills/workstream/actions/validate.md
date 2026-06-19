# Action: Validate

Confirm the workstream's outputs are real before closing. A workstream does not advance to cleanup on faith.

## Steps

### 1. Run the deterministic gate

```bash
python -B tools/gate.py run
```

This executes your defined checks (tests, lint, types — set them once with `gate.py init`) and returns a hard GO / NO-GO by exit code. Also acceptable: the `/verify` or `/run` skill, or the project's test command from its `CLAUDE.md`. If the project genuinely has no automated checks, say so explicitly and verify behavior by an observable alternative — never skip silently.

Record the result (command run, exit code, what passed or failed) in `workstream-notes.md` prefixed `[validate]`.

**If NO-GO:** stop. Document the failures in `workstream-notes.md` and surface them to the user. Return to `actions/implement.md` to remediate, then re-run the gate.

### 2. Adversarial QA

Hand the gate result and the workstream's completion criteria (from `plan.md`) to a Sonnet subagent with the prompt: "Red-team these deliverables against every completion criterion — find anything claimed done but not actually verified."

The subagent returns findings to main context (≤400 words). Record sign-off or objections in `workstream-notes.md` prefixed `[validate]`.

**If objections are raised:** resolve them before proceeding. Unresolved objections block advance to cleanup.

### 3. Advance phase

Only when the gate is GO **and** adversarial QA signs off:

```bash
python -B tools/workstream.py complete <name>
```

Load `actions/cleanup.md`.
