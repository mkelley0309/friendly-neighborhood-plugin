# Action: Validate

> **Phase council** (QRDPIV: V) — consult only when the concern is live (full map in `/friendly-neighborhood:creed`): driver `gwen` (run it — test functionality against the criteria); counsel `jameson` (adversarial); watch villains `mysterio` (claiming done without proof — the exact failure this phase exists to catch), `cat` (security holes left open), `electro` (fragile/cascading).

Confirm the mission's outputs are real before closing. A mission does not advance to cleanup on faith.

## Steps

### 1. Run the deterministic gate

```bash
python -B tools/gate.py run
```

This executes your defined checks (tests, lint, types — set them once with `gate.py init`) and returns a hard GO / NO-GO by exit code. Also acceptable: the `/verify` or `/run` skill, or the project's test command from its `CLAUDE.md`. If the project genuinely has no automated checks, say so explicitly and verify behavior by an observable alternative — never skip silently.

Record the result (command run, exit code, what passed or failed) in `workstream-notes.md` prefixed `[validate]`.

**If NO-GO:** stop. Document the failures in `workstream-notes.md` and surface them to the user. Return to `actions/implement.md` to remediate, then re-run the gate.

### 2. Functional validation — spawn `gwen`

Hand the gate result and the mission's completion criteria (from `plan.md`) to `gwen`. Her job: *exercise* the work — run it, drive each flow, probe the edges — and confirm it actually does what each completion criterion says, reporting evidence ("ran X, got Y, expected Z"), not opinion. `jameson` may be spawned alongside as the adversarial second pair of eyes on the framing.

`gwen` returns findings to main context (≤400 words). Record sign-off or objections in `workstream-notes.md` prefixed `[validate]`.

**If gwen raises objections:** resolve them before proceeding. Unresolved objections block advance to cleanup.

### 3. Security red-team (when the surface warrants it) — spawn `cat`

If the work touches auth, secrets, input handling, or any external surface, spawn `cat` to red-team it. If Black Cat finds an open window — a hardcoded secret, a missing auth check, an injection surface — close it before advancing. Record findings in `workstream-notes.md` prefixed `[validate]`.

### 4. Advance phase

Only when the gate is GO, `gwen` signs off, **and** any `cat` findings are resolved:

```bash
python -B tools/workstream.py complete <name>
```

Load `actions/cleanup.md`.
