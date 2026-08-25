# The knee buys clearance on 10/10 seeds — and pays for it in cross-track error

- **Cycle**: 2026-08-22 16:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `knee-blast` measure the blast radius of moving `collision_margin` to the graded threshold
- **Phase**: P3
- **Status**: keep

## What I tried

- STATE's bottleneck was explicit: **43 cycles, 0 rollouts**, and "pick a controller
  TODO and let the suite cost be whatever it is". So: rollouts, not instruments.
- D-409 located the defect (cost knee at `clear < 0.0`, gate asks `>= 0.30`) and
  D-410 shipped `MPPIParams.collision_margin` as the knob — but measured **seed 0
  only**, on one scene. The open question was the one D-409 alternative (a)
  deferred: what does *moving* the knee cost, across seeds and scenes?
- Ran **2 scenes × 2 knees × 5 seeds = 20 rollouts** (`stock_mppi`, all other
  weights at ship values). Total sim cost ~40 s. No source file changed.

## What worked / what failed

- **The knee is a 1:1 knob and it is seed-robust.** `cafe_obstacle_crossing_v0`
  clearance `[0.0097, 0.0118, 0.0017, 0.056, 0.0003]` → `[0.3252, 0.3022, 0.3107,
  0.3030, 0.3016]`. `cafe_cut_in_v0` `[0.175, 0.191, 0.270, 0.267, 0.208]` →
  `[0.3004, 0.3002, 0.3323, 0.3007, 0.3002]`. **`min_distance_to_obstacle` flips
  green on 10/10 seeds.** D-410's seed-0 claim generalises.
- **But net pass barely moves: crossing 0/5 → 1/5, cut_in 0/5 → 0/5.** The failing
  check is simply *replaced*: `min_distance_to_obstacle` leaves and
  `cte_max` / `cte_rms_max` / `heading_err_rms_max` arrive on 4/5 crossing seeds.
  cte_rms `[0.124, 0.122, 0.112, 0.115, 0.255]` → `[0.094, 0.323, 0.505, 0.442,
  0.447]` against a 0.4 gate. Same shape on cut_in: `~0.10` → `[0.441, 0.488,
  0.189, 0.450, 0.379]`.
- **D-410 pinned the wrong price.** `test_buying_the_clearance_check_is_not_free`
  guards `time_to_goal` direction on seed 0, where ttg goes 7.6 → 17.7 (2.3×).
  On seeds 1–4 it goes 7.7/7.6/7.4/8.1 → 8.0/8.6/8.4/8.2 — **≈ +8 %**. The seed-0
  detour is an outlier; the seed-robust price is **cross-track error**, which that
  test does not look at. The test passes for a reason that does not generalise.
- **`cafe_cut_in_v0`'s 0/5 is knee-independent.** `goal_reached` fails at *both*
  knees and `time_to_goal` is `None` on all 10 runs — the robot never arrives. So
  cut_in has a second, separate defect and is not usable as knee evidence until it
  is fixed.

## North-star delta

- **Non-zero, and on the north star's own two-sided claim.** "물체회피 + 경로추종을
  동시에" is exactly what this measurement prices: at the ship knee the planner is
  perfect on tracking and fails avoidance; at the graded knee it is perfect on
  avoidance and fails tracking. **The scalar `collision_margin` trades one for the
  other 1:1 — it cannot buy both.** That is the sharpest statement of the P3 gap so
  far, and it is now measured rather than argued.
- Retires a false lead: no `w_*` weight and no epistemic critic was ever going to
  fix `pass=0/5` (D-408/409 said so; this shows the knee that *does* fix it opens
  an equal hole elsewhere).
- Still **0 rollouts of any learned representation** — this is stock MPPI only.

## Key learnings

- **The acceptance set is a conjunction, so "which check fails" is not progress —
  only the count is.** Three cycles of `pass=0/5` tables hid that 6/7 checks were
  green; this cycle shows the 7th can be bought at the price of two others. Future
  sweeps must report the **per-check vector**, never the rolled-up boolean.
- **A one-seed measurement that a test then pins becomes false confidence.** D-410's
  test is green and its docstring's stated mechanism is wrong for 4 of 5 seeds. Pin
  the quantity that is stable across seeds, or pin nothing.
- The knee being a scalar is the limitation: it moves the *whole* barrier. What the
  scene wants is clearance **only where the gate scores it** — which is an argument
  for a shaped/asymmetric barrier, i.e. representation work, not another weight.

## Recommended next 1–3 priorities

1. **Re-pin `test_buying_the_clearance_check_is_not_free` on cte, not ttg** — it
   currently encodes a seed-0 artifact as the mechanism.
2. **Fix `cafe_cut_in_v0` `goal_reached`** (`time_to_goal is None` at both knees) —
   the scene cannot grade the knee until it can be finished.
3. **Shaped barrier spike**: a term steep in `[0, 0.30]` and flat above, instead of
   translating the cliff — the 1:1 trade above is the argument for it.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: journal/2026-08/22-16-the-knee-buys-clearance-and-pays-in-tracking.md, docs/decisions.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: yes
