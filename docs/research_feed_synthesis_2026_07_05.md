# Research Feed Synthesis — 2026-07-05 Top-3 Suggested TODOs

_Generated: 2026-07-06 00:00 KST · cycle `p3-research-feed-eval-0705`_

Evaluated against the project north star and current state. All three Suggested TODOs from the
2026-07-05 feed require P2 code in some form. This note ranks them so the next executor picks
the highest-impact item cold once PR #44 (`EnsembleResidualDynamics`) lands on main.

**Current bottleneck**: P2 build-path cluster (#44 → #45 → #23 → #24) must merge before any
downstream P3 or representation-aware-sampler code can be built or tested.

---

## Entry 1 — Condition-Aware Residual Dynamics (Variational Neural Dynamics)

- **Source**: arXiv 2606.27353 (Scaramuzza group; quadrotor hardware; Jun 2026)
- **Mechanism**: physics prior + neural residual + recurrent encoder that infers a hidden
  "condition" variable (venue / disturbance regime) from recent state-action history;
  residual output and policy are both conditioned on the latent condition — 5× faster
  recovery from recurring disturbances once a regime is recognized.
- **North-star fit**: directly addresses the three-venue generalization requirement
  (café / small_city / 미관측 rosbag) — the condition encoder distinguishes venues
  *without per-venue re-training*, which is exactly the gap the static-offline P2 residual arms
  leave open.
- **Phase dependency**: **P2 (strong)** — needs `EnsembleResidualDynamics` as the base
  residual interface before adding the recurrent condition encoder. Cannot start before #44.
- **Caveat**: source platform is quadrotor; no diff-drive / Nav2 / Gazebo; borrow is
  strictly the physics-prior + neural-residual + recurrent-condition-encoder *architecture*,
  not the task.
- **Suggested TODO**: `[research]` prototype a **condition-aware residual dynamics model**
  (Variational Neural Dynamics recipe): physics prior + neural residual + recurrent encoder
  conditioned on recent state-action history — A/B vs static offline residual on café→small_city
  venue switch; scoring recovery speed and cross-track error.

---

## Entry 2 — MPPI-PID Gain-Space Path-Following

- **Source**: arXiv 2603.29499 (mini forklift; Ito group; submitted to IFAC JSC; Mar 2026)
- **Mechanism**: MPPI optimizes 3D PID-gain space (K_p, K_i, K_d) instead of the full
  T×n control-sequence space; gains drive a physical PID controller; plant dynamics modeled
  by a physics + NN residual (same P2 learning target). Reduces optimization dimensionality,
  cuts chattering, comparable path-tracking performance.
- **North-star fit**: 경로추종 completeness axis (cross-track error / heading error /
  smoothness / time-to-goal all addressed by the PID structure) + P2 residual interface
  (physics + NN residual from real diff-drive data). Most *independent* of the three —
  a unicycle prior can stand in for the NN residual for a first-cut prototype before P2 lands.
- **Phase dependency**: **P2 partial** — a simplified version (unicycle kinematic model as
  physics prior, no NN residual yet) can be prototyped now; full version needs P2 for the
  learned residual term.
- **Caveat**: source platform is mini forklift (Ackermann-ish), no Nav2 / Gazebo / crowd;
  PID-gain space is 3D for 1D lateral error — compositional gain banks needed for full nav;
  no head-to-head vs ICODE-MPPI or full-sequence MPPI.
- **Suggested TODO**: `[research]` prototype **MPPI-PID gain-space path-following** on
  nav2_mppi café-straight: sample PID gain space (K_p, K_i, K_d) instead of full control
  sequences, using unicycle prior as initial dynamics model (upgrade to P2 residual once #44
  lands); A/B vs full-sequence MPPI on cross-track error / input smoothness / sample-budget.

---

## Entry 3 — HOLO-MPPI: BEV-Conditioned Sampling Prior

- **Source**: arXiv 2606.16480 (Min, D'sa, Tariq, Isele, Azizan, Bae; Jun 2026; cs.RO)
- **Mechanism**: offline-trained hierarchical policy takes the current observation + goal and
  outputs MPPI's *sampling distribution parameters* (mean, covariance, or latent), enabling
  MPPI to refine online without per-scenario Gaussian prior retuning.
- **North-star fit**: **highest thesis alignment** — directly instantiates the core
  hypothesis: "representation quality determines planning quality." The BEV/semantic front-end
  is the observation input; the offline policy output *is* the sampling prior; MPPI refines
  online. This is the "representation-aware-proposal" move the project name promises.
  Multi-venue generalization follows from the prior learning scene-discriminating features —
  no per-venue hand-tuning of the Gaussian covariance.
- **Phase dependency**: **P1 BEV (designed) + offline training** — needs a BEV feature
  extractor (P1 work) and a diverse training set (café + small_city sim). Does *not* require
  the P2 ensemble residual to start (the learned prior conditions the sampler independently
  of the dynamics model). Could overlap with early P2 work.
- **Caveat**: source domain is autonomous vehicle driving scenarios (intersections, merges),
  not indoor/outdoor mobile nav; whether BEV encodes enough scene-discriminating signal to
  separate café corridor from small_city plaza is the key open question (candidate for Q-016);
  no code surfaced.
- **Suggested TODO**: `[research]` prototype a **BEV-conditioned MPPI sampling prior**
  (HOLO-MPPI pattern): offline-train a policy that takes P1 BEV features as input and outputs
  nav2_mppi's sampling distribution parameters, replacing the fixed Gaussian prior — A/B on
  café vs small_city without per-scene retuning vs the GPC self-bootstrapping and
  fixed-prior baselines.

---

## Ranking

| Rank | Entry | North-star fit | Phase dependency | Key gap addressed |
|---|---|---|---|---|
| **1** | HOLO-MPPI BEV prior | Core hypothesis instantiation — the "representation-aware" move | P1 BEV + offline train (no P2 required) | Replaces per-venue hand-tuned Gaussian prior with learned representation-to-sampler bridge |
| **2** | Condition-aware residual | P2 multi-venue adaptation (5× faster venue-switch recovery) | P2 strong (#44 required) | Multi-venue generalization via regime-identifying recurrent encoder |
| **3** | MPPI-PID gain-space | 경로추종 completeness, dimension-reduction lever | P2 partial (unicycle first cut viable now) | Path-tracking quality + sample efficiency via structured 3D optimization |

**Tie-breaker rationale**:
- HOLO-MPPI ranks first because it is the only entry that advances the *core representation
  thesis* and can be started with P1 BEV work before P2 lands. Its P2 independence is a
  significant scheduling advantage given the current 21-day P2 stall.
- Condition-aware residual ranks second because its multi-venue adaptation mechanism is the
  strongest technical answer to the three-venue north-star requirement — but it is blocked
  strictly by #44.
- MPPI-PID ranks third: most independent and immediately actionable with a unicycle prior,
  but it is an algorithmic-efficiency / path-tracking lever rather than a
  representation-thesis move, so it is lower thesis-alignment per north-star priority.

---

## Recommended Backlog Order (for post-Notion-MCP sync)

When Notion MCP is reachable, create the following [research]-prefixed Backlog items:

1. `[research] HOLO-MPPI: prototype BEV-conditioned sampling prior` — P1, P2, Owner=claude,
   Priority=P1 (thesis-critical; P2-independent scheduling advantage)
2. `[research] condition-aware residual dynamics (Variational Neural Dynamics recipe)` — P2,
   Owner=claude, Priority=P1 (pick after #44 merges)
3. `[research] MPPI-PID gain-space path-following (unicycle first cut)` — P2/P3,
   Owner=claude, Priority=P2 (can start now; upgrade to P2 residual later)

---

## Open Question (candidate for Q-016 when `deliberations.md` is conflict-free)

**HOLO-MPPI prior interface**: should the learned sampling prior condition on
(a) raw P1 BEV features only, (b) P2 latent / residual encoder output, or (c) both?
Trade-off: (a) is P2-independent and evaluable earlier; (b) carries richer dynamical
context but requires P2 to land first; (c) composes both but couples the training pipeline.
Current lean: start with (a) — P2-independent prototype, upgrade to (c) after P2 lands.
_Defer to deliberations.md once #60 merges (D-011 — #60 currently holds deliberations.md)._
