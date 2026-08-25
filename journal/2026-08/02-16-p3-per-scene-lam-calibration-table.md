# Per-scene `lam` calibration: the criterion, the table, and a scene that never finishes

- **Cycle**: 2026-08-02 16:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE claude-actionable **#2** — calibrate `lam` per scene across the matrix
- **Phase**: P3
- **Status**: keep

## What I tried

- Took STATE **#2** (per-scene `lam` calibration) and executed it so that it also
  settles **#1** (the Q-035 fork) by mechanism rather than by fiat. Gate 1 fired for
  the **35th** consecutive cycle (queue 6 = #66/#67/#68/#69/#44/#23, **20.9 d** since
  #64, deadlock-breaker still **0** superseded candidates, escalation floor 08-03
  22:01 → not re-sent), so this landed on **#67 in place** — tenth cycle running,
  zero new review bandwidth.
- Shipped `eval/mppi_sandbox/calibrate_lam.py`: a matrix generator over
  (scenario × controller) producing `eval/scenarios/lam_windows.yaml`, plus
  `SceneCalibration.is_calibratable` — the Q-035 criterion.
- Ran the real matrix: **8 scenes × 2 controllers × 8 rungs × 8 seeds**, a factor-2
  log ladder `0.05 → 6.4` chosen to span the 20× disjointness measured at 15:00.
- Added `test_lam_calibration_table.py` (17 tests): table structure, both
  empty-window causes, and **one** narrow live re-measurement (3 rungs × 4 seeds)
  so CI does not pay ~1000 closed-loop runs per PR.

## What worked / what failed

- ✅ **Q-035 option (c) generalises.** The fork's cheapest branch was "retire
  `offset = 0.3`" — retiring one scene **by name**, which finds the next
  pathological scene the same expensive way. The shipped criterion instead is:
  *a scene is an admissible ablation surface for a controller iff its admissible
  window is non-empty*. `offset = 0.3` is retired as a **consequence**, and scenes
  nobody has looked at yet are screened by the same rule before any A/B.
- ✅ **Q-025's constructive proof now holds between two *shipped* scenario files**,
  not a synthetic variant. The cafe scenes are admissible at `lam ∈ {0.2, 0.4, 0.8}`;
  **`city_curved_v0` is admissible only at `{1.6, 6.4}`**. The intersection over the
  matrix is **empty**, so no fixed temperature serves it — 15:00 showed this against
  a hand-built centred hazard, this shows it against the repo's own matrix.
- 🔴 **An empty window has two causes, and I initially conflated them.**
  `cafe_cut_in_v0` is uncalibratable for **both** controllers at a per-seed ESS
  spread of **1.00×** — as reproducible as a scene gets. The blocker is not
  temperature: no rung gets every seed to the goal. That is the Q-034 shape, a
  completion failure wearing a temperature failure's clothes, and my first
  criterion would have sent a bisection search after it. Fixed by splitting
  `completes_anywhere` from `min_spread > band_width`; the two demand completely
  different next actions.
- 🔴 **`city_curved_v0`'s window is non-contiguous** — admissible at 1.6 and 6.4,
  **not** at 3.2, at spread 1.00×. ESS is monotone in `lam`, so this cannot be a
  band exit; it has to be a completion hole in the middle of the range. Recorded,
  not explained. It is the most interesting unexplained result this cycle.
- 🔴 **`city_figure8_v0` costs more than the other seven scenes combined** and blew
  a 700 s wall-clock timeout, which discarded **fifteen finished cells** because the
  table was written only at the end. Fixed (`on_cell` + `imap_unordered`, partial
  tables persist), at the price of a full re-run — the whole matrix took two passes
  of this cycle's budget.
- ✅ **The empty intersection survives excluding the dead cell.** With
  `cafe_cut_in_v0` removed, the calibratable cells still share nothing: cafe at
  {0.2, 0.4}, `city_curved_v0` at {1.6, 6.4}. Pinned as its own test, because an
  empty intersection that follows from one non-completing scene would be a claim
  about that scene, not about temperature.
- ✅ **Suite 125 → 142 passed + 1 xfailed, 130 s → 132.5 s** — 17 tests for +2.5 s.
  STATE item #6's budget holds precisely because the wide ladder stayed out of CI.

## North-star delta

- **No movement on avoidance or tracking** — fourth consecutive measurement-validity
  cycle. Honest accounting: this cycle produced no new closed-loop capability.
- What it *does* buy: the standing caveat ("every cross-scene number was measured at
  a temperature that silences the cost terms") now has a **remedy that is one command
  long** instead of a per-scene research task. The Q-032 re-baseline can read a table
  rather than run a study.
- One scene of the eight is now known to be **unusable as an ablation surface for any
  controller** (`cafe_cut_in_v0`), which was not known before and would have silently
  polluted any matrix-wide aggregate.

## Key learnings

- **A negative result needs its *cause* attributed, not just its bounds justified.**
  15:00's lesson was that "no value works" and "wrong decade" print identically; this
  cycle's is one level down — "no value works" and "the arm never finishes" also print
  identically, and only the first is a temperature finding.
- **Generalise the retirement, not the retiree.** Option (c) was framed as removing a
  named scene; the same evidence supports a criterion that screens scenes
  automatically. Picking the general form cost roughly the same code.
- **A long measurement that is consumable only on full success gets run at useless
  settings.** Fifteen good cells were thrown away by one straggler. Incremental
  persistence is not polish on a job of this length; it is what makes the honest
  setting affordable.
- **Cost is now a first-class property of a scene.** `city_figure8_v0` being ~7× the
  rest is a fact the P5 harness needs before it schedules anything matrix-wide.

## Recommended next 1–3 priorities

1. **Diagnose `cafe_cut_in_v0`'s non-completion** — it is uncalibratable for both
   controllers at 1.00× spread, so either the scene is mis-specified (goal
   unreachable / horizon too short) or both controllers fail it identically. Either
   answer matters more than another temperature result.
2. **Explain `city_curved_v0`'s hole at `lam = 3.2`** — a non-monotone admissibility
   pattern under monotone ESS should not exist; if the cause is completion, the
   completion metric belongs in the table beside the window.
3. **Feed the table into the Q-032 re-baseline** — still the same one dedicated
   branch, still gated on the queue draining. Do not stack.

## Artifacts

- PR: #67 (in place — gate 1, 35th consecutive skip)
- Files touched: `eval/mppi_sandbox/calibrate_lam.py`,
  `eval/mppi_sandbox/tests/test_lam_calibration_table.py`,
  `eval/scenarios/README.md`, `eval/scenarios/lam_windows.yaml`
- TSV row appended: yes
