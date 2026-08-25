# Slowing the blind arm makes it collide more — the deficit is representational, not kinematic

- **Cycle**: 2026-08-02 07:00 KST
- **Branch**: `autoresearch/p3-visibility-gated-obstacle-cost` (existing PR #69 — **no new PR**)
- **TODO**: STATE claude-actionable #1 (re-frame #69's assertion)
- **Phase**: P3
- **Status**: keep

## What I tried

- Gate 1 fired for the **26th** consecutive cycle (6 OPEN: #66/#67/#68/#69/#44/#23; **20.7 d**
  since #64). Deadlock-breaker re-derived: **0** `Status: superseded` in `decisions.md` → crit (b)
  still has no candidate. Escalation floor 08-03 22:01 untouched. Notion permission ungranted an
  **8th** cycle → gates 2/4 unevaluated, moot.
- Took STATE item **#1** — but noted it is the one backlog item that **adds zero queue depth**,
  because it edits a PR already in the queue instead of opening a 7th. Nine cycles of measurement
  had produced nothing landable; this is the first that writes to a reviewable surface.
- Before changing any assertion, **measured** the shipped scene at N=24, and then swept a speed
  handicap on the gated arm.

## What worked / what failed

- **🔴 STATE's item #1 as written would have made #69 weaker.** It says re-frame the headline from
  the collision count to `min_clearance`. On the scene #69 actually ships, paired clearance is
  **15/24 stock-favoured, sign p = 0.15 — not significant** — while the collision count is
  **0/24 vs 6/24, Fisher p = 0.011**. The 23–24/24 clearance robustness from 06:00 was measured
  under *rescoped* settings, not the shipped one. Swapping the headline naively would have shipped
  a non-significant claim. Caught only by measuring first.
- **🔴 The shipped comparison carried an undisclosed speed confound**: the gated arm runs
  **1.58×** the oracle's realized speed (0.439 vs 0.279 m/s).
- **✅ Removing the confound strengthens the finding in both metrics — and the sign is the
  interesting part.** Handicapping the gated arm makes it collide **more**, monotonically:

  | vg `v_max` | stock | vg | Fisher 1-s | mean_v ratio | paired stock>vg | goal reached |
  |---|---|---|---|---|---|---|
  | none (shipped) | 0/24 | 6/24 | 0.011 | 1.58× | 15/24 | 24/24, 24/24 |
  | 0.35 | 0/24 | 13/24 | <1e-4 | 0.95× | **24/24** | 24/24, 24/24 |
  | 0.30 | 0/24 | **14/24** | <1e-4 | 0.83× | **24/24** | 24/24, 24/24 |
  | 0.25 | 0/24 | **20/24** | <1e-4 | 0.73× | **24/24** | 24/24, 24/24 |

  The obvious confound ("the blind arm just drove faster") is not merely removed — it runs
  **against** the effect. And paired clearance goes **15/24 → 24/24**: the shipped config's weak
  clearance separation was itself a speed artifact.
- **✅ Completion guard is safe to assert everywhere** — 24/24 both arms at every setting
  (max `d_goal` 0.058 m vs `goal_xy_tol` 0.25).
- **✅ Landed, additively.** `test_visibility_gated_mppi.py` 7 → **8 passed**; new
  `TestEffectSurvivesSpeedControl`, a `_reached_goal` guard on every comparison, and the regime
  caveat in the module docstring. No existing assertion removed or weakened → the 13×-verified
  merge recipe is unchanged. Full suite **64 passed, 1 failed**, the failure pre-existing on this
  branch and **exactly the test #66 replaces** (verified by stashing and re-running).

## North-star delta

- **First landable artifact in 26 cycles.** Everything since 07-12 lived in `/tmp` or untracked
  journal files; this is on a branch, pushed, CI-visible, and inside an existing PR.
- **The core hypothesis now has a speed-controlled, completion-guarded, monotone result on a
  reviewable surface**: blind arm 0/24 → 14/24 collisions at 0.83× the oracle's speed. Previously
  this existed only as an uncommitted 03:00 measurement.
- Review load unchanged — queue is still exactly 6.

## Key learnings

- **A backlog item written from a prior cycle's measurement can be scoped to the wrong regime.**
  06:00 established clearance-robustness under *rescope* and STATE turned that into "re-frame
  #69's headline"; but #69 ships the *un-rescoped* scene, where that metric is n.s. Re-measure in
  the target configuration before acting on a recommendation derived from a different one.
- **Confound removal is not only a subtraction.** The speed handicap could only have hurt the
  finding; that it helps, monotonically, converts a nuisance control into positive evidence about
  mechanism. Worth running the handicap *past* the matching point rather than stopping at parity.
- **The gate's purpose admits actions the gate's letter doesn't obviously cover.** Gate 1 protects
  human review bandwidth. Editing a queued PR costs zero additional bandwidth, so it stays
  available even at cap — nine prior cycles treated "capped" as "nothing may be written."

## Recommended next 1–3 priorities

1. **Do the same speed-control pass on #68** (`blind_corner`) — 05:00 found the confound
   **inverted** there (`vg` at half speed still 3× closer). Same instrument, second scene.
2. **Land `_reached_goal` + the speed handicap as shared sandbox helpers**, not test-local — every
   future A/B needs both, and this cycle re-implemented them inline.
3. **Merge the P3 chain** — unchanged, still the binding constraint (user-owned).

## Artifacts

- PR: #69 (updated in place, comment `#issuecomment-5153674660`) — **no new PR opened**
- Files touched: `eval/mppi_sandbox/tests/test_visibility_gated_mppi.py`,
  `results/p3-visibility-gated-obstacle-cost.tsv`
- Commits: `4180a08`, `e96833c`
- TSV row appended: yes
