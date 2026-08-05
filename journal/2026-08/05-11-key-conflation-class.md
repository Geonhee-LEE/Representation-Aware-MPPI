# D-080's bug was a class, not an incident — and the last bare-keyed scan is unfalsifiable on the shipped tree

- **Cycle**: 2026-08-05 11:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: 10:00 journal rec #2 — audit the package for other name-keyed scans
- **Phase**: P3
- **Status**: keep

## What I tried

- **Recovered the 10:00 crash first.** It committed `1f69128` and died before
  push / TSV / JOURNAL / STATE / cron-log. Pushed the commit, and the recovery
  turned up the real damage — see below.
- Built `eval/mppi_sandbox/key_conflation.py`: the collision **population**
  (which names could conflate at all), a **differential probe** (call a scan
  with two same-named registries, compare readings), and a **synthetic control**
  for the case the shipped tree cannot exercise.
- Chose measurement over an "is this scan qualified?" AST heuristic on purpose:
  that heuristic would itself be a name-keyed scan and would owe this module its
  own audit.

## What worked / what failed

- 🔴 **The 10:00 cycle pushed a red tree, and nobody had run the suite on it.**
  `1f69128` fails 3 tests — `851 passed, 3 failed`. All three are D-080's own
  uncounted census cost: guard pool 65 → **66** (`undeclared_unreachable`),
  `unwatched_exemptions` 4 → **5** (`DECLARED_DEF_TIME`), `exemption_masking`
  screened pairs 17 → **18**. Its journal *names the first two in prose* and
  never re-pinned the tests. D-043 mechanises re-taking a count; nothing
  mechanises **running the suite at all** when the cycle dies before Phase 4.
  Fixed all three pins here.
- ✅ **The blind spot is live, not theoretical**: **16 of 286** module-level
  constants have their bare name owned by ≥2 modules, across **43** collision
  pairs. `EXCLUDED_TESTS` was one of sixteen. D-080 read as a one-off; it is not.
- ✅ **D-080's repair holds under an independent probe** — `references` reads 17
  vs 1, `binding` reads `CALL_TIME` vs `DEF_TIME`. Asserted from outside the
  module it repaired, by the *definition* of the defect rather than the shape of
  the fix.
- 🔴 **The remaining bare-keyed scan cannot be convicted on the shipped tree.**
  `unresolved_reads` keys on the bare name by construction — an unresolved read
  has no owner to key on — so its "the resolved count is a lower bound" is a
  claim about a **name**, not a **registry**. But the package holds **zero**
  unresolved reads, so both readings are empty. `conflating()` is empty and one
  of its three inputs *was never actually asked*; `unprobed()` reports that
  separately and a test pins it **unrun**, not clean.
- 🔴 **My own wrong-direction control failed on the first draft.** The fixture
  carried only `self.REG` reads, so the keyed scan read 0/0 and graded
  `VACUOUS` — proving nothing, and leaving "broken fixture" and "broken scan"
  indistinguishable. Adding resolvable reads (a: 2, b: 1) made it
  `DISTINGUISHES`. D-079's rule cost real money inside the cycle that cites it.
- 🔴 **Census cost, twenty-third cycle — and it is zero because it is invisible.**
  `key_conflation`'s two population-shaped functions both narrow by **equality
  against a verdict string** (`== VERDICT_IDENTICAL`, `== VERDICT_VACUOUS`) —
  D-079's exact invisible spelling, reproduced one cycle later in a module
  written without reference to it. First cycle where the invisible spelling
  accounts for **all** of a module's guards rather than some.

## North-star delta

- **No avoidance or tracking number moved — forty-ninth consecutive instrument
  cycle.** Scenes able to contribute an avoidance number: **5**, reportable:
  **4** — unchanged. The 가려진-obstacle class still has exactly one working
  cost term (D-027).
- What moved: PR #67 goes from **red to green** (3 failures introduced by the
  10:00 crash, now fixed), and one published magnitude class — every count
  keyed on a bare name — has a live population attached to it (16/286) instead
  of an anecdote.

## Key learnings

- **A cycle that dies before Phase 4 can push a tree nobody ever tested.** D-043
  and D-044 police *when* the count is taken and assume a count exists. The
  07:00 and 10:00 crashes both pushed untested trees this day; the second one
  was actually broken. The cheap repair is a Phase-3 gate, not a wider registry.
- **Re-taking a count cannot catch a broken key.** D-078 taught "date the
  quote"; D-080's quote was fresh and wrong. The question that catches it is
  *what is this count keyed on*, and it has to be asked of the scan, not the number.
- **Identical-and-empty is not identical.** Naming that third verdict is most of
  this module's value: without it, `unresolved_reads` reads clean and the
  package would carry a known-unkeyable scan as audited.

## Recommended next 1–3 priorities

1. **Gate Phase 3 on a green suite before push** — a cycle that crashes after
   commit should not be able to leave a red branch. Two crashes in one day.
2. **Apply `reader_cost` to the other seven registries** (10:00 rec #1, still
   uncollected) — controls whose only readers are `SUBPROCESS` never run.
3. **Probe the other 15 collision names** — `SCANS` covers three scans over one
   pair; the population says 43 pairs exist.

## Artifacts

- PR: pending merge (`autoresearch/p3-epistemic-shadow-cost-critic`, PR #67)
- Files touched: `eval/mppi_sandbox/key_conflation.py` (new),
  `eval/mppi_sandbox/tests/test_key_conflation.py` (new),
  `eval/mppi_sandbox/tests/test_guard_reflexivity.py`,
  `eval/mppi_sandbox/tests/test_exemption_masking.py`, `docs/decisions.md`
- TSV row appended: yes
