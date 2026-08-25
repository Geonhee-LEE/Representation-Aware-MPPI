# What the suite actually spends: 59% of it is the project checking itself

- **Cycle**: 2026-08-26 03:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `Q-203` derive which lam tests actually roll out (discharge + compare)
- **Phase**: P3
- **Status**: in_progress

## What I tried

- **D-112 Step 0 fired rc=1 and took the cycle.** Three commits from 02:00
  (`5010a3f`, `1d8be44`, `d580e0a`) sat finished-but-unpushed: the 02:00 receipt
  came back red on four censuses, the cycle repaired all four, verified them
  green individually in 15.60 s, and then correctly refused to push on a
  partial check. One full-suite receipt licenses all three commits; nothing
  needed re-deriving.
- **Ran `lam_rollout compare` on the sidecar 02:00 had already paid for.**
  STATE's next-actionable #2 called this "seconds, no suite" and it was — but
  the log lives at `/tmp/suite-receipt.json.log`, which this cycle's own receipt
  overwrites, so the first act was `cp` to `/tmp/lam-durations-0226-02.log`.
  A free reading that a later step destroys is not free; it is free *once*.
- Read the composition of the measured set rather than just its size, which is
  where the actual finding was hiding.

## What worked / what failed

- **The comparison refutes the instrument D-473 shipped one cycle earlier:
  `both=15 derived_only=69 measured_only=230`.** The static walk names 84
  tests; the measured set holds 245; they share 15. D-473's headline — "a
  static walk finds 84 tests" — is true only in the sense that the walk emits
  84 names. 82% of them are not in the expensive population, and the walk misses
  94% of it.
- **But the two instruments are not measuring the same thing, and that is the
  real finding.** `measured_rollout_tests` thresholds on **duration ≥ 1.0 s**,
  which is a proxy for "rolls out" and a poor one. The top measured entries are
  not rollouts at all: `test_guard_reflexivity::test_report_names_its_own_findings`
  at **304.40 s**, then five `test_exemption_masking` entries at 167–242 s. Those
  are meta-guards — the project checking its own checking. Near-disjointness is
  what you get when a static rollout walk is compared against a wall-clock
  threshold; it indicts the proxy, not only the walk.
- **Quantified, and this is the number worth carrying: 68 of the 249 measured
  tests are meta-guards, and they account for 2227.8 s of 3754.7 s — 59.3% of
  all measured test time.** Suite total is 3837.2 s of test time across 14
  worker `--durations` blocks, 1282 s wall at `-j16`. The suite's cost is
  dominated by self-verification machinery, not by MPPI.
- **So Q-203's plan had the marker on the wrong set.** The stated goal was to
  mark rollout tests `@pytest.mark.slow` so `-m "not slow"` separates table
  assertions from rollout assertions and makes the 8-controller install fit in
  one cycle. Marking the *derived* 84 would barely move the wall clock — most
  of them are cheap. Marking the *measured* set is what buys budget back, and
  59% of that saving comes from tests that have nothing to do with the north
  star.
- **No marker applied this cycle, deliberately.** `cycle_wallclock review`
  opened with the previous run at 40m58 against a 35-min budget and said cut
  scope. The discharge is the obligation; editing test files ahead of the one
  receipt that licenses three commits would risk a second red for a change that
  is not yet decided (which set gets the marker is now an open question, not a
  known answer).

## North-star delta

- **No movement on the metrics, and a cost finding that bears on all of them.**
  The P5 headline is still computed over 2/8 of the controller axis. P5 entry is
  2026-09-03 — eight days. The reason the axis has not widened is budget, and
  59.3% of the budget is now shown to be spent on guards about guards.
- Three commits' worth of finished work stopped being invisible: the strand is
  discharged, so `lam_rollout` and the four census repairs are on origin and in
  PR #67 rather than on one machine's disk.

## Key learnings

- **A free reading has an expiry.** The 02:00 sidecar was already paid for, but
  it sits at the exact path this cycle's receipt rewrites. STATE said "the log
  is already paid for"; it did not say "and the next receipt eats it". Copy
  first, read second — the ordering is one command and the alternative is
  re-buying 21 minutes.
- **Comparing two instruments tells you about the weaker one, and you do not
  know in advance which that is.** D-473 shipped the static walk as the answer
  and the duration reading as the free cross-check. The cross-check turned out
  to be the one measuring something else entirely — a ≥1 s threshold is a
  *cost* oracle, not a *rollout* oracle. Both readings are useful; they are just
  not answers to the same question, and `compare`'s three-way split silently
  presents them as if they were.
- **The expensive population was never the one under investigation.** Three
  cycles have been spent trying to enumerate the rollout cascade to make the
  install affordable. The install is unaffordable mostly because of
  `exemption_masking` and `guard_reflexivity`, which no rollout enumeration
  would ever have named.
- Confirming D-473's own closing note from the other direction: a clean pass
  with a stated scope is not a clean tree, and a *named* set with a plausible
  size is not the *relevant* set.

## Recommended next 1–3 priorities

1. **Answer Q-205 before marking anything** — decide whether `@pytest.mark.slow`
   keys on the measured-cost set (buys the wall clock back) or the derived
   rollout set (matches the marker's name). These are near-disjoint, so it is a
   real choice and not a naming detail.
2. **Then mark and measure** — apply the chosen marker and record what
   `-m "not slow"` actually costs. That number, not an estimate, is what says
   whether the 8-controller install fits in one cycle.
3. **Then install the 8-controller table** — premise measured (D-472), collision
   resolution chosen (D-471 (b)). D-457's 16+8 price is unconfirmed for a fifth
   cycle.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: journal/2026-08/26-03-what-the-suite-actually-spends.md, journal/2026-08/26-02-name-what-rolls-out.md, docs/deliberations.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: yes
