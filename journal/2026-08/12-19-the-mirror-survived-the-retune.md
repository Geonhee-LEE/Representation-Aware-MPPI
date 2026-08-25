# The mirror survived the retune — it is the family, not the difficulty

- **Cycle**: 2026-08-12 19:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `STATE-1` Retune `city_crossing_v0` to an uncensored operating point (Q-134)
- **Phase**: P3
- **Status**: keep

## What I tried

- Swept a lead/lag δ on all four pedestrian schedules (the scene shipped with
  each one intercepting the robot **exactly** at its x) and read the baseline
  worst-case clearance at each: **0.0 / 0.75 / 1.5 / 2.25 / 3.0 s → 0.0025 /
  0.2415 / 0.6832 / 1.0554 / 1.2684 m**, all 6/6 reached.
- Applied δ = **0.75 s**, the only rung that straddles the declared 0.30 m
  margin (worst 0.2415 *under*, median 0.3869 *over*). 1.5 s and beyond is
  uncontested — the censoring flips to convoy's FLOOR direction.
- Re-walked the `w_risk × w_ped` 2×2 on the retuned scene: 6 paired seeds,
  λ = 0.8, D-219/D-222's protocol unchanged.
- Added `test_the_baseline_is_not_censored_below_the_margin`.

## What worked / what failed

- **The mirror reproduced.** At the uncensored operating point the sign pattern
  is the same as D-222's censored one, and still the opposite of the cafe
  family:

  | | `w_ped = 0` | `w_ped = 50` | step |
  |---|---|---|---|
  | `w_risk = 40` | 0.3504 | 0.3418 | **−0.0085** |
  | `w_risk = 0`  | 0.2415 | 0.2901 | **+0.0486** |

  Standalone helps, with-risk hurts — cafe is exactly inverted (+0.3755 /
  +0.1968 / +0.0806 with risk, flat-to-negative alone). Zero
  `BOUGHT_WITH_FREEZE`; every cell 6/6.
- **The existing anti-vacuity screen was one-sided, and its docstring said
  otherwise.** `test_the_baseline_is_contested_at_the_declared_margin` claims
  to screen "both censoring directions"; both of its assertions bound the
  baseline from *above*. The δ = 0 scene — median clearance 0.018 m, i.e. the
  typical run already inside the margin — **passed it cleanly**. Failing worse
  is still failing to clear.
- **`is_interaction` is still `False`, but for a different reason than D-222
  thought.** The ladder now reads `SIGN_FLIP / SIGN_FLIP / CONDITIONAL /
  INERT` across {1e-6, 1e-3, 1e-2, 5e-2}: it collapses because **both** steps
  are sub-5 cm, not because the scene is degenerate. Off-family, `w_ped` barely
  moves clearance in either direction — an order of magnitude under cafe.
- **Largest effect in the table is not `w_ped` at all**: the risk term alone
  buys **+0.1089 m** (0.2415 → 0.3504). On `cafe_obstacle_crossing_v0` the same
  comparison *costs* 0.0134 m. That is mirrored too, and it is 2× the size of
  anything `w_ped` does here.

- **The census billed the new screen, in the good column.** `default_lam_sites` went `decides` 82 → 83 / `total` 167 → 168 with `defaults`, `forwards` and `inert_defaults` all unmoved — the new screen names `lam=0.8` at the call site, so it cost nothing on the column that tracks silent temperatures. Caught by the first suite, one line to repair.

## North-star delta

- **Q-134 answered, and D-222's conclusion strengthened rather than
  overturned.** The off-family mirror is a property of the environment family,
  not of a regime where every arm fails. `is_interaction`'s cafe-boundedness
  stands on a reading that is now uncensored.
- One measurement surface repaired: the off-family scene is gradeable in both
  directions instead of one, so the next cycle to touch its schedule finds out
  from a test rather than from a confounded table.
- No planner capability change. This is a measurement cycle.

## Key learnings

- **A screen that names two directions can be checking one.** The docstring
  was written in good faith and the file's four other assertions are sound;
  the gap was that "contested" was spelled as a single upper bound. The
  censored scene passed it. Prose asserting coverage is not coverage — the
  same shape as D-107's empty-population-reads-as-clean, one level up.
- **Retuning changed the magnitudes by ~4× and the sign pattern by nothing.**
  That is what makes this a family reading: the confound Q-134 named was real
  and worth 4 minutes to remove, and removing it left the conclusion intact.
  Had I only re-read the verdict token I would have seen `SIGN_FLIP` both
  times and learned nothing — D-222's own warning about tallying tokens.
- **Sub-5 cm steps are the honest ceiling of this scene's `w_ped` reading.**
  6 seeds with no CI cannot separate +0.0486 m from noise. The reproducing
  *sign across two operating points* is the evidence here; neither step's
  magnitude is.

## Recommended next 1–3 priorities

1. **Seed-widen the off-family 2×2** — 6 → 20 seeds with a paired CI on the
   two steps. It is the only thing standing between "the sign mirrors" and "the
   sign mirrors significantly", and both steps are now sub-5 cm.
2. **Read the risk term alone across families** — it is the biggest mirrored
   effect measured (+0.109 off-family vs −0.013 on cafe crossing) and no
   decision has booked it.
3. **Re-probe the `journal/` / `results/` / `STATE.md` pins** (D-207) — still
   STATE #3; paid again this cycle by write-ordering rather than by a suite.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/scenarios/variants/city_crossing_v0.yaml, eval/mppi_sandbox/tests/test_city_crossing_scene.py, docs/decisions.md, docs/deliberations.md, journal/2026-08/12-19-the-mirror-survived-the-retune.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: yes
