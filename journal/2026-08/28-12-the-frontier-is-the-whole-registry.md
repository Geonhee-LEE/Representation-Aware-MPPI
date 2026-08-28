# The frontier is the whole registry — P5 has no single baseline to choose

- **Cycle**: 2026-08-28 12:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — Choose P5's baseline controller, or prove none is non-dominated
- **Phase**: P5 (entry 2026-09-03, 6 days out)
- **Status**: keep

## What I tried

- Took STATE's own stated cheap first cut, verbatim and with no new rollout:
  read `reportable_surface()` together with the per-arm `cte_*` / clearance
  censuses already on disk, and ask whether any single arm is non-dominated on
  the north-star metrics across the completable scenes.
- Shipped `baseline_domination` (+ 20 tests): derives the two axes' coverage
  from the live censuses, normalises their **opposite senses** (clearance is a
  floor, cross-track a ceiling), and computes the Pareto frontier.
- Separated duplicate arms from genuine tradeoffs before counting the frontier.

## What worked / what failed

- **STATE's second branch is the answer, and it is not close.** On the joint
  surface **no arm dominates any other** — every distinct pair has each side
  winning ≥2 of the 8 columns. The frontier is the *entire registry*. There is
  no single-baseline choice available.
- **One "non-domination" was duplication and would have inflated the count.**
  `geometric_mppi` and `stock_mppi` are bit-identical on all 8 joint columns
  (0-0 pairwise). Two identical arms are mutually non-dominated *by
  construction*. Collapsing them gives **7 distinct** arms, not 8. This
  reproduces `clearance_census`'s inert-channel signature on a **disjoint**
  column set — independent confirmation the geometric channel does not bite.
- **Each single axis nominates a baseline, and the two nominations are
  disjoint.** Clearance alone: `cbf_mppi` dominates all seven others outright.
  Cross-track alone: `essps_mppi` / `frozen_risk_mppi` / `risk_mppi`, with
  `cbf_mppi` dominated. A P5 report quoting either axis in isolation would name
  a winner the other axis refutes. This is `cte_vacuity`'s clearance/tracking
  tension, now measured as a frontier rather than noted from one side.
- **The joint surface is 4 of 8 completable scenes, not 8** — STATE's phrasing
  ("across the 8 scenes") was not available. The two axes cover different
  subsets for *unrelated* reasons: three scenes have zero obstacles so the
  clearance question is not *posed*, and `cafe_obstacle_contested_v0` simply has
  no recorded `cte_rms` column. Derived in `coverage()`, not typed.
- **`census_preempt` earned its keep again** — caught `guard_tally` 147→150
  (my three new screens) in ~2 s, pre-suite, instead of a red run 13 min later.

## North-star delta

- **A P5 decision is settled, negatively and on record**: the report needs a
  per-class contract, not a single baseline. That was STATE's own stated fork
  and the branch it lands on removes a choice P5 entry would otherwise force
  blind in 6 days.
- No planner movement — no controller, representation or dynamics code touched,
  no rollout run. This is an instrument + reading cycle.
- The measured frontier is a **lower bound** on the true tradeoff width:
  `time_to_goal` and smoothness — two of the north star's 경로추종 clauses —
  have no per-arm-per-scene census in the tree at all.

## Key learnings

- **A frontier computed over duplicates is not a frontier.** The check that
  makes the reading trustworthy is the one that removes a member. Had the
  duplicate not been screened, this cycle would have reported "8 arms
  non-dominated" — the same inert-channel error, committed by the instrument
  built to detect it.
- **Sign normalisation is where a two-axis reading dies silently.** A floor bar
  and a ceiling bar compared with one sign inverts the frontier and nothing goes
  red. Done once in `_cte_column`, pinned by a test, rather than at each site.
- **The single-axis answers were decisive and contradictory.** That is the
  strongest argument for having taken the joint read: either axis alone would
  have produced a confident, citable, wrong baseline.
- **One joint cell is calibration-inadmissible and it belongs to the clearance
  winner** (`cbf_mppi × cafe_obstacle_crossing_v0`, the only empty window in the
  reportable 64). Rather than assert this away, the claim that it does not move
  finding #1 is *measured* — dropping the scene leaves the frontier the whole
  registry (`test_frontier_survives_dropping_the_inadmissible_scene`).

## Recommended next 1–3 priorities

1. **Draft P5's per-class contract** — the report now needs one arm named per
   obstacle/tracking class rather than a single baseline. The 4-scene joint
   surface plus the two disjoint single-axis frontiers is the input.
2. **Buy the `time_to_goal` per-arm-per-scene census** — the frontier is a
   lower bound until it exists, and it is the north-star clause with no
   instrument at all.
3. **Widen the frontier to 8 seeds** (`WIDENING_UNBOUGHT` = 224 rollouts) —
   seed-0 rankings are the weakest evidence on this branch, though more seeds
   can only *add* tradeoffs, never collapse the frontier to a single arm.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/baseline_domination.py, eval/mppi_sandbox/tests/test_baseline_domination.py, eval/mppi_sandbox/tests/test_guard_reflexivity.py, docs/decisions.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: pending
