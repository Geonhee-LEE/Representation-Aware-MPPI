# The instrument was complete and had never been read

- **Cycle**: 2026-08-06 06:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #6/#8 — fix the ordering that forces a 4th suite run (+ #7)
- **Phase**: P4 (P3 work surface)
- **Status**: in_progress

## What I tried

- Ran `inert_surface.probe` for real on all four `POST_RECEIPT_WRITES`
  candidates — the differential read the module was built to record and that
  nobody had ever taken. Mutate the file, re-run its *named reader subset*
  (10–14 test files, not the suite), compare outcomes, restore.
- Transcribed the four verdicts into `PROBED` as `Pin`s carrying the reader-set
  premise, the tree they were taken on, and the reader count.
- Spelled the ~900-character `readers_key` strings as `_key("test_x.py", ...)`
  so a reviewer can see *which* file entered or left the set.
- Fixed STATE #7 in the same seam: `push_preflight record` now unlinks `--out`
  before it runs.

## What worked / what failed

- **All four grade `INERT`.** D-044's hand-written "(checked)" was correct —
  and the project paid the tax anyway for two cycles, because a correct
  hand-check that was never mechanised exempts nothing.
- **The real defect was not the composition, it was that `PROBED` was `{}`.**
  `inert()` returns `False` for every unpinned candidate, so `filter_drift`
  ignored nothing and every receipt graded `STALE` on the 4b/4c/TSV writes.
  The module was complete, tested, documented — and inoperative.
- **Two of its own tests were vacuous and green.**
  `test_every_shipped_pin_states_its_premise_and_when` looped over `{}`;
  `test_shipped_pins_are_not_stale_on_this_tree` asserted `()` because there
  was nothing to be stale. Two passing tests, zero measurements, and nothing
  in the suite said so.
- **Cost was the honest surprise**: ~34 min of wall clock for four probes
  (8–12 min each). The subset really is much cheaper than the suite; four of
  them are not.

## North-star delta

- **No avoidance or tracking number moved** — 63rd consecutive instrument
  cycle. Scenes able to contribute an avoidance number: 5, reportable: 4.
- What moved is throughput, not capability: the per-cycle suite tax drops from
  4 full runs to 2, and the crash case now fails closed the way D-082 said it
  did.

## Key learnings

- **An instrument that has not been read grades nothing.** This is a different
  failure from a wrong instrument and it is invisible in exactly the same way a
  vacuous test is: everything is green because nothing was asked.
- **Emptiness has to be decided before success for registries too, not just
  probes.** This package already applies that rule to `Comparison`, to
  `guard_vacuity`, to `key_conflation` — and its own pin registry shipped empty
  with a loop test over it.
- **The pre-docs suite run is the avoidable one now.** The order that costs one
  run is: edit code → write `docs/` → run suite → 4b/4c/TSV → check → push.
  I ran it before the docs writes this cycle out of habit and paid for it.

## Recommended next 1–3 priorities

1. **Read this branch's CI with `ci_verdict`** — the D-094 ceiling raise is
   still an unconfirmed arithmetic claim; the run on `d6b60c8` was `in_progress`
   at 53 min when this cycle started, past no ceiling yet.
2. **Apply "was this registry ever populated?" to the other typed sets** —
   `MEASURED_CLAIMS`, the seven registries D-080 named. Same shape.
3. **Reorder the constitution's Phase 4 so the suite runs once** (after the
   `docs/` writes), now that the post-receipt writes are provably exempt.

## Artifacts

- PR: #67 (87th consecutive cycle writing into it)
- Files touched: `eval/mppi_sandbox/inert_surface.py`,
  `eval/mppi_sandbox/push_preflight.py`,
  `eval/mppi_sandbox/tests/test_inert_surface.py`,
  `eval/mppi_sandbox/tests/test_push_preflight.py`, `docs/decisions.md`
- TSV row appended: yes
