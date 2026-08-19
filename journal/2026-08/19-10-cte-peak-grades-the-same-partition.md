# The peak cross-track bar grades the same partition the RMS bar did

- **Cycle**: 2026-08-19 10:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1c — sweep `cte_max` (peak) from the pinned `CTE_SEED0` rollouts
- **Phase**: P3
- **Status**: keep

## What I tried

- Took the last free column on the acceptance matrix: `cte_max`, the peak
  cross-track bar, declared by 4 of 8 scenes and named by D-358 as the cheapest
  remaining sweep. STATE said the rollouts were "already pinned" — they are
  **not**: `CTE_SEED0` pins the derived `cte_rms` statistic, not the
  trajectories. Re-harvested the 64 rollouts (8 scenes x 8 arms, seed 0) reading
  `metrics["cte_max"]`; ~90 s.
- Shipped `eval/mppi_sandbox/cte_peak_vacuity.py` mirroring `cte_vacuity`'s
  shape (pinned census, ceiling comparison, `drift()` CLI) + 13 pytest.
- Shrank `cte_vacuity.UNSWEPT_KEYS` by the key this cycle closes, deriving the
  gap against all three swept keys so the two censuses cannot disagree.

## What worked / what failed

- **The hypothesis I wrote the module to confirm was refuted by the data, and
  the refutation is the result.** I expected the peak bar to grade a scene the
  RMS bar washes out — an excursion that survives a max but not a mean. It does
  not: `cafe_obstacle_crossing_v0` discriminates on **both** bars, and
  `straight`/`curved`/`figure8` are vacuous on **both**. `RMS_BLIND` is empty.
  I had the wrong finding pinned in the first draft and the module's own
  `drift()` caught it (`rc=1`) before any test was written.
- So D-358's five vacuous cells are **not** an artefact of statistic choice.
  The obvious cheap repair — "read the peak instead" — was free once the
  rollouts existed and moves nothing.
- **Corroboration for the feed's curvature mechanism, on two statistics.**
  Headroom (declared / attained `hi`) orders the vacuous scenes
  `curved` (2.18x) < `figure8` (9.25x) < `straight` (23.26x) on the peak bar,
  and `curved` (3.84x) < `figure8` (20.0x) < `straight` (22.7x) on the RMS bar.
  Same monotone ordering, two different statistics of the same trajectories.
- Honest limit: that ordering is **3 points read off scene names**, with no
  curvature radius computed. `CURVATURE_UNMEASURED` names the test that would
  promote it from corroboration to evidence.
- `cbf_mppi` is the only arm over any peak bar (`1.0272` vs `1.0`, by `0.0272 m`)
  — the same arm `clearance_census` calls its only winner and the same arm
  D-358 found failing cross-track twice.

## North-star delta

- The 경로추종 column's last unswept acceptance key is closed: 4 scenes graded,
  1 `DISCRIMINATING`, 3 `VACUOUS_PASS`, 4 `UNDECLARED`. Unswept keys 13 -> 12.
- **No new gradeable cell.** The matrix's grading power is unchanged; what moved
  is that one candidate explanation for the vacuity is now eliminated rather
  than open.
- The user-blocked question is materially narrowed: "mis-set constants or
  intended slack?" now has a third answer that is not threshold-shopping —
  scene geometry — with a measured ordering behind it.

## Key learnings

- **A vacuity finding should be attacked with a different statistic before a
  different threshold.** It costs one re-harvest and it cleanly separates "we
  measured it wrong" from "the scene cannot excite it". Here it eliminated the
  first, which is what makes the second worth a cycle.
- STATE's "zero new sim time" was wrong and cheap to disprove — pinned
  *statistics* are not pinned *rollouts*. Worth checking before budgeting a
  cycle on the claim.
- Writing the module's `drift()` census before the tests paid: the pin I typed
  from expectation went red against the derived value in one command.

## Recommended next 1-3 priorities

1. **Measure the curvature claim** — per scene, min curvature radius of
   `Scenario.waypoints` vs the sampler's `horizon x v_max` reach. Converts
   D-360 finding #2 from a 3-point ordering into a testable claim, no rollouts.
2. **`city_curved_v0` at 2.18x headroom is the cheapest scene to make grade** —
   an 8-seed widening (448 rollouts, `WIDENING_UNBOUGHT`) would say whether it
   falls on its own.
3. **4 scenes declare no `cte_max`** (`convoy`/`cut_in`/`freezing`/`head_on`),
   including both headline scenes — `acceptance_coverage`'s blind spot, and the
   reason this column is silent exactly where D-352/D-353 took their numbers.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/cte_peak_vacuity.py, eval/mppi_sandbox/cte_vacuity.py, eval/mppi_sandbox/tests/test_cte_peak_vacuity.py, eval/mppi_sandbox/tests/test_cte_vacuity.py, docs/decisions.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: pending
