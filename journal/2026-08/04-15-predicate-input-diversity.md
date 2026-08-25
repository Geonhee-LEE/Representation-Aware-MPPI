# Distinct inputs, not call counts — and the top candidate is the one it cannot read

- **Cycle**: 2026-08-04 15:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `Q-074` reach the test surface — lean (c), the argument distribution
- **Phase**: P3
- **Status**: keep

## What I tried

- Q-074 leaned **(c)**: don't try to read the assert, read the **argument
  distribution of the subject predicates the tests call** — D-057's real defect
  was that its bar was only ever evaluated on one kind of scene.
- Built `predicate_inputs`: same population as D-061, same patching recorder,
  same subprocess suite, same excluded tests — but the wrapper writes down a
  **fingerprint of the arguments** instead of the return value.
- Split `predicate_vacuity._PLUGIN` into `PRELUDE / RECORD_VALUES / INSTALL /
  DUMP` so the install-and-alias-rebind half has exactly one statement. `_PLUGIN`
  reassembles byte-identical, pinned by a test; the `DUMP` split is load-bearing
  because `atexit` is LIFO and a second registration would clobber the first's file.
- Joined the two censuses: `recited()` = one-sided **and** single-input;
  `ordering_shift()` = where D-061's rank-by-calls and rank-by-distinct disagree.

## What worked / what failed

- ✅ **The refactor did not move D-061's reading.** 61 predicates (was 59; the new
  module adds 2 of its own, both `UNOBSERVED` because its tests are excluded):
  `BOTH` 43, `ALWAYS_TRUE` 3, `ALWAYS_FALSE` 4, `UNOBSERVED` 11, `NON_BOOLEAN` 0,
  4 refused. The **7 candidates are the same 7**.
- ✅ **Calibration is no longer 0.** The constructed set contains the shape the
  history could not supply — `recited_bar` reads **50 calls / 1 distinct**, which
  is D-057's shape exactly. `miscalibrated() == ()`, and the mirror pins the
  *count* as well as the verdict, so a recorder that fingerprinted nothing would
  fail it (3 of 4 verdicts would still be right).
- 🔴 **The statistic changes the ordering — but not at the head.** Shift on **3 of
  7**: `guard_is_derived` 1→3, `Direction.quieter` 2→1, `weight_units._has` 3→2.
  Rank 0 and ranks 4–6 are unchanged.
- 🔴 **The site D-061 led with is the one this instrument cannot read.**
  `_shells_out_to_git_diff`: 5694 calls, **2944 distinct** — so *not* recited —
  but `address_reprs=True`, because its arguments are AST nodes with
  identity-based reprs. The declared bias (addresses over-count distinct) bites
  precisely at the top candidate, so the reading is **uninformative by its own
  rule**, not evidence of a well-probed predicate. Reported as such rather than
  ranked. 9 of 47 `MANY_INPUTS` are inflated this way.
- ✅ **One informative new candidate.** `local_only_audit.guard_is_derived`:
  `ALWAYS_TRUE`, **26 calls, 2 distinct, no address reprs**. D-061 ranked it #2 on
  its call count; it is two questions asked thirteen times each. That is the
  D-057 shape with a fingerprint that can be trusted, and it is the next witness.
- ⚠️ The 2 sites that *are* one-sided-and-single-input (`is_timing_sensitive`,
  `Liveness.moved`) were both already `n=1` under D-061. The conjunction
  re-derives what the call count already said about them and adds nothing.

## North-star delta

- **No avoidance or tracking number moved — thirtieth consecutive instrument
  cycle.** Scenes able to contribute an avoidance number: 5, reportable: 4.
- What moved: D-061's own headline statistic is now measured rather than
  asserted, and it is **wrong in a specific, bounded way** — it ranks by answers
  when the evidence is questions.
- What moved against the story: the correction does not rescue the search. The
  candidate that the new statistic promotes (2 distinct inputs) is a suite gap of
  the same kind D-060 and D-061 already found. Three censuses, three readings,
  one consistent conclusion: this package's checks are **under-tested**, not
  vacuous.

## Key learnings

- **A call count counts answers; the evidence is questions.** `ALWAYS_FALSE`
  after 5694 calls and after 1 are different claims — D-061 was right about that
  — but the number separating them is the distinct-input count, and D-061 picked
  the one that was easy to read.
- **A declared bias is only worth declaring if you check where it bites.** The
  fingerprint over-counts on address reprs, which was written down as making
  `SINGLE_INPUT` *strong*. Measured, it lands on the single most-cited site in
  the previous cycle's report and voids its distinct count. Naming the direction
  of an error is not the same as knowing which reading it destroys.
- **`distinct == 1` is a boundary, not a threshold.** This is how the module
  avoids becoming the fourth unjustified constant (D-020's is still open):
  everything above 1 is reported as a count and left ungraded, exactly as D-061
  left the call count.
- The instrument enters its own population. Two new `UNOBSERVED` predicates, and
  its tests are in `EXCLUDED_TESTS` from the first commit — D-060's lesson paid
  upfront for the second cycle running.

## Recommended next 1–3 priorities

1. **Witness `local_only_audit.guard_is_derived`** — 26 calls / 2 distinct /
   informative. The one candidate this cycle promoted on trustworthy evidence.
2. **Give the fingerprint a value-based fallback for AST nodes** so the top
   candidate's 2944 becomes readable — or declare that class unreadable and stop
   ranking it. Currently it is neither.
3. **Q-075**: does an `UNOBSERVED` count of 11 mean anything, given that both
   censuses exclude the tests that would call those predicates?

## Artifacts

- PR: #67 (open, 57th consecutive cycle writing into it)
- Files touched: `eval/mppi_sandbox/predicate_inputs.py`,
  `eval/mppi_sandbox/tests/test_predicate_inputs.py`,
  `eval/mppi_sandbox/predicate_vacuity.py`, `docs/decisions.md`,
  `docs/deliberations.md`
- TSV row appended: yes
