# Q-049's table says the four weights aren't one class — and the denominator was the finding

- **Cycle**: 2026-08-03 06:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic` (24th consecutive cycle into queued PR #67)
- **TODO**: STATE #2 — measure the four shipped critic weights as multiples of baseline cost spread (Q-049)
- **Phase**: P3
- **Status**: keep

## What I tried

- Built `eval/mppi_sandbox/weight_units.py`: leave-one-out cost decomposition by
  **toggling a weight to 0 and re-evaluating the real `_cost`** — exact, since
  `cost(w) − cost(0) = w·f(traj)`, and it cannot drift from the controller the
  way a re-implemented cost formula would.
- Denominator is `rest = cost − w·f`, not the total, so a term is never priced
  against a baseline containing itself. That makes one statistic well-defined
  for add-on critics *and* baseline-internal terms (`w_terminal`).
- Declared `REPORTING_STATISTIC = "median"` **before** dividing (D-024's mistake
  class), and returned both so callers can check the choice on their own scene.
- Ran the table on `cafe_obstacle_crossing_v0` at `lam = 1.6` (D-027's
  temperature) for four arms: healthy baseline, `w_risk = 40` default,
  `w_epist = 200`, `w_voo = 200`.

## What worked / what failed

- 🔴 **Q-049's four knobs are not one class, so the question it asked has no
  single answer.** `w_terminal = 30` → **0.328**, the only live plain additive
  coefficient. `w_risk = 40` → **0.064**. `w_epist = 200` → **exactly 0** (it
  multiplies a term whose spread is identically 0 — D-021 re-derived by a
  general instrument rather than quoted). `k_margin_per_sigma` → **undefined**:
  it is not a coefficient at all but a shift *inside* `exp(-clear/scale)` and
  the `clear < 0` indicator, so its unit is metres. The units hazard is real
  but narrow.
- 🔴 **The generalisable finding is the denominator, not the numerator.** Same
  `w_voo = 200`, same scene, same `lam`: **6.19×** against the baseline it is
  added to, **1.46×** against the arm carrying it — a 4.2× understatement. The
  mechanism is worse than a scale error: at `w_voo = 200` the run **never
  completes** (1000 steps vs the baseline's 114), so it spends most of its life
  off-path and `w_path`'s own spread inflates **11.6×** (48.1 → 555.7), lifting
  the denominator 79.09 → 862.6. **A weight measured on its own arm is graded
  against the wreckage it caused, and the worse it is the better it looks.**
- ✅ **My first stated mechanism for that was wrong and the test now excludes
  it.** I expected `w_collision = 1e4` to wake up and swamp the denominator.
  Measured: its median spread is **exactly 0 on both arms** — even the derailed
  one, where it fires only intermittently (mean 2210, median 0). The repo's
  largest weight by 250× is a guard, not a competitor. The real competitor is
  `w_path = 20` at ratio **2.42**: the baseline landscape *is* path tracking.
- ✅ **The ratio's precondition holds exactly, and the measurement still doesn't
  transfer.** On a fixed rollout batch, per-unit spread is constant to machine
  precision for every additive coefficient (ratio 1.000000). `k_margin_per_sigma`
  swings **2.57×** over 0.05–0.4 on a batch placed inside the shadow. But in
  *closed* loop `w_voo`'s per-unit spread reads **2.50 / 2.34 / 5.30** at
  w = 1 / 7 / 200, because a different weight steers to a different state
  sequence. So: linear algebra, non-extrapolable measurement — measure at the
  weight you intend to ship.
- ⚠️ **A fourth independent confirmation of D-021's gate, unlooked-for.**
  `k_margin_per_sigma` measures identically 0 in closed loop on this scene for
  the same reason `w_epist` does — the rollouts never reach a σ > 0 cell. Its
  non-additivity is only demonstrable on a synthesised shadow batch
  (`shadow_batch`), which is why that helper exists.
- ⚠️ I initially wrote §2 from a `lam = 0.1` run while the tests ran at
  `lam = 1.6`; at the shipped `lam` the verdict actually *flips* (0.049× vs
  6.19×) rather than merely understating. Only the `lam = 1.6` pair is
  measured on both arms, so that is what shipped — the flip is unverified.

## North-star delta

- **No avoidance or tracking number moved** — this is a pure measurement module
  and no repo default changed. Honest zero on the north star's own metrics.
- What it buys is a **precondition for the head-of-line item**: STATE #1 wants a
  `lam` window calibrated for an arm carrying `w_voo`, and that sweep is only
  meaningful once the weight is stated in units that don't flatter themselves.
  This cycle says which weight to calibrate for, and why the naive one is not it.
- Reportable matrix unchanged at **4** scenes.

## Key learnings

- **A ratio is a pair, and the denominator is where the mistake lives.** I spent
  the cycle assuming the interesting question was "how big is the numerator" —
  D-027 framed it that way and so did Q-049. The measurement that mattered was
  which *arm* supplies the baseline, and it inverts the incentive: a weight bad
  enough to derail a run inflates its own denominator.
- **Rank the mechanism before writing it down** — the same lesson as 08-03 04:00,
  hit again. "Collision term wakes up" was plausible, ~250× the next weight, and
  wrong; one leave-one-out row killed it. It is now a *negative* assertion in the
  test file so the next reader can't re-adopt it.
- **State the temperature with the ratio.** Two arms measured at different `lam`
  produced numbers that disagreed by 30× and I nearly shipped them as one table.
- **Declaring the statistic is cheap; discovering you needed it is not.** median
  79.09 vs mean 3806.8 on one scene.

## Recommended next 1–3 priorities

1. **Calibrate a `lam` window for a `w_voo` arm at a scale-matched weight**
   (STATE #1, now well-posed): use `spread_per_unit_weight` on the *baseline*
   arm to pick the weight, not the arm carrying it.
2. **Re-measure the self-vs-baseline denominator gap at the shipped `lam = 0.1`**
   — the exploratory read suggests the verdict *flips* there (0.049× vs > 1),
   which is a stronger claim than the 4.2× understatement that shipped.
3. **Decide whether baseline-spread ratio becomes the reporting format** for
   every weight sweep, or stays an on-demand instrument. D-028 shipped the
   instrument and moved no default.

## Artifacts
- PR: #67 (already queued — no new review bandwidth consumed)
- Files touched: `eval/mppi_sandbox/weight_units.py`, `eval/mppi_sandbox/tests/test_weight_units.py`, `docs/decisions.md` (D-028), `docs/deliberations.md` (Q-049 → resolved), `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV row appended: yes
