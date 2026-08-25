# The pairing came back negative

- **Cycle**: 2026-08-20 17:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE next-actionable #1 — harvest `cte_max` on `cafe_head_on_v0`
- **Phase**: P3
- **Status**: in_progress (suite red then fixed; one clean suite owed before push)

## What I tried

- Bought the half STATE named: `cte_max`, 8 arms × 8 seeds on `cafe_head_on_v0`
  (64 rollouts, **52.5 s** — under half the 118 s STATE priced), pinned into
  `excursion_seed_width.SEED_ENSEMBLE`. `tail_mean.third_paired()` flips to
  `True`.
- Verified the harvest reproduces the pinned seed-0 data **two independent
  ways** before reading anything off it: every seed-0 value equals
  `cte_peak_vacuity.CTE_MAX_SEED0["cafe_head_on_v0"]`, and the seed-0 spread
  equals `excursion_tracking.CENSUS[scene][3]` = `0.2804`.
- Added `third_baseline_ratio`, `contrast_replicates`, `dominance_holds`,
  `COMPARABLE_CELLS`; rewrote `COLUMN_CLAIM_FORM` and four `drift()` clauses.

## What worked / what failed

- **The contrast does not replicate, and that is the result.** `cte_max` on
  `cafe_head_on_v0` grades at **`3.12x`** its own null floor (`2.73x`
  adversarial). It does not miss. Finding #1 is a *conjunction* — `cte_max`
  misses (`0.96x`) while TVaR₀.₉ clears (`2.64x`) — and on the first scene
  excited in both columns since, only the second half survives (`3.88x`).
- So the population of scenes where a maximum is ungradeable is still **one**.
  D-383's reading of `cte_max` as the degenerate endpoint of a tail-averaging
  continuum was a statement about the observable; this says the degeneracy is
  a statement about `(observable, scene)`.
- What survives is weaker and better founded: `dominance_holds()` — TVaR's
  ratio exceeds `cte_max`'s on **2/2** comparable cells (`2.64` vs `0.96`,
  `3.88` vs `3.12`). That is a *noise-reduction* claim, decisive only where the
  gap is marginal against seed noise. Convoy's `cte_max` gap is `0.0633` against
  a `0.0659` floor; head-on's is `0.2960` — **4.7×** larger — against a
  comparable floor (`0.0948`). A big enough effect clears an 8-seed floor as a
  maximum.
- **This could not have been reasoned out from the first scene.** Five cycles
  read the asymmetry as evidence about the observable. One 52-second harvest
  says it was evidence about a scene whose effect was small.
- Byproduct: `cafe_head_on_v0`'s bar window `+0.2216` is the first entry in
  `INTERSECTION` **above** its own A-A null floor (`2.34x` p95, `2.04x`
  adversarial). `floor_reach.INTERSECTION_UNDER_FLOOR`'s caveat — that convoy's
  `+0.0550` is `0.82x` of a floor and so manufactured from a zero effect — is
  specific to convoy and does not generalise to every positive width.
- `census_preempt` earned its 2 s for the **fourth** cycle running: the renamed
  both-columns test entered `loop_reach.targets()` and was unrecorded in
  `READING`. Caught pre-commit, not 17 minutes into a suite.
- **The suite still went red (12 tests, 1246 s), and `census_preempt` could not
  have seen it.** I wrote the `COMPARABLE_CELLS` consistency checks as `drift()`
  clauses. That gave `drift()` a difference-shaped population
  (`guard_reflexivity.KIND_DIFFERENCE`), which promoted `tail_mean.drift` into
  `revocable_collections()` — a pool every member of which owes
  `guard_direction.PROBES` an *executed* direction reading. It had none, so
  `unprobed_revocable()` went `()` → `('tail_mean.drift',)`, and that raises at
  **fixture setup**, taking `test_guard_direction` (9), `test_guard_reflexivity`
  (2) and `test_probe_reach` (1) down together. None of the five censuses reads
  guard *shape*; `census_preempt`'s own `UNCOVERED` line does not list this
  either, because it is not a census at all — it is a classification that
  changed under an edit to an unrelated function's body.
- Fix: the four checks moved to the test layer, where every other pin on this
  module already lives. Verified green across the five affected modules —
  the count was read off a local run and never registered, so it is not quoted
  here (the registered reading is the one the push-gate receipt carries).
  `unprobed_revocable()` back to `()`, `census_preempt` 5/5 clean.
  **No push**: the receipt on disk grades the red tree and the gate refuses it,
  correctly. One clean suite is owed and **no diagnosis is owed**.

## North-star delta

- **Non-zero, and it is a subtraction.** 경로추종 (half the north star) does not
  gain a second scene where the maximum fails; it loses the claim that it would.
  The cross-track column's honest reading narrowed from "TVaR grades where
  `cte_max` cannot" to "TVaR grades at least as high as `cte_max`, and the
  difference matters only near the floor".
- `REMAINING_DEBT` `384 → 320`. Three of eight scenes now carry a cross-track
  ensemble.
- No controller changed; no scenario got safer. This moves what the branch is
  allowed to *say*, not what the planner does.

## Key learnings

- **A conjunction generalises only as well as its weaker half.** Six cycles
  carried "cte_max fails / TVaR clears" as one object. It is two claims with
  different scopes, and nothing forced them apart until a scene was found that
  could test both.
- **The set that supports a cross-column inference cannot contain its own
  falsifier.** `both_columns_scenes()` grew 1 → 2 and both members agree — but a
  scene enters only once its cross-track column has been *bought*, so the
  falsifying shape (clearance excited, cross-track degenerate) is unobservable
  there by construction. Two agreeing cases are worth no more than one.
- **Buying the cheap half of a pair is worth more than a third of anything
  else.** The last three cycles harvested new scenes to extend a column; this
  one completed a cell and got a refutation. Completion beats extension when the
  claim is a conjunction.
- `excited()` has now changed the verdict three times (D-385 rejected, D-387
  admitted, D-388 excluded `city_curved_v0` from `COMPARABLE_CELLS` where its
  `0.35x`-vs-`0.07x` inversion would have refuted `dominance_holds()` on a
  population of two arm rows).

- **A guard's classification is an emergent property of its body, and no census
  watches it.** Adding a check to a guard can change what *kind of guard it is*,
  and the machinery then demands things of it that were never demanded before.
  The pre-commit checks all read populations; this was a shape change.
- **Budget: ~70 min against 35.** The overrun is one red 21-minute suite plus a
  10-minute targeted re-verify. The re-verify was the right spend — it converts
  next cycle from "diagnose and fix and run" into "run".

## Recommended next 1–3 priorities

0. **Run one suite and push** — the fix is committed and locally verified; three
   commits (`f334bff`, `7ea283e`, `d408afd`) are ahead of origin. Nothing to
   diagnose. This outranks everything below.
1. **Re-price D-383 in `docs/decisions.md`** — its finding #1 is now a
   scene-scoped result. It is not wrong; its stated scope is.
2. **Buy one more paired cell** (`cafe_cut_in_v0` or `cafe_freezing_v0`,
   clearance-excited, ~55 s each) — `dominance_holds()` rests on two cells and a
   third is the cheapest thing that could refute it.
3. **branch-scope-decision (user)** — the branch has produced one measured
   subtraction and no planner change in 17 cycles.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: `eval/mppi_sandbox/tail_mean.py`,
  `eval/mppi_sandbox/excursion_seed_width.py`,
  `eval/mppi_sandbox/aa_calibration.py`, `eval/mppi_sandbox/loop_reach.py`,
  `eval/mppi_sandbox/tests/test_tail_mean.py`,
  `eval/mppi_sandbox/tests/test_excursion_seed_width.py`,
  `docs/decisions.md`
- TSV row appended: yes
