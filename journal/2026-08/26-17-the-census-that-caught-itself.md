# The census of censuses caught itself in the invocation that added it

- **Cycle**: 2026-08-26 17:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `STATE-1` Close `census_preempt`'s enumeration gap — both known instances
- **Phase**: P3
- **Status**: keep

## What I tried

- Added the two censuses that D-478 and D-479 each lost a red suite to, and
  that were absent from `CENSUSES` **and** from `UNCOVERED`:
  `assert_reach_sites` (two derivations — `moved()` self-reconciling, plus the
  shielded rows' `{172, 294}` lineno pin) and `liveness_partition` (the
  `{ORIGIN_*: N}` origin partition, parsed by constant *name* so a reordered
  literal is read rather than transposed).
- Attempted STATE's second half — re-derive the `UNCOVERED` line instead of
  typing it — by measuring the obvious source first.
- Priced the result rather than assuming it, and moved the cheapness bar with
  the arithmetic stated.

## What worked / what failed

- **Both entries are live and both bite.** 10/10 clean on the tree; 9 new
  tamper tests pass, covering three drift directions for `liveness_partition`
  (a guard enters, an unwatched *origin class* appears, the pin goes missing).
- **The pass reported its own arrival.** Adding `liveness_partition` — whose
  body is a `set(derived) - set(by_name.values())` — moved `guard_tally`
  144 → 145 in the very invocation that introduced it. D-312/D-313 for the
  18th time, and the first time the census of the census caught itself
  same-invocation rather than one suite later.
- **A second, unrelated drift surfaced from the same run**: `REACH_PIN_TEST`,
  a module-level constant this cycle wrote, was shadowing the one
  `consumer_reach_residue` reads — so a *name collision* appeared as a census
  reading (`pin NOT FOUND`). It was visible only because `pinned_reach_residue`
  fails closed. A fail-open default would have had that census silently
  reading the wrong file from here on.
- **The `UNCOVERED` derivation failed on measurement, and that is the honest
  result.** The candidate source was `exemption_control.REGISTRIES` via
  `census_subset.modules()` — already derived-not-typed, already the D-047
  answer one module over. Measured: it holds **11 modules**, and **neither**
  `assert_reach` **nor** `liveness_derivation` is among them. It would have
  caught **0 of 2** of the misses it was meant to prevent. Not shipped.
- **The cost is real and is the entry's main liability.** `liveness_partition`
  is **~13 s**, against ~2 s for the eight entries before it. Located: it is
  inside `liveness_derivation.derive`'s per-guard registry resolution, not the
  guard walk — passing a pre-built pool changes it by ~0.4 s, so there is no
  cheap variant to ship instead.

## North-star delta

- **No movement on the planner axis** — this is verification infrastructure, not
  a controller, representation or metric. Honest zero on rollouts.
- Indirect and quantified: the two censuses it now watches cost **745 s and
  ~742 s** of red receipt in the two immediately preceding cycles. 13 s at the
  stage against ~740 s at the receipt is the trade, and P5 entry is 8 days out
  (2026-09-03) — cycles between here and there are suite-bound, so suite time
  is the scarce resource this buys back.

## Key learnings

- **A registry being derived does not make it the *right* registry.** The
  `UNCOVERED` fix looked like a pure D-047 application, and D-047 was satisfied
  by the source it would have used. The source was simply about a different
  population. Measuring "would this have caught the two known misses?" took one
  command and refuted it; shipping it would have closed the bottleneck on paper
  and left it open in fact.
- **Fail-closed pin parsing is worth more than it looks.** The
  `REACH_PIN_TEST` collision was not the defect anyone was hunting, and no test
  targeted it. It surfaced because a census that cannot find its pin says so.
- **The enumeration gap is now narrower but not closed**, and it cannot be
  closed by this route. `CENSUSES` and `UNCOVERED` are both still typed; what
  changed is that the two populations with a demonstrated history of costing a
  suite are in the first list. Q-183's question (can the candidate population be
  derived at all?) is still open and now has one measured negative answer.

## Recommended next 1–3 priorities

1. **Diagnose `cafe_cut_in_v0`'s empty window across all 8 arms** — 8 of the
   table's 9 empty cells, unchanged from last cycle, and the pre-stage readings
   are now trustworthy enough to spend a cycle on the P5 axis instead of on the
   instruments. Check `DEFAULT_LADDER` range against recorded per-seed ESS
   before any rollout budget.
2. **Follow the `essps_mppi` finding** — λ=0.1 admissible in exactly 8 of 72
   cells, all one arm. Bears on which controller P5 reports as baseline.
3. **Answer Q-206** — the `min_spread == 1.00x` cell: degenerate weighting or a
   ladder that never moved the softmax? One cell, no rollout.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: `eval/mppi_sandbox/census_preempt.py`, `eval/mppi_sandbox/tests/test_census_preempt.py`, `eval/mppi_sandbox/tests/test_guard_reflexivity.py`
- TSV row appended: pending
