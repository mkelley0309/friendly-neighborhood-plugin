---
name: spider-sense
description: A manual pre-flight danger check before any risky or hard-to-reverse operation — mass deletes, force-pushes, schema drops, writes outside the project, secret exposure. Run this yourself when something feels off. The automatic PreToolUse hook covers routine operations; this skill is for when you want to think it through deliberately.
---

# Spider-Sense Pre-Flight Protocol

Something's tingling. Run this checklist before you proceed.

---

## Step 1 — Pause

Stop. Don't execute yet. Name the operation you're about to perform in one sentence.

## Step 2 — Identify the Risk

Ask: could this be destructive or irreversible? Watch for:

- Mass delete (`rm -rf`, `DROP TABLE`, bulk overwrite)
- Force-push to a shared branch
- Schema migrations that drop columns or tables
- Writes outside the project directory
- Any operation that touches secrets, credentials, `.env`, permissions, or otherwise widens what's exposed
- Bulk API mutations with no dry-run option

## Step 3 — State the Blast Radius

What breaks if this goes wrong? Who or what is affected? Is it recoverable?

## Step 4 — Choose Minimum Force

Is there a safer alternative that achieves the same outcome?

- Soft delete instead of hard delete?
- Dry-run before live run?
- Backup before overwrite?
- A targeted change instead of a bulk one?

Default to the safer path unless you have an explicit reason not to.

## Step 5 — Confirm Before Proceeding

State your plan out loud (or in a comment). Get a thumbs-up if the stakes are high. Then go.

---

## Pairing Notes

This manual protocol works alongside two automated safety layers:

- **PreToolUse spider-sense hook** — intercepts high-risk tool calls automatically and applies the same logic without you having to ask.
- **Enforced deny rules** — certain operations are blocked outright regardless of instruction; no override path exists.

If the hook fires and you disagree with it, that's worth a second look before you push back.
