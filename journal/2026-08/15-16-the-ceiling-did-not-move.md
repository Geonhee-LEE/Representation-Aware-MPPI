# The ensemble was repaired and the ceiling did not move

- **Cycle**: 2026-08-15 16:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `rebaseline-onto-lam-1.0` Re-take D-268/D-270/D-271/D-281 at `(lam=1.0, w_voo=5)`
- **Phase**: P3
- **Status**: keep

## What I tried

- STATE's first priority: re-baseline four cycles of readings onto the rung
  D-283 just showed admissible, **starting with D-027's ceiling** — the first
  rung on this branch where that question is well-posed at all.
- Took the seed-0 `w_voo` ladder at `lam = 1.0` (`1/5/20/50/200`) through the
  existing `calibrated_ladder.sweep`, same `ess_at_peak.ISOLATION` as D-266 and
  D-268, so the only thing that moved between readings is the temperature.
  5 closed-loop runs + 5 leave-one-out ratio reads, **21.5 s**.
- Landed `ceiling_bracket` / `ceiling_response` / `ceiling_gap` with the
  verdict vocabulary fixed before the counts were read, plus 9 tests.

## What worked / what failed

- **The ceiling is located, not merely reachable.** `verdict()` already
  reported `can_address_d027_ceiling`; that is a boolean about whether a ladder
  *could* answer. `ceiling_bracket` returns which two rungs it sits between:
  **`(5, 20]`** at `lam = 1.0`, ESS `31.41 → 2.63` across the step, and the arm
  is audible on **both** sides (`0.267`, `0.625`) — so the crossing bounds a
  region that is actually usable rather than an empty one.
- **The lift bought no weight headroom.** `lam = 0.8` brackets the ceiling at
  `(5, 20]` too. `CEILING_HELD`: same bracket, and the same one-rung usable set
  `{w = 5}` at both temperatures. D-283 repaired the *seed* ensemble at that
  weight (`7/8 → 16/16`); this is the orthogonal question and its answer is no.
- **The seed-axis argument does not port to the weight axis, and that is the
  finding.** `ceiling_gap` is `span_admits_band` moved one axis over: the gap
  across the ceiling (`11.96x`) against a band that is `10.0x` wide. But the
  premise — one shared `lam` scaling both rungs by a common factor — is
  **measurably false** here: the same two temperatures lift `w = 5` by `1.006x`
  and `w = 20` by `1.373x`. So `bars_shared_rung` stays `False` where the
  seed-axis verdict would have barred the pair.
- **The gap is narrowing, and I did not extrapolate it.** `16.33x → 11.96x`
  from `lam 0.8 → 1.0`, still above `10.0x`. Two rungs license nothing about a
  third (D-283's `extrapolates`), so no closing temperature is projected.
- **Free cross-check I did not plan for**: the ladder's `w = 5` cell reproduces
  `MEASURED_SEEDS_16_LAM10`'s seed-0 row to every recorded digit (`31.4085`,
  `0.266901`). Two different sweep bodies landing on one cell is the only
  check that they have not drifted in isolation or in how the ratio is read;
  it is now pinned.

## North-star delta

- **The usable `w_voo` operating region on this scene is one rung wide, and
  widening it is not a temperature problem.** That is a real constraint on the
  epistemic arm's scale, arrived at by measurement rather than assumed.
- No obstacle, clearance or near-miss number moved. Still one scene
  (`cafe_freezing_v0`), still `transfers_to_ab_scene = False`.

## Key learnings

- **"Can it answer?" and "what is the answer?" are different deliverables.**
  `can_address_d027_ceiling` had been `True` since D-270 and nobody had spent
  the 21 s to read the bracket off it. The boolean was mistaken for the result.
- **A repaired ensemble does not imply a repaired ladder.** D-283's `16/16` is
  a statement about one weight; the ceiling is a statement about the weight
  axis, and the lift that moved the first moved the second not at all.
- **Port an argument, port its premise.** The ratio-vs-ratio move worked on the
  seed axis because `span_response` discharged the common-factor premise. The
  same move on the weight axis inherits a premise that is false there, and the
  honest payload withholds the conclusion rather than shipping it with a
  caveat (D-047 — caveats retire silently, fields do not).

## Budget

- **Overran: ~46 min against a 35 min budget.** The first suite came back red on
  two `guard_reflexivity` pins — `ceiling_gap` is the 111th guard and is
  deep-only for D-051's reason — and a second 11 min suite was the only way to
  push green. I took the overrun rather than leave four commits stranded on
  disk, which is the failure D-112 exists to prevent.
- **What would have caught it earlier**: the guard registry is pinned by an
  exact count, so *any* new filtering function moves it. That is knowable
  without running the 11 min suite — `guard_reflexivity.guards()` alone takes
  ~20 s. A cycle that adds a module-level predicate should read the pool before
  it commits, the same way `inert_surface staged` is read before the stage.

## Recommended next 1–3 priorities

1. Walk `lam = 1.2` at `w ∈ {5, 20}` (2 runs, ~9 s) — the gap is narrowing
   `16.33 → 11.96` toward `10.0` and a third rung is what licenses any
   statement about where, or whether, it closes.
2. Re-baseline the remaining D-270/D-271 readings onto `lam = 1.0` now that the
   ladder is there.
3. Buy back the 5 withdrawn `inert_surface` exemptions — sixth consecutive
   cycle carrying that tax.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/calibrated_ladder.py, eval/mppi_sandbox/tests/test_calibrated_ladder.py, eval/mppi_sandbox/tests/test_guard_reflexivity.py, docs/decisions.md
- TSV row appended: yes
