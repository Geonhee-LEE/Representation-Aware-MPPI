# The null's second rung is refused twice, and its numbers point the other way

- **Cycle**: 2026-08-10 03:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — run the geometric null on the other five walked rungs
- **Phase**: P3
- **Status**: keep

## What I tried

- Turned D-167's single-rung reading into a **census**: `NullRung` is a record
  (scenario, λ, weight, `w_geom`, clearances, admissibility, the recorded arms
  it pairs against), `NullCensus` grades over however many rungs exist, and
  `Attribution` takes a rung instead of reading module constants.
- Coverage is reported **before** the verdict and its denominator is read from
  `margin_free.census()` — walking a seventh rung there lowers this census's
  coverage rather than silently flattering it.
- Walked the second rung and the **first on another scene**: `cafe_head_on_v0`
  `w_obs_soft = 75`, λ = 0.8, D-166's second-largest effect (`A = 0.9980`).
  16-seed `w_geom` ladder to calibrate, then 32 seeds paired with the recorded
  arms.

## What worked / what failed

- 🔴 **The rung is refused on ESS: 31/32.** All 32 reached the goal; seed 25's
  softmax ran at **134.15** against `ab.ess_band(256) = [12.8, 128.0]`. The
  direction is the unhelpful one — **above** the band is a softmax too near
  uniform, i.e. the term too *quiet* to rank rollouts.
- 🔴 **And the calibration never identified a coefficient there.** The ladder
  `w_geom ∈ {1, 2, 2.5, 4, 8}` moves median ESS from 115.86 to 115.64 — a span
  of **0.19%** of the risk arm's 115.90. D-167 picks `w_geom` by landing the
  null's ESS on the risk arm's; on this scene every candidate lands there, so
  the pick (`w_geom = 2.0`) is the ladder's spacing, not a measurement. New
  `NullRung.coefficient_identification` reads `FLAT` / `IDENTIFIED` /
  `UNRECORDED` — three states, because "the criterion could not pin it" and
  "nobody wrote down whether it could" are opposite epistemic states.
- 🟡 **The refused numbers point the other way.** `residual_share = 0.0485`
  on head_on against convoy's **0.7725**: geometry reproduces 5% of the gain on
  one scene and 77% on the other. Kept as data, quoted as a result nowhere —
  the census does not consume it and stays `SINGLE_RUNG` at **1/6**.
- 🟢 **The convoy reading is bit-for-bit unmoved** by the refactor
  (`A = 0.9868 / 1.0000 / 0.6953`, share `0.7725`), and the four
  witness-less verdicts now build a stated `NullRung` instead of
  monkeypatching module globals — a synthetic verdict cannot silently diverge
  from the shipped one because both go through the same method.
- 🟢 **`exposed_to_quiet_null`** makes the controller's residual asymmetry
  countable: a `REPRESENTATION_ADDS` on a `FLAT` rung is the one reading the
  "null was merely quieter" objection eats. Currently 0/1.

## North-star delta

- No movement on the headline (`unsafe_rate` 0.0000 / `min_clearance` 0.3579 /
  `success_rate` 1.0000) — this cycle bought instrument and one refused walk.
- The attribution claim's evidence base is **still one rung**. The cycle's
  honest contribution is that the second rung did not silently join it.

## Key learnings

- **A calibration protocol is a scene-local object.** ESS-matching pinned
  `w_geom` on convoy (ESS 12.40 at `w_geom = 40` vs 105.07) and is degenerate
  on head_on (0.19% span over a 8× coefficient range). Any future arm compared
  this way needs its ladder's *response*, not just its picked value, recorded.
- **The convenient refusal is the one that tests the rule.** head_on's numbers
  would have read as a large win for the representation. They are refused by
  the same all-seeds ESS rule that refused `LOUDER_NULL`, and stayed refused.
- Two scenes disagreeing by 15× on `residual_share` means the D-167 headline is
  not yet a property of the mechanism; it is a property of convoy `w = 75`.

## Recommended next 1–3 priorities

1. **Re-walk head_on `w = 75` at a `w_geom` that is actually loud enough** —
   the ladder must be extended upward (≥ 20) until median ESS *responds*, then
   the rung re-walked at the ESS-matched value. Without that, the scene's
   disagreement with convoy is unmeasured, not measured.
2. **Walk the remaining four rungs** (head_on `w ∈ {100, 150, 250}`, crossing
   `w = 250`), each with its ladder response recorded, so `SINGLE_RUNG` can
   become a real census.
3. **Make `sandbox:pass=N` state which quantity it is** — `passed` vs
   `executed`. Carried six cycles.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/geometric_null.py, eval/mppi_sandbox/tests/test_geometric_null.py
- TSV row appended: yes
