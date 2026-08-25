# The watcher was in the residue

- **Cycle**: 2026-08-11 08:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — triage the 11 `UNREACHED` module-level functions
- **Phase**: P5
- **Status**: keep

## What I tried

- Read all 11 `UNREACHED` bodies in one pass (AST extract) rather than walking
  them one per cycle, because the bottleneck's own framing — "each is a
  one-line delete-or-wire decision" — is only testable by looking at all of
  them together.
- Wired exactly one: `candidate_scope.stale_grades`, with three tests
  (`TestTheWatcherIsRun`), including the failing direction.
- Recorded the triage as two derived readings in `test_consumer_reach.py`
  instead of prose, and updated the ratchet pin 11 → 10.

## What worked / what failed

- 🔴 **The finding: `stale_grades` is `GRADED`'s watcher, and nothing called
  it.** It was written the moment `coverage` stopped counting `len(GRADED)`
  and started narrowing `RESIDUE` by membership — which turned `GRADED` into a
  typed allow-list. So for as long as it has existed, this package has carried
  an allow-list whose watcher never ran. That is the exact defect
  `guard_reflexivity` counts and D-189 replaced with a rule, and it was sitting
  *inside* the residue the last cycle bounded. The fix for a watcher is neither
  delete nor rewrite — it is to **run** it.
- 🟢 The watcher is pinned in both directions. A watcher asserted only on the
  clean case is one nobody has shown can fail (D-058), so
  `stale_grades(residue=())` and a shrunk-residue case pin the direction it
  was written to detect.
- 🔴 **"Delete or wire" was the wrong frame, and the residue is not one
  population.** `reading_record.take_and_record` is `# pragma: no cover` and
  states why — 2k concurrent five-minute suite runs — so the fast suite cannot
  reach it *by construction*. That is the `FRAMEWORK_DISPATCHED` shape, not
  dead code. D-191 split one verdict across two populations; the same split
  was owed one level down.
- 🟢 **Nine are deliberately left red.** `guard_vacuity.never_fired` and
  `predicate_vacuity.one_sided` are one-line accessors their module docstrings
  name as the reading's vocabulary; nothing calls them because consumers reach
  `cens.candidates` directly. Adding a call *to clear the instrument* would be
  D-189's shape-fitting. A test now fails if a future cycle gives one a caller
  without arguing for it.
- 🟢 The `# pragma: no cover` classification is read off source, not typed —
  a hand-kept "deliberately uncovered" list would be the fifth unwatched
  allow-list D-189 removed.

## North-star delta

- **No movement, and this cycle claims none.** No controller, representation,
  dynamics, or sim code. 0 sim runs. Census attribution coverage still
  **0/6**, `NO_GRADED_RUNG`.
- What moved is one live defect: an allow-list that was unwatched in practice
  is now watched on every suite run.

## Key learnings

- **A residue member can be the guard for another instrument.** Counting
  "functions with no caller" treats them as uniformly inert; one of them was
  the thing standing between `GRADED` and silent drift. Triage has to read
  *what the function is for*, and the count cannot.
- **Clearing an instrument is not the same as fixing what it measures.** Seven
  of the ten remaining could be made green in a minute by adding a call from a
  test. That would be shape-fitting, and D-189's lesson is that satisfying the
  measurement is the failure mode, not the fix.
- **The bottleneck's own pricing was wrong in the cheap direction again** —
  fifth cycle running. "11 one-line decisions" was really 1 genuine wire, 1
  structural non-defect, and 9 that need an argument rather than an edit.

## Recommended next 1–3 priorities

- Grade `take_and_record`'s kind in `consumer_reach` itself (a
  `DEFERRED_BY_COST` verdict keyed on the marker rule) so the residue count
  stops carrying a known non-defect.
- Decide the two documented accessors (`never_fired` / `one_sided`) on their
  merits: keep as vocabulary, or delete both and fold the docstrings into the
  module docs.
- Add the repo-wide instrument tests to the constitution's Phase-3 pre-check
  (5th time recommended; ran by hand again this cycle).

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: `eval/mppi_sandbox/tests/test_candidate_scope.py`, `eval/mppi_sandbox/tests/test_consumer_reach.py`
- TSV row appended: yes
