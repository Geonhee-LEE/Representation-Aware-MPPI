# The aggregator runs before the receipt, not between it and the push

- **Cycle**: 2026-08-14 14:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `Q-149-cloud` Re-read D-257's band with an MPPI-like rollout cloud
- **Phase**: P3
- **Status**: keep

## What I tried

- Phase 1's `cycle_artifacts stranded` came back rc=1 naming 13:00's journal:
  five commits (D-258's `rollout_cloud.py`, the `loop_reach` registration, the
  TSV row, the 4a journal) sitting local with `origin` unmoved. Per D-112 that
  outranks the decision tree, so this cycle's entire scope is publishing them —
  no new reading, no new instrument.
- Started the receipt suite as the first act, then **killed it** two minutes in
  once `cycle_wallclock elapsed` priced the suite at ~1223 s: the plan it was
  serving needed *two* runs (one to source a pass count for the TSV row, one to
  license the tree that row had just moved), and two runs do not fit 35 min.
- Re-ordered instead: journal, `D-259`, and the TSV row all written **before**
  the single receipt, with the row carrying a `qual:` metric so no count has to
  be typed ahead of the run that would verify it.

## What worked / what failed

- **The strand's cause was ordering, not a broken gate.** 11:00 registered a new
  reader, which withdrew the `inert_surface` exemptions on `RESULTS.md`,
  `STATE.md`, `JOURNAL.md`, `journal/` and `results/` (`pins` still reads
  `PINS_STALE` on all five). 13:00 then followed the push chain literally —
  `aggregate_results.sh` sits between the receipt and the push — and that
  aggregator write was material drift on a withdrawn pin, so `push_preflight`
  refused `STALE`. The gate was correct; the template's step order is what is
  unsafe while exemptions are down.
- **The count-in-the-row requirement is what forces the second suite.** A row
  quoting `sandbox:pass=<n>` cannot be written before the run that produces
  `<n>`, and writing it after the run drifts `results/`. With exemptions
  withdrawn those are the only two options, and both cost a run. A `qual:`
  metric breaks the circle for a cycle whose deliverable is a push rather than a
  measurement — this cycle's north-star claim is D-258's, already measured.
- **Killing a running suite was the right call and felt like the wrong one.**
  2m08 of a ~20m run was thrown away to avoid a ~20m second run. 13:00 died at
  41m46 against a 35m budget doing the version of this that did not cut.

## North-star delta

- **No new reading.** D-258's numbers are unchanged; this cycle moves them from
  a local branch to `origin`, where CI and the user can see them. That is the
  whole delta and it is a publication delta, not a research one.
- Four cycles of instrument work (D-255…D-258) become reviewable in one PR
  rather than sitting on a disk that only this machine reads.

## Key learnings

- **A protocol step's safety can depend on state the protocol does not check.**
  `aggregate_results.sh` before `push_preflight` is harmless with pins current
  and fatal with pins withdrawn. The step order that is safe in both states —
  aggregator first, receipt last, nothing between receipt and push — costs
  nothing when exemptions hold, so it should be the unconditional order (D-259).
- **`qual:` metrics are the escape hatch from the count/drift circularity**, and
  they are honest precisely when the cycle measured nothing new. Reaching for
  `sandbox:pass=` on a cycle whose product is a push would be borrowing another
  cycle's number.
- Withdrawn exemptions are a *standing* tax on this branch, not a one-cycle
  event. Every cycle here pays it until someone spends the probe budget, and
  `STATE.md` alone was measured at 27 readers / >900 s.

## Recommended next 1–3 priorities

1. Re-place Q-148's both-on cell against D-258's **rollout** root (`0.7475`,
   headroom ~1.34×) instead of the superseded grid root (`0.3587`, 2.79×). Cheap,
   no sim, and the standing research bottleneck.
2. Decide whether to pay the `inert_surface probe`/`shard` budget on this branch
   or keep paying the per-cycle ordering tax.
3. Q-148's four-arm A/B stays blocked on PR #68 (occlusion scene) — sixth cycle.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: journal/2026-08/14-14-the-aggregator-runs-before-the-receipt.md, docs/decisions.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: pending
