---
name: church-bell
description: The kill switch for a symbiote. Terminates an escalated self-clone subagent — immediately if it trips a villain dissent (about to do real damage), when it overruns its turn budget, or manually. Confirms the return to baseline and logs the cost.
---

# Ring the Bell

The church bell takes the symbiote off — by force if it has to. Borrowed power that starts doing harm gets cut, now, before it spreads.

---

## When it rings

1. **Villain dissent during a symbiote (the urgent one).** The escalated clone is about to do something a villain would *approve* of — needless destruction (Carnage), a force-push or schema drop, faked verification (Mysterio), wasted tokens (Kingpin). **Ring immediately: kill the clone before it acts.** This is the bell's whole reason for existing.
2. **Turn budget exhausted.** The clone hit `symbiote_max_turns` (the corruption meter). It stops; you take over.
3. **Manual.** You decide the suit has been on long enough, or the escalation isn't paying off.

> The bell is for **symbiotes** — escalated self-clones — not for any persona running at its native level. Miguel's baseline opus doesn't ring it; but if Miguel puts the suit on (escalating effort to xhigh/max), *that* escalation rings like any other.

## The protocol

1. **Kill the clone.** Stop the symbiote subagent cleanly — do not let it complete the turn you're objecting to. Discard the in-flight action that tripped the dissent.
2. **Log the cost.** Turns consumed, approximate tokens, and why it was rung (dissent / overrun / manual). Honesty here keeps the budget real.
3. **Confirm baseline.** You are the baseline persona again — your default model, standard effort, no borrowed power.
4. **Resume deliberately.** Review whatever the clone produced *before* the kill with fresh, baseline judgment. Keep what's sound; drop what tripped the alarm.

## Automatic vs. manual

The `SubagentStop` hook rings the bell automatically when a symbiote clone's session ends (turn cap or completion) and confirms the return to baseline. The urgent case — killing on villain dissent mid-flight — is yours to trigger the moment spider-sense tingles or a villain would nod. The suit is off. Stay grounded.
