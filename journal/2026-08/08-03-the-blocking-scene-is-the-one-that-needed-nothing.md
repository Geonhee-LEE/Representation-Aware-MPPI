# The blocking scene is the one that needed nothing

- **Cycle**: 2026-08-08 03:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #2 — answer Q-111 (is the relieving `w_obs_soft` per-scene?)
- **Phase**: P5
- **Status**: keep

## What I tried

- Shipped `relief_interval.py`: runs `barrier_ceiling.sweep` on every
  obstacle-bearing scene at that scene's **own** calibrated rung
  (`lam_for_cell`), then reconciles the per-scene results into one cross-scene
  verdict — `GLOBAL_REPIN` / `PER_SCENE_REQUIRED` / `UNRELIEVABLE`.
- Ladder `(30, 100, 300, 1000, 3000)`, geometric because the knob is a gain,
  bracketing the shipped `w_obs_soft = 10` and D-125's relieving 300.
- Reconciliation is a **set** intersection over tested rungs, not an interval
  intersection — nothing in this repo argues `all_reached AND ess_in_band` is
  monotone in the weight, so a mid-ladder hole is permitted and interval
  arithmetic could nominate a rung inadmissible on the scene it came from.
- 3m13 of sim, 8 seeds, 3 sweepable scenes × 6 rungs.

## What worked / what failed

- ✅ **Q-111 answers `PER_SCENE_REQUIRED`. (a) global repin is refuted with a
  measurement, not an argument.** `cafe_head_on_v0` threshold **300**, ceiling
  **3000**; `cafe_obstacle_crossing_v0` threshold **300**, ceiling **1000**;
  `cafe_convoy_v0` needs no relief and its ceiling is **30**. The two sets are
  disjoint, so no tested rung serves all three.
- 🔴 **Q-111's own decision rule was wrong, and that is the transferable
  part.** It said "문턱이 scene 별로 갈리면 (b)/(c), 다 같으면 (a)". The
  thresholds **are** the same — both needing scenes want exactly 300 — and (a)
  is still refused. The binding constraint is not a spread in thresholds; it
  is a **ceiling on the scene that needed nothing**. The Q measured the axis
  where the scenes agreed and would have closed on (a) had it not also been
  told the other axis.
- ✅ **D-125's threshold survives a 2× temperature change for free.** D-125
  found 300 on head_on at λ=0.8; this survey runs head_on at its own λ=0.4 and
  finds 300 again. The relief threshold is not a temperature artefact.
- 🔴 **Two of Q-111's "five obstacle-bearing scenes" cannot be swept at all**,
  for two different pre-existing reasons, and both refusals are the repo
  working: `cafe_freezing_v0` declares no margin (D-120's `unscored_margin`),
  `cafe_cut_in_v0` has an empty admissible temperature window
  (`completes_anywhere: false`). They are carried by name in `refused`, not
  dropped — a cross-scene verdict over "the scenes that happened to run" is
  the empty-denominator failure D-107 and D-120 both booked.
- 🔴 **A test caught a real defect before it shipped.** A scene unsafe by less
  than `MIN_IMPROVEMENT` cannot be improved on by `MIN_IMPROVEMENT`, so every
  rung — including a perfect one — failed the relief test for arithmetic
  reasons and the scene was graded `UNRELIEVED`, which outranks everything and
  would have vetoed a repin on a difference the survey cannot measure. Split
  out as a fourth verdict `SUBRESOLUTION`: it may refuse a rung, not demand
  one.
- 🟡 **`convoy`'s ceiling of 30 is the ladder's floor**, so its true ceiling is
  somewhere in (30, 100] and untested. The disjointness verdict does not
  depend on it — 30 < 300 either way — but the *width* of the gap does.

## North-star delta

- The first cross-scene statement about the knob that moved a safety verdict:
  **one weight cannot serve the matrix**, measured over 3 scenes and 18 rungs.
- Converts Q-111 from an open architecture question into a two-way choice
  ((b) per-scene weight vs (c) weight derived from scene geometry) with (a)
  eliminated on evidence.
- No new controller capability. The `unsafe_rate = 0.6667` headline is still
  uncorrected — this cycle produced the rung table that correction needs.

## Key learnings

- **A decision rule can be sound about the axis it names and still reach the
  wrong verdict, if the binding constraint lives on an axis it did not name.**
  Q-111 asked whether thresholds differ; the answer was no and the conclusion
  was still (b)/(c), because ceilings do.
- **The scene that needs no relief is not a bystander to a global repin — it
  is a voter with veto power.** Convoy was 0/8 safe at the shipped weight and
  is the only reason the repin fails.
- **Set intersection over interval intersection was not pedantry**: the
  synthetic non-contiguity case is pinned in a test, and it nominates a bad
  rung under interval arithmetic.
- A resolution bar and a presence bar must not be the same constant even when
  they are compared against the same quantity.

## Recommended next 1–3 priorities

1. **Re-run the 8-cell baseline matrix at each cell's own admissible
   `w_obs_soft`** — the rung table this needs now exists (head_on/crossing 300,
   convoy shipped 10). This is the `unsafe_rate = 0.6667` correction.
2. **Answer Q-112 — densify the ladder between 30 and 300** to locate convoy's
   true ceiling and test whether the two needing scenes' shared 300 is a real
   agreement or a 3×-ladder artefact. Decides whether (c) is even askable.
3. **Re-run D-119 / D-124's A/Bs above the relief threshold** — still the
   oldest outstanding correction; both were scored inside the failure region.

## Artifacts

- PR: pending merge (`autoresearch/p3-epistemic-shadow-cost-critic`, #67)
- Files touched: `eval/mppi_sandbox/relief_interval.py`,
  `eval/mppi_sandbox/tests/test_relief_interval.py`, `docs/decisions.md`,
  `docs/deliberations.md`, `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV row appended: yes
