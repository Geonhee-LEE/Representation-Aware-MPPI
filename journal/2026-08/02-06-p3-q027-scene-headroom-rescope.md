# Q-027: rescoping the scene kills the collision result and strengthens the clearance one

- **Cycle**: 2026-08-02 06:00 KST
- **Branch**: _none_ — gate 1 (pr-queue-full=6) fired, 25th consecutive skip
- **TODO**: _none picked_ — executor merge-blocked; work done as an uncommitted probe
- **Phase**: P3 (calendar P4 window; the P3 chain is what is queued)
- **Status**: in_progress (uncommitted, `/tmp/proto_0802_06/`)

## What I tried

Q-027 (raised 05:00) asked whether `cafe_blind_approach_v0` is admissible as a
**safety** test-bed at all, given its oracle rides the barrier at ~1 cm on every
seed. The direct test: re-scope the scene so the oracle plans a **real berth**,
then check whether #69's stock-vs-vg separation survives.

- **Part 1** — barrier grid (`w_obs_soft` × `obs_soft_scale`) × `lam`, with ESS
  measured at every point (raising the barrier raises the cost scale, so a
  fixed-`lam` barrier sweep would silently re-run the 03:00 temperature bug).
- **Part 2** — after part 1's winners turned out to be artifacts (below), added a
  hard **goal-reached guard** and swept two honest headroom axes: lowering
  `w_path`, and offsetting the hazard off the path centreline.
- **Part 3** — full N=24 both arms on the **minimal-edit** rescopes, including a
  **geometry-only** one where the controller is bit-identical to what #69 ships.

## What worked / what failed

- 🔴 **Part 1's "headroom" was freeze, and my filter let it through.** It ranked
  settings on (berth ≥ 0.10 m) ∧ (ESS in band) and reported three winners at
  `w_obs=160` with oracle berth **+0.82…+1.53 m** and 0/24 collisions. All three
  are bogus: oracle `d_goal` was **5.42 / 5.13 / 1.50 m** on a 7 m path at
  `mean_v` 0.11 m/s. The oracle never reached the hazard — its "berth" is where it
  gave up, its 0/24 is bought by not moving, and the p = 1.19e-07 against `vg` was
  pure progress confound. **STATE's own backlog names this guard and I omitted it.**
- ✅ **With the goal guard, real headroom does exist** — 10 settings pass
  (berth ≥ 0.10, `d_goal` ≤ 0.25, both arms' ESS in 0.05K–0.50K), so the scene is
  not stuck choosing between graze and freeze after all.
- 🔴 **The collision result does not survive rescoping.** N=24, Fisher one-sided:

  | rescope | stock | vg | Fisher | stock med clr | vg med clr | Wilcoxon | pairs stock>vg |
  |---|---|---|---|---|---|---|---|
  | **SHIPPED** (control) | 0/24 | **5/24** | **0.0248** | +0.010 | +0.005 | 0.0164 | 16/24 |
  | `w_path=3` | 0/24 | 0/24 | 1.00 | +0.257 | +0.021 | 1.19e-07 | **24/24** |
  | `w_path=1` | 0/24 | 2/24 | 0.24 | +0.388 | +0.018 | 1.19e-07 | **24/24** |
  | **geometry-only** `offset=0.6` | 0/24 | 0/24 | 1.00 | +0.176 | +0.087 | 5.96e-07 | 23/24 |
  | **geometry-only** `offset=0.9` | 0/24 | 0/24 | 1.00 | +0.364 | +0.265 | 5.96e-07 | 23/24 |

  `p = 0.0248 → 1.00` the moment the oracle gets room. **#69's headline metric is
  regime-specific to the degenerate scene.**
- ✅ **The clearance result survives everything and gets stronger** — 23–24 of 24
  pairs in every rescope, including the **geometry-only** one where no controller
  knob moves. It cannot be a tuning artifact.
- ⚠️ **p = 1.19e-07 is the exact floor of a 24-pair signed-rank test** (2/2²⁴).
  Identical p across settings is saturation, not equal effect size — read size off
  the medians. Part 2 reported that p three times without noticing.

## North-star delta

- **The mechanism is now visible, and it is the project's thesis.** Under the
  `w_path` rescopes the oracle widens its berth to **+0.26 → +0.39 m** while `vg`
  stays pinned at **+0.02** — the gated arm *cannot spend* the freedom, because it
  does not see the hazard until 1 m out. **The representation, not the cost
  weighting, is the binding constraint on achievable safety margin.** That is the
  cleanest statement of the core hypothesis the project has produced from data.
- **P5 metric guidance sharpens 05:00's Q-021 answer**: `collision_rate` is the
  metric that **does not survive scene re-scoping**; `min_clearance` is the one
  that does, on both scenes and under a controller-untouched geometry edit.
- Honest scope: 5 rescopes × 24 seeds, one scene family, one sensing range. The
  three part-2 settings were near-duplicates sharing seeds — correlated views,
  not replications.

## Key learnings

- **05:00's lesson recurses: a *large* margin is not safe either — check the
  progress it was bought at.** Zero collisions and 1.5 m of clearance can both be
  purchased by refusing to move. Every safety claim needs a **completion guard**
  on the same run, not as a separate check.
- **A metric that reverses under scene re-scoping was measuring the scene.** The
  collision count survived temperature, contact-threshold and radius sweeps at
  05:00, then died on the first *geometry* perturbation — invariance under
  controller nuisance parameters does not imply invariance under scene scope.
- **#69 should be re-scoped before it lands**, not withdrawn: its assertion is
  true as written and its clearance evidence is far stronger than its own
  description claims, but the *collision* framing is the fragile half.

## Recommended next 1–3 priorities

1. **Re-frame #69's assertion around `min_clearance`, not the collision count** —
   the clearance form holds on 5 rescopes + a second scene; the count form holds
   only in the shipped tuning.
2. **Land a `completion_guard` helper** asserting `d_goal ≤ goal_xy_tol` for every
   arm in any A/B, and make the sandbox refuse to report a comparison without it.
3. **Commit this + the previous 17 orphaned journal entries** — user action; the
   executor cannot push `main`.

## Artifacts
- PR: _none_ (gate-1 skip; no branch created)
- Files touched: none committed. Probe source + raw JSON in `/tmp/proto_0802_06/`
  (`_headroom.py`, `_headroom2.py`, `_headroom3.py`, `headroom{,2,3}.json`);
  scratch merge tree reused at `/tmp/scratch_p3merge`
- TSV row appended: no (no branch)
