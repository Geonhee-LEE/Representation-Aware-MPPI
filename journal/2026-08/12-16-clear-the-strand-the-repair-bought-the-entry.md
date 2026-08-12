# Clearing the strand: the repair that cleared three reds bought one

- **Cycle**: 2026-08-12 16:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: strand clearance (D-112 obligation) — 15:00's four commits never reached origin
- **Phase**: P5 (calendar) · work is P3-line
- **Status**: keep

## What I tried

- Phase 1's `cycle_artifacts stranded` read rc=1: the 15:00 cycle wrote a
  journal, committed four times, and refused to push on a red suite (2 failed /
  2633 passed). Per D-112 that outranks the decision tree, so this cycle picked
  nothing new — it cleared the strand.
- 15:00 recorded a diagnosis for the two remaining reds and I checked it before
  acting on it. **It was wrong.** Both failures trace to a single entrant, and
  it is not the function 15:00 named.
- Fixed both pins with the measured values and the prose each pin's convention
  asks for: `guard_reflexivity` pool `101 -> 102`, `scalar_readings` `12 -> 13`.

## What worked / what failed

- 🔴 **15:00's diagnosis was wrong in a way worth recording.** It attributed the
  reds to `step_bought_with_freeze` "wanting its `and`-shaped guard registered
  in two pinned tallies". Measured: that function is **not in the pool at all**,
  and the AND set is untouched at nine. Its `and` is a boolean operator joining
  two scalar comparisons; `SENSE_AND` reads set intersection (`&`). A cycle that
  is out of budget can still write down a guess, and this one wrote it in the
  register reserved for readings. The cost was ~4 min of this cycle re-deriving.
- 🟢 **The real entrant is `three_arm.is_interaction`, and it entered because
  15:00 removed an unwatched population.** The predicate first shipped as
  membership in `INTERACTION_VERDICTS`, a typed module-level allow-list;
  `unwatched_exemptions` went 5→6. The repair (D-104's option: state the reading
  so the set need not exist) spells the complement as
  `v in ("MAIN_EFFECT", "INERT")` — an inline two-string tuple in membership
  position, D-102's exact shape. So **paying the allow-list bill bought a pool
  entry**: three census reds cleared, one created.
- 🟢 The same entrant hits the second pin for an unrelated reason, and that one
  refutes a standing gloss: `scalar_readings`' other twelve members all return
  one *string*, which had been read as "the reading selects for renderers".
  `is_interaction` returns `bool`. The reading selects for **arity one** — a
  conclusion can have arity one without rendering anything.
- 🟢 Second-order cost is nil on both axes and **both were measured**, not
  inferred from one: `unwatched_exemptions` reads 5, `NO_REGISTRY` holds at 19.
  D-180's lesson ("DERIVED, therefore nil" is the inference that cannot be made)
  applied rather than restated.

## North-star delta

- **No new capability measurement — this cycle is the delivery of 15:00's.** The
  3-scene 2×2 result (interaction generalizes on all three eligible scenes at
  every threshold; the sign flip decays to `CONDITIONAL` at 5 cm) reaches origin
  and CI here rather than sitting on disk.
- The branch's capability claim is unchanged and now reviewable: "PGIF's
  predicted-geometry field needs the BEV risk term" holds on 3/3 scenes.

## Key learnings

- **A diagnosis written past the suite deadline should be labelled as a guess.**
  15:00 was right to stop rather than edit pins unverified — that judgement was
  correct and this cycle endorses it. What cost time was recording the *cause*
  in the same voice as the measurements around it. The honest form is "2 reds
  outstanding, cause unmeasured".
- **The census now has a two-sided price and both sides are measured.** D-104
  measured a repair that *deleted* a guard from the census (nil cost, wrongly).
  This is the same repair from the other side: it *inserts* one. Removing an
  unwatched population and entering the pool are the same edit.
- Cheap probe worth reusing: `python3 -c "import ...guard_reflexivity as gr;
  print(len(gr.guards()))"` is 0.25s. Re-deriving both census values by hand
  cost far less than the 20-min suite 15:00 could not afford — D-180 priced this
  exact confusion and the lesson generalizes to diagnosing a red pin, not just
  to shipping one.

## Recommended next 1–3 priorities

1. Q-133 (`carried_drift`'s offence) still blocks the nine `test_guard_direction`
   probe reds — unchanged, still the longest-standing item.
2. Nothing on the 3-scene result needs re-measuring; the next capability step is
   a scene outside the `cafe_*` family, where `SIGN_FLIP` has no prior.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/tests/test_guard_reflexivity.py, eval/mppi_sandbox/tests/test_guard_direction.py, docs/decisions.md, journal/2026-08/12-16-clear-the-strand-the-repair-bought-the-entry.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: yes
- Suite: 2635 passed, 158 skipped, 1 xfailed (rc=0, 518.78s, 14 shards) — receipt `results/receipts/fdbb2ca00b58d7c3.json`. 15:00's 2633/2 becomes 2635/0; the delta is exactly the two pins.
