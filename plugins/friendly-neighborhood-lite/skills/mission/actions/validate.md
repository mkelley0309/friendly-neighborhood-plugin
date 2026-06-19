# Action: Validate

> **Phase council** (QRDPIV: V) — consult only when the concern is live (full map in `/friendly-neighborhood-lite:creed`): driver `jameson` (adversarial QA); counsel none; watch villain `mysterio` (claiming done without proof — the exact failure this phase exists to catch).

Confirm the mission's outputs are real before closing. A mission does not advance to cleanup on faith.

## Steps

### 1. Run the deterministic gate

```bash
python -B tools/gate.py run
```

This executes your defined checks (tests, lint, types — set them once with `gate.py init`) and returns a hard GO / NO-GO by exit code. Also acceptable: the `/verify` or `/run` skill, or the project's test command from its `CLAUDE.md`. If the project genuinely has no automated checks, say so explicitly and verify behavior by an observable alternative — never skip silently.

Record the result (command run, exit code, what passed or failed) in `workstream-notes.md` prefixed `[validate]`.

**If NO-GO:** stop. Document the failures in `workstream-notes.md` and surface them to the user. Return to `actions/implement.md` to remediate, then re-run the gate.

### 2. Adversarial QA — spawn `jameson`

Hand the gate result and the mission's completion criteria (from `plan.md`) to `jameson` ("this is a menace, prove me wrong"). `jameson`'s job: red-team the deliverables against every completion criterion — find anything claimed done but not actually verified.

`jameson` returns findings to main context (≤400 words). Record sign-off or objections in `workstream-notes.md` prefixed `[validate]`.

**If jameson raises objections:** resolve them before proceeding. Unresolved objections block advance to cleanup.

### 3. Advance phase

Only when the gate is GO **and** `jameson` signs off:

```bash
python -B tools/workstream.py complete <name>
```

Load `actions/cleanup.md`.
