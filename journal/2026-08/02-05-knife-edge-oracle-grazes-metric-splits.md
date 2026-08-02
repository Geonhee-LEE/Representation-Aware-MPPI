# The oracle does not clear, it grazes at 1 cm — and no single metric detects the effect on both scenes

- **Cycle**: 2026-08-02 05:00 KST
- **Branch**: none (gate 1 fired, 24th consecutive) — work is uncommitted in `/tmp/proto_0802_05/`
- **TODO**: none picked; took 04:00's own stated limit ("the oracle's margin is still thin: +0.012 m")
- **Phase**: P3
- **Status**: in_progress

## What I tried

04:00 left one threat to its result unresolved: the safe arm's mean min-clearance was
**+0.012 m**. If the whole `stock` arm sits 1 cm from contact, "0/24" is a coin on its edge.
Three probes at the in-band temperature (`lam=0.3`), `cafe_blind_approach_v0`, N=24:

- **A — the distribution, not the count.** Per-seed min-clearance for both arms. A collision
  *count* discards the quantity that decides it.
- **B1 — scoring-threshold sensitivity** (free, no re-plan): recompute the collision rate of the
  *same* trajectories under a shifted contact threshold `d`. Measures distance to the decision
  boundary. **B2 — planning-radius sensitivity** (full re-plan, 192 runs): vary `robot_radius`,
  which enters both the planner cost and the score. The honest "was 0.30 m a tuned sweet spot?"
- **C — second scene.** `cafe_blind_corner_v0` (#68), line-of-sight rather than range-limited
  occlusion. One scene is an anecdote.

## What worked / what failed

- **🔴 The oracle does not route around the hazard — it rides the barrier.** `stock` clearance is
  median **+0.0096 m**, min **+0.0026**, max **+0.034**; **13/24 seeds within 1 cm** of contact.
  And it is **radius-invariant**: median graze **+0.0116 / +0.0096 / +0.0129 / +0.0132 m** at
  `robot_radius` 0.25 / 0.30 / 0.35 / 0.40 — a 60 % change in robot size moves it by 3 mm. The
  gap is set by the barrier-vs-progress cost equilibrium, not by geometry. 04:00 (and #69's
  scenario comment) read 0/24 as "the oracle plans a clear berth". It does not. Both arms graze.
- **✅ But the result is not a knife-edge in the direction that matters.** Loosening the contact
  test to require **2 cm of penetration** (`d = −0.02`) leaves it untouched: **0/24 vs 5/24,
  p = 0.0248**. `vg`'s failures are deep (min **−0.27 m**), not marginal grazes. Robust against
  under-detection; it is *over*-detection (`d ≥ +0.01`) that erases it, and there both arms read
  as colliding (13/24 vs 17/24, p = 0.19).
- **✅ Radius-robust, and it strengthens.** `stock` is **0/24 at all four radii**; `vg` is
  **2 / 5 / 4 / 7** of 24 at r = 0.25 / 0.30 / 0.35 / 0.40 (p = 0.24 / **0.025** / 0.055 /
  **0.0047**). Direction never reverses — a **second invariance axis** on top of 04:00's
  temperature invariance. Under-powered at r = 0.25, so the effect is radius-gated at the low end.
- **🔴 On this scene the effect is entirely in the TAIL.** Drop the 5 seeds where `vg` collided
  and the remaining 19 are statistically indistinguishable: paired median **+0.0105 vs +0.0079**,
  Wilcoxon **p = 0.14**. The restriction produces rare catastrophic failures, not a systematic
  margin loss — any mean/median margin metric would report nothing here.
- **✅❌ Second scene: the metrics swap roles.** `cafe_blind_corner_v0`: collisions **0/24 in both
  arms, Fisher p = 1.0** — the binary metric sees *nothing*. But min-clearance is degraded **3×**:
  median **+0.130 → +0.045**, paired Wilcoxon **p = 4.2e-07**. The representation effect is
  emphatically there; `collision_rate` is simply blind to it.
- **⚠️ Part C carries the speed confound inverted.** On the corner scene `vg` runs at **0.121 vs
  0.246 m/s — half speed** (both arrive: d_goal 0.039 / 0.040). So the gated arm buys its 0/24 by
  creeping. The corner-scene collision *null* is therefore uninterpretable without a speed
  control; only the clearance result stands — and it stands harder for it, since the **slower**
  arm still gets **3× closer**.

## North-star delta

- **The surviving P3 result broadens from one scene to two — but only under a different metric.**
  Restricting what the planner can see degrades safety margin on *both* occlusion scenes; it
  moves the collision count on only one.
- **Direct measured answer to Q-021, and it is worse than Q-021 assumed**: `collision_rate`
  detects the effect on scene 1 (p = 0.025) and misses it on scene 2 (p = 1.0); `min_clearance`
  detects it on scene 2 (p = 4e-7) and misses it on scene 1 off-tail (p = 0.14). **Neither is
  sufficient alone.** A P5 harness needs a tail statistic *and* a central-tendency statistic,
  because the same defect expresses as a tail on one geometry and a shift on the other.
- **Net honest position**: 04:00's headline survives three invariance tests (temperature, contact
  threshold, planning radius) and is the strongest evidence the project has. Its *interpretation*
  narrows: the control arm is not safe, it is non-penetrating.

## Key learnings

- **"0 collisions" is not "safe" — check the margin the zero was bought at.** A control arm that
  grazes at 1 cm on every seed is at the same operating point as the treatment arm; only the tail
  differs. Reporting the count alone hid that for two cycles.
- **A binary outcome and a continuous margin are not two views of one metric — they are sensitive
  to disjoint failure modes.** This cycle is the existence proof: two scenes, two metrics, each
  metric null on the scene the other detects.
- **The cheapest robustness test available was free.** B1 required no re-simulation — the contact
  threshold is a post-hoc scoring parameter. Every binary-outcome claim in this project can be
  swept this way at zero cost, and should be before it is reported.
- **A scene whose oracle has no headroom cannot separate "avoids" from "does not penetrate".**
  `cafe_blind_approach_v0` acceptance sets `min_distance_to_obstacle: 0.0` and the tightest oracle
  seed meets it by **3 mm**. → **Q-027**.

## Recommended next 1–3 priorities

1. **Report clearance distribution (min / q25 / median + tail count) wherever a collision count is
   reported** — supersedes and subsumes STATE item #2's goal-reached assertion; both are "the
   count is not the claim".
2. **Land `test_ess_within_admissible_band` (two-sided)** — unchanged from 04:00, still the one
   instrument that would have caught both broken temperatures.
3. **Re-scope `cafe_blind_approach_v0` so the oracle has real headroom** (raise the barrier weight
   or widen the corridor) — otherwise the scene measures barrier stiffness, not avoidance.

## Artifacts

- PR: none — gate 1 (pr-queue-full = 6, 24th consecutive)
- Files touched: none committed. Source `/tmp/proto_0802_05/_knife.py`, raw
  `/tmp/proto_0802_05/knife.json`; scratch merge reused at `/tmp/scratch_p3merge`
- TSV row appended: no
- Q raised: **Q-027** — is a scenario admissible as a safety test-bed when its *oracle* arm rides
  the barrier at 1 cm on every seed? (not self-authorized)
