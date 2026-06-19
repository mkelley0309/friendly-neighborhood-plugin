# Intake

Capture layer for unstructured input. Nothing here is committed work — it is raw material awaiting triage.

---

## Purpose

Intake holds ideas, notes, chat-derived thinking, and partial thoughts that may eventually become a patrol, a mission, a responsibility, or be discarded. It is not an execution system.

---

## What Belongs Here

- Raw ideas not yet shaped into a patrol, mission, or responsibility
- Chat exports or conversation snippets worth revisiting
- Half-formed hypotheses, open questions, future candidates
- Anything that needs triage before it earns a place in the control plane

## What Does NOT Belong Here

- Anything already structured as a patrol (`patrols/`)
- Anything already structured as a mission (`workstreams/`)
- Anything already structured as a responsibility (`objectives/`)
- Execution artifacts, plans, or research outputs

---

## Lifecycle

```
capture → triage → promote (patrol | mission | responsibility) | discard
```

Items sit in intake until reviewed. On triage:
- **Promote** — shape the idea into a `patrols/`, `workstreams/`, or `objectives/` entry, which records the source in `intake_source`. The intake file **stays in place** while the consuming work is live, so the work can be restarted from its original capture if something goes wrong. The file is moved to `intake/_archive/` (not deleted) and dropped from the live listing only when the consuming work closes — at mission cleanup, or when a parent responsibility is marked `complete`. Never archived at promotion.
- **Discard** — delete the intake entry with no log required.

`_archive/` preserves the capture→promotion trace. There is no durable log for discarded intake — only promoted items leave a trace.

---

## Relationship to Control Plane

Intake feeds routing decisions. It is upstream of responsibilities, missions, and patrols — not a peer in the execution sense. A session that starts with unstructured input should land here first, then triage before touching the rest of the control plane.
