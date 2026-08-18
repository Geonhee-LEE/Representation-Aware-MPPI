# The four-scene question is not a second null — it splits three ways

- **Cycle**: 2026-08-18 10:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `state-p1` Plan-time separability beyond `cut_in`
- **Phase**: P3
- **Status**: keep

## What I tried

- Discharged STATE.md's bottleneck item 1 — "run the separability matrix over
  the four scene pairs `cut_in` was not, and find out whether *any* pair
  separates at plan time on a non-constant observable."
- Found the one-vs-rest matrix over all five scenes was **already measured and
  cached** at all three indices (`SEPARATION`, `CAUSAL_OBSERVED`). What was
  missing was not a measurement but a **readout**: the branch had five per-index
  tables and no accessor that says which scenes survive the index control.
- Added `robust_causal_separators` (intersection across causal indices),
  `scene_visibility` (three-way classifier), `visibility_census` (partition),
  `format_visibility_grade`. Four tests, including a structural partition pin.

## What worked / what failed

- **The expected second null did not happen.** The census reads
  `robust: (head_on,)`, `index_fragile: (freezing,)`,
  `invisible: (cut_in, convoy, obstacle_crossing)`. One scene *does* separate at
  plan time on an observable that moves: `head_on` on `closing_speed`, at both
  causal indices.
- **The sting is where the visibility landed.** D-333 named `cut_in` as the
  switch's decision point and showed `cbf_mppi` already wins `head_on`. So the
  one robustly visible scene is the one no switch needs, and all three scenes a
  switch would have to arbitrate are invisible. The negative is now *sharper*
  than a flat null would have been: it is not "these observables see nothing",
  it is "these observables see exactly the wrong scene".
- **Intersection vs union is load-bearing, and `freezing` is the witness.**
  `freezing` separates on `ttc` at `fixed_time` and on nothing at
  `first_detection`. A union-valued implementation would call it robust and be
  green on every other row — hence the dedicated test.
- The hindsight and causal tables disagree about *which* observable carries
  `head_on` (`min_ttc` at critical, `closing_speed` causally). Not a
  contradiction — `min_ttc` has no causal counterpart by construction — but it
  means "head_on is separable" was never one claim.
- `inert_surface staged` returned `STAGED_MOVED` on all five snapshot pins.
  Paid as D-207 price, not bought back: D-315 records Q-091's measurement that
  all five are `REPROBE_SELF_BLOCKED`. Its consequence (every write before the
  receipt) is already D-315's mandated order.

## North-star delta

- **First plan-time visibility result on this branch that is not a null**, but
  it moves the north star ~0: the visible scene is the one already covered. The
  unseen-distribution clause is still untouched.
- The invisible class now has **three named members**, not one. `cut_in`'s
  invisibility was a scene fact; three of five invisible is a fact about the
  *observable set*, which is the more actionable of the two.

## Key learnings

- **The bottleneck asked for a measurement that had already been paid for.**
  40 rollouts × 3 indices were cached since D-335; five cycles of prose read
  the `cut_in` row and never ran `causal_informative_table` over the other four.
  Before scripting a re-take, run the accessors that already exist.
- **A one-scene question cannot produce a three-way answer.** With `cut_in`
  alone the only available verdicts are separable / not. The classes appeared
  only once the rule ran over all five — which is what the control was for.
- Adding four pure functions moved **no** census (`guard_tally` 122 unchanged).
  Predicates over registries get admitted to the guard pool; functions that
  *derive* from existing tables do not. That is a cheap shape to prefer.

## Recommended next 1–3 priorities

1. **Ask what `closing_speed` sees that the invisible three do not** — the one
   robust separator is now a worked example, and the question "why this one"
   is answerable against the same cached tables at zero rollout cost.
2. **Amend D-330 with the Q-166 discriminant** — carried, still costs a suite,
   still only worth bundling with other guard work.
3. **Fold the node-ID lesson into the loop prompt** — carried unshipped from
   08:00 and 09:00.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic, PR #67)
- Files touched: eval/mppi_sandbox/scene_separability.py, eval/mppi_sandbox/tests/test_scene_separability.py, docs/decisions.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: yes
