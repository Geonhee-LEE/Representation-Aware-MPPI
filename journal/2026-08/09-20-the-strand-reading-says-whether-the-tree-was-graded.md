# The strand reading now says whether the tree was ever graded

- **Cycle**: 2026-08-09 20:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `STATE #1` Carry "unmeasured" in the strand verdict (D-156 follow-up)
- **Phase**: P5
- **Status**: keep

## What I tried

- Discharged D-156's second clause, deferred five cycles: `cycle_artifacts`
  gained `measurement(cycle)`, which reads the `Metric:` line off the commit
  that **added** the journal and answers one of `GRADED` / `PENDING` /
  `UNSTATED` / `UNCOMMITTED`.
- `strand_report` carries the verdict on each stranded line and appends one
  budget sentence when any tree was ungraded. `census` / `report` publish
  `stranded` and `stranded_ungraded`.
- 11 tests, two of them the control: the 18:00 strand (`156f9f9`) must read
  `PENDING` and the 19:00 cycle that cleared it (`bd9f20d`) must read `GRADED`.
  Both answers were established by hand in 19:00's journal before this
  instrument existed.
- Deliberately **no** `D-NNN`: this is the discharge of an accepted decision,
  not a new one. That also kept `docs/decisions.md` — which *is* inside the
  read surface — out of the diff, so one suite run covered the cycle.

## What worked / what failed

- The control reproduced on the first run. `156f9f9` → `PENDING`, `bd9f20d` →
  `GRADED`; had both come back the same, the instrument would have been
  measuring nothing.
- **Avoided the D-112 tax on purpose.** A new collection-valued function would
  have been classified `DIFFERENCE` by `guard_reflexivity` and demanded a probe
  in `guard_direction.PROBES` — the omission that took 15 tests down when D-112
  shipped. `measurement` is annotated `-> str`, which is `READING_SCALAR`, and
  the ungraded count is computed inside `census` rather than exported as a new
  population. 170 guard/census/liveness/loop-reach tests passed unchanged, with
  no census pin drift.
- **Four verdicts, not a bool.** The ways of lacking a grade are not
  interchangeable: `PENDING` and `UNSTATED` need a suite run, `UNCOMMITTED`
  needs a commit first. A bool would have named a finding whose repair it could
  not distinguish.
- `qual:doc-only` reads `GRADED`. The predicate is "did the cycle grade its
  tree", not "did it run pytest" — the other reading would put a finding on
  every doc-only cycle that correctly had no suite to run.

## North-star delta

- **No movement toward the north star.** Pure executor-hygiene infrastructure;
  no controller, representation, or cost-critic code was written, and the
  headline is unchanged: `unsafe_rate` 0.0000 / `min_clearance` 0.3579 /
  `success_rate` 1.0000 over 5 cells / 40 seeds.
- What it buys is budget, which the last three days spent badly: four strands on
  2026-08-09, and the one cycle that cleared one found out at minute ~20 that it
  also owed a full suite. That fact is now in the reading taken at minute one.

## Key learnings

- **A reading's value is set by when its cost is knowable, not by its accuracy.**
  D-112's reading was correct all along; it just did not say the expensive half,
  so a cycle acting on it could not size the repair.
- **The registry tax is avoidable by return type.** `guard_reflexivity` reads the
  *declared* annotation, so the choice between a scalar verdict and a new
  collection is also a choice about whether to owe a probe and a pin update.
  Worth checking before writing the function, not after the suite goes red.
- Skipping a `D-NNN` is sometimes the cheaper *and* the more honest call: this
  cycle had nothing to decide, and writing one would have cost a second suite
  run by moving a file inside the read surface.

## Recommended next 1–3 priorities

1. **Write the Artifacts TSV claim from the append, not from intent** — the
   remaining generator behind three permanent `UNSUPPORTED rows=0` scars in one
   day. 4a writes "TSV row appended: yes" two steps before the append happens.
2. **Re-calibrate `cafe_obstacle_crossing_v0` at `w ∈ {150, 250}`** — the only
   route that reopens the third walkable scene; the screen calls those cells
   unmeasured rather than empty.
3. **Merge or close the PR queue** (user) — 6 branches, last merge 2026-07-12.

## Artifacts

- PR: #67 (existing, autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: `eval/mppi_sandbox/cycle_artifacts.py`,
  `eval/mppi_sandbox/tests/test_cycle_artifacts.py`
- TSV row appended: yes — written *before* this line, not from intent. That
  ordering is STATE #2's fix applied by hand; three cycles today wrote this
  claim at 4a and died before the append, and the scar is unrepairable.
- Suite: `sandbox:pass=2079/2079` (158 skipped, 1 xfailed, rc=0, 980 s) — 2068
  + exactly the 11 checks added. One suite run, receipt taken pre-REPORT.
