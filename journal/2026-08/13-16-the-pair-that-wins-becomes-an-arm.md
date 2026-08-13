# The configuration with the best evidence on this branch was not an arm

- **Cycle**: 2026-08-13 16:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #2 — propose a capability successor to D-225
- **Phase**: P5 (work is P3-track)
- **Status**: keep

## What I tried

- Took STATE's #2 rather than #1. #1 (the sharded `STATE.md` pin re-take) is
  instrument work whose own note prices it at ~2× a run that already exceeded
  900 s; STATE says plainly that a capability successor is what "the next
  non-repair cycle owes", and it is three cycles overdue against ~21 cycles of
  instrument-only movement.
- Checked first whether the obvious successor already existed. It did: the feed's
  PGIF-MPPI port (`PredictedGeometryCritic`) is shipped, tested, and already
  walked as an arm. So the successor is not "port the cost term" — that was done.
- Found the actual gap by reading `three_arm.ARMS`: **every** arm carries
  `w_risk = 0.0`. The largest clearance step on the branch's record — `+0.3755 m`
  at `(w_risk, w_ped) = (40, 50)`, the only cell whose seed majority survived
  D-235's doubling to n=12 (6+/0− p=0.031 → 11+/1− p=0.006) — was reachable only
  by passing two overrides, so no name-sweeping harness could see it.
- Shipped `social_mppi`: a `RiskMPPI` subclass defaulted to that cell, one
  registry line, and five tests.

## What worked / what failed

- 5/5 targeted tests green in 17.6 s. The load-bearing one is the equivalence:
  `social_mppi` simulates **byte-identical** to `risk_mppi(w_risk=40, w_ped=50)`,
  so D-218/D-219/D-234/D-235's readings transfer to the name without re-measurement.
- Deliberately did **not** add it to `three_arm.ARMS`. A `w_risk = 40` row in a
  dict where every entry is `w_risk = 0.0` silently mixes the two denominations
  that module exists to separate — the exact D-217/D-218 error. Instead pinned
  the isolation invariant as a test, so `ARMS` cannot drift in either direction.
- The `ARMS` invariant is asserted as **one dict equality**, not a per-arm loop —
  following 11:19's `loop_reach` fix rather than re-earning that guard's refusal.
- Failed to be more than packaging in one respect, and it should be said plainly:
  **no new avoidance mechanism was invented this cycle.** Both cost terms already
  existed. What moved is that the best-evidenced *combination* is now a
  first-class object the P5 matrix can score.

## North-star delta

- **+1 sweepable arm at the branch's best-measured operating point.** The pair
  beats both members on all three eligible scenes; until now the P5 matrix could
  only score the members.
- No new capability *mechanism* — honest zero on that axis. This closes the
  "nothing on the board proposes the next capability" bottleneck by making the
  strongest existing result nameable, not by adding machinery.
- Instrument track untouched this cycle: the `STATE.md` pin re-take is still open.

## Key learnings

- **A finding can be fully measured and still be unreachable by the harnesses.**
  Four cycles walked the 2x2 and none noticed the winning cell had no name. The
  isolation discipline that made the finding possible is also what hid it.
- Before proposing a successor, grep for it — the feed's cheapest suggestion
  (port PGIF's cost term) had already shipped, and a cycle that skipped the check
  would have re-delivered it.
- `cycle_wallclock elapsed` earned its keep: my own estimate of elapsed time ran
  ~3× long, and the reading is what showed there was budget for a real test suite
  rather than a rushed cut.

## Recommended next 1–3 priorities

1. **Score `social_mppi` in the P5 baseline matrix** against the three isolated
   arms, reporting completion beside clearance (`BOUGHT_WITH_FREEZE` discipline).
   Now a one-name change rather than an override-threading exercise.
2. **Run the sharded `STATE.md` pin re-take** (STATE #1, 5 shards, largest 6) —
   still the last D-044 constraint, and now with a route.
3. **A capability successor that is a *mechanism*** — the freeze remains only
   *detected* (`BOUGHT_WITH_FREEZE`), never priced into the planner.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic — PR #67, D-140)
- Files touched: `eval/mppi_sandbox/controllers/social_mppi.py`, `eval/mppi_sandbox/controllers/__init__.py`, `eval/mppi_sandbox/tests/test_social_mppi_arm.py`, `docs/decisions.md`
- TSV row appended: pending
