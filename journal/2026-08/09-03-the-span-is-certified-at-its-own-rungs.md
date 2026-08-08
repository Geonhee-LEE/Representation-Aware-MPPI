# The span is certified at its own rungs — and the unmeasured case is not a refusal

- **Cycle**: 2026-08-09 03:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE next-claude-actionable #1 — point the sweep drivers at `assert_certified`
- **Phase**: P3
- **Status**: keep

## What I tried

- Gave `ScorableBand` the enforcing consumer it never had. D-144 built
  `certify`/`assert_certified` for one `Headroom`; a *band* still walks the
  weight axis at a fixed λ and takes that λ as a free argument, so a `span`
  could be published over rungs nobody certified.
- Shipped `certify_span` / `assert_span_certified` / `SpanCertification` in
  `scorable_band.py`, scoped to `band.scorable` — the rungs whose verdicts set
  the span, not the ones that merely witness an edge.
- Split the refusals by **whether a measurement exists that disagrees**, not by
  whether a measurement exists: `SPAN_UNMEASURED` (`NO_TABLE_AT_WEIGHT`,
  `NO_CELL`) reports; `SPAN_REFUSING` (`OFF_WINDOW`, `EMPTY_WINDOW`) raises.
- Zero closed-loop runs — a deliberate scope cut off the 80m50 wall-clock
  reading on the 01:00 cycle, which held the lock through a 02:00 that never ran.

## What worked / what failed

- 🟢 **The guard enforces without refusing everything.** Only three weights
  (10 / 75 / 100) carry a table, so a per-rung "must be calibrated" rule would
  have refused essentially every band — D-144's accept-nothing vacuity with the
  sign flipped, which reads as maximal strictness and checks nothing. The
  existence/disagreement split is what makes enforcement affordable: a ladder
  running past `w = 100` is *unwitnessed*, and only a table that speaks and says
  no is a defect.
- 🟢 **Both directions pinned, plus the middle.** `CALIBRATED` at λ = 0.8
  certifies (D-132's operating point); the same band at λ = 3.2 raises (head_on
  records `[0.2, 0.4, 0.8]` at every calibrated weight); `(10, 250)` grades
  `SPAN_UNCALIBRATED` and does *not* raise. Three tests, three outcomes — a
  two-outcome guard could not have told the last two apart.
- 🟢 **The empty denominator is refused rather than passed.** `certify_span`
  raises on a `NO_SCORABLE_RUNG` band instead of certifying it: a band that
  publishes nothing would pass every check vacuously, which is the shape
  D-107 / D-120 / D-127 each booked one axis over.
- 🟢 **The partition states itself once.** `SPAN_REFUSING` is *derived*
  (`UNCERTIFIED - SPAN_UNMEASURED`) and a test asserts the two classes partition
  `UNCERTIFIED` exactly, so a refusal added upstream lands loudly instead of
  being silently absent from both sets — D-047's rule applied before the copy
  had a chance to drift.
- 🟡 **`require_calibration` is off by default and that is a real concession.**
  The strict reading is the one worth wanting; it is unaffordable at 3 calibrated
  weights. The flag exists so a call site that *does* walk calibrated weights
  only can demand it, and so which sites those are is recorded in code rather
  than assumed.
- 🟡 **No driver calls it yet.** This cycle shipped the enforcing entry point;
  wiring an actual sweep driver to it is the next step, and until that lands the
  guard is *available* one level up rather than load-bearing — the exact
  criticism D-143 made of `resolve`, now true of this at the band layer.

## North-star delta

- No new safety/tracking dynamics. The headline is unchanged: `unsafe_rate`
  0.0000 / `min_clearance` 0.3579 / `success_rate` 1.0000 over 5 cells / 40 seeds.
- What moved is that a published `span` can now be refused. The λ guard reached
  the object the project actually publishes bands over, and the refusal it issues
  names a weight to go measure rather than declaring a number untrustworthy.
- Pure guard work — no representation, no controller, no closed-loop evidence.
  Honest reading: this buys defensibility of existing claims, not new capability.

## Key learnings

- **The affordability of a guard is part of its design, not an afterthought.**
  The obvious enforcement rule here (every rung calibrated) is correct and
  useless — it would fire on every honest band. Splitting "unmeasured" from
  "contradicted" is what let the check be strict about the thing it can be
  strict about. A guard nobody can pass gets deleted or muted; a guard that
  names the gap gets bought.
- **Scope the certification to what carries the claim.** Certifying every rung
  would have counted coverage the headline never rests on, and would have let an
  ESS-refused rung at an uncalibrated weight drag down a span it contributes
  nothing to.
- **Deriving the second half of a partition costs one line and removes a whole
  class of drift.** This is the third cycle in a row where the D-047 shape came
  up; it is cheap enough to be the default.

## Recommended next 1–3 priorities

1. **Wire one real sweep driver to `assert_span_certified`** — this cycle built
   the entry point, and by its own D-143 standard an unconsumed guard is untested
   in the way that matters. `require_calibration=True` at a site that walks
   `{10, 75, 100}` only would be the strongest first consumer.
2. **Walk `gap_gated_mppi` at `w = 75`** — gives D-146's new column its first
   weight contrast and widens `COMPARED_ARMS` to three. The scope test in
   `test_lam_window_weight_dependence` is written to fail when this lands. ~512
   runs, ~6 min.
3. **Hand-walk `convoy` at 16 seeds** — still the one cell grading
   `WINDOW_DISJOINT` on *both* weight contrasts. ~128 runs.

## Artifacts

- PR: #67 (open — continued per D-140, no new queue item)
- Files touched: `eval/mppi_sandbox/scorable_band.py`,
  `eval/mppi_sandbox/tests/test_span_certification.py`, `docs/decisions.md`
- TSV row appended: yes
