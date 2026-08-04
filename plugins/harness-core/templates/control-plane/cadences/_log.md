---
note_type: cadence-ledger
tags: [cadences, log]
---

# Cadence Log

Running record of closed cadences, newest first. Written at close by the `cadence` skill, immediately before the folder is deleted.

**This is the durable record.** The cadence folder does not survive closing, so anything not carried into an entry here (or rescued to `outputs/`, the vault, or a project) is gone.

A cadence closes one of two ways, and both are logged:

- **Retired** — the job is done, or it was automated away, or the thing it watched stopped existing. A retirement caused by *the cadence automating itself out of a job* is a success, and the entry should say so plainly.
- **Abandoned** — it stopped mattering, or nobody ran it. Say why. An abandoned cadence with no reason recorded is indistinguishable from one that was silently forgotten.

Each entry carries: what **recurred** and on what trigger, how it **ran** (how many times, over what period, what the gate said), how it **ended**, and what is **carried forward** — most usefully, whatever the self-improvement diary had accumulated that outlives the cadence itself.

**Read it for repeats.** A cadence abandoned twice for the same reason is telling you the work is shaped wrong, not that the cadence was.

---

*(no cadences closed yet)*
