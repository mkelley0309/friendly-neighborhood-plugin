# Action: Research

> **Phase council** (Relay: R) — consult only when the concern is live (full map in `/friendly-neighborhood:creed`): drivers `silk` (recall/docs/codebase), `noir` (investigation); counsel `aunt-may`, `ned`, `madame-web`; watch villains `lizard`, `vulture`, `kraven`, `kingpin`.

Research is **mandatory** for every formal campaign — Payload Relay and Short Relay alike. There is no path from Questions (or Initiate) directly to Design or Blueprint without a research.md. If source material is provided by the user, it still passes through the research protocol: write it to `_working/`, then distill from `_working/`.

---

## Core Principles

**Progressive distillation.** Each pass produces raw findings saved to disk. Distillation is a separate, bounded step that reads only those saved files — never the main conversation, never the pass output held in memory.

**Structured handoffs to clean context.** Each subagent gets a scoped mission and a bounded return. Distillation runs in a fresh context that has never seen the original request, the conversation, or the pass instructions — only the `_working/` files. This is intentional: it forces semantic compression, not summarization of what was said.

**Limited token usage.** Each pass subagent returns ≤2k tokens to main context — a confirmation that the file was written and the key themes found, nothing more. The main context never reads raw pass output. After all passes are complete, the main context reads only `research.md`.

**Semantic density.** `research.md` must earn its length. Every sentence must be load-bearing for Design or Blueprint. No recaps of what was asked, no meta-commentary about sources, no restating what the user already knows.

---

## Pass Selection

| Campaign type | Knowledge | Web | Codebase |
|---|---|---|---|
| Knowledge maintenance / reorg | ✓ | — | — |
| GTM / content generation | ✓ | ✓ | — |
| Build project (greenfield) | ✓ | ✓ | — |
| Build project (extending existing) | ✓ | ✓ | ✓ |
| Competitive / external research | ✓ | ✓ | — |
| System setup / process design | ✓ | — | — |
| Research with deliverable | ✓ | ✓ | — |

When the user provides source material directly (paste, file, link), treat it as an additional pass: write it to `_working/research-provided-{n}.md` before doing anything else.

---

## Mandatory Protocol

### Before Running Any Pass

1. Confirm `_working/` exists in the campaign folder. Create it if not: it must exist before any pass runs.
2. Read `index.md` and `request.md` (if it exists). Do not read any other campaign file.
3. Determine which passes to run from the table above.

### Per Pass — Default to a Subagent (Sonnet)

Each pass is, by default, a separate subagent call. The subagent's job is **write findings to disk and return a short confirmation** — not to produce a finished summary for main context consumption.

**Main-context fallback.** If this session operates under a policy that forbids unrequested subagent spawns, or delegation genuinely isn't available, run the pass directly in main context instead: write the same findings file, to the same path, with the same frontmatter and `## Sources` section, before moving on to the next pass or to distillation. The discipline that matters — findings on disk before distillation reads them, every finding sourced — is what this protocol actually protects; a subagent is the default way to get there, not the only one.

Subagent instructions must include:
- The specific question or scope for this pass
- The target file path: `control-plane/workstreams/{name}/_working/research-{type}-{n}.md`
- A hard instruction: **"Write your findings to that file before returning. Do not return findings as your response — confirm the file was written and name the top 3–5 themes found."**
- A source-capture instruction: **"Every finding must be traceable to a source — a vault file path, a URL, a codebase file path, or 'user-provided'. Do not record anything derived solely from model weights. If you cannot point to a source, omit the finding."**
- Token budget for the return: ≤200 words back to main context

Pass file frontmatter:
```yaml
note_type: workstream-artifact
workstream: {name}
pass_type: knowledge | web | codebase | provided
tags: [workstream/{name}]
```

Pass file structure — each file must end with a `## Sources` section:
```markdown
## Sources

- `knowledge/vault/path/to/file.md` — brief description of what was taken from it
- https://example.com/article — brief description
- User-provided, YYYY-MM-DD — [description of the material]
```

Rules for sources:
- Web pass: include full URL for every factual claim. If a URL is unavailable, omit the claim.
- Knowledge/vault pass: include the vault file path for every finding. Line numbers where relevant.
- Codebase pass: include file path and line number range.
- Provided pass: note "User-provided" with today's date; the material itself is the source.

Pass types and their scopes:
- `research-knowledge-{n}.md` — vault and sources; use the general-purpose subagent (Sonnet)
- `research-web-{n}.md` — external sources; use the general-purpose subagent with WebSearch
- `research-codebase-{n}.md` — project code and config; use the general-purpose subagent (Sonnet)
- `research-provided-{n}.md` — user-supplied material; write verbatim or lightly structured to disk before proceeding

**Do not use the Explore subagent for any pass.** Explore is read-only — it has no Write tool — so it cannot write its own pass file, which the protocol above requires. Each pass file must be written by the subagent that produced it, using a subagent with Write access; main context never reads raw pass output, so routing it through the orchestrator to write on Explore's behalf would violate that rule too.

Run passes **sequentially, one at a time**. Do not run distillation until **all** pass files exist on disk. Certainty of completion takes priority over speed — a stalled or half-written pass file leaves the campaign in an unrecoverable state.

**Chained passes.** A later pass may read an earlier pass file when it needs that pass's output as input (e.g. a coverage pass rating the item list an inventory pass produced). Sequential execution makes this safe. Brief it explicitly: name the earlier file path and the section or table it may use. Unnamed files and sections stay off limits. Main context still never reads either file.

**Knowledge-pass write exception.** A knowledge pass reads `knowledge/` but writes its pass file to `control-plane/workstreams/{name}/_working/` — a deliberate break from one-subtree scoping. Brief it as: read-only in `knowledge/` (no writes there), exactly one write path (its pass file). Nothing else outside `knowledge/` is read or written.

### Distillation — Fresh Subagent, Clean Context

After all pass files are written, distillation defaults to a **separate subagent** (Sonnet), for the fresh-context guarantee described above. This subagent must:
- Be given only the paths to `_working/research-*.md` files — nothing else
- Read those files and produce `research.md` using the template below
- Have no reference to the conversation, the original request, or the pass subagent outputs

**Main-context fallback.** Under the same conditions as the per-pass fallback above, distillation can run in main context instead — deliberately re-reading only the `_working/research-*.md` files (not the conversation or the original request) to approximate the fresh-context discipline a real subagent enforces automatically. State explicitly that this ran in main context so a later reader knows the guarantee was approximated, not native.

Brief the distillation subagent with this structure:
> "You are distilling research pass files into a self-contained research document. Read only the files at these paths: [list]. Write `research.md` at [path] using the template provided. Do not summarize what was asked or how you got here — synthesize only what is in those files, organized for downstream use in Design and Blueprint steps. Carry forward every source from the pass files: cite vault paths and URLs inline where the finding appears, and consolidate all sources in a `## Sources` section at the end of `research.md`. Omit any finding not backed by a source in the pass files."

The distillation subagent returns ≤300 words to main context confirming the file was written and flagging any open questions it couldn't resolve.

### After Distillation

Main context reads `research.md` only. It does not read `_working/` files. If `research.md` is insufficient to proceed to Design, run an additional targeted pass rather than re-reading raw `_working/` files.

### Write Queue Signal

Immediately after `research.md` is accepted, write a queue signal to `knowledge/distillers/queue/{campaign}-{YYYYMMDD}.md`. This notifies the knowledge pipeline that research-phase material is available for vault candidacy review.

```yaml
signal: research-complete
workstream: {kebab-case-workstream-name}
research_path: control-plane/workstreams/{name}/_working/
target_vault_subtrees: []
queued_at: {YYYY-MM-DD}
status: pending
```

Leave `target_vault_subtrees` empty — the Scout role will classify during queue processing. The queue file status transitions from `pending → processing → done` per `knowledge/distillers/queue/README.md`.

---

## Advance Phase

After `research.md` is complete and read by main context:

- → **design** if research surfaced architectural decisions or structural choices to make
- → **blueprint** if research is sufficient to blueprint directly

Update `index.md`: set `workstream_phase`, update the Payload Relay artifact status table, update `Last Active`.

---

## Template: `research.md`

```markdown
---
note_type: workstream-research
workstream: {name}
tags: [workstream/{name}]
---
# {Campaign Title} — Research

Distilled from {n} knowledge pass(es), {n} web pass(es), {n} codebase pass(es). Self-contained — downstream steps do not read `_working/` files.

## Key Findings

### Knowledge

{Distilled vault/sources knowledge relevant to this campaign — gaps noted explicitly}

### Web

{Distilled external knowledge — standards, competitor info, technical refs}
← omit section if no web passes were run

### Codebase

{Distilled codebase knowledge — existing patterns, dependencies, constraints}
← omit section if no codebase passes were run

### Provided Source Material

{Structured summary of user-supplied material}
← omit section if no user-provided material

## Decisions Implied by Research

{Decisions the research surfaces that must be made in Design or Blueprint — be specific}

## Open Questions

{What research couldn't resolve — flags for Design or Questions follow-up}

## Sources

{Consolidated list of all sources cited across pass files. Format per type:}
- `knowledge/vault/path/to/file.md` — what was taken from it
- https://example.com/article — what was taken from it
- User-provided, YYYY-MM-DD — description of the material
```

---

## Enforcement Checks

Before declaring research complete, verify:
- [ ] `_working/` directory exists and contains one file per pass run
- [ ] Each `_working/` file has proper frontmatter
- [ ] Each `_working/` file ends with a `## Sources` section — no unsourced findings
- [ ] `research.md` exists and was written by a distillation subagent reading only `_working/` files
- [ ] `research.md` has a `## Sources` section carrying forward all pass sources
- [ ] No finding in `research.md` is derived solely from model weights — every claim traces to a vault path, URL, codebase path, or user-provided material
- [ ] Main context has not consumed raw pass output — only the `research.md` distillation
- [ ] `index.md` Payload Relay artifact status table updated to reflect completed steps
