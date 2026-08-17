# Naming the registry clears the first live provenance exposure

- **Cycle**: 2026-08-18 07:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: (none picked — strand repair, per D-112 REVIEW step 0)
- **Phase**: P3
- **Status**: keep

## What I tried

- REVIEW step 0 returned `rc=1` naming **two** stranded cycles (05:00, 06:00).
  06:00 had already diagnosed the cause: the strand is not unpushed work, it is
  **red** work — its suite measured 3606/3609 and `push_preflight check` refused,
  exactly as D-082 designed. So the obligation this cycle was not "push", it was
  "make the tree green, then push".
- All three failures were one cause, already written up as **Q-164** with a lean
  toward option (a). I took that lean: restructure the guard so `OBSERVABLES` is
  named at the call site rather than fetched through `_observables_of(t)`.
- The repair is the one D-052 (b) prescribed *in advance* for this exact shape,
  and the `_provenance` docstring spells it out: "name the helper's registry at
  the call site (pass it, or alias it to a module constant), not widen this
  predicate."
- Split the old filter in two: `observable in OBSERVABLES` (the registry half,
  now a bare typed constant) and `_table_carries(observable, t)` (the half that
  genuinely depends on the table, returning a bool so it is not read as an
  exemption at all).

## What worked / what failed

- ✅ **Exposure back to `()`.** `provenance_depth_exposure()` returns empty, and
  the guard is still admitted — now `provenance='TYPED', constant='OBSERVABLES'`
  where it was `DERIVED, None`.
- ✅ **D-336's measurement reproduces exactly.** `obstacle_side_observables()`
  still returns `('obstacle_speed', 'path_lateral_speed')`, matching the
  `OBSTACLE_SIDE_OBSERVABLES` pin. Q-164's lean argued the restructure should
  cost nothing because D-336's finding is about the registry's *content*, not
  the path by which the guard reads it. That held.
- ⚠️ **The fix moved a fourth pin nobody had listed.** Naming the registry makes
  the guard visible to the **shallow** scan too, so it had to be withdrawn from
  `test_the_shallow_predicate_was_hiding_two_more_guards`'s deep-only set — the
  first entry ever to *leave* that set, running opposite to
  `magnitude_survival.published`, which entered it for the mirror-image reason.
  Q-164 predicted three test files; the true blast radius was four.
- ❌ **Verification by targeted pytest failed on time, not on content.** Running
  the five relevant test files serially blew a 600 s timeout — those files are
  cheap only when the suite shards them in parallel. I fell back to computing
  the three pinned quantities directly in-process (~1 s each), which is what
  actually confirmed the repair.

## North-star delta

- **No movement toward the north star, and this cycle should not pretend
  otherwise.** It is a repair of the verification machinery, not of the planner.
- What it *does* buy is the unblocking of two cycles of real P3 work (D-336's
  obstacle-side constancy finding + D-337's strand reading) that have been
  sitting ungradeable on disk since 05:00.
- The substantive P3 question — Q-162/D-334's finding that `cut_in` has **no**
  plan-time separator once scenario constants are removed — is untouched and
  remains the bottleneck.

## Key learnings

- **A guard-admission predicate and a provenance predicate disagreeing is not a
  bug, but it has a blast radius nobody prices at write time.** D-050/D-052
  argued the disagreement through and even wrote the repair down; what neither
  anticipated is that applying the repair *moves the guard between scans*, so
  the fix touches a pin the Q's own analysis did not name.
- **Q-164's cost estimate was low by one file, and the missing file was the
  census pin.** Worth generalising: when a repair changes how a scan *reaches*
  a guard, check the scan-comparison pins, not just the ones that were red.
- **`timeout N pytest <files>` is a bad verification instrument in this repo.**
  Serial file selection is slower than the sharded full suite for anything
  touching `guard_reflexivity`. Direct in-process computation of the pinned
  quantity is seconds and answers the same question.

## Recommended next 1–3 priorities

1. Land this branch — the PR (#67) has been open and blocked on a red tree for
   three cycles; nothing else on this branch can be graded until it merges.
2. Return to Q-162/D-334's live question: `cut_in` has no plan-time separator
   after constants are removed, which downgraded D-333's 5/5 coverage to an
   oracle-conditional bound. That is the real P3 bottleneck.
3. Consider whether `census_preempt` should carry a scan-comparison census, so a
   guard that migrates between shallow and deep is caught at stage (2 s) rather
   than by the suite (862 s) — Q-163's fifth-census idea, now with a second
   supporting instance.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/scene_separability.py, eval/mppi_sandbox/tests/test_guard_reflexivity.py, docs/decisions.md, docs/deliberations.md
- TSV row appended: pending
