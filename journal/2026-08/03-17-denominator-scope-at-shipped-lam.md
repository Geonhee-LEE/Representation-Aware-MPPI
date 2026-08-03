# The denominator verdict flips at the temperature the repo ships

- **Cycle**: 2026-08-03 17:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — re-measure the self-vs-baseline denominator gap at the shipped `lam = 0.1`
- **Phase**: P4
- **Status**: keep

## What I tried

- Took STATE #1 as written — unpicked for nine cycles, and head of the list
  since the citation thread finished last cycle. D-028 measured `w_voo = 200`
  two ways on `cafe_obstacle_crossing_v0` (6.19× against the baseline arm,
  1.46× against its own) at `lam = 1.6`; the repo ships `lam = 0.1`.
- Re-read the same pair at both temperatures with the existing
  `weight_units.measure` instrument — no new machinery needed for the
  measurement itself, ~1.7 s per closed-loop run.
- Added `denominator_scope.py`: reads both denominators at one temperature and
  reports **which term captured the `rest` denominator**, plus closed-loop
  health (steps, clearance, goal distance) so a damage explanation can be
  checked rather than assumed.
- 13 tests (5 fast arithmetic/verdict-structure, 8 slow measurement).

## What worked / what failed

- 🔴 **The verdict flips, on the self-referential side.** Self ratio
  **1.464 → 0.0488**. At the shipped temperature the own-arm statistic calls
  `w_voo = 200` *negligible* (5 % of what it competes with) — the exact weight
  D-027 proved collapses the softmax. Against the baseline it still reads
  **3.30×**. Understatement **9.15× → 67.7×**. At `lam = 1.6` only the margin
  was wrong; at `lam = 0.1` the conclusion is.
- 🔴 **D-028 Decision (3) is false here.** It explicitly ruled the collision
  term out — `w_collision = 1e4`, median spread *exactly 0 on both arms*,
  "guard not competitor". At `lam = 0.1` the loud arm's median spread is
  exactly **1e4** and the `w_voo` row's denominator is **10183** (724 at
  `lam = 1.6`). The guard *is* the denominator.
- ✅ **But nothing collides**, and saying so was worth a test. Executed min
  clearance **0.0119 m**, *better* than the baseline arm's 0.0097 m. The 1e4 is
  a spread over the **rollout cloud** — at the median step some of K = 256
  sampled rollouts cross the boundary and some do not. "The loud arm crashes"
  would have been a stronger claim than the data supports.
- 🔴 **And the understatement is not driven by damage.** D-028 predicted it
  "grows with the damage" from the never-finishes mechanism (1000 vs 114
  steps). At `lam = 0.1` the loud arm is far *healthier* — **116 vs 93 steps**
  (1.25×, not 8.8×), goal distance 0.290 m vs 3.821 m — and the understatement
  rose **7.4×**. Damage fell on every available axis while the understatement
  grew.
- 🔴 **D-028 Decision (5)'s methodology rule is also `lam = 1.6`-specific.**
  Per-unit ladder at `w = 1/7/200`: 2.497 / 2.337 / 5.299 (**2.27×** swing) at
  `lam = 1.6` vs 2.658 / 2.576 / 2.483 (**1.07×**) at `lam = 0.1`. The cheap
  small-weight probe D-028 declared invalid is accurate to 7 % at the shipped
  temperature.
- ✅ **The citation guard fired on this cycle's own module** and went green only
  after registration — sixth live verification. It also surfaced that
  `SCANNED_MODULES` is hand-maintained, i.e. D-037's exact failure mode; added
  `denominator_scope.py` and declared `tests/` excluded **with a reason**
  (magnitudes there sit in assertion messages, where a drifted number already
  fails its own test).

## North-star delta

- **No avoidance or tracking number moved — eighth consecutive instrument
  cycle.** Honest reading: this corrects how the repo prices cost weights, it
  does not make the planner avoid anything better.
- What it does buy: the weight-pricing statistic used to justify `w_voo` is now
  known to invert at the shipped temperature, so any future weight chosen with
  it would have been chosen wrong. That is a real defect removed from the path
  between here and a tuned planner, not a new capability.
- 가려진-obstacle class still has exactly one working cost term (D-027). Scenes
  able to contribute an avoidance number: **5**, reportable: **4** — unchanged.

## Key learnings

- **A statistic that understates at one operating point can invert at another.**
  D-028 reported a margin difference and generalised a mechanism from it; both
  ratios exceeding 1 hid that the *conclusion* was one temperature away from
  moving. A margin that survives is not a verdict that survives.
- **"Graded on its own wreckage" was the right slogan and the wrong mechanism.**
  The driver is not how damaged the arm is but **which term captures the
  denominator** — and that can be a term the weight never touched. Reporting a
  ratio without naming its denominator's owner is what let the wrong mechanism
  generalise.
- **Machine scope was fully stamped and operating-point scope was not.** Every
  one of D-028's claims carried its `AVX512_SKX` stamp (D-033/D-036) and every
  one was still mis-scoped, because `lam` is not a field anybody records. →
  **Q-059**.
- **Rescope, not retract** (D-036's distinction, second application): D-028's
  measurements and its headline "the denominator is the finding" both stand;
  only the three supporting mechanisms are now `lam = 1.6`-conditional.

## Recommended next 1–3 priorities

1. **Count what fraction of `claim_scope` claims were measured at a
   non-shipped operating point** — Q-059's lean (c). Cheap: each claim already
   records its instrument, so read each instrument's default `lam`.
2. **Reproduce the flip on a second scene** before treating "prefer the
   baseline denominator" as a rule. One scene, one seed, one weight.
3. **Reproduce D-030's redundancy on a second scene** (unchanged, STATE #2) —
   Q-052's lean still needs it before becoming a tool default.

## Artifacts

- PR: #67 (existing — 35th consecutive cycle writing into it, no new review bandwidth)
- Files touched: `eval/mppi_sandbox/denominator_scope.py`,
  `eval/mppi_sandbox/tests/test_denominator_scope.py`,
  `eval/mppi_sandbox/citation_audit.py`, `docs/decisions.md` (D-039),
  `docs/deliberations.md` (Q-059)
- TSV row appended: yes
