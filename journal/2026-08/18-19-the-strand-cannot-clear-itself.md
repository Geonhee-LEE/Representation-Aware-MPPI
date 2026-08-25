# The strand cannot clear itself — a 1341s suite does not fit beside an inherited red receipt

- **Cycle**: 2026-08-18 19:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — discharge the 18:00 strand
- **Phase**: P3
- **Status**: in_progress  (strand NOT discharged — now spans two cycles)

## What I tried

- `cycle_artifacts stranded` fired at the top of REVIEW: 18:00's journal and two
  commits (`01167a7`, `157d562`) sit on disk, never pushed, because 18:00's
  receipt came back RED on eight pins. Per D-112 that outranks the decision
  tree, so this cycle took no new TODO.
- 18:00 had already enumerated all eight repairs and called them mechanical.
  The plan was therefore: apply eight known repairs, run one suite, push.
- Ran `test_guard_reflexivity.py` to confirm its two — **318s**, and that one
  file is 8% of the suite.

## What worked / what failed

- **Two of the eight are repaired**, and the mechanism is now read off the pool
  rather than inferred. `scene_separability.format_tail_grade` has
  `population_kind == DIFFERENCE` because its population is
  `{o: worst_tail_extension(o) for o in tail_extensions_by_observable()}` — a
  dict comprehension over a call, which is the same syntax a set difference
  wears — and `reading == SCALAR` because it is a formatter. It is therefore
  the **first `unmirrored_revocable` entrant with no direction to execute at
  all**: the six before it were guards whose collapse was masked
  (`undeclared_drift`) or working (`staged_declarations`, `unwatched_strandings`).
  Kept rather than exempted, per D-342 — an exemption would be a second
  statement of the formatter rule.
- **The other six are not repaired, and that is the cycle's real result.**
  `cycle_wallclock elapsed` read `SUITE_UNAFFORDABLE` at **10m08** — the 8m51
  suite deadline had already passed while the *diagnostic* for the remaining six
  was still running. That diagnostic (four files, `exemption_control` /
  `exemption_masking` / `extremum_reading` / `guard_direction`) had produced two
  `F`s out of ~30 tests at 23m33 and had still not finished.
- **So the strand is self-perpetuating, and the arithmetic is the reason.** The
  suite is 1341s = 22.4 min against a 35 min budget. A cycle that inherits a red
  receipt must spend budget *diagnosing* before it can repair, and diagnosis
  here is itself measured in suite-fractions (318s for one file). Diagnose +
  repair + re-measure does not fit. 18:00 deferred the verdict to "the next
  cycle in one shot"; this cycle **is** that next cycle, and one shot was not
  available.
- **Push refused again, and correctly** (D-082). No green receipt exists for
  this tree, and manufacturing one was never affordable.

## North-star delta

- **No planner movement, and none was possible** — the whole cycle was spent
  against verification machinery, not representation. Honest zero.
- What moved is negative and worth having: the branch now knows that its own
  guard suite has grown past the point where a red receipt is recoverable
  inside one cycle. That is a fact about the *harness*, not the hypothesis, and
  it will keep costing cycles until it is addressed.

## Key learnings

- **A strand check that cannot be cleared within budget is a strand generator.**
  D-112 correctly makes the strand the first obligation, but the obligation is
  only dischargeable if the verification it requires fits in the remaining
  budget. At 1341s it does not, so each inheriting cycle adds a journal to the
  pile it was told to clear — exactly the failure D-112 was written to stop,
  arriving through the front door.
- **Diagnosis is not free and was budgeted as if it were.** 18:00 diagnosed the
  eight in 40s by running node IDs it already knew. This cycle did not know
  them and had to rediscover them by running whole files — a ~30× difference
  that no phase budget accounts for. The enumeration in a red cycle's journal is
  therefore load-bearing state, and 18:00's was good; what was missing was the
  **node IDs**, without which the enumeration cannot be replayed cheaply.
- **`census_preempt` was clean throughout and stayed blind throughout.** All
  eight pins sit in its declared `UNCOVERED` gap. Second consecutive cycle where
  a clean census reading carried no information about the receipt — D-345's
  fifth census closed one gap and the remaining four are where the failures
  live.

## The six remaining pins — node IDs, so the next cycle does not re-pay for them

This section is Q-167's proposal executed once by hand, because the cycle that
would benefit is the next one and the debt was measured here.

Confirmed red, with IDs (recovered by `--co` + failure position in **90s**,
after the full run had been killed):

```
eval/mppi_sandbox/tests/test_exemption_control.py::test_this_module_gives_the_four_unwatched_lists_a_control_not_a_watcher
eval/mppi_sandbox/tests/test_exemption_masking.py::test_module_global_route_covers_the_rest
```

Repairs, per 18:00's enumeration: `TTC_FAMILY` into the controlled set; the
module-global route count 23 → 25.

**Not reached, so not confirmed**: `extremum_reading` ×2 and `guard_direction`
×2. The four-file run was killed by its own 900s timeout after 31 tests without
emitting a summary — it never got to those two files. 18:00 describes them as
two unregistered `min`/`max` sites in `ttc_family_has_the_heavier_tail` (sweep
verdict flips to `UNREGISTERED_SITES`), and the scalar pool moving 16 → 18 with
`format_tail_grade` entering `unprobeable_revocable`. The second of those is
consistent with what this cycle measured directly — `format_tail_grade` reads
`SCALAR` — so it is likely still red and its repair is the same one-line
pin bump applied here to `unmirrored_revocable`.

## Recommended next 1–3 priorities

1. **Discharge the strand with the node IDs above, not the files.** Repair the
   two confirmed, run `extremum_reading` + `guard_direction` alone to confirm
   the other four, then one suite. Budget the suite start before 8m51 — that
   is the whole margin, and it is why this cycle failed.
2. **Q: should a red-receipt journal be required to record failing node IDs?**
   The 40s-vs-30min gap says yes, and it is a one-line addition to the 4a
   template. File as a deliberation before it is built.
3. Carried from 18:00: apply the facing-end rule to the invisible class
   (`convoy` / `obstacle_crossing` have no facing end — ask what their negative
   margins would need for a gap to open). Zero rollout.

## Artifacts
- PR: **not pushed** — receipt red and unearnable this cycle; `b3ee087` local only
- Files touched: eval/mppi_sandbox/tests/test_guard_reflexivity.py, docs/decisions.md, docs/deliberations.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: pending
