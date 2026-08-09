# The head_on verdict is a free parameter, not a reading

- **Cycle**: 2026-08-10 04:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — extend the `w_geom` ladder upward on `cafe_head_on_v0` `w = 75` until the sampler responds, then re-walk
- **Phase**: P3
- **Status**: keep

## What I tried

- Extended the `w_geom` ladder on `cafe_head_on_v0` `w = 75`, λ = 0.8 upward by
  20× — `{10, 20, 40, 80, 160}` on top of D-168's `{1, 2, 2.5, 4, 8}` — at 16
  seeds, re-taking the risk and stock ESS targets on the *same* ensemble rather
  than quoting them (112 runs).
- STATE's plan was: find the coefficient where median ESS finally responds,
  ESS-match there, re-walk 32 seeds. Both of its predicted outcomes assumed the
  null was too **quiet**.
- When the ladder still refused to respond, asked the other question instead:
  what would each candidate coefficient have **concluded**? Added
  `NullRung.clearance_ladder` / `ladder_verdicts` / `verdict_identification` and
  the `VERDICT_UNIDENTIFIED` refusal, plus `behavioural_response` as the
  companion to `ess_response`.

## What worked / what failed

- 🔴 **The ladder does not wake the sampler at any coefficient.** Median ESS
  over `w_geom ∈ [10, 160]`: 116.01 → 115.23 → 114.98 → 115.15 → 114.04, a span
  of **1.70%** of the risk arm's 115.90. Extended 20× past the old top rung, the
  reading barely moved off D-168's 0.19%. Neither of STATE's two branches
  happened — the third did.
- 🔴 **ESS and behaviour are decoupled by two orders of magnitude.** Across that
  same ladder mean clearance travels **0.2856 → 0.5099** (+79%), which is
  **1.40×** the mechanism's entire gain over stock on those seeds. The term was
  never quiet; the sampler's ESS is simply *blind* to it on this scene. So
  "matched on ESS" is not "matched in loudness", and D-167's calibration
  criterion is measuring something other than what it is used for.
- 🔴 **The consequence, and this cycle's finding: the verdict is a free
  parameter.** `residual_share` runs **0.0485 → 1.76** monotonically across
  coefficients the ESS criterion cannot tell apart, and the *verdict* with it —
  `REPRESENTATION_ADDS` at `w_geom ∈ {10, 20, 40}`, `GEOMETRY_WINS` at
  `{80, 160}`. Two **opposite** answers on one rung. D-168's `0.0485`, the
  number that read as a large win for the representation, is the extreme low end
  of a range the same protocol licenses all of.
- 🟢 **The ladder rungs are not refusable on the walk's grounds**: 16/16 reached
  and 16/16 in band at every one, recorded in
  `HEADON_W75_LADDER_ADMISSIBILITY`. The objection that retired the 32-seed
  `w_geom = 2.0` walk (seed 25 at ESS 134.15) does not reach these, so the
  verdict spread cannot be waved off as bad runs.
- 🟢 **`UNRECORDED` deliberately does not refuse.** Convoy's ladder was never
  asked this question, and a rule that refused it would retroactively ungrade
  the one rung the census has — `coefficient_identification`'s three-state
  convention, one property down. Pinned by its own test.
- 🟡 One existing test pinned `ess_response < 0.01`, the pre-extension reading.
  Rewritten to the measured 1.70% and **tightened in meaning**: the old bound
  was consistent with "the ladder was too short", this one is not.

## North-star delta

- **No movement, and the cycle argues one prior reading was over-credited.**
  Headline unchanged: `unsafe_rate` **0.0000** / `min_clearance` **0.3579** /
  `success_rate` **1.0000**. No new controller or representation code — the
  `geometric_mppi` arm is D-167's.
- What it removes is a claim: head_on's `residual_share = 0.0485` is no longer
  available as evidence in either direction, and the census stays `SINGLE_RUNG`
  at **1/6** for a reason that no number of extra seeds can fix.
- What it adds is an instrument that applies to the *rest* of the census —
  convoy's `0.7725` now has a named, testable way of being wrong that nobody has
  yet checked.

## Key learnings

- **A calibration criterion has to be shown sensitive to the thing it is
  calibrating.** ESS-matching was adopted because it is stricter than
  cost-ratio matching; on this scene it is not a match criterion at all. The
  diagnostic that catches this is cheap — record what the ladder does to
  *behaviour* alongside what it does to ESS — and was not being taken.
- **`FLAT` was being read as a caveat when it is a question.** A flat ladder is
  harmless if every coefficient on it yields the same verdict and fatal if they
  disagree; nothing in the module could tell those apart until now. That is why
  the new state refuses the rung rather than annotating it.
- **The convenient number was the fragile one.** `residual_share = 0.0485` was
  the branch's best-looking figure on this scene and it is the one that
  dissolved. Worth remembering next time a favourable reading arrives from an
  uncalibrated knob.
- The same check should be run on convoy before its `0.7725` is quoted again —
  convoy's ESS ladder *did* respond, so it may well survive, but "may well" is
  the state head_on was in yesterday.

## Recommended next 1–3 priorities

1. **Record convoy `w = 75`'s clearance ladder and take its
   `verdict_identification`** — the one graded rung in the census rests on a
   coefficient whose verdict-stability is now `UNRECORDED`. Same 16-seed shape
   as this cycle, ~5 min of runs, and it either hardens D-167's headline or
   retires it.
2. **Replace ESS-matching with a criterion that is behaviourally sensitive** —
   e.g. match the null's cost-term spread across rollouts, or match achieved
   clearance gain, and state which quantity the match is in.
3. **Make `sandbox:pass=N` state which quantity it is** — `passed` vs
   `executed`. Carried seven cycles.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic, PR #67)
- Files touched: `eval/mppi_sandbox/geometric_null.py`,
  `eval/mppi_sandbox/tests/test_geometric_null.py`,
  `eval/mppi_sandbox/loop_reach.py`, `docs/decisions.md`
- TSV row appended: pending
