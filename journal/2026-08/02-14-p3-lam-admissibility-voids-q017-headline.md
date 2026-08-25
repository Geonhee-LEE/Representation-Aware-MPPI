# No shared temperature is admissible — and the first claim the guard voids is mine

- **Cycle**: 2026-08-02 14:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE claude-actionable **#1** — re-measure Q-017 at `lam = 5.0` under `assert_ess_in_band`
- **Phase**: P3
- **Status**: keep

## What I tried

- Pointed 13:00's per-seed `ab.assert_ess_in_band` at 12:00's own headline arm
  (`risk_mppi`, `offset = 0.3`, `lam = 1.2`, `w_epist` 200 vs 0) at n = 8.
- When that failed, swept **twelve** temperatures (0.8 → 5.0) over **both** arms at
  n = 8, recording per-seed ESS range, band compliance, completion, and paired
  clearance sign counts at each.
- Landed the result as `test_lam_admissibility_voids_q017.py` — 14 tests, CI cost
  bounded to a 3-point ladder (1.2 / 1.8 / 5.0), full table in the docstring.

## What worked / what failed

- 🔴 **12:00's headline temperature is void.** `lam = 1.2` has arm median ESS
  **28.95** — inside the Q-026 band — but per-seed range **7.5 – 59.0**, so 7/8 seeds
  comply and the arm does not. The failing seed is *inside* 12:00's original 3-seed
  ensemble; the median is what hid it.
- 🔴 **Re-picking `lam` does not rescue it — no shared temperature exists on this
  scene.** Twelve temperatures, both arms, never 8/8; best is 7/8 (at 1.2 and 1.8).
  The reason is a **width argument**, not insufficient sweeping: the band spans a
  factor of **10** (`0.05K … 0.5K`) and the per-seed spread reaches **18×** (lam 1.4).
  Where the spread *is* narrow (2.1–3.6× at lam 1.7–1.9, 2.3× at lam 3.0), the median
  has already climbed past the ceiling — the ESS-vs-`lam` curve is steep exactly where
  the spread is wide, and flat only after saturating near-uniform.
- 🔴 **STATE item #1's premise was wrong, not just its answer.** `lam = 5.0` was
  13:00's admissible value for **`stock_mppi` on a centred hazard**. Here — `risk_mppi`,
  `offset = 0.3` — it sits at median ESS **187**, *above* the ceiling of 128. Q-025 said
  a fixed `lam` is not controlled across scenes, 13:00 added seeds; this adds
  **controllers**, and the three interact.
- ✅ **The Q-017 (a) refutation survives, and is now much better supported.** Paired
  clearance sign counts never sweep the ensemble at **any** of the twelve temperatures —
  one-hot (0.8) through near-uniform (5.0), every arm completing. Only 12:00's
  *measurement* was void; its *verdict* rests on broader evidence than it originally had.
- ✅ Green and additive: 14 tests in a new file, no existing assertion touched → **#66
  merge recipe unchanged**. Suite **102 → 116 passed + 1 xfailed**, 81 s (new file 24 s).

## North-star delta

- **No movement on avoidance or tracking.** This cycle spent its budget invalidating a
  number, which is the guard from 13:00 paying for itself on the first claim it met.
- The standing caveat sharpens once more: the re-baseline that Q-032 defers now inherits
  a constraint it may not be able to satisfy — on at least one scene there is **no**
  `lam` that puts an A/B's two arms in band together. That is a precondition failure for
  the ablation protocol itself, not a tuning task.
- Q-017 (a) moves from "refuted at one admissible temperature" to "refuted across the
  whole measurable temperature range", which is the stronger and cheaper claim.

## Key learnings

- **A guard's first job is to void its author's own most recent result.** 13:00 shipped
  `assert_ess_in_band` and named this self-check priority #1; it fired immediately. The
  cheap version of this discipline — point every new instrument at the last headline
  before pointing it anywhere else — has now caught the same class of error three cycles
  running (mean paired gap, arm-median ESS, and now the headline `lam`).
- **When a tolerance band is narrower than the spread it must contain, the parameter is
  not mis-tuned — it is not a valid control.** Sweeping finer is the wrong response.
  Either the band needs an argument for widening (this repo has not made one), or the
  temperature is per-seed (and the arms stop sharing a controller), or the scene is
  retired as an ablation surface. **Q-035's lean was refuted from the measurement side.**
- **Admissibility is a property of the (scene, controller, seed) triple.** Three cycles
  each found one axis; the mistake each time was assuming the value transferred along
  the axes not yet tested. The next `lam` claim should state its triple explicitly.
- A verdict can outlive the measurement that produced it. Worth separating in reports:
  12:00's number is dead and its conclusion is stronger than before.

## Recommended next 1–3 priorities

1. **Decide the Q-035 fork before the re-baseline, not during it** — widen the band with
   an argument, calibrate `lam` per seed, or retire `offset = 0.3` as an ablation surface.
   The re-baseline (STATE #3) cannot pick a temperature until this is settled.
2. **Check whether the no-shared-`lam` result is scene-specific or general** — repeat the
   twelve-point sweep on the centred hazard and on `cafe_straight_v0`. If 13:00's
   `lam = 5.0` / `stock_mppi` compliance is the exception rather than the rule, the
   ablation protocol has a much larger problem than one scene.
3. **Q-034's upper end** stays open and is now cheaper to frame: near-uniform arms here
   *do* complete at `lam = 5.0` (unlike `lam = 30`), so the inadmissibility boundary sits
   between them.

## Artifacts

- PR: **#67** (pushed in place — no new review bandwidth), commits `27e602e`, `e6055e9`
- Files touched: `eval/mppi_sandbox/tests/test_lam_admissibility_voids_q017.py`,
  `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV row appended: yes (`sandbox:pass=116/116`, `keep`)
