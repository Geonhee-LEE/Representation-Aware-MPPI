# The sum does not cancel — and the knob is the ratio, not the sign

- **Cycle**: 2026-08-14 10:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `STATE-1` Q-148's cheap precursor — read the summed sign of both epistemic arms
- **Phase**: P3
- **Status**: keep

## What I tried

- Executed Q-148's own stated cheap precursor: added a third `BOTH =
  "both-arms-on"` entry to `epistemic_sign.probe_all` that classifies the
  **sum** of the two opposed critics' costs on the same blind-corner geometry.
- Added `cancelling_ratio()` — the `w_epist : w_voo` root at which the summed
  split is zero, derived from the two unit-weight splits (each arm is linear in
  its own weight, so the sum's sign is a function of the ratio alone).
- Added a fourth verdict `CANCELLED` to `classify`, because summing opposed
  arms makes an exact-tie split a *reachable* configuration rather than a
  measure-zero accident.
- 14 → 28 tests in `test_epistemic_sign.py`.

## What worked / what failed

- **The sum does not cancel** — Q-148's lean (c) survives its own test.
  Exposed 12.000 vs observed 5.587, split **+6.413**, verdict **REPEL**, and
  unchanged at `w ∈ {1, 10, 200}` so it is a statement about the ratio, not the
  magnitude. The supports really do differ as the lean guessed.
- **But the equal-weight verdict is an artifact of choosing 1:1, and that is
  the actual finding.** The cancelling root is `0.3587 : 1`, i.e. the attract
  arm needs **2.79×** the repel weight to take the sum. "Both on at weight 1"
  is not a neutral default — it hands the sum to repel.
- **The `CANCELLED` prediction was walked, not just derived**: setting the
  weights to the algebraic root gives split `1.1e-16` → CANCELLED, and `±1%`
  flips it to ATTRACT / REPEL respectively. So `SPLIT_EPS` detects a knife-edge
  rather than defining a band.
- **One test I wrote was wrong and the measurement said so.** I pinned the
  `s1 <= 0` refusal via `radius=0.0`, assuming it would kill the shadow. It
  does not — the disc still casts one — so the branch is genuinely unreachable
  with the two shipped critics. Replaced with a test of the *precondition*
  and marked the guard defensive-and-untested in the code, rather than
  contriving a geometry to reach it.

## North-star delta

- No planner movement — this is a cost-field reading with no sim in the loop,
  and it says nothing about where rollouts actually go.
- It does move the **design** of the deciding experiment: Q-148's A/B was
  specified with three arms, and this measurement shows three is not enough.
- The uncomfortable half: the sum collapses toward the arm D-021 measured
  *inaudible* on the crossing scene. Construction-sign and audibility remain
  the distinction D-255 made first-class, and this reading is on the first.

## Key learnings

- **A verdict that is a tie-break is fine until the tie becomes reachable.**
  `mean_e > mean_o else ATTRACT` was harmless for one arm and wrong for a sum;
  the feature that made it wrong was added in the same cycle that used it.
- **Read the ratio, not the verdict, when both terms are linear in weights.**
  The 1:1 answer is one sample of a one-parameter family, and reporting it
  alone would have made a tuning choice look like a property of the critics.
- **An unreachable guard should be labelled, not test-contrived.** Writing a
  geometry to reach `s1 <= 0` would have been a test of my fixture, not of the
  code.

## Recommended next 1–3 priorities

1. Q-148's closed-loop A/B on an occlusion scene with the corrected **four**
   arms (three + both-on near the cancelling root) — still blocked by PR #68's
   feasibility filter.
2. Check whether `cancelling_ratio` is geometry-stable — one disc at one radius
   is a single sample, and the A/B's both-on cell depends on the root.
3. Still owed: the D-NNN amending D-112's strand recipe.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/epistemic_sign.py, eval/mppi_sandbox/tests/test_epistemic_sign.py, docs/decisions.md, docs/deliberations.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: pending
