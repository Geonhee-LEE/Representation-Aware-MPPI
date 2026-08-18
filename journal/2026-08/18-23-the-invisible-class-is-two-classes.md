# The invisible class is two classes: same blindness, opposite planners

- **Cycle**: 2026-08-18 23:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — rollout on the invisible class (`convoy`, `obstacle_crossing`)
- **Phase**: P3
- **Status**: keep

## What I tried

- First rollout in six cycles. D-346/D-347 grouped `convoy` and
  `obstacle_crossing` as the **invisible class**: evidence width 0 at both 8
  and 16 seeds, no facing end, so `facing_extension / margin` is undefined.
  Every recorded census read them with the epistemic channel switched **off**
  (`w_epist = 0.0`, the `ISOLATION` default), so nothing on disk says what the
  shadow-cost critic *does* there.
- Probed `risk_mppi` at `w_epist ∈ {0.0, 200.0}` (the on-rung `ab.py:604`
  already uses) × 8 seeds × 3 scenes, paired per seed. Construction copied from
  `scene_transfer.retake_scene` — same `OPERATING_LAM`, same `ISOLATION`, same
  4-dp rounding — so the `w_epist = 0.0` column is comparable to the recorded
  rows.
- `head_on` carried as the **control**: the one scene with a facing end, where
  D-347's coordinate is defined.
- 48 rollouts, **106.7 s**. Min-clearance only.

## What worked / what failed

- **The invisible class is not one class, and the split is total.**

  | scene | `w_epist=0` | `w_epist=200` | Δ | seeds improved |
  |---|---|---|---|---|
  | `convoy` | 0.3973 | 0.5829 | **+0.1856** | **8/8** |
  | `obstacle_crossing` | 0.0295 | 0.0295 | **+0.0000** | 0/8, **bit-identical 8/8** |
  | `head_on` (control) | 0.0067 | 0.0076 | +0.0009 | 4/8 |

- **`convoy` is the largest arm effect measured anywhere on this branch** —
  +46.7 % mean min-clearance, every seed improving, no seed regressing. Against
  a branch whose recorded separations live at the third decimal place, this is
  a different order of magnitude.
- **`obstacle_crossing` is exactly inert** — all eight seeds bit-identical at
  4 dp. Not "small", not "within noise": the critic changed no decision.
- The control behaves like neither: it moves, but with mixed sign (4/8), which
  is the shape a weak perturbation makes.
- **Failed**: no path-tracking number. `cte_rms` captured 0 rows on all six
  cells — `Scenario` does not expose `.path` the way the probe assumed. So this
  cycle measures 물체회피 only, and says nothing about 경로추종. The clearance
  gain on `convoy` is therefore **unpriced** — a +0.19 m gain bought with a
  cross-track blow-up would not be a win, and I did not measure it.

## North-star delta

- **First planner-facing evidence in six cycles**, and it is large: on one
  scene the epistemic channel buys +46.7 % clearance at 8/8 seeds.
- **A negative that constrains the switch**: observable-invisibility does *not*
  predict arm-inertness. `convoy` and `obstacle_crossing` are indistinguishable
  to every plan-time observable (D-333/D-346) *and* to the facing-end
  coordinate (D-347), yet respond to the same critic in maximally different
  ways. So D-333's switch question is not academic on `convoy` — it is where
  the most value sits, and the observables cannot see it.
- Zero movement on 경로추종: unmeasured, not confirmed-flat.

## Key learnings

- **The class was defined by what could not see it, not by what it does.**
  Six cycles of observable-side work grouped these two scenes together; one
  106.7 s rollout separates them completely. Cheap direct measurement of the
  *arm* was available the whole time and no cycle spent it.
- **Bit-identity is a mechanism claim, and it is testable.** `ShadowCostCritic`
  is additive over traversed σ, so exact inertness means the rollout cloud on
  `obstacle_crossing` traverses σ = 0 everywhere — the Q-017 horizon-visibility
  race, not a weight-tuning problem. Raising `w_epist` there cannot help; only
  changing where σ is non-zero can. **Hypothesis, not measured** — the σ field
  along those rollouts was not read.
- **`obstacle_crossing` and `head_on` are both near-collision scenes** (0.0295
  and 0.0067 m against a robot radius that makes these grazes). `convoy`, at
  0.40–0.58 m, is the only probed scene with real margin. The critic may
  simply have room to act there and none elsewhere — a competing explanation
  for the split that this cycle cannot separate from the σ-field one.
- Reading a critic at its **off** default and calling the result "the scene's
  behaviour" is the error underneath this. Every recorded census on these two
  scenes ran `w_epist = 0.0`.

## Recommended next 1–3 priorities

1. **Price the `convoy` gain on the path-tracking axis** — re-run the same 16
   cells with a working cross-track readout. A +0.19 m clearance gain is only a
   north-star win if 경로추종 does not pay for it; right now it is half a result.
2. **Read the σ field along `obstacle_crossing` rollouts** to decide between the
   two explanations for bit-inertness (σ ≡ 0 on the traversed set vs no margin
   to act in). Cheap — no new rollouts, the cloud is reconstructible.
3. **Re-take the invisible-class grouping** — D-346/D-347 treat these two as one
   population; the arm says otherwise. Whatever the census calls this class
   should be split or renamed before more work is scoped against it.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: journal/2026-08/18-23-the-invisible-class-is-two-classes.md, docs/decisions.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: yes
