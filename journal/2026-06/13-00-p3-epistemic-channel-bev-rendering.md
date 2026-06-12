# P3 epistemic-channel BEV rendering spec

- **Cycle**: 2026-06-13 00:00 KST
- **Branch**: `autoresearch/p3-epistemic-channel-bev-rendering`
- **TODO**: `37cc5d39` Spec P3 epistemic-channel BEV rendering: ensemble var σ² → ego-frame grid channel
- **Phase**: P3
- **Status**: keep

## What I tried
- Resumed the `Doing` TODO carried (gate-1-blocked) all of 2026-06-12; gate-1 cleared this cycle (PR queue 5 < 6), so it became executable.
- Wrote `docs/epistemic_channel_bev_rendering.md`: a rendering contract turning the ensemble `σ²` (born in `[M,T]` trajectory space) into a dense `[H,W]` ego-frame BEV channel.
- Logged Q-009 (σ²_ref normalization knob) and indexed the doc in `docs/README.md`.

## What worked / what failed
- The real design problem was sharper than the parent reference implied: `σ²` is **not** natively a grid — it's a per-rollout-step value. Forced an explicit split: **scatter** (rollout-coupled, max-reduce, drives the cost critic) vs **query-grid** (sampler-independent dense raster, drives RViz + P5 calibration). Both reduce σ² identically so the channel is consistent.
- Two normalization traps caught and pinned down: (1) raw `trace(Σ)` lets the largest-unit dim dominate → scale-normalize per dim first; (2) per-frame min-max destroys cross-frame comparability → **fixed `σ²_ref`**, which then exposed the "where does `σ²_ref` come from" gap (Q-009).
- Anchored grid geometry to the actual `local_costmap` params (6m/3m, 0.05m) instead of inventing numbers — no second source of truth for extent/res.

## North-star delta
- + 1 P3 deliverable specced (epistemic channel of the 5-channel risk BEV, `dynamic_obstacles_uncertainty_track.md` §3 U1/U2 row) — design, not measured movement.
- Keeps epistemic/aleatoric **separate** by contract, preserving the P3 epi/ale split that is the phase's whole point.
- No build/sim movement (doc-only); 0 measured numbers still (unchanged, gated on user sim run).

## Key learnings
- "Render-ready as a BEV channel" was a one-line hand-wave hiding a trajectory-space→grid-space map; making the scatter-vs-query split explicit is the actual content, and it cleanly assigns each path to its consumer (critic vs viz/metric).
- The epistemic channel inherits the **same un-set-knob problem** as the margin gain: `σ²_ref` (Q-009) and `k` (Q-008) are both gated on a measured OOD spread we won't have until P5 — they should be swept together, not hand-picked separately.

## Recommended next 1–3 priorities
- Spec the **aleatoric channel** (predictive-variance head → BEV) as the sibling row, reusing this doc's grid/normalization contract — keeps the epi/ale pair symmetric.
- Spec the **multi-channel BEV stack tensor** (`[5,H,W]` order + unobserved-mask channel) as the single interface the risk-aware MPPI cost consumes.
- (user) Still the gating move: merge build-path PRs #44/#45/#47 to unblock the P2 code lane.

## Artifacts
- PR: https://github.com/Geonhee-LEE/Representation-Aware-MPPI/pull/50 (autoresearch/p3-epistemic-channel-bev-rendering)
- Files touched: docs/epistemic_channel_bev_rendering.md, docs/deliberations.md, docs/README.md, results/p3-epistemic-channel-bev-rendering.tsv
- TSV row appended: yes
