# The baseline is not slow — its speed is decoupled from `target_speed_mps`

- **Cycle**: 2026-08-02 02:00 KST
- **Branch**: none — gate 1 (pr-queue-full=6), 21st consecutive skip
- **TODO**: none picked; took STATE item #2 (queue-free measurement)
- **Phase**: P3 (calendar P4)
- **Status**: keep (uncommitted — gate 1)

## What I tried

- 01:00 left a confound: the `vg` baseline runs at **mean v = 0.441 vs a 0.9
  target**, so every duration comparison of the last four cycles sits on a
  baseline at 49 % of its own target. Goal: find the mechanism, not just the number.
- Built an **open-loop positive control** (command `(target, 0)` every tick, no
  MPPI) to establish whether the plant can reach the target at all — without it,
  "the controller is slow" cannot be distinguished from "the sim is slow".
- Swept `target_speed` × {open-loop, stock}, then tested four mechanisms:
  clip-bias in the noise update (H2), speed-weight starvation (H3), softmax
  degeneracy (H4), and an adaptive-temperature fix. All n=8 seeds for the claims.

## What worked / what failed

- ✅ **Positive control is clean**: open-loop reaches 0.199 / 0.394 / 0.582 / 0.761
  for targets 0.2 / 0.4 / 0.6 / 0.8. The plant and the acceleration limits are
  not the constraint (`v_max = 0.8`, so 0.761 is the ceiling; the yaml's 0.9 is
  **unreachable by construction** — a second, separate bug).
- 🔴 **The framing "49 % of target" was wrong, and too kind.** Realized speed is
  nearly *independent* of the target: as target goes 0.2 → 0.9 (4.5×), stock
  mean_v goes 0.372 → 0.441 (1.2×). At target 0.2 the robot runs **1.86× too
  fast**; at 0.9, 0.49× too slow. `target_speed_mps` is close to decorative.
- ✅ **Mechanism 1 — softmax degeneracy.** Median cost spread / `lam` ≈ **600–1240**,
  so `exp(-Δc/λ)` is effectively argmin: **ESS ≈ 5.3 of 256 samples** (98 % of the
  sample budget discarded). At `lam=100`, n=8: mean_v **0.441±0.007 → 0.710±0.004**,
  duration **15.71 s → 9.71 s** (open-loop ideal 9.1 s), `cte` 0.016 → 0.032 —
  both far inside the 0.2 acceptance floor. Survives on an obstacle scene
  (`probe_on_path_v0`, n=8): 0.440 → 0.701, 16.05 s → 9.96 s.
- ❌ **Mechanism 1 is not the whole story.** No fixed `lam` both tracks the target
  and holds `cte`: `lam=100` overshoots at target 0.4 (1.25×), `lam=1000` tracks
  well (1.12/1.03/0.99/0.83) but blows `cte` to **0.45** and times out. An
  **adaptive** `lam = spread/κ` (κ=3, ESS held constant) matched `lam=100` and did
  **not** fix the low-target overshoot (target 0.2 → **2.18×**).
- 🟡 **Mechanism 2, unfixed**: `w_terminal·dist²` (30) dominates `w_speed·Σ(v−v_ref)²`
  (2) at low targets, so the controller is paid to rush regardless of `v_ref`.
  Raising `w_speed` 100× moves mean_v only 0.441 → 0.591 and multiplies `cte` by 6.
- ⚠️ **H2 (clip-bias) is real but minor**: substituting the *realized* perturbation
  (clipped control − U) for the raw noise in the update gains +0.06…+0.13 mean_v.
  A genuine correctness bug in `stock_mppi.command`, not the main effect.
- ❌ **Could not re-check the four-cycle headline.** Re-running `horizon_slow` vs
  `EpistemicVGMPPI` at `lam=100` needs `visibility_gated_mppi`, which exists only
  on unmerged PR #69. Deferred rather than rushed — it needs the scratch-worktree merge.

## North-star delta

- **A real, measured defect in the baseline every P3/P5 number is referenced to**:
  the planner discards 98 % of its samples, and its speed is set by cost-term
  ratios rather than by the scenario's speed knob. This is upstream of the metric set.
- **A candidate fix with an effect size 30 SEM wide** (`lam=100`: +61 % mean_v,
  −38 % duration, `cte` still 6× inside acceptance), reproduced on two scene families.
- **Negative movement on trust in the last four cycles' timing results**: they were
  all measured at ESS ≈ 5/256, and the arm that beat the "epistemic" controller
  (`horizon_slow`) is itself a speed-shaping intervention. Ordering unverified.

## Key learnings

- **The positive control changed the question.** Open-loop hitting 0.761 is what
  turned "the baseline is slow" into "the baseline ignores its target" — the
  sweep, not the single point, carried the information. Second cycle running that
  the control arm is where the finding actually is.
- **A tuning constant can be a correctness bug.** `lam=0.1` reads like a taste
  parameter; at spread/λ ≈ 10³ it silently converts MPPI into random search. Any
  MPPI in this repo should report ESS as a first-class diagnostic, not a debug print.
- **Two defects hid behind one symptom.** The temperature fix removes the
  high-target deficit and leaves the low-target overshoot untouched — if I had
  stopped at `lam=100` looking good at target 0.9, I would have shipped a
  half-fix and called the baseline healthy.
- **Timing metrics were never comparable across scenarios** with different
  `target_speed_mps`, because realized speed barely depends on it.

## Recommended next 1–3 priorities

1. **Re-run the four-arm comparison at `lam=100`** (needs the #66→#69 scratch merge).
   Until then, no duration claim from 23:00/00:00/01:00 should be treated as live.
2. **Land `test_ess_is_not_degenerate`** — assert ESS ≥ some fraction of `samples`
   for every registered controller. Same shape as 01:00's sensitivity probe:
   a cheap, seed-free, registry-parameterised invariant.
3. **Fix `stock_mppi.command` to use the realized perturbation** in the weighted
   update (H2) — small, self-contained, unambiguously a bug.
4. Reject `target_speed_mps > v_max` at scenario load (probe scenes ask for 0.9
   against a 0.8 limit).

## Artifacts
- PR: none — gate 1 blocks the branch (21st consecutive skip)
- Files touched: none in-repo; probe source + raw JSON in `/tmp/proto_0802_02/`
  (`_speed.py`, `_ess.py`, `_seeds.py`, `_adaptive.py`, `speed.json`, `ess.json`,
  `seeds.json`, `adaptive.json`, `onpath.json`) — reproducible cold
- TSV row appended: no (no branch to append to)
