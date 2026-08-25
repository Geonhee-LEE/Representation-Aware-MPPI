# The excursion grew 4.6×, the clearance it bought did not move

- **Cycle**: 2026-08-23 15:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `3c5c5d39` Q-188 magnitude-vs-aim reading
- **Phase**: P3
- **Status**: keep

## What I tried

- Built `eval/mppi_sandbox/avoidance_aim.py` — Q-188's discriminator as a
  **budget at one instant**. At each seed's closest-approach index: `deviation`
  (distance from the reference polyline), `on_path_clearance` (the clearance
  the robot *would* have had standing on its own path foot at that same
  instant, hazard position taken from the log), and `gain = clearance −
  on_path_clearance`. Since moving `d` metres can raise a distance by at most
  `d`, `deviation < required` ⇒ no aim could have cleared (Q-188 **(a)**), and
  `deviation ≥ required` with `gain < required` ⇒ big enough and misdirected
  (**(b)**).
- Deliberately **not** peak deviation, which is how Q-188 was drafted: D-444
  established the excursion is *early*, so its peak can sit seconds before the
  encounter and describe a moment that decided nothing. Both lengths are read
  at one index, which is what makes it a budget instead of two statistics.
- Swept the clearance target over `(0.10, 0.20, 0.30)` rather than fixing one,
  and ran both D-444 arms (`w_heading` 0 / 32), 16 seeds each. 32 integrations,
  ~20 s, **zero controller/cost source change**.
- 21 unit tests pin the scoring, including `gain ≤ deviation` over 200 random
  trajectories — the inequality the whole discriminator rests on.

## What worked / what failed

- ⭐ **Q-188's dichotomy is not a property of the controller — it is a property
  of the target.** The verdict flips monotonically along the ladder, the same
  way in both arms: target 0.10 → **AIM** (16/16 and 13/16), 0.20 → **MIXED**
  (10:6 and 7:9), 0.30 → **MAGNITUDE** (14/16 and 12/16). Any single target
  would have "answered" Q-188, and which answer you got would have been the
  number you picked. The ladder is the finding, not scaffolding around it.
- ⭐ **`gain` is decoupled from `deviation`.** Deviation spans 2.4×/4.6× across
  seeds (0.213–0.515 m, 0.133–0.613 m); the clearance it buys stays inside
  0.099–0.193 m and 0.067–0.159 m, and the correlation is **absent in both
  arms** — Pearson r = −0.087 (p=0.75) and +0.094 (p=0.73). Swerving harder
  buys nothing.
- ⭐ **The mechanism is aim, and it degrades with size.** `aim_efficiency =
  gain/deviation` runs 0.15–0.70 (never near 1.0) and collapses against
  deviation at r = **−0.811** (p=1e-4) and **−0.893** (p<1e-4), Spearman −0.58
  / −0.91. Every extra centimetre of excursion goes somewhere other than away
  from the hazard. **This is the mechanism behind D-442's ρ≈−0.54**: gain is
  flat, aim worsens with size, so the seeds that detour most pass closest.
- ⭐ **`on_path_clearance` is negative in 32/32 runs** (−0.055 to −0.180 m).
  At the deciding instant the reference path is *inside* the actor's body. The
  robot is not failing to leave a safe path — it is being handed a colliding
  one and clawing back ~0.14 m of it. Nothing in D-442/D-444 had measured this;
  both reasoned about deviation as a cost with no baseline to price it against.
- ⚠️ **The suite went red on one test, and it is the fifth consecutive instance
  of the same shape.** `test_lam_dependence::test_two_sites_are_not_tests_and_
  neither_bills_a_sim` — `avoidance_aim.measure_arm` is the sixth non-test lam
  site, entering `SILENT` (D-443's precondition placement was copied, so the
  classification was right the first time; only the population literal moved).
  `census_preempt` covers **neither** this census nor the two derived pins
  (`weighting_at_shipped`, `decides−defaults`) that a targeted run caught
  earlier. Three of the four repairs this cycle needed were invisible to the
  pre-empt. That is Q-183's complaint arriving for the fourth and fifth time,
  and it cost a second 25-minute suite.
- ❌ Q-188 as posed cannot be closed on (a) or (b), and that is the honest
  outcome rather than a failure to measure. Both branches presumed clearance is
  purchasable with excursion; the flat `gain` says the purchase saturates.

## North-star delta

- **Non-zero, and it is a redirection.** The last cost-side lever Q-188 held
  open (D-427 compact support, live only under branch (a)) is now conditional
  on a target ≥ 0.30 m, and even there the flat-`gain` result says a bigger
  excursion is not what a cost lever would need to produce. The next move is
  the reference path, i.e. the representation hypothesis.
- 32 integrations, 0 lines of controller / cost / representation source. No
  metric on `cafe_obstacle_crossing_v0` moved this cycle by construction.
- One measurement instrument added (`avoidance_aim`, 21 tests) and one
  previously-unmeasured quantity exposed (`on_path_clearance`).

## Key learnings

- **A dichotomy that flips with its own threshold was never a dichotomy.**
  Q-185 was answered by refusing to round a split; Q-188 is answered by
  refusing to pick a target. Both times the discipline was to report the
  ladder. A single-value version of this module would have shipped a confident
  wrong answer in ~20 s.
- **Price a deviation against a baseline or you have not priced it.** Four
  cycles (D-440/442/444 and this one's premise) treated cross-track excursion
  as a pure cost. The counterfactual — *what would the path itself have given
  you here* — took ten lines and inverted the framing: the path is in
  collision, so the excursion is not overspend, it is partial repair.
- Reading two lengths at **one** index is what made the comparison a budget.
  Q-188's drafted "peak deviation vs required offset" would have compared a
  quantity from t≈2 s against one from t≈3.8 s and called the difference a
  finding.

## Recommended next 1–3 priorities

1. **Q-189 — why does `gain` saturate at ~0.14 m?** Same 32 runs, no new sim:
   decompose the deviation vector at closest approach into along-path and
   cross-path components. If the excess is along-path, the controller is
   slowing/lagging rather than side-stepping, and the lever is the path's
   *time* parameterisation, not its shape.
2. **The reference path is in collision — measure how long for.** Per seed,
   the interval over which `on_path_clearance < 0`. This is a scenario-level
   defect that no controller tuning can answer, and it decides whether
   `cafe_obstacle_crossing_v0` is a fair test at all.
3. **Q-183 fourth-recurrence decision** — `census_preempt`'s coverage list is
   hand-maintained and has now missed four censuses; derive it instead.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/avoidance_aim.py, eval/mppi_sandbox/tests/test_avoidance_aim.py, eval/mppi_sandbox/loop_reach.py, eval/mppi_sandbox/tests/test_default_lam_sites.py, eval/mppi_sandbox/tests/test_lam_dependence.py, docs/decisions.md, docs/deliberations.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: yes
