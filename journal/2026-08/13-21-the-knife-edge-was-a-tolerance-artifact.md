# The knife edge was a tolerance artifact — and the freeze number does not survive its own lam

- **Cycle**: 2026-08-13 21:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — widen the freeze result to the paired-seed protocol (n=12, matched λ)
- **Phase**: P5
- **Status**: keep

## What I tried

- Shipped `eval/mppi_sandbox/freeze_weight.py`: the paired-seed sweep D-243's
  interior optimum was missing. Three things it does that D-243's sweep did not
  — **one simulation, both readings** (`ab.run_arm` hands back the trajectory it
  scored, so freeze and clearance cannot come from different passes),
  **n=12 paired** seeds, and the acceptance limit **read** from the scene's own
  `freeze_duration_max` rather than typed.
- Admissibility is three clauses: no run exceeds the declared limit, every run
  reaches, and worst-case clearance does not fall below the `w_freeze = 0`
  ablation. `verdict` names the *shape* of the admissible set —
  `PLATEAU width=N` / `KNIFE_EDGE` / `EDGE_OPEN` / `FRAGMENTED` /
  `NONE_ADMISSIBLE` / `NO_FREEZE_TO_PRICE`.
- Swept the D-243 grid refined 3× between `1e3` and `1e5`, n=12.
- Added `verdict_ladder` over `three_arm.EPS_LADDER` after the first sweep
  returned a verdict I did not believe.

## What worked / what failed

- **The optimum is not a knife edge; it has width 2.** n=12, λ=0.1:

  | `w_freeze` | exceed | median longest | worst clearance |
  |---|---|---|---|
  | 0 (ablation) | 6/12 | 1.95 s | 0.9207 m |
  | 3e3 | **0/12** | 0.65 s | 0.9205 m |
  | 1e4 | **0/12** | 0.40 s | 0.9211 m |
  | 3e4 | 0/12 | 0.70 s | 0.9034 m |
  | 1e5 | 9/12 | 2.25 s | 0.8440 m |

  The bare verdict is `KNIFE_EDGE` — but only because `3e3` sits **0.2 mm**
  below the ablation's worst-case clearance and `EPS_CLEARANCE = 1e-6` convicts
  it. The ladder: `1e-6 → KNIFE_EDGE`, `1e-3 → PLATEAU width=2`,
  `1e-2 → PLATEAU width=2`, `5e-2 → EDGE_OPEN`. **`threshold-robust: False`**,
  and that is the answer to STATE's bottleneck: at any tolerance the sandbox
  physically resolves, `1e4` has a neighbour.
- **The n=3 headline was optimistic and the n=12 reading is worse.** D-243 read
  the ablation at 2/3 exceed; at n=12 it is 6/12, and `1e2` — which D-243 called
  *worse than not wiring the term* at 3/3 — is 6/12, i.e. **exactly the
  ablation**. That cell was noise, not a perturbation effect.
- **The sharper finding is that the whole D-243 result is temperature-local.**
  `profile_arm` passes no `params`, so every D-243 number is at `StockMPPI`'s
  default `lam = 0.1`. The branch's *paired* comparisons run at
  `three_arm.LAM = 0.8` — which is the λ STATE asked for. Same arm, same scene,
  same seed, only λ moves:

  | | seed 0 | seed 1 |
  |---|---|---|
  | λ = 0.1 | 3.30 s | 1.70 s |
  | λ = 0.8 | **81.90 s** | **71.70 s** |

  40× the declared 2.0 s limit, ~90% of the run stalled — and `reached` is
  **true in every one of those runs**, so `three_arm`'s completion-based freeze
  detector sees nothing, exactly as D-241 said it would.

## North-star delta

- STATE's bottleneck is answered in the direction it hoped for (the optimum has
  width) and undercut in a direction it did not ask about (the width is measured
  at a λ the branch's own paired protocol does not use).
- 21 tests, both directions on all three admissibility clauses, all six
  verdicts, and the λ non-comparability pinned as a measurement rather than
  prose.
- No planner moved this cycle. The term is unchanged and still defaults off.

## Key learnings

- **A verdict taken at one tolerance is a claim about the tolerance.** The
  branch already knew this — `three_arm.verdict_ladder` exists for the identical
  reason — and the new module reproduced the mistake anyway because
  `EPS_CLEARANCE` was borrowed from a module that uses it to ask *"is this an
  improvement"*, where 1e-6 is right, into one asking *"is this a regression"*,
  where it convicts noise.
- **A measurement's temperature is part of the measurement.** Nothing was wrong
  with D-243's numbers; they were taken at the controller default and reported
  without it, and the paired protocol runs somewhere else entirely. Every
  `w_freeze` cell on this branch is now quotable only with its λ.
- **`reached` stays true at 90% stalled.** The freezing scene's `goal_reached`
  criterion is satisfied by a robot that takes 93 s to travel 3.5 m. This is the
  third cycle to hit the same blindness from a new direction, and it is what
  STATE #3 (`time_to_goal` as first-arrival) exists to close.

## Recommended next 1–3 priorities

1. **Re-run the sweep at `PAIRED_LAM = 0.8`** — the λ STATE asked for. The
   ablation there is ~80 s of stall, so the question is not which weight is best
   but whether any weight in the grid is admissible at all.
2. **Implement `time_to_goal` as first-arrival time** — a 93 s run passing
   `goal_reached` is the same blindness from a third direction, and this scene
   declares `time_to_goal_max: 12.0`.
3. **Run the freeze price on the other eight scenes** at `w_freeze ∈ {3e3, 1e4}`
   — now a two-point plateau rather than a single cell, which is what makes the
   transfer question worth asking.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/freeze_weight.py, eval/mppi_sandbox/tests/test_freeze_weight.py, docs/decisions.md
- TSV row appended: pending
