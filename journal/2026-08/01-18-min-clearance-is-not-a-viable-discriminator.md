# SKIP (13th) — power analysis: min-clearance can never be this project's discriminator; collision rate can

- **Cycle**: 2026-08-01 18:00 KST
- **Branch**: none (gate 1 fired — queue 6/6)
- **TODO**: none picked
- **Phase**: P3/P5 boundary
- **Status**: in_progress (finding recorded; no branch possible)

## What I tried

- Re-derived gate 1 from scratch: 6 in-queue (#69/#68/#67/#66/#44/#23), 0 pushed-but-PR-less,
  0 branches in 24h. Deadlock-breaker: `grep superseded docs/decisions.md` → still **0**
  `Status: superseded by D-NNN` entries, so criterion (b) has no candidate. Not forced.
- 17:00 showed the Q-017 clearance assertions are single-seed artifacts but left the obvious
  question open: **how many seeds would it actually take?** STATE's "≥16 seeds" was a guess.
  Ran a proper **paired 48-seed sweep** of `test_epistemic_margin_widens_berth_in_occlusion_geometry`
  (`risk_mppi`, `w_risk=0`, k=0.0 vs k=0.4, same geometry as the test) + a power/MDE analysis,
  and a Fisher-exact power sim for the collision-**rate** alternative. 69 s wall, inside the 2-min limit.

## What worked / what failed

- **The effect is not underpowered — it is refuted.** n=48 paired: mean **−0.00344 m**,
  sd 0.0284, **95% CI [−0.0115, +0.0046]**. Zero is *inside* the interval; the test's asserted
  **+0.02 is far outside it**. Sign test **26/48 positive** (t = −0.84) — a coin flip. So main's
  test does not assert a real effect that CI noise perturbs; it asserts an effect the data
  **excludes**, and passes on seed 0 by coincidence.
- **The point estimate is slightly negative**, i.e. k·σ margin may marginally *cost* clearance
  here. Directionally consistent with #67's "redundant" claim, but the honest n=48 answer is
  "≈ 0, sign unresolved" — which is why Q-017 must go back to `open` rather than flip to #67's negative.
- **Min-clearance is unaffordable as a discriminator, quantitatively.** MDE at 80% power:
  N=1 → 0.080 m, N=8 → 0.028 m, **N=16 → 0.0199 m**, N=48 → 0.0115 m, N=500 → 0.0036 m.
  STATE's "≥16 seeds" turns out to be *exactly* the N whose MDE is the asserted 0.02 — a right
  number aimed at the wrong effect. Resolving a 5 mm effect needs **253 seeds (~6 min sim)**;
  the observed 3.4 mm needs **534 (~13 min)**. Both **blow the executor's 2-min sim hard limit**.
- **Pairing does not rescue it.** corr(k=0, k=0.4) across seeds is only **+0.379**, and the paired-diff
  sd (0.0284) is *larger* than either arm's (0.0279 / 0.0225). Changing k re-rolls the trajectory, so
  common-seed variance reduction evaporates. There is no cheap variance trick left to try.
- **Collision rate is affordable and decisive.** Fisher-exact power for #69's observed 0.375 vs 0.0:
  N=8 → 0.13, **N=16 → 0.77, N=24 → 0.97 (35 s sim)**, N=32 → 0.99. The metric this project can
  actually afford is a Bernoulli rate, not a surviving-margin scalar.

## North-star delta

- **A metric is retired on evidence.** Every "representation buys clearance" claim in the Q-017
  thread was measuring a quantity whose noise floor (±0.028 m) is larger than the baseline
  clearance itself (0.030 m). That is not a north-star *advance*, but it stops the project from
  spending P5 building an ablation table on an instrument that cannot resolve its own effect.
- **#70 `seed_sweep` is confirmed as the right instrument for the right reason** — and its metric
  should be **rate**, not clearance. 24 seeds/arm is enough and costs 35 s.
- Merge stall unmoved: 484 h / 20.2 d since #64.

## Key learnings

- **"Underpowered" and "refuted" need distinguishing before proposing a fix.** 17:00's conclusion
  ("n=1 is worthless, use more seeds") implied more seeds would reveal the effect. They reveal its
  absence. Had the next cycle just bumped N to 16, the test would have gone red honestly and been
  misread as a regression.
- **Compute the MDE before choosing N.** "≥16 seeds" sounded conservative and was numerically the
  precise threshold for the effect someone *hoped* for — an anchoring artifact. MDE-first turns
  seed count from a guess into a derived quantity.
- **The hard limits are a metric-design constraint, not just an ops rule.** A 2-min sim ceiling
  means any scalar needing >200 seeds is permanently out of reach for this executor. Metric choice
  must be power-checked against that ceiling *before* a harness is built around it.

## Recommended next 1–3 priorities

1. **Reopen #70 `seed_sweep`; make collision/unsafe RATE the primary metric at N=24** (power 0.97,
   35 s). Demote min-clearance to a reported-but-not-asserted diagnostic.
2. **Revert Q-017 to `open`** in `docs/deliberations.md`, citing n=48 CI [−0.0115, +0.0046] —
   the negative (#67) is as unsupported as the positive (main).
3. **Replace main's `test_epistemic_margin_widens_berth_...` with #66's deterministic contract
   test** — independently re-confirmed: it is the only form of this assertion that can be true.
   (Unchanged merge recipe; keep #66.)

## Artifacts

- PR: none — gate 1, queue 6/6
- Files touched: none committed. Local-only: `STATE.md`, `JOURNAL.md`, this journal file.
  Analysis scripts were throwaway (`/tmp/power.py`, `/tmp/stats.py`, `/tmp/binom.py`).
- TSV row appended: no (no branch)
