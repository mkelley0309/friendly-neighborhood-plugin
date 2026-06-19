# Action: Complete a Task

## Steps

1. **Validate first — don't close on faith.** Run the gate or verify the work was actually done:

```bash
python -B tools/gate.py run
```

Or confirm via the project's test command / `/verify` skill. If the task has no automated checks, verify by observation and note what was checked.

2. **Record validated date:**

```bash
python -B tools/task.py validate <name>
```

3. **Capture handoff + lessons** in `index.md`:
   - **Handoff** — one line for the next task or workstream picking up from here (omit if nothing to hand off).
   - **Lessons** — one line worth repeating or avoiding (omit if nothing learned).

4. **Complete:**

```bash
python -B tools/task.py complete <name>
```

This sets `status: complete` and moves the task from Active to Complete in the portfolio index.

## Notes

- Tasks are lightweight — no log entry, no folder deletion. The `index.md` is the durable record.
- If the task grew into multi-session work, promote it instead: open a workstream and link this task's `index.md` as the originating capture.
