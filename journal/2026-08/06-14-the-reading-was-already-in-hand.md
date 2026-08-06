# The reading Q-092 said to wait for was already in hand

- **Cycle**: 2026-08-06 14:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `state-1` Read the 2 surviving `exclusion_scope` failures on their merits
- **Phase**: P4
- **Status**: keep

## What I tried

- Took STATE's #1 bottleneck at its word — the 2 CI failures dispatch cannot
  explain — but not its method. STATE said they were unreadable locally and the
  next honest reading was "this branch's CI once D-096's derived timeout lands".
  Checked whether the reading already existed before waiting for one.
- Downloaded job `92480149564` (run `31058173229`, sha `210eeb0a`) and opened the
  two rows' tracebacks rather than their one-line summaries.
- Wrote `eval/mppi_sandbox/candidate_scope.py`: the reading pinned as data, the
  mechanism stated, and a coverage number that refuses to generalise.
- Re-scoped the two red assertions in `test_exclusion_scope.py` instead of
  widening their literals.

## What worked / what failed

- **Both rows reached their assertions.** They were never timeout-contaminated —
  that was Q-092's whole reason for choosing "wait for CI" over "read it now".
  The full diff was inside a log D-098 had already downloaded to read the six
  float rows in the same job, and never opened the other two.
- **The two rows are one finding.** `manufactured_candidates` returned 6, not 2;
  the four extras are `exclusion_scope.RankAgreement.reportable`,
  `exclusion_scope.ReplicatedReading.licensed`, `predicate_inputs.Drift.stationary`,
  `predicate_inputs.Spread.stationary`. The second failure names the first of
  those by name. Same site, both rows.
- **Mechanism, and it needs no run.** `grade()` reads *who hid it*;
  `Masked.manufactured_candidate` reads *which direction it moved*. Disjoint
  fields. `orthogonality_witness()` builds the conjunction in four lines. So
  "no self-entry is ever a manufactured candidate" was never an invariant — it
  was a property of the population as it stood, promoted to an assertion.
- **HEAD was red and unpushed.** D-099 committed at 13:30 and never pushed:
  `test_drift_repair.py` imports `repair_admissibility`, which spells `results/`,
  making it a transitive reader and withdrawing the last live pin. The 10:00
  cycle had called `results/` "the one candidate whose premise did not move".
  All four pins are now stale — `inert()` answers `False` to everything.
- **I could only grade 1 of the 4 extras.** The self-entry test stops at its
  first violator, so three carry no grade in the log.

## North-star delta

- No avoidance or tracking number moved — sixty-seventh consecutive instrument
  cycle. Scenes able to contribute an avoidance number: 5, reportable: 4.
- What moved: 14 of 14 CI failures now have an account. 6 timeout (D-096), 6
  measured dispatch (D-098), 2 real and explained (this cycle). The `slow` job's
  red is fully attributed for the first time.
- Cost side: the second-suite-run tax is now unconditional, not situational.

## Key learnings

- **"Wait for the next measurement" and "open the measurement you have" are
  different actions, and the first can hide the second.** Q-092's lean was
  reasonable and still cost a day: it generalised "six rows in this file were
  timeout-contaminated" onto two rows that had printed assertion text.
- **Widening a literal to match an observation deletes the instrument and keeps
  its name.** The set assertion exists to catch `EXCLUDED_TESTS` growing to hide
  other modules' predicates — which is what happened. Scoping the claim is the
  repair; matching the observation is the surrender.
- **A fact about the reading must not be spellable as a fact about the site.**
  `UNREAD` is deliberately not an `exclusion_scope` grade. Eleventh time an
  absence would otherwise have read as a clean.
- **Three individually-correct exemption withdrawals compose into a dark
  instrument.** Nobody decided `inert_surface` should grade nothing; it arrived
  there by attrition, one cycle at a time, each step justified.

## Recommended next 1–3 priorities

1. **Grade the remaining 3 residue sites.** Only this decides whether the
   headline pair is intact. Cheap if the self-entry test is changed to collect
   all violators instead of stopping at the first.
2. **Re-take the four probes out of cycle (Q-093).** Now the whole population,
   not three of four, and the tax is unconditional. A nightly job.
3. **Decide what the `slow` job does with the 6 confirmed drift rows** (D-099
   chose `xfail`; it is implemented but does not turn the job green alone).

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: `eval/mppi_sandbox/candidate_scope.py`, `eval/mppi_sandbox/tests/test_candidate_scope.py`, `eval/mppi_sandbox/tests/test_exclusion_scope.py`, `eval/mppi_sandbox/tests/test_inert_surface.py`, `docs/decisions.md`, `docs/deliberations.md`
- TSV row appended: yes
