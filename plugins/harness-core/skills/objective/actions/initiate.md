# Action: Initiate Objective

Create a new objective. Load this file only.

## When to Run

User is starting a formal, review-cycle-measured goal. Signals:
- "This is one of my objectives this cycle"
- "I'm being measured on this"
- Work that will span multiple workstreams and multiple months
- Strategic goal that warrants Key Results, milestones, and a persistent decisions log

## Steps

### 1. Name it

Propose a `kebab-case-name` that matches or reflects the language used in the formal review process. Confirm with the user before creating anything.

### 2. Create the folder and `index.md`

Run:

```
python -B tools/objective.py create {kebab-case-name} --title "{Title}"
```

The CLI scaffolds `control-plane/objectives/{name}/index.md` with Key Results, Milestones, Workstreams sections, and an append-only Key Decisions Log.

### 3. Shape the objective

Ask the shaping questions (one focused message, 2–3 questions, wait for answers before writing):

- What problem does this objective solve? (not what it is — what it enables)
- Who are the stakeholders measuring it?
- What does success look like at review time?
- What's the cadence — when are formal reviews?

Fill in the **Objective** section and **Success Criteria** once you have answers.

### 4. Set health and cadence

```
python -B tools/objective.py set-cadence {name} "quarterly"
python -B tools/objective.py health {name} on-track
```

### 5. Add Key Results (if the user has them)

```
python -B tools/objective.py add-kr {name} "<result>" "<target>"
```

### 6. Confirm and hand off

Tell the user: objective created, Key Results table ready, decisions log is empty and append-only.

If the user is ready to spin up work toward this objective: suggest the `workstream` skill with `parent: "objectives/{name}"`. For lightweight single-thread work, suggest the `task` skill.
