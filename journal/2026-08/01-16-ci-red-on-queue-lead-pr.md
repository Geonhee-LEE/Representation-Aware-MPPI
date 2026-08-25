# The queue's lead PR has been CI-red for 20 days — and the escalated merge order would land it on main

- **Cycle**: 2026-08-01 16:00 KST
- **Branch**: none (gate 1 fired — skip path; all work local + throwaway worktrees)
- **TODO**: none picked (`EXECUTOR_SKIP reason=pr-queue-full count=6`)
- **Phase**: P3/P5 boundary
- **Status**: in_progress (diagnostic; no branch, no commit, no push)

## What I tried

- 11th consecutive gate-1 skip. SHA pin re-verified: `origin/main`=`1c0ba893` and all six PR
  heads (#69 `40f9ae04`, #68 `eeebc2a8`, #67 `0616d7e2`, #66 `23e71346`, #44 `5616a562`,
  #23 `a19328dc`) identical to 09:00→15:00. `research/feed.md` re-`stat`-ed per the 15:00
  lesson: `12:03:13`, unchanged since. Deadlock-breaker re-derived: still 0
  `Status: superseded by D-XXX` → crit (b) has no candidate. Nothing new there.
- **New this cycle: ran `gh pr checks` on the queue — the one signal 11 diagnostic cycles
  never looked at.** Every prior cycle validated the merge order with *local* pytest only.
- Followed the failure into the job log, reproduced it locally, then re-simulated the whole
  merge chain in throwaway detached worktrees (no branch, no commit, no push).

## What worked / what failed

- **PR #67 — the first PR in the escalated merge order — is `pytest FAILURE` at its current
  head SHA.** Not stale: the failing run's `headSha` == `0616d7e2` == the live head. It has
  been red since `2026-07-12T16:13Z`, i.e. the entire 20-day stall.
- It fails on a test **#67 itself authored**:
  `test_shadow_cost_is_redundant_for_a_single_collinear_obstacle` asserts
  `abs(clearance[w_epist=200] − clearance[w_epist=0]) < 1e-6`. CI measures **0.038 m** —
  larger than the 0.014 m baseline clearance it is compared against.
- **It passes locally.** Same commit, same test set (`eval/mppi_sandbox/tests/` +
  `eval/tests/test_path_tracking_metrics.py` + `test_run_metrics.py`): local `60 passed`,
  CI `1 failed / 59 passed`. Root cause: `sandbox-ci.yml` installs `pip install --quiet
  numpy pyyaml pytest` with **no version pin** → runner gets numpy 2.x; this box is numpy
  **1.26.4** / py 3.12.3. Float reduction order flips an exact-equality assertion made over
  a *stochastic closed-loop rollout at a single seed*.
- **#66 and #67 are not duplicates — the 09:00 "#67 performs #66's entire payload" claim is
  wrong.** Both retire the same red test, with opposite engineering quality:
  - **#66** replaces it with a **rollout-cost contract test** (`_extra_margin` returns
    exactly 0.4 in shadow / 0.0 on the visible flank; shadowed rollout cost crosses
    `w_collision`). Deterministic, no sampler, no closed loop. **CI passes.** Its docstring
    already documents the ~1e-12 closed-loop measurement and defers the open question to Q-017.
  - **#67** keeps the closed-loop comparison and **inverts** the assertion to "effect < 1e-6".
    Environment-fragile by construction. **CI fails.**
  So `gh pr close 66` discards the robust replacement and keeps the red one.
- **main is red on its own** — confirmed locally, `1 failed / 56 passed`:
  `test_epistemic_margin_widens_berth_in_occlusion_geometry` demands an effect
  `> +0.02` and measures **2e-12**. Same failure mode, opposite sign. main's last green
  Sandbox CI push run was **2026-07-11**.
- **Corrected merge path simulated end-to-end** (main → 66 → 67 → 68 → 69 → 44):
  one conflict at #67 on `test_risk_mppi.py` + `docs/deliberations.md`; resolving the test
  file in favour of #66's contract test while keeping #67's `TestShadowCostCritic` and the
  `w_epist=0.0` baseline-invariance hunk gives **47 passed** sandbox-only / **73 passed**
  full CI set, smoke run `pass: true`, `ShadowCostCritic` still covered by 3 unit tests.
  Same 47 as the 09:00 path — but **one more PR lands, the fragile test is gone, and main
  should return to CI-green.**

## North-star delta

- No code landed; still merge-blocked. **But the escalated instruction was wrong in a way
  that would have made things worse**: following it lands a CI-red commit on main, after
  which every subsequent PR runs against a red baseline — the exact condition that made this
  diagnosis take 20 days to surface.
- Indirect but real: the Q-017 **negative finding is not environment-robust**. "Shadow cost
  is redundant for a single collinear obstacle" is asserted as exact-zero; on the runner's
  numpy the shadow cost moves executed clearance by 3.8 cm. The negative result rests on
  numerical noise in a single-seed sampler, not on the geometric argument its docstring makes.

## Key learnings

- **Green-locally is not green.** Eleven cycles re-derived the same SHA pin and never ran
  `gh pr checks`. The pin proves *inputs* are unchanged; it says nothing about a signal
  nobody read. A skip is not a licence to keep checking the same three things.
- **`pip install numpy` with no pin makes CI a moving target against a static dev box.** The
  cheapest durable fix is a one-line version pin (or a `requirements-ci.txt`) in
  `sandbox-ci.yml`.
- **Exact-equality assertions over a stochastic closed-loop rollout at one seed are not
  tests — in either direction.** Both fragile tests live in `TestRepresentationMovesTheNeedle`:
  one demands ≥0.02 and gets 2e-12, the other demands <1e-6 and gets 0.038. The right form is
  rate-over-seeds — which is exactly what **parked PR #70 (`seed_sweep`)** provides. #70 is no
  longer just a P5 convenience; it is the fix for a live test-suite defect.
- **"Redundant" needs to be checked at the diff, not the summary.** #66 and #67 read as
  duplicates from their titles and both touch the same file — but one is a unit contract and
  the other a closed-loop exact-equality. Cheap to check, and it inverted the recommendation.

## Recommended next 1–3 priorities

1. **User: run the corrected 5-merge path** (below, in STATE.md) — supersedes msg#768.
2. **Pin numpy in `sandbox-ci.yml`** (one line) — first branch to author once the queue drains.
3. **Reopen #70 `seed_sweep`** and convert `TestRepresentationMovesTheNeedle` to
   rate-over-seeds assertions; open a Q-NNN on whether Q-017's negative finding survives a
   seed sweep on numpy 2.x.

## Artifacts

- PR: none (gate 1 fired; no branch created)
- Files touched: `journal/2026-08/01-16-ci-red-on-queue-lead-pr.md`, `STATE.md`,
  `JOURNAL.md`, `.cron_activity_local.log`, `.last_correction` (all local-only)
- TSV row appended: no (no branch, no commit)
