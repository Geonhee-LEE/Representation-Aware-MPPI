# The freeze price is void at the paired lam — and the grid ends before the answer

- **Cycle**: 2026-08-13 22:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `STATE#1` Re-run the `freeze_weight` sweep at `PAIRED_LAM = 0.8`
- **Phase**: P5
- **Status**: keep

## What I tried

- Ran the shipped `freeze_weight` sweep at `--lam 0.8` — the temperature every
  paired comparison on this branch runs at — against the same 8-point grid and
  the same 12 paired seeds D-244 used at `lam = 0.1`. 96 runs, ~6 min.
- Read the verdict, the tolerance ladder, and the per-cell trend.
- Shipped the one instrument change the reading demanded, plus its tests.

## What worked / what failed

- **The D-243/D-244 setting is void at the paired temperature, not shifted.**
  `3e3` and `1e4` — D-244's `PLATEAU width=2` — are **12/12 exceed** at
  `lam = 0.8`, median longest stall **82.15 s / 64.15 s** against the scene's
  declared **2.0 s**. Verdict `NONE_ADMISSIBLE`, and unlike D-244's knife edge
  it is **threshold-robust**: all four rungs of `EPS_LADDER` agree, so no
  clearance tolerance rescues it.
- **The binding clause changed, which is why the ladder is silent.** At
  `lam = 0.1` the interesting failure was clause 3 (freeze bought with
  clearance). At `lam = 0.8` *every* cell fails clause 1 (`n_exceed == 0`), so
  the clearance clause is never active and the ladder has nothing to move.
- **The grid ran out while the term was still working.** Top three cells:
  `1e4 → 12/12`, `3e4 → 8/12`, `1e5 → 6/12`, median longest `64.15 → 6.65 →
  2.05 s`. The best cell measured is the **last** one, and `1e5`'s median has
  essentially reached the limit. `NONE_ADMISSIBLE` is true but under-informative
  — it reads as "no weight buys the freeze" when the measurement only supports
  "no weight *in this grid* does."
- So I split it: **`NONE_ADMISSIBLE_TREND_OPEN`** when the admissible set is
  empty *and* the top cell strictly improves on its neighbour. This is the
  inadmissible-side twin of the `EDGE_OPEN` guard the module already had on the
  admissible side — the same over-claim, in the direction nobody had guarded.
- **Small weights do nothing but jitter.** `1e2 / 3e2 / 1e3` all stall as long
  as the ablation while reading *higher* worst-case clearance than it
  (0.9417 / 0.9433 / 0.9588 vs 0.9372) — consistent with the term being far
  too weak to change the trajectory at this temperature.
- **The census fired again (15th consecutive cycle), in the earned direction.**
  The new measured pin names its rung, so `decides` 91 → 92 with `defaults`
  held at 61 — fifth consecutive earned nil. Also corrected an internal
  inconsistency in D-244's own census narrative: it recorded `(92, 61, 32)`
  against `total 184`, but that triple sums to 185 and the pin it described
  read `(91, 61, 32)`.

## North-star delta

- **A shipped setting was withdrawn on measurement, which is movement.**
  `w_freeze ∈ {3e3, 1e4}` cannot be quoted at the temperature the branch's
  clearance results live at. Nothing regressed; a claim that was not yet earned
  stopped being made.
- **+1 verdict the harness can distinguish.** The freeze-pricing instrument can
  now separate "measured failure everywhere" from "grid exhausted mid-trend" —
  the difference between a result and a budget.
- No movement on obstacle avoidance or path tracking themselves. This is a
  measurement-methodology cycle on the freezing scene.

## Key learnings

- **A weight is not a setting until it is measured at the temperature it will
  be quoted beside.** D-243 → D-244 → D-245 is three cycles of the same claim
  getting narrower: first n=3 → n=12 deflated it, then the tolerance ladder
  reframed it, now the temperature voids it. The number was never wrong; the
  scope attached to it was.
- **`NONE_ADMISSIBLE` was doing two jobs.** Any verdict that can be reached
  both by walking the whole space and by running out of budget will get read as
  the former. That shape is worth looking for in the other verdict enums here.
- **The next grid point is the cheap experiment.** `3e5` / `1e6` at `lam = 0.8`
  is ~24 runs, and it decides between "the term works, the grid was short" and
  "the term genuinely cannot buy this freeze without paying clearance" — since
  clearance is already sliding (0.9372 → 0.8537 across the grid), the honest
  prior is that the admissible set is empty for a *reason*, not for a budget.

## Recommended next 1–3 priorities

1. Extend the grid upward (`3e4, 1e5, 3e5, 1e6`) at `lam = 0.8` and resolve
   `NONE_ADMISSIBLE_TREND_OPEN` into a real verdict.
2. Implement `time_to_goal` as first-arrival time — a 12/12 `reached` beside an
   82 s stall is the fourth appearance of the same blindness.
3. Ask whether the ablation is a fair denominator at this temperature: a
   baseline frozen ~90% of the run earns its clearance by not moving, so clause
   3 may be structurally unwinnable once clause 1 is satisfied.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic, #67)
- Files touched: `eval/mppi_sandbox/freeze_weight.py`,
  `eval/mppi_sandbox/tests/test_freeze_weight.py`,
  `eval/mppi_sandbox/tests/test_default_lam_sites.py`
- TSV row appended: pending
