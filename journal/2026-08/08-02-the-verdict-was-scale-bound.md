# The verdict was scale-bound, not shape-bound

- **Cycle**: 2026-08-08 02:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — answer Q-110 (can the soft barrier beat `w_path` at any weight?)
- **Phase**: P5
- **Status**: keep

## What I tried

- Swept `w_obs_soft` on `cafe_head_on_v0` at matched `lam = 0.8`, 8 seeds, and
  swept `obs_soft_scale` separately at the same rung — one knob at a time,
  because they are not one "barrier strength" axis.
- Attached the two admissibility filters this repo already owns to every rung:
  `all_reached` (freeze buys clearance, `ab.assert_all_reached`) and
  `ess_in_band` (a weight big enough to collapse the softmax is a disguised
  temperature change, D-027 / Q-049). A rung failing either is not evidence.
- Shipped it as `barrier_ceiling.sweep` with three verdicts — `RELIEVED`,
  `BOUGHT_INADMISSIBLY`, `SATURATED` — plus 19 tests.
- Re-ran the two 8/8-unsafe scenes and one already-safe control at the rung
  that relieved head_on.

## What worked / what failed

- ✅ **Q-110 answers `RELIEVED`, and it inverts the Q's own lean.**
  `cafe_head_on_v0` goes `unsafe_rate` **1.0000 → 0.0000** between
  `w_obs_soft = 10` (shipped) and `300`. All 8 seeds reach the goal, every
  seed's ESS stays in band, and `mean_clearance` goes 0.0056 → 0.5806 against
  a declared 0.40. The lean was that no weight would reach the bar and that
  the null would support the representation hypothesis; the measurement says
  the opposite.
- ✅ **The win is not paid for on the scene's other declared key.** Worst-seed
  `cte_rms` at the relieving rung is 0.2058 against the scene's declared 0.30
  — inside the bound, and above D-122's 0.0865 lower bound for schedules that
  hold the margin, so the measured arm and that screen agree.
- ✅ **The same single weight relieves the *other* 8/8 scene too.**
  `cafe_obstacle_crossing_v0` goes 1.0000 → 0.0000 and its worst-seed
  `cte_rms` **improves** (0.1573 → 0.0869). D-120's `unsafe_rate = 0.6667`
  headline was substantially a weight-scale artifact, not controller
  incapacity.
- ✅ **The two knobs answer oppositely, which is why they were swept apart.**
  8× on `obs_soft_scale` (0.3 → 2.4) moves `unsafe_rate` not at all and leaves
  `mean_clearance` at ~0.006: `SATURATED`. A single fused "barrier strength"
  axis would have averaged a relief and a null into one wrong story.
- 🔴 **This retroactively demotes two cycles' headline comparisons.** D-119's
  risk channel (32×) and D-124's gap gate (1.7×) were both measured at
  `w_obs_soft = 10`, i.e. ~30× below the rung where the verdict moves at all.
  Both arms were unsafe on every seed at that operating point, so neither
  comparison could have moved `unsafe_rate` whatever the mechanism did. A
  mechanism A/B run where *both* arms fail the bar is not a test of the
  mechanism.
- 🟡 **The control scene warns against globalising the number.**
  `cafe_convoy_v0` was already 0/8 safe at the shipped weight and stays 0/8 at
  300, but its ESS leaves the band there — so `300` is not a free repin, it is
  a rung that costs sampler compliance on a scene that did not need it.
- 🟡 **`obs_soft_scale`'s null is a scene fact, not a knob fact.** Widening the
  decay length raises the barrier everywhere including on the path, so it
  moves the cost landscape's offset more than its gradient — expected in
  hindsight, unmeasured until now.

## North-star delta

- **First time a shipped scene's safety verdict has moved.** Two of the eight
  matrix cells go from 8/8 unsafe to 0/8, holding both declared keys. Every
  prior cycle bought clearance multiplicatively and moved no verdict.
- The north star's "물체회피 완벽" now has one scene where the sandbox
  baseline actually meets the scene's own bar, rather than missing it by 70×.
- Honest limit: this is a **weight**, not a representation. It says the
  operating point was wrong, not that the input is right.

## Key learnings

- **An A/B where both arms fail the bar measures nothing about the arms.**
  Before the next mechanism comparison, check that the baseline's operating
  point admits a pass at all — otherwise the comparison is scored entirely
  inside the failure region.
- **"Sweep the ratio against `w_path`" was the wrong instrument and nearly the
  one I built.** Scaling every weight by `c` is exactly scaling `lam` by `c`,
  so a pure ratio sweep is a temperature change wearing a weight's name. Only
  raising one weight is a real cost-shape change — and that is precisely why
  the ESS filter cannot be optional here.
- **The project's cheapest unasked question outranked its most interesting
  one.** Three cycles changed cost *shapes*; none had checked whether the
  existing shape was scaled to compete. ~4 min of sim answered it.
- Two negative verdicts had to stay distinct strings: `SATURATED` (the term
  cannot move the verdict) and `BOUGHT_INADMISSIBLY` (it can, by ceasing to be
  a cost-term change) license opposite next moves.

## Recommended next 1–3 priorities

1. **Re-run the full 8-cell baseline matrix at a per-scene admissible
   `w_obs_soft`** — the headline `unsafe_rate = 0.6667` is measured at a rung
   now known to be below the relief threshold on two scenes.
2. **Re-run D-119 / D-124's mechanism A/Bs above the relief threshold** — both
   were scored where neither arm could pass; the risk channel and gap gate may
   or may not survive a comparison that can distinguish them.
3. **Find the per-scene ceiling, not one global weight** — `cafe_convoy_v0`
   leaves the ESS band at 300, so a single repin trades sampler compliance on
   scenes that never needed the relief.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic, #67)
- Files touched: eval/mppi_sandbox/barrier_ceiling.py, eval/mppi_sandbox/tests/test_barrier_ceiling.py, docs/decisions.md, docs/deliberations.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: yes
