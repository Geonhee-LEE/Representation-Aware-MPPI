# REVIEW never asked whether the tree was pushable

- **Cycle**: 2026-08-30 10:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `strand-discharge` + STATE #1 (add `tree_provenance declared` to REVIEW)
- **Phase**: P5
- **Status**: in_progress

## What I tried

- Phase 1 `cycle_artifacts stranded` fired rc=1: three cycles (08-29 07:00 /
  08:00 / 20:00) finished on disk, 4 commits ahead of origin, one tree never
  graded. Discharging that outranked the decision tree.
- Took STATE's `Next claude-actionable` #1 as the cycle's own deliverable:
  `tree_provenance declared` had three call sites and every one of them ran
  *after* the suite. Added Phase 1 Step 0-quinquies.
- Added `review_section` / `wired_into_review` + a 9-test `TestLoopWiring`
  class pinning the call.

## What worked / what failed

- The gate this cycle inherited was already green: `declared` reported OK
  because D-494's commit landed the 15 files of cadence drift. So the strand
  was a plain push, not a repair — the TSV rows for all three stranded cycles
  were already present and correct.
- The obvious pin would have been wrong. `bottleneck_scope.wired_into_loop`
  is a whole-file substring test, and copying it here would have passed
  **vacuously**: `python3 -m eval.mppi_sandbox.tree_provenance declared` already
  appears in Phase 4a-ter. The pin only means something section-scoped, so
  `wired_into_review` slices Phase 1 first. `test_the_pin_is_section_scoped_not_whole_file`
  is the regression that would have caught the copy.
- `inert_surface staged` returned `STAGED_MOVED` — the new test file withdrew
  5 exemptions. Under the pre-D-315 write order that was a second suite; under
  the current order every REPORT write already precedes the receipt, so it cost
  nothing. That is the first time the D-315 inversion has visibly paid.

## The strand was NOT discharged — the suite is red, and it was red before this cycle

The receipt came back `rc=1`: **4517 passed, 164 skipped, 9 failed** in 751.77s.
None of the 9 is this cycle's work. All 9 are census pins that D-492's
`obstacle_instrumentation.py` grew by one, and D-492 is one of the three
stranded cycles — the one `cycle_artifacts stranded` flagged as **never
graded**. So the strand was not merely unpushed, it was unpushable, and that
fact was undiscoverable until a suite had been bought.

The 9, by module — a cold-pickable repair list:

- `test_extremum_reading.py::test_registry_covers_the_live_population` —
  `unregistered` contains `('obstacle_instrumentation.py', 'scenes_led_by',
  'max(arms, key=lambda a: arms[a])')`. Register the site.
- `test_extremum_reading.py::test_hull_without_a_repair_is_a_finding`
- `test_exemption_control.py` ×3 — `len(ec.TAMPERS)` is **17, pin 16**.
- `test_exemption_masking.py` ×2 — population is **24, pin 23**.
- `test_guard_direction.py::test_the_exclusion_is_not_special_cased_to_the_guard_it_drops`
- `test_guard_witness.py::test_each_witness_makes_its_guard_raise[guard_direction.readings]`

All five modules are **exactly** the ones `census_preempt` names in its
`Not covered:` line (`exemption_control.REGISTRIES`,
`extremum_reading.SITE_CLASSES`, plus the masking/direction/witness trio it
does not re-derive). `census_preempt` returned `CLEAN` on all 10 censuses it
*does* cover, 13 minutes before the suite found 9 failures in the ones it does
not. That is D-317's shape again: a check whose scope was narrower than it
looked reads exactly like a clean one.

## North-star delta

- **No movement on the north star.** Zero rollouts, no controller /
  representation / dynamics code. Seventh consecutive cycle whose artefact is a
  removed obstruction rather than an added capability (D-486 → … → D-495).
- What it does buy: three stranded cycles reach origin, and the specific
  failure that stranded two of them (spend a suite, *then* discover the tree is
  unpushable) is now caught by a command that runs before PLAN.

## Key learnings

- A check having callers is not the same as a check being *reachable in time*.
  `declared` was invoked three times per cycle and still could not prevent
  D-494, because all three invocations were downstream of the spend they would
  have saved. Placement, not coverage, was the defect.
- The vacuous-pin trap scales with call-site count. D-481's pin shape is only
  sound for a single-call-site module; the moment a module is invoked from
  several phases, "the prompt mentions this invocation" stops discriminating.
  Worth checking the other `TestLoopWiring`-style pins for the same shape.
- Seven cycles of obstruction-removal is itself the finding. Each was locally
  justified, but the branch has not run a rollout since 08-29 01:00.

## Recommended next 1–3 priorities

- **Fix the 9 census-pin failures above — first, before anything else.** They
  block the push of four cycles, and the list is cold-pickable. Mostly `+1` pin
  bumps plus one site registration.
- **Extend `census_preempt` to cover the five it currently disclaims.** It cost
  2 s and returned CLEAN while 9 failures sat in its blind spot; the whole point
  of that check is to make this class of failure cost seconds, not 13 minutes.
- **Author the static-obstacle scene at D-493's price** — yaml + 8-arm sweep
  (~15 s) + the pool/scene-count pin bumps `census_preempt` enumerates. The one
  uncovered derivable class, and it breaks the obstruction-removal streak.
- **Audit the other loop-wiring pins for the vacuous shape** — any module with
  more than one call site in the prompt has `bottleneck_scope`'s whole-file test
  as an unsound template.
- **Buy `heading error`** — 32 rollouts, priced by D-490, still unbought.

## Artifacts
- PR: **not pushed** — `push_preflight check` refuses a red receipt, correctly. Branch is 7 commits ahead of origin (D-492 / D-493 / D-494 + D-495 ×3).
- Files touched: eval/mppi_sandbox/tree_provenance.py, eval/mppi_sandbox/tests/test_tree_provenance.py, scripts/prompts/auto_research.md
- TSV row appended: yes
