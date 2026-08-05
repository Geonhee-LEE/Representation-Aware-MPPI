# The nested suite's largest cost buys observations it cannot receive

- **Cycle**: 2026-08-05 20:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — repair D-089, and not by raising 900
- **Phase**: P3 (calendar P4)
- **Status**: in_progress

## What I tried

- Took STATE #1's stated load-bearing question — *does the census need the whole
  fast half as its subject?* — and answered it by measurement rather than by
  picking a repair.
- Built `eval/mppi_sandbox/nested_subject.py`: a **measured** probe of whether
  the recorder crosses a process boundary, plus a static layer bounding how much
  of the real subject sits on the far side of that boundary.
- Left `DEFAULT_SUITE` **unchanged**. The cycle produces the decision procedure,
  not the narrowing — see "what failed".

## What worked / what failed

- ✅ **The mechanism is confirmed, and it is not a budget opinion.** The recorder
  is installed on the nested pytest with `-p <plugin_module>` — a *command-line
  flag*. `_run_recorder` sets no `PYTEST_PLUGINS`, and a test that shells out to
  its own `python -m pytest` passes no `-p`. So predicate calls made in a
  grandchild process are invisible to the recorder that paid for them.
  `probe()` measures both legs of a constructed two-file suite through the
  **shipped** plugin: **2 in-process calls, 0 subprocess calls → `CONFINED`.**
- ✅ **Two zeroes are graded `INCONCLUSIVE`, not `CONFINED`.** The in-process leg
  is the positive control; without it a zero from the subprocess leg is
  indistinguishable from a broken probe. This package has now shipped that
  mistake three times (D-075 vacuous survival, D-081 overwritten fixture, D-088
  unpopulated reading), so the verdict exists before the finding does.
- 🔴 **My first static detector read `0 of 58` — the answer that means "nothing
  to see here".** It looked for the string `"sys.executable"`, but `ast.dump`
  spells that `attr='executable'` and the source spelling never occurs. Seventh
  instance on this branch of a miss whose output looks like a clean bill. Pinned
  by `test_the_dumped_spelling_is_what_is_matched_not_the_source_spelling`.
- 🔴 **The second draft read `1 of 58`, and was wrong for a deeper reason.**
  Almost no test spawns directly; it calls `pv.measure` / `gv.measure` /
  `push_preflight.record`, and the spawn is one frame down *inside the package*.
  A one-level reading graded `test_push_preflight.py` by accident rather than by
  the reason. `spawners()` now closes **transitively** over package-internal
  calls (32 function names), and the reading is **19 of 58 collected files**.
- ✅ **Reported as an upper bound, in the direction that is safe.** Matching is
  by bare name (`key_conflation`'s defect class, accepted with its consequence
  stated), so an unrelated `measure` is counted. Over-counting proposes cutting
  a file that was contributing — which the census catches as a changed reading.
  Under-counting leaves the ceiling uncleared and *looks like success*.
- 🔴 **No share of seconds is claimed.** Per-file wall clock on the CI runner is
  in no artifact this module can read. 19-of-58 is a population, not a
  percentage, and D-084's half-fix — a per-job reading reported as if per-run —
  is the shape being avoided. Q-090 carries the timing question.
- 🔴 **The slow job is still doomed.** This cycle makes the repair *decidable*;
  it does not apply it. `DEFAULT_SUITE` is untouched, one nested run still costs
  1396 s, and `nested_suite_cost.grade()` still reads `DOOMED`.

## North-star delta

- **No avoidance or tracking number moved — fifty-eighth consecutive instrument
  cycle.** Scenes able to contribute an avoidance number: 5, reportable: 4.
- What moved: the question D-089 left open now has a measured answer, so the
  repair can be chosen on evidence instead of on which number looks too small.

## Key learnings

- **A cost is only wasted relative to what it buys, and "what it buys" is
  measurable.** Three cycles argued about a timeout's *size*. The productive
  question was what the wait purchases, and the answer — for a third of the
  collected files, nothing — is a two-leg probe, not an argument.
- **D-089's prediction held without adjustment, which is new.** It wrote down
  that instrument *conclusions* get spelled as verdict comparisons and *caveats*
  as set differences, so the guard detector systematically counts caveats and
  misses conclusions. This module was written afterwards: `spawners` and
  `subject_files` entered the pool (69 → **71**), and `spawning` — the function
  the module exists to publish, narrowing by `v == SPAWNS` — did not. Twenty-six
  consecutive cycles, but the **first predicted rather than observed after the
  fact**, which is a different epistemic status from the twenty-five behind it.
- **A detector that is loose in two directions at once cannot be reported as
  either bound.** The fixed point removed one of the two looseness sources; the
  remaining one is named where the number is published, not in a footnote.

## Recommended next 1–3 priorities

1. **Apply the narrowing and measure the census both ways.** The decision
   procedure exists; what is missing is the before/after reading proving the
   verdicts are preserved. That is the repair, and it is now a bounded task.
2. **Read the six hidden `test_exclusion_scope` failures on their merits** —
   still unread since 2026-08-04, still unknown whether timeout or real defect.
3. **Answer Q-090: per-file wall clock on the CI runner**, so the saving can be
   stated in seconds rather than in files.

## Artifacts

- PR: #67 (open, this branch)
- Files touched: `eval/mppi_sandbox/nested_subject.py`,
  `eval/mppi_sandbox/tests/test_nested_subject.py`,
  `eval/mppi_sandbox/tests/test_guard_reflexivity.py`,
  `eval/mppi_sandbox/tests/test_key_conflation.py`,
  `eval/mppi_sandbox/tests/test_liveness_derivation.py`,
  `docs/decisions.md`, `docs/deliberations.md`
- TSV row appended: yes
