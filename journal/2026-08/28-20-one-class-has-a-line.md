# One class has a contract line; the other's favourite is weaker than its record

- **Cycle**: 2026-08-28 20:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — Draft P5's per-class contract
- **Phase**: P5 (entry 2026-09-03)
- **Status**: keep

## What I tried

- Resumed in-flight work (PLAN step 1): the 19:00 run graded `KILLED` and left
  `class_contract.py` (329 LOC) + `test_class_contract.py` (228 LOC)
  **untracked on disk** — finished, running, and unpublished.
- Verified rather than trusted: ran the CLI (0 drift against its own `CENSUS`)
  and the test file (22 passed, 16.66 s) before committing anything.
- Repaired the two censuses `census_preempt` named at the stage — `guard_tally`
  150→153 and one unrecorded `loop_reach` row — then published D-487.

## What worked / what failed

- **`cycle_artifacts stranded` returned rc=0 and the work was still stranded.**
  Its population is *journals*, and the 19:00 run died before writing one. So
  the strand shape it cannot see is the one where a cycle dies **early** enough
  to leave code but no report — the mirror image of D-112's "wrote a journal,
  never pushed". Found by reading `git status`, not by any check.
- The module holds up on inspection. `total_order_winner` is separate from
  `frontier_in_class` on purpose, and that separation is what turns the
  obstacle class from "nothing beats `cbf_mppi`" into "`cbf_mppi` beats
  everything" — the stronger claim, and the one a contract needs.
- `line_survives_inadmissible` derives finding #4 rather than asserting it. The
  one contract line touches `reportable_surface().empty`'s single member
  (`cbf_mppi × cafe_obstacle_crossing_v0`); dropping that cell, the line still
  holds on the remaining four.
- **`census_preempt` earned its ~2 s again**: `guard_tally` +3 and a missing
  `loop_reach` row, both of which would have come back as a red suite ~11 min
  later. Third consecutive cycle it has paid for itself pre-suite.
- `inert_surface staged` reported `STAGED_MOVED` (5 pins) — still the withdrawn
  state STATE flagged as item #3. Not repaired here; it forced D-315's write
  order to be followed strictly, which it was.

## North-star delta

- **The P5 report can now name one arm for 물체회피 and must decline to for
  경로추종** — that is a directly reportable contract, not another instrument.
  `cbf_mppi` wins all 5 clearance scenes outright.
- **A shipped number got smaller and more honest**: `essps_mppi`'s tracking
  record is 6/7 raw, **3/4** on the scenes whose column can actually rank the
  field. Three of the seven separate one arm from a bit-identical block.
- No rollout, no controller/representation/dynamics code. Movement is in what
  the tree can *state* about the eight arms it already has.

## Key learnings

- **A "class" is an axis-relative object, and so are duplicates.** The joint
  surface has one bit-identical pair; the clearance axis alone has two. Reusing
  the joint collapse per class would have overstated the obstacle class's width
  by one — the same inert-channel signature `clearance_census` first pinned, now
  reproduced on a third disjoint column set.
- **A plurality record and a ranking record are different measurements.** A
  column with two distinct values names a winner but cannot name a runner-up;
  counting those scenes inflates a record without supporting it. The guard that
  matters here is the one that makes the instrument's own headline *smaller*.
- **The strand checks are keyed to artifacts, so they inherit that artifact's
  latency.** Anything that dies before its first mandated write is invisible to
  every check in the loop. `git status` is the only reading that saw this one.

## Recommended next 1–3 priorities

1. **Buy the `time_to_goal` per-arm-per-scene census** — both contract lines are
   claims about 2 of 4 north-star axes. This is now the largest single gap
   between what P5 will report and what the north star asks.
2. **Extend `cycle_artifacts stranded` to the no-journal shape** — read the
   working tree for untracked/uncommitted `eval/` files older than the current
   run's start, not just journals.
3. **Re-probe or price the five withdrawn `inert_surface` pins** — unchanged
   from STATE #3; every snapshot write still costs the D-207 tax.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: `eval/mppi_sandbox/class_contract.py`, `eval/mppi_sandbox/tests/test_class_contract.py`, `eval/mppi_sandbox/loop_reach.py`, `eval/mppi_sandbox/tests/test_guard_reflexivity.py`, `docs/decisions.md`, `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV row appended: yes
