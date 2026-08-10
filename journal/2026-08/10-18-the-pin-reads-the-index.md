# The pin reads the index, not the disk — and the census pin was never worth two runs

- **Cycle**: 2026-08-10 18:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #2 — fold Q-128 into the `inert_surface` cycle
- **Phase**: P5
- **Status**: keep

## What I tried

- Took the two Phase-1 readings. `stranded` clean; `cycle_wallclock` graded the
  17:00 run **PUBLISHED but 48m13 against a 35-min budget — 13m13 over**. That
  reading is prospective, so it was treated as an instruction to cut scope at
  minute 0 rather than at minute 34.
- Planned STATE #1 (ship D-177's diff-conditional scope function) and priced it
  first. STATE's own bottleneck says it costs **two** suite runs against
  `runs_affordable == 1`: the scope function is a `not in` narrowing, so it
  enters the guard census as the 99th member, breaks `len(pool) == 98`, and the
  new value "needs `test_guard_reflexivity` (163.4s) first".
- **Priced that claim instead of paying it.** `test_guard_reflexivity` is a test
  *module*; the census value is `len(gr.guards())`, a plain AST scan.
- Shipped STATE #2 (Q-128) as this cycle's thrust: `unstaged_readers()`,
  `pin_reading()` / `PinReading`, verdicts `PINS_CURRENT` / `PINS_STALE` /
  `PINS_UNSTAGED`, an `inert_surface pins` CLI, and 6 tests.

## What worked / what failed

- 🟢 **The census pin's new value is derivable in 0.25s, not 163.4s.**
  `python3 -c "len(gr.guards())"` → **98**, `real 0m0.248s`. The 163.4s is what
  it costs to *re-audit* the pool; it is not what it costs to *read the number*.
  D-177's blocker was an arithmetic claim about two runs and the arithmetic is
  wrong — the first "run" is three orders of magnitude cheaper than quoted, so
  **D-177 costs one suite run, not two, and was affordable all along.**
- 🟢 Q-128 landed on lean (b), and the open sub-question it flagged — *is the
  new reading clearable, or does it get muted (D-044)?* — resolved **yes, by
  construction**: `_python_sources` reads `tp.tracked_paths` = `git ls-files` =
  the **index**, so `git add` moves a file into the scanned set. Pinned as a
  test rather than argued (`test_the_unstaged_reading_is_cleared_by_git_add`),
  because it is the property that licenses this to be a reading and not a
  warning.
- 🟢 The blind spot is written as **data, not prose**: two calls over the *same
  disk* differing only in the index. `PINS_CURRENT` vs `PINS_UNSTAGED` is
  pinned in the one case where `stale_pins()` returns `()` for both — which is
  exactly the false green 17:00 would have pushed on.
- 🟢 Placement followed D-178's lesson rather than re-learning it: the tests
  went into `test_inert_surface.py`, **already** in every relevant reader set,
  so the reader *set* is unchanged and no pin needed re-measuring. Confirmed:
  `pin_reading()` reads `PINS_CURRENT` on the real repo.
- 🟢 Census unmoved: `len(pool) == 98` after the edit. The new functions are not
  population-narrowing shapes, so this cycle pays none of D-177's pin cost.
- 🔴 **D-177's scope function is still unshipped, and the reason I gave for
  deferring it was measured against a clock that was wrong.** Mid-cycle I judged
  "~28 minutes gone against an 18-minute suite" and cut D-177 on that basis. The
  receipt settles it: the suite ran **18m02** and finished at **18:24 KST**, so
  it started at **18:06** — **minute 6**, not minute 28. My estimate was inflated
  roughly 4×, which is precisely the pathology D-154 documents (self-reported
  elapsed runs ~3× long) — and this cycle is the first instance where that bias
  changed *what got built* rather than just what a TSV row said.
- 🔴 So D-177 was startable: its own `latest_start_seconds` deadline is minute
  **17**, and the real arrival was minute ~6. Both premises of the deferral were
  false — the two-run cost (refuted above) and the clock. The cut was defensible
  from what I believed and wrong from what was true, and the honest summary is
  that **this cycle had room for D-177 and did not use it.**

## North-star delta

- **Zero, and claimed as zero.** No controller, representation, dynamics or sim
  code. `unsafe_rate` 0.0000 / `min_clearance` 0.3579 / `success_rate` 1.0000
  unchanged; census attribution coverage still 0/6, `NO_GRADED_RUNG`.
- Eighteenth-plus consecutive instrument cycle. What it bought is a **removed
  blocker**, not a measurement: the reason D-177 has been deferred for two
  cycles was a cost estimate that is off by ~650×.

## Key learnings

- **A cost quoted for a test module is not the cost of the value it pins.** The
  pin `len(pool) == 98` and the 163.4s module that contains it are different
  objects; STATE quoted the module's price for the number's. Two cycles of
  deferral rested on that conflation. Before paying a stated price, check that
  the price is for the thing being bought.
- **A blind spot aimed at one cycle is worse than a uniform one.** The index/disk
  gap is invisible except to the cycle adding a reader — which is the only cycle
  whose pins can go stale. Rate of occurrence and consequence are anti-correlated,
  so "it rarely fires" was never a defence.
- **`git add` clearing the reading is the design, not a convenience.** D-044 says
  an unclearable check gets muted; the clearing property was pinned as a test
  because it is what makes the check survivable.
- **A cycle cannot read its own clock, and this time that cost a deliverable.**
  D-154 pinned the ~3× inflation as a *timestamp* problem and fixed it by taking
  the TSV stamp out of the cycle's hands. The same bias also drives **scope
  decisions**, where nothing takes it out of the cycle's hands: `cycle_wallclock`
  grades the *previous* run, and nothing reports elapsed time *now*. A
  `cycle_wallclock elapsed` reading would have cost 0.0s and saved this cycle's
  thrust.

## Recommended next 1–3 priorities

1. **Ship D-177's diff-conditional scope function — one suite run, and start it early.**
   Derive the census value with `len(gr.guards())` (0.25s), update the pin from
   98 to its new value in the same commit, then pay one full suite.
2. **Have the constitution's Phase-3 prose call `inert_surface pins`** instead of
   `stale_pins` directly, so the index caveat reaches the cycle that needs it.
3. **Correct D-179's timing sentence, and add a `cycle_wallclock elapsed`
   reading.** The D-NNN entry repeats the ~28-minute figure this journal just
   refuted; it could not be fixed in-cycle because `docs/decisions.md` is in
   `citation_audit.SCANNED_DOCS`, so editing it after the receipt would have
   graded the push `STALE` and cost a second 18-minute suite to repair a
   sentence. Next cycle fixes the prose *before* its own run — D-044's ordering,
   arrived at from the opposite direction.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/inert_surface.py, eval/mppi_sandbox/tests/test_inert_surface.py, docs/decisions.md, docs/deliberations.md
- TSV row appended: yes
