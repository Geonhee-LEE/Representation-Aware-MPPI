# `w_omega` reshuffles the heading residual — it does not fix it

- **Cycle**: 2026-08-23 01:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `heading-err-under-knee-shape` (STATE #1)
- **Phase**: P5
- **Status**: keep

## What I tried

- Took STATE's #1 — the sole dominant residual after D-430: under the
  `knee+shape` pair on `cafe_obstacle_crossing_v0`, clearance is green 16/16 and
  every remaining failure is `heading_err_rms_max` (10 seeds).
- Priced the obvious lever, the rotation-effort weight `w_omega` (0.5 default),
  with a 4-point sweep at n=16: **6 / 5 / 9 / 7** net pass at
  w_omega ∈ {0.5, 1.0, 2.0, 4.0}. 64 integrations, ~40 s, zero source change.
- Read 2.0's 9/16 as a candidate lift, then tested it **paired** — the arms
  share seeds, so McNemar applies and Fisher (which D-430 used) throws the
  pairing away.
- Shipped the result as `tests/test_heading_effort_weight.py` (5 tests, 32
  integrations, ~21 s) + D-433 + Q-181.

## What worked / what failed

- ❌ **The lever does not work, and that is the deliverable.** McNemar on the
  same 16 seeds: 5 seeds fail→pass against 2 pass→fail, exact two-sided
  **p ≈ 0.45**. The 6/16 → 9/16 headline is not established at n=16.
- ❌ **The response curve is non-monotone** (0.5→6, 1.0→**5**, 2.0→9, 4.0→7).
  The dip at 1.0 is the tell: a knob that worked would not go *down* on the way
  up. I would have shipped "w_omega=2.0 lifts the scene" as a positive result if
  I had swept two points instead of four.
- ❌ **Per-seed heading deltas are two-sided** — 0.5→2.0 improves
  `heading_err_rms` on 9 seeds, worsens it on 7, spanning −0.55 to +0.28. The
  population barely moves; which seeds sit on which side of 0.30 does.
- ✅ **This is D-430's shape found on a second knob.** D-430: the barrier-shape
  knob reshuffles seeds between modes rather than converting them. Same here for
  effort weighting. Two independent knobs behaving this way is a claim about the
  *scene*, not about either knob.
- ✅ Clearance is untouched by effort weighting — 16/16 on both arms,
  0.300–0.328. The knee owns clearance and `w_omega` does not spend it.
- ✅ At w_omega=2.0 the residual set is **heading-only** (7 seeds); D-430's cte
  failures (3+3) are absent. Recorded as the reshuffle seen from the other side,
  *not* as a fix.

## North-star delta

- **Non-zero, negative.** One lever removed from the table for 경로추종 on this
  scene, with the paired evidence to keep it removed. 96 integrations total,
  no source change.
- **A methodological correction that reaches backwards**: D-430's Fisher test
  was the wrong test for a shared-seed design. The pairing was always available
  and unused.
- 물체회피 unchanged — clearance stays solved at 16/16.

## Key learnings

- **Sweep enough points to see the curve, not the argmax.** Two points here
  (0.5, 2.0) read as a clean +3 lift. Four points show noise. The extra ~20 s
  was the difference between a false positive and a negative result.
- **Shared seeds mean paired tests.** Fisher on paired arms is both wrong and
  *less* powerful; McNemar was free and decisive.
- **Two knobs now reshuffle rather than shift on this scene.** That redirects
  the next lever from tuning to structure — which is Q-181's suspicion:
  clearance is bought by deviating from the reference path and `heading_err_rms`
  is measured against that same path, so the knee that pins clearance to
  0.300–0.328 (D-426: the robot parks on whatever knee it is priced against) may
  be *paying* for it in heading. If so, no effort weight can ever fix it.

## Recommended next 1–3 priorities

1. **Answer Q-181 — is the heading residual definitionally coupled to the knee?**
   Cheap and decisive: correlate per-seed `heading_err_rms` against
   `min_obstacle_clearance` / detour magnitude across the existing arms. If the
   coupling is tight, the residual is not a controller defect and the acceptance
   threshold is what should move.
2. **`census-only-push-subset`** — price a shard subset licensing a push for a
   census-only change. This cycle overran on the suite again (see below).
3. **`receipt-store-test-isolation`** (Q-180) — mechanical, still open.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: `eval/mppi_sandbox/tests/test_heading_effort_weight.py`,
  `docs/decisions.md`, `docs/deliberations.md`, `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV row appended: yes
