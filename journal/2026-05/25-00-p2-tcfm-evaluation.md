# TCFM Architecture Evaluation for P2 Dynamics Integration

- **Cycle**: 2026-05-25 00:00 KST
- **Branch**: `autoresearch/p2-tcfm-evaluation`
- **TODO**: `36ac5d39` [research] Clone + evaluate TCFM (arxiv 2403.10809, github CORE-Robotics-Lab/TCFM) — 100× faster than diffusion; cfm_mppi alternative
- **Phase**: P2
- **Status**: keep

## What I tried
- Cloned TCFM repo and performed deep architecture analysis of the CFM class, TemporalUnet backbone, TransformerForDiffusion model, and sampling pipeline
- Compared TCFM's trajectory forecasting approach with cfm_mppi's MPPI-integrated control generation
- Mapped TCFM's conditioning mechanism (`global_cond` dict) to our representation channels (BEV, risk fields)
- Assessed two integration paths: Option A (trajectory generator replacing MPPI rollout) vs Option B (learned dynamics model for MPPI forward sim)

## What worked / what failed
- Architecture analysis revealed TCFM and cfm_mppi are complementary, not competing — TCFM provides the backbone + training pipeline, cfm_mppi provides the MPPI integration pattern
- The `p_sample_loop_cfm` method is elegantly simple: single ODE solve via `torchdiffeq.odeint` with Euler method (~100 steps vs diffusion's ~1000)
- No unicycle/robot domain configs exist in TCFM — all aircraft and pursuit-evasion. We need our own trajectory dataset.
- Conditioning via `global_cond` dict is flexible enough for our multi-channel BEV representation without architecture changes

## North-star delta
- +1 P2 design document: first artifact mapping learned dynamics architecture to our MPPI pipeline
- Identified concrete integration path (Option A: trajectory generator) that can produce end-to-end "learned representation → MPPI" demo
- No runtime improvement yet — this is a research evaluation, not implementation

## Key learnings
- CFM's speed advantage over diffusion is real and architecturally simple — a single ODE solve replaces iterative denoising, making real-time MPPI control feasible (~50-100 Hz)
- TCFM's TemporalUnet is the better fit for our short-horizon navigation (vs Transformer which needs 5000+ trajectories to train)
- The project's biggest data bottleneck is trajectory collection — synthetic unicycle data can bootstrap, but real sim runs (TODO `358c5d39`) are needed for validation
- Option A (trajectory generator) is strictly simpler to prototype than Option B (learned dynamics) and validates the core hypothesis ("representation quality bounds control quality") just as well

## Recommended next 1–3 priorities
1. **[P2, claude]** Create synthetic unicycle trajectory dataset generator for TCFM training bootstrap
2. **[P2, claude]** Map Flow Planner hierarchical CFM onto Nav2 global/local split (TODO `36ac5d39…81ec`, complements this evaluation)
3. **[P2, user]** Run cafe sim to capture real trajectory data (TODO `358c5d39`, still blocked)

## Artifacts
- PR: https://github.com/Geonhee-LEE/Representation-Aware-MPPI/pull/22
- Files touched: docs/tcfm_evaluation.md, results/p2-tcfm-evaluation.tsv, RESULTS.md
- TSV row appended: yes
