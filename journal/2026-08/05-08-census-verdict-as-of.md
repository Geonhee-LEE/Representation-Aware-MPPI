# D-077's prose was measured one write too early, and the repair is a spelling

- **Cycle**: 2026-08-05 08:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: resume in-flight (decision tree step 1) — the 07:00 cycle crashed after commit
- **Phase**: P3
- **Status**: keep

## What I tried

- Found the 07:00 cycle (D-077) **committed but never pushed**: no TSV row, no
  `JOURNAL.md`, no `STATE.md`, and a journal claiming *TSV row appended: yes*.
  Resumed per decision-tree step 1.
- Before finishing its bookkeeping, checked whether its numbers were right — the
  commit message said **"5 in 19"** and the entry prose said **"18 중 5"**. Built
  `magnitude_census.as_of(decision)` to settle it by measurement instead of by
  picking.
- Asked why the branch's own drift detector did not catch it, and found the
  answer was not "nobody registered it" but "the registry has no vocabulary for
  it".
- Shipped the repair as a canonical spelling plus `quoted()` / `drifted()`, with
  a vacuity check and a negative control in the same cycle.

## What worked / what failed

- 🔴 **The diagnosis is an equality, not a story.** `as_of("D-076")` returns
  **exactly** `18 printing / 12 uncovered / 76 decisions` — the three numbers
  D-077's prose carries. The difference between prose and test is precisely one
  write: D-077's own entry. That rules out a typo and rules in the D-043
  write-ordering defect, **inside the entry that cites D-043 and states it
  re-took the count after 4a-bis**. It did re-take the count; the *test* has
  19/77/13. Re-running the suite moves the pytest number and moves nothing in
  the prose beside it, and D-043/D-044's ordering table mechanises only the
  former.
- 🔴 **`citation_audit` could not have caught this, and not by oversight.** It
  scans `docs/decisions.md` for exactly this failure, but only for the six
  claims in `MEASURED_CLAIMS` — and a census count **cannot join that registry
  as it stands**: every entry that cites it correctly cites a *different* number,
  because writing the entry changes the document being counted. A registry keyed
  on one magnitude per claim has no vocabulary for a time-indexed claim. This is
  a category gap, not a missing row.
- ✅ **So the repair is a spelling, not a seventh registry entry.**
  `N printing / M transcribed / K uncovered (T decisions)` is machine-checkable
  against `as_of` because it is indexed by the entry stating it; adding the index
  turns a moving magnitude back into a fixed claim. D-077 rewritten in it;
  `drifted()` is `()`.
- ✅ **Vacuity blocked in the same cycle that created the guard.** `drifted() ==
  ()` passes vacuously if nobody uses the spelling — D-076's 0-of-22 finding
  exactly. So the bite is asserted separately (`quoted()` non-empty, D-077
  present) **and** a negative control tampers D-077's quote back to the stale
  triple and asserts the guard catches exactly 1. First guard on this branch
  shipped with both.
- ✅ **Removed D-077's forcing function without losing it.** D-077 hard-pinned
  `decisions == 77` and predicted D-078 would break it *by design*. It did. But a
  test that requires re-typing a number every cycle is how the stale triple
  survived in the first place, so the total is now read as-of the newest entry
  while the counts the verdict rests on stay hard-pinned. Same protection, no
  per-cycle re-typing.
- 🔴 **D-077's own pass count is unrecoverable.** Its tree is gone — I edited it
  before a clean run existed. The 829 I measured straddles my first doc edits and
  is a reading of neither tree. Stated, not quoted.

## North-star delta

- **No avoidance or tracking number moved — forty-sixth consecutive instrument
  cycle.** Scenes able to contribute an avoidance number: 5, reportable: 4 —
  unchanged. Zero new runs, zero sim time.
- What moved: a published entry on this branch disagreed with its own test, and
  now does not; and the class of claim that made it invisible has a guard.

## Key learnings

- **Re-taking a count and re-taking the prose are different acts.** D-043/D-044
  mechanise the first and the branch has been reading that as covering both for
  thirty-odd cycles. The pytest number is re-taken by a command; every other
  magnitude in the entry is re-taken by remembering to.
- **A drift registry that assumes one magnitude per claim cannot police a claim
  about the record itself.** Self-referential counts are time-indexed, and the
  cheap fix is to write the index down rather than to widen the registry.
- **A guard and its negative control belong in the same commit.** D-076 spent a
  cycle discovering a filter that had never removed anything; that is avoidable
  at near-zero cost by tampering the input once and asserting the guard fires.
- **The crash was the useful part.** Had 07:00 pushed cleanly, the stale triple
  would have shipped and the next cycle would have read 18 as the population.

## Recommended next 1–3 priorities

1. **Apply the negative-control pattern to the other typed exemption sets**
   (`CARRIED_FIELDS`, `EXCLUDED_TESTS`, `NAME_SCOPE_CLAIMS`, `SCOPED_CLAIMS`,
   `DEGENERATE_READINGS`, `TEMPERATURE_RELEVANT`) — D-076 measured bite for one
   set; a tamper test per set is cheap and generalises it.
2. **Read D-067's 14 novel magnitudes** — still the last uncovered candidate
   clean under every spelling. Either `PUBLISHED` is missing a third reading or
   it is not, and either answer shrinks the 13.
3. **Widen `quoted()` beyond the canonical spelling, or declare it won't be.**
   D-077's title states the verdict in prose that is not policed; the honest
   options are a parser or a written-down limit.

## Artifacts

- PR: #67 (existing — 73rd consecutive cycle writing into it, no new review bandwidth)
- Files touched: `eval/mppi_sandbox/magnitude_census.py`,
  `eval/mppi_sandbox/tests/test_magnitude_census.py`, `docs/decisions.md`,
  `journal/2026-08/05-07-published-magnitude-census.md` (correction block)
- TSV row appended: yes — including the row the 07:00 cycle never wrote
