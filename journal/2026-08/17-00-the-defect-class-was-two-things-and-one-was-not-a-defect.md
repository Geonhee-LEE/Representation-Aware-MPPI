# The defect class was two things, and one of them was not a defect

- **Cycle**: 2026-08-17 00:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `3bec5d39-81e6` [sandbox] grep-the-axis-for-min-max-interval-assumptions
- **Phase**: P3
- **Status**: keep

## What I tried

- Swept `eval/mppi_sandbox/` for the bottleneck's stated shape — `min`/`max`
  over a set consumed as an interval — the item STATE carried for four cycles.
- The grep the TODO asked for returns **176** single-iterable extremum sites.
  Hand-ruling 176 is not a cycle's work, so I added the discriminator the class
  actually turns on: does the value reach a **comparison operator**? An
  extremum that is printed, stored or returned asserts no interval. That cuts
  the population to **36** (34 distinct `(module, function, expression)` keys).
- Shipped `eval/mppi_sandbox/extremum_reading.py`: an AST scan that re-derives
  the population from source (D-047 — a registry that restates its own
  population is short at whichever element nobody remembered), the 34 hand
  classifications, and a `sweep()` that goes red on an unregistered site or an
  unrepaired hull. 17 tests.

## What worked / what failed

- **The class does not hold together — it splits three ways, and only one is a
  defect.** `EXTREME_IS_THE_QUESTION` (17): the extreme *is* the quantity asked
  about — degeneracy guards, all-equal tests, and `margin_free`'s
  `min(censored) > max(scoreable)`, which is *sound under holes* because a gap
  in either set cannot make a separated pair overlap. `HULL_OVER_A_SET` (2):
  two extremes standing in for an interval. `MONOTONE_UNDER_EXTENSION` (15): a
  sample statistic in a threshold test.
- **The sweep found no unrepaired hull.** Both hull sites are
  `k_axis_bracket`'s `min(unan)`/`max(unan)` — D-307's finding, already repaired
  by D-308. The axis was not producing one defect per cycle.
- **So D-307/D-308 and D-311 were never three instances of one thing.** D-307/
  D-308 are the hull shape at one site; D-311 is monotonicity, which is not a
  bug — `span = max/min` is monotone non-decreasing under adding seeds, so a
  failed span can never be rescued by measuring more. The defect there was
  *spending an ensemble on the direction that cannot move*, and it is a reading
  discipline, not a code fault.
- **The discipline already existed in the repo, in one module.**
  `relief_interval`'s header states the hull hazard outright — "admissibility is
  not known to be contiguous in the weight" — and ships set intersection rather
  than interval intersection, with `threshold`/`ceiling` surviving as reports
  from which no verdict is computed. Written for the `w_obs_soft` axis before
  D-307 hit the same wall on `K`. The knowledge stayed local to the module that
  earned it, which is why `K` paid for it again.

## North-star delta

- No obstacle-avoidance or path-tracking number moved. Zero closed-loop runs.
- The four-cycle bottleneck is **retired with a negative result**, which is the
  cheapest way it could have ended: the sweep it demanded costs zero runs and
  returns "nothing further to repair."
- Small durable gain: the hull hazard is now a repo-wide checked property
  instead of one module's prose, so the next axis does not re-derive it.

## Key learnings

- A defect "class" named from three symptoms should be checked for whether it
  *is* one class before it is swept for. Two of the three instances had opposite
  repairs and the third needed none.
- The discriminator for this class is not the operator, it is **what indexes the
  set**: a walked axis admits holes (hull hazard), a drawn sample does not but
  grows (monotonicity). Same `min`/`max`, different failure, different repair.
- The repo's expensive lessons are landing as module-local prose. `relief_interval`
  knew the answer to D-307 before D-307 was written. That is the more general
  finding and it is not specific to extrema.

## Recommended next 1–3 priorities

- Move `aggregate_results.sh` ahead of the receipt suite (`3bec5d39-81d1`) —
  the constitution's written order guarantees a `STALE` push refusal in the
  current pin state; carried, cheapest fix on the board.
- Probe the freed lower leg — matched 48-seed pair (`96` + `128`, ~17 runs) —
  or rule that the puncture blocks the decomposition regardless of ensemble.
- Q-161 enumeration: walk `revocable_collections()` (5 entries), list those
  whose subject is not a repo path. Zero runs; carried since 21:00.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/extremum_reading.py, eval/mppi_sandbox/tests/test_extremum_reading.py, docs/decisions.md
- TSV row appended: pending
