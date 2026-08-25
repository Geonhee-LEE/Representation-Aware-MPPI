# Q-017's "shadow cost is redundant" is a seed-0 artifact — and it was #67's red CI all along

- **Cycle**: 2026-08-02 08:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic` (PR #67, already queued)
- **TODO**: STATE item #12, re-derived (`[auto]` — Notion unreachable, 9th cycle)
- **Phase**: P3
- **Status**: keep

## What I tried

- Gate 1 fired for the 27th consecutive cycle (queue = 6, re-derived per-branch;
  0 pushed-but-PR-less, 0 new branches in 24 h). Applied 07:00's precedent —
  **write into a PR already in the queue**, which consumes no new review bandwidth.
- STATE's item #1 (speed-control pass on #68) turned out **infeasible**: it needs the
  `visibility_gated` controller, which exists only on #69's branch. Neither main nor
  #68 has it, and branch-stacking is forbidden. Fell through to item #12.
- Item #12 said "pin numpy in `sandbox-ci.yml` — one line; sole cause of #67's red CI".
  Pulled the actual CI log before writing the line. It is **not** a numpy pin.

## What worked / what failed

- 🔴 **The claimed one-line fix was wrong, and landing it would have been worse than
  doing nothing.** #67's CI fails on a real assertion:
  `test_shadow_cost_is_redundant_for_a_single_collinear_obstacle` expects clearance
  bit-identical at `w_epist` 0 vs 200; CI measures **0.0140 vs 0.0520**. It passes
  locally (numpy 1.26.4) and fails in CI (unpinned → numpy 2.x). So pinning numpy
  *would* have turned CI green — by freezing the one environment where a false claim
  holds.
- 🔴 **Seed sweep, n=24: the redundancy claim holds on 2 seeds — 0 and 22.** The two
  arms differ on **22/24**, median |Δclearance| **1.6 cm**, max **7.8 cm**. Seed 0 sat
  in a coincidence basin and the assertion pinned exactly that coincidence. CI's numpy
  perturbs the float path just enough to move seed 0 out of it.
- ✅ **But "not redundant" is not "useful".** Direction is a coin flip: shadow arm ends
  up farther on **10** seeds, closer on **12**. The term is *active but
  non-directional* — it perturbs the solution without steering it. That is a sharper
  statement of the Q-017 null than "redundant", and it is the one that replicates.
- ✅ Removed the false test; added `test_shadow_cost_seed_robustness.py`, which asserts
  over a seed ensemble (≥5/8 seeds move, max |Δ| > 1 cm) so it holds under **both**
  numpy versions. Memoized the sweep → 16 sims. CI-equivalent suite **62 passed**
  (was 1 failed / 59 passed) and got *faster*: 22 s → 19 s.
- ✅ Conflict-safe: #66 drops this same test, so the documented "#66 wins on
  `test_risk_mppi.py`" resolution stays correct. The durable finding lives in a **new
  file** neither #66 nor #67 touches, so it survives any resolution of that chain.

## North-star delta

- **#67 goes red → green for the right reason.** One of the two stated blockers on the
  5-PR merge chain is cleared, without a new PR and without papering over a result.
- A recorded P3 finding (Q-017, "epistemic shadow cost is redundant") is **retracted and
  replaced** with a stronger, seed-robust one. Net movement is negative-but-honest: we
  know less than we thought we did, and now know it at n=24 instead of n=1.

## Key learnings

- **A backlog item that names its own root cause can be wrong about it.** "Sole cause of
  #67's red CI" survived 20 days of STATE rewrites unchallenged. Reading the CI log cost
  one command and inverted the fix.
- **Environment-sensitivity is a symptom, not the disease.** "Passes locally, fails in
  CI" reads like a dependency problem; here it was the assertion sitting on a knife-edge
  where a float-path change flips the outcome. The right response to env-dependent
  flakiness is to ask what the claim rests on, not to pin the env.
- **Single-seed assertions on closed-loop sims are claims about an RNG stream.** This is
  the third cycle in a row (05:00 knife-edge, 06:00 scene-rescope, now seed) where a P3
  result died to a nuisance variable. The pattern is one instrument short: every A/B
  needs seed + scene + speed controls declared before it is reportable.

## Recommended next 1–3 priorities

1. **Revert Q-017 to `open` in `docs/deliberations.md`** citing this n=24 sweep — STATE
   item #13 already asked for this; this cycle supplies the mechanism (active but
   non-directional, not redundant). Must land on a branch that isn't in the #66-wins
   conflict set.
2. **Speed-control pass on #68** — still owed, still blocked on `visibility_gated`
   reaching main. Unblocks automatically when #69 merges.
3. **A shared `seed_sweep` helper in the sandbox** — three cycles have now hand-rolled
   one. `test_shadow_cost_seed_robustness.py` has the shape to promote.

## Artifacts

- PR: #67 (existing, updated — no new queue depth)
- Files touched: `eval/mppi_sandbox/tests/test_risk_mppi.py`,
  `eval/mppi_sandbox/tests/test_shadow_cost_seed_robustness.py`,
  `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV row appended: yes (`sandbox:pass=62/62`, status `keep`)
