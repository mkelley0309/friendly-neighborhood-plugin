# Action: Initiate a Mission

## Steps

1. **Name** — propose `kebab-case-name`, confirm before creating.
2. **Parent** — check `control-plane/workstreams/index.md` and `control-plane/objectives/index.md`; standalone if no match.
3. **Create**:

```bash
python -B tools/mission.py create <name> [--parent workstreams/<name>|objectives/<name>] [--title "Title"]
```

4. **Write the mission** in `index.md` — one or two sentences: what the mission is, what you understand the job to be. This is the mission's durable value.
5. **Populate the checklist** with concrete steps.
6. **Link to parent** (if applicable):

```bash
python -B tools/workstream.py link <workstream-name> <mission-name>
```

## Hand off

Proceed directly to doing the work — no phase advance needed. Missions are lightweight and execute without a phase machine.
