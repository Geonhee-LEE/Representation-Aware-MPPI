# Epistemic caution recovers the oracle collision rate — measured, N=24, p=0.022

- **Cycle**: 2026-08-01 22:00 KST
- **Branch**: none (gate 1 fired, 17th consecutive) — measured in a throwaway worktree off `origin/main` + `#69` + `#70`
- **TODO**: none picked — SKIP path, `reason=pr-queue-full count=6`
- **Phase**: P3/P5
- **Status**: in_progress (result measured, cannot be committed until the queue drains)

## What I tried

- Gate 1 re-derived from scratch: 6 OPEN (`#69/#68/#67/#66/#44/#23`), 0 pushed-but-PR-less,
  0 branches in 24 h, `grep -cE '^\s*-?\s*\*\*Status\*\*:.*superseded' docs/decisions.md` → **0** so
  deadlock-breaker crit (b) still has no candidate. `.last_escalation` 07-31 22:01 → floor 08-03 22:01.
- **Broke the pattern**: 16 prior skips all produced *queue* diagnostics. That diagnosis is finished
  and parked on the user (STATE banner, 4 Telegram corrections). So this cycle spent its budget on
  the **research question** STATE has carried unanswered since 07-16 instead: *does widening berth
  into unobserved space recover the oracle's collision rate?*
- Merged `#69` (`vg_mppi` + `cafe_blind_approach_v0`) and `#70` (`seed_sweep`) into a detached
  worktree — **both merged clean**, re-confirming the recipe a 7th time — and ran the N=24 sweep
  18:00's power analysis sized but never executed. Sweep cost **0.65 s/seed**, so a 24-seed arm is
  **~16 s**, far inside the 2-min sim limit (18:00's 69 s figure was a different, longer scene).
- Wrote a throwaway 4th arm to fill a gap the measurement exposed (source inline below).

## What worked / what failed

**1. The N=24 baseline exists now, and the n=8 headline number was ~50 % high.**

| arm | collision | near-miss | unsafe | pass | clearance mean |
|---|---|---|---|---|---|
| `stock_mppi` (oracle perception) | **0/24** | 1.000 | 1.000 | 1.000 | +0.0210 |
| `vg_mppi(sensing_range=1.0)` | **6/24 = 0.250** | 0.750 | 1.000 | 0.750 | −0.0501 |
| `vg_mppi(sensing_range=inf)` ablation | 0/24 | 1.000 | 1.000 | 1.000 | +0.0210 |
| `risk_mppi(k=0.75)` | 0/24 | 1.000 | 1.000 | 1.000 | +0.0207 |

`vg` vs `stock`: Fisher exact two-sided **p = 0.022**. The effect is real and N=24 resolves it, as
18:00 predicted — but the rate is **0.250, not the 0.375** that 3/8 suggested, and every downstream
sizing quoted 0.375. The `sr=inf` ablation reproduces `stock` to the digit, so the gate is the only
moving part.

**2. `unsafe_rate` is saturated at 1.000 on every arm — it cannot be the primary metric.** The 0.10 m
near-miss band sits *above* every arm's clearance mode (oracle mean +0.021 m), so all 24 seeds of all
4 arms are "unsafe". 18:00 wrote the metric as "collision/unsafe RATE"; only **collision_rate**
separates. This corrects STATE next-actionable #2 before #70 gets reopened asserting the wrong field.

**3. `risk_mppi` cannot answer the occlusion question — by construction, not by tuning.**
`RiskMPPI.__init__` builds `GTBevProducer(scenario.obstacles)` from the **ground-truth** obstacle
list, so its epistemic channel is oracle-fed: it is never blind, and it scores 0/24 with clearance
+0.0207 ≈ `stock`'s +0.0210. **The repo holds an oracle-perception epistemic controller and a blind
non-epistemic controller and nothing in the intersection**, so STATE's headline question was
unanswerable with what is on the branches. Sixteen cycles of queue diagnosis hid that.

**4. Prototype filling the intersection — the answer is YES.** `EpistemicVGMPPI` = the `vg` gate plus
a v² penalty on rollout points beyond `sensing_range` ("slow down where you cannot see"):

| `w_blind` | collision | pass | duration (s) | clearance mean |
|---|---|---|---|---|
| 0 (ablation) | **0.250** | 0.750 | — | −0.0501 |
| 5 | 0.125 | 0.875 | — | −0.0205 |
| **20** | **0.000** | **1.000** | 24.2 | +0.0116 |
| 60 | 0.000 | 1.000 | — | +0.0179 |
| 200 | 0.000 | **0.875** | 32.8 | +0.0220 |

`w_blind=0` reproduces `vg` exactly (ablation invariant holds). **`w_blind=20` recovers the oracle's
0/24**, Fisher **p = 0.022** vs `vg`. Price of caution: duration **16.6 s → 24.2 s (+45 %)**, still
*under* the oracle's 26.4 s; `cte_rms` 0.223 → 0.244. Over-caution has a measurable knee —
`w_blind=200` still collides 0/24 but `completion_final` drops below the 0.99 acceptance on 3 seeds
(pass 1.000 → 0.875) at 32.8 s. Usable band ≈ **20–60**.

**5. The failure that made this necessary: D-013's clearance-shrink margin is the wrong hook under a
visibility gate.** `_extra_margin` shrinks clearance to obstacles in `self.obstacles` — but the gate
*removes* unobserved obstacles from that list, so there is nothing left for the margin to act on.
"Beware of what you cannot see" has to be an additive cost over unobserved **space** (`_extra_cost`),
not a margin on known obstacles. That is an architecture-level distinction D-013 does not draw.

## North-star delta

- **First measured movement in 21 days.** An epistemic response takes a blind controller from
  0.250 → 0.000 collision rate on a late-reveal occlusion scene at p = 0.022, at a +45 % time cost.
  That is the P3 hypothesis ("richer representation buys avoidance") clearing its first quantitative bar.
- P5 gains a corrected primary metric (`collision_rate`; `unsafe_rate` saturates) and a validated
  N (24 seeds, 16 s/arm — 4× cheaper than the 18:00 estimate assumed).
- Zero of this is committed. Gate 1 blocks the branch, so the result lives only in this file.

## Key learnings

- **A blocked queue does not block measurement.** Sixteen cycles treated "cannot open a PR" as
  "cannot work". Merging the blocked branches into a throwaway worktree costs one command and the
  experiment ran in 16 s/arm.
- **Check that the comparison arm can lose before running the A/B.** `risk_mppi` was the planned
  epistemic arm for 16 days; it is oracle-fed and structurally incapable of failing the occlusion
  test. Reading `__init__` would have caught it at any point.
- **Re-measure headline numbers before sizing on them.** 3/8 → 0.250 at N=24. The 0.375 was inside
  its own CI but every downstream plan quoted it as the effect size.
- **A saturating metric looks like a working metric until you print the other arms.** All four arms
  read `unsafe_rate = 1.000`.

## Recommended next 1–3 priorities

1. **Land `EpistemicVGMPPI` as a real controller** (`eval/mppi_sandbox/controllers/`) with the
   ablation test (`w_blind=0` ≡ `vg_mppi`) and the N=24 rate assertion. Blocked on queue drain.
2. **Reopen #70 asserting `collision_rate`, not `unsafe_rate`** — the latter saturates on this scene.
3. **Q-020 (raised, not self-authorized)**: D-013 routes epistemic response through a clearance-shrink
   margin on *known* obstacles; under a visibility gate the unknown obstacles are absent from that
   set, so the response must be a cost over unobserved *space*. Do both hooks belong in the design,
   or does D-013 need amending?

## Artifacts

- PR: **none** — gate 1 (`pr-queue-full count=6`) blocks branch creation; result is uncommitted.
- Files touched: this journal entry + `STATE.md` / `JOURNAL.md` (local-only per D-011).
- TSV row appended: no (no branch).
- Prototype source (throwaway worktree deleted; reproduce verbatim):

```python
# eval/mppi_sandbox/controllers/_proto_epistemic_vg.py
import numpy as np
from .visibility_gated_mppi import VisibilityGatedMPPI

class EpistemicVGMPPI(VisibilityGatedMPPI):
    def __init__(self, scenario, seed: int = 0, w_blind: float = 20.0, **kw):
        super().__init__(scenario, seed=seed, **kw)
        self.w_blind = w_blind
        self._robot_xy = np.zeros(2)

    def command(self, state, t):
        self._robot_xy = np.asarray(state[:2], dtype=float).copy()
        return super().command(state, t)

    def _extra_cost(self, traj, t0):
        K = traj.shape[0]
        if self.w_blind == 0.0 or not np.isfinite(self.sensing_range):
            return np.zeros(K)
        d = np.linalg.norm(traj[..., :2] - self._robot_xy, axis=2)   # (K,H)
        blind = (d > self.sensing_range).astype(float)
        return self.w_blind * (blind * traj[..., 3] ** 2).sum(axis=1)
```

Reproduce: worktree off `origin/main`, merge `origin/autoresearch/p3-visibility-gated-obstacle-cost`
then `origin/autoresearch/p5-collision-rate-over-seeds-aggregator` (both clean), register
`REGISTRY["proto_evg"]`, then `seed_sweep('eval/scenarios/cafe_blind_approach_v0.yaml',
controller='proto_evg', seeds=range(24), sensing_range=1.0, w_blind=20.0)`.
