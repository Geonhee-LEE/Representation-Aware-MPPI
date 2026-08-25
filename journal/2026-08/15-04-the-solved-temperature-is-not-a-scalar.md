# The solved temperature exists at every step — and is not a scalar

- **Cycle**: 2026-08-15 04:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `3bcc5d39` [research] ESSPS as calibrate_lam: λ 를 target ESS 로 푸는 1-D Brent solve
- **Phase**: P3
- **Status**: keep

## What I tried

- Ported **ESSPS** (Watson & Peters 2210.03512) as `eval/mppi_sandbox/essps.py`:
  `solve_lam_for_ess` root-finds `ESS(λ) = φ·K` on real rollout costs, `φ = 10/32`
  kept as a *fraction* (ESS reads normalized weights, so only the fraction ports;
  the paper's LBPS arm carries `‖R‖∞` and is not scale-invariant — not borrowed).
- Harvested the per-step cost vectors of one closed-loop `cafe_freezing_v0` run at
  the operating point `(lam = 0.8, w_voo = 5)` in `ess_at_peak.ISOLATION`, and
  solved λ at each of the 115 steps.
- Compared the ESSPS scalar against the **compliance-optimal** constant λ found by
  sweeping — the control that keeps the comparison off a strawman.

## What worked / what failed

- **The TODO's question has a structural answer, and it is the boring one.** ESS is
  monotone in λ (→1 as λ→0, →K as λ→∞), so a target in `(1, K)` is always hit:
  solved at **115/115** steps. The hoped-for "no λ exists" — which would have made
  D-268's `ESS_DEGENERATE_THROUGHOUT` a property of the cost landscape — cannot
  occur, for reasons that need no measurement.
- **The spread is the finding, not the existence.** Per-step solved λ moves **47.6×**
  across one episode (`0.4281 → 20.3615`, median `1.4786`). A scalar cannot sit
  where that quantity needs to be.
- **The per-scene ESSPS constant is dominated by the table it was meant to delete.**
  Median-matching (ESSPS's own objective) picks `λ = 1.4882` → band held on
  **57/115** steps. The compliance-optimal constant is `λ = 0.7870` → **69/115**.
  The latter is the shipped operating point `0.8` **to within 1.6%**.
- **No constant works at all.** Even at the optimum, 44 steps sit below the floor
  and 2 above the ceiling. The distribution is skewed, so matching the median pushes
  the tail through the ceiling (max ESS `182.03` vs `128.0`) with the lower tail
  still under the floor.
- **Provenance held**: the harvested run reproduces D-270's recorded median ESS
  `31.2344` to 4 dp, live — so this is the cost stream the branch has been reading.

## North-star delta

- No movement on obstacle avoidance or path tracking. The gain is again subtractive,
  and this time it retires a **queued escape hatch**: Q-155's option (c) was the
  only one that removed the calibration matrix, and it does not.
- It also *vindicates* a shipped number rather than merely questioning one — `0.8`
  is now known to be the best constant this scene admits, not just a rung someone
  picked off an off-axis table (D-273).

## Key learnings

- **"Does X exist" is the wrong question when X is a root of a monotone function.**
  The TODO priced existence as falsifiable and cheap; it was cheap and *unfalsifiable*.
  The discriminating question was always the spread, and that was equally cheap to
  ask — I nearly spent the cycle proving a tautology.
- **Compare against the best constant, not the incumbent.** Had I compared ESSPS's
  `1.4882` only against the shipped `0.8`, the result would have read as "the table
  happens to win here". Sweeping for the compliance optimum showed the shipped rung
  *is* the optimum, which is a much stronger and more durable statement.
- **What is retired is the form, not the method.** ESSPS solves λ **per iteration**;
  this measurement only kills the per-scene constant. The per-iteration version stays
  live but is a controller-inner-loop change that would re-date every λ-conditioned
  number on this branch — a cost Q-156 now carries rather than this cycle.

## Recommended next 1–3 priorities

1. **Audit the other window consumers for off-axis reads** (`3bcc5d39`) — D-273 graded
   one cell; ~30 modules resolve windows through `lam_window_key`. Static read, no runs.
2. **Price the per-iteration ESSPS** (Q-156) — what breaks if `lam` becomes a solved
   per-step quantity inside `StockMPPI.command`, given every recorded λ number assumes
   a constant.
3. **Ensemble-at-n16 (Q-153)** — re-read the operating point at
   `CENSUS_LADDER_SEEDS = 16` so `7/8` becomes comparable to the census predicate.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: `eval/mppi_sandbox/essps.py`, `eval/mppi_sandbox/tests/test_essps.py`, `docs/decisions.md`, `docs/deliberations.md`
- TSV row appended: pending
