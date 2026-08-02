# The three nuisance controls become one importable module

- **Cycle**: 2026-08-02 09:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic` (PR #67, already in queue)
- **TODO**: `(notion-unreachable)` Promote `seed_sweep` + `_reached_goal` + `v_max` handicap to shared sandbox helpers (STATE items #2+#3)
- **Phase**: P3
- **Status**: keep

## What I tried

- Gate 1 fired for the **28th** consecutive cycle (queue 6: #66/#67/#68/#69/#44/#23,
  20.8 d since the last merge). Deadlock-breaker re-derived from scratch — 0 PRs carry a
  `superseded` status in `docs/decisions.md`, so criterion (b) still has no candidate.
  Escalation floor is 08-03 22:01. Applied the 07:00/08:00 precedent instead: land on a
  branch **already under review**, which costs zero new review bandwidth.
- Promoted the three nuisance controls that the last three cycles each hand-rolled into
  `eval/mppi_sandbox/ab.py`: `seed_sweep` / `run_arm(v_max=…)` / `reached_goal` /
  `assert_all_reached` / `summarize` / `paired_delta` / `sign_counts`.
- Refactored `test_shadow_cost_seed_robustness.py` (this branch's own file) onto it, so the
  module has a real consumer rather than being dead code awaiting one.
- Added `test_ab_harness.py` — 11 contract tests on the *guards themselves*.

## What worked / what failed

- **The refactor reproduced 08:00's numbers exactly**: 7/8 seeds differ, seed 0 tied,
  max |Δclearance| 2.87 cm. That is the only acceptable outcome for a refactor of a
  measurement, and it is worth having checked — the helper defaults differ from the
  hand-rolled code in one place (see the scope note below).
- **Two claims became assertable that were not before.** Both arms complete the path on
  all 8 seeds (the shadow-cost comparison had *no* completion guard until now — it was
  simply assumed), and the arms are speed-matched at **1.003×** (0.1375 vs 0.1371 m/s).
  So unlike #69, this comparison needs no `v_max` handicap — and now says so in a test
  rather than in a docstring.
- **A deliberate API divergence**: `ab.run_arm` scores clearance against *all* scenario
  obstacles by default; #69's `_run` scored `obstacles[0]` only. Kept the safer default and
  made the subset an explicit, tested override. #69's file is untouched (branch-stacking is
  forbidden), so adopting `ab` there is a post-merge follow-up that will need this line read.
- Suite 62 → **76 passed**, 19 s → 29 s. The added 10 s is real closed-loop sim in the
  harness contract tests; it buys the guards being verified rather than trusted.

## North-star delta

- **No new controller behaviour and no new P3 finding — this is instrument work.** Honest
  reading: zero direct movement toward "perfect avoidance in all environments".
- Indirect but real: the last **three** cycles each retracted or weakened a P3 result on a
  different nuisance axis (05:00 knife-edge scene, 06:00 scene scope, 08:00 seed). The cost
  of *not* controlling for those was three cycles of rework. That cost is now ~4 lines at a
  call site.
- Q-030 ("seed × scene × speed declared, or not reportable") was un-adoptable as a rule
  while compliance meant re-deriving the machinery each time. It is now cheap enough to
  actually enforce at review.

## Key learnings

- **A guard that is documented but not asserted is not a guard.** The shadow-cost test
  carried a careful docstring about seeds while silently assuming completion and speed
  parity. Both assumptions happened to hold — but nothing would have said so if they
  stopped holding, which is exactly the shape of the 20-day false finding it replaced.
- **Refactoring a measurement is a measurement.** The value here was not tidiness; it was
  that porting to a shared default surfaced the `obstacles[0]`-vs-all divergence between two
  branches that both believed they were reporting "clearance".
- **Third occurrence is the right trigger for promotion, not the first.** Written after one
  cycle, this module would have encoded the seed axis only and missed both speed and
  completion — the two axes discovered later.

## Recommended next 1–3 priorities

1. **Revert Q-017 to `open` in `docs/deliberations.md`** — still the highest-value unclaimed
   item, still blocked on needing a branch outside the #66 conflict set. Unchanged from 08:00.
2. **Adopt `ab` in `test_visibility_gated_mppi.py` (#69) after merge** — and resolve the
   `obstacles[0]`-vs-all scoping question explicitly when doing so, not silently.
3. **Raise Q-030 formally** once a non-conflicting branch is available; the enabler now exists,
   so the question is only whether to make it a review gate.

## Artifacts

- PR: #67 (already open; this commit lands on the existing branch)
- Files touched: `eval/mppi_sandbox/ab.py` (new), `eval/mppi_sandbox/tests/test_ab_harness.py` (new), `eval/mppi_sandbox/tests/test_shadow_cost_seed_robustness.py`, `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV row appended: yes (`sandbox:pass=76/76`, keep)
