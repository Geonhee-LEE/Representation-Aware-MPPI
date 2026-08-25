# The diff was cheap; enumerating the cascade was not

- **Cycle**: 2026-08-25 21:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `3c7c5d39` Resolve Q-202, then install the 8-controller table
- **Phase**: P3
- **Status**: keep

## What I tried

- Cleared a **strand first** (D-112): 19:00's journal and two commits were on
  disk and not on `origin`. `HEAD` was already the green-receipt commit and
  every dirty path was declared local-only, so the gate passed unchanged and
  the push discharged it. PR #67 was already open.
- Ran STATE #1's gating measurement: the **rollout-free cell-by-cell diff** of
  `variants/lam_windows_w10.yaml` against D-470's parked 72-cell reading.
- Installed the table anyway once the diff came back clean — copied the
  reading over `eval/scenarios/lam_windows.yaml`, retired the w10 variant from
  `lam_window_index.TABLES` (resolution (b)), and repaired the four break
  sites I could find.
- Tried three ways to enumerate the remaining cascade, and reverted the
  install when none of them returned inside the budget.

## What worked / what failed

- **The diff worked and was decisive**: 24 of 24 variant cells reproduce in
  the parent across all five fields, mismatches **0**, headers identical, and
  the superset is strict on both axes (controllers 8 ⊃ 3, scenes 9 ⊃ 8).
  Q-202's (b) is no longer a lean.
- **Q-202's own arithmetic was wrong**: it and D-471 both call the variant
  "24 cells / **2** controllers". It is **3** — `gap_gated_mppi`, `risk_mppi`,
  `stock_mppi`. The cell count was right, so nobody re-factored it.
- **The install itself was not the hard part** — ~4 min, and `WeightCollision`
  genuinely went away (collection clean, 0 import errors).
- **Enumerating the reds is what has no cheap path.** `-x` gave one red in
  7.8 s (`test_ab_temperature_protocol` — the 9th scene entering the strict
  partition; fixed). Getting the *full* list needs `-x` off: the fast subset
  blew a **420 s** timeout, a narrowed 10-module selection blew **150 s**, and
  `xdist` is not installed (`-n 16` → `unrecognized arguments`; the 14 shards
  are `push_preflight`'s own runner, not a pytest flag).
- So D-457's 16+8 is **still unconfirmed on this tree**, for the third cycle
  running. I reverted rather than gamble a 20.5 min blind suite that, if red,
  leaves no receipt and therefore no push at all.

## North-star delta

- **Zero rollout movement.** No controller ran under evaluation. The P5
  headline is still computed over 2/8 of the controller axis.
- What moved is that the install's remaining risk is now **one** unknown
  (the cascade size) instead of two — its premise is measured and pinned in a
  0.18 s guard, so the next attempt does not re-buy this question.

## Key learnings

- **The blocker moved from the install to the instrument.** D-471 found an
  identity collision; this cycle found that even with the collision resolved,
  the cycle cannot *see* what it broke. Three timeouts on three different
  selections is a structural property of this branch, not bad luck (Q-203).
- **A cheap measurement can be decisive and still not unblock anything.** The
  diff cost seconds and answered the question STATE asked. It bought the
  premise, not the install — those were priced as one item and are two.
- **`--durations` on the receipt run is free.** The suite runs anyway; the
  per-test timings that would let a cycle split rollout tests from table tests
  cost nothing extra. Not taking it this cycle was the miss.
- The real minute-0 error repeats D-470's: I budgeted for "install + cascade"
  without first asking whether the cascade was *observable* in 35 minutes.

## Recommended next 1–3 priorities

1. **Take `--durations=40` on the next receipt run and park it** (cost 0), then
   implement Q-203 (b) — derive which lam tests actually roll out. This is the
   prerequisite for the install, not a detour around it.
2. **Then install**, on a tree where the cascade is enumerable in seconds.
3. **Fix Q-202/D-471's "2 controllers" → 3** wherever the prose repeats it.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/tests/test_lam_table_install_collision.py, docs/decisions.md, docs/deliberations.md
- TSV row appended: pending
