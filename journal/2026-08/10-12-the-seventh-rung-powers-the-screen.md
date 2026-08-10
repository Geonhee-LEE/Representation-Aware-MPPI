# The 7th rung powers the screen, and the screen refutes the accusation

- **Cycle**: 2026-08-10 12:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — walk one more `w_geom` rung on the convoy 16-seed ladder
- **Phase**: P3
- **Status**: keep

## What I tried

- Walked convoy `w = 75`'s `w_geom` ladder at a **7th rung, `w_geom = 15`** —
  interior to the existing `{10, 20}` spacing so it is an interpolation, not an
  extrapolation. 16 seeds, λ = 0.8, `w_obs_soft = 75`, seeds 0–15, D-170's
  protocol exactly. Reads `(16, 16)` admissible, median ESS 35.95, mean
  clearance 1.1158.
- Bought a **provenance cross-check** in the same process: re-walked the
  already-recorded `w_geom = 20` rung. It reproduced the shipped constants
  **bit for bit to four decimals**, so this rung and the other six come from
  one harness rather than two that agree.
- Wired the rung into the three ladder constants and re-read Q-124's screen.

## What worked / what failed

- 🟢 **The screen is powered and it answers.** 5 admissible against 2 refused
  is 21 labellings → `min_achievable_p = 1/21 = 0.0476`, clearing `ALPHA =
  0.05` by the narrowest margin this population admits. `points_needed` went
  1 → **0**; D-174 priced the rung and the price was correct.
- 🟢 **Verdict: `SELECTION_INDEPENDENT`** (coupling 0.6000, p = 0.4286). Q-124's
  answer is **no** — `ess_band` admissibility does not select `residual_share`.
- 🔴 **The rung bought the right to read the number, not the number.** Coupling
  barely moved (0.6250 → 0.6000) and p *rose* (0.4000 → 0.4286). Everything
  that changed was power. Worth stating plainly because the tempting summary —
  "the extra evidence exonerated the filter" — is false: the point estimate
  always said this, and before the rung it was unreadable.
- 🟢 **The refutation is directional, not a shrug.** Both refused rungs sit
  *inside* the admissible span (0.3302 → 1.0041), and `w_geom = 20` — a null
  reproducing the **entire** mechanism gain at share 1.0041 — is admitted. A
  filter selecting for the representation could not have let that through.
  D-174 could already assert this; it now rides a powered population.
- 🔴 **Band admissibility is not monotone in the coefficient.** `w_geom = 10` is
  `(16, 15)` and refused, while `15` and `20` are both `(16, 16)`. So the band
  is not a threshold in `w_geom` and no rung can be graded from its
  neighbours — which is precisely why the added point had to be *walked*.
- 🟡 **A pin moved that I did not go looking for**: D-171's gain-match
  concordance is computed over rung *pairs*, so 7 rungs adds 6 pairs and the
  value rose 13/15 = 0.8667 → **19/21 = 0.9048**. `CRITERION_CIRCULAR` holds
  and gets *stronger* from a point collected for an unrelated purpose.
- 🟢 D-174's superseded reading is kept as a **derivation** rather than deleted:
  drop the new rung from the screen and the same code returns 6 points, 4
  admissible, 1/15, underpowered, +1. The verdict moved because a measurement
  landed, not because the analysis was re-specified.

## North-star delta

- No movement on the headline safety numbers, and none was available: this
  cycle buys a **licence to read** an existing census, not new controller
  behaviour. `unsafe_rate` 0.0000 / `min_clearance` 0.3579 / `success_rate`
  1.0000 unchanged.
- The attribution census's denominator question is now one step from closure:
  the instrument screening it (Q-124) is answered on the 16-seed population.
  Coverage remains **0/6**, `NO_GRADED_RUNG` — this cycle did not re-open it.

## Key learnings

- **`points_needed` is the most useful thing this branch has built in a week.**
  It converted "underpowered" from a dead end into a purchase order for 16 sim
  runs, and the purchase closed at exactly the quoted price. Prefer bounded
  findings that name their own remedy over caveats.
- **Buy a cross-check when a measurement is added to an old ensemble.** The
  `w_geom = 20` re-walk cost 16 runs and converted "presumably the same
  harness" into a bit-for-bit fact. Cheap insurance for any rung appended to a
  constant table walked cycles earlier.
- **A fresh point that strengthens a finding it was not collected to test is
  worth more than one that was.** The 19/21 concordance is the only reading
  here immune to the "you chose the measurement to get the answer" objection
  that has bitten this branch three times (D-167/D-168/D-169).

## Recommended next 1–3 priorities

1. **Resolve Q-125 — which seed count the census calls its own.** It was
   correctly deferred until a powered screen existed; one now does, so
   choosing the strictness is no longer "moving a threshold to obtain a
   finding".
2. **Re-walk the frozen arm on `cafe_head_on_v0` `w = 75`** — one refused rung
   is not a result, and the frozen arm needs no calibration run.
3. **Make `sandbox:pass=N` state which quantity it is** — `passed` vs
   `executed`. Carried thirteen cycles.

## Artifacts
- PR: #67 (already open — D-140; this cycle adds no review bandwidth)
- Files touched: `eval/mppi_sandbox/geometric_null.py`,
  `eval/mppi_sandbox/admissibility_selection.py`,
  `eval/mppi_sandbox/representations/frozen_bev.py`,
  `eval/mppi_sandbox/tests/test_geometric_null.py`,
  `eval/mppi_sandbox/tests/test_admissibility_selection.py`
- TSV row appended: yes
