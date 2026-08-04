---
note_type: stakeout-ledger
tags: [stakeouts, log]
---

# Stakeout Log

Running record of closed stakeouts, newest first. Written at close by the `stakeout` skill, immediately before the folder is deleted.

**This is the durable record.** The stakeout folder does not survive closing, so anything not carried into an entry here (or rescued to `outputs/`, the vault, or a project) is gone.

A stakeout closes one of two ways, and both are logged:

- **Retired** — the job is done, or it was automated away, or the thing it watched stopped existing. A retirement caused by *the stakeout automating itself out of a job* is a success, and the entry should say so plainly.
- **Abandoned** — it stopped mattering, or nobody ran it. Say why. An abandoned stakeout with no reason recorded is indistinguishable from one that was silently forgotten.

Each entry carries: what **recurred** and on what trigger, how it **ran** (how many times, over what period, what the gate said), how it **ended**, and what is **carried forward** — most usefully, whatever the self-improvement diary had accumulated that outlives the stakeout itself.

**Read it for repeats.** A stakeout abandoned twice for the same reason is telling you the work is shaped wrong, not that the stakeout was.

---

*(no stakeouts closed yet)*
