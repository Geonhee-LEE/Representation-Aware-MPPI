# The selectivity claim survives its statistics but not its label — the "epistemic" cost reads no epistemic state

- **Cycle**: 2026-08-02 00:00 KST
- **Branch**: none (gate 1 fired, **19th consecutive**) — measured in a throwaway worktree off `origin/main` + `#66`+`#67`+`#68`+`#69`
- **TODO**: none picked — SKIP path, `reason=pr-queue-full count=6`
- **Phase**: P3/P5 (calendar phase P4)
- **Status**: in_progress (result measured, cannot be committed until the queue drains)

## What I tried

- Gate 1 re-derived per-branch: **6 OPEN** (`#66/#67/#68/#69/#44/#23`), 0 pushed-but-PR-less, 0 branches
  in 24 h, daily-cap 0/10. `grep -cE '^\s*-?\s*\*\*Status\*\*:.*superseded' docs/decisions.md` → **0**,
  so deadlock-breaker crit (b) still has no candidate; not forced. `.last_escalation` 07-31 22:01 →
  floor **08-03 22:01**, not re-sent. Last merge #64 @ 2026-07-12 → **20.4 d**.
- Declined a tempting false unblock: all 6 PRs carry `needs-user-attention`, which the executor *could*
  strip with `gh pr edit`. Removing it would hand Curator an auto-merge path into `main` — routing
  around the "merging is the user's job" hard limit by proxy. Left in place deliberately.
- 23:00 retracted the safety claim and left one standing: *"the representation makes the caution
  **selective**"* — epistemic `w=20` costs **+2.9 %** on an open scene where a duration-matched
  `v_max=0.65` cap costs **+17.9 %**. Its own §3 undercuts it: **both** "nothing hidden" scenes
  (`city_curved_v0`, `cafe_straight_v0`) have *no modeled obstacles at all*, so "the cost stays inert
  where it is not needed" had only ever been measured on an **empty map**.
- That comparison also pits a **soft cost** against a **hard clamp**, so I built the two arms that
  separate the candidate explanations, N=24 per cell, paired by seed:
  **(H1) spatial structure** — `uniform_soft(w=10)`, the blind mask *deleted* (23:00's arm);
  **(H2) soft-vs-hard** — `horizon_slow(w=20, h0_frac=0.5)`, **new**: identical `v²` penalty, but the
  mask is the **rollout step index** (`h > H/2`). It references no obstacle set, no `sensing_range`,
  no visibility geometry — it cannot encode anything epistemic.

## What worked / what failed

**0. ✅ 23:00 reproduced exactly** — `epistemic +2.9 %`, `speedcap +17.9 %`, paired Δ `+3.17 s`
CI `[+2.88, +3.45]`. The worktree is faithful, so what follows is a real disagreement, not drift.

**1. ❌ H1 refuted — a mask with zero epistemic content is *better* at selectivity.**

| arm (N=24, paired) | blind: dur / coll | curved: dur | curved Δ vs baseline |
|---|---|---|---|
| `vg_mppi(sr=1.0)` baseline | 16.64 / **6/24** | 21.03 | — |
| `epistemic(w_blind=20)` | 24.16 / **0/24** | 21.63 | **+2.9 %** `[+0.25,+0.95]` |
| `uniform_soft(w=10)` — mask deleted | 27.29 / **0/24** | 28.15 | +33.9 % `[+6.57,+7.68]` |
| **`horizon_slow(w=20)` — rollout-index mask** | 25.59 / **0/24** | **19.40** | **−7.7 %** `[−1.96,−1.29]` |
| `speedcap(v_max=0.65)` | 24.65 / **0/24** | 24.80 | +17.9 % `[+3.46,+4.08]` |

`horizon_slow` is duration-matched on the blind scene (25.59 s, inside the 24.2–27.3 s band of every
safe arm) and reaches the same **0/24** — then on the open scene it is **faster than the baseline**,
beating the epistemic arm by **−2.23 s, CI [−2.59, −1.86]**. A penalty that knows *nothing* about
visibility dominates the one that is supposed to encode it.

**2. ❌ H2 also refuted — softness alone is not the mechanism.** `uniform_soft` is a soft, tradeable
cost and is the **worst** arm of all (+33.9 %, worse than the hard clamp's +17.9 %). So "soft costs
stay inert, hard clamps don't" is false as stated.

**3. 🔍 The code says it outright — no experiment needed.** `EpistemicVGMPPI._extra_cost` is
`w · Σ_h v_h² · 1[‖xy_h − xy_robot‖ > sensing_range]`. Introspected references to
`self.obstacles`, `last_observed`, `observed_obstacles`, `_all_obstacles`, `_occluded`: **all False**.
`sensing_range` enters only as a scalar radius. The controller labeled "epistemic" is a **distal-speed
penalty**; its blind mask is a function of the robot's own pose and the rollout geometry, on *every*
scene — not just the obstacle-free ones. The empirical result only confirms what the source already said.

**4. ⚠️ Mechanism identified but not pinned.** What the two cheap arms share is that they penalise only
the **distal** part of the rollout, leaving near-term speed free; the two expensive arms penalise the
immediate segment too. Sweeps are consistent but weak (N=12, curved): epistemic falls monotonically
with `sensing_range` (0.5→4.0 m: 21.98→20.93 s — a wider range shrinks the penalised distal region),
while `horizon_slow` is *faster than baseline at every* `h0_frac` (19.16 / 19.43 / 20.10 for
0.25 / 0.50 / 0.75) and moves the *wrong* way with `h0`. I do not have a mechanism that explains that
sign. **Honest status: the retraction is solid; the replacement mechanism is a hypothesis.**

**5. Not free.** `horizon_slow` buys its speed partly with tracking error on the blind scene
(`cte_rms` 0.3055 vs epistemic 0.2443); on curved they are near-tied (0.1419 vs 0.1230). So it is not
*strictly* dominant — but selectivity was defined on time cost, and on that axis it wins outright.

## North-star delta

- **Net movement is a second retraction, one level deeper than 23:00's.** The claim's *statistics*
  survive (+2.9 % vs +17.9 %, CI excludes zero, reproduced). Its *interpretation* does not: it is not
  evidence that a richer representation buys anything, because the controller contains no
  representational information and a non-representational control does better on the same axis.
- **The P3 hypothesis now has zero surviving quantitative support.** Two cycles ago it had a safety
  result; 23:00 reduced that to an efficiency result; this cycle removes the representation from the
  efficiency result. What has actually been measured across all three cycles is **cost-shaping over the
  MPPI horizon** — a real and reusable finding, but orthogonal to "representation quality bounds
  control quality".
- **P5 metric consequence, third in three cycles.** After `unsafe_rate` (saturates) and
  `collision_rate` (gameable by slowness), add: **a controller's *name* is not a factor.** Any
  representation-vs-baseline comparison needs an arm that has the same *cost structure* with the
  representation removed — not merely the representation's weight set to zero. `w_blind=0` was a
  correct ablation and still could not catch this, because it tests the term's *presence*, not whether
  the term carries the information the label claims.

## Key learnings

- **An ablation tests whether a term matters; it cannot test whether the term means what you named it.**
  `w_blind=0` was the right ablation and passed. The check that caught this was 30 s of introspection
  on `_extra_cost`'s free variables — *does this function read the state it claims to depend on?*
  That check is cheap, static, and should run before any measurement.
- **Two cycles in a row, the decisive arm was the one that keeps the functional form and destroys the
  semantics** (23:00: invert the mask; 00:00: re-index the mask to rollout step). This is now a
  pattern worth naming, not a coincidence.
- **A refutation can be produced by reading the code you are about to benchmark.** The measured result
  is confirmatory here; the claim was already dead in the source.
- Third consecutive cycle where the blocked queue cost nothing — ~7 min CPU. But the record is now
  **12 uncommitted journal entries** deep, and this cycle contradicts two of them. The
  commit-the-record item is no longer housekeeping; the on-disk narrative is actively misleading.

## Recommended next 1–3 priorities

1. **Do NOT land `EpistemicVGMPPI` under that name** — supersedes 23:00's recommendation #1. If the
   controller lands at all it is `DistalSpeedPenaltyMPPI`, with `horizon_slow` as a registered control
   arm and a test asserting the **−2.23 s** gap (i.e. asserting the non-representational arm *wins*).
   Landing it as "epistemic" would commit a claim this cycle refuted.
2. **Add a `test_cost_term_reads_its_named_state` contract to the sandbox** — static introspection that
   a critic named for a representation actually references that representation's state. ~15 LOC,
   catches this whole class before it costs three cycles.
3. **Build one scenario with a modeled, fully-visible obstacle** (`dynamic_obstacles` with a static
   entry off the reference path). Every "nothing hidden" scene in the matrix is an *empty* map, so
   "inert where not needed" has still never been tested against a present-but-observed obstacle.
4. **Q-022 (raised, not self-authorized)**: should the P5 harness require, for every
   representation-bearing controller, a *semantics-destroying* control arm (same cost structure,
   representation replaced by a non-informative surrogate) alongside the usual weight-zero ablation?

## Artifacts

- PR: **none** — gate 1 (`pr-queue-full count=6`) blocks branch creation; result is uncommitted.
- Files touched: this journal entry + `STATE.md` / `JOURNAL.md` (local-only per D-011).
- TSV row appended: no (no branch).
- Arm source: `_proto_arms.py` reproduced below; `EpistemicVGMPPI` / `UniformSlowVG` / `NearSlowVG`
  are verbatim from 22:00 / 23:00. Only `HorizonSlowVG` is new.

```python
# eval/mppi_sandbox/controllers/_proto_arms.py  (new arm only; others in 01-23-*.md)
class HorizonSlowVG(VisibilityGatedMPPI):
    """Same v^2 penalty; mask = rollout step index > h0. Reads no obstacle set,
    no sensing_range, no visibility geometry — cannot encode anything epistemic."""

    def __init__(self, scenario, seed: int = 0, w_slow: float = 20.0,
                 h0_frac: float = 0.5, **kw):
        super().__init__(scenario, seed=seed, **kw)
        self.w_slow = w_slow
        self.h0_frac = h0_frac

    def _extra_cost(self, traj, t0):
        K, H = traj.shape[0], traj.shape[1]
        if self.w_slow == 0.0:
            return np.zeros(K)
        h0 = int(self.h0_frac * H)
        mask = np.zeros((1, H))
        mask[0, h0:] = 1.0
        return self.w_slow * (mask * traj[..., 3] ** 2).sum(axis=1)
```

Reproduce: merge `#66→#67→#68→#69` into a worktree off `origin/main` (resolve `#66↔#67` on
`test_risk_mppi.py` + `docs/deliberations.md` in favour of `#66`), drop the module in, register
`proto_evg` / `uniform_slow` / `horizon_slow`, run N=24 × {blind, curved}.
