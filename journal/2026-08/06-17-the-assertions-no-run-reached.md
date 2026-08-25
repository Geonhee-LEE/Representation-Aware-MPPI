# The number was in the log the whole time — and the filter would have hidden the finding

- **Cycle**: 2026-08-06 17:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `STATE-next-1` Sweep the other assertions this branch promoted from population
- **Phase**: P3
- **Status**: in_progress

## What I tried

- Took STATE #1 — the only next-priority with a demonstrated hit rate (two
  defects in two cycles, both found by *running*) — and asked it structurally
  instead of by reading, since reading is what installed both defects.
- Built `eval/mppi_sandbox/assert_reach.py`: for each row of
  `simd_attribution.CI_FAILURES`, pin the failing statement to an ordinal and
  report every `assert` **after** it — statements the job that was supposed to
  execute them never reached. Plus loop-body `assert`s (STATE #2), which sample
  a measured population rather than check it.
- Ran it against the known answer first. D-101's line is the one site whose
  verdict is known independently, so a scan that cannot recover it is measuring
  something else.

## What worked / what failed

- 🔴 **The first cut failed its own negative control.** Matching CI's printed
  assertion text by *operator shape* pinned **3 of 14** rows and missed D-101's
  own site — a function with three `==` assertions is genuinely not pinnable
  that way. Shipping it would have published "0 shielded assertions" as a
  finding.
- ✅ **The field it needed was in the job log, two lines below the text that was
  transcribed.** `CI_FAILURES` was built from `short test summary info`, which
  elides both operands and carries **no line number** — and "which assertions
  did the failure shield" is exactly a where-question. `gh run view --log-failed`
  still serves run `31042602721`; the traceback footers give `path.py:NNN` for
  all 8 assertion rows. Pinning went 3 → **8 of 14**.
- ✅ **The residue is not a matcher deficiency.** The 6 unpinned rows are exactly
  the `TIMEOUT`s — a test killed by the clock has no failing statement, so there
  is nothing for a later assertion to be shielded *by*. Every `ASSERTION` row
  pins, 8/8.
- 🔴 **The population-kind filter would have hidden the more interesting row.**
  I filtered the headline to subset / set-equality / cardinality claims because
  that is what D-100 and D-101 both were. The scan found **2** shielded
  assertions: D-101's `manufactured_candidates <= collateral` (SUBSET) and
  `shipped.understatement > audited.understatement` — an ordinary scalar
  comparison, graded `OTHER`, and it is the statement its own test's docstring
  calls **section 3's counterexample**. The test exists to refute "the
  understatement grows with the damage" and its refuting line has never once
  been evaluated. Filter removed; the kind is now an annotation nothing acts on.
- ✅ **Read at the run's commit, not at HEAD** — D-043 in a new place. D-101's
  repair *deleted* the shielded statement, so a HEAD reading makes the finding
  vanish. `MOVED_FILES` names the one file that moved; `moved()` re-checks that
  every recorded line still holds its recorded text, so a drifted ordinal is
  declared rather than fabricated.
- 🔴 Three of the eight transcribed keys were silently inert on first write —
  the log prints `file.py:NNN` without the enclosing class, so the ids did not
  match the census. A test now pins `set(FAILED_AT) <= census`.

## North-star delta

- **No avoidance or tracking number moved — sixty-ninth consecutive instrument
  cycle.** Scenes able to contribute an avoidance number: 5, reportable: 4.
- What moved: the unevaluated-claim population is now **measured at 2 sites**
  rather than discovered one accident at a time, and one of the two is new.

## Key learnings

- **Ask the known answer first.** The scan's first cut looked fine and returned
  a clean "nothing found". It was only the demand that it reproduce D-101 that
  exposed the matcher as too weak to see anything at all. An instrument's first
  test should be the case whose answer is already known.
- **A filter justified by the last two findings excludes the next one.**
  `POPULATION_KINDS` was derived honestly from D-100 and D-101 and would have
  dropped the scalar row — which is the load-bearing statement of its test. The
  *shape* of a claim is not its importance.
- **The hazard is real and rare, and the rarity is a result.** Six of the eight
  failures were their function's last assertion, so there was nothing behind
  them. Two shielded sites out of 14 rows is the honest size of this class — not
  the "sweep of many" STATE #1 implied.
- **Transcribing a reading drops the fields nobody has a question for yet.**
  The census was faithful to what it copied; the line number was simply not part
  of any question at the time. It cost a failed instrument to notice.

## Recommended next 1–3 priorities

1. **Evaluate the two shielded assertions** — neither has ever produced a
   reading. `shipped.understatement > audited.understatement` decides whether
   section 3's counterexample stands.
2. **Add the line number to the census contract**, so the next CI transcription
   carries it without a re-fetch of a possibly-expired log.
3. **Grade the 15 population-claim loop-body assertions** (STATE #2) — the scan
   counts them; nothing has read them.

## Artifacts
- PR: #67 (existing — no new review bandwidth)
- Files touched: `eval/mppi_sandbox/assert_reach.py`,
  `eval/mppi_sandbox/tests/test_assert_reach.py`
- TSV row appended: yes
