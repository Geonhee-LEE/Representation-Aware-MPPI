# The strand was red for two reasons, not one

- **Cycle**: 2026-08-18 08:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: (none picked — strand repair, per D-112 REVIEW step 0)
- **Phase**: P3
- **Status**: in_progress

## What I tried

- REVIEW step 0 returned `rc=1` naming **three** stranded cycles (05:00, 06:00,
  07:00) and said all three trees were ungraded. `probe` said the receipt on
  disk grades `82d1220`, not `HEAD` — so the strand needed a suite, not a push.
- 07:00 had left the diagnosis in Q-165: the tree is red at 3604/3609, and all
  five failures were attributed to `OBSERVABLES` entering the `TYPED`
  population. That attribution had flipped Q-165's lean from (a) to (b)/(c),
  i.e. toward deleting the membership test D-338 had just written.
- Before acting on the flip I ran **the five failing node IDs alone**: 24.8 s
  against the full suite's 866.98 s. 07:00 had tried the five *files* and blown
  a 600 s timeout; the node IDs are 1/35 of a suite and answer the same question.
- Read the five assertions, found the attribution was wrong, and paid (a)'s
  actual bill: two pin bumps + the ninth `exemption_control` tamper.

## What worked / what failed

- ✅ **The five failures have two causes, split 3/2 — not one cause.**
  `magnitude_census`'s two (`printing` 21 → 22) were moved by **D-338's own
  `decisions.md` entry**, whose prose prints suite counts and the guard tally.
  They would have moved if D-338 had written no code at all. The mover is the
  REPORT-phase doc write D-043 *mandates*.
- ✅ **One of the remaining three is a result, not a cost.**
  `scalar_readings` 15 → 16's entrant is `constant_at_every_index` itself, which
  D-336 put in the pool days ago. It did not join; it became **visible**. That
  visibility is exactly what D-338 set out to buy.
- ✅ **So the real bill for (a) was 2 pins + 1 control**, and the ninth control
  (`_observables`) reads `BITES`: dropping `obstacle_speed` from the registry
  takes `obstacle_side_observables()` from two names to one.
- ✅ Verified in-process rather than by re-running files: `unwatched <=
  controlled` True with 9 entries, `scalar` 16, route sum 23, census 22/16.
  `census_preempt` clean on all four re-derived censuses.
- ⚠️ **`OBSERVABLES` is the first entry on `unwatched_exemptions` that no cycle
  declared.** It has been a module-level tuple since D-334; D-338 changed only
  the *path* by which it is read. Nothing in that diff looks like declaring an
  allow-list, and the population grew anyway.
- ❌ **A docstring edit went in as code first** — I replaced two lines and left
  the original `"""` above my new prose, producing a syntax error. Caught by an
  `ast.parse` one command later, but only because I ran one.
- ❌ **Q-165's flip rested on an over-attribution I could have caught in 25 s.**
  It cost a cycle's worth of lean-writing and nearly cost the deletion of a
  working guard.

## North-star delta

- **No movement toward the north star.** This is verification-infrastructure
  repair on a branch whose *last* north-star reading (D-334) was negative:
  `cut_in` has no plan-time separator that is not a scenario constant.
- What it does buy is that the branch's four cycles of work become pushable —
  five commits have been stranded since `a77c705`.

## Key learnings

- **Run the failing node IDs, not the failing files.** 24.8 s vs a 600 s timeout
  vs an 867 s suite. 07:00 concluded "targeted pytest failed on time, not on
  content" and fell back to reasoning; the narrower selection was available and
  would have overturned its conclusion.
- **A red suite's failures are not one story by default.** Q-165 bundled five
  into one cause because they arrived together. Two of them were the loop's own
  mandated doc write — a mover present in *every* cycle, which is precisely why
  it is easy to attribute to whatever else changed.
- **"The count moved" and "the cost was paid" are different claims.** A pin that
  moves because something hidden became visible is reporting a repair, not a
  regression, and D-330's delete-the-membership-test rule cannot tell the two
  apart. That gap is now Q-166.

## Recommended next 1–3 priorities

1. **Q-166**: classify the 9 `unwatched_exemptions` entries as domain-declaration
   vs real allow-list, using "does any caller supply the argument from outside
   the registry". Doc-only — no suite needed.
2. Return to the north star: D-334 left `cut_in` with no non-constant separator.
   The open question is whether any *other* scene pair is separable at plan time.
3. Fold "run failing node IDs before reasoning about a red suite" into the
   EXECUTE-phase guidance beside `cycle_wallclock elapsed`.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/exemption_control.py, eval/mppi_sandbox/tests/test_exemption_control.py, eval/mppi_sandbox/tests/test_exemption_masking.py, eval/mppi_sandbox/tests/test_guard_direction.py, eval/mppi_sandbox/tests/test_magnitude_census.py, docs/decisions.md, docs/deliberations.md
- TSV row appended: pending
