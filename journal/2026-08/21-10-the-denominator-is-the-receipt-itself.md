# The denominator is the receipt itself — Q-177's blocking sub-question has a third answer

- **Cycle**: 2026-08-21 10:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — answer Q-177's blocking sub-question (`suite_coverage`'s denominator)
- **Phase**: P5
- **Status**: keep

## What I tried

- Ran Q-177's own "다음 action" literally: find where `suite_coverage`'s `4119`
  denominator comes from — stored in the receipt, or re-collected per call.
  Q-177 said that one line decides whether lean (c) is implementable at all.
- Two greps and one call, ~90 s total: `grep -rn "4119" --include=*.py eval/`,
  `grep -rn "collect_only\|--collect-only"`, then `suite_coverage.of()` on both
  a real full-suite count map and a synthetic 9-test one.
- Recorded the answer as D-401 and closed Q-177 `resolved → D-401` **without**
  executing any of its three options.

## What worked / what failed

- **The either/or was false.** `4119` is neither stored nor collected: it is
  `executed + skipped + deselected`, all three read out of *that receipt's own*
  `counts` dict by `of(counts)`. The literal `4119` does not exist anywhere in
  `eval/` (0 grep hits) — it is this receipt's `3954 + 164 + 1`. The only
  `--collect-only` in the package is inside `tests/test_suite_coverage.py:303`,
  a test, not a production path.
- **So lean (c) is unimplementable as written** — there is no `4119` to divide
  by. Called directly: the scoped receipt returns `9 executed, none left out` /
  `sandbox:pass=9/9` / grade `FULL`; the full receipt returns `3955 of 4119
  executed (96.0%)` / grade `PARTIAL`.
- **This is the other half of D-400's mechanism.** D-400 attributed the reversal
  to `check()` not reading the target list. That is half. The other half is that
  **coverage is self-referential**: narrowing the scope shrinks numerator and
  denominator together, so the ratio goes *up*. Making `check()` read the target
  list would not remove this property.
- What failed: nothing was executed toward closing the hole — deliberately. Both
  surviving options need a declared-suite population that does not exist, and
  buying one at minute 5 of a 35-minute budget is the census `+1` shape that put
  eight consecutive first-suites RED (D-399).

## North-star delta

- **No planner movement — 33rd consecutive cycle.** 0 rollouts, no controller,
  representation or dynamics code touched. Be plain about it: this is a
  verification-surface cycle, not a navigation one.
- It does retire a question that had been STATE's #1 for **four** cycles running,
  and retires it in the direction that *saves* the next cycle from re-deriving
  it — which is the specific waste STATE #1's repetition was evidence of.
- The 22-minute suite remains voluntary (D-400) and remains unpriced. This cycle
  re-priced the cheapest proposed fix and found it was not cheap.

## Key learnings

- **Run the blocking sub-question before re-litigating the options.** Q-177's
  lean ranked (c) over (a) on cost alone. Ninety seconds of grep showed the two
  cost the same, which re-orders the whole question — and no amount of further
  deliberation would have surfaced it.
- **A self-referential denominator is a distinct defect from an unread target
  list.** They co-occur here, and D-400 folded them into one attribution. Fixing
  the one D-400 named would have left the reversal standing.
- **"Where does this number come from" beats "what should this number be."**
  Three cycles of design pressure went onto a string (`0.2% of the declared
  suite`) whose denominator had never been checked for existence.

## Recommended next 1–3 priorities

1. **Re-choose between Q-177 (a) and (b) now that they are equally priced** —
   the tie-breaker is no longer cost but whether "a defence that depends on the
   reader" is acceptable (Q-176 rejected exactly that, and D-397 followed it).
2. **Guard the `*_raw` exemption risk (D-399)** — assert every `second_*_raw`
   helper appears in `scene_scoped_claims()` as `LOAD_BEARING`. Small, and it
   protects the D-399 defence from a later tidy-up.
3. **If (a) is chosen, price the declared-suite population first** — a pinned
   literal goes stale on every test added; a collect breaks `check()`'s
   network-free invariant. Neither is free, and that is now measured, not feared.

## Artifacts
- PR: #67 (already open — D-140: continuing on an open PR adds no review bandwidth)
- Files touched: docs/decisions.md, docs/deliberations.md, journal/2026-08/21-10-the-denominator-is-the-receipt-itself.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: yes
