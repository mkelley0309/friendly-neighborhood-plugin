# distillers/staging/

Candidate vault notes awaiting Peer Review. Written by Harvester. Each candidate is evaluated by the Peer Reviewer before admission to `vault/`.

---

## Candidate Format

One file per candidate note: `staging/{slug}.md`

Candidates must carry full distiller frontmatter contract fields:

```yaml
---
note_type: vault-note
source_path: <relative path under sources/>
source_url: <original URL>
synced_at: <ISO date>
distilled_at: <ISO date>
tags: [vendor/<slug>, ...]
confidence: medium   # Harvester default; distillers use high
---
```

Body: the candidate vault note content, written as if it were already in the vault.

---

## Review Annotation Format

Peer Reviewer writes `{slug}-review.md` alongside each candidate:

```yaml
---
note_type: peer-review
candidate: staging/{slug}.md
decision: ADMIT | REJECT | MERGE
reviewed_at: <ISO datetime>
---
```

Body: rationale for the decision.

- **ADMIT** — note is ready; include the target vault path (`vault/{subtree}/{slug}.md`). The orchestrating agent performs the move.
- **REJECT** — reason + what must change before re-submission. Candidate stays in staging until reworked or dropped.
- **MERGE** — target note path in vault + merge instruction. Candidate stays in staging until merged or declined.

---

## Lifecycle

1. Harvester writes `staging/{slug}.md`
2. Peer Reviewer writes `staging/{slug}-review.md` with decision
3. On ADMIT: orchestrating agent moves `{slug}.md` to vault; both staging files deleted
4. On REJECT: operator chooses. Rework: edit the candidate and re-run Peer Review. Drop: move both files to `staging/_archive/`
5. On MERGE: operator applies the merge, then both files are deleted. If declined, move both files to `staging/_archive/`

---

## Stale Policy

Items unresolved for more than 14 days are surfaced by Scout as stale, with their state and next action. Scout does not move or delete them — it reports them for user action.

`_archive/` holds dropped or declined candidates with their reviews. It is never deleted, and Scout does not read it.
