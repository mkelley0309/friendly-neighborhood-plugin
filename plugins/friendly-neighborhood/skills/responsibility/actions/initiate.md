# Action: Initiate Responsibility

Create a new responsibility. Load this file only.

## When to Run

User is starting a formal, review-cycle-measured objective — not a tactical patrol or mid-tier mission. Signals:
- "This is one of my responsibilities this cycle"
- "I'm being measured on this"
- Work that will span multiple missions or patrols and multiple months
- Strategic objective that warrants a persistent decisions log

## Steps

### 1. Name it

Propose a `kebab-case-name` that matches or reflects the language used in the formal review process. Confirm with the user before creating anything.

Examples: `neighborhood-watch`, `web-slinger-readiness`, `city-grid-resilience`.

### 2. Ask the shaping questions

The Responsibility section is the most important. Don't let it be vague. Surface these if not already clear:

- What problem does this responsibility solve? (not what it is — what it enables)
- Who are the stakeholders measuring it?
- What does success look like at review time? What are the 1–3 measurable Key Results?
- What's the relationship to existing responsibilities?
- What review cadence makes sense (monthly, bi-weekly, quarterly)?

One focused message, 2–3 questions. Wait for answers before writing.

### 3. Create the responsibility

Run:

```
python -B tools/objective.py create {kebab-case-name} --title "{Title}"
```

Then write `index.md` into `control-plane/objectives/{name}/` as the first file.

**Frontmatter:**

```yaml
objective: {kebab-case-name}
status: active
health: on-track
cadence: {cadence}
created: {YYYY-MM-DD}
tags: [objective, {secondary-tag}, ...]
note_type: objective
```

**Required sections (in order):**

```markdown
# {Responsibility Title} — Responsibility Context

## Responsibility

{1–2 paragraphs — what this is and why it matters. Tie to strategy where relevant.}

## Key Results

| Result | Target | Current |
|---|---|---|
| *(populated via add-kr)* | | |

## Milestones

- [ ] *(populated via add-milestone)*

## Missions

*(linked workstreams advance this responsibility — populated via link-mission)*

## Success Criteria

- {concrete, verifiable criterion}
- {concrete, verifiable criterion}

## Dependencies

- **{dependency name}** — {what's needed, from whom, why}

## Key Decisions Log

| Decision | Rationale | Date |
|---|---|---|
| *(append-only; never truncated)* | | |

## Definition of Done

{Specific conditions under which this responsibility closes. What "done" means for review purposes.}

## Related Notes

- {markdown links to parent strategy, dependent responsibilities}
```

### 4. Seed the structure

After creating the file, set up structured tracking with the CLI:

**Set cadence and initial health:**
```
python -B tools/objective.py set-cadence {name} "{cadence}"
python -B tools/objective.py health {name} on-track
```

**Add 1–3 Key Results** (one `add-kr` call per result):
```
python -B tools/objective.py add-kr {name} "{measurable result}" "{numeric or qualitative target}"
```

**Seed milestones** (one `add-milestone` call per checkpoint):
```
python -B tools/objective.py add-milestone {name} "{concrete checkpoint text}"
```

**Link any already-known workstreams advancing this responsibility:**
```
python -B tools/objective.py link-mission {name} {workstream-name}
```

These are all idempotent and safe to run in sequence.

### 5. Update portfolio index

Add a row to the Active table in `control-plane/objectives/index.md`:

```markdown
| [{name}]({name}/index.md) | {one-line description} | Active |
```

### 6. Confirm and hand off

Tell the user: responsibility created, Key Results defined, milestones seeded, cadence set, decisions log is empty and append-only.

If the user is ready to spin up coordinated work toward this responsibility: suggest the `/friendly-neighborhood:mission` skill to open a mission, then link it with `link-mission`. For lightweight tactical work that doesn't warrant a mission, suggest `/friendly-neighborhood:patrol` instead.
