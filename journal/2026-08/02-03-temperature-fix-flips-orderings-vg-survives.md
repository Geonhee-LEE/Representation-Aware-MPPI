# The temperature fix flips every duration ordering — and #69's collision result survives it, speed-controlled

- **Cycle**: 2026-08-02 03:00 KST
- **Branch**: none — gate 1 (pr-queue-full=6), 22nd consecutive skip
- **TODO**: STATE `Next claude-actionable` **#1** — re-run the four-arm comparison at `lam=100`
- **Phase**: P3
- **Status**: in_progress (uncommitted; gate 1 blocks the branch)

## What I tried

- Built the **`#66→#67→#68→#69` scratch merge** 02:00 lacked (`visibility_gated_mppi` is on #69 only,
  not on main). Merge recipe re-verified a **12th** time: one conflict, #66↔#67, on
  `test_risk_mppi.py` + `docs/deliberations.md`, resolved in favour of #66; #68/#69 clean.
  **44/44 sandbox tests pass on the merged tree** — including #67's, whose PR CI is red, confirming
  #67's redness is environmental (numpy pin), not a code defect.
- **Re-ran the four-arm comparison at `lam=0.1` vs `lam=100`**, n=8 seeds, with per-arm **ESS
  instrumentation** (02:00 measured ESS on `stock` only) and a `target_speed 0.7` variant, since
  02:00 found the probe yamls ask 0.9 of a `v_max=0.8` plant.
- **Re-ran PR #69's own headline** (`cafe_blind_approach_v0`, N=24, `sensing_range=1.0`) at both
  temperatures — the claim that occlusion moves a *collision* outcome, which the whole P3 epistemic
  track rests on.
- **Speed-controlled it**: swept a hard `v_max` handicap on `vg` down to where it runs *slower* than
  the oracle, to answer the objection that killed 22:00's claim.
- **Positive control**: `vg` + a max-decel reflex on reveal — same gated perception, different response.

## What worked / what failed

- **🔴 The orderings reverse.** `horizon_slow` vs `stock_vg` on `probe_on_path_v0`: at `lam=0.1`
  it is **−5.9 % faster** (15.10 vs 16.05 s) — that sign *was* the 00:00 headline. At `lam=100` it
  is **+11.4 % slower** (11.10 vs 9.96 s). Every duration-ordering conclusion from 23:00 / 00:00 /
  01:00 is measured on a broken instrument and does not survive.
- **ESS is arm-dependent, not just baseline-dependent.** At `lam=0.1`: `stock` 6.4/256, but the arms
  that *add* a cost term drop to **1.4/256**. At `lam=100` all arms sit at **210–225/256**. So adding
  a cost term at fixed `lam` silently makes the controller optimize *worse* — an ablation arm and its
  baseline are not running the same algorithm. This is a general defect in the ablation method, not
  a fact about these five arms.
- **✅ `proto_evg` ≡ `stock_vg` bit-for-bit in all four conditions** (as does `near_slow`). 01:00's
  inertness finding is **temperature-independent** and stands — it was established structurally
  (positive control on the cost term), not by outcome comparison. The one surviving finding of the
  last five cycles is the one that never used a duration.
- **✅ #69's headline survives and strengthens**: collisions `stock` **0/24** vs `vg` **6/24** at
  `lam=0.1`, and **0/24 vs 24/24** at `lam=100`. The degenerate softmax was *understating* it.
- **✅ …and it is speed-controlled.** At `lam=0.1` the result was confounded (`stock` crawled at
  0.279 m/s vs `vg` 0.439). Handicapping `vg` to `v_max=0.6` gives **mean_v 0.519 vs stock's 0.522 —
  `vg` is slower — and still collides 5/24 vs 0/24**, Fisher one-sided **p = 0.025**. The confound
  that killed 22:00's claim is removed by construction, not by argument.
- **⚠️ The effect is speed-gated.** `vg` collides 24/24 at 0.72 m/s, 5/24 at 0.52, and **0/24 at
  ≤ 0.42**. Below ~0.5 m/s the gate stops mattering.
- **⚠️ The oracle's margin is razor-thin**: `stock` clears with mean min-clearance **0.034 m**
  (min 0.015). "Oracle clears" is a 1.5 cm result, not a comfortable one.
- **❌ The collision is a *response* failure, not a perception-timing one.** Reveal geometry gives
  0.7 m of travel after the gate trips; at `accel_max=1.0` the braking limit is **v_crit = 1.18 m/s**,
  above `v_max`. The plant can stop in time at *every* achievable speed, yet `vg` collides at 0.52.
  The brake-on-reveal control confirms it directly: **0/24 collisions, clearance +0.40 m** where
  plain `vg` is −0.40 m at the same `v_max`. But it never reaches the goal (mean_v 0.08, 36 s
  timeout) — it brakes as long as the hazard stays visible.

## North-star delta

- **First speed-controlled representational safety result in the project**: at matched speed
  (0.519 vs 0.522 m/s), restricting *what the planner can see* moves collisions 0/24 → 5/24,
  p = 0.025. The core hypothesis has a measured instance for the first time; every prior attempt
  died on the speed confound.
- **A retraction of four cycles' timing conclusions**, and confirmation that PR #69 — queued 17 days —
  carries a real, now-stronger result. The queue is holding back a live finding, not just paperwork.
- **Two endpoints bracketing the P3 target, both unacceptable**: gated perception with the stock cost
  → 24/24 collisions; gated perception with a brake reflex → 0/24 but zero task completion. The
  epistemic cost function's job is now a measured gap, not a description.

## Key learnings

- **Structural probes survived the instrument bug; outcome comparisons did not.** 01:00's inertness
  finding used a positive control on the cost term and is temperature-independent. Every conclusion
  drawn from comparing durations across arms is now retracted. This is a strong argument for landing
  STATE items **#2** (`test_ess_is_not_degenerate`) and **#3** (`test_cost_term_reads_its_named_state`)
  before any further comparative claim.
- **A fixed `lam` is not a neutral setting across arms.** Because ESS falls when a cost term is added
  (6.4 → 1.4), "hold `lam` fixed and add a term" is not a controlled ablation. Sharpens Q-024 and
  raises **Q-025** below.
- **A blind-hazard scenario only discriminates inside a speed band.** Here it is ~0.5–0.8 m/s, set by
  reveal distance vs stopping distance. Outside it the scenario is uninformative in both directions.
  Every `blind_*` scene should declare the band it is testing in.
- **The observed onset (~0.5 m/s) is 2.3× below the braking limit (1.18 m/s).** The planner leaves
  most of its deceleration authority unused — 01:00's "the gate is representational, the response is
  not" is now quantified, and it is the same `w_terminal` vs `w_speed` imbalance 02:00 found.

## Recommended next 1–3 priorities

1. **Land the two instrument tests (#2, #3)** before any further comparative claim — this cycle is the
   second consecutive demonstration that they would have caught a live error.
2. **✅ Checked, no action — #69 is safe to merge.** Its assertion is a *lower* bound
   (`sum(c < 0.0) >= 1`) plus a mean comparison, and it runs at the default `lam`; the temperature
   fix moves the collision count **up** (6/24 → 24/24), so the test only gets more true. The one
   fragile spot is `test_run_scenario_reports_gated_collision`, which pins seed 4 deterministically —
   it will need revisiting if and when `lam` is changed project-wide (Q-024), not before.
3. **Q-025**: is a fixed-`lam` ablation admissible at all, given ESS is arm-dependent?

## Artifacts

- PR: none — gate 1 (pr-queue-full=6), 22nd consecutive skip
- Files touched: none committed. Source + raw JSON in `/tmp/proto_0802_03/`
  (`_recheck2.py`/`recheck2.json`, `_vg69.py`/`vg69.json`, `_speedctrl.py`/`speedctrl.json`,
  `_brake.py`/`brake.json`); scratch merge left at `/tmp/scratch_p3merge` (git worktree, detached)
  so the next cycle reuses it without redoing the conflict resolution.
- TSV row appended: no (no branch to append to)
