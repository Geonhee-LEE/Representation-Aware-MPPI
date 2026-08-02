# The epistemic collision win is a speed confound — but the representation buys *selectivity*

- **Cycle**: 2026-08-01 23:00 KST
- **Branch**: none (gate 1 fired, 18th consecutive) — measured in a throwaway worktree off `origin/main` + `#66` + `#68` + `#69` + `#70`
- **TODO**: none picked — SKIP path, `reason=pr-queue-full count=6`
- **Phase**: P3/P5
- **Status**: in_progress (result measured, cannot be committed until the queue drains)

## What I tried

- Gate 1 re-derived from scratch: 6 OPEN (`#69/#68/#67/#66/#44/#23`), 0 pushed-but-PR-less, 0 branches
  in 24 h, `grep -cE '^\s*-?\s*\*\*Status\*\*:.*superseded' docs/decisions.md` → **0**, so
  deadlock-breaker crit (b) still has no candidate. `.last_escalation` 07-31 22:01 → floor 08-03 22:01,
  not re-sent. All four queued branches merged clean into the worktree — **8th confirmation** of the recipe.
- Last cycle (22:00) claimed *"epistemic caution recovers the oracle collision rate, 0.250 → 0.000,
  p = 0.022"*. It measured `w_blind=0` (ablation) and `w_blind ∈ {5,20,60,200}` — i.e. it varied the
  penalty's **magnitude** but never its **structure**, and never controlled for the fact that every
  non-zero `w_blind` also made the robot **slower** (16.6 s → 24.2 s). So this cycle built the
  controls that experiment was missing.
- Three duration-matched controls, all on `cafe_blind_approach_v0`, all N=24:
  **(a)** `UniformSlowVG` — same v² penalty with the spatial mask deleted (penalise speed *everywhere*);
  **(b)** `NearSlowVG` — the **logical inverse** mask: penalise speed only *inside* `sensing_range`
  ("slow down where you CAN see"), the exact opposite of the hypothesis;
  **(c)** plain `vg_mppi` with `Limits(v_max=0.65)` — a one-line speed cap, **zero** cost-shaping.
- Then asked the north-star question 22:00 did not: *what does caution cost on scenes with nothing hidden?*

## What worked / what failed

**1. ❌ The epistemic framing is refuted. Every duration-matched control recovers the oracle rate.**

| arm (N=24, `cafe_blind_approach_v0`) | collision | pass | duration | cte |
|---|---|---|---|---|
| `vg_mppi(sr=1.0)` — blind baseline | **6/24 = 0.250** | 0.750 | 16.64 | 0.2232 |
| `proto_evg(w_blind=20)` — **epistemic** | **0/24** | 1.000 | 24.16 | 0.2443 |
| `uniform_slow(w=10)` — **no spatial structure** | **0/24** | 1.000 | 27.29 | 0.2411 |
| `near_slow(w=15)` — **inverted, wrong-place** mask | **1/24 = 0.042** | 0.917 | 25.23 | 0.2291 |
| `uniform_slow(w=1)` — matched to *vg*'s duration | 4/24 = 0.167 | 0.833 | 18.41 | 0.2235 |
| **`vg_mppi(v_max=0.65)` — pure speed cap, no cost term** | **0/24** | 1.000 | 24.65 | 0.2482 |
| `stock_mppi` — oracle | 0/24 | 1.000 | 26.37 | 0.2092 |

A one-line `v_max` cap — no BEV, no visibility reasoning, no cost shaping of any kind — reproduces
the headline result exactly (0/24 @ 24.65 s vs epistemic 0/24 @ 24.16 s; Fisher p = 1.0). The
*inverted* mask, which encodes the opposite of the hypothesis, scores 1/24 — indistinguishable from
the epistemic arm (p = 1.0). And the intermediate control (`uniform_slow w=1`, duration 18.41 s) sits
at 0.167, **between** the two endpoints. Collision rate on this scene tracks **traversal duration**,
monotonically, regardless of *where* the caution is spent. 22:00's `w_blind` sweep was a
disguised speed sweep.

**2. ✅ The structured cost does have a real, measured advantage — on efficiency, not safety.**
A speed cap is unconditional; a soft cost competes with the other cost terms and can stay inert
where it is not needed. Measured (N=24 per cell, paired by seed, Δ vs the `vg_mppi` baseline):

| scene | epistemic `w=20` | speed cap `v_max=0.65` | paired Δ (speed − epistemic) |
|---|---|---|---|
| `cafe_blind_approach_v0` (**hides** something) | +45 % (16.6→24.2 s) | +48 % (16.6→24.7 s) | ≈ 0 — both pay |
| `city_curved_v0` (nothing hidden) | **+2.9 %** [+0.25,+0.95 s] | **+17.9 %** [+3.46,+4.08 s] | **+3.17 s, 95 % CI [+2.88,+3.45]** |
| `cafe_straight_v0` (nothing hidden) | +6.9 % | +3.4 % | −0.45 s [−1.35,+0.44] (n.s.) |
| `cafe_obstacle_crossing_v0` | 0.93× | 0.96× | both free |
| `cafe_blind_corner_v0` | 0.98× | 0.82× | both free |

So the honest claim is **not** "the representation makes it safe" — it is **"the representation makes
the caution selective"**: it pays the full +45 % on the scene that actually hides an obstacle and
+2.9 % on a long open curve where a duration-matched speed cap pays +17.9 %. On `cafe_straight_v0`
(short, low speed demand) neither binds, so the advantage is not universal — it appears exactly where
the speed cap would otherwise bind.

**3. Three scenarios carry no sandbox obstacles at all.** `cafe_straight_v0`,
`city_curved_v0`, `cafe_obstacle_crossing_v0` all report `min_obstacle_clearance = +inf` — their
obstacles are Gazebo actors that `scenario.py` does not model. They are valid *path-tracking* scenes
but cannot score any avoidance metric, which is worth knowing before P5 builds a matrix on them.

## North-star delta

- **Net honest movement is a retraction plus a smaller, better-supported claim.** 22:00's headline
  ("epistemic caution recovers the oracle collision rate") does not survive its controls and must not
  be carried into P5 or any external write-up. What survives is narrower and still real: a structured
  blind-space cost achieves the same safety as a speed cap while spending **6× less time** on an open
  scene (+2.9 % vs +17.9 %, paired CI excludes zero).
- **P5 metric consequence, as large as 22:00's `unsafe_rate` finding**: `collision_rate` alone is
  gameable — *any* controller can reach 0/24 by being slow. Every collision-rate comparison needs a
  **duration-matched control arm** (or an explicit time/safety Pareto), otherwise the harness will
  keep certifying slowness as intelligence.
- The P3 hypothesis ("richer representation buys avoidance") is **not** cleared by this evidence. A
  weaker form ("richer representation buys avoidance *at lower time cost*") is supported on one scene.

## Key learnings

- **Sweeping a parameter's magnitude is not a control; varying its structure is.** 22:00 ran a
  5-point `w_blind` sweep with a correct ablation at `w_blind=0` and still measured a confound —
  because every point on the sweep moved speed and structure together. The cheap decisive test was the
  *inverted* mask, which took 90 s to write.
- **When a fancy intervention wins, try the dumbest intervention that produces the same side-effect.**
  `v_max=0.65` is one line and matched a 30-line epistemic controller exactly.
- **A negative result relocated the positive one.** Killing the safety claim is what exposed the
  efficiency claim, which is the more interesting one for a north star that says *all* environments —
  a robot that is safe by being slow everywhere fails "path following" even when it passes "avoidance".
- Confirms 22:00's meta-lesson at one more level: the blocked queue cost nothing here either. Total
  compute for a refutation + a replacement finding: **~6 minutes of CPU**.

## Recommended next 1–3 priorities

1. **Land `EpistemicVGMPPI` — but with the corrected claim and the controls as tests.** The
   registered controller should ship with `test_speed_matched_control_also_reaches_zero_collisions`
   (guards against re-asserting the refuted claim) and `test_selectivity_on_open_scene` (asserts the
   +2.9 % vs +17.9 % gap, the claim that *does* hold). Same ~30 LOC, honest test suite.
2. **Add a duration-matched control arm to the P5 harness spec** before #70 is reopened — see Q-021.
3. **Q-021 (raised, not self-authorized)**: is `collision_rate` admissible as a P5 primary metric at
   all without a time-normalisation, given that a one-line speed cap saturates it? Candidate fixes:
   (a) mandatory duration-matched control arm, (b) report a (collision_rate, duration) Pareto point,
   (c) a composite metric. This supersedes 22:00's recommendation #2 as written.

## Artifacts

- PR: **none** — gate 1 (`pr-queue-full count=6`) blocks branch creation; result is uncommitted.
- Files touched: this journal entry + `STATE.md` / `JOURNAL.md` (local-only per D-011).
- TSV row appended: no (no branch).
- Control-arm source (throwaway worktree deleted; reproduce verbatim alongside 22:00's `_proto_epistemic_vg.py`):

```python
# eval/mppi_sandbox/controllers/_proto_uniform_slow.py
import numpy as np
from .visibility_gated_mppi import VisibilityGatedMPPI

class _MaskedSlowVG(VisibilityGatedMPPI):
    INVERT = False
    UNIFORM = False

    def __init__(self, scenario, seed: int = 0, w_slow: float = 20.0, **kw):
        super().__init__(scenario, seed=seed, **kw)
        self.w_slow = w_slow
        self._robot_xy = np.zeros(2)

    def command(self, state, t):
        self._robot_xy = np.asarray(state[:2], dtype=float).copy()
        return super().command(state, t)

    def _extra_cost(self, traj, t0):
        K = traj.shape[0]
        if self.w_slow == 0.0:
            return np.zeros(K)
        if self.UNIFORM:
            mask = np.ones(traj.shape[:2])
        else:
            if not np.isfinite(self.sensing_range):
                return np.zeros(K)
            d = np.linalg.norm(traj[..., :2] - self._robot_xy, axis=2)
            mask = (d <= self.sensing_range).astype(float) if self.INVERT \
                else (d > self.sensing_range).astype(float)
        return self.w_slow * (mask * traj[..., 3] ** 2).sum(axis=1)

class UniformSlowVG(_MaskedSlowVG):
    UNIFORM = True

class NearSlowVG(_MaskedSlowVG):
    INVERT = True
```

Pure-speed control needs no new class:
`run_scenario(SC, controller='vg_mppi', seed=s, sensing_range=1.0, limits=Limits(v_max=0.65))`.
