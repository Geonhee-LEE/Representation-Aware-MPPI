# The mover is the scene, not the weight

- **Cycle**: 2026-08-08 14:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `Q-118` λ ladder on `cafe_head_on_v0` at `w = 150`
- **Phase**: P3
- **Status**: keep

## What I tried

- Walked λ ∈ {0.2, 0.4, 0.8, 1.6} × {`stock_mppi`, `risk_mppi`} × 16 seeds on
  `cafe_head_on_v0` at `w_obs_soft = 150` — 128 runs, 300 s, margin 0.40. This
  is the one walk that holds the *scene* fixed against D-135's head_on cell and
  the *weight* fixed against D-134's crossing cell.
- Appended `HEADON_W150_CELL` to `REMEASURED` and re-read `shift_census`.
- Shipped `contrasts(factor)` / `attribution(factor)` — which cell pairs isolate
  the scene axis and the weight axis, and whether the isolated axis moves the
  window.

## What worked / what failed

- **Both arms grade `WINDOW_HELD` at `w = 150`**, re-measuring to exactly their
  recorded `[0.2, 0.4, 0.8]`: every rung 16/16 in band, 16/16 reaching goal,
  λ = 1.6 at 0/16 on both. Same grade this scene took at `w = 100`.
- **So the confound resolves, and it resolves toward the scene.** With a scene
  contrast at fixed `w = 150` and a weight contrast at fixed scene, `attribution`
  reads scene `FACTOR_MOVES`, weight `FACTOR_INERT`. Census is now **4 of 6
  arm-cells held**, and the two movers are both crossing.
- **The walk could have retracted a rung D-132 shipped and did not.** At λ = 0.8,
  `w = 150` reads stock **10/16** unsafe vs risk **1/16** — D-132's `p = 0.0021`
  rung reproduced *exactly* from an independent walk, at a temperature both arms
  are admissible at.
- λ = 1.6 fails **upward** here (median ESS 171 against a band top of 128) —
  the softmax too flat, not collapsed to argmin. D-131's crossing refusals were
  all the low side; this is the first high-side refusal in the registry.
- 🔴 Two test-maintenance costs, both caught by cheap pre-flights rather than by
  a suite: `test_remeasurement_lookup_is_keyed_by_scene_and_weight` asserted
  head_on@150 was `None` (read before editing, not discovered by a run), and two
  census tests pinned the 4-arm-cell literals. `loop_reach.READING` needed one
  new row, surfaced by a 90 s `loop_reach report` rather than a 14 min suite.

## North-star delta

- The project's one significant mechanism claim (D-132's band) is now
  **reproduced at a second weight from an independent walk** and confirmed
  admissible there — it survived the second measurement that could have retracted it.
- The off-key tax is now **scoped**: it is a property of the pathological scene,
  not of weight excursion. head_on tolerates a 15× weight excursion (10 → 150)
  without moving a rung, so re-keying effort can be aimed at crossing-like cells.
- No movement on the north star's own numbers — the headline
  (`unsafe_rate` 0.0000 / `min_clearance` 0.3579 / 5 cells / 40 seeds) is untouched.

## Key learnings

- **A registry is informative in proportion to what its cells *share*, not to how
  many it has.** Two cells at distinct (scene, weight) pairs supported no
  attribution at all; the third was valuable precisely because it *repeated* two
  coordinates. A fourth cell at a fresh pair would add two arm-cells to the
  census and zero contrasts. This is now asserted, not just written down.
- **"Cannot tell" must not collapse into "no difference."** `attribution` returns
  `NO_CONTRAST` rather than `FACTOR_INERT` when the isolating pairs share no arm
  — the same empty-denominator shape D-107/D-120/D-127 each booked.
- **Prose that states a conclusion outlives the measurement that falsifies it.**
  The preamble's "the census cannot yet separate those two axes" was true when
  written and wrong one cycle later; deriving it from the registry means the
  next cell updates it for free.
- Narrowing a guard's justification is not the same as weakening the guard:
  `OFF_KEY` still refuses on both scenes, because a lookup cannot know it is on
  the benign one until ~300 s has been spent finding out.

## Recommended next 1–3 priorities

1. **Re-key `lam_windows.yaml` by weight** (Q-116 option (a)) — now much better
   bounded: the scene attribution says the re-calibration only has to cover
   crossing-like cells, not the whole table.
2. **Give `SEPARATED` a resolution floor (Q-115)** — still open, and every rung
   of this cycle's ladder graded `SEPARATED` including λ = 1.6, where both arms
   are out of band.
3. **A third scene in the registry** — but at `w = 100` *or* `w = 150`, not a
   fresh weight, so it adds a contrast rather than only a census row.

## Artifacts

- PR: #67 (already open)
- Files touched: `eval/mppi_sandbox/lam_window_key.py`,
  `eval/mppi_sandbox/loop_reach.py`,
  `eval/mppi_sandbox/tests/test_lam_window_key.py`,
  `docs/decisions.md`, `docs/deliberations.md`,
  `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV row appended: yes
