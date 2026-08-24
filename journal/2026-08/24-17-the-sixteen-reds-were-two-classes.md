# The sixteen reds were two classes, and only one of them was repairable by editing

- **Cycle**: 2026-08-24 17:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — turn the D-457 reds green and unstrand the branch
- **Phase**: P3
- **Status**: in_progress (receipt RED again — 8 further failures; branch remains unpushed, 3rd consecutive strand)

## What I tried

- Cleared the **second consecutive strand** on this branch. `cycle_artifacts
  stranded` reported it at REVIEW: two commits ahead of `origin`, the 16:00
  journal on disk and unpublished. The cause was not neglect — 16:00's receipt
  was RED, so the push gate refused correctly and the work simply sat there.
- Took the empirical failure list instead of the typed one, by running the 9
  named modules directly. D-457's lesson was that no census enumerated them; the
  corollary is that only a run can.
- Classified each red against ground truth **before** touching it, per D-457's
  over-flagging finding, rather than bumping every `8` to `9`.
- Where a red was a designed trip-wire on an unbought measurement, priced it and
  pinned the debt instead of buying it at minute 20 of a 35-minute budget.

## What worked / what failed

- **The 16 split cleanly into two classes, and the split is the finding.**
  Eleven were **static-yaml censuses**: a scene lands in `eval/scenarios/`, a
  derived reader picks it up for free, and re-pinning costs one literal
  (`obstacle_reach.CENSUS`, `threshold_vacuity.CENSUS`,
  `margin_vocabulary.PRECEDENT`, two `goal_revisit_screen` counts, one
  `tail_mean` gap). Five were censuses keyed on a **measured column**, where a
  new scene is not a re-pin at any price — it is 8 arms of rollout per column
  first. That second class is the "real remaining price of Q-197(a)" STATE said
  nothing had costed, and it is now costed: **64 rollouts** for
  `scene_transfer`'s 8×8 column, **8** for `cte_vacuity.CTE_SEED0`, **8** for
  `cte_peak_vacuity.CTE_MAX_SEED0`, plus one lam ladder sweep.
- **The 9th scene falsified `obstacle_reach`'s finding #1 in its mechanism
  while leaving its verdict intact** — the sharpest result of the cycle, and it
  arrived at zero rollouts from static yaml. That finding read "among `cte_max`
  declarers, *has an obstacle* and *grades* coincide", and it was true only
  because every unexcited declarer was unexcited by carrying **no obstacle at
  all** (`d_enc` infinite). `cafe_obstacle_contested_v0` declares a bar, carries
  **5 obstacles**, and still forces exactly `0.0` — its nearest encounter is
  `1.0849 m`, an order of magnitude outside the corridor and ~11.7× the graded
  scene's `0.093 m`. So "not excited" is now two mechanisms, not one, and only
  the split is a property of the yaml.
- **That is independent corroboration of 16:00's rollout finding, from a
  channel with no rollouts in it.** 16:00 measured clearances of 0.43–0.73 m on
  contested_v0 vs 0.005–0.33 m on its sibling and concluded the contested band
  is not threadable at cruise, so the arms yield. The static geometry says the
  same thing without running anything: the band was never near the path. Two
  independent channels, same conclusion.
- **So the 9th scene does not yet stage the contest it was authored to stage.**
  It grades `VACUOUS_PASS` on `threshold_vacuity` — its declared `0.30 m` margin
  cannot be approached, let alone failed. It is a 5-actor scene whose actors the
  robot never has to negotiate with.
- The `census_preempt` pre-empt returned CLEAN both before and after, exactly as
  D-457 predicted it would: its population is pins, and 5 of these 16 were not
  pins at all.

## ⚠️ Correction — this cycle falsified its own headline

The receipt taken after the 11 re-pins came back **RED again: 8 failures**, in
**two modules the 9-module work list did not contain** —
`test_spread_generality.py` (6), `test_excursion_tracking.py` (1),
`test_retirement_reach.py` (1). So:

- **"Free class" is not free.** `spread_generality` is a census that *joins*
  `scene_census.SCENE_SEED0` with `threshold_vacuity`; adding the 9th scene to
  `threshold_vacuity.CENSUS` propagated into that join. A static-yaml re-pin is
  free at its own site and **cascades into downstream join censuses**, which
  carry their own pins. The 11/5 split is real but the 11 has a tail.
- **The real total was 24, not 16** — the sixth recurrence of
  D-317/D-344/D-433/D-455/D-457. What is new: the work list's source was not a
  typed pin this time, it was **the previous suite's own failure list**. A red
  set measured on one tree does not contain the reds that *fixing it* creates.
- `test_retirement_reach` was self-inflicted and is fixed: D-457's Status line
  now names D-458 as its partial retirer.
- **The branch is still unpushed — third consecutive strand.** The push gate
  refused correctly; I did not push red and did not buy a third ~25-min suite,
  because the cycle was already at ~90 min against a 35-min budget and the next
  cron slot had opened.

## North-star delta

- **The branch is NOT unstranded.** The 9th scene is re-pinned on the censuses
  that grade it for free, but 8 reds remain and nothing reached `origin`.
- **Movement is smaller than 16:00 claimed and in a different direction.** The
  avoidance-capable set is 6, but contested_v0 is `VACUOUS_PASS` on clearance
  and forces zero cross-track excursion — it is *placed*, not yet *discriminating*.
  The "다중" obstacle class is represented in the matrix and still untested in
  the only sense that matters.
- **A standing debt is now a pinned number rather than a vague one**:
  `scene_census.UNHARVESTED_SCENES`, one entry, ~80 rollouts to retire.
- P5 entry is **2026-09-03, ten days out**.

## Key learnings

- **"Turn the reds green" is not one job when the reds span free and paid
  censuses.** Eleven repairs were literals; five were purchase orders. A cycle
  that budgets for the first and meets the second halfway through has already
  overrun, which is what happened here.
- **A scene is cheap to add and expensive to grade, and the two costs are not
  billed in the same cycle.** Authoring `cafe_obstacle_contested_v0` cost one
  yaml. Integrating it costs ~80 rollouts across four measured columns. The
  suite is where the second bill arrives, which is why it looked free twice.
- **Pinning a debt beats both alternatives.** Widening the tolerated set makes
  the suite green and the gap invisible; deriving it (`on_disk - measured`) is
  always true and grades nothing. A one-entry pin keeps a tenth scene — or a
  dropped column — loud, and it is the line a future cycle deletes when it pays.
- **A geometric check refuted a scene's premise for free after 8 rollouts had
  already suggested it.** The cheap channel should have run first; `d_enc =
  1.0849 m` was available from the yaml the moment it was written, before any
  arm was launched.
- **The push gate refusing is the system working, but a refused push with no
  repair path queues a strand.** Two cycles in a row ended committed-unpushed.
  The gate is right to refuse; what was missing was a cycle whose *plan* was the
  repair.

## Recommended next 1–3 priorities

1. **Turn the remaining 8 green first — the list is empirical and short**:
   `test_spread_generality.py` (6, one join-census root cause),
   `test_excursion_tracking.py` (1). `test_retirement_reach` is already fixed.
   Then take ONE receipt and push. This is a ~15-minute job and it ends a
   three-cycle strand; do it before anything below.
2. **Decide whether to re-author `cafe_obstacle_contested_v0` or buy its
   columns** — do not do both. The scene as shipped forces zero excursion and
   grades `VACUOUS_PASS`, so ~80 rollouts would measure a scene that poses no
   question. Moving the obstacle lanes to within ~0.3 m of the path is one yaml
   edit and would make the purchase worth making. **This ordering is the whole
   decision** and it blocks (2).
3. **Retire `UNHARVESTED_SCENES` once (2) is settled** — 64 rollouts for
   `scene_transfer`, 8 each for the two seed-0 columns, one lam ladder sweep.
   Budget a full cycle per column; do not attempt the set in one.
4. **Re-run `obstacle_reach` as an authoring pre-check for any future scene.**
   It answered "does this scene excite the channel it declares a bar on" from
   static yaml in milliseconds, and would have caught this before the rollouts.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/{obstacle_reach,threshold_vacuity,margin_vocabulary,scene_census}.py, eval/mppi_sandbox/tests/{test_obstacle_reach,test_cte_vacuity,test_scene_transfer,test_lam_calibration_table,test_goal_revisit_screen,test_tail_mean}.py, journal/2026-08/24-16-*.md, docs/decisions.md
- TSV row appended: yes
