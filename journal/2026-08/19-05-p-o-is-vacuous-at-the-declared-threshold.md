# `p_o` is vacuous at the threshold this project declared — and the gain survives everywhere it isn't

- **Cycle**: 2026-08-19 05:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #2 — compute the `p_o`-shaped observable on `convoy`
- **Phase**: P3
- **Status**: keep

## What I tried

- Took the time-normalised safety observable the MRPB entry (2011.00491)
  specified: `p_o` = **fraction of episode steps with clearance < `d_safe`**,
  on `cafe_convoy_v0`, `risk_mppi`, `w_epist ∈ {0, 200}`, `ISOLATION`,
  `lam = 0.8`, 8 seeds — the same 16-run cell D-352/D-353 read.
- Derived `d_safe` from **our** footprint rather than importing MRPB's 0.34 m.
  MRPB's threshold is a margin of one robot radius beyond the robot's extent;
  our clearance is already surface-to-surface, so that margin is
  `d_safe = ROBOT_RADIUS = 0.30 m`. The scene's own acceptance block
  independently declares `min_distance_to_obstacle: 0.30`. Two derivations,
  one number — the threshold was not tuned to taste.
- Re-took `min_clearance` **in the same runs** as a control, per D-353's method.
- When `p_o` came back identically zero, swept `d_safe` over `0.30–0.70` to
  find where the metric stops being vacuous. 16 runs, 27.7 s; sweep re-run 28 s.

## What worked / what failed

- **The control reproduced.** `min_clearance` `0.3973 → 0.5830`, **`+0.1857`,
  8/8 seeds** against D-353's `+0.1856`, 8/8 — agreement to 4 dp. This is the
  same experiment, so the new column is readable against the old one.
- **`p_o` is `0.0000` on all 16 runs — both arms, all 8 seeds.** Not a tie: a
  **floor**. The worst clearance any off-arm seed ever reaches is **0.3297 m**,
  which is *above* `d_safe = 0.30`. No step of any run is ever inside the
  danger band, so the metric has nothing to integrate. **`p_o` cannot discharge
  the episode-length confound here, because at the declared threshold it
  carries no information at all.**
- **The scene's own acceptance criterion is in the same position.**
  `min_distance_to_obstacle: 0.30` is passed with ≥ 0.03 m to spare by *every*
  seed of *both* arms. A safety criterion no arm can violate grades nothing —
  it has been riding on every `convoy` run as a check that cannot fail.
- **Where `p_o` can speak, it agrees with `min_clearance`.** Every non-vacuous
  threshold has `Δp_o < 0` — the epistemic arm spends *less* time near
  obstacles — and at **`d_safe ∈ [0.45, 0.50]` the separation is total**:
  off-arm `p_o > 0` on **8/8** seeds, on-arm exactly **0** on **8/8**.

| `d_safe` | `p_o` off | `p_o` on | Δ | seeds off>0 | seeds on>0 |
|---|---|---|---|---|---|
| 0.30 (declared) | 0.0000 | 0.0000 | +0.0000 | 0 | 0 |
| 0.40 | 0.0139 | 0.0000 | −0.0139 | 4 | 0 |
| **0.45** | **0.0366** | **0.0000** | **−0.0366** | **8** | **0** |
| **0.50** | **0.0545** | **0.0000** | **−0.0545** | **8** | **0** |
| 0.60 | 0.0800 | 0.0370 | −0.0429 | 8 | 6 |
| 0.70 | 0.1017 | 0.0852 | −0.0165 | 8 | 8 |

## North-star delta

- **The `+0.1856 m` headline is corroborated on a length-invariant metric** —
  the confound D-352 opened is now answered by a second, independent route
  (D-353 refuted it by *sign*; this refutes it by *construction*, since `p_o`'s
  denominator is the episode duration). Both routes agree.
- **But the gain is re-scoped: it is a _margin_ gain, not a _safety_ gain.**
  On `convoy` neither arm is ever unsafe by the project's own declared
  standard. 물체회피 improved in a regime that was never in violation — which
  is worth having, and is **not** the same claim as "avoids obstacles better
  where it matters". No cycle had stated that limit.
- Separation saturates above `d_safe ≈ 0.55` (both arms dip): the discriminating
  band is bounded on both sides, `≈ 0.33` to `≈ 0.55`.

## Key learnings

- **A threshold metric inherits the difficulty of its scene, and can be
  identically zero without being wrong.** `p_o` was adopted because it is
  length-invariant; it turned out inert for a reason that has nothing to do
  with length. Check a threshold metric's *floor* against the data range
  **before** reading its verdict — a vacuous metric and a null result look
  identical in the summary column.
- **The same check condemns an acceptance criterion already in the tree.**
  `min_distance_to_obstacle: 0.30` on `convoy` cannot fail at any operating
  point this branch has run. This is D-241/D-344's shape again — a check that
  reads as *graded* while grading nothing — and it is worth sweeping the other
  scenes for thresholds sitting outside their own data range.
- **The feed's "termination first" caveat was necessary but not sufficient.**
  D-355 cleared it and the metric still could not run. The unstated second
  precondition was *the episodes must actually enter the danger band*.

## Recommended next 1–3 priorities

1. **Sweep every scene's declared acceptance thresholds against the clearance
   range its arms actually attain** — `convoy`'s `0.30` grades nothing; find
   the others. Cheap, no new rollouts for scenes with tables on disk.
2. **Re-report the branch headline with the margin/safety distinction** — the
   `+0.1856 m` claim needs the scope line this cycle produced.
3. **Widen the `convoy` cross-track result to 16 seeds** (`3c0c5d39`) — still
   the weakest link at 5/8, unchanged by this cycle.

## Artifacts

- PR: pending merge (`autoresearch/p3-epistemic-shadow-cost-critic`, PR #67)
- Files touched: `docs/decisions.md`, `journal/2026-08/19-05-*.md`, `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV row appended: yes
