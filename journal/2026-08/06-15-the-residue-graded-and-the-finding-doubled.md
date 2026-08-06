# The residue graded — and the finding doubled

- **Cycle**: 2026-08-06 15:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — grade the remaining 3 residue sites (Notion unreachable, 96th cycle)
- **Phase**: P4 (calendar) / P3 work
- **Status**: in_progress

## What I tried

- Asked what the exclusion list settles **before** paying for a run.
  `self_entry_is_impossible()` is a one-sided bound: `SELF_ENTRY` needs an
  excluded file that is the site's own instrument, so a site whose module has no
  excluded test is `COLLATERAL` by construction, with no suite at all.
- Took the measurement the bound could not replace — one attributed run
  (`measure_attributed(pop, excluded=())` → `effect_from_one_run`), 10 min 23 s.
- Turned the loop-body `assert` in
  `test_self_entries_are_the_majority_and_are_left_alone` into collect-then-assert,
  and added a slow test that grades **every** residue site off the same fixture
  and prints the whole table on failure.
- Recorded per-site provenance (`SOURCE` / `SOURCES`): three of the four grades
  were taken on this box, not on CI.

## What worked / what failed

- ✅ **The residue is 2 / 2, and the half nobody read is the half that matters.**
  `exclusion_scope.RankAgreement.reportable` and `ReplicatedReading.licensed` are
  `SELF_ENTRY`; `predicate_inputs.Drift.stationary` and `Spread.stationary` are
  **`COLLATERAL`**. So the finding is **four** sites, not two. For
  `Spread.stationary` the *sole* hider is `test_exclusion_scope.py` — not its
  instrument. That is verbatim what the self-entry assertion's docstring says it
  exists to catch, and it had already fired: the loop reported the first violator
  it reached, which was one of the two harmless ones.
- ✅ **The run-free bound settled both headline sites and none of the residue.**
  `guard_reflexivity` and `local_only_audit` have no excluded test, so the
  D-061/D-062 pair was `COLLATERAL` by construction — the grade never needed a
  measurement. `RUN_FREE_DISCHARGED = ()` is kept rather than deleted: an empty
  result is the price tag on the run, not an absence.
- 🔴 **A second live defect, and it survived D-100's own repair by two lines.**
  `manufactured_candidates`' docstring has said "the subset of `collateral`" for
  thirty-odd cycles and a slow test asserted it. It is **false** — two of the six
  are `SELF_ENTRY`. D-100 diagnosed exactly this shape (a property of the
  population promoted to an invariant) two `assert`s earlier in the same test and
  left this one standing, because the test died before reaching it. Would have
  been a fresh CI red on the next run.
- 🔴 **The rule that covered three sites now covers none.** "An ungraded site
  reads `UNREAD`" lost its whole live population the moment the residue was
  graded — the vacuous-over-empty shape that already bit this branch on 06-06. So
  `reading()`/`coverage()` take the table as a call-time parameter and the rule is
  exercised on a seventh site that does not exist, plus a negative control that
  drops an entry and requires the site to reopen.
- 🔴 **Gate 1 fired for the 115th time** — queue = 6, unchanged, 24.9 d since the
  last merge. Work continues on the already-open PR #67, costing no new review
  bandwidth. `.last_escalation` floor is 08-06 22:19, so no escalation this cycle.

## North-star delta

- **No avoidance or tracking number moved — sixty-eighth consecutive instrument
  cycle.** Scenes able to contribute an avoidance number: 5, reportable: 4.
- What moved: the `COLLATERAL` finding is now **measured at four sites** rather
  than pinned at two with three sites unread, and one more would-be CI red is
  fixed before CI saw it.

## Key learnings

- **Ask what the cheap instrument settles before buying the expensive one — and
  keep the answer even when it is empty.** The bound discharged the headline pair
  for free and nothing of the residue; recording that emptiness is what justifies
  the ten minutes.
- **A loop-body `assert` is a sampling policy nobody chose.** It converts "grade
  every violator" into "grade whichever the iteration order reaches first", and
  the sample it returns is not random — here it returned both harmless sites and
  neither actionable one, across two separate CI runs.
- **Diagnosing a defect class does not sweep it.** D-100 named
  property-promoted-to-invariant and repaired the instance it could see; the
  identical instance two lines down went unrepaired because no run had ever
  reached that line. Fixing the reachable one is not the same as searching.
- **`every`, not `some`.** `Drift.stationary` is hidden by its own instrument
  *and* a foreign one; the weaker reading of `grade` would have filed it as
  bookkeeping. A site a foreign file can hide is hidden.

## Recommended next 1–3 priorities

1. **Decide Q-095** — scope `EXCLUDED_TESTS` per subject rather than per file.
   The finding says the mechanism is mis-scoped, not the list. Wants a dedicated
   branch after the chain merges (contract change → full re-baseline).
2. **Sweep the other assertions this branch promoted from population.** Two found
   in two cycles, both by running rather than by reading. Ask it of every
   `assert x <= y` over a measured set.
3. **Hunt other loop-body asserts over measured populations** — the same sampling
   policy, wherever a test iterates a measured set.

## Artifacts

- PR: #67 (already open, 91st consecutive cycle writing into it)
- Files touched: `eval/mppi_sandbox/candidate_scope.py`,
  `eval/mppi_sandbox/exclusion_scope.py`,
  `eval/mppi_sandbox/tests/test_candidate_scope.py`,
  `eval/mppi_sandbox/tests/test_exclusion_scope.py`, `docs/decisions.md`,
  `docs/deliberations.md`
- TSV row appended: yes
