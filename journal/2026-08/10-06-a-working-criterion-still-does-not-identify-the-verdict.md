# A working ESS criterion still does not identify the verdict — census 0/6

- **Cycle**: 2026-08-10 06:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — record convoy `w = 75`'s clearance ladder and take its `verdict_identification`
- **Phase**: P3
- **Status**: keep

## What I tried

- Walked convoy `w = 75`'s own `w_geom` ladder — `{1, 2.5, 5, 10, 20, 40}` × 16
  seeds at the rung's λ = 0.8, re-taking the risk/stock ESS targets on that same
  ensemble rather than quoting the 32-seed walk's (128 runs, ~4 min).
- Wired the measured ladder into `CONVOY_W75_NULL` and read
  `verdict_identification`, the question D-169 shipped and never asked here.
- Added the sharper `matched_ladder` / `matched_verdict_identification` /
  `better_matched` so the reading survives the obvious objection about which
  ladder rungs get counted.

## What worked / what failed

- 🔴 **The finding, and it is stronger than D-169's.** On convoy the ESS
  criterion **works** — median ESS 97.52 → 14.03, a response of **86.6%** of
  the target against head_on's 1.70%, so `coefficient_identification` reads
  `IDENTIFIED` and D-169's "the sampler is blind to `w_geom` on this scene"
  escape hatch does not apply. The verdict flips across it anyway:
  `REPRESENTATION_ADDS` at `w_geom ∈ {1, 2.5}`, `GEOMETRY_SUFFICES` at
  `{5, 10, 20, 40}`, with `residual_share` running **0.3302 → 1.0041**. So the
  defect is not scene-specific blindness. **ESS-matching identifies a
  coefficient and does not thereby identify a verdict** — two different
  properties, and convoy has the first without the second.
- 🟢 **The "you counted rungs the criterion would never pick" objection is
  closed by measurement, not prose.** `matched_ladder` keeps only rungs that
  are ladder-admissible *and* match the ESS target at least as well as the
  shipped 2.5 → `{1, 2.5, 5}`. The verdict still splits inside it, because the
  rung that flips it, `w_geom = 5`, is **16/16 in band** and a *better* ESS
  match than the coefficient the published reading was taken at
  (|94.41−96.36| = **1.95** vs |86.08−96.36| = **10.28**). No far-out rung is
  cited at all.
- 🔴 **A separate defect fell out: the calibration did not pick its own
  criterion's optimum.** `better_matched = (1.0, 5.0)` — two coefficients match
  strictly better than the shipped 2.5, and the best of them says the opposite
  thing. Invisible from the shipped `w_geom` alone, so it is a property now.
- 🔴 **Consequence: the attribution census is empty.** Both walked rungs are
  refused → `NO_GRADED_RUNG`, coverage **0/6**. D-167's `residual_share =
  0.7725`, the branch's most-quoted attribution figure, is no longer a reading
  the census will quote. This is an empty denominator, **not** a tie and not a
  null result about the mechanism (D-107's shape).
- 🟢 **The ladder cross-checks against both recorded walks exactly**: its
  `w_geom = 2.5` rung is the first 16 seeds of the 32-seed `NULL_CLEARANCES`
  and its `5.0` rung is the first 16 of the refused `LOUDER_NULL`, bit for bit.
  So this ladder and those walks are one measurement seen at two seed counts,
  not two that happen to agree.
- 🟢 Unlike head_on's 16/16-everywhere ladder, convoy's **loses seeds as it
  climbs** (15/16 at `w_geom = 10`, 8/16 at 40) — the same sampler response
  `coefficient_identification` reads, seen in the band instead of the median,
  and an independent sign the criterion is live here.
- 🟡 Three shipped tests pinned the pre-measurement census (1/6, `SINGLE_RUNG`,
  head_on as the sole unidentified rung) and were rewritten to the measured
  reading; none was loosened. Two rules that had been resting on convoy's
  `UNRECORDED` state (`SINGLE_RUNG`, "unrecorded does not refuse") moved to
  synthetic witnesses — a witness that exists only while some real rung stays
  unmeasured disappears the moment the project does its job.

## North-star delta

- **Negative, and the honest direction.** Zero controller/representation code;
  headline unmoved at `unsafe_rate` **0.0000** / `min_clearance` **0.3579** /
  `success_rate` **1.0000**. What moved is the confidence interval on the
  branch's central claim: attribution coverage went **1/6 → 0/6**, so the
  project now has *no* rung at which the clearance gain is demonstrably owed to
  the representation.
- What is bought for that: the failure is now localised to the **calibration
  criterion** rather than to the mechanism. Nothing here says the
  representation does not add — it says ESS-matching cannot be the instrument
  that decides, on either scene tested, including the one where it responds.

## Key learnings

- **A criterion that identifies its parameter can still fail to identify the
  answer.** D-169 measured the first failure and named it blindness; that
  diagnosis predicted convoy would survive. It did not, so the general form is
  the true one and the next criterion has to be validated against *verdict*
  stability, not against parameter response.
- **Restricting to the criterion's own preferred candidates is the honest way
  to report a refusal.** Had the whole ladder been quoted, the result would
  have been rebuttable in one line. Measuring `matched_ladder` cost ~15 lines
  and makes it not.
- **The most-quoted number was again the fragile one** — third cycle running
  (D-168's 0.0485, D-169's, now D-167's 0.7725). The pattern is specific: every
  figure that dissolved was taken at a coefficient or threshold nobody had
  shown the answer to be insensitive to.

## Recommended next 1–3 priorities

1. **Replace ESS-matching with a criterion validated on verdict stability** —
   match the null's across-rollout cost spread or its achieved clearance gain,
   and require the picked coefficient's verdict to hold over its own
   neighbourhood before publishing it. This now blocks every rung, not just
   future ones.
2. **Decide whether attribution is answerable at all with a scalar-coefficient
   null** — if no coefficient choice is defensible, the ablation may need to be
   structural (remove the representation's *input*, not scale its weight).
3. **Make `sandbox:pass=N` state which quantity it is** — `passed` vs
   `executed`. Carried eight cycles.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: `eval/mppi_sandbox/geometric_null.py`, `eval/mppi_sandbox/tests/test_geometric_null.py`, `docs/decisions.md`
- TSV row appended: pending
