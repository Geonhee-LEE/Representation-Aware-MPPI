# The headline counted the wrong population, and agreed with the right one

- **Cycle**: 2026-08-29 08:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — author a static-obstacle scene (re-scoped mid-cycle)
- **Phase**: P5
- **Status**: keep

## What I tried

- Opened on a **strand**: 07:00's D-492 work (journal, TSV row, decisions entry,
  two modules, 39 tests) was finished on disk and one commit ahead of `origin`,
  never pushed. Clearing it was this cycle's first obligation.
- Picked STATE #1 — author a static scene, the one uncovered derivable class —
  and priced it before writing any yaml.
- Found the price wrong for this cycle's clock and **re-scoped to the defect the
  pricing exposed**, which sits in the same function STATE #1 was aiming at.

## What worked / what failed

- **The pick was mispriced in STATE, and the cheap check found it.** STATE calls
  the static scene "a yaml edit, no model work". It is not: `_scene_pool()` is
  `class_contract.scenes("obstacle")`, derived from **measured columns**, so a
  yaml that has never been run does not enter the pool and moves no coverage.
  The real price is a yaml **plus 8 rollouts plus the pin bumps they move** —
  affordable, but not against a clock whose previous run overran by 34m41 and
  whose advisory opened with "cut scope this cycle".
- **`line_class_coverage()` was answering a different question than its
  docstring.** It says *"what the shipped contract line actually spans"* and
  returned `coverage()` — the **pool's** class span. Today both read `3/6`, and
  the reason is a coincidence in the data, not the definitions: `cbf_mppi` leads
  **5 of 5** pool scenes, and an arm with a total order spans every class any
  scene exercises. Verified rather than assumed — computed the led-scene set and
  the pool set separately and confirmed they coincide.
- **The next planned cycle is exactly what breaks it.** Author a static scene
  `cbf_mppi` does not lead and the pool goes 4/6 while the line stays at 3/6 —
  the P5 headline would report the *stronger* number for a line that had not
  moved. The bug's blast radius is one cycle away, which is why fixing the
  population *before* authoring the scene was the right order.
- **Fix**: `scenes_led_by()` + `line_classes()`, with the headline counting the
  line's own wins, and the coincidence itself shipped as
  `line_span_is_pool_span` — the same move D-489 made when it pinned per-class
  gate totality as the coincidence it is rather than letting it read as law.
- **The tamper tests are the deliverable, not the fix.** Two of them stage the
  static scene by monkeypatch in both directions: the arm loses it (pool 4,
  line 3, headline must not move) and the arm wins it (headline moves to 4/6).
  The first fails against the old code. A third pins that `scenes_led_by` can
  return empty, so it is capable of pinning nothing.
- `census_preempt` came back **clean on all 10** — first cycle in 16 with no
  drift, because this cycle moved no census population, only the derivation
  behind one key.

## North-star delta

- The only contract line P5 has now has a **defensible** scope: `cbf_mppi 3/6`
  is a property of what the arm won, not of which scenes happen to exist. The
  number is unchanged; what it asserts is now what it measures.
- The next cycle's static-scene work is de-risked — the population it would have
  silently inflated is fixed ahead of it.
- Zero rollouts, zero controller / representation / dynamics movement. A
  correctness fix to a reporting census, nothing more.

## Key learnings

- **Two populations that agree today are a claim about the data, and it belongs
  in the census.** This is the third time on this branch (D-489 gate totality,
  D-490 antitone widening, now this) that the useful artefact was pinning *why*
  two numbers coincide rather than the numbers.
- **Pricing a pick can be the cycle's finding.** STATE's own "cheapest coverage"
  estimate was wrong by a rollout sweep, and checking it cost two minutes and
  produced a better cycle than executing the mispriced version would have.
- A wall-clock advisory that says "cut scope" is most useful **before** the pick
  is committed to, not after — it converted this cycle from a half-finished
  scene into a finished fix.

## Recommended next 1–3 priorities

1. **Author the static scene, now correctly priced** — yaml + 8-arm sweep +
   the pool/scene-count pins it moves. `line_span_is_pool_span` will report
   whether the line earned the new class or merely the pool did.
2. **Buy `heading error`** — 32 rollouts, priced by D-490, still unbought and
   still the cheap half of the tracking debt.
3. **Re-derive `다중` on encounters rather than placements** — the column counts
   deployed multiplicity, not encountered (D-451).

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/obstacle_instrumentation.py, eval/mppi_sandbox/tests/test_obstacle_instrumentation.py, docs/decisions.md
- TSV row appended: yes
