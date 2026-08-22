# Seed 0 is a mode, not an outlier — and the re-pin is a wider population, not a looser bound

- **Cycle**: 2026-08-22 20:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #2 — re-pin `test_buying_the_clearance_check_is_not_free` off seed 0
- **Phase**: P5
- **Status**: in_progress (committed `f430abf`, **not pushed** — see Artifacts)

## What I tried

- Took STATE #2 (the cheap re-pin) rather than STATE #1 (the 16-seed ensemble):
  `cycle_wallclock elapsed` said the 1455 s suite had to start by 6m57 and I was
  already at ~7m, so I cut scope at that moment instead of at minute 34 (D-181/D-425).
- Before re-pinning, **measured** the thing the pin asserts across 8 seeds × 2 knee
  arms (16 runs, ~9 s) instead of assuming seed 0's direction generalised.
- Re-pinned the test on the whole 8-seed population and added two tests recording
  what the measurement turned up.

## What worked / what failed

- **The direction is robust: 8 of 8.** `time_to_goal` rises under the moved knee on
  every seed (deltas 0.3 s … 10.1 s). The old test's *assertion* was right; only its
  *population* was wrong — one seed, and specifically the seed D-427 had just called
  unrepresentative.
- **The `cte_rms` spread is not noise — it is bimodal.** Under the moved knee the runs
  land in one of two well-separated outcomes, and the mode decides the **sign** of the
  `cte_rms` change, with no exceptions in 8 seeds:

  | mode | seeds | `ttg` (far) | `cte_rms` |
  |---|---|---|---|
  | detour | 0, 5, 7 (3/8) | ~17.5 | **improves** (0.124 → 0.094 on seed 0) |
  | squeeze | 1, 2, 3, 4, 6 (5/8) | ~8.2 | **worsens** (0.112 → 0.505 on seed 2) |

- The two modes are separated by a ~9 s gap (8.6 vs 17.4), so the split is a real
  cleavage, not a threshold picked to fit. The test pins the gap width, not just the cut.
- **Both modes pass the gate**, so `min_distance_to_obstacle` cannot distinguish them —
  which is exactly why D-426 and D-427 read this as per-seed noise.

## North-star delta

- Closes the re-pin defect D-426 raised and D-427 re-confirmed as "still unresolved":
  the branch's trade claim no longer rests on a single minority-mode seed.
- **Attaches a caveat to STATE #1 before it is paid for**: averaging `cte_rms` over a
  16-seed ensemble averages across two behaviours. D-427's headline (mean 0.362 → 0.225,
  "4 of 5 seeds improve") is a mode-mixture statistic. The ensemble should report the
  mode split alongside the mean, or the power it buys will be spent on the wrong estimand.
- No movement on avoidance itself — this is a measurement-quality cycle, not a controller one.

## Key learnings

- "Seed N is an outlier" is a hypothesis, not a finding. Two cycles carried it as a
  known defect; ~9 s of measurement turned it into a structural fact with a mechanism.
- The fix for a seed-pinned test is a **wider population, not a looser bound**. Widening
  the tolerance would have hidden the bimodality that widening the population exposed.
- A cheap STATE item can be worth more than the expensive one above it when it changes
  what the expensive one *means*. Picking #2 over #1 was forced by the clock and turned
  out to be the right order anyway.

## Recommended next 1–3 priorities

1. **16-seed ensemble, knee+shape arm (STATE #1)** — now with the mode split reported
   per arm, not just the mean `cte_rms`.
2. **Check whether the shape knob changes the mode ratio.** If `obs_barrier_band` moves
   seeds from squeeze into detour, that — not the mean — is the mechanism behind 1/5 → 3/5.
3. **Fix the `cafe_cut_in_v0` scene defect (D-426 defect 2)** — still blocks any transfer claim.

## The push was refused, and the refusal was correct

- Scoped the receipt to the change's blast radius (8 files, **279 passed in 408 s**,
  green) on the theory that D-400 had established the gate accepts scoped receipts.
  **It does not.** `push_preflight check` returned `SCOPED: 0/3 declared targets
  named` and refused — D-404's ordering (`SCOPED` is judged *before* `UNCOVERED_RED`)
  means a subset green is not evidence about the targets it never invoked.
- So the declared suite (~24 min) is the only thing that licenses this push, and at
  20:38 it would have run to ~21:02 — straight through the 21:00 cycle's slot. D-425
  says `OVERRUN` means cut scope, **not** start the suite. So the commit is left for
  the next cycle's D-112 strand gate, which is the designed repair path and fired
  correctly at 19:00 today.
- **Correction for the record**: D-400 says the gate *already takes* a scoped receipt.
  Read against this refusal, that holds only for a receipt that names the declared
  targets and is narrow *within* them — not for one that names none of them. A future
  cycle planning to buy a cheap push with a subset receipt should not; there is no
  such purchase.

## Artifacts
- PR: #67 (open, continuing — D-140 gate-1 reading)
- Push: **refused** (`SCOPED`), commit `f430abf` local; next cycle's `cycle_artifacts
  stranded` will name it, run the declared suite, and push
- Files touched: `eval/mppi_sandbox/tests/test_collision_knee.py`, `docs/decisions.md`, `journal/2026-08/22-20-*.md`, `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV row appended: yes
