# The guard's first enforcing consumer — and it refused everything

- **Cycle**: 2026-08-08 22:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #2 — point a sweep driver at `resolve()` (available → enforced)
- **Phase**: P5
- **Status**: keep

## What I tried

- Gave `lam_window_index.resolve` its first **non-test** consumer:
  `comparison_headroom.certify(row)` resolves *both* arms of a `Headroom` at
  the row's own `weight` and grades its recorded `lam` against the two windows.
- Added the enforcing half — `assert_certified` raising
  `UncertifiedOperatingPoint` — so a driver can no longer take λ as a free
  argument. D-143 supplied the window; nothing consumed it.
- Added exactly **two** verdict names (`CERTIFIED`, `OFF_WINDOW`). The index's
  own refusals (`NO_TABLE_AT_WEIGHT`, `NO_CELL`, `EMPTY_WINDOW`) pass through
  verbatim rather than being restated under new names (D-047).
- Certified the two mechanism claims the project has actually published.

## What worked / what failed

- 🔴 **The guard's first real consumer refused every row, and the cause was a
  filename suffix.** `Headroom.scenario` records `cafe_head_on_v0`; the tables
  key on `cafe_head_on_v0.yaml`; `lookup` matched on basename. Every
  certification came back `NO_CELL` — a refusal that is *indistinguishable at
  the call site* from an uncalibrated cell, and which fails in the **vacuous**
  direction: a guard that refuses everything reads as maximal strictness and
  checks nothing. Fixed by matching on the stem, symmetrically on both sides.
  D-143's lesson recurs one level up — the basename rule was correct for
  thirty cycles because every caller was a test holding a table-shaped key.
- 🔴 **D-124's gap-gate A/B grades `NO_CELL`, sole arm `gap_gated_mppi`.** That
  controller appears in **no** calibration table at any weight, so the λ it was
  published at was never measured admissible for it. This is a *second,
  independent* reason that claim is unscored — `sub_margin` already said its
  delta sits below the margin; this says its temperature is unmeasured.
- 🔴 **The risk channel's separating rung is `NO_TABLE_AT_WEIGHT`.** The
  project's first genuinely scorable mechanism result (`w = 100`, 1.0000 →
  0.2500 unsafe) sits at a weight with no table. STATE's "re-key `w = 100`"
  item is now a *failing test* rather than a paragraph.
- 🟢 **It accepts, too.** head_on at `w = 10`, λ = 0.8 — D-132's operating
  point — grades `CERTIFIED` on both arms. Both directions pinned, so this is
  not `guard_vacuity`'s complaint with the sign flipped.
- 🟢 **The refusal names its arm.** D-133's `crossing` rung at λ = 3.2 grades
  `OFF_WINDOW` with `sole_uncertified = stock_mppi`: the *baseline* was out of
  band while the mechanism was in it. A single boolean would have printed that
  identically to the both-arms case (the `scorable_band.sole_refuser` argument,
  one axis over).
- 🟡 Zero new closed-loop runs — deliberate, per the 33m51 wall-clock reading
  on the preceding cycle. Pure code + tests.

## North-star delta

- No new safety/tracking numbers. The headline stands where D-136 left it.
- What moved: the calibration is **enforceable** for the first time. Every
  prior cycle could publish a delta at any (weight, λ) and no code path could
  object; `assert_certified` is that path.
- Honest accounting of the cost: of the project's two published mechanism
  claims, **neither certifies** — one for a never-calibrated arm, one for a
  never-measured weight. That is a finding about the claims, not about the
  guard.

## Key learnings

- **A guard's first non-test consumer is its first real test.** D-143 said
  this about the *file choice*; the same sentence held one level down for the
  *key format*, and the bug was invisible for thirty cycles because every
  caller was a test that already spoke the table's dialect.
- **Vacuity has two directions and only one is watched.** The repo has
  `guard_vacuity` for guards that accept everything. This one accepted nothing,
  which looks like rigour on every dashboard.
- **Refusals should be ranked by what they cost to clear.** `NO_CELL` needs a
  calibration run, `OFF_WINDOW` needs a different λ — so when the arms disagree
  in kind, the verdict names the larger missing thing.

## Recommended next 1–3 priorities

1. **Re-key `w = 100`** — now has a named failing consumer
   (`test_the_risk_channels_separating_rung_sits_at_an_uncalibrated_weight`),
   which is the strongest form the item has had. ~1024 runs, ~16 min.
2. **Calibrate `gap_gated_mppi`** — it is an arm the project published a claim
   for and never calibrated; one column, and it clears a `NO_CELL`.
3. **Point the ladder walks at `assert_certified`** — `certify` now exists;
   `scorable_band` and the sweep drivers still do not call it.

## Artifacts

- PR: #67 (open, continued per D-140)
- Files touched: `eval/mppi_sandbox/comparison_headroom.py`,
  `eval/mppi_sandbox/lam_window_key.py`,
  `eval/mppi_sandbox/tests/test_operating_point_certification.py`
- TSV row appended: yes
