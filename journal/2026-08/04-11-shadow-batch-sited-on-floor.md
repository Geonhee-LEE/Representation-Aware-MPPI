# The rollout batch was sited on the floor — 42–100 % of it, and one scene entirely

- **Cycle**: 2026-08-04 11:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — Q-071: measure `weight_units._shadow_trajectory`'s corner contamination
- **Phase**: P3
- **Status**: keep

## What I tried

- Q-071's own lean was **(b) measure before fixing**, on the grounds that here
  the selected cells *are the input* — unlike D-057, where the floor biased a
  reported fraction, this code **places rollout points** on those cells. So:
  count, per scene, the share of `shadow_batch`'s σ > 0.5 selection sitting at
  `d_robot > r_sense`.
- Then price the fix against the only published magnitude that actually reads
  that batch: the margin knob's per-unit spread ratio.
- Then, and only then, apply (a): split the field into scene-cast and renderer
  floor (`shadow_cells` / `ShadowCells`), site the batch on the scene half.
- Static, no sim. 8 scenes at their start pose.

## What worked / what failed

- 🔴 **The floor is 112 cells in every scene that renders — identically.** That
  is what makes it a property of the grid rather than of any world, and it is
  the claim the whole correction rests on, so it is pinned as its own test.
  Contamination against the raw selection: `cafe_freezing` 41.8 %,
  `cafe_obstacle_crossing` **48.3 %**, `cafe_cut_in` 49.1 %, `cafe_convoy`
  50.0 %, `cafe_head_on` **100.0 %**.
- 🔴 **On `cafe_head_on_v0` the batch was sited entirely on shadow the scene
  never cast** — 112 selected, 112 floor, 0 scene cells. And the guard clause
  three lines below, `raise ValueError("no shadow cells in this BEV — pick
  another pose")`, passed. It could never fail: the corners guarantee
  `sel.any()` on every scene that renders at all. Same defect D-057 fixed in
  `unseen.min() > 0.0`, in guard-clause dress, exactly where Q-071 said it was.
- ✅ **The recalibration bill exists and is small.** Only one published number
  reads this batch — the margin knob's per-unit spread ratio on the crossing
  scene — and it moves **2.568 → 2.717**. The conclusion it supports
  (`> 2.0` ⇒ non-additive, no exchange rate) is unchanged, and the shipped
  assertion passes on the corrected batch without being loosened.
- ✅ **The guard now fires, and that is shown by execution.** `cafe_head_on_v0`
  raises, pinned by test; before this cycle the identical call returned a
  batch. A trigger that can occur, demonstrated on the instance that occurs.
- ✅ The three obstacle-free scenes are refused **one layer earlier** (no BEV
  rendered at all), and that is a separate test — otherwise `vacuous` would
  quietly mean two different things.
- ⚠️ **Eighth consecutive cycle whose new code entered a census its own package
  takes.** The new test helper arms a controller at an explicit `lam`, so
  `default_lam_sites` read `DECIDES` 31 against a pinned 30 and
  `test_census_counts_are_pinned` failed. Pin and the module's running-tally
  docstring both updated (30/103 → 31/104); the partition's *conclusions* are
  stated against the split, not the totals, and none moved.

- Fast half: **583 passed** / 135 skipped / 1 xfailed (was 572), re-taken after
  the 4a/4a-bis writes per D-043/D-044; `verify` and `declared` both clean.

## North-star delta

- **No avoidance or tracking number moved — twenty-sixth consecutive instrument
  cycle.** Scenes able to contribute an avoidance number: 5, reportable: 4.
- Unlike D-055, no published magnitude is retracted; one is **corrected upward
  by 5.8 %** and its conclusion survives. The 가려진-obstacle class still has
  exactly one working cost term (D-027).
- What did move: the synthetic batch every future `k_margin_per_sigma` /
  `w_epist` algebra check is built on is now on cells a sensor could have seen.

## Key learnings

- **Measuring first was the right call and cheap** — but not for the reason the
  lean gave. The bill turned out to be 5.8 %, i.e. the fix would have been
  nearly harmless applied blind. The value of measuring first was that it
  produced the *head-on 100 %* reading, which is the finding; the recalibration
  number was the smaller half of the answer.
- **A contamination fraction and a vacuity predicate are the same measurement.**
  `out_of_range == selected` is exactly "this scene casts no shadow here", so
  the instrument Q-071 asked for and the guard the guard clause should have had
  are one object. That is why the fix is three lines and not a rewrite.
- **Three cycles of "check the guard's trigger can occur" have now found three
  instances** (D-055's liveness bar, D-057's `unseen.min()`, this). All three
  were reachable by asking what a predicate reads on the *empty* member of its
  population. The shape is worth a grep, not just a habit.

## Recommended next 1–3 priorities

1. **Grep the package for the remaining guard clauses whose trigger cannot
   occur.** Three known members now calibrate the search; two of them were
   found by hand from a single docstring contradiction.
2. **Q-070: count the guards whose before-reading is non-empty in the enriched
   fixture** (known to be 6 via `reach_gap`). Static, 2–3 readings.
3. **Re-run the audible/deaf partition through `reach_on_trajectory`** — after
   D-057 the nominal driver's deaf class is known to be entirely vacuous, so
   this is the only route to populating the interesting one. 8 sims.

## Artifacts

- PR: #67 (open, fifty-third consecutive cycle writing into it)
- Files touched: `eval/mppi_sandbox/weight_units.py`,
  `eval/mppi_sandbox/tests/test_weight_units.py`, `docs/decisions.md`,
  `docs/deliberations.md`
- TSV row appended: yes
