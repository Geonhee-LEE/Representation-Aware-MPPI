# The blocker is the other arm's only win

- **Cycle**: 2026-08-18 00:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #2 — fill `cafe_convoy_v0` + `cafe_obstacle_crossing_v0` to ensemble width
- **Phase**: P5
- **Status**: keep

## What I tried

- Measured the last two hostable scenes at ensemble width (8 arms × 8 seeds
  each) through the existing `retake_scene(scene)`, taking coverage **3/5 →
  5/5**. Launched both in the background at minute 3 and wrote the module and
  test changes while they ran, so the measurement was not on the critical path.
- Recorded both columns (`CONVOY_ENSEMBLE`, `OBSTACLE_CROSSING_ENSEMBLE`) and
  added the two scenes to `MEASURED_SCENES` / `_COLUMNS` / `RETAKE_COST`.
- Added `blocking_scenes(arm)` and `narrowest_block()` — the complement of
  `arms_that_generalise()`, which at complete coverage is the half that carries
  the information.
- Rewrote the module docstring, which still led with D-330's falsified
  two-scene framing.

## What worked / what failed

- **`cbf_mppi` won both new scenes 8/8** (`convoy` +0.1494, `obstacle_crossing`
  +0.1888), so it takes **4 of 5** and `blocking_scenes('cbf_mppi')` is exactly
  `('cafe_cut_in_v0',)`. `arms_that_generalise()` is still `()`.
- **The blocking scene is `social_mppi`'s only win in the entire matrix.** The
  two arms are exact complements over the hostable set — their union covers all
  five scenes. That reframes the gap as a *selection* problem rather than a
  missing capability, which is a stronger and more actionable statement than
  "no arm generalises". Not planned; it fell out of completing the set.
- **The core hypothesis is still unsupported.** The arm that travels is the
  classical constraint arm. Every representation arm loses ≥4 of 5;
  `geometric_mppi` is bit-identical to the baseline on all 40 arm-seed pairs;
  `risk`/`frozen_risk` remain indistinguishable at 40/40.
- **A fixture's whole population vanished.** `_ensemble`'s refusal path was
  tested with a "hostable but unmeasured" scene, and that set is now empty.
  D-332 had recorded that such a fixture *expires* when its scene is measured;
  completing coverage did something different — it removed the category. Moved
  the negative case to a non-hostable scene (`cafe_straight_v0`, zero
  obstacles), which no cycle can ever measure, so it cannot expire again.
- **Third consecutive cross-scene over-estimate.** 211.8 s actual against
  ~390 s projected (1.67× and 2.06×, after D-332's 1.38×). The over-pricing is
  why both scenes fitted in one cycle.
- **`census_preempt` caught the guard-tally drift at the stage** (121 vs pin
  120, 2.4 s against a 1002 s suite) — `blocking_scenes` entered the pool.
  That is the check working exactly as D-318 intended.
- **And then the suite went red anyway, on two pins the pre-empt does not
  cover.** I repaired the tally, read that as "the guard question is settled",
  and pushed on. 824 s later: `test_and_shaped_guards_are_exactly_these_four`
  and `test_the_shallow_predicate_was_hiding_two_more_guards`. I had written
  the entrant into the AND-shaped literal — which it is not, it is NOT-shaped —
  and left it out of the deep-minus-shallow literal, which it does belong to
  (it filters against `winners(s)`, a same-module call: D-051's reason). Both
  literals are *placements*, not counts, and `census_preempt` re-derives counts.
  Its `UNCOVERED` line named four other registries and was clean and correct
  throughout; the gap is a different axis than the one that line describes.

## North-star delta

- Coverage of the "all environments" clause moved **3/5 → 5/5 hostable
  scenes** — complete over what this repo can measure (3 of 8 scenarios declare
  zero obstacles and cannot host the census at all).
- The clause is **still unmet**, but its counterexample is now a single named
  scene rather than a diffuse failure, and the counterexample is covered by an
  arm already shipped. Distance to north star unchanged in *capability*;
  materially reduced in *diagnosis*.
- No movement on the representation hypothesis — this cycle is evidence
  against it, honestly recorded.

## Key learnings

- **An emptiness claim hides its own magnitude.** `arms_that_generalise() ==
  ()` read identically at 2, 3 and 5 scenes while the underlying situation went
  from "nothing travels" to "one arm is blocked by one scene". The complement
  (`blocking_scenes`) should have existed three cycles ago; the fix is cheap
  and the information it exposes was already in the data.
- **Completing a set can retire a test fixture rather than break it.** The
  expiry D-332 anticipated was a fixture pointing at a scene that later got
  measured; what actually happened is the fixture's entire population emptied.
  A negative case should be drawn from a category that cannot be filled, not
  merely from one that is currently unfilled.
- **Cross-scene extrapolation over-prices, consistently.** Three boundaries,
  three over-estimates, all in the same direction. Scenes differ in episode
  length, so an arm-count extrapolation does not cross a scene boundary —
  D-332's narrowing now has confirming evidence, and the practical consequence
  is that scene-filling work is cheaper than STATE has been pricing it.
- **Backgrounding the measurement was the whole budget story.** 211.8 s of sim
  overlapped with the edits instead of preceding them.
- **A clean pre-empt is not a clean guard question.** `census_preempt` bounds
  the cost of a *count* drift to seconds, and it did. But adding a guard also
  requires spelling it into the right *placement* literals, and no sub-second
  check covers those — so the cycle that adds an entrant is exactly the cycle
  that pays a full suite to find out where it goes. The pre-empt's `UNCOVERED`
  line lists registries, which reads like the complete statement of what it
  misses and is not: the axis it does not cover is placement-vs-population, not
  four named registries. That is the next thing worth pre-empting, and it is
  cheap — the two literals are derivable from `guards()` the same way the
  tally is.

## Recommended next 1–3 priorities

1. **Ask whether the `cbf`/`social` switch can be made scene-blind** — the two
   arms cover all five scenes; the open question is whether any observable
   available at plan time separates `cut_in` from the other four. This is the
   new bottleneck and it is a representation question, which is why it is
   worth the branch's time.
2. **Diagnose why `cbf_mppi` loses `cut_in`** (old STATE #1) — now better
   posed: not "why does it fail" but "what does `social_mppi` supply there
   that the constraint does not".
3. **Prune the `risk`/`frozen_risk` duplicate** — 40/40 identical pairs across
   the complete hostable set. The evidence is now maximal; it will not improve.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic, PR #67)
- Files touched: `eval/mppi_sandbox/scene_transfer.py`, `eval/mppi_sandbox/tests/test_scene_transfer.py`, `docs/decisions.md`, `docs/deliberations.md`, `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV row appended: pending
