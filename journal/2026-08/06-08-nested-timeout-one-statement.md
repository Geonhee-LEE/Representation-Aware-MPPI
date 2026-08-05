# The ceiling raise is confirmed, and the job's actual defect finally spoke

- **Cycle**: 2026-08-06 08:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — read this branch's CI with `ci_verdict`
- **Phase**: P4
- **Status**: keep

## What I tried

- Ran STATE #1 — the item that has sat at the top of the board for four cycles
  because only a *completed* `slow` run could discharge it. One had completed:
  run `31042602721` on `d6b60c8`, and `ci_verdict` reads it per job.
- Read the failures it published — the first legible ones in twelve-plus runs —
  and classified all 14 rather than fixing the first.
- Built `nested_timeout.py`: an AST scan that **measures** how many places state
  the nested-suite timeout, derives the requirement from the worst observed
  suite cost × `declared_ceiling.HEADROOM_FACTOR`, and grades each site.
- Collapsed the seven statements into one (`nested_suite_cost.NESTED_TIMEOUT_SECONDS`,
  900 → 2792) and wired all six spawns to import it.

## What worked / what failed

- ✅ **D-094 is confirmed.** `slow` ran **162.7 min against the 360 min cap,
  +55% headroom, not killed** — the first completed run since the raise. The
  arithmetic D-094 could only assert is now measured. `fast` is `PASS`.
- 🔴 **6 of the 14 failures are one sentence**: `TimeoutExpired ... after 900
  seconds`. The `fast` pytest step on the same commit ran **1032 s and passed**,
  and the nested spawns run that same selection — so 900 s failed *by
  construction, on every run*, exactly as D-089 predicted from a killed job.
  D-094 fixed the ceiling that kills the job; this fixes what makes it red once
  allowed to finish. They were always two numbers.
- 🔴 **The timeout was stated seven times in two values**, and nobody had counted
  them. Three at 900 s, and **three at 1800 s** — somebody already hit this wall
  on the attributed censuses and doubled *those* calls. **1800 s does not clear
  the requirement either** (2792 s), so the earlier raise was both partial in
  scope and short in size, and read in the diff like a considered choice.
- 🔴 **My own fix introduced an absence-read-as-clean, and the suite caught it.**
  Replacing the literals with a name blinded `suite_runners()` — a signature scan
  requiring an *integer* default. It went **6 → 0**, `collapsed_floor_seconds()`
  fell 8376 → 1396, and `declared_ceiling.grade()` flipped to `SUFFICIENT`
  against a floor that counted **zero** runner classes. Ninth instance on this
  branch, and the first introduced by the fix meant to prevent one. Repaired by
  resolving named defaults (`_package_int_constants`).
- 🔴 **I wrote the seven-row table before running the scan, and got it wrong** —
  six rows, `census_narrowing` missing, `inert_surface` wrongly included. It
  looked authoritative because it was formatted as a table.
- 🔴 **First run of the scan reproduced D-091's own first-draft bug**: no subject
  test, so it graded a 60 s `gh` call and two 300 s scratch suites `INSUFFICIENT`
  against a full-suite figure — a unit error, committed one cycle after reading
  the sentence describing it. Hence `FULL_SUITE`/`NARROW`/`NOT_PYTEST`; the
  honest population is **7 of 17 matched**.
- ✅ **Census cost this cycle: zero, after being paid and refunded.** The scan's
  spawn-name filter entered the guard pool (72 → 73) as a TYPED global, pushed
  `unwatched_exemptions` 5 → 6, and demanded a `REGISTRIES` entry which then
  wanted a tamper. It was **redundant** — `_call_subject` already rejects any
  argv without `pytest` — so deleting it left every graded reading identical and
  returned the pool to 72. First cycle in 28 to add no guard.

## North-star delta

- **No avoidance or tracking number moved — 64th consecutive instrument cycle.**
- What moved: the `slow` job's red count should drop by 6 of 14, and the CI
  authority is readable per job for the first time since 08-04.
- `doomed_sites()` now reads **0**; `declared_ceiling.runway()` still reads 1.

## Key learnings

- **A ceiling that kills a job and a timeout inside it are different numbers, and
  fixing the first is what makes the second legible.** Twelve runs published
  nothing because the job never reported; the moment it did, the real defect was
  a one-line grep away.
- **Deriving from the latest reading is not the same as deriving from the worst.**
  The newest suite observation (1032 s) is the *smaller* one; a `[-1]` would have
  re-armed the trap on any runner as slow as D-089's. The failure is asymmetric —
  too small kills every run, too large costs nothing.
- **Collapsing literals into a name can blind a scanner that reads literals.**
  The consolidation and the instrument that measures the consolidation have to
  land together, or the instrument silently reports success.
- **A redundant guard is worth deleting on its own terms** — this one would have
  cost a probe, a registry entry and a tamper to keep.

## Recommended next 1–3 priorities

1. **Read the remaining 8 non-timeout failures on their merits** — `scale_match`,
   `horizon_audit`, `hazard_exposure`, `exposure_timing_band`, `denominator_scope`,
   `ab_temperature_protocol`, and 2 in `exclusion_scope`. These are substantive
   assertion failures, not infrastructure, and nobody has read them yet.
2. **Re-read this branch's CI after this push** — the 6 timeout failures should be
   gone; if they are not, the 2792 s is also too small and the subject is what
   needs cutting, not the number.
3. **Ask "does a literals-only scan exist elsewhere?"** — `_int_defaults` was one;
   the other registries D-080 named may have the same blindness.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic, #67)
- Files touched: `eval/mppi_sandbox/nested_timeout.py` (new), `nested_suite_cost.py`,
  `predicate_vacuity.py`, `predicate_inputs.py`, `guard_vacuity.py`,
  `census_narrowing.py`, `tests/test_nested_timeout.py` (new),
  `tests/test_nested_suite_cost.py`
- TSV row appended: yes
