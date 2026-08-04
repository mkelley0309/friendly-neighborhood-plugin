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

3. **Capture handoff + lessons + friction** in `index.md`:
   - **Handoff** — one line for the next task or workstream picking up from here (omit if nothing to hand off).
   - **Lessons** — one line worth repeating or avoiding *about this work* (omit if nothing learned).
   - **Friction** — one line if the *harness* got in the way (omit if it didn't, which is the common case). Test: would this still be true on an unrelated task? If it names the subject matter it is a lesson, not friction.

4. **Carry unresolved friction out of the task.** For each Friction line still unresolved, append a row to `control-plane/_harness/friction.md` under Open — `| date | task | {name} | {the rule} | 1 |`. Create the file from the `workstream` skill's `framework-templates.md` if absent. If an equivalent row already exists, increment its **Recurred** count rather than adding a duplicate — recurrence is the signal that it needs fixing. Skip anything already fixed during the task.

5. **Resolve every checkbox before closing.** A completed task must contain no `- [ ]`. Frontmatter `status` is the *portfolio* signal, but an unchecked box is a *file-level* signal, and anything that reads checkboxes rather than frontmatter (an Obsidian task query, a Base, a plain grep) will keep reporting a closed task as live work. Both signals have to agree. Resolve each remaining item into exactly one of three states:
   - **Done** — tick it.
   - **Dropped** — delete the checkbox and state it as prose under Lessons or Handoff, with the reason. Never tick something that did not happen.
   - **Carried** — delete the checkbox and name the destination in Handoff: the task, workstream or objective that now owns it.

   This matters most for a task closed early or closed against an unmet gate, which is exactly when the leftover box is both the most tempting to leave and the most misleading.

6. **Rescue anything durable before it is destroyed.** The folder is deleted at step 8, so sweep it first. Produced artifacts go to `control-plane/outputs/{name}/`, vault content to `knowledge/vault/` via `/harness-core:knowledge`, source material to `intake/_archive/`, code to `projects/{name}/`. Most tasks hold nothing but their own `index.md` and need no action, but the one that does is the one that loses primary evidence. Name what you moved in the log entry.

7. **Write the log entry** in `control-plane/tasks/_log.md` (create it from the header in that file if absent), newest first, as a dated section:

   ```markdown
   ## YYYY-MM-DD · task-name

   **Was.** The assignment, in a sentence or two.
   **Produced.** What actually came out, and where anything durable now lives.
   **Carried forward.** The lesson worth repeating. Say "nothing" rather than inventing one.
   **Handoff.** Only if something picks up from here.
   ```

   **This is the durable record, not a summary layer** — the folder does not survive, so anything not carried here or rescued at step 6 is gone. Keep it proportional (a task is the lightest tier and never gets workstream-grade distillation) but not so thin the work becomes unreconstructable.

   This is the lessons analogue of `_harness/friction.md`, on the same argument: a lesson that lives only inside one task will not be noticed on the next one. **Check the log for a repeat while you are in it.** A lesson appearing twice belongs somewhere more permanent than a log — a skill, a tool, or a checklist — and saying so in the new entry is the most useful thing a task close can produce.

8. **Complete, then delete:**

```bash
python -B tools/task.py complete <name>
python -B tools/task.py delete <name>
```

`complete` sets `status: complete` and moves the row from Active to Complete in the portfolio index, repointing its link at `_log.md`. `delete` removes the folder permanently. **Verify the log entry exists before deleting** — read it back, the same discipline the workstream cleanup applies.

## Notes

- Tasks are lightweight, and the lightness is in the *record*, not the retention: one dated section in `_log.md` rather than a folder of artifacts. A workstream gets a whole `_log/` file because it has `research.md` and `_working/` bulk to compress. A task gets a paragraph.
- If the task grew into multi-session work, promote it instead: open a workstream and carry this task's assignment across as the originating capture. Promote before completing, not after — completing deletes the folder.
