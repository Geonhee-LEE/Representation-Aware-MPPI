# Widening does not move the 경로추종 record — it empties it

- **Cycle**: 2026-08-29 06:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: resume-in-flight — D-490's deferred record claim
- **Phase**: P5
- **Status**: keep

## What I tried
- Discharged a **strand**: 03:00's two commits (D-490) were finished on disk and never
  reached `origin`; 05:00 was KILLED mid-work leaving 250 uncommitted lines in `eval/`.
  Both are carried out on this push rather than re-derived.
- Took D-490's deferred claim: ran `class_contract`'s record machinery over
  `tracking_instrumentation`'s three-clause **gated** columns — `record_under`,
  `outright_wins_under`, `tally_under`, `eligible_scenes_under`.
- Made the conjunction the bar: an arm wins a scene only by leading on **every**
  censused clause there, per `CLAUDE.md`'s "동시에".
- Labelled both records with their clause sets in `class_contract.census()` and
  **cited** the widened one from `tracking_instrumentation` rather than recomputing it.

## What worked / what failed
- **The widened record is empty.** `tally_under() == ()` — no arm leads any of the four
  scenes on all three clauses. The shipped one-clause record is `essps_mppi 2/3`; the
  widened one is `none 0/4`.
- The contrast is **not** confounded by population: `record_pools_equal()` is `yes`, and
  re-running the widened machinery at one clause over the same pool reproduces
  `essps_mppi 2/3` exactly. The two fractions differ by clause set alone.
- Declining to name a winner was load-bearing. `max` over an all-zero tally names an arm
  alphabetically; a report quoting "cbf_mppi 0/4" would credit an arm that did nothing.
- `CLASS_AXIS["tracking"]` is still `"cte"` and D-487/D-489's shipped keys have not moved
  — the widened record ships **beside** them under a clause-labelled key, not over them.
- Staging moved 5 inert-surface pins (this cycle added readers). Known D-207 price, paid.

## North-star delta
- 경로추종 now has a record claim on **3 of 4** clauses where it had one on 1 — and the
  claim is that **no arm holds the class**. That is a narrowing, not a win.
- Third consecutive cycle where buying a measurement removed a claim rather than adding
  one. D-486 (frontier is the whole registry), D-487 (per-class contract is 1 of 2 lines),
  now D-491 (the surviving line has no holder under its own class definition).
- No new controller / representation / dynamics code. Movement is in what P5 may assert.

## Key learnings
- **A per-clause plurality and a conjunctive record are different questions, and the gap
  is the finding.** `essps_mppi` leads cross-track on scenes it wins nothing on once
  smoothness and time-to-goal must hold simultaneously — exactly the trade the 3-wide
  frontier already said the class cannot resolve, now visible in the record column.
- Quoting `2/3` and `0/4` side by side is only honest because two *unrelated* filters
  (ranking-resolution, census-coverage) happen to select the same four scenes. That is a
  coincidence, so it is asserted rather than assumed — it can silently stop holding.
- A strand plus a killed cycle can be discharged together when the killed cycle's work is
  self-consistent and its own tests are green. Re-deriving it would have cost the cycle.

## Recommended next 1–3 priorities
1. Price and buy `heading error` (the 4th clause, 32 rollouts per D-490) — it is the only
   remaining way the widened record could change, and antitone widening bounds which way.
2. Run the same conjunctive record over 물체회피 — `cbf_mppi` holds a 5/5 total order on
   one clause; whether it survives its own class's full clause set is unasked.
3. State the P5 headline over `none 0/4`: the per-class contract's tracking line now has
   an explicit "no holder" value rather than a pending one.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/tracking_instrumentation.py, eval/mppi_sandbox/class_contract.py, eval/mppi_sandbox/tests/test_tracking_instrumentation.py
- TSV row appended: yes
