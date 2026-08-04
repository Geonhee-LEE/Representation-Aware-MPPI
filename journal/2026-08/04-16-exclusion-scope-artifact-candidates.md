# The witness already existed — and the census could not see the file it lives in

- **Cycle**: 2026-08-04 16:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — witness `local_only_audit.guard_is_derived`
- **Phase**: P4 (instrument lane; subject is P3 code)
- **Status**: keep

## What I tried

- STATE #1 asked for a witness: construct an input making `guard_is_derived`
  return `False`, or show none exists. Before constructing one, asked whether the
  tree already contained one.
- It did. `guard_witness._w_unguarded_declarations` builds a repo whose push
  guard is neither derived nor literal and calls `unguarded_declarations(root)`,
  whose first line is `guard_is_derived(root)` → `False`. Present since D-060.
- So the question changed: why did the census score it `ALWAYS_TRUE`? Because
  `test_guard_witness.py` is in `predicate_vacuity.EXCLUDED_TESTS`.
- Built `exclusion_scope.py` to measure what that list hides: two censuses over
  one population (shipped exclusion / lifted), with each moved verdict attributed
  to a specific file by lifting the entries **one at a time**.

## What worked / what failed

- 🔴 **8 predicates move, and the two that cost something are both `test_guard_witness.py`
  collateral.** `local_only_audit.guard_is_derived` `ALWAYS_TRUE → BOTH`, and
  `guard_reflexivity._shells_out_to_git_diff` `ALWAYS_FALSE → BOTH`. The second is
  **D-061's headline** — the 5694-call site its report led with, which D-062 then
  voided on address-repr grounds. Two consecutive cycles ranked an artifact.
- 🔴 **The mechanism is a scope mismatch, inherited verbatim.** `guard_vacuity`
  reads coverage of a *line*, so hiding a witness file hides exactly the
  contamination. `predicate_vacuity` reads a return-value distribution over
  *every* predicate, and a test file calls far more predicates than the ones it
  is the instrument for. Same tuple, different meaning.
- ✅ **The other 6 moves are `SELF_ENTRY` and the exclusion is right about them** —
  `guard_witness.Attempt.satisfiable`, two `predicate_inputs.InputReading` members,
  three in `predicate_vacuity`. The finding is not "drop the list"; it is "the
  scope is wrong", and `corrected_candidates` says by how much.
- ✅ **Attribution is measured, not inferred.** A move is attributed to the file
  whose individual lift reproduces it; the filename convention is used only for
  the `SELF_ENTRY` judgement and `unresolved_subjects` makes it falsifiable.
  `UNATTRIBUTED` exists because per-file lifts are independent and a move needing
  two files at once reproduces under neither.
- ⚠️ **Eleventh consecutive cycle whose module enters a registry its own package
  audits** — `test_exclusion_scope.py` joins `EXCLUDED_TESTS`, so this module's own
  entry sits inside its own measurement. That is the honest place for it, not a
  workaround.

## North-star delta

- **No avoidance or tracking number moved — thirty-first consecutive instrument
  cycle.** Scenes able to contribute an avoidance number: 5, reportable: 4.
- What moved: two of the seven one-sided candidates are withdrawn, and the
  withdrawal is by execution rather than by re-reading. The candidate list D-061
  and D-062 both ranked was ordering an artifact at the head.
- Honest bound: this corrects an instrument, not a controller. The 가려진-obstacle
  class still has exactly one working cost term (D-027).

## Key learnings

- **An exclusion list is part of the measurement surface and nothing was auditing
  it.** Three cycles built instruments to catch claims about populations that
  were never executed; the population *this* instrument declared was cut by a
  tuple copied from a different instrument that reads a different thing.
- **"Construct a witness" has a cheaper predecessor: check whether the suite
  already contains one.** D-060's move is right, and asking it of the tree first
  cost one grep and answered a question two cycles had gotten wrong.
- **A verdict change has a direction and the direction is not the grade.**
  `BOTH → one-sided` manufactures a suspect; `UNOBSERVED → BOTH` only says the
  excluded file was the sole caller. Merging them would have reported the
  correction as four times its true size.

## Recommended next 1–3 priorities

1. **Q-076 (b): record the running test's nodeid per observation** so exclusion
   becomes a classify-time, subject-scoped filter — 5 suite runs collapse to 1,
   and `SELF_ENTRY` becomes a derivation. D-063's lift measurement is its
   calibration.
2. **Re-read the 5 surviving one-sided candidates** now that the head of the list
   is gone — D-062's `by_input_diversity` ordering was taken over a set that
   included both artifacts.
3. **Ask the same question of `guard_vacuity.EXCLUDED_TESTS`.** Its scope
   argument is sound for coverage, but nobody has measured whether
   `test_guard_witness.py` also covers guard lines it is not the witness for.

## Artifacts
- PR: #67 (existing, autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: `eval/mppi_sandbox/exclusion_scope.py`,
  `eval/mppi_sandbox/tests/test_exclusion_scope.py`,
  `eval/mppi_sandbox/predicate_vacuity.py`, `docs/decisions.md`,
  `docs/deliberations.md`
- TSV row appended: yes
