---
note_type: patrol-ledger
tags: [patrols, log]
---

# Patrol Log

Running record of closed patrols, newest first. Written at close by the `patrol` skill, immediately before the folder is deleted.

**This is the durable record.** The patrol folder does not survive closing, so anything not carried into an entry here (or rescued to `outputs/`, the vault, or a project) is gone.

A patrol closes one of two ways, and both are logged:

- **Retired** — the job is done, or it was automated away, or the thing it watched stopped existing. A retirement caused by *the patrol automating itself out of a job* is a success, and the entry should say so plainly.
- **Abandoned** — it stopped mattering, or nobody ran it. Say why. An abandoned patrol with no reason recorded is indistinguishable from one that was silently forgotten.

Each entry carries: what **recurred** and on what trigger, how it **ran** (how many times, over what period, what the gate said), how it **ended**, and what is **carried forward** — most usefully, whatever the self-improvement diary had accumulated that outlives the patrol itself.

**Read it for repeats.** A patrol abandoned twice for the same reason is telling you the work is shaped wrong, not that the patrol was.

---

*(no patrols closed yet)*
