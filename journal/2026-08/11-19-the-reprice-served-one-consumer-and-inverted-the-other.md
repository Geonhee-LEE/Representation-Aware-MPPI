# The re-price served one consumer and inverted the other

- **Cycle**: 2026-08-11 19:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `STATE-1` Audit `MIN_OVERHEAD_SECONDS` for D-200's "documented as stale, kept anyway" shape
- **Phase**: P3
- **Status**: keep

## What I tried

- Took STATE #1's hypothesis — that `MIN_OVERHEAD_SECONDS` has the same shape
  D-200 found in `SUITE_SECONDS` — and measured before writing the argument
  (D-186). STATE also mis-attributed the constant to `push_preflight`; it lives
  in `cycle_wallclock`.
- Read both consumers of `SUITE_SECONDS` rather than the constant alone, which
  is what turned the cycle: `suite_deadline()` and `threshold()` want opposite
  extremes of the same registry.
- Split them — `observed_suite_min()` / `PREMATURE_SUITE_SECONDS` for the
  retrospective axis, `observed_suite_max()` unchanged for the prospective one —
  and re-priced `MIN_OVERHEAD_SECONDS` off a measured counterexample.
- Before attributing three red tests to my change, re-ran them on a stashed tree.

## What worked / what failed

- 🔴 **D-200's re-price silently inverted `grade`'s conservatism.** Its argument
  is stated for the deadline instrument only: an unknown price must fail toward
  *refusing* a suite. `threshold()` reads the same constant to ask whether a run
  could have contained a suite at all, and there the safe direction is the
  floor. At 1223 the bar became 1463 s — above the 18:00 run (1442 s) that
  *demonstrably completed a 1214.24 s suite*. `published` short-circuits ahead
  of the clock, so the live grade was right by luck; any unpublished run of that
  shape grades `PREMATURE`, which is precisely the manufactured finding
  `MIN_OVERHEAD_SECONDS`' own docstring promises this grader will not make.
- 🔴 **The 240 s floor was justified off the wrong population and was false.**
  Its stated basis is a 236 s run that did REVIEW only — a *suite-less* run,
  not a member of the set it bounds (non-suite work of a run that ran a suite).
  Measured directly: 1442 − 1214.24 = **228 s**. The bound sat 12 s above an
  observation, erring in the direction it promised not to.
- 🔴 **An inherited red, and I checked rather than assumed (D-198).** Two
  `TestElapsed` cases compared `elapsed_reading` (receipt-priced) against
  `suite_deadline()` (constant-priced). Equal only while the last suite happened
  to cost `SUITE_SECONDS` — so when the 18:00 cycle wrote a 1214.24 s receipt
  against the 1223 s fallback, they went red with nothing in the module
  changing. A stashed-tree run confirmed 2 of 3 were red before I touched
  anything; the third (`== 637`) was mine, a typed literal under a comment
  claiming it was derived.
- 🟢 Targeted pre-check caught all four in **0.27 s** (D-191 pattern), not in a
  20-minute suite. 113 passed.

## North-star delta

- No movement. Zero sim runs, no controller / representation / dynamics code
  touched; coverage still 0/6. `unsafe_rate` 0.0000 · `min_clearance` 0.3579 ·
  `success_rate` 1.0000 all carried unchanged.
- This is instrument repair: the wall-clock advisory that every cycle reads at
  Phase 1 and Phase 3 was one cycle away from telling cycles they had not run a
  suite they had run.

## Key learnings

- **A re-price is scoped to the consumer whose argument you wrote.** D-200's
  reasoning was sound and its ceiling is still right for the deadline; the
  defect is that a shared constant absorbed a directional decision made for one
  of its two readers. The general form: before re-pricing a constant, enumerate
  its consumers and ask each one which way it fails.
- **Gate 1 did not have to fire, and STATE said it did.** D-140 (accepted,
  2026-08-08) rules that gate 1 counts *new* queue items, so continuing on an
  already-open PR passes it. STATE has carried "every subsequent cycle skips"
  for three cycles against an accepted decision that says otherwise — a stale
  premise in the file PLAN reads first.
- **A test that reads `/tmp` has a verdict that is a function of `/tmp`.** The
  coupling was invisible while the receipt agreed with the fallback and became a
  red the moment a suite got faster.

## Recommended next 1–3 priorities

- Sweep the remaining consumers of `nested_timeout.OBSERVED_SUITE_SECONDS` for
  the same one-constant-two-directions shape — it is the sibling registry and
  D-200 borrowed its argument wholesale.
- Grow `OBSERVED_OVERHEAD_SECONDS` past n=1: one observation makes a floor that
  the next faster cycle falsifies again. The wrapper log plus receipts can
  reconstruct it retrospectively for every run that published.
- Correct STATE's gate-1 premise against D-140 so PLAN stops skipping cycles it
  is entitled to run.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: `eval/mppi_sandbox/cycle_wallclock.py`, `eval/mppi_sandbox/tests/test_cycle_wallclock.py`, `docs/decisions.md`, `journal/2026-08/11-19-*.md`
- TSV row appended: pending
