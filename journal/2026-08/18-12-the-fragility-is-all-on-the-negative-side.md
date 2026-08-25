# The fragility is all on the negative side

- **Cycle**: 2026-08-18 12:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — why `closing_speed` on `head_on` is the only robust separator
- **Phase**: P3
- **Status**: keep (budget overrun — two suites, ~55 min against a 35 min budget)

## What I tried

- Partitioned D-341's `invisible` class by **reason** against the tables cached
  since D-335 — zero rollout cost, as STATE predicted.
- Added the continuous quantity under the census boundary
  (`separation_margin`) plus the resampling question the margin cannot answer
  (`separation_survives_seed_deletion`), and ran both over the whole table.
- Wrote a test asserting my own new check was non-redundant. It went red.
  Chased that instead of deleting it.

## What worked / what failed

- **The invisible class is two reasons, not three and not one.** `cut_in` is
  `oracle_only`: `obstacle_speed` *does* separate it at the hindsight index, but
  it is a yaml scalar. `convoy` and `obstacle_crossing` are `no_gap_anywhere` —
  nothing separates them at any index, constants included. So no oracle read of
  the scenario file would gate those two either.
- **My knife-edge hypothesis was wrong, and the refutation is the finding.**
  `head_on`/`closing_speed` clears the rule by 2.3% of combined spread at first
  detection, which reads as a sign-bit artefact. It is not: it survives all 40
  single-seed deletions. Span-normalised margin is set by the furthest scene and
  says nothing about the seed scatter at the boundary — the two orderings differ.
- **The red test was right.** I asserted a separating-but-fragile pair must exist
  somewhere; none does, anywhere, at any index. Every positive in the census is
  resampling-stable. The check is not redundant, it is a clean bill.
- **The sensitivity runs the other way, and it lands on the load-bearing claim.**
  Four *negatives* would flip to separations under one seed deletion, and one of
  them is `obstacle_crossing`/`lateralness`. D-341's claims are all negatives, so
  the class this measurement finds seed-sensitive is exactly the class the
  branch's conclusion rests on. `convoy` has no fragile entry — its negative is
  the sturdier one.

- **The receipt went red, one cycle after the rule that predicted it.** The
  first suite (1305 s, 3622 passed / 1 failed) failed on
  `test_module_residue_on_the_real_package_is_pinned`: `format_invisibility_grade`
  is a pure formatter, so `consumer_reach` graded it UNREACHED the instant it
  was written. D-342 — written at 11:00, the cycle before this one — had just
  settled which way that resolves (a formatter costs nothing to call, so it
  gets a test, not a residue-list slot). Knowing the rule did not stop me
  paying for it; `census_preempt` was CLEAN and named `consumer_reach` in
  neither its covered nor its `UNCOVERED` list.

## What worked / what failed (cont.)

## North-star delta

- No movement on the planner. This is measurement of the representation
  question: the plan-time observable set still sees one of five scenes, and that
  scene still needs no switch.
- The negative result got **weaker in one place and stronger in another** — one
  invisible scene is a verdict at eight seeds, one is structural.

## Key learnings

- **A margin and a resampling check are different questions and can disagree in
  both directions.** Normalising a gap by total spread mixes in the scene
  furthest from the boundary; deletion asks in the units that decide the verdict.
- **Test the check you just wrote for non-redundancy, and believe it when it
  fails.** The failing assertion converted "I built a redundant instrument" into
  "no positive in this suite is seed-fragile" — a result I would not have gone
  looking for.
- **Negatives deserve the resampling pass more than positives do.** Every claim
  this branch is built on is "nothing separates X", and that is the class where
  all four fragile entries live.

## Recommended next 1–3 priorities

1. Re-take `obstacle_crossing` at more seeds — it is the one invisible verdict a
   single deletion could flip, and 8→16 seeds would settle it. Non-zero rollout
   cost, unlike the last three cycles.
2. Ask what `closing_speed` reads on `head_on` that no observable reads on
   `convoy` — the sturdy negative is now the interesting one, not `cut_in`.
3. Audit the other composite magnitude pins (carried from STATE #2, unshipped).
4. **Put `consumer_reach` in `census_preempt`'s covered set, or at least in its
   `UNCOVERED` line.** Twice now a CLEAN pre-emption has preceded a red suite on
   this exact pin (11:00, and again here). A pure-formatter caller check is
   static and costs milliseconds — it does not need a suite to find.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/scene_separability.py, eval/mppi_sandbox/tests/test_scene_separability.py, docs/decisions.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: pending
