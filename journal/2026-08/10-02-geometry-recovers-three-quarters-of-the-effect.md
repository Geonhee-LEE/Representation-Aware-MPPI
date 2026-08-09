# Geometry recovers three quarters of the effect the representation was credited with

- **Cycle**: 2026-08-10 02:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — run the feed's one-variable min-lidar ablation (2607.16591)
- **Phase**: P3
- **Status**: keep

## What I tried

- Built the null arm the branch has never run: `GeometricMPPI` — `StockMPPI`
  plus `w_geom · Σ_t exp(−min_n(‖x_t − p_n(t₀)‖ − r_n − r_robot)/scale)` in
  `RiskMPPI`'s own cost slot. Positions **frozen at `t₀`** (one lidar scan, no
  motion model), reduced by **`min`** over obstacles (a lidar returns the
  nearest return; the sandbox's soft barrier sums per-obstacle instead), decay
  length defaulting to the barrier's so the null gets no second tunable.
- Walked it against the population's **most separated** rung — convoy
  `w_obs_soft = 75`, λ = 0.8, seeds 0–31, where D-166 records the mechanism at
  `A = 1.0000` with the two arms' clearance ranges disjoint.
- Graded head-to-head with `margin_free.RungComparison`: paired by seed,
  rank statistic + paired bootstrap CI + TOST. No threshold anywhere.
- New `geometric_null.py` carries the walk, the calibration, and the verdict.

## What worked / what failed

- 🔴 **The equal-coefficient swap was refused, and that is the first finding.**
  `w_geom = w_risk = 40.0` was defended in the controller docstring by a shape
  argument — both summands peak at 1.0 at contact and decay. Measured, that arm
  runs at median ESS **12.40** against the risk arm's **105.07** at the same
  λ = 0.8, 4/8 seeds outside `ab.ess_band`. A λ ladder over {0.4, 0.8, 1.6, 3,
  6} finds **no shared admissible temperature**: stock and risk are 8/8 only at
  0.8, where the null is 4/8; the null's best is 1.6 (7/8), where stock is 1/8
  and risk 0/8. Equal coefficient is not equal loudness, so the "one-variable
  swap" as first written moved the term *and* the sampler's operating point.
- 🟢 **Calibrating by the sampler's own response fixes it and is the stricter
  match.** Hold λ = 0.8 for all three arms, pick `w_geom` whose median ESS lands
  on the risk arm's → `w_geom = 2.5` (median ESS 86.08, **32/32** in band,
  32/32 reached). This equalises the quantity the comparison is sensitive to,
  which `scale_match`'s cost-ratio does not — and the cost-ratio route was not
  available anyway without a `scale_match.ADDITIVE_WEIGHTS` entry.
- 🔴 **Geometry alone very nearly reproduces the branch's headline separation.**
  `A(geom vs stock) = 0.9868` against the mechanism's `1.0000`; paired
  Δ = **+0.1143 m**, CI `[+0.1002, +0.1301]`, against the mechanism's
  **+0.1480 m**, CI `[+0.1324, +0.1627]`.
- 🟡 **The representation does keep a real residual, and it is a quarter.**
  Head-to-head `A(risk vs geom) = 0.6953`, Δ = **+0.0337 m**, CI
  `[+0.0161, +0.0505]` — excludes zero, so `REPRESENTATION_ADDS` rather than a
  tie. But `residual_share = 0.7725`: **77% of the gain survives removing the
  representation entirely.**
- 🔴 **And the residual does not survive turning the null up one rung.** At
  `w_geom = 5.0` the null recovers **91%** (Δ = +0.1351) and the head-to-head
  reads `EQUIVALENT` at ε = 0.05 m, CI `[−0.0073, +0.0337]` ∋ 0. That rung is
  **refused** (`LOUDER_NULL`, ESS out of band on 32 seeds) and the verdict never
  reads it — pinned by a test that perturbs it and checks the verdict is
  unmoved — but a residual that is 23% at one admissible coefficient and
  undetectable one rung up is not a stable 23%.
- 🟢 **The 8-seed licence bit again, same direction as D-163.** `w_geom = 5.0`
  was **8/8** in band on the calibration ensemble and **not** 32/32 on the walk.
  The cheap measurement is the permissive one, twice now.
- 🟢 **The ablation invariant checks against the branch's own recorded data,
  not just against itself.** `geometric_mppi` at `w_geom = 0` reproduces
  `CONVOY_W75_CLEARANCES["stock_mppi"]` with max |Δ| = **0.0** over 32 seeds —
  so this cycle's runs and the recorded constants are on one footing, and the
  head-to-head is not comparing across two measurement epochs.
- 🟡 The positive control matters here: at `w_geom = 0` vs `2.5` the trajectories
  differ in **length**, not only in value, so the "term is live" test had to
  accept shape inequality — an `allclose` would have errored rather than failed.

## North-star delta

- **No headline movement, and the cycle argues the headline was over-credited.**
  `unsafe_rate` **0.0000** / `min_clearance` **0.3579** / `success_rate`
  **1.0000** unchanged — no scenario, no representation, no sim-visible change.
- What moves is **attribution**: the branch's clearance result on its strongest
  rung is now known to be ~77% geometric. That is a smaller claim than
  yesterday's and a better-founded one.
- One new controller in the registry (`geometric_mppi`), usable as the null for
  every future representation arm, not just this one.

## Key learnings

- **A one-variable swap has to be verified as one variable.** The shape argument
  for equal coefficients was plausible, cheap to state, and measurably false;
  the ESS ladder is what caught it. Any future arm added to this cost slot
  should be ESS-calibrated before it is compared, not after.
- **"Does it beat stock" and "does it beat the null" are far apart.** The same
  rung reads `A = 1.0000` against stock and `0.6953` against a term with no
  learned anything. Every prior positive reading on this branch is denominated
  against stock, so every one of them is open to the same discount.
- **Report the share, not the verdict.** `REPRESENTATION_ADDS` alone reads as a
  win. `REPRESENTATION_ADDS, residual_share = 0.77` is the same measurement and
  a different message; the share is the number STATE's bottleneck asked for.
- 2607.16591's direction (min-lidar **beats** uncertainty) is **not** reproduced
  here — the mechanism stays ahead. Its weaker reading — the uncertainty term
  buys much less than its headline suggests — is.

## Recommended next 1–3 priorities

- **Re-run the null on the other five walked rungs.** One scene, one rung is the
  weakest possible base for an attribution claim, and the machinery is now
  written — head_on `w ∈ {75, 100, 150, 250}` and crossing `w = 250` each cost
  ~60 s plus one ESS calibration.
- **Re-take the residual with the null ESS-matched at 16 or 32 calibration
  seeds**, since the 8-seed ensemble licensed a coefficient the 32-seed walk
  refused; the admissible-coefficient *window* is what the residual is a
  function of.
- **Make `sandbox:pass=N` state which quantity it is** — `passed` vs `executed`.
  Carried five cycles.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/controllers/geometric_mppi.py, eval/mppi_sandbox/controllers/__init__.py, eval/mppi_sandbox/geometric_null.py, eval/mppi_sandbox/tests/test_geometric_null.py, docs/decisions.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: pending
