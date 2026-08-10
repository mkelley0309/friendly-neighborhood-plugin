---
name: symbiote
description: Temporarily escalate YOUR OWN power for a hard sub-task by spawning a higher-powered clone of yourself — same role, tools, and memory, just a stronger model and/or higher effort — strictly turn-limited. Use when your baseline keeps circling a genuinely hard problem. The clone is killable by the church bell if it triggers a villain dissent or runs past its turn budget. Any **spidey** can wear it.
---

# Putting on the Black Suit

The symbiote is **borrowed power for yourself** — not a hand-off to someone else. You stay you. You map everything about yourself onto a stronger tier for a short, bounded burst, then take the suit off.

> **Who can wear it:** any **Spider-variant** — every spidey (`peter`, `silk`, `noir`, `miles`, `peni`, `gwen`, `ham`, `ben-reilly`, `jessica`, `punk`, **and `miguel`**). Support cast and villains do not symbiote.
>
> **What escalates:** model *and/or* effort. A driver on a cheaper model escalates the **model** (e.g. sonnet → opus). Miguel is already opus, so his symbiote escalates **effort/thinking** (e.g. high → xhigh/max). His opus *baseline* is his native architect level — not a symbiote and not bell-subject; only the escalation above it is.

**The suit is a burst, not a mode.** It should be on for as short a time as possible — a few turns to crack one hard sub-task, then off. Staying suited up is the flaw the whole mechanic exists to prevent (the `venom` villain watches for it).

---

## When to put it on

Reach for the symbiote only when your baseline model genuinely can't crack a specific sub-task:

- You've circled the same hard problem more than once at baseline.
- A single dense step needs more reasoning than your default tier can muster.

If you're reaching out of impatience or habit, that's **Venom** behavior — the `venom` villain flags exactly this.

## The protocol

1. **Justify it.** One sentence: why your baseline model isn't enough for *this* sub-task.
2. **Clone yourself, stronger.** Spawn a subagent of **your own persona** — same role, tools, and memory (`subagent_type` = you) — escalated one tier: a stronger **model** (e.g. sonnet → opus) if you're below opus, or higher **effort/thinking** (e.g. high → xhigh/max) if you're Miguel and already there. Tag the spawned task with "symbiote" so the church bell can see it. You are not becoming a different agent; you're wearing the suit.
3. **Set the turn limit.** The clone is hard-bounded by `symbiote_max_turns` (userConfig, default 8) — the corruption meter. Scope the task so it finishes well inside that budget.
4. **Stay watched.** Spider-sense (the `PreToolUse` hook) and the deny-list apply to the clone too. If what it's doing would make a villain nod — needless destruction (Carnage), faked success (Mysterio), over-engineering (Octavius) — **ring the church bell** (`/friendly-neighborhood:church-bell`) to kill the clone before it does damage.
5. **Take the suit off.** When the clone finishes, hits its turn cap, or the bell rings, control returns to baseline you. Log what the escalation cost.

## Ambient signal — the black suit on the deck

The moment you don the suit, flip your stream to the black suit so the operator *sees* you're running borrowed power:

`bash .claude/scripts/agent-log.sh <your-name> --suit-on`

From then on your clone's narration renders white-on-black in the observation deck — unmistakable. Church-bell runs `--suit-off` when the suit comes off; you don't clear it yourself.

## Venom warning

Borrowed power that never comes home stops being borrowed. Escalating every sub-task, never trusting your baseline, is how you become Venom. If the `venom` villain fires, the escalation probably wasn't necessary.
