# The 96 helpers are doing their job; the residue is 11

- **Cycle**: 2026-08-11 07:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — triage the module-level public functions with no non-test caller
- **Phase**: P5
- **Status**: keep

## What I tried

- Extended `consumer_reach` with **population B** — every module-level public
  function in non-test modules of `eval/mppi_sandbox/` — reported separately
  from population A (alternative constructors) and never summed with it.
- Graded B and read what came back, rather than assuming the shape STATE
  assumed.
- Made `is_finding` key on **scope**: `TEST_ONLY` is A's defect and B's normal
  state; `UNREACHED` is the only verdict that reads the same in both.
- Added `FRAMEWORK_DISPATCHED` as a **verdict**, not a filter, for the
  `pytest_*` hooks.

## What worked / what failed

- 🔴 **The bottleneck's premise was wrong in the direction that matters.** It
  asked whether the package carries "a large write-only instrument surface,"
  pricing the answer at ~88 undifferentiated functions. Measured: population
  744, `LIVE`=626, `TEST_ONLY`=**96**, `REFERENCED_NOT_CALLED`=8,
  `FRAMEWORK_DISPATCHED`=2, `UNREACHED`=**11**. The 96 are `assert_*` /
  `*_census` / `*_screen` helpers that a test suite calls — **a helper the
  suite calls is being used for its purpose**, not dead weight. The write-only
  residue underneath them is an order of magnitude smaller than the number
  D-189 was avoiding.
- 🟢 So the answer is: the instrument cycles are **compounding, not
  accumulating**. That is the first direct evidence either way in three weeks.
- 🔴 **Two of the 13 raw `UNREACHED` were false alarms by construction.**
  `loop_reach.pytest_configure` / `pytest_unconfigure` are pytest plugin hooks
  — resolved by name by the framework, exactly as the interpreter resolves
  `__new__`, which is why `definitions()` already carries a dunder rule. The
  tempting fix is a filter; that would be a fifth unwatched allow list, which
  is the defect `guard_reflexivity` counts. Graded into their own verdict
  instead — visible in the report, excluded from the finding, hidden nowhere.
- 🟢 The instrument put **its own new function** in the residue on first run
  (`consumer_reach.module_findings`, `UNREACHED` until the test called it).
  Reflexive and correct — a good sign the population is honest.
- 🟢 `check` still grades A only; B is a **ratchet**, pinned by name in a test.
  11 uncalled functions cannot be cleared in one cycle, and a red standing for
  weeks is a red nobody reads (D-044).

## North-star delta

- **No movement, and this cycle claims none.** No controller, representation,
  dynamics, or sim code. `unsafe_rate` / `min_clearance` / `success_rate`
  unchanged, census attribution coverage still **0/6**, 0 sim runs.
- What moved is a three-week-old open question closed with a measurement: the
  instrument layer is not write-only debt.

## Key learnings

- **"N functions with no non-test caller" is not one number.** Splitting it by
  *what the absence of a caller means* turned a 96-item wall into a 96-item
  normal state plus an 11-item finding. The same verdict string can be a defect
  in one population and the healthy case in another — which is why `is_finding`
  had to key on scope rather than on the verdict alone.
- **A population excluded for a good reason still needs a reading eventually.**
  D-189's exclusion was right about burial and wrong as permanent silence; the
  fix was not to un-exclude but to report *separately*.
- **The framework-hook case generalises the dunder rule.** Any name an external
  framework dispatches by convention has no in-repo call site by construction.
  Grading it beats filtering it, every time.

## Recommended next 1–3 priorities

1. **Triage the 11 `UNREACHED` functions** — now a named, bounded list. Each is
   delete-or-wire, and the pin makes either choice a one-line edit.
2. **Decide `from_sweep`: keep as the re-walk landing site, or delete** —
   unchanged from last cycle; still A's only residue, still gated on the user's
   re-walk decision.
3. **Add the repo-wide instrument tests to the Phase-3 pre-check** —
   `test_loop_reach.py` + census pins. Fourth cycle running where this would
   have paid for itself.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/consumer_reach.py, eval/mppi_sandbox/tests/test_consumer_reach.py, docs/decisions.md
- TSV row appended: yes
