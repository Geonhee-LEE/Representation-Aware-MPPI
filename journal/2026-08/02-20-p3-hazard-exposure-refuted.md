# The exposure predictor was right in one direction and wrong in the other

- **Cycle**: 2026-08-02 20:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE claude-actionable **#1** — what makes the crossing scene different from `cafe_convoy_v0`? (Q-040)
- **Phase**: P3
- **Status**: keep

## What I tried

- Shipped `eval/mppi_sandbox/exposure.py`: a **static, simulation-free** screen in
  `feasibility.py`'s sense. Walks the reference path at the scene's own
  `target_speed_mps`, evaluates every obstacle's scripted schedule at each sample, and
  reports time-in-contest, peak simultaneous contest and closest nominal approach.
  0.1 s for all eight scenes.
- Candidate predictor: **contested fraction** — the time-integral, because 18:00's
  mechanism is cost *magnitude* and a collision term accumulates by integration.
  Static ranking looked strong: crossing **74%** vs convoy **43%** on identical
  obstacle counts, with `peak_contesting` ranking them **backwards** (2 vs 5), so the
  two candidate statistics were cleanly decoupled.
- Refused to stop there. A ranking over n = 8 with one positive proves nothing — any
  statistic that happened to rank the crossing scene first would look like a predictor.
  Built a **two-sided controlled intervention** in `eval/scenarios/variants/`: two
  **pure-timing** edits (only the waypoint `t` fields differ from the parent; lanes,
  x endpoints, speeds, radii, directions, robot path and acceptance block all
  byte-identical, enforced by a test that diffs the yamls rather than by a comment).
  Each variant's header **registers its prediction before** any run was paid for.
- Calibrated both variants over the full 8-rung × 8-seed ladder × 2 controllers.

## What worked / what failed

- 🔴 **The treatment arm refuted the hypothesis.** `cafe_convoy_staggered_v0` raises
  exposure 43% → **77%** — past the `per_arm` scene's own 74% — and its two arms still
  share **[0.4, 0.8]**. Time-in-contest is not sufficient, and not even monotone, so it
  is not the Q-040 predictor.
- ✅ **The converse arm confirmed it.** `cafe_obstacle_crossing_sync_v0` drops 74% →
  **26%** and its arms **re-overlap** at [1.6, 3.2] where the parent is disjoint
  ([0.4, 0.8] vs [1.6, 3.2]). Had I run only this arm — the cheaper, more obvious one —
  I would have reported the hypothesis as established.
- ✅ **The healed scene shows the shape a real predictor has to explain**: both windows
  moved **up together** (stock 0.4–0.8 → 1.6–3.2). The sync pass scaled *both* cost
  landscapes; separation needs something that scales **one arm's more than the other's**.
- ✅ **What survives is an interaction, not a main effect.** The four cells happen to
  form a complete 2×2 in (staggered timing) × (counter-flow actors), with `per_arm` in
  exactly one corner: crossing (✓✓) `per_arm`; convoy_staggered (✓✗), crossing_sync
  (✗✓), convoy (✗✗) all `shared`. Neither factor alone does it.
- ⚠️ **Stated as a lead, not a result** — the two off-diagonal cells come from different
  parents (0.3 vs 0.5 m/s, 5.0 vs 4.5 m), so the design is not fully crossed within one
  scene. Two more variants close it.
- ✅ Cost held: **168 → 181 passed + 1 xfailed**, **145.6 s → 165.1 s**. Twelve of the
  thirteen new tests simulate nothing; the whole 19.5 s is the one CI reproduction of
  the decisive cell (1 rung × 4 seeds, vs the ~250-run ladder that stays a script).
- ✅ Additive only — no existing assertion touched, variants live **outside** the
  `eval/scenarios/*.yaml` glob that three test modules pin at exactly 8.

## North-star delta

- **No capability movement** — still measurement methodology. But the project now knows
  one *wrong* answer for certain instead of carrying a plausible one forward, and knows
  it for the cost of two yaml files and four calibration cells.
- The exposure screen is durable regardless of the refutation: any new scene's hazard
  profile is now a **millisecond query** instead of a ~250-run calibration, which is
  what P5 needs before scheduling anything matrix-wide.
- Scenes able to contribute an avoidance number: **5**, reportable: **4** — unchanged.

## Key learnings

- **A one-sided intervention is a confirmation ritual.** The converse arm behaved
  exactly as predicted and was cheaper to reach; taking it alone would have promoted a
  false predictor into the calibration story. The refutation only exists because the
  *treatment* arm was run too. This generalises past this cycle and is recorded as
  **D-018**.
- **Register the prediction in the artifact, before the run.** Both variant headers say
  what they expect. That is why "77% and still shared" reads as a refutation rather
  than as an inconvenient number to reinterpret afterwards.
- **Enforce a control mechanically or it is not a control.** `test_variant_changes_only
  _obstacle_start_times` diffs the parent and variant yamls, so a later hand-edit that
  quietly changes a lane or a speed breaks the *test*, not the conclusion.
- **Two plausible statistics that rank the same pair oppositely are a gift** —
  `contested_fraction` and `peak_contesting` disagreeing is what made the intervention
  able to tell them apart instead of moving them together.

## Recommended next 1–3 priorities

1. **Close the 2×2 within a single parent** — `cafe_convoy_counterflow_v0` (convoy
   timing, two actors reversed) and `cafe_obstacle_crossing_staggered_noflow_v0`
   (crossing timing, all five same direction). If `per_arm` still appears only at
   ✓✓, the interaction is established rather than suggested. ~4 calibration cells,
   the cheapest experiment in the repo.
2. **Ask what the risk term actually reads.** Separation needs a factor that scales
   *one* arm's landscape more than the other's; the sync result shows exposure scales
   both. Counter-flow plausibly does it through the epistemic/occlusion channel
   `risk_mppi` alone consumes — checkable by ablating `w_epist` on the crossing scene.
3. **Unchanged and still first in real terms**: drain the merge queue (#66 → #67 → #69
   → #68). 39 consecutive gate-1 skips.

## Artifacts

- PR: **#67** (already open — landed in place, zero new review bandwidth, 14th cycle)
- Files touched: `eval/mppi_sandbox/exposure.py`,
  `eval/mppi_sandbox/tests/test_hazard_exposure.py`,
  `eval/scenarios/variants/cafe_convoy_staggered_v0.yaml`,
  `eval/scenarios/variants/cafe_obstacle_crossing_sync_v0.yaml`,
  `eval/scenarios/variants/lam_windows_variants.yaml`, `docs/decisions.md`
- TSV row appended: yes (`b237727`, `sandbox:pass=181/181`, keep)
