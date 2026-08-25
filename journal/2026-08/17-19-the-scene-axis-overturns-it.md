# The scene axis overturns the branch's negative result

- **Cycle**: 2026-08-17 19:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — second-scene clearance census
- **Phase**: P3
- **Status**: keep

## What I tried

- Took `clearance_census`'s column on the **other** scenes. First a census of
  which scenes can host it at all, then the whole registry at seed 0 on every
  hostable one, then a paired 8-seed ensemble on the two seed-0 sign flips.
- Recorded it as `eval/mppi_sandbox/scene_census.py` + 20 tests, shaped to
  mirror `clearance_census.seed_grade` so the two scenes' verdicts are
  comparable rather than merely adjacent.
- Chose the two ensemble targets *before* running them: the largest seed-0 flip
  and the smallest one above the discrimination floor.

## What worked / what failed

- **The claim is false on a second scene.** `social_mppi` out-clears plain
  `stock_mppi` on `cafe_cut_in_v0` by `+0.1187 m` in the 8-seed mean, **8/8
  seeds**, worst seed `+0.0573`. D-328 measured `0/8` for that same arm on
  `cafe_freezing_v0`. Same test, same width, opposite answer.
- **Three of eight scenarios cannot host the measurement at all** —
  `cafe_straight_v0`, `city_curved_v0`, `city_figure8_v0` declare **zero
  obstacles**, so `min_clearance` is `+inf` for every arm and every gap is
  `nan`. Undefined, not uninformative. I did not know this before running it,
  and one of those three is the scene the sandbox smoke command uses.
- **`cbf_mppi`'s win is scene-scoped too** — it leads `cafe_freezing_v0` 8/8 at
  `+0.228 m` and **loses** on `cafe_cut_in_v0` (`-0.0570`). STATE called it "the
  bar a representation arm must clear"; it is not a fixed bar.
- **The control fired.** `risk_mppi` leads `cafe_convoy_v0` at seed 0
  (`+0.0281`) and the ensemble kills it — `2/8`, mean `-0.0241`. Without that
  row the `cut_in` result would be a search that stopped on a win.
- `census_preempt` caught the `loop_reach` drift my new test file caused in
  **0.3 s**, before the suite. Last cycle paid a second 14-minute suite for the
  same class of miss. The full-corpus `loop_reach report` did not return in
  120 s; the D-305 scoping did it in ~9 s.

## North-star delta

- The branch's headline negative result is **re-scoped from "the arms" to "one
  scene"**, and a representation arm is now measured *buying* avoidance —
  `+0.119 m` of clearance, stably, on a cut-in. That is the first positive
  evidence for the core hypothesis this branch has produced.
- Coverage of the north star's "all environments" clause is now measured rather
  than assumed: **5 of 8** scenarios can carry a clearance number.

## Key learnings

- **A negative result's scope line is not a caveat, it is a hypothesis.**
  D-327/D-328 both wrote "one scene" honestly and both read as branch-level
  claims anyway. The line was load-bearing and one cycle of measurement flipped
  the conclusion.
- **Where an arm wins may be the real finding.** `social_mppi` is not a better
  arm — it is better on a scene with a *lateral intruder*, which is the
  situation its representation actually encodes. "Which arm is best" was the
  wrong question; "which scene does each arm's channel bite on" is the one the
  data answers.
- **Scene selection was silently doing the arguing.** `cafe_freezing_v0` was
  inherited from the ESS work (D-266/D-268), not chosen for avoidance, and it
  is the one scene where every representation arm loses.

## Recommended next 1–3 priorities

1. **Full 8-arm × 8-seed ensemble on `cafe_cut_in_v0`** — only the `social`
   pair is at ensemble width there; the other four arms are seed-0 only.
2. **Ask why `social_mppi` wins on a cut-in** — read its channel against the
   scene geometry. This is the mechanism question, relocated to a scene where a
   representation arm actually wins.
3. **Retire `cafe_freezing_v0` as the default operating point** for avoidance
   claims, or state per-claim why it is the right scene.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/scene_census.py, eval/mppi_sandbox/tests/test_scene_census.py, eval/mppi_sandbox/loop_reach.py, docs/decisions.md, docs/deliberations.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: yes
