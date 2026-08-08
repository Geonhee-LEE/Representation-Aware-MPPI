# The band survives its own re-keying — and the guard finally refuses something it can also permit

- **Cycle**: 2026-08-08 12:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — Q-117: λ ladder on `cafe_head_on_v0` at `w = 100`
- **Phase**: P5
- **Status**: keep

## What I tried

- Walked λ ∈ {0.2, 0.4, 0.8, 1.6} × both arms × 16 seeds at `w_obs_soft = 100`
  on `cafe_head_on_v0`, margin 0.40 — 128 runs, 296 s. This is the cell
  D-131/D-132's band was measured on, at the weight it was measured at, using
  a λ that came from a table generated at `w = 10`.
- Graded the result through `lam_window_key.window_shift`, the four-way witness
  D-134 shipped without a `WINDOW_HELD` instance.
- Consolidated the two re-measured cells into a `Remeasurement` dataclass + a
  `REMEASURED` registry, with `window` / `recorded` / `shift` / `shared` all
  derived from stored `(n_in_band, n)` counts, and added `shift_census()`.

## What worked / what failed

- **Both arms held, exactly.** Recorded `[0.2, 0.4, 0.8]` re-measures to
  `{0.2, 0.4, 0.8}` on both `stock_mppi` and `risk_mppi`, every rung **16/16**
  in band and 16/16 reaching the goal. `WINDOW_HELD` on both.
- **λ = 0.8 — D-132's operating point — is admissible for both arms.** So the
  band was walked at a temperature its arms are actually admissible at, and
  D-134's finding is bounded to the cell that produced it.
- **The hold is set equality, not containment**: λ = 1.6 is **0/16** on both
  arms. A window that held by widening would have been the weaker result.
- The separation at this weight is large and consistent across the whole
  admissible ladder — stock `unsafe_rate` 0.94/1.00/1.00 vs risk
  0.25/0.31/0.38 at λ = 0.2/0.4/0.8, mean clearance 0.30 vs 0.42.
- **The suite went red on bookkeeping, not on the finding.** The three new
  per-arm assertions are population-claim loops, so `loop_reach.READING` had to
  record them (`n = 2` each) before `test_recorded_reading_covers_exactly_todays_targets`
  would pass — and re-taking that reading exposed its prose claiming "all 15
  population claims" over a set that has been 18 for three cycles. Cost: one
  extra 14-minute suite.
- **`git add -u` staged all five local-only files** into the bookkeeping commit,
  which is the D-011 offence the branch rule exists to prevent. Three tests went
  red for it — `local_only_audit`'s own branch check plus two
  `exemption_masking` census tests whose population shifted — and the commit was
  rewritten to the three intended paths. The rule says `git add -- <specific
  paths>` for exactly this reason; `-u` is not a shortcut for it.
- Driver smoked at 2 seeds first (two cycles' standing lesson) and caught one
  attribute error (`ArmSafety.n_safe` does not exist) before the 5-minute run.

## North-star delta

- **The project's only significant mechanism claim is no longer in question.**
  D-132's band (`{75, 100, 150}`, p = 2.5e-4) was one plausible re-measurement
  away from retraction this morning; it now has a witnessed admissible
  temperature at its own weight.
- The guard shipped yesterday is now non-vacuous **in both directions** —
  before this cycle `WINDOW_HELD` was a branch no measurement reached.
- Headline safety numbers untouched: no new scenario, no controller change.

## Key learnings

- **A guard justified by one cell is justified by its worst cell.** D-134's
  crossing has disjoint per-arm windows and a 5-actor block; reading "windows
  move" off it was the generalisation the second cell was needed to test. The
  honest rate is **2 of 4 arm-cells held**, not "windows move".
- **The census is confounded and says so.** The cells that moved are crossing
  *and* `w = 150`; the ones that held are head_on *and* `w = 100`. Scene and
  weight are the same two rows, which is why Q-118 nominates head_on at
  `w = 150` — the one walk that holds the scene fixed *and* can retract a rung
  D-132 actually shipped.
- **A rate must be able to name its numerator.** `shift_census` returns grade →
  member labels, not counts, so "2 of 4 held" can always be audited back to
  which two.

## Recommended next 1–3 priorities

1. **Q-118: λ ladder on `cafe_head_on_v0` at `w = 150`** — breaks the
   scene-vs-weight confound and re-keys a rung inside D-132's shipped band.
2. **Re-key `lam_windows.yaml` by weight** (Q-116 option (a)) — now bounded by
   two measured cells rather than open-ended.
3. **Give `SEPARATED` a resolution floor (Q-115)** — still open; every rung of
   this cycle's ladder graded `SEPARATED`, including λ = 1.6 where both arms
   are out of band.

## Artifacts

- PR: #67 (open, `autoresearch/p3-epistemic-shadow-cost-critic`)
- Files touched: eval/mppi_sandbox/lam_window_key.py,
  eval/mppi_sandbox/tests/test_lam_window_key.py, docs/decisions.md,
  docs/deliberations.md
- TSV row appended: yes
