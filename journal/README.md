# Cycle Journal — Representation-Aware-MPPI

This directory holds **one markdown file per auto-research cycle**, written by the hourly executor (Phase 4 of `scripts/prompts/auto_research.md`). The repo-root `JOURNAL.md` is a digest pointing back here; this directory is the full record.

## File naming

```
journal/YYYY-MM/DD-HH-<branch-slug>.md
```

- `YYYY-MM` — KST month subdir, created by the executor with `mkdir -p`.
- `DD-HH` — day + 2-digit hour (24h KST). Two cycles in the same hour are extremely rare given the 1/h cadence + safety gates; if one ever happens, append `-2` to the slug.
- `<branch-slug>` — same slug as the autoresearch branch (`<phase>-<title-kebab-≤40>`).

Example: `journal/2026-05/06-10-p0-state-md-bootstrap.md`.

## Required sections (canonical template)

```markdown
# <Cycle title — short and specific>

- **Cycle**: 2026-MM-DD HH:MM KST
- **Branch**: `autoresearch/<phase>-<slug>`
- **TODO**: `<short-id>` <title>
- **Phase**: P<N>
- **Status**: keep | discard | crash | in_progress

## What I tried
<2–4 bullets describing the actual change attempted>

## What worked / what failed
<honest 2–4 bullets — concrete observations, not just "it built">

## North-star delta
<1–3 bullets quantifying movement toward "perfect MPPI in all envs".
 Be honest about zero-impact runs.>

## Key learnings
<2–4 bullets — what would change my mind about future TODOs given this
 cycle. If nothing was learned (mechanical task), say so explicitly.>

## Recommended next 1–3 priorities
<concrete actions or TODO titles. These feed into PLAN_NEXT.>

## Artifacts
- PR: pending merge (autoresearch/<phase>-<slug>)
- Files touched: <comma list>
- TSV row appended: yes | no
```

Total length: < 80 lines. Skim-readable; not a novella.

## Append-only spirit

- Never edit a past entry except to fix typos. The next cycle reads them as historical signal — re-writing history corrupts the loop.
- If a cycle's conclusion turned out wrong, write a NEW entry that says so. Don't retcon.
- The `Status` field reflects the **state at write time**, not later validation by a human merging the PR. PR-merge state lives in GitHub, not here.

## Rotation / archival

- Each monthly subdir caps at ~30 entries (1/h × 24/day, but most cycles skip — practical observed rate is ~3–8 cycles/day).
- When a month closes out, no automatic action — the directory simply stops growing. Archival to a single rolled-up `journal/archive/<year>-W<week>.md` is **future work**.
- The repo-root `JOURNAL.md` digest caps at 20 entries; older digests roll off but the per-cycle files here remain canonical.

## How the loop reads this

Each cycle's REVIEW phase (`scripts/prompts/auto_research.md` Phase 1) reads:
- `JOURNAL.md` top 5 entries (paragraph each — fast scan).
- `STATE.md` (root) — single-page snapshot rewritten by the previous cycle.

It does **not** routinely follow links into individual files in this directory unless the bottleneck explicitly references one. So write the digest line in `JOURNAL.md` carefully — that's what the next agent actually sees.
