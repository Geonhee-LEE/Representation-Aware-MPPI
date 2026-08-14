# Q-148's both-on ratio is picked — and the headline was measured at the wrong radius

- **Cycle**: 2026-08-14 16:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `Q-148-ratio-pick` Choose the both-on arm's replacement ratio and record it as a D-NNN
- **Phase**: P3
- **Status**: keep

## What I tried

- STATE's #1 asked for a *choice* between a sign-robust cell (outside the root
  band) and the maximally-contended one (`band.mean`), which `both_on_cell`
  deliberately declines to make. Before picking I asked which radius the A/B is
  actually run at — `both_on_cell.survey` sweeps seven and defaults to `r=0.5`.
- Read Q-148's next action: the A/B runs on `cafe_blind_corner_v0`, whose
  occluding wall is five discs of **`radius: 0.3`**. Quoted that number rather
  than importing the yaml (it lives on unmerged PR #68).
- Shipped `eval/mppi_sandbox/ratio_pick.py` + 9 tests: the pick, the two
  measurements behind it, and a `transfers_to` guard for the cost.

## What worked / what failed

- **Measurement 1 — D-260's headline does not hold at the A/B's geometry.**
  `r=0.3` is the single radius in the surveyed set where the published `0.3587`
  is **not** `ATTRACT`: its band `[0.1704, 0.5770]` contains the ratio, so the
  cell reads `INDETERMINATE`. That band is also the widest in the set (`0.4066`,
  2.07x the `r=0.5` band). D-260 is correct about the five radii it surveyed and
  silent about the only one that will be run.
- **Measurement 2 — contendedness does not transfer; sign-robustness does.**
  Across the six posed radii `max(band.lo) = 0.6386 > min(band.hi) = 0.5770`
  (`r=0.3` and `r=0.5` are outright disjoint), so **no constant ratio is
  `INDETERMINATE` everywhere**. Sign-robust constants do exist (`< 0.1704`
  attract, `> 0.8347` repel) at every radius.
- **The pick is not a coin flip, and measurement 2's naive reading is a trap.**
  Read alone, 2 favours sign-robust: it is the only choice that is a constant of
  the branch rather than a function of the scene. But a resolved sign *is* one
  arm dominating the sum — `is_duplicate_of_a_single_arm` is exactly the
  negation of `INDETERMINATE`. A sign-robust both-on arm is the third instance
  of the duplication that D-256 and D-260 each caught once.
- A test I wrote was wrong: `test_scene_radius_provenance` used a docstring-split
  text heuristic and failed on a *comment* naming the scene, which is the
  provenance record working as intended. Replaced with an AST import check —
  the boundary is about code, not prose.

## North-star delta

- No closed-loop movement; this is still a cost-field reading, and the A/B stays
  blocked on PR #68 for the eighth cycle.
- What moved: the four-arm A/B's both-on cell now has a **defensible** weight
  (`0.4121 : 1` at the scene's radius) instead of one that was twice found to be
  a disguised re-run of a single arm. The experiment can be run the moment #68
  lands without re-deriving its design.

## Key learnings

- **A survey's default parameter is not the experiment's parameter.** Three
  cycles reported this cell at the instrument's `r=0.5` while the scene it feeds
  is `r=0.3`. Nothing was wrong with any measurement; the question "which radius
  is the A/B at" had simply never been asked out loud, and the answer flips the
  headline.
- **Two desiderata can look like a trade-off and be one property twice.**
  "Sign-robust" and "duplicates a single arm" are the same condition under two
  names, so the tension STATE recorded was not real once stated precisely. That
  is why the pick needed no new evidence — only the definition unpacked.
- **`INDETERMINATE` is the right reading to accept, not to tune away.** The A/B
  is adjudicated on near-miss and clearance (Q-148; D-250 warns off `d_reached`),
  which need no cost-field sign at all.

## Recommended next 1–3 priorities

- **Q-148 four-arm spec freeze**: write the four `(w_epist, w_voo)` pairs out
  explicitly now that the both-on cell is fixed, so the A/B is a config, not a
  derivation, when #68 merges.
- **`inert-probe-budget`** (carried): decide whether to buy back the five
  withdrawn `inert_surface` exemptions via sharding, or keep paying D-259's
  ordering discipline per cycle.
- **Re-check `SCENE_RADIUS` on #68 merge** — `scene_radius_provenance()` returns
  `recheck_on_merge: True`; if the merged yaml's occluder radius differs, every
  number in `ratio_pick` is about a scene that no longer exists.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/ratio_pick.py, eval/mppi_sandbox/tests/test_ratio_pick.py, docs/decisions.md, docs/deliberations.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: pending
