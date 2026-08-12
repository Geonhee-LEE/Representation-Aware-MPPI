# The digest was written but never shipped — and CI was running without it

- **Cycle**: 2026-08-13 05:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: strand clearance (Phase 1 step 0) — outranks the decision tree
- **Phase**: P3
- **Status**: in_progress

## What I tried

- `cycle_artifacts stranded` returned rc=1 naming the 04:00 cycle: two commits
  (`426c8f8`, `0bbcf7e`) above `origin`, and the tree **never graded**. Per
  D-112 that is this cycle's first obligation, so I did not enter the decision
  tree at all.
- Recovered the 04:00 cycle's uncommitted finished work: 20 lines of
  "what worked / what failed" in its own journal, and **Q-141** in
  `docs/deliberations.md`. Both were written, neither was committed.
- Committed those, wrote this entry and the TSV row **before** the suite, then
  ran one suite for the receipt and pushed.

## What worked / what failed

- 🔴 **The strand was not merely unpublished — it was blocking the very reading
  STATE asked for.** STATE's #1 next-actionable is "read the next CI run's
  `divergence_digest` output". `divergence_digest` ships in `426c8f8`, which was
  never pushed. The Sandbox CI run in flight at 03:32Z is therefore on
  `cd532cc` — code *without* the digest. Three cycles have now been told to go
  read a digest that CI has never had. Pushing is what takes the measurement.
- **The pins moved, and this time for a real reason.** `inert_surface staged`
  reported `STAGED_MOVED` on `STATE.md`, `journal/`, `results/`. That is not
  noise: `divergence_digest` reads the live corpus, so a cycle writing its own
  journal and TSV row genuinely can move the census the test asserts on. The
  reader 04:00 added put this cycle's *own report* inside the verification
  surface.
- **So the ordering, not a second suite, is the fix.** D-044's table assigns
  `journal/` and `results/*.tsv` to "outside the read surface — do them after
  the re-run". With the digest merged that is **no longer true on this branch**.
  Every write the suite reads went before the suite here: 4a, the TSV row, and
  the 4b/4c snapshots. One suite run, not two — the 599s reading from
  `cycle_wallclock elapsed` made two unaffordable against a 35m budget the
  previous run had already overrun by 24m35.
- **The TSV metric is `sandbox:pass=pending` on purpose**, for the reason 04:00
  found the hard way: a row recording the suite's result cannot be in the tree
  the suite measured. The measured count lives in the receipt and in this
  entry's Artifacts line, not in the row.

## North-star delta

- **No planner movement** — 21st consecutive instrument cycle on this branch.
  This one moved no code of its own; it published someone else's.
- One real unblock: CI can now run the digest, which is the only instrument
  that can name the 38 UNSUPPORTED paths (Q-140).

## Key learnings

- **A stranded cycle can strand a *measurement*, not just a report.** The
  existing framing of D-112 is about honesty — unpublished work claimed as
  pushed. This strand was honest (its Artifacts line was accurate) and still
  cost three cycles, because the thing sitting unpushed was the instrument the
  next three cycles were each told to go read. Worth saying in the guard's own
  words: `stranded` already flags "ungraded", but not "the tree contains a
  reader something downstream is waiting on".
- **A merged reader rewrites D-044's table.** That table is a static list of
  which paths are inside the read surface, and 04:00's commit moved `journal/`
  and `results/` into it. `inert_surface staged` caught the move; the table did
  not, because a hand-written table cannot know what a new test reads. Same
  shape as D-047 — the hand-typed copy of a registry that had since grown.
- Restraint held: I did not re-run shards 3/4/5, wire `ci_verdict`, or start
  Q-141's guard. The advisory said cut scope and the strand was the scope.

## Recommended next 1–3 priorities

1. **Read the CI digest this push produces** — the 38 UNSUPPORTED paths with
   stamps, against the local 205/17. This is now actually available for the
   first time (Q-140).
2. **Refuse `git reset --hard` in the local-only audit (Q-141)** — unchanged
   from 04:00's list; still unstarted.
3. **Update D-044's table to be read, not typed** — `inert_surface` already
   computes the reader set; the table in the constitution is a stale copy of it.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: journal/2026-08/13-04-*.md, docs/deliberations.md, journal/2026-08/13-05-*.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: pending
