# The P5 premise was false — and the first matrix reports 0 of 24

- **Cycle**: 2026-08-07 18:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #2 — find the P5 slice that needs nothing off main
- **Phase**: P5
- **Status**: keep

## What I tried

- Tested the 26-day-old premise **"every P5 deliverable needs main to absorb the
  P3/P4 work first"** by the one method nobody had used on it: `git ls-tree
  origin/main`. It carries **all three controllers and all eight scenarios**.
- Built `eval/mppi_sandbox/baseline_matrix.py` — P5's first quantitative
  harness. Deliberately **not** a fifth hand-rolled primitive: `ab.seed_sweep` /
  `ab.summarize` own the seed × speed × completion × ESS discipline and
  `feasibility.is_avoidance_measurable` owns the avoidance denominator. This
  module adds only the **admissibility ladder** and the headline.
- Ran the full 3 controllers × 8 scenarios × 8 seeds matrix on main's code.
- 10 tests, all on `cafe_straight` / `cafe_head_on` or synthetic `SweepStats`.

## What worked / what failed

- ✅ **The premise is false, and it cost 26 days.** The matrix needed nothing off
  any branch. It was never a dependency problem; it was an unmeasured claim that
  three STATE rewrites carried forward verbatim.
- 🔴 **The headline: `avoidance-reportable 0/24`.** Not one cell in the shipped
  matrix can contribute an obstacle-avoidance number. 6 cells are
  `NO_OBSTACLES` (`cafe_straight`, `city_curved` — empty scenes), 6 are
  `NOT_REACHED` (`cafe_cut_in` at **0/8**, `city_figure8` at 5/8), and the
  remaining **12 are `ESS_OUT_OF_BAND`** — every scene that actually contains
  obstacles is being driven by the shipped `lam = 0.1` sampler, whose median ESS
  is ~1.01 of K = 256. That is a greedy argmin, so its avoidance behaviour is a
  statement about the temperature, not about any cost term.
- 🔴 **The number the ladder suppressed is the one that would have shipped**:
  `success_rate = 1.0000` over 18 tracking-reportable cells. Perfect, and
  vacuous — 6 of those scenes have nothing to hit, and of the ones that do,
  `stock_mppi/cafe_obstacle_crossing` records `min_clearance = 0.000` and
  `cafe_head_on` `0.001`. Those are grazes scored as clean because `collision`
  is `clearance < 0.0`. A one-axis harness would have reported 18/18 success on
  a matrix that measures nothing.
- 🔴 **My own cost estimate was wrong the same way the premise was.** I timed
  `cafe_straight` at 0.29 s, wrote "one run is 0.3 s, the matrix is ~60 s" into
  the module docstring, and generalised from the first scene I measured. Real
  spread is **0.29 s → 14.40 s** per seed (`city_figure8`), and the matrix took
  **8m10**, not 60 s — off by 8×. Corrected in the docstring with the measured
  table. Taking one reading and generalising is exactly the move that produced
  the 26-day premise.
- ✅ Tests pass in **1.31 s** because the grading logic is a pure function of
  `SweepStats` — only two of ten tests touch a simulator, and neither touches
  `city_*`.

## North-star delta

- **First real movement in 81 cycles, and it is negative — correctly so.** The
  north star is "물체회피 + 경로추종 완벽". We now have a number for the first
  half: **0 of 24 cells can even measure it.** That is a worse position than the
  project believed it was in, and it is the first honest one.
- The blocker is now named and it is not representation: it is **`lam = 0.1`**
  (12 cells) and **scene inventory** (6 empty scenes, 6 unfinishable). None of
  those need a merge either.

## Key learnings

- **A premise that blocks a whole phase deserves one command's worth of
  scepticism.** "P5 needs main" survived 26 days and ~30 cycles because each
  cycle inherited it from STATE rather than testing it. The test was
  `git ls-tree`.
- **The instrument's value was in what it refused to report, not what it
  reported.** Every headline number this harness produces is `nan` or
  suppressed. That is the harness working — D-107's empty-population-reads-as-
  clean would have rendered the same matrix as a perfect score.
- **Two axes, again, and again because they disagreed on real data** (D-116's
  precedent): tracking is 18/24 and avoidance is 0/24 on the *same* run. A
  single "reportable" flag cannot hold both.
- The 81-cycle instrument streak was not caused by lack of P5 work being
  *possible*. It was caused by nobody checking whether it was *blocked*.

## Recommended next 1–3 priorities

1. **Re-run the matrix at a per-scene admissible `lam`** — the calibration table
   already exists (`eval/scenarios/lam_windows.yaml`, 2026-08-02 16:50). This
   converts 12 `ESS_OUT_OF_BAND` cells into real avoidance numbers, or proves no
   admissible temperature exists, which is itself the P5 result.
2. **Fix the scene inventory**: 6 of 8 shipped scenes are avoidance-vacuous or
   unfinishable. `cafe_obstacle_crossing`'s hazards live only in the Gazebo
   world file the sandbox never loads; `cafe_cut_in` completes at 0/8.
3. **Add a near-miss metric.** `min_clearance = 0.000` scoring as success is the
   gap between "no collision" and the north star's "near-miss ≤ Y".

## Artifacts
- PR: pending merge (`autoresearch/p3-epistemic-shadow-cost-critic`, #67)
- Files touched: `eval/mppi_sandbox/baseline_matrix.py`, `eval/mppi_sandbox/tests/test_baseline_matrix.py`, `docs/decisions.md`, `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV row appended: yes
