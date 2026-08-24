# The CI failure count was a floor, and nothing said so

- **Cycle**: 2026-08-25 06:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `heading-weight-machine-dependence` (STATE next-actionable #1)
- **Phase**: P3
- **Status**: keep

## What I tried

- STATE's #1 asked me to reproduce the 3 `test_heading_effort_weight.py`
  failures under `NPY_DISABLE_CPU_FEATURES` and decide Q-054. Before spending
  the reproduction I read the CI run those 3 came from — run `32756918395`,
  head `12a5a8d7`, the first run after D-462 made tests actually execute.
- Pulled the per-shard logs rather than the run-level conclusion, and ran the
  named failures locally on the same tree.
- Shipped `ci_verdict.py` + 7 tests: a reader that refuses to report a failing
  set from a run that has none, and returns `is_floor` with every count.

## What worked / what failed

- **STATE undercounted: 7 failures across 4 files, not 4 across 2.** The three
  it missed — `test_arm_audibility.py::test_bisect_point_reproduces`,
  `::test_sweep_ratio_reproduces_a_recorded_point`, and
  `test_heading_price_absence.py::test_weight_converts_on_the_obstacle_free_scene`
  — sit in files STATE never named, which is exactly why "two failure classes"
  read as a complete taxonomy. `STATE_READING` is a strict subset of
  `OBSERVED_FAILURES`, pinned as a datum.
- **All 7 pass locally, in 39.77 s.** Not "some are flaky" — the divergence is
  total. A local receipt carries *zero* information about this class.
- **And 7 is still a floor: 2 of the run's 9 jobs reached no verdict.** Shard 6
  was `cancelled` at 1804 s against its own `timeout-minutes: 30`; the slow
  closed-loop job was still `in_progress` at 3h36m of a 360-minute ceiling. I
  first read the slow job as hung and was wrong — 360 is its declared budget
  and it is inside it. The cancel is the real finding.
- The suite the local receipt graded green (4202 passed) and the CI run are
  therefore not two readings of one tree; they are readings of two machines,
  and only one of them is the one the PR ships on.
- **`census_preempt` earned its place and then mis-read, both in one cycle.**
  It caught my `VERDICT_CONCLUSIONS = frozenset({...})` entering the TYPED
  allow-list population within 2 s of staging — a *category* constant matching
  `unwatched_exemptions()`'s shape, exactly D-330's documented trap. Applied
  D-330's prescribed repair (delete the membership test, don't bump the pin):
  it is now a `has_verdict()` predicate.
- **But its `guard_tally` then reported `139 vs pin 140` — and that red is
  false.** `test_guard_reflexivity.py`'s pin test passes in 0.43 s. Measured
  both ways: `guards()` returns **139 with my files present and 139 with them
  removed**, so this cycle contributes nothing to the pool; the shortfall is
  `census_preempt` harvesting in a process that has not imported every
  guard-registering module, while pytest imports the whole test tree and
  reaches 140. **Worse, its first reading was clean for the wrong reason**:
  139 base + 1 from my stray frozenset = 140, which matched the pin by
  coincidence. So the instrument read CLEAN on the tree that had the defect
  and DRIFT on the tree that had been repaired. Both readings were wrong, in
  opposite directions, ten minutes apart.

## North-star delta

- **Zero physical movement** — no controller line, no rollout, no metric moved.
  ~40 cycles now without a rollout.
- What moved is the evidence base's honesty: the number STATE was about to
  spend a cycle acting on was wrong in both directions (too small, and
  presented as complete when it was a floor).
- `ceiling_breaches()` supplies the evidence for a call the workflow's own
  comment already reserved: shard 6 is the **fourth** crossing of the
  D-084/D-094/D-227 shape, and that comment forbids another number bump.

## Key learnings

- **D-462's lesson has a third axis.** That decision said a local receipt cannot
  see a missing dependency because it runs where the dependency is present.
  Same shape here: a *partial* CI run cannot see the failures in shards that
  never reported, and its count is indistinguishable from a complete one. Both
  are "the instrument cannot observe its own blind spot".
- **Q-054 is re-scoped, not answered.** It was framed as "re-pin, re-derive, or
  demote 3 asserts". The population is 7 tests in 4 files, every one a
  reproduction of a constant recorded off a chaotic closed-loop rollout. A
  per-assert fix does not address a family.
- **Reading the run-level conclusion is what hid this.** `gh run list` says
  `in_progress`; the shard verdicts are one API call further down. The cheap
  reading and the correct one differ by one call.
- My own wall-clock estimate ran ~3× long again (I called 14 min at 5m12).
  `cycle_wallclock elapsed` disproved it, as it did on 2026-08-24 20:00.

## Recommended next 1–3 priorities

1. **Re-read run 32756918395 once the slow job concludes** — `failing_tests()`
   becomes callable and the floor becomes a total. Do not decide Q-054 on the
   floor.
2. **Q-054 at family scope**: decide the disposition of the 7-test
   recorded-rollout-constant class as one population, not test by test.
3. **`census_preempt.guard_tally` under-counts by import reachability** — it
   harvests in a process that has not imported every guard-registering module.
   File it: a census that can read CLEAN on a defective tree and DRIFT on a
   repaired one is worse than an absent one. (Not folded into D-463; it is a
   separate instrument defect and deserves its own measurement cycle.)
4. **Shard 6's ceiling**: intra-file split or a ceiling with a measured floor
   behind it — the workflow comment rules out another guess.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/ci_verdict.py, eval/mppi_sandbox/tests/test_ci_verdict.py, docs/decisions.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: yes
