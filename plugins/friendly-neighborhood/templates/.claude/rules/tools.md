---
description: Operating contract for the tools subtree — capability primitives, scripts, and CLIs.
paths: ["tools/**"]
---

# Tools

Capability primitives — scripts, CLIs, helpers that are not domain-specific. Invoked by control-plane, projects, or skills.

```
tools/
  CLAUDE.md    ← thin pointer (contract is here)
  {tool-name}/ or {tool-name}.{ext}
```

---

## What Belongs Here

- Generic utilities usable across multiple projects
- Shared scripts (file conversion, format validation, cross-system glue)
- Small CLIs wrapping external APIs or services

## What Does Not

- Domain-specific logic → `projects/{name}/`
- Prompt assets → `prompts/`
- Knowledge content → `knowledge/`
- One-off scratch → campaign `_working/`

---

## Conventions

- Each non-trivial tool gets a folder with a `README.md` (purpose, usage, dependencies)
- Prefer idempotent, composable scripts over monolithic pipelines
- Structured output (JSON, JSONL) over free-form
- Document invocation examples so callers don't read source

---

## Boundaries

- Must not reach into `projects/` internals
- May read from `knowledge/sources/`; may not write to `knowledge/vault/`
- Do not orchestrate — coordination belongs in control-plane

---

## Control-Plane Tools

The CLIs below use stdlib only (argparse, pathlib, datetime, re) — no third-party packages. They resolve their workspace root from `$WORKSPACE_ROOT` env var, falling back to `os.getcwd()`. Set `WORKSPACE_ROOT` to your repo root before running, or run them from the repo root. Run with `python -B` to skip `__pycache__` bytecode generation.

These map to the **three tiers of work**: responsibilities (long-lived strategy), campaigns (the heavy QRDBIV lifecycle), and missions (lightweight units). `gate.py` is the deterministic go/no-go check used at validate.

### workstream.py — the heavy (QRDBIV) tier

Manages the heavy QRDBIV lifecycle at `control-plane/workstreams/{name}/index.md`.

```
python -B tools/workstream.py list
python -B tools/workstream.py create <name> [--framework qrdbiv|rbiv] [--parent objectives/<name>] [--title "Title"]
python -B tools/workstream.py status <name>
python -B tools/workstream.py next <name>
python -B tools/workstream.py advance <name> <phase>
python -B tools/workstream.py check-step <name> "<step text>"
python -B tools/workstream.py link <campaign> <mission>     # register a child mission
python -B tools/workstream.py block <name> "<reason>"
python -B tools/workstream.py unblock <name>
python -B tools/workstream.py complete <name>
python -B tools/workstream.py archive <name> [--log-date YYYY-MM-DD] [--description "..."]
python -B tools/workstream.py delete <name>
```

Valid phases: `questions research design blueprint implement validate complete cleanup`
Frameworks: `qrdbiv` (default, all phases) · `rbiv` (clear-spec: research→blueprint→implement→validate→cleanup)

### mission.py — the lightweight tier

Manages lightweight, often-repeatable units at `control-plane/missions/{name}/index.md`. No phase machine — a mission carries just enough admin (mission, checklist, handoff, lessons) to be resumable and handed off.

```
python -B tools/mission.py list
python -B tools/mission.py create <name> [--parent workstreams/<name>|objectives/<name>] [--title "Title"]
python -B tools/mission.py status <name>
python -B tools/mission.py validate <name>     # stamp validated: <today> after the work is confirmed
python -B tools/mission.py complete <name>
python -B tools/mission.py delete <name>
```

### objective.py — the strategy tier

Manages long-lived responsibilities with structured progress tracking at `control-plane/objectives/{name}/index.md` — Key Results, milestones, linked campaigns, a checkpoint patrol, health, and an append-only decisions log.

```
python -B tools/objective.py list
python -B tools/objective.py create <name> [--title "Title"]
python -B tools/objective.py status <name>     # prints KRs, milestone done/total, linked campaigns
python -B tools/objective.py health <name> <on-track|at-risk|blocked|stale>
python -B tools/objective.py set-cadence <name> "<cadence>"
python -B tools/objective.py add-kr <name> "<result>" "<target>"
python -B tools/objective.py update-kr <name> "<result>" "<current>"
python -B tools/objective.py add-milestone <name> "<text>"
python -B tools/objective.py check-milestone <name> "<text>"
python -B tools/objective.py link-campaign <responsibility> <campaign>     # link a child campaign
python -B tools/objective.py log-decision <name> "<decision>" "<rationale>"
python -B tools/objective.py complete <name>
```

### gate.py — the deterministic go/no-go gate

Runs measurable checks (tests, lint, build) and returns a hard GO / NO-GO. Used at the campaign **validate** phase and to close a mission.

```
python -B tools/gate.py init                 # write a gate.json template
python -B tools/gate.py run [--config gate.json] [--check "name=command"]
```

Exit code `0` = GO (all checks passed), `1` = NO-GO. Compose multiple `--check "name=cmd"` flags or list them in `gate.json`.

### setup-keys.ps1

One-time PowerShell script to set API keys as persistent user-level environment variables. Run from the repo root:

```powershell
.\tools\setup-keys.ps1 -AnthropicKey "sk-ant-..." -OpenRouterKey "sk-or-..."
```
