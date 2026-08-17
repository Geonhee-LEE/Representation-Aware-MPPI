# The deficit is the arm, not the seed — and the ensemble that was "too expensive" took 98.8 s

- **Cycle**: 2026-08-17 18:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: Q-159 — is the `0.17 m` baseline deficit a seed-0 accident or an arm property?
- **Phase**: P3
- **Status**: keep

## What I tried

- Followed Q-159's *own* caveat before its recommendation: it leaned on option
  (c) (a two-arm pair, `~8 min`) because it priced option (a) (8 seeds × 8 arms)
  at `~32 min`, but its next-action line said to **measure the per-arm seconds
  first** because D-326's comparable estimate had been 15× long.
- Measured: one `retake` = **10.6–14.2 s**, not the `~4 min` the module docstring
  claimed. So I ran option (a) outright — the whole registry at seeds 0–7.
- Recorded the result as `SEED_ENSEMBLE` + `seed_grade()` / `SeedVerdict` in
  `clearance_census.py`, with 7 new tests; resolved Q-159, wrote D-328.

## What worked / what failed

- **The full ensemble took 98.8 s.** Q-159's `~32 min` was **19× long**. The
  compromise it leaned toward was never necessary — and the estimate was large
  enough to have changed the plan, which is the part that matters.
- **0/8 seeds, 5/5 arms.** No representation arm out-clears plain MPPI on even
  one seed. Every arm's *best* seed still loses (`best_gap < 0`), so this is now
  a claim about magnitude and sign-stability, not just the sign D-327 allowed.
- **Paired reading was load-bearing.** The baseline's own spread across seeds is
  `0.5152`–`0.6123` — wider than several of the gaps — so a mean-vs-mean
  comparison would have been noisier than the effect. Per-seed differencing
  removes the seed variation the two arms share.
- **One D-327 claim did not survive**: "best representation arm =
  `gap_gated_mppi`" is a **seed-0 artifact**. On 7 of 8 seeds it is
  `social_mppi`. The top of the ranking moves with the seed; the sign against
  the baseline does not.
- Two worst-seed values I typed into the D-328 table from the summary were
  wrong (`risk` −0.1917 vs actual −0.2131; `essps` −0.2965 vs −0.3054). Caught
  by re-deriving through `seed_grade` instead of trusting the typed table —
  same failure mode the 17:00 cycle logged, same fix.

## North-star delta

- The branch's central negative result is now **8-seed, whole-registry** rather
  than single-seed: representation work on this branch has not bought obstacle
  clearance anywhere in the ensemble. That is real movement — an honest,
  reproducible bound on the core hypothesis as implemented so far.
- The length confound is now refuted *within* a class rather than by a direction
  argument: `gap_gated_mppi` loses and `cbf_mppi` wins while both run the
  baseline's step class (813–1167), so episode length cannot separate either.
- Still **one scene, one operating point**. The next falsifier is `scene`, not
  `seed` — that axis is now the widest untested part of the claim.

## Key learnings

- **Price a run before scoping around its cost.** Three consecutive inherited
  estimates on this branch ran 15×, 19× and 20× long, and each was big enough to
  pick the plan. On this branch the honest answer has always been seconds.
- **A cheap measurement can promote a hedged claim instead of just confirming
  it.** I expected to confirm D-327's sign; the ensemble also upgraded the claim
  to a magnitude and killed one of its sub-claims.
- **`cbf_mppi` remains the real bar.** It beats plain MPPI 8/8 by `+0.228 m`
  mean while being a *constraint* method. Comparing representation arms to
  `risk_mppi` was measuring against the wrong control for many cycles.

## Recommended next 1–3 priorities

1. **Widen the census to a second scene** — the seed axis is now closed and the
   scene axis is the claim's widest untested edge. Cost is now known to be ~100 s
   per scene, so this fits a cycle easily.
2. **Read `cbf_mppi`'s cost/constraint path against `risk_mppi`'s** — STATE's
   standing bottleneck, now sharper: the win is 8/8 and within-class, so it is a
   mechanism question, not a noise question.
3. **Human merge** — 6 PRs, 36 days since the last merge; #68 also unblocks
   `transfers_to_ab_scene`.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/clearance_census.py, eval/mppi_sandbox/tests/test_clearance_census.py, docs/decisions.md, docs/deliberations.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: pending
