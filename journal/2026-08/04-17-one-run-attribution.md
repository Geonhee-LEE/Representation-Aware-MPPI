# One-run attribution — and D-063 named the wrong file

- **Cycle**: 2026-08-04 17:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — finish D-063's attribution run (via STATE #2 / Q-076 (b))
- **Phase**: P4 (calendar) / P3 (work)
- **Status**: keep

## What I tried

- STATE #1 asked for the 6-run attribution D-063 could not afford. Before
  running it, **priced it**: one instrumented suite run is **4 min 57 s**, and
  the loop is `2 + len(EXCLUDED_TESTS)` = **6** runs, not the `1 + len(...)` = 4
  the module's own docstring claimed. True bill ≈ **30 min** against a stated
  4 — mispriced **7.5×**.
- So took Q-076 (b) instead: record the **originating test file** on every
  observation (`predicate_vacuity.measure_attributed` + `fold`), which turns
  "what if file *X* had been `--ignore`-d" from another run into a filter over
  one record. `exclusion_scope.effect_from_one_run` reconstructs base, lift and
  all four per-file lifts from a single measurement.
- Did **not** assert the counterfactual — checked it.
  `reconstruction_disagreements` compares the reconstructed base against a real
  `--ignore` run, site by site.
- Rewrote the two slow tests (which cost 6 runs *each*, ~60 min for the pair,
  which is why they had never been green) onto one module-scoped record.

## What worked / what failed

- ✅ **The reconstruction is exact where it was checked**: 0 disagreements over
  **62** predicates between the folded record and a measured base run. Cost
  **2** runs against 6, and unlike 6 it carries its own calibration.
- 🔴 **D-063's attribution was half wrong, and wrong on the site that mattered.**
  The grades survive — both headline sites are `COLLATERAL` — but
  `guard_reflexivity._shells_out_to_git_diff` is hidden by
  **`test_predicate_vacuity.py`**, not by `test_guard_witness.py` as D-063 wrote.
  `local_only_audit.guard_is_derived` → `test_guard_witness.py` is correct.
  1 of 2.
- 🔴 **Why the call graph misread it, in numbers.** `test_guard_witness.py`
  calls that predicate **188** times and every one returns `False` — a heavy
  caller carrying zero information, which is exactly what made it a plausible
  culprit to read off a call graph. The verdict turns on **one** `True` out of
  5944 calls, and that one is **D-062's own witness**, written to show this
  predicate satisfiable, living in an excluded file. The census hid the only
  evidence that its top candidate was not vacuous.
- ✅ `unattributable_calls()` is **empty** — every observation has an owning test
  file, so nothing survives the fold unattributed. Reported rather than assumed.
- ⚠️ The slow suite's own re-run had not finished at write time; the numbers
  above are read off a completed attributed run plus a completed base run, and
  the first slow pass is what **found** the wrong attribution (it failed the
  assertion that encoded D-063's claim).

## North-star delta

- **No avoidance or tracking number moved — thirty-second consecutive instrument
  cycle.** Scenes able to contribute an avoidance number: 5, reportable: 4.
- What moved: a measurement that was budgeted at 30 min and never run now costs
  ~10 min and has run, and it **overturned** a published attribution rather than
  confirming it. The 가려진-obstacle class still has exactly one working cost
  term (D-027).

## Key learnings

- **Price the measurement before planning around it.** D-063 was not
  over-ambitious; it was working from a cost that had never been executed, off
  by 7.5×. In a package whose entire theme is "state your population rather than
  assume it", the unstated quantity was its own bill.
- **A call count and a call graph fail the same claim in opposite directions.**
  188 informationless calls looked like the culprit; the single decisive call
  did not. Neither instrument could have found this — only an origin recorded
  per observation.
- **The cheap reading was not a compromise, it was the enabling condition.**
  Q-076's lean assumed the expensive run had to land first as calibration. Half
  true: only *one* run of it is needed, and spending the other five would have
  bought the same answer 20 minutes later.
- **`SELF_ENTRY` is still a filename convention.** The origin is a file, not a
  subject, so the derivation Q-076 wanted is only half done.

## Recommended next 1–3 priorities

1. **Re-read the 5 surviving one-sided candidates** — D-062's `by_input_diversity`
   ordering was taken over a population that includes both withdrawn artifacts.
2. **Ask the same question of `guard_vacuity.EXCLUDED_TESTS`** — now affordable:
   the same origin recorder applies to a coverage census.
3. **Derive `SELF_ENTRY` from the subject rather than the stem** — the remaining
   half of Q-076.

## Artifacts

- PR: #67 (open, autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: `eval/mppi_sandbox/predicate_vacuity.py`,
  `eval/mppi_sandbox/exclusion_scope.py`,
  `eval/mppi_sandbox/tests/test_exclusion_scope.py`,
  `eval/mppi_sandbox/tests/test_predicate_vacuity.py`,
  `docs/decisions.md`, `docs/deliberations.md`
- TSV row appended: yes
