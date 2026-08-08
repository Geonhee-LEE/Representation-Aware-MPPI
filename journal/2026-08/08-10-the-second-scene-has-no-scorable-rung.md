# The second scene has no scorable rung: its transition and its ESS band are disjoint

- **Cycle**: 2026-08-08 10:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — walk the densified ladder on `cafe_obstacle_crossing_v0` and build its `ScorableBand`
- **Phase**: P5
- **Status**: keep

## What I tried

- D-132's band — `{75, 100, 150}` on `cafe_head_on_v0`, `w = 100` at p = 2.5e-4
  — is one scene's property. `cafe_obstacle_crossing_v0`, the other scene D-125
  relieved, had never been scored for headroom at any rung, so "the mechanism
  has a band" and "the mechanism has a band on one scene" were the same
  sentence.
- Walked `w ∈ {30, 75, 150, 300, 500, 750, 1000, 2000}` (head_on's band region
  stretched to bracket crossing's relief threshold of 1000, D-127), 16 seeds per
  arm, margin 0.30, both arms — at **two** temperatures, because this scene's
  calibrated `lam` windows are **disjoint** (stock `[0.4, 0.8]`, risk
  `[1.6, 3.2]`, recorded in the scene file since the 5-actor block landed). So
  λ = 0.8 and λ = 3.2 were both walked in full: 512 runs, 225 s.
- Shipped per-arm ESS attribution on `BandRung` (`ess_arms` /
  `out_of_band_arms`) and `ScorableBand.refused_by_arm` / `sole_refuser`,
  because on a scene with disjoint windows "the rung was refused" and "the
  *baseline* refused the rung" are different facts and the report could only
  say so in prose.

## What worked / what failed

- 🔴 **`NO_SCORABLE_RUNG` at both temperatures.** Not one rung on this scene can
  carry a mechanism claim. The reason is structural, not a near miss: the rungs
  where the arms **differ** and the rungs where the sampler is **compliant** are
  disjoint sets. At λ = 0.8 the arms differ at 30/75/150 and every one of those
  is ESS-refused; the four compliant rungs (300–1000) all read stock 0.0000 vs
  risk 0.0000. At λ = 3.2 exactly **one** rung of eight is graded (2000), and it
  is `NO_HEADROOM_SAFE` too.
- 🔴 **The refusal is two-sided, so it does not bound the mechanism.**
  `sole_refuser` is `None` at both temperatures — `stock_mppi` leaves the band
  at {30, 75, 150, 2000} and `risk_mppi` at {30, 75, 2000} (λ = 0.8). This scene
  has no admissible shared operating point in its own transition region, which
  is a statement about the scene and the sampler, **not** evidence the risk
  channel fails here.
- 🔴 **The trap D-131 installed the refusal for fired on this scene, hard.** At
  λ = 0.8, `w = 75`, the raw numbers are stock **16/16** unsafe → risk **7/16**,
  Fisher **p = 8.2e-4** — a *larger* effect than head_on's best admissible rung.
  Median ESS there is **1.8 / 2.2**: the softmax has collapsed to argmin-over-
  draws and λ is inert. Reported unrefused, this would have been the project's
  strongest result and it would have been about the sampler.
- 🟡 **One rung came within one arm of scorable**: λ = 0.8, `w = 150`, stock
  4/16 → risk 0/16 (p = 0.10), with **risk in band and stock out**. That is the
  concrete lead — the scene is one baseline-side calibration away from having a
  gradeable rung.
- ✅ The driver smoked at 2 seeds first (last cycle's lesson) and ran clean on
  the first full launch — no attribute failures, no lost sweeps.

## North-star delta

- **D-132's claim is now bounded, and the bound is honest.** The risk channel
  has a measured, significant, three-rung band on exactly **one** of the two
  scenes it was ever admissible on. On the second, the comparison cannot be run
  at all at either calibrated temperature.
- **No movement on the headline.** The 5-cell / 40-seed `unsafe_rate = 0.0000`
  matrix is untouched; this cycle measured headroom, not the matrix.
- The negative is worth more than a second band would have been: it names *why*
  the mechanism is unscorable here (transition ∩ ESS band = ∅) rather than
  leaving "no result on crossing" as an absence.

## Key learnings

- **A scene can have a mechanism and no place to measure it.** Headroom asks
  whether the arms *can* differ; ESS asks whether the run is about the cost
  term. Both scenes pass each check somewhere — crossing just never passes them
  at the same rung. That intersection, not either factor, is the reportable
  surface.
- **Attribution changes what a refusal means.** A `NO_SCORABLE_RUNG` owned by
  the mechanism arm bounds the mechanism; one owned by the baseline bounds the
  operating point; a two-sided one bounds the scene. Same verdict string, three
  different next moves.
- **The strongest-looking number on this scene is the inadmissible one.** The
  ESS refusal is not conservatism — it is the only thing between this cycle and
  a p = 8.2e-4 headline measured at ESS 1.8.

## Recommended next 1–3 priorities

1. **Calibrate `lam` at the weight, not at the shipped weight** — `lam_windows.
   yaml` was measured at `w_obs_soft = 10` and every refusal above came from
   using it at 30–2000. A per-(scene, weight) window is what would turn
   crossing's `w = 150` into a graded rung. This is STATE's standing #3, now
   with a measured motive.
2. **Walk a denser λ ladder at crossing's `w = 150`** — the one rung where the
   mechanism arm is compliant and only the baseline is not. Cheapest possible
   route to a second scorable rung.
3. **Give `SEPARATED` a resolution floor (Q-115)** — still open, and this
   cycle's λ = 3.2 / `w = 150` rung (0/16 vs 2/16, p = 0.48, sign against) is a
   second live instance.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic, #67)
- Files touched: `eval/mppi_sandbox/scorable_band.py`,
  `eval/mppi_sandbox/tests/test_scorable_band.py`, `docs/decisions.md`,
  `docs/deliberations.md`, `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV row appended: yes
