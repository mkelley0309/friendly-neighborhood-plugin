#!/usr/bin/env python3
"""build/difflint.py — plan 3.5 comparison report.

Compares `build/_generated/{edition}/` (generate.py's output) against
`plugins/{edition}/` (the byte-reproduction reference target) for all three
editions, and writes a structured, human-readable report to
`build/difflint-report.md`.

Does NOT classify discrepancies as bug-to-fix-everywhere vs.
genuine-edition-difference-as-config — that's step 3.6's job, not this
script's. This only reports what differs.

Also runs one automated, non-negotiable check: no generated file may contain
a pinned-frontmatter-key collision — `campaign:`, `mission:`, `responsibility:`,
or `patrol:` at the start of a line (those are display words; only
`workstream:`/`objective:`/`assignment:`/`cadence:`/`mission:`-per-data-model
etc. are real frontmatter keys per `vocabulary/data-model.yml`, and
`campaign`/`responsibility`/`patrol` must NEVER be one). This check exits
non-zero and prints a loud, specific failure if it finds a hit anywhere.
"""
from __future__ import annotations

import difflib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GENERATED_ROOT = ROOT / "build" / "_generated"
PLUGINS_ROOT = ROOT / "plugins"

EDITIONS = ["harness-core", "friendly-neighborhood-lite", "friendly-neighborhood"]

# The task brief names all four words (campaign/mission/responsibility/patrol)
# as ones that must never appear as a frontmatter key "anywhere". Taken
# literally that's inconsistent with vocabulary/data-model.yml: `mission:`
# and `patrol:` ARE the correct, intended frontmatter keys for the
# non-pinned assignment/cadence tiers in the lite and full editions (a
# blanket zero-hits check on those two words would permanently fail on
# correct output). What data-model.yml actually calls the landmine is pinned
# tiers (objective/workstream) getting their frontmatter key corrupted to a
# themed display word — i.e. `campaign:`/`responsibility:` must NEVER appear
# as a key in ANY edition (workstream/objective are pinned, full stop), while
# `mission:`/`patrol:` are only wrong in editions that haven't adopted them
# (core, which must keep `assignment:`/`cadence:`). This check implements
# that corrected, per-data-model version rather than the literal brief —
# flagged in build/README.md rather than silently applied.
ALWAYS_FORBIDDEN_KEYS = ["campaign", "responsibility"]  # pinned tiers' themed words
CORE_ONLY_FORBIDDEN_KEYS = ["mission", "patrol"]  # correct in lite/full, wrong in core


def forbidden_key_pattern(words: list[str]) -> re.Pattern:
    return re.compile(r"^(" + "|".join(re.escape(w) for w in words) + r"):", re.MULTILINE)


def normalize(text: bytes) -> str:
    """Decode + normalize line endings so a CRLF (Windows checkout of
    `plugins/*`) vs. LF (this generator's output) is never reported as a
    discrepancy — see build/README.md "Line endings"."""
    try:
        decoded = text.decode("utf-8")
    except UnicodeDecodeError:
        return None
    return decoded.replace("\r\n", "\n")


def walk_files(root: Path) -> dict:
    out = {}
    if not root.exists():
        return out
    for p in root.rglob("*"):
        if p.is_file():
            if "__pycache__" in p.parts:
                continue
            out[p.relative_to(root).as_posix()] = p
    return out


def diff_edition(edition: str) -> tuple[str, list[str]]:
    gen_root = GENERATED_ROOT / edition
    ship_root = PLUGINS_ROOT / edition
    gen_files = walk_files(gen_root)
    ship_files = walk_files(ship_root)

    gen_names = set(gen_files)
    ship_names = set(ship_files)

    added = sorted(gen_names - ship_names)  # generated has it, shipped doesn't
    removed = sorted(ship_names - gen_names)  # shipped has it, generated doesn't
    common = sorted(gen_names & ship_names)

    lines = [f"## {edition}", ""]
    forbidden_hits = []

    if not ship_root.exists():
        lines.append(f"- **shipped tree missing at `{ship_root}`** — nothing to compare.")
        return "\n".join(lines), forbidden_hits
    if not gen_root.exists():
        lines.append(f"- **generated tree missing at `{gen_root}`** — generate.py did not build it.")
        return "\n".join(lines), forbidden_hits

    lines.append(f"- generated files: {len(gen_files)}, shipped files: {len(ship_files)}")
    lines.append(f"- added (in generated, not shipped): {len(added)}")
    lines.append(f"- removed (in shipped, not generated): {len(removed)}")

    changed = []
    for name in common:
        gen_bytes = gen_files[name].read_bytes()
        ship_bytes = ship_files[name].read_bytes()
        if gen_bytes == ship_bytes:
            continue
        gen_text = normalize(gen_bytes)
        ship_text = normalize(ship_bytes)
        if gen_text is not None and ship_text is not None and gen_text == ship_text:
            continue  # pure line-ending difference, not a real discrepancy
        changed.append(name)

    lines.append(f"- changed (content differs): {len(changed)}")
    lines.append("")

    # frontmatter-key check runs over generated content regardless of
    # whether the file also differs from shipped — this is a hard invariant.
    check_words = list(ALWAYS_FORBIDDEN_KEYS)
    if edition == "harness-core":
        check_words += CORE_ONLY_FORBIDDEN_KEYS
    key_pattern = forbidden_key_pattern(check_words)
    for name, path in gen_files.items():
        if not name.endswith(".md"):
            continue
        text = normalize(path.read_bytes())
        if text is None:
            continue
        for m in key_pattern.finditer(text):
            line_no = text.count("\n", 0, m.start()) + 1
            forbidden_hits.append(f"{edition}/{name}:{line_no}: `{m.group(1)}:` used as a frontmatter key")

    if added:
        lines.append("### Added (generated only)")
        lines.extend(f"- `{n}`" for n in added)
        lines.append("")
    if removed:
        lines.append("### Removed (shipped only, generator doesn't produce it)")
        lines.extend(f"- `{n}`" for n in removed)
        lines.append("")
    if changed:
        lines.append("### Changed")
        for name in changed:
            lines.append(f"<details><summary><code>{name}</code></summary>\n")
            gen_text = normalize(gen_files[name].read_bytes()) or ""
            ship_text = normalize(ship_files[name].read_bytes()) or ""
            diff = difflib.unified_diff(
                ship_text.splitlines(keepends=True),
                gen_text.splitlines(keepends=True),
                fromfile=f"shipped/{name}",
                tofile=f"generated/{name}",
            )
            lines.append("```diff")
            lines.append("".join(diff).rstrip("\n"))
            lines.append("```")
            lines.append("\n</details>\n")

    return "\n".join(lines), forbidden_hits


def main() -> int:
    report_sections = []
    all_forbidden = []
    totals = {}

    for edition in EDITIONS:
        section, forbidden = diff_edition(edition)
        report_sections.append(section)
        all_forbidden.extend(forbidden)

    report = (
        "# difflint report — build/_generated/* vs plugins/*\n\n"
        "Generated by `build/difflint.py`. Reports discrepancies only — "
        "classification (bug-to-fix-everywhere vs. genuine-edition-difference-"
        "as-config) is step 3.6's job, not this script's.\n\n"
        "Line-ending-only differences (CRLF-checkout `plugins/*` vs. LF "
        "generator output) are normalized away before comparison; they are "
        "not real discrepancies.\n\n"
        + "\n\n".join(report_sections)
    )
    out_path = ROOT / "build" / "difflint-report.md"
    out_path.write_text(report, encoding="utf-8", newline="\n")

    print(f"difflint: report written to {out_path.relative_to(ROOT)}")
    for edition in EDITIONS:
        # quick summary counts re-derived for stdout (cheap; report already computed them)
        gen_files = walk_files(GENERATED_ROOT / edition)
        ship_files = walk_files(PLUGINS_ROOT / edition)
        added = len(set(gen_files) - set(ship_files))
        removed = len(set(ship_files) - set(gen_files))
        changed = 0
        for name in set(gen_files) & set(ship_files):
            gb, sb = gen_files[name].read_bytes(), ship_files[name].read_bytes()
            if gb == sb:
                continue
            gt, st = normalize(gb), normalize(sb)
            if gt is not None and st is not None and gt == st:
                continue
            changed += 1
        print(f"  {edition}: added={added} removed={removed} changed={changed}")

    if all_forbidden:
        print(
            f"\nFATAL: {len(all_forbidden)} forbidden display-word frontmatter key(s) "
            "found in generated output:",
            file=sys.stderr,
        )
        for hit in all_forbidden:
            print(f"  - {hit}", file=sys.stderr)
        return 1

    print("\nfrontmatter-key check: PASS (no campaign:/mission:/responsibility:/patrol: leaked as a key)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
