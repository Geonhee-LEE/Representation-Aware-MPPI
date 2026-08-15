# The five exemptions are blocked by the module that grants them

- **Cycle**: 2026-08-16 06:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `<reprobe-stale-pins>` Buy back the 5 withdrawn `inert_surface` exemptions
- **Phase**: P3
- **Status**: keep

## What I tried

- Took STATE's #1 item — seventeen cycles deferred, and last cycle promoted it
  from "tax" to "agenda-setter" because it dictated the whole write order.
- Priced the re-take properly instead of attempting it: `carried_drift` is a
  `git diff`, so pricing all five candidates costs milliseconds against the
  ~12 min a single probe pass costs.
- Every one of the five came back `PREMISE_DRIFTED` **by mediating module**,
  which is the branch of `PremiseDrift.rerun` that degrades to the *full*
  reader set. The cheap composed path (`reprobe` over entrants only) is not
  expensive here — it is unavailable.
- Shipped the distinction as a reading (`inert_surface blocker`, D-295) plus
  seven tests, so the eighteenth cycle does not re-derive it by hand.

## What worked / what failed

- **The blocker is `inert_surface` itself, in all five cases.** It is a
  mediating module of every candidate — the only module besides
  `citation_audit` that is — and it is the module the registry, the probe, the
  composition rule and this new reading all live in. So the tool sits inside
  its own read surface: every cycle that maintains the exemption machinery
  invalidates every exemption it grants, at once.
- **Measured, not asserted**: 23 of the last 40 commits touched
  `inert_surface.py`. Per pin, it accounts for 17/37, 10/15, 16/21, 17/32 and
  18/42 of the mediating-module drift since the base commit.
- **This is why seventeen deferrals were correct.** Each one looked like
  procrastination on a 12-minute bill. It was not: the bill buys a pin that the
  next edit to `inert_surface.py` withdraws again, and that edit has landed in
  58% of recent commits.
- **The guard obligation bit, and I cut scope rather than fake it.** The first
  take split the drifted modules against a typed `SELF_MEDIATING` registry
  inside the function, which made it a `DIFFERENCE` population with a `TYPED`
  exemption — a revocable collection guard.
  `guard_direction.unprobed_revocable()` correctly demanded an executed probe,
  and `test_guard_direction.py:50` asserts that set is empty, so the suite
  would have gone red. The fixture that obligation needs (a scratch repo
  carrying a pin whose mediating module has moved) did not fit the budget, so
  the split moved to a property of the returned reading and the function now
  carries `modules_drifted` through unfiltered.
- **The seconds-scale pre-check paid for itself again.** `gd.unprobed_revocable()`
  is a 2-second call and it caught this before the suite — the exact lesson the
  03:00 cycle wrote down after spending 12 minutes discovering the same class of
  failure.

## North-star delta

- **No movement.** No obstacle, clearance, CTE or near-miss number changed;
  still one scene, still `transfers_to_ab_scene = False`. This is infrastructure.
- What it buys is cycle throughput, which is the thing actually rate-limiting
  the science: the last four cycles ran 44, 88, 45 and ~95 minutes against a
  35-minute budget, and the overrun was *entirely* pin tax in three of them.
- Converts a recurring 12-minute-bill deliberation into a one-line reading.

## Key learnings

- **A guard inside its own read surface has no fixed point.** The composed
  re-take (D-206) was built to make pins cheap to refresh; it cannot fire for
  these five, because the module implementing it is what drifts. Cost was never
  the binding constraint — self-reference was, and pricing alone could not see
  the difference.
- **"Expensive" and "unavailable" call for opposite decisions**, and
  `PREMISE_DRIFTED` spells them identically. Foreign churn is worth re-taking;
  self-inflicted churn buys a pin that does not survive the next cycle.
- **Do not launder a probe obligation.** The tempting fix was to make the
  reading scalar so `unprobeable_revocable` would excuse it. That is exactly the
  laundering D-045/D-047 name as the defect; declining to incur the obligation
  is honest, dodging it after incurring it is not.
- The real question this raises is not "when do we pay?" but **"should these
  five candidates be pinned at all?"** — filed as Q-160.

## Recommended next 1–3 priorities

1. Answer Q-160: retire the pins for self-blocked candidates and let the D-044
   write-ordering trick be the standing mechanism, rather than a workaround.
2. Register the `reprobe_block` probe properly and move the `SELF_MEDIATING`
   split back into the function — one change, once the fixture exists.
3. `<locate-the-k-endpoints>` — bisect `(64, 96)` or `(128, 256)`, ~16 runs,
   turns the bracket into a located endpoint. The science item.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/inert_surface.py, eval/mppi_sandbox/tests/test_reprobe_blocker.py, docs/decisions.md, docs/deliberations.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: pending
