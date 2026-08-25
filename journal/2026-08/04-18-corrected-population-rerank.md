# Re-taking two published rankings over the population that survived — and one of them vanished

- **Cycle**: 2026-08-04 18:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `STATE-1` Re-read the 5 surviving one-sided candidates
- **Phase**: P3
- **Status**: keep

## What I tried

- D-061 ranked the one-sided candidates by call count; D-062 re-ranked the same
  set by distinct inputs and stated its claim falsifiably as `ordering_shift` —
  the two orderings disagree. D-063/D-064 then proved 2 of that set's 7 members
  were artifacts of `EXCLUDED_TESTS`. Both rankings were still standing over the
  contaminated set.
- Made the population an argument (`predicate_inputs.shift_over`) — a rank is
  positional, so a shift over a set is not a claim about a subset of it and
  cannot be transported, only re-taken.
- Added `exclusion_scope.surviving` / `rerank` / `corrected_shift` /
  `voided_leaders`, and paid the 2 runs (attributed vacuity + input census,
  5 min 12 s each) to read the real answer rather than assert it.

## What worked / what failed

- 🔴 **The corrected `ordering_shift` is empty.** Over the 5 survivors, ranking
  by calls and ranking by distinct inputs **agree completely**. D-062's own
  docstring set this as the judgement — "if the two orderings agree, D-061's
  call count was a fine proxy and this instrument bought a bound and nothing
  else" — and on the corrected population it fires.
- 🔴 **Both published headlines were the same artifact.**
  `guard_reflexivity._shells_out_to_git_diff` held **rank 0 of both** orderings
  (5938 calls *and* 3068 distinct). D-061 led with it and D-062 led with it.
- 🔴 **All 3 published disagreements traced to one artifact's position.** They
  were `guard_is_derived` itself (rank 1→3) plus `quieter` (2→1) and `_has`
  (3→2), which moved only because the artifact sat between them.
- ✅ The negative result is expressible: a clean set reranks to itself, and a
  paired test pins the case where the correction *preserves* a shift, so the
  empty reading is evidence rather than a wiring bug.
- ⚠️ 683 passed after the pin update; the one failure en route was my own —
  `surviving`/`voided_leaders` tripped the running tally (49 → 51).

## North-star delta

- **No avoidance or tracking number moved — thirty-third consecutive instrument
  cycle.** Scenes able to contribute an avoidance number stays 5, reportable 4.
- What moved: a published empirical claim was withdrawn **by its own stated
  criterion**, on a measurement the authoring decision could not afford. D-064
  made this cost 2 runs; at D-063's price it would not have been asked.
- What moved against the story: this is the third consecutive cycle whose
  entire subject is the measuring apparatus. The 가려진-obstacle class still has
  exactly one working cost term (D-027).

## Key learnings

- **A rank is not transportable.** Both sort keys are per-site, so the survivors'
  relative order never changed — which makes it *look* like the reading carries
  over. It does not: what was published were rank-0 sentences, and dropping a
  member renumbers everyone below it. "The ordering is unchanged" and "the
  ranking is unchanged" are different claims and only the first is free.
- **An instrument that names its own falsification condition can be held to it
  later by someone else.** D-062 wrote down what would void it and shipped a
  test for the negative case; that is the only reason this cycle could void it
  in one line instead of arguing about it.
- **The detector keys on the narrowing, not on its risk.** Four functions
  implement one correction; the two that difference against a registry entered
  the reflexivity pool, the two that take the population as a parameter did not.
  D-056's `misscored_probes` note, now with a same-cycle control.
- The correction is population-only: survivors' distinct counts are still read
  under `EXCLUDED_TESTS`. Written into the slow test's docstring as a bound, not
  bought.

## Recommended next 1–3 priorities

1. **Take the input census with the exclusion lifted** (1 run) — closes the bound
   this cycle declared, and it is the only remaining way a survivor's `distinct`
   is still the exclusion's number rather than the suite's.
2. **Re-read what D-061/D-062 concluded downstream of their rank-0 sites**, now
   that both headlines are withdrawn — the 5-survivor list is small enough to
   read whole.
3. **Ask the same question of `guard_vacuity.EXCLUDED_TESTS`** (STATE #2,
   unchanged): whether `test_guard_witness.py` covers guard lines it is not the
   witness for.

## Artifacts

- PR: #67 (existing — 60th consecutive cycle, no new review bandwidth)
- Files touched: `eval/mppi_sandbox/exclusion_scope.py`,
  `eval/mppi_sandbox/predicate_inputs.py`,
  `eval/mppi_sandbox/tests/test_exclusion_scope.py`,
  `eval/mppi_sandbox/tests/test_guard_reflexivity.py`, `docs/decisions.md`
- TSV row appended: yes
