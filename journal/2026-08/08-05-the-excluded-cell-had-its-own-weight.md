# The excluded cell had its own weight, and the weight axis is not an interval

- **Cycle**: 2026-08-08 05:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `STATE-1-q113` Answer Q-113 — is the operating weight per-scene or per-cell?
- **Phase**: P5
- **Status**: keep

## What I tried

- Ran Q-113's own proposed instrument unchanged: `relief_interval.survey` on
  `cafe_obstacle_crossing_v0` alone with `controller="risk_mppi"`. The function
  was already parameterised by controller, so the question cost one sim run and
  no new code — the per-cell survey Q-113 asked for already existed.
- Extended the ladder one rung past `DEFAULT_LADDER`'s top (to **10000**) so the
  answer would not sit on the ladder's edge untested-above, which is the
  honest-limit shape D-126 booked for convoy's floor.
- Captured the whole rung table (unsafe, clearance, reached, median ESS, band,
  worst `cte_rms`) rather than the survey's one-line verdict, because the
  verdict alone cannot show *why* the rungs between failed.
- Shipped `operating_weight.audit_cell` + `CellAudit` + `admits` +
  `render_audits` with 9 tests.

## What worked / what failed

- ✅ **Q-113 answers: the cell has an admissible weight of its own — 3000, not
  the scene's 1000.** So D-127's `ESS_OUT_OF_BAND` exclusion was a **keying
  artefact**, not a cell that is unanswerable on the weight axis. At 3000 the
  cell reads `unsafe_rate` **0.0000**, `min_clearance` **1.6978**, all 8 seeds
  reaching, ESS in band, worst `cte_rms` **0.2228** against the scene's declared
  0.40 — so the relief is not paid for on the scene's other declared key either.
- 🔴 **The transferable finding is the shape of the admissible set, and it is
  worse than "different".** Median ESS walks **91.9 → 80.1 → 205.5 → 204.7 →
  157.6 → 27.5 → 11.9** across w = 10 (baseline), 30, 100, 300, 1000, 3000,
  10000, and the band admits only **w=10 and w=3000**. The tolerated set is
  **two islands `{10, 3000}`** separated by five rungs that all fail — and they
  fail in *both* directions (100/300/1000 sit too high, 10000 too low). Interval
  arithmetic over `[min, max]` would nominate 100, 300 and 1000, every one of
  them inadmissible on the very cell the interval came from.
  `relief_interval`'s preamble refused to assume contiguity and had only a
  **synthetic** mid-ladder-hole witness; this is the live one, on a shipped cell.
- 🔴 **Nothing in `operating_weight` could have seen D-127's exclusion coming.**
  `weights()` hands the cell a float and the cell discovers its own
  inadmissibility afterwards, as a missing row in the denominator. That is the
  actual defect Q-113 names, and it is a *reporting* defect, not a tuning one.
  `audit_cell` closes it: the excluded cell is now named from a measurement
  **before** the matrix runs.
- 🟡 **3000 is a knife-edge and the audit says so.** It is the *only* rung the
  cell tolerates — both neighbours fail — so it is a reportable measurement, not
  a robust operating point. `CellAudit.knife_edge` exists so `cell_weight` is
  never printed alone, because a bare 3000 reads far more solid than it is.
- ✅ **The shipped-weight-is-never-a-rung category error was already waiting one
  layer out.** `admits` would have been wrong as `weight in admissible`: the
  ladder never contains 10.0, so a cell asked about the shipped weight must be
  asked via `baseline_admissible`. This is the *second* sighting of the bug that
  bit `resolve()` last cycle, so it is one function with one test rather than an
  inline `in` per call site (D-047). Two tests pin it.
- ✅ Census bill **nil** (`decides`/`defaults`/`inert_defaults`/`forwards` all
  unmoved) and `citation_audit` green on the pre-flight, caught in **33 s** —
  the D-117 discipline paid for the third cycle running.

## North-star delta

- **D-127's honest split closes on the measurement side**: the 8 seeds that
  "left the denominator instead of being answered" are answered — that cell is
  0/8 unsafe at a weight it admits. The 0.0000 headline's missing cell is no
  longer a hole, it is a named `CELL_DIFFERS` with a measured alternative.
- **But the headline itself does not move this cycle**, deliberately. Adopting
  3000 for that one cell would key the table by cell and re-confound the
  cross-controller delta on a second axis (D-123's structure on the weight
  knob). Q-113's lean — measure per-cell, report per-scene, name the excluded
  cell — is what shipped.
- Weight-axis admissibility is now **known non-monotone on real hardware-free
  data**, which retires interval arithmetic as an option for every future sweep
  on this knob rather than leaving it a stated worry.

## Key learnings

- **A cell leaving a denominator and a cell being unanswerable look identical
  from the aggregate, and only a per-cell measurement separates them.** D-127
  reported the exclusion honestly and still could not tell which it was; one
  ~1-minute run did.
- **When a design refuses an assumption for stated reasons, the refusal is worth
  keeping even with no witness — the witness may arrive on a shipped cell.**
  `reconcile`'s set intersection was defended on a synthetic hole three cycles
  ago and would have shipped a wrong rung today.
- **The same category error recurs at each layer that re-asks the question.**
  `shipped in permits` bit `resolve`; `weight in admissible` was the identical
  bug in `admits`. Extracting the predicate once is the fix that scales.
- Extending a ladder by one rung is cheap insurance against the answer landing
  on the edge: 10000 turned "3000 is the ceiling, untested above" into "3000 is
  a one-rung island", which is a different and more useful claim.

## Recommended next 1–3 priorities

1. **Audit the *other* seven matrix cells against their scene weights** — the
   same ~1 min/cell survey. If more than one cell is `CELL_DIFFERS`, the
   scene-keyed headline's matched-arms justification weakens and Q-113's
   trade-off has to be re-argued with a count instead of one instance.
2. **Re-run D-119 / D-124's A/Bs above the relief threshold** (still open from
   D-125) — both were scored ~30× below it, where both arms fail.
3. **Answer Q-112 — densify the ladder between 100 and 300.** Now sharper: the
   islands finding means ladder density decides which rungs are *visible*, not
   just how precisely a threshold is located.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic, #67)
- Files touched: eval/mppi_sandbox/operating_weight.py, eval/mppi_sandbox/tests/test_operating_weight.py, docs/decisions.md, docs/deliberations.md, results/p3-epistemic-shadow-cost-critic.tsv, journal/2026-08/08-05-the-excluded-cell-had-its-own-weight.md
- TSV row appended: yes
