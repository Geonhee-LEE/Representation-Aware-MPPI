# D-363's spread separation inverts at seed width — and its unexcited endpoint has 2 arms, not 8

- **Cycle**: 2026-08-19 20:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `state-1-seed-axis` Give `excursion_tracking.measure()` a seed axis
- **Phase**: P3
- **Status**: keep

## What I tried

- STATE #1 asked for a seed axis on `excursion_tracking`. D-369 had already
  confirmed no cross-track seed data exists on disk, so this was the first
  cycle in five that could not be paid at zero rollouts. Priced it before
  scoping around it (`clearance_census`'s own lesson): **116.8 s for 128
  rollouts**, not the 448 the full column costs.
- Widened only the **binding pair** — `cafe_convoy_v0` supplies
  `SPREAD_SEPARATES`'s excited minimum `0.1441`, `city_curved_v0` its unexcited
  maximum `0.0730`. No third scene can move a min-vs-max claim without first
  crossing one of those two, so two scenes suffice to *refute* and are openly
  insufficient to *re-derive*.
- New module `excursion_seed_width.py` + 21 tests; one `loop_reach.READING` row
  for the rectangularity claim.

## What worked / what failed

- **Seed 0 reproduces `excursion_tracking.CENSUS`'s spread column to 4 dp on
  both scenes**, cell-by-cell against `cte_peak_vacuity.CTE_MAX_SEED0`. So this
  is D-363's measurement widened, not a different one — the join is checked,
  not asserted.
- **The unpaired seed-robust reading inverts.** Worst excited seed `0.0612`
  against widest unexcited seed `0.0730` — **`0.838x`**, and the gap is `0.0118`,
  an order of magnitude above rounding. D-363's "with no overlap" is a seed-0
  statement that seed width contradicts.
- **Paired by seed index it holds 8/8** (`p = 2^-8`), and I am not allowed to
  use that. D-367's own source, limit #3: common random numbers reduce the
  variance of an arm-vs-arm difference **on a shared seed** and say nothing
  about a **scene-vs-scene** contrast. Two scenes at seed `s` share an RNG seed
  but not the geometry it drives. So the verdict is a **downgrade** — `no
  overlap` → `unproven at seed width` — not a refutation and not a survival.
  This is the first time the branch has had to decline its own strongest number.
- **The finding I did not go looking for**: on `city_curved_v0`, **seven of
  eight arms emit bit-identical `cte_max` on all eight seeds**. The entire
  `0.0730` is `essps_mppi` against a seven-fold tie.

## North-star delta

- 물체회피/경로추종 grading surface: **one claim weakened, one sharpened.**
  `excursion_tracking` finding #2 — the statement that decides which scenes a
  `cte_rms_max` bar can discriminate in at all — no longer supports "no
  overlap". The standing user-blocked repairs are unaffected (both are on
  excited scenes), but the *argument* for them is now narrower.
- `cafe_convoy_v0` is the one scene this cycle leaves **barrable at seed
  width**: per-seed intersection `(0.0750, 0.1300)`, width `+0.0550`, and a bar
  at its midpoint verifiably cuts the population on all eight seeds (tested,
  not inferred).
- `city_curved_v0` is now measured **unbarrable at any value**: intersection
  width `-0.0392` — the per-seed ranges do not all overlap, so seed noise
  exceeds arm spread outright. That is exactly the hypothetical
  `excursion_tracking.SEED_SCOPE` raised in words ("could in principle be
  dwarfed by seed noise"), now a number.

## Key learnings

- **`effective_arms` is the statistic `spread` was standing in for.** A scene
  with 2 distinct arms is not a scene with a narrow spread — it is a scene with
  almost no population, and no bar placement can fix that. This re-reads
  `HIGH_LEVEL_LOW_SPREAD` on a mechanism instead of a symptom, and it predicts
  that *every* obstacle-free scene will collapse the same way, because an
  obstacle-free scene gives seven of eight cost channels nothing to bite on.
  Cheap to check on `city_figure8_v0` and `cafe_straight_v0`.
- **Widen a min-vs-max claim at its endpoints, not across its population.** The
  refutation cost 128 rollouts where the census costs 512. The asymmetry is
  structural: extremes can kill such a claim and cannot rebuild it.
- **D-367's imported caveat did real work one cycle later.** The rider was taken
  as a per-pair result and it came back as a *veto* on this cycle's most
  quotable number. A caveat that only ever confirms is not being used.
- **The five zero-rollout cycles were a run, not a rule.** D-369's grep is what
  made this one's price knowable in advance; "read what's on disk first"
  returned `nothing here` and that was still the cheapest possible answer.

## Recommended next 1–3 priorities

1. **Count `effective_arms` on the other six scenes** — zero rollouts for the
   three with seed-0 harvests already pinned, and it tests this cycle's
   prediction that obstacle-free ⇒ near-degenerate population.
2. **Re-state `excursion_tracking.SPREAD_SEPARATES` and `SEED_SCOPE`** to carry
   D-370's downgrade at the site of the claim, not only in a sibling module —
   the same "answer lives one module away from the question" gap D-368/D-369
   named twice.
3. **384 rollouts** remain to widen the other six scenes; only worth it if
   priority 1 leaves a corrected gap looking derivable.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/excursion_seed_width.py, eval/mppi_sandbox/tests/test_excursion_seed_width.py, eval/mppi_sandbox/loop_reach.py, docs/decisions.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: yes
