# Spread does not generalise — the two columns are vacuous for different reasons

- **Cycle**: 2026-08-19 15:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #3 — does arm spread predict gradeability on the clearance column too?
- **Phase**: P5
- **Status**: keep

## What I tried

- Took STATE's #3 at face value: D-363 established that on the 경로추종 column
  gradeability is made of **spread**, so the cheap test of generality is whether
  the 물체회피 column's one vacuous scene (D-357) is also a narrow-spread scene.
- Joined `threshold_vacuity.CENSUS` (clearance verdicts) to the attained
  clearance ranges in `scene_census.SCENE_SEED0` and to `excursion_tracking`'s
  cross-track spreads. Zero rollouts — all three operands were already pinned.
- Shipped `eval/mppi_sandbox/spread_generality.py` + 8 pytest pins.

## What worked / what failed

- **The hypothesis is refuted, and cleanly.** Every scene where clearance is
  measurable spreads `0.1964`–`0.3512 m`. The cross-track column's vacuous five
  spread `0.0070`–`0.0730`. No clearance scene comes anywhere near the narrow
  band, so spread is near-constant across that population and separates nothing.
- **The sharpest single comparison**: `cafe_head_on_v0` is `VACUOUS_FAIL` on
  clearance at spread `0.1964`, while `cafe_convoy_v0` *grades* on cross-track at
  spread `0.1441`. Ample dispersion, criterion still cannot cut. So spread is
  **necessary** (D-363 stands) and **not sufficient** (this cycle).
- The two columns turn out to fail by two different mechanisms: cross-track is a
  **width** failure (arms don't differ, no bar cuts), clearance is a **placement**
  failure (arms differ by `0.1964`, the declared `0.40` sits above the entire
  range — best arm `0.2003`).
- One float-equality assertion failed on `0.2003 - 0.0039 == 0.1964`; that was my
  test, not the data. Fixed with `round(..., 4)`.

## North-star delta

- The 물체회피 column's one vacuous cell is now **diagnosed rather than counted**:
  it is repairable by moving a constant, which the 경로추종 column's five are not.
- No new rollouts, no new scene, no controller change — the movement is in what
  the acceptance matrix is understood to measure, not in a measured number.

## Key learnings

- **A mechanism established on one column earns a test before it earns a
  generalisation.** D-363's spread story was strong enough that STATE proposed
  carrying it over; four points of arithmetic said no. The cost of checking was
  ~3 minutes against a finding that would otherwise have been assumed.
- **The branch has been applying one refusal too broadly.** "Do not shop the
  threshold" was learned on the width column (D-356/357/358, refused three
  times, correctly). On the placement column it is the wrong call — there the
  constant genuinely is mis-set, and moving it *into* the attained range is a
  repair, not shopping. Same words, opposite verdict.
- **`cafe_head_on_v0` may already be the scene STATE keeps proposing to author.**
  It carries dispersion on *both* channels (clearance `0.1964`, cross-track
  `0.2804`, excited partition) and grades on **neither** — clearance vacuous-fail,
  cross-track undeclared (D-362). The "author a scene exciting both channels"
  item may be a two-constant declaration on an existing scene.

## Recommended next 1–3 priorities

1. Move `cafe_head_on_v0`'s `min_distance_to_obstacle` into its attained range —
   user-blocked (the value is scene intent) but now argued as a *repair*.
2. Widen the four excited scenes to 8 seeds (STATE #1, still unpaid) — every
   spread in this cycle is seed-0-only, including the `0.1964` vs `0.1441` pair
   the refutation turns on.
3. Ask whether `cafe_freezing_v0`'s `UNDECLARED` clearance key is the same
   placement gap: it has two obstacles, the most clearance data on the branch,
   and no criterion at all.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/spread_generality.py, eval/mppi_sandbox/tests/test_spread_generality.py, docs/decisions.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: yes
