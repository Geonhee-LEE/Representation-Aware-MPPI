# The test asserted what a checkout cannot have

- **Cycle**: 2026-08-13 07:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — read the next CI run and confirm or refute D-231
- **Phase**: P3
- **Status**: keep

## What I tried

- Took STATE #1 literally: read the CI run on `c0a63f0` and grade D-231's
  falsifiable prediction (shard 6's two `cycle_artifacts` failures should clear).
- `gh run view --log-failed` refused — the run is still in progress, and this
  repo's slow job may hold a run open for 6 h (`timeout-minutes: 360`, D-094).
  Four runs were in flight at once. Went to the **job-level** log endpoint
  instead, which returns a completed job's log while the run is still open
  (**D-232**).
- Read both failing shards' assertion text, then fixed the two survivors so they
  branch on the **presence of their subject** rather than on a proxy (**D-233**).
- Verified the CI half by reproducing CI's conditions: a fresh clone of the exact
  commit CI ran, no receipts store, no declared drift, full history.

## What worked / what failed

- ✅ **D-231 confirmed.** Shard 6: **76 `cycle_artifacts` tests PASSED, zero
  failed.** The prediction's subject is gone. Q-140 closes as answered *and*
  verified — the TZ fix reached further than predicted, since the two
  `push_claim_gate` failures STATE listed as separately-understood also cleared.
  The run went from **6 failures → 2**.
- 🔴 **Both survivors were asserting properties only a dev worktree can have.**
  `exemption_masking` read `assert 0 == 1`: its population is *this worktree's*
  drift on declared local-only paths, and a fresh checkout has none.
  `quoted_counts` read "the real store holds no datable receipt": `results/receipts/`
  is gitignored, so a checkout has no store.
- 🔴 **The `exemption_masking` branch was guarding the wrong property.** It
  branched on `_DECIDABLE` — can this clone answer *history* questions — which
  D-228's `fetch-depth: 0` flipped to **true** on CI. History-decidability and
  worktree-drift-presence are two different facts that sat behind one predicate.
  D-047's shape, fourth instance on this branch.
- ✅ Fixed under the module's own "split rather than skipped" rule, so the CI
  half still asserts something falsifiable: with no drift the pair must vanish
  exactly with its subject (`masks == ()`); with no store the boundary must be
  absent rather than a fabricated constant (`boundary is None`).
- ✅ Measured, not argued: fresh clone at `c0a63f0` → **2 passed** (80 s). The
  pre-fix reading at that same commit is the CI log itself.

## North-star delta

- No planner movement — 23rd instrument cycle on this branch. Honest.
- The CI authority should now be **green**, for the first time since the streak
  began. That is the precondition for a red meaning something again: two
  permanently-red tests are how a suite gets muted (D-044's own argument).
- A blocked reading is unblocked: three consecutive cycles were told to read a
  digest and reported it unreachable. It was reachable the whole time.

## Key learnings

- **A permanently-red test is not a known issue, it is a broken instrument.**
  D-230 correctly diagnosed both as "structurally unpassable in CI" and then
  carried them as known for 22 cycles. Diagnosing is not fixing.
- **Branch on the subject, not on a proxy for it.** Both fixes are the same
  shape, and the `_DECIDABLE` case shows the cost: a proxy that was accurate
  when written silently stopped tracking its subject when an unrelated change
  (`fetch-depth: 0`) landed.
- **When a reading is "unavailable", check the access path before the content.**
  The annotation API only yields `Process completed with exit code 1`, which is
  what made three cycles conclude the test names were unobtainable.

## Recommended next 1–3 priorities

1. **Read the next CI run job-level and confirm the run is green** — D-233's
   falsifiable prediction: zero failures across all 8 shards.
2. **Return to capability work — a successor to D-225.** 23 instrument cycles is
   the real cost on this branch; `three_arm.ARMS` is built and green.
3. **Q-141** — refuse `git reset --hard` in the local-only audit.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/tests/test_exemption_masking.py, eval/mppi_sandbox/tests/test_quoted_counts.py, docs/decisions.md
- TSV row appended: pending
