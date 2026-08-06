# The position was a field of the failure, not a table beside it — and D-103's bill was still on the counter

- **Cycle**: 2026-08-06 21:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #2 — add a line-number field to the `CI_FAILURES` contract
- **Phase**: P3
- **Status**: in_progress

## What I tried

- Moved the failing statement's **position** into the census row: `CiFailure`
  grows `lineno` + `statement`, `located` / `unlocated` publish the population
  and its residue, and `RUN_ID` / `RUN_COMMIT` move to the census they describe.
- Made `assert_reach.FAILED_AT` a **derivation** of `sa.located()` rather than a
  second hand-kept transcription of the same eight rows.
- Wrote the contract test STATE #2 actually asked for: `unlocated() == ()`, so a
  census transcribed without positions is red at transcription time.
- Found the tree **already red** at HEAD and repaired that too — D-103's
  `loop_reach.report` was an unpaid pool member with an unwatched allow-list.

## What worked / what failed

- ✅ **The reading is unchanged: 2 shielded sites, 6 unpinned, `moved() == ()`.**
  Removing the duplication moved no number, which is what a de-duplication
  should do.
- ✅ **The subset check could not have caught the omission.** `FAILED_AT ⊆
  census` was the strongest thing sayable while the table was hand-kept, and it
  catches a key naming nothing — but the omission ran the *other* way: 14 census
  rows, 8 positions, and nothing said the 8 were the right 8. Derived, the two
  cannot disagree and the test asserts equality.
- 🔴 **HEAD was red, and had been for three hours.** D-103 (18:10) committed,
  never pushed, and left `test_unwatched_allow_lists_are_module_layer_only`
  failing: `UNEVALUATED` shipped as a typed literal, so `unwatched_exemptions`
  went 5 → 6 within one test run of being written. `origin` is still at 85e0bc7
  — the push gate's `&&` did its job, silently, and no cycle re-read the pin.
- 🔴 **The obvious repair would have deleted the guard instead of paying for
  it.** Deriving the constant (`UNEVALUATED = unevaluated_grades()`) makes
  `_is_set_valued` say no, `loop_reach.report` **leaves the pool**, and the pin
  reads 77-unchanged — D-103's cost recorded as nil. Naming the derivation at
  the call site keeps it counted at 78 *and* reads `DERIVED`. Three spellings of
  one set, three census readings; one has both properties. Measured, not argued.
- ✅ **My own new test entered `loop_reach`'s target set** and had to be graded
  (`SAMPLED n=8`). D-103's instrument charged D-104 within one cycle of existing.

## North-star delta

- **No avoidance or tracking number moved — seventieth consecutive instrument
  cycle.** Scenes able to contribute an avoidance number: 5, reportable: 4.
- What moved: a field three cycles needed and one cycle recovered by luck is now
  a contract, and the branch is **green again** after three hours red.

## Key learnings

- **A position is a property of the failure, not of the module that wants one.**
  Kept beside the census, the field is optional and stays unwritten until
  someone needs it; kept *in* the row, its absence is a red test.
- **The strongest check on a duplicated table is still one-directional.** `⊆`
  catches a phantom key and cannot see a missing one. Derivation is what turns
  the subset into an equality.
- **A repair can be spelled so that it erases its own bill.** The detector's
  form-dependence (D-072/D-073) has so far decided whether a guard is *visible*;
  here it decided whether a *payment* is recorded or reads as a disappearance.
- **A cycle that never pushes leaves no red anywhere.** D-103's journal, TSV and
  STATE all read green because the count was taken before the write that broke
  it — D-043's hazard in the one place D-043 does not reach: the cycle that dies.

## Recommended next 1–3 priorities

1. **Re-take D-103's suite count and TSV row** — its journal quotes a pass count
   for a tree that was red at the census pin, and the row still says `keep`.
2. **Give the `slow`-job failure transcription the same contract** — `CI_FAILURES`
   is now positional; the next run's transcription should be generated from the
   job log rather than copied by eye.
3. **Sweep the 13 non-shielded `assert x <= y` / `== {literal}` sites** (STATE #3).

## Artifacts

- PR: #67 (existing — no new review bandwidth)
- Files touched: `eval/mppi_sandbox/simd_attribution.py`,
  `eval/mppi_sandbox/assert_reach.py`, `eval/mppi_sandbox/loop_reach.py`,
  `eval/mppi_sandbox/tests/test_simd_attribution.py`,
  `eval/mppi_sandbox/tests/test_assert_reach.py`,
  `eval/mppi_sandbox/tests/test_loop_reach.py`,
  `eval/mppi_sandbox/tests/test_guard_reflexivity.py`
- TSV row appended: yes
