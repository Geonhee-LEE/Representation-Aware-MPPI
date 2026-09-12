# The knee+shape heading residual is a proximity effect, not a steady-driving one

- **Cycle**: 2026-09-12 10:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `[sandbox] knee+shape 아래 heading_err_rms_max 공략` (STATE #1)
- **Phase**: P5
- **Status**: in_progress (deliberate strand — see correction note below)

## What I tried

- Wrote `eval/mppi_sandbox/heading_error_phase.py` to localize *where* the
  `knee+shape` arm's `heading_err_rms_max` failures (10/16 seeds on
  `cafe_obstacle_crossing_v0`, per D-430) come from — avoidance maneuver,
  recovery, or steady driving — as STATE's next-action asked.
- First attempt: a discrete clearance-band phase split at
  `AVOIDANCE_BAND = 0.30` (the same value the knee/shape knobs are set to).
  It reported **100% steady, 0% avoidance, 0% recovery on all 10 failing
  seeds**.
- Before trusting that, checked why: measured minimum clearance across all 16
  seeds is 0.3001–0.3279 m — strictly above 0.30 on every seed, by as little
  as 0.0001 m. The compact-support barrier's whole job is to keep clearance
  just outside its own band, so a `clearance <= 0.30` test cannot fire on any
  seed *by construction*. Widened the band to 0.5/0.9/1.5/2.5 as a sanity
  check and the verdict flipped almost entirely to "avoidance dominates" —
  proof the discrete-phase framing itself is not well-posed here (proximity
  is continuous on this scene, not bimodal), not that either band was wrong.
- Replaced it with a threshold-free measure: Spearman rho between
  per-timestep clearance and `|heading_error(t)|` within each run, plus the
  clearance at each failing seed's single worst heading-error instant.

## What worked / what failed

- The naive banded approach **failed silently** — it would have shipped a
  confident, wrong answer ("it's a steady-driving problem") had I not
  measured the barrier's own min-clearance distribution first.
- The correlation approach worked cleanly: rho is negative on **all 16**
  seeds (range -0.117 to -0.599, none near zero or positive), and every
  failing seed's peak heading error sits at clearance 0.32–1.05 m, against a
  ~3.0 m open-road ceiling elsewhere in the same runs.
- 5/5 new tests pass (`test_heading_error_phase.py`), including one that pins
  the boundary artifact itself (`test_the_barrier_never_enters_its_own_band`)
  so a future cycle doesn't have to rediscover it before trusting a band.
- `census_preempt` caught a real drift pre-suite (`lam_site_census`
  96/43 → 98/44, 3 new sim-backed call sites in the new files) — repaired in
  the same commit before it could cost a red suite.

## North-star delta

- Direct progress on 경로추종 (path tracking): the open tracking question
  STATE named is now answered with a falsifiable, threshold-free measurement
  rather than a guess. The answer also *reorients* the next knob: since the
  error is concentrated near the obstacle, a global heading-effort term
  (`w_heading`, already explored in Q-185/avoidance_price.py and found to
  collide with the avoidance cost) is the wrong shape — a *proximity-gated*
  heading term (active only inside some clearance band, mirroring the
  barrier's own compact support) is the better-motivated next experiment.
- 물체회피 unaffected — no controller/cost code changed, only measurement.

## Key learnings

- A phase/band definition reused from an unrelated knob (the collision gate)
  is not automatically a meaningful *measurement* boundary — the gate value
  is where the controller's response saturates, which made it the worst
  possible choice for a proximity classifier on this scene. Worth generalizing:
  before trusting any clearance-band split anywhere else in this sandbox,
  measure the min/max clearance distribution first.
- This is a second independent design (after Q-185/avoidance_price.py) on
  "does the heading residual come from being near the obstacle" — the two use
  different methods (cross-seed correlation with detour/clearance vs.
  within-run correlation with instantaneous clearance) and agree in
  direction, which is worth more than either alone.

## Recommended next 1–3 priorities

1. Discharge this cycle's strand: run the full sandbox suite, take a receipt
   via `push_preflight record`, and push commits `f74ef19`/`cab5826` (no
   re-diagnosis needed — the code and docs are already correct, only the
   receipt is missing).
2. Design and test a proximity-gated heading term (`w_heading` active only
   when `clearance < some band`, sized off this cycle's measured 0.32–1.05 m
   peak-error window) as the knob this localization was a precondition for.
3. `inert_surface probe`/`reprobe` — now **two** consecutive cycles have
   withdrawn the same 5 pins (JOURNAL.md/RESULTS.md/STATE.md/journal/results)
   without re-taking them.

## Correction note

The first TSV row this cycle appended (commit `f74ef19`) was mis-marked
`keep` — written before checking `cycle_wallclock elapsed`, which returned
`SUITE_UNAFFORDABLE` (19m39 elapsed, 17m12 deadline already passed) once
actually checked. No full-suite receipt exists for this tree, so `keep` was
an overclaim: only the new test file (5/5) and the repaired census pins were
directly verified, not the whole suite `push_preflight` requires to push.
Appended a second, honest row (status `in_progress`) rather than pretending
the first didn't happen — TSV is append-only by design for exactly this
case. This cycle ends as a **deliberate strand**: commits stay local-ahead of
origin, and the next cycle's Phase 1 Step 0 (`cycle_artifacts stranded`)
picks up the suite + push per the established D-378 pattern.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic, #67)
- Files touched: `eval/mppi_sandbox/heading_error_phase.py` (new),
  `eval/mppi_sandbox/tests/test_heading_error_phase.py` (new),
  `eval/mppi_sandbox/tests/test_default_lam_sites.py` (census pin repair)
- TSV row appended: yes
