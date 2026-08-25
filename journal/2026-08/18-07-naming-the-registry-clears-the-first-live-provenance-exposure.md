# Naming the registry clears the first live provenance exposure

- **Cycle**: 2026-08-18 07:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: (none picked — strand repair, per D-112 REVIEW step 0)
- **Phase**: P3
- **Status**: in_progress

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
- ❌ **The tree is still red, and the strand is NOT cleared.** The receipt suite
  (866.98 s, 14 shards) returned **3604 passed / 164 skipped / 5 failed**, and
  `push_preflight check` refused. Five is *more* than the three I set out to fix.
- ❌ **Q-164's "three failures, one cause" premise was wrong.**
  `test_guard_direction::test_the_exclusion_is_not_special_cased_to_the_guard_it_drops`
  was one of the original three and **still fails** after the repair. Two of the
  three did clear (the `predicate_depth` and `exemption_masking` exposure pins),
  so the cause was shared by two, not three.
- ❌ **Three new failures cascaded from the pin I bumped**, in exactly the
  direction D-330 warned about: `exemption_control` (its "four unwatched lists"
  control), `exemption_masking::test_module_global_route_covers_the_rest`
  (`assert (21 + 2) == 22`), and two in `magnitude_census`. Admitting
  `OBSERVABLES` to the `TYPED` population is not a local pin bump — it moves a
  count that four other modules reconcile against.
- ❌ **Verification by targeted pytest failed on time, not on content.** Running
  the five relevant test files serially blew a 600 s timeout — those files are
  cheap only when the suite shards them in parallel. I fell back to computing
  the three pinned quantities directly in-process (~1 s each), which is what
  actually confirmed the repair.

## North-star delta

- **No movement toward the north star, and no movement on the strand either.**
  Three cycles of P3 work (D-336, D-337, and now D-338) remain ungradeable on
  disk, and the branch is still unpushable.
- The one durable gain is diagnostic: `provenance_depth_exposure` is genuinely
  back to `()`, and the *cost* of getting it there is now measured rather than
  guessed — 5 red tests across 4 files, which is what Q-165 needs to be decided
  properly.
- The substantive P3 question — Q-162/D-334's finding that `cut_in` has **no**
  plan-time separator once scenario constants are removed — is untouched and
  remains the bottleneck.

## Key learnings

- **A guard-admission predicate and a provenance predicate disagreeing is not a
  bug, but it has a blast radius nobody prices at write time.** D-050/D-052
  argued the disagreement through and even wrote the repair down; what neither
  anticipated is that applying the repair *moves the guard between scans* and
  *changes a watched population's cardinality*, so the fix touches pins the Q's
  own analysis did not name — four of them.
- **Q-164's cost estimate was low by three files, and the direction of the miss
  is the lesson.** I found the fourth pin (the shallow/deep set) statically and
  assumed that was the blast radius. It was not: admitting a constant to the
  `TYPED` population moves a *count*, and counts get reconciled by modules that
  never mention the constant. Static reasoning found every pin that names the
  guard; only the suite found the ones that name its cardinality.
- **D-330's rule looks right and my choice against it looks wrong.** I took
  Q-165 option (a) — keep the do-nothing membership test, bump the pin — largely
  because deleting the test would drop the guard from the pool. The suite says
  (a) costs at least four more reconciliations. That is evidence for (b)/(c),
  and it arrived 866 s *after* the decision instead of before it.
- **`timeout N pytest <files>` is a bad verification instrument in this repo.**
  Serial file selection is slower than the sharded full suite for anything
  touching `guard_reflexivity`. Direct in-process computation of the pinned
  quantity is seconds and answers the same question.

## Recommended next 1–3 priorities

1. **Decide Q-165 first, then re-run once.** The next cycle should not re-take
   the suite before choosing between (a) bump four more reconciliations, (b)
   delete the membership test and let the guard leave the pool, or (c) make
   `_table_carries` set-valued. Each costs 866 s to verify, so the choice must
   be made statically. My read after this cycle: (b) or (c), not (a).
2. `test_guard_direction::test_the_exclusion_is_not_special_cased_to_the_guard_it_drops`
   needs its own diagnosis — it survived the repair, so it is a second cause
   that Q-164 folded into the first by mistake.
3. Return to Q-162/D-334's live question: `cut_in` has no plan-time separator
   after constants are removed, which downgraded D-333's 5/5 coverage to an
   oracle-conditional bound. That is the real P3 bottleneck.
4. Consider whether `census_preempt` should carry a scan-comparison census, so a
   guard that migrates between shallow and deep is caught at stage (2 s) rather
   than by the suite (862 s) — Q-163's fifth-census idea, now with a second
   supporting instance.

## Artifacts
- PR: #67 open, still unpushable (red receipt; `push_preflight check` refused)
- Files touched: eval/mppi_sandbox/scene_separability.py, eval/mppi_sandbox/tests/test_guard_reflexivity.py, docs/decisions.md, docs/deliberations.md, journal/2026-08/18-07-*.md
- Receipt: 3604 passed / 164 skipped / **5 failed** in 866.98 s across 14 shards (RED)
- TSV row appended: yes
