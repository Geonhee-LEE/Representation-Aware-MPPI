# The epistemic channel speaks for the first time — and the reason it was silent was the cost's *shape*, not its weight

- **Cycle**: 2026-08-03 05:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic` (PR #67 — already in the queue, no new review bandwidth)
- **TODO**: STATE #1 — try the alternate-perspective cost construction (feed 2026-08-03 00:00, arXiv 2404.07781). Raised and deferred **four** cycles running.
- **Phase**: P3
- **Status**: keep

## What I tried

- Built `ObservationValueCritic` + `observation_value_map` — the 2404.07781 borrow. Where `ShadowCostCritic` charges σ **at** the rollout point (a *distance-to-unseen* cost), this charges each rollout point for the shadow area it **fails to reveal by standing there**: `V(q)` = fraction of currently-shadowed cells visible from `q`, `cost_k = w_voo · Σ_h (1 − V)`. Aggregate map, one scalar per location, built against the **in-range shadow** only (crediting the beyond-range halo would make it a proxy for "drive forward", which the path term already owns).
- A/B'd the two constructions side by side on `cafe_obstacle_crossing_v0` at the shipped `H = 30`, same isolation D-021 used (`w_risk = 0`, `k = 0`) — the shadow arm re-measured here as this cycle's control, not quoted.
- Swept `w_voo` at both endpoints of the risk_mppi `lam` window (1.6, 3.2), first at 4 seeds and then — because the 4-seed number looked too good — at **8**, paired per seed.
- Measured the term's cost against the *baseline's own* cost spread, after the naive weight produced a collision.

## What worked / what failed

- ✅ **The primary gate passes.** Shadow cost: **0 / 92** live steps, max spread **0.00**. Value-of-observation at the same weight: **115 / 115** live, max spread **1060**, mean 539. Every `w_voo` tested changes the executed trajectory; `w_epist = 200` still changes none. This is the **first non-inert epistemic consumption path in the repo** — D-021 finding #2 is repaired, and repaired by changing the construction rather than the weight or the horizon.
- 🔴 **The clearance claim did not replicate and is withdrawn.** At n = 4 a scale-matched arm read **+60 % mean clearance** (0.0455 → 0.0728) with ESS in band. At n = 8, paired sign counts are **+4/−4**, **+5/−3**, **+5/−3**, **+5/−3** across the four (lam, weight) cells, with mean Δ flipping sign. A coin flip. D-019's "the verdict is a (scene, n_seeds) property" recurring verbatim, and I caught it only because I re-ran a number I liked.
- 🔴 **The naive weight is a temperature change in disguise.** `w_voo = 200` — inherited from what `w_epist` was set to — is **6.19×** this scene's median per-step total-cost spread (79.09 baseline; 2.45 per unit weight). Median ESS collapses **77.9 → 1.00** (argmin-over-draws: `lam` is inert) and the arm **collides** — min clearance **−0.436**, 2/4 reaching goal. Scale-matched weights (10 %/20 % of baseline spread → `w_voo` ≈ 3.2/6.5) stay in the D-017 ESS band.
- ⚠️ **The feed's headline question stays open.** Whether 2404.07781's *own* cell value is bearing-dependent needed the RA-L PDF, and `WebFetch` is not granted in this non-interactive session. Not recorded as a claim about the paper. For the construction built here the answer is pinned: on a one-disc scene two cells **equidistant from the nearest shadow cell** score **0.0 and 1.0** — a maximal counterexample to distance-predicts-value, i.e. D-021 finding #4 stated positively.
- Cost: ~**2.75×** the control-step wall clock (2.2 s vs 0.8 s per run of this scene).

## North-star delta

- **The 가려진-obstacle class has a working cost term for the first time.** Six cycles of epistemic work had been measured against a term multiplying exactly zero; there is now one that the softmax can hear at the shipped horizon on a shipped scene. That is a real capability unlock, and it is the narrow claim.
- **No avoidance number improved.** Clearance is a coin flip at n = 8. Scenes able to contribute an avoidance number: **5**, reportable: **4** — unchanged.
- **One repo-wide hazard found**: shipped critic weights have never been stated relative to the baseline cost they compete with, and at least one plausible weight choice silently converts the planner into argmin-over-draws. Filed as Q-049.

## Key learnings

- **When a term is inert, suspect the cost's shape before its weight.** D-021 correctly localised the gate to rollout reach and then spent Q-043 asking whether to move the scenes or the planner to that gate. Neither was necessary: evaluating the *same information* at the locations the rollouts already visit dissolved it. A dichotomy handed over by a prior cycle is a hypothesis — that is now twice in two cycles (D-026).
- **Re-run any number you are pleased with at double n before writing it down.** The +60 % clearance survived one cycle's worth of plausibility and zero of replication.
- **A weight is meaningless without the scale of what it competes against.** "6.19× the baseline cost spread" explained the collision, the ESS collapse and the whole shape of the sweep in one number, and it cost one instrumented run.
- **Keep the refuted construction next to the new one.** Deleting `ShadowCostCritic` would have demoted this cycle's control to a citation; measured side by side in one file, the 0/92 vs 115/115 comparison stands on its own.

## Recommended next 1–3 priorities

1. **`(w_voo, horizon)` 2×2 on the blind-corner scene (#68)** — Q-043's original plan, now runnable with a term that is *not* identically zero. Still gated on #68/#69 merging.
2. **Calibrate a `lam` window for the `w_voo` arm** before any clearance claim is retried. Every window in `lam_windows.yaml` was measured with the epistemic channel off (D-021 #1), and D-027 shows this term is large enough to move the temperature by itself.
3. **Answer Q-049**: measure the four shipped critic weights as multiples of baseline cost spread on the re-baseline branch (#11) — one table decides whether the units question is real or already harmless.

## Artifacts
- PR: #67 (already open — 23rd consecutive cycle writing into a queued PR)
- Files touched: `eval/mppi_sandbox/critics/observation_value.py` (new), `eval/mppi_sandbox/critics/__init__.py`, `eval/mppi_sandbox/controllers/risk_mppi.py`, `eval/mppi_sandbox/tests/test_observation_value_critic.py` (new), `docs/decisions.md` (D-027), `docs/deliberations.md` (Q-049, Q-043 update)
- TSV row appended: yes
