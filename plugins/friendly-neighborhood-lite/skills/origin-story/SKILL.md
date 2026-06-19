---
name: origin-story
description: Scaffold a fresh Friendly Neighborhood workspace into the current project — the constitution, the three-tier control-plane (responsibility/mission/patrol), an empty knowledge vault, the portable CLIs, and the auto-loading .claude/rules contracts. Run this once on a new project after installing the plugin. Safe to re-run; never overwrites existing files.
disable-model-invocation: true
---

# Origin Story — scaffold your workspace

Every web-slinger needs an origin. This sets up a working, domain-neutral harness in the current project so the other skills (patrol, responsibility, mission, web-archive) have a home. It copies the plugin's bundled `templates/` into your project and **never overwrites anything that already exists**.

## Steps

1. **Confirm you're in the right place.** The scaffold lands in the current project directory (`$CLAUDE_PROJECT_DIR`, or the directory Claude Code was launched from). Tell the user where that is and confirm before writing if it looks unexpected.

2. **Check for Python 3** (the harness's one prerequisite — the orchestration CLIs need it). Try in order until one prints a 3.x version:
   - `python3 --version`
   - `python --version`
   - `py --version`

   If **none** works, stop and tell the user:
   > Friendly Neighborhood needs Python 3 for its orchestration CLIs (patrol / responsibility / mission). Install it, then re-run `/friendly-neighborhood-lite:origin-story`:
   > • macOS: `brew install python` (or python.org)
   > • Windows: `winget install Python.Python.3` (or python.org)
   > • Linux: your package manager, e.g. `sudo apt install python3`

   Remember which launcher worked — it's the one to use (with `-B`) for the CLIs everywhere (`python3` / `python` / `py`).

3. **Run the scaffolder** with the working interpreter:
   ```
   <python> -B "${CLAUDE_SKILL_DIR}/../../scripts/scaffold.py"
   ```
   (e.g. `python3 -B "${CLAUDE_SKILL_DIR}/../../scripts/scaffold.py"`)

4. **Set the concurrency budget.** Ask: *"How many subagents may run in flight at once? (soft budget — a cost/coordination guideline, not a safety cap. Default 2; raise it if your machine and quota allow.)"* Take the answer (a number, or "2" if they accept the default) and set it in the scaffolded contract: in `_addenda/claude-code.md`, replace `up to 2 subagents in flight at once` with `up to <N> subagents in flight at once`. If they keep the default, leave it.

5. **Report** what it created vs. skipped, then point the user at next steps:
   - `constitution.md` is the base contract; subtree contracts auto-load via `.claude/rules/` as you work.
   - `/friendly-neighborhood-lite:creed` loads the operating doctrine.
   - Start work: `/friendly-neighborhood-lite:mission` (complex, multi-session QRDPIV work), `/friendly-neighborhood-lite:patrol` (a lightweight unit or one iteration), `/friendly-neighborhood-lite:responsibility` (a long-lived measured goal), or `/friendly-neighborhood-lite:web-archive` (knowledge pipeline).
   - Optional UX: the knowledge vault is plain markdown; install the kepano Obsidian skills separately if you want graph/wikilink/Bases tooling (`npx skills add kepano/obsidian-skills -g -a claude-code`). Not required.

## Notes

- **Idempotent.** Re-running only fills in missing files; it never clobbers your work.
- This is the only skill that writes a whole tree — that's why it's user-invoked only (`disable-model-invocation`). The model won't scaffold without you asking.
