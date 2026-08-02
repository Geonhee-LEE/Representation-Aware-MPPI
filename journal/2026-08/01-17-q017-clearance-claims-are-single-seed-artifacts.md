# Q-017 clearance claims are single-seed artifacts — both the positive (main) and the negative (#67)

- **Cycle**: 2026-08-01 17:00 KST
- **Branch**: _none — gate 1 (pr-queue-full=6) fired; diagnostic-only cycle_
- **TODO**: _none picked_
- **Phase**: P3 (queue), P4 by calendar
- **Status**: in_progress (finding recorded, no code shipped)

## What I tried

- Re-derived all four safety gates from scratch. Gate 1 fires: 6 OPEN PRs (#69/#68/#67/#66/#44/#23),
  all seven SHAs identical to the 09:00→16:00 pin, 0 merges/closes in 72h, 20.1d stall.
  Deadlock-breaker crit(b): `grep -cE 'Status.*supersed' docs/decisions.md` = 0 → no candidate.
  **12th consecutive exhausted cycle**, not forced.
- Tried to **confirm** 16:00's root-cause attribution (CI drifts to numpy 2.x because
  `sandbox-ci.yml` pins nothing) from the runner itself. `gh run view --job 86668823117 --log`
  returns **empty** — the 2026-07-12 log is no longer retrievable. Hypothesis unconfirmable that way.
- Building an isolated numpy-2.x venv is blocked: `python3 -m venv` needs `python3-venv` via apt
  (hard limit). So I tested the **cheaper decisive question instead** — is the assertion
  seed-fragile *regardless* of numpy version? Ran both red tests' bodies over seeds 0–7 in a
  throwaway detached worktree at #67's head, under local numpy 1.26.4.

## What worked / what failed

- **#67's test fails 7/8 seeds under the SAME numpy that "passes" it.**
  `test_shadow_cost_is_redundant_for_a_single_collinear_obstacle` asserts
  `|clear(w_epist=200) − clear(0)| < 1e-6`. Seed 0 (the hardcoded one): 1.9e-12 → passes.
  Seeds 1–7: 1.9e-3 … 2.9e-2 → all fail. The pass is a **coincidence at one seed**, not a property.
- **main's test fails 6/8 seeds too**, and its *sign flips*.
  `test_epistemic_margin_widens_berth_in_occlusion_geometry` asserts `clear(k=0.4) > clear(0)+0.02`.
  Passes at seeds 4, 7 only; seeds 3, 5, 6 give **negative** delta (k·σ *reduced* clearance).
- Baseline clearance itself is seed-dominated: `clear(k=0)` spans 0.00045 → 0.055 m across 8 seeds,
  a ~100× spread, while the effect under test is ~1e-2 m. **Effect size ≈ seed noise.**
- Consequence: **16:00's "pin numpy" follow-up is not a root-cause fix.** A pin would at best
  re-freeze the seed-0 coincidence. Demote it from "first branch when queue drains" to hygiene.

## North-star delta

- No code shipped (gate-blocked). But a **negative result that removes false evidence**: the Q-017
  epistemic-margin conclusion is unsupported in *both* directions. Nothing in the current sandbox
  justifies "k·σ buys clearance in occlusion geometry" or "shadow cost is redundant".
- Net movement toward "물체회피 완벽" is honestly **negative-then-positive**: we knew less than we
  thought an hour ago, which is the precondition for measuring it correctly.

## Key learnings

- The 20-day stall's deepest problem was never the merge order — it is that **a single-seed
  closed-loop clearance comparison was accepted as a finding**, twice, in opposite directions.
  CI redness was the symptom that finally exposed it.
- This upgrades **parked PR #70 (collision-rate-over-seeds aggregator)** from a P5 convenience to
  the **blocking instrument** for the whole Q-017 thread. Reopen it first, not last.
- It also independently **strengthens keeping #66**: its deterministic rollout-cost contract test
  removes the sampler and the closed loop from the assertion entirely — the only form of this test
  that can be true. 16:00 reached the right conclusion via CI-green; the stronger reason is that
  #67's assertion is measuring a claim that is false.
- Method note: "confirm the hypothesis" and "test what the hypothesis implies" are different costs.
  The runner log was unavailable and the venv was blocked, but an 8-seed local sweep — 3 min —
  answered the question that actually mattered.

## Recommended next 1–3 priorities

1. **Merge order is unchanged** (66 → 67 → 68 → 69 → 44, resolving #67's `test_risk_mppi.py`
   conflict in favour of #66's test). msg#771 stands; no new Telegram sent.
2. **Reopen #70 (seed-sweep aggregator) first** once the queue drains — every clearance claim in
   Q-017 needs seed aggregation (≥ 16 seeds, report median + IQR) before it means anything.
3. **Revert Q-017 in `docs/deliberations.md` to `open`** — both the "partially-answered" negative
   (#67) and main's implicit positive rest on n=1. Requires a branch; blocked by gate 1.

## Artifacts

- PR: _none — gate 1 blocked branch creation_
- Files touched: this journal entry, `STATE.md`, `.cron_activity_local.log` (all local-only, uncommitted)
- TSV row appended: no (no branch)
