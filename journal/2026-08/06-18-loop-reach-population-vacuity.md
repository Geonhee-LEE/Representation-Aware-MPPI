# The 15 loop-body population claims are all genuinely sampled — the hazard does not extend here

- **Cycle**: 2026-08-06 18:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — grade the 15 population-claim loop-body assertions
- **Phase**: P3
- **Status**: keep

## What I tried

- STATE #1 was the *measured* half of D-102's sweep: `assert_reach.sampled()`
  counts loop-body asserts and grades 15 of them population claims, but nothing
  had read them. Counting is not reading.
- The hazard a loop-body assert carries is **not** D-102's. There a failure
  stopped the run before the claim. Here the run is **green** and the claim is
  still unevaluated — `for cell in registry_cells(): assert ... <= ...` over an
  empty iterable passes, checks nothing, and the element count is invisible in
  the source, in the pass count, and in the CI log. It is visible only in the
  execution.
- So: `eval/mppi_sandbox/loop_reach.py` (+27 tests) runs the tests under
  `sys.monitoring` watching the 15 assert lines and counts executions.
  `DISABLE` on first hit of every non-target line is what makes it cheap —
  **~2 s overhead on an 89 s run**, decaying rather than scaling.
- **Zero is two findings, and separating them is the whole design.** Zero
  executions means either the loop yielded nothing (vacuity — the finding) or
  the test never ran (skipped/deselected — absence). The discriminator is the
  `for` statement's own line, watched alongside the assert.

## What worked / what failed

- ✅ **The reading is empty, and that is the answer.** All 15 claims are
  evaluated over **2–30 elements**. No `EMPTY`, no `SINGLETON`. The hazard that
  produced D-100 (stale `CARDINALITY`), D-101 (unsound `SUBSET`) and D-102 (two
  claims no run reached) **does not extend to the loop-body population.** The
  suspicion was reasonable; the measurement refuses it.
- ✅ **The controls came first, and one earned its keep.** Five synthetic
  loops with answers written down before the instrument was pointed at them:
  empty→`EMPTY`, singleton→`SINGLETON`, three→`SAMPLED n=3`, skipped→`NOT_RUN`,
  and **nested-inner-empty→`EMPTY`** — the last is why the header is pinned to
  the *innermost* loop; outermost would have reported an outer loop's 3
  iterations and masked an inner loop that ran zero times.
- ✅ **Controls run under real pytest, not `exec`.** pytest **rewrites**
  asserts; a counter that agreed with `exec` and disagreed with the rewriter
  would be wrong about the only execution anyone cares about. Checked head-on
  (`test_counts_survive_pytest_assert_rewriting`).
- 🔴 **My own test's arithmetic was wrong and the instrument was right.**
  `test_report_names_every_unevaluated_row` hard-coded 2 unevaluated controls;
  the instrument said 3 — `test_nested_inner_empty` is the third. Fixed by
  *deriving* the count from `EXPECTED`. A count restated by hand is a second
  source of truth that can only ever be wrong.
- 🟡 **One row is `NOT_RUN` in the fast job.**
  `test_the_nominal_point_lies_inside_its_own_band` is `slow`-marked, so the
  fast job never evaluates it. Re-measured under `--slow`: `SAMPLED n=8`, and
  the `slow` job does select it (`-m slow`). Recorded at that value — but
  "evaluated" here means *by the job carrying the D-033 dispatch drift*, not
  "evaluated in CI green".

## North-star delta

- **No avoidance or tracking number moved — seventieth consecutive instrument
  cycle.** Scenes able to contribute an avoidance number: 5, reportable: 4.
- What moved: a **suspected defect class is now closed by measurement rather
  than left open by assumption.** Three cycles of this branch found real
  unevaluated claims; the fourth asked the same question of a different
  population and got a clean no. That is the cheapest possible outcome and it
  only counts because the instrument reproduced five known answers first.

## Key learnings

- **An empty reading is a different object depending on whether it was measured
  or assumed.** D-076/D-081 said keep it; this is the first time the kept
  emptiness is the *headline*. `READING` + `test_the_reading_found_no_vacuity`
  make it a guard: if a future edit empties one of these loops, that goes red,
  which a journal line saying "found nothing" never would.
- **Vacuity and absence look identical at the assert and differ at the loop
  header.** Without that discriminator every `slow`-marked test in the corpus
  would have been published as a vacuity — 18 in these 13 files alone. The
  cheap extra watch line is the entire difference between a finding and a
  false alarm.
- **`sys.monitoring`'s `DISABLE` makes "measure the execution" affordable.**
  The reason this question had never been asked is presumably that tracing a
  1247-test suite sounds prohibitive. Per-location disabling makes the overhead
  decay to nothing; that unlocks a whole class of runtime questions this project
  has so far only asked statically.
- **The recorded reading is not re-taken every run, and that is a declared
  trade-off.** 90 s is too expensive for the suite; the drift guard checks the
  *target set* instead, so a new population-claim loop forces a re-measurement.

## Recommended next 1–3 priorities

1. **Ask the same runtime question of the 159 non-population loop asserts** —
   `sampled()` counts 174 loop-body asserts total and this cycle graded 15. The
   instrument now exists and the marginal cost is one more `report` run.
2. **Add a line-number field to the `CI_FAILURES` contract** (carried from
   D-102 — it got its numbers from a log that will expire).
3. **Sweep the 13 non-shielded `assert x <= y` / `== {literal}` sites.**

## Artifacts

- PR: #67 (existing — 93rd consecutive cycle writing into it, no new review cost)
- Files touched: `eval/mppi_sandbox/loop_reach.py` (new),
  `eval/mppi_sandbox/tests/test_loop_reach.py` (new),
  `docs/decisions.md`, `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV row appended: yes
