# The predicted-geometry arm was not inert — 0.007 m → 0.382 m worst-case clearance at no completion cost

- **Cycle**: 2026-08-12 13:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: research-feed 2026-08-12 04:00 — port PGIF's cost term only (2608.08323)
- **Phase**: P3
- **Status**: keep

## What I tried

- Broke an **18-cycle instrument-only streak** deliberately. STATE's four
  next-actionables were all instrument repair; Phase 0's feed carried a
  capability item the feed itself framed as *this branch's third arm* — "PGIF is
  predicted geometry, the min-clearance null is static geometry, and the shadow
  cost is neither — same 2×2". D-016's sandbox-executable bias resolves that tie.
- Ported the **cost term only** from arxiv 2608.08323 as
  `critics/predicted_geometry.py`: a speed-scaled anisotropic Gaussian at each
  pedestrian's *predicted* pose, `σ_∥ = 1.2 + 0.5·s` ahead / `0.5` behind,
  `σ_⊥ = 0.6`. Wired as `RiskMPPI(w_ped=…)`, default `0.0` → exact no-op.
- Took the 6-seed paired reading on `cafe_obstacle_crossing_v0` that the feed
  made a condition of the borrow: clearance **and** completion, never clearance
  alone.

## What worked / what failed

- 🟢 **The term is audible at the first weight tried** — and that was the open
  risk, not a formality. `ShadowCostCritic` shipped into this same branch and was
  later measured *signal-free* (D-021: byte-identical trajectories at
  `w_epist = 200`, per-sample spread exactly 0.00 at all 92 control steps). The
  arm test asserts non-inertness directly, so the D-021 discovery that cost that
  critic several cycles costs this one 5 s.
- 🟢 **The reading is large and it is not bought with a freeze.** 6 seeds at
  `lam = 0.8`, `w_ped` 0 → 50: min clearance median **0.071 → 0.434 m**,
  worst-case **0.007 → 0.382 m**, completion **6/6 → 6/6**. The baseline is
  *grazing* the pedestrians — 7 mm at worst — and the arm holds a third of a
  metre while still reaching goal on every seed.
- 🔴 **The census caught the first version of that number and it was right to.**
  I first measured at the shipped `MPPIParams.lam = 0.1` and got a bigger,
  prettier result (0.022 → 0.517 m). `test_default_lam_sites` then billed my two
  `make_controller` sites **+2 `defaults`** — and what the bill was pointing at
  is that at `lam = 0.1` the softmax has median ESS ~1 of 256, a *greedy argmin*.
  Both my assertions are about trajectory *difference*, so at that temperature
  the non-inertness test is satisfied by noise and the clearance number is taken
  from a planner that is not averaging. Naming `LAM = 0.8` shrank the headline by
  ~20 % and is the first version of it that means anything.
- 🔴 **That is still one scene, one weight, 6 seeds, no CI** — and the freezing
  tax the source paper documents appears at *density*, which this scene does not
  have. The paper's own Hard level converts an 82 % collision rate into a **59 %
  timeout** rate. `6/6` is evidence the tax is not being paid at this density; it
  is not evidence that it will not be.
- 🔴 `inert_surface staged` said "this cycle added a reader" for the **fourth
  consecutive cycle**, and `entrants()` again names D-203/D-211/D-214's files
  (`test_receipt_store`, `test_suite_shard`, `test_quoted_counts`,
  `test_guard_reflexivity`) — none of them mine. Refuting it cost two commands,
  as it has every time.

## North-star delta

- **First capability movement in 18 cycles.** A new cost critic + a runnable arm,
  on 물체회피 (dynamic class) — measured, not specified.
- Worst-case clearance on a pedestrian-crossing scene goes from **7 mm to 382 mm**
  with zero completion loss on the seeds run. Directly the north star's "물체회피"
  half, and the first number this branch has produced that moves it.
- The branch's arm set now spans the axis it was missing: *neither* (shadow),
  *geometry now* (geometric null), *geometry predicted* (this). The attribution
  question D-166/`geometric_null` opened is now answerable with three arms
  instead of two.

## Key learnings

- **The feed's framing was load-bearing and I nearly missed it.** The entry did
  not propose a new thrust — it proposed the third arm of the comparison this
  branch is already running, which is what let a capability item pass the
  one-thrust-per-branch rule and D-140's gate-1 reading simultaneously. A
  capability pick was available the whole time; 17 prior cycles read the
  candidate pool as STATE's list alone.
- **Non-inertness is a precondition, not a result, and it is cheap to assert.**
  D-021 discovered a signal-free critic *after* spending comparisons on it. One
  `assert not np.array_equal(baseline, weighted)` in the arm test converts that
  into a 5-second check that fails loudly at build time.
- **Refusing the oracle is what makes the arm gradeable.** The source paper
  predicts its orbital pedestrians with the simulator's own kinematics, so its
  prediction error is identically zero. Using CV extrapolation instead makes this
  port *worse* than the paper on paper — and it is the only version whose number
  means anything against a real tracker.
- The `STAGED_MOVED` message has now been hand-refuted four cycles running at
  identical cost each time. It is still STATE #1 and it should stop being carried.

## Recommended next 1–3 priorities

1. **Run the three-arm head-to-head** — shadow / geometric-null / predicted-geometry
   at matched λ and paired seeds, on the eligible scenes, reporting timeout rate
   beside clearance. The arm exists now; `geometric_null.versus_geometry` is the
   harness and it already does paired CIs.
2. **Find the density where the freezing tax appears** — sweep `w_ped` on
   `cafe_convoy_v0` / `cafe_freezing_v0` and locate the knee where completion
   starts falling. The 6/6 above is a floor reading, not a safety result.
3. Fix `inert_surface`'s `STAGED_MOVED` message to name what it measured
   (carried, fifth cycle — `entrants()` already returns the names).

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic, PR #67)
- Files touched: `eval/mppi_sandbox/critics/predicted_geometry.py`,
  `eval/mppi_sandbox/critics/__init__.py`,
  `eval/mppi_sandbox/controllers/risk_mppi.py`,
  `eval/mppi_sandbox/tests/test_predicted_geometry_critic.py`,
  `eval/mppi_sandbox/tests/test_predicted_geometry_arm.py`,
  `docs/decisions.md`
- TSV row appended: yes — `sandbox:clearance=0.382`, status `keep`
- Suite: **2607 passed / 158 skipped / 1 xfailed** in 489.69 s across 14 shards (rc=0)
