# The escape hatch is not graded — Q-196's lean priced, and its cheap option refuted

- **Cycle**: 2026-08-24 07:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `3c5c5d39` Q-196 — 광고/무대 격차를 P5 metric set 이 상속해도 되는가
- **Phase**: P3 (P5 entry 2026-09-03, 10 days out)
- **Status**: keep

## What I tried

- Took Q-196 (STATE next-actionable #1) and, before implementing its lean (b)
  — "make a new `cafe_obstacle_contested_v0` yaml" — **counted the consumers**,
  which is the discipline D-451/D-453 established and which STATE names as this
  branch's cheapest repeated win.
- Derived the `eval/scenarios/*.yaml` population's reader set by grep rather
  than trusting the prose that describes it.
- Checked where the four existing crossing variants live and **why**, then
  checked whether that placement satisfies what Q-196 actually asks for.
- Zero source lines, zero sim, zero re-measurement.

## What worked / what failed

- **The lean's price tag was wrong by an order of magnitude.** Q-196 costed (b)
  at "matrix 가 한 칸 늘고 … 혼동 위험". Measured: **23 modules** glob that
  population (14 non-test source, 9 test), and at least four literals are
  pinned to its size — `len(shipped.scenes) == 8`, `reasons_recorded == 8`,
  `threshold_vacuity`'s `len(col) == 8`, `cte_peak_vacuity`'s `8 * 8 * 7` —
  plus `scene_census.SCENE_OBSTACLES`, which is *derived and compared*. So (b)
  is a **census cycle**, not a doc cycle.
- **The cheap escape hatch is refuted, and that is the sharper half.** All four
  crossing variants sit in `variants/` and say why: the parent dir is globbed
  and pinned. But `obstacle_reach.py:204/223` globs `eval/scenarios/` **only** —
  so a scene parked in `variants/` is **not graded**. Q-196's entire complaint
  is that the *graded* obstacle scene stages 2 actors. Placement there would
  cost nothing and answer nothing, while looking like Q-196 was closed. That is
  the most dangerous of the four alternatives and it is now written down as such.
- **The escape hatch's own documentation carried the D-451 defect.** Three
  variant yamls state the population is "pinned at exactly 8 by three test
  modules" — understated, in the same declaration-vs-reality shape D-451
  diagnosed in the parent scene. Fixed in all three **without hand-typing a
  replacement count**: the note now points at the derivation command and names
  the pin classes a grep will miss.
- Caught **before** a suite went red, unlike D-317/D-450/D-451. Cost: ~3 min of grep.

## North-star delta

- **Zero measured movement** — no rollout, no controller line, no metric
  re-taken. Honest: this is verification-surface work again, cycle ~39 without
  a rollout.
- What it does buy is directly north-star relevant: the "다중 · 가까운 · 가려진"
  obstacle classes remain untested, and this cycle establishes that the
  *cheap-looking* way to close that gap (`variants/`) would have left it open
  while appearing to close it. Ten days before P5 entry, that is the difference
  between a metric set built on a tested scene and one built on a label.

## Key learnings

- **"Where does the file go" is a population question, not a filing question.**
  The two candidate directories differ in *who reads them*, and only one is
  graded. Any future "just add a variant" reflex should first ask which globs
  see it.
- **A count written in prose decays, and the escape hatch is not exempt.** The
  "three test modules" line was itself the defect it was warning about. The
  repair is to point at the derivation, never to write a fresher number.
- **The counting discipline now pays before the suite, not after.** Four prior
  instances were diagnosed by a red suite; this one and D-453 were diagnosed by
  grep. That is the shape worth keeping.

## Recommended next 1–3 priorities

1. **Q-197 — decide whether to buy the census cycle before P5 entry
   (2026-09-03).** Lean (a), weakly. Before starting it, count how many of
   D-454's 23 consumers `census_preempt` actually covers — that decides 1 suite
   vs 2, and it is unmeasured.
2. **Derive the `key_discrimination` narrow-key census** (unchanged from prior
   STATE — red four times, in neither `census_preempt` list).
3. **Q-192 + Q-183 — delete one of option (c)'s two conflicting triggers.**

## Artifacts
- PR: pending merge (`autoresearch/p3-epistemic-shadow-cost-critic`, PR #67)
- Files touched: `docs/decisions.md`, `docs/deliberations.md`, `eval/scenarios/variants/cafe_obstacle_crossing_noflow_v0.yaml`, `eval/scenarios/variants/cafe_obstacle_crossing_sync_noflow_v0.yaml`, `eval/scenarios/variants/cafe_convoy_staggered_v0.yaml`
- TSV row appended: yes
