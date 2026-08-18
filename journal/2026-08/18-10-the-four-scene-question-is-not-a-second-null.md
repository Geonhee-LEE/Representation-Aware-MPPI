# The four-scene question is not a second null — it splits three ways

- **Cycle**: 2026-08-18 10:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `state-p1` Plan-time separability beyond `cut_in`
- **Phase**: P3
- **Status**: in_progress — measured, **not pushed** (red tree, push gate refused)

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
- ~~Adding four pure functions moved **no** census~~ — written before the suite
  and **wrong**; see the red section below. `guard_tally` held at 122, but two
  other censuses moved. Left struck rather than deleted: the mistake was
  believing a green `census_preempt` covered the question it appeared to.

## The cycle ended red — and `census_preempt` said CLEAN

- The receipt came back **rc=1: 3610 passed / 164 skipped / 1 xfailed / 3 failed**
  in 972.38s. `push_preflight check` refused. Three commits sit on disk unpushed;
  D-112's REVIEW step 0 will name them next cycle.
- **The failures are mine, and the arithmetic proves it.** The cycle-start probe
  graded `e4070a4` green at 3609 passed. 3609 + 4 new tests = 3613 = 3610 + 3.
  So all four new tests pass and **three pre-existing pins went red** because the
  four new public functions moved two censuses:
  - `test_key_discrimination`: discrimination 0.097 → **0.2014**, crossing the
    0.20 rung. Its own message forbids the cheap fix — "re-read the finding
    rather than re-tuning this list".
  - `test_consumer_reach::test_module_residue_on_the_real_package_is_pinned`.
- **`census_preempt` returned CLEAN twice, before and after the writes.** Neither
  `key_discrimination` nor `consumer_reach` is among the four censuses it
  re-derives, and — the part worth carrying — **neither appears in its `UNCOVERED`
  line either**, which names only `inert_surface` pins, `tsv_timestamp audit`,
  `exemption_control.REGISTRIES`, `extremum_reading.SITE_CLASSES`. So the
  uncovered set is strictly larger than the check advertises. This is D-317's
  lesson recurring one layer up: a check whose scope is narrower than it looks
  reads exactly like a clean one, and this time even its self-declared gap was
  incomplete.
- **My own "shape decides admission" learning was wrong as stated.** `guard_tally`
  stayed 122, so the functions did not enter the *guard* pool — but they did
  enter the *key* population. Deriving from existing tables buys exemption from
  one census, not from all of them.

## Recommended next 1–3 priorities

1. **Discharge this strand first (D-112)** — three commits are complete and
   measured but red. Decide `key_discrimination` **statically** before spending
   another 972 s: is 0.2014 a real doubling of discrimination, or an artefact of
   four names entering the wide key? Re-tuning the rung is explicitly forbidden
   by the test.
2. **Widen `census_preempt` or fix its `UNCOVERED` line** — it named four gaps
   and has at least six. A cycle that trusts it pays a full suite to find out.
3. **Ask what `closing_speed` sees that the invisible three do not** — the
   substantive follow-up, answerable against cached tables at zero rollout cost.
   Notion TODO created this cycle.
4. **Amend D-330 with the Q-166 discriminant** — carried, still costs a suite.
5. **Fold the node-ID lesson into the loop prompt** — carried from 08:00/09:00.
   It paid again here: 40 s on three node IDs against 972 s for the suite.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic, PR #67)
- Files touched: eval/mppi_sandbox/scene_separability.py, eval/mppi_sandbox/tests/test_scene_separability.py, docs/decisions.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: yes
