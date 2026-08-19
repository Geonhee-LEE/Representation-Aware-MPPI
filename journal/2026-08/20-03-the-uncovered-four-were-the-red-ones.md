# The UNCOVERED four were the red ones — and the exposure D-050 predicted went live

- **Cycle**: 2026-08-20 03:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: strand discharge (D-112) — outranks the decision tree
- **Phase**: P3
- **Status**: keep

## What I tried

- Phase 1's `cycle_artifacts stranded` returned rc=1: 02:00's two commits
  (D-375, `tail_stability.py`) never reached origin, and the tree was **ungraded**.
  `push_preflight probe` then read that tree's receipt as `NOT_GREEN, failures=7`.
- Diagnosed the 7 rather than re-running the suite blind. All seven sit in the
  **four censuses `census_preempt` prints as "Not covered"** — `default_lam_sites`,
  `exemption_masking`, `predicate_depth`, and its own tally test. 02:00 ran the
  pre-empt, got `CLEAN` on all 5 it covers, repaired those 3, and shipped.
- Split the 7 into three kinds and repaired each differently: one real
  regression, one ordinary census growth, one precision bug in the check itself.

## What worked / what failed

- **The regression is the interesting one.** `provenance_depth_exposure()` went
  `()` → one entry. This is the repo's **first live exposure**, and D-050/D-052
  named in advance the edit that would cause it — "extract the duplicated
  registry behind a helper" — which is exactly what `tail_stability` did. A guard
  that reaches its registry one frame down is admitted by `_is_set_valued` and
  then classified `DERIVED`, so `bite`, `unwatched_exemptions` and **all of**
  `exemption_masking` skip it silently.
- **The prescribed repair failed twice before it cleared the exposure.** The
  docstring says name the registry at the call site and forbids widening the
  predicate. (a) passing `CENSUS` as an argument still read `DERIVED` —
  `_provenance` only grants `TYPED` when every callee is in `_SET_CALLS`, and a
  helper is not. (b) binding to a local first also failed — the detector follows
  the local back to its assignment. (c) a set-comprehension over `CENSUS` at the
  call site cleared it, because `.items()` is an `Attribute` call and never
  enters the `callees` tally.
- **And then (c) broke a different census by exactly the amount it fixed.**
  Making the guard `TYPED` was the point, and it gave `drift` **two** typed
  exemptions on the same constant. `exemption_masking.routes` keys on
  (guard, constant), so two exemptions collapse to one route: `typed` 27 vs
  `routes` 26, and the masking screen's own population pin went red. I only
  found this because the slow `test_exemption_masking` run finished — the fast
  derivations all looked clean.
- **The fourth spelling is the one that holds.** Written as a count comparison
  (`len(CENSUS[scene]) - len(saturated_by_midpoint(scene, CENSUS))`) the check is
  not an exemption at all, so `drift` keeps the single pair it should. All four
  censuses agree simultaneously: guards 130, typed 26 == routes 26, exposure `()`,
  drift `()`. One predicate, four spellings, four different census readings,
  identical behaviour — the sharpest instance of D-072's syntax result this
  branch has produced.
- **One of the seven was the check being wrong, not the tree.** `str(130) not in
  source` false-fired because the module's prose contains "cost 1305 s". The
  collision switched on the moment the tally reached 130. Replaced with a
  digit-boundary regex rather than rewording the prose, which would only re-arm
  it for the next tally.
- **What did not fail: 02:00's judgement.** It ran the pre-empt it had and did
  every repair that pre-empt asked for. The module was printing its own scope
  limit the whole time.

## North-star delta

- **No movement on either column, and none attempted.** 물체회피 and 경로추종
  numbers are untouched; the 512-rollout fork is exactly where D-375 left it.
  This cycle bought a *pushable* tree, not a measurement.
- The strand is discharged, which is the thing that was compounding: two cycles'
  finished work was sitting on disk and every further cycle added to the pile.

## Key learnings

- **A clean check and a clean tree are different claims** — D-317 paid 785 s for
  this and it recurred at full price. `census_preempt` prints `UNCOVERED` for a
  reason; D-318 wrote down "read that line" and this cycle is what ignoring it
  costs. The follow-up worth having is widening the pre-empt to the other four.
- **A predicted exposure is still a surprise when it lands.** D-050/D-052 wrote
  the trigger, the diagnosis, and the repair years of cycles in advance, and it
  *still* took four spellings to land, because two plausible readings of "name
  the registry at the call site" don't satisfy the predicate and the one that
  does breaks a neighbouring census. The docstring should say which shapes
  qualify, not just the principle.
- **When a guard false-fires, fix the guard, not the data it read.** Rewording
  the prose to dodge "1305" was the one-character-cheaper repair and it would
  have re-armed at the next tally that is a prefix of some number in the file.
- **Fast derivations are not a substitute for the slow test.** Every intermediate
  spelling was checked by re-deriving the census directly in seconds, and each
  time the census I checked was clean — the one I hadn't thought to check was
  the one that broke. This is the cycle's own bottleneck finding, one level in:
  a check whose scope is narrower than the surface you touched reads exactly
  like a clean one.

## Recommended next 1–3 priorities

1. **Widen `census_preempt` to the four it declares uncovered** — this cycle is
   the second time that gap cost a red suite. Highest-value infra move available.
2. **Price `s` — the 10-seed pilot on `cafe_convoy_v0`** (carried from D-375,
   unchanged): `n ≈ 8/(Δ/s)²` and the project has never measured `s`.
3. **Note the qualifying shapes in `_provenance`'s docstring** — "pass it as an
   argument" is listed as a repair and does not actually work.

## Artifacts

- PR: #67 (already open — D-140: continuing on an open PR adds nothing to the queue)
- Files touched: `eval/mppi_sandbox/tail_stability.py`, `eval/mppi_sandbox/tests/test_default_lam_sites.py`, `eval/mppi_sandbox/tests/test_census_preempt.py`, `eval/mppi_sandbox/tests/test_exemption_masking.py`, `docs/decisions.md`, `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV row appended: yes
