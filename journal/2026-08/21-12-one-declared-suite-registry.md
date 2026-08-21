# The declared suite becomes one statement; the copies that agreed were the ones that could not drift

- **Cycle**: 2026-08-21 12:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `3c3c5d39` D-402 실행: DECLARED_SUITE registry 하나로 통합 + check() 의 SCOPED verdict
- **Phase**: P5
- **Status**: in_progress

## What I tried

- Ran D-402's mandated **step 1 first**: do the four machine-readable copies of
  the declared-suite tuple actually agree today? Read all four. **They agree** —
  same three strings, same order. So the D-047 third instance D-402 suspected is
  *latent*, not manifest.
- Declared `eval/mppi_sandbox/declared_suite.py::DECLARED_SUITE` and derived all
  four copies from it (`predicate_vacuity`, `guard_vacuity`,
  `tests/test_receipt_scope.py`, `tests/test_suite_coverage.py`).
- Added `tests/test_declared_suite.py`: a source scan asserting no site
  re-hand-types the three-string run, plus a textual check that the
  constitution's three **prose** copies still name every registry target.
- **Cut step 3** (`push_preflight.check()` returning `SCOPED`) at the elapsed
  reading, not at minute 34 — see below.

## What worked / what failed

- The consolidation is a net deletion: two 5-line literals and one 5-line test
  constant collapse to three `DECLARED_SUITE` references. `predicate_vacuity`'s
  self-confessing comment (*"Deliberately the same tuple `guard_vacuity` uses"*)
  is gone — the promise is now an import.
- `DEFAULT_SUITE is DECLARED_SUITE` is `True` in both censuses, so the four
  copies can no longer disagree by construction. That makes the *equality* half
  of the new test vacuous on purpose; what it actually guards is the **return**
  of a hand copy.
- **The interesting finding is which copies could drift.** The four that agreed
  are the four that can import. The three that cannot import — the constitution's
  prose — are the ones with no mechanism holding them, and they are exactly
  D-047's failure form. So the registry alone would have consolidated the safe
  half and left the dangerous half untouched; the prose scan is the part that
  earns its keep.
- `inert_surface staged` read `STAGED_MOVED` — adding one test file withdrew the
  exemptions on all five pins (`JOURNAL.md`, `RESULTS.md`, `STATE.md`,
  `journal/`, `results/`). It cost nothing here **only because D-315's order
  already puts the receipt last**: every write to those five was done before the
  suite, so there was no post-receipt drift to pay for. Under the pre-D-315
  order this same rc=1 would have been a guaranteed `STALE` refusal.
- `census_preempt` clean on all five re-derived censuses; its `UNCOVERED` line
  names four it does not reach, `inert_surface` pins among them — which is
  exactly the one that moved. The two readings are complementary, and reading
  only the clean one would have missed it.
- `cycle_wallclock elapsed` read `SUITE_AFFORDABLE` with **4m27** left to start a
  1533s suite. Steps 1–2 fit that window; step 3 opens `push_preflight` and does
  not. Scope was cut at that reading (D-181), which is the instruction working
  as designed rather than a budget overrun discovered late.

## North-star delta

- **No planner movement — 35 cycles now.** 0 rollouts; no controller,
  representation, or dynamics code touched. This is verification-surface work.
- Net LOC down; one registry replaces four hand copies. Simplicity criterion
  counts this as a win, but it is a win inside the meta-layer, not toward
  navigation.
- The prose-drift guard is the only part with a claim on future correctness: a
  target added in Python but not in the runbook now goes red instead of silently
  narrowing the suite a human runs.

## Key learnings

- **"Do the copies agree?" and "can the copies drift?" are different questions,
  and D-402 asked the first.** The answer to the first was yes, which reads like
  a clean bill; the answer to the second is what mattered. Consolidating only
  the importable copies would have been measurably correct and strategically
  beside the point.
- **A vacuous equality test is fine when you can say why.** After derivation the
  four values *cannot* differ, so asserting they match proves nothing. Naming
  that in the test docstring and pointing the assertions at the re-hand-typing
  instead keeps the file from being another D-060 instrument-eats-its-signal.
- **The elapsed reading is worth taking before the edit, not after.** It named a
  4m27 window up front, which is what made "ship steps 1–2, defer step 3" a
  decision rather than a rescue.

## Recommended next 1–3 priorities

1. **Finish D-402 step 3** — `push_preflight.check()` grades `receipt.command`
   against `DECLARED_SUITE`, returning `SCOPED` when a receipt does not cover
   it. The registry it needs now exists; budget a full cycle for the gate.
2. **Decide the 35-cycle scope question (user)** — D-390…D-402 without one
   rollout. This is the second cycle STATE has raised it.
3. **Guard the `*_raw` exemption risk (D-399)** — small, protects an existing
   defence.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/declared_suite.py, predicate_vacuity.py, guard_vacuity.py, tests/test_receipt_scope.py, tests/test_suite_coverage.py, tests/test_declared_suite.py
- TSV row appended: pending
