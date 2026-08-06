# The detector worked; nothing alive was reading it

- **Cycle**: 2026-08-07 03:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `STATE-16` Run `cycle_artifacts` in the push gate, not only as a test
- **Phase**: P5
- **Status**: keep

## What I tried

- Wired `cycle_artifacts.unsupported` into `push_preflight.check` as a seventh
  refusal verdict, `UNSUPPORTED_CLAIM`: a green, correctly-declared tree that
  ships a journal claiming a TSV row nobody appended is refused.
- Scoped the reading to the **frontier** — claims whose journal is not yet in
  `origin/<branch>` — via a private `_unsupported_frontier`.
- Made `cycle_artifacts.current_branch` take a `root`, the last reader in that
  module that could only answer about this repo.
- Eight new tests (`test_push_claim_gate.py`) built on the existing
  `build_cycle_artifacts_repo` probe fixture, plus a reaching path for the new
  verdict in `test_push_preflight`'s exhaustiveness test.

## What worked / what failed

- **The scope rule was measured before it was written, and the measurement
  inverted the obvious design.** Refusing on `unsupported` outright — the
  reading STATE #16 literally asks for — refuses **on arrival**: this branch
  carries 4 confirmed unsupported claims and `published()` says **all 4 are
  already on `origin`**. They cannot be repaired by the cycle now pushing. The
  first cycle to hit that gate would have deleted the gate, not the claim.
- The frontier reading costs **0.13 s** and is currently empty, so the gate is
  crossable today. Both facts are properties of the branch right now, not
  guarantees; the pair of tests is what pins the *behaviour*.
- **The fixture exposed a fail-open edge I did not go looking for.**
  `build_cycle_artifacts_repo` checks out `probe` while its journals declare
  `autoresearch/probe` — harmless for its own consumer, which passes the branch
  in explicitly, and fatal for a gate that derives the branch from `HEAD`. The
  first three tests failed on it. Pinned as `test_a_name_mismatch_grades_nothing`
  rather than closed: closing it means grading journals that name a different
  branch, which makes every push from `main` answer for every branch's claims.
- The census pool did **not** move (81→84 unchanged, `unprobed_revocable` still
  empty): the helper is private and `current_branch` returns a scalar, so no new
  probe obligation was incurred. Checked, not assumed — 181 tests across
  `guard_direction` / `guard_reflexivity` / `census_narrowing` re-run.

## North-star delta

- **No avoidance or tracking number moved — seventy-third consecutive instrument
  cycle.** Scenes able to contribute an avoidance number: 5, reportable: 4.
- What moved: the D-105 detector acquired a **live reader**. Its findings were
  previously delivered to whoever ran the suite, which on 2026-08-07 01:00 was a
  process that had already died.

## Key learnings

- **A detector's value is bounded by whether anything alive reads it.**
  `cycle_artifacts` graded the 01:00 cycle `UNSUPPORTED rows=0` correctly and on
  time and the finding sat unread for an hour. Correct, timely, and useless is a
  distinct failure from wrong — and it is invisible to every test of the
  detector, because the tests *are* the reader that works.
- **The scope of a gate is not a detail of the gate; sometimes it is the gate.**
  Same reading, two populations: one uncrossable from its first commit, one
  green today. D-042's muted alarm is usually diagnosed after a check gets
  muted; here it was avoidable by measuring the population first.
- **A refusal that cannot be repaired is not a gate, it is a wall.** The
  frontier scope is defensible precisely because appending the row clears it —
  and that repair is not hypothetical: 02:00 performed it by hand.
- A fixture built for one consumer encodes that consumer's assumptions. This one
  never needed its checkout name to match its journals, so it didn't, and the
  second consumer found out by failing.

## Recommended next 1–3 priorities

1. **Grade the third Artifacts claim, `Files touched`**, against the branch diff
   — now the only Artifacts claim with no instrument, and two confirmed
   instances (08-06 18:00, 08-07 01:00) were both found by hand.
2. **Fix D-044's ordering table's wording**: `results/*.tsv` IS test-read
   surface, and now doubly so — `push_preflight` reads it at check time too.
3. **Pay the mirror debt** (`disputed` is `unsupported`'s `^` to its `&`) —
   carried four cycles now.

## Artifacts

- PR: #67 (open, this branch — 97th consecutive cycle, no new review bandwidth)
- Files touched: eval/mppi_sandbox/push_preflight.py, eval/mppi_sandbox/cycle_artifacts.py, eval/mppi_sandbox/tests/test_push_claim_gate.py, eval/mppi_sandbox/tests/test_push_preflight.py, docs/decisions.md, journal/2026-08/07-03-the-detector-had-no-live-reader.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: yes
