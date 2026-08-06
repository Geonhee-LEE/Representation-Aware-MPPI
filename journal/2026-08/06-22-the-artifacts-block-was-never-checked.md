# The Artifacts block is a prediction, and nothing ever checked it — 6 of 99 cycles claimed a TSV row they never appended

- **Cycle**: 2026-08-06 22:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: 21:00 journal #1 — re-take D-103's suite count and TSV row
- **Phase**: P3
- **Status**: in_progress

## What I tried

- Went to discharge the 21:00 cycle's #1 (D-103's TSV row was never appended)
  and found the same defect **in the cycle that reported it**: `origin` was at
  `85e0bc7`, two cycles behind, and 21:00's own journal reads
  `TSV row appended: yes` over a TSV whose last row is 17:42.
- So built the instrument instead of doing the bookkeeping by hand:
  `eval/mppi_sandbox/cycle_artifacts.py` (+28 tests, 2 s) grades every journal's
  `## Artifacts` claims against the repository they describe.
- Two claims are checkable: **did a TSV row appear** (against `results/*.tsv`)
  and **did the cycle leave the machine** (is the journal file in
  `origin/<branch>`).

## What worked / what failed

- ✅ **The population is 6 of 99, not the 3 that were known.** The three known
  cases (09:00, 18:00, 21:00) plus **08-05 10:00, 13:00 and 14:00**, which
  nobody had looked for. One cycle in sixteen, and every one reads as a complete
  cycle in its journal.
- 🔴 **The first cut said 9, and 2 of the 9 were wrong.** It read the row's
  `timestamp` column — hand-typed, and a cycle that overruns types the hour it
  *finished* in. The row stamped `04:05` carries `pass=1048` and D-093's text,
  which is the **02:00** cycle's work: one cycle wrongly convicted, one wrongly
  credited, from a single transcribed field. Assignment now keys on the
  `commit` column, which is a git object with a real date (`315d74f` → 02:46).
  D-104's finding — a hand-kept copy drifts from the thing it copies — one
  cycle later, in the field next to the one it fixed.
- ✅ **The control was necessary and not sufficient.** 09:00 was established by
  hand by the 10:00 cycle, so it is the one case with an independent answer, and
  it is the first test. But it is a *positive*, and the first cut reproduced it
  while still being wrong twice — a control set of positives cannot bound the
  false-positive rate. `test_the_reading_is_not_everything` is the check that
  the grader discriminates at all.
- 🔴 **D-104 wrote "a cycle that never pushes leaves no red anywhere" and then
  did not push.** The push gate (D-082) is not at fault: it fails closed and it
  never ran. A gate that is never reached raises no alarm, which is why the
  absence needs an instrument rather than a stricter gate.
- ✅ **The newest cycle is exempt by position, not by name.** A cycle in flight
  has a journal and no push; that is normal. Skipping whichever is last means
  two consecutive silent cycles go red on the second — one cycle of latency,
  and it is exactly what would have fired at 21:00.
- 🔁 **Census cost, 33rd cycle: pool 78 → 80**, and D-089's across-function rule
  is broken **on purpose** for the first time. `unsupported` is the module's
  headline and it *entered* — because D-104's prescribed repair (derive the set,
  name the derivation at the call site) puts `in finding_grades()` inside the
  conclusion. Six predictions held on the *natural* spelling of a conclusion;
  D-104's repair overrides the natural spelling. The two rules are in tension
  and this is the first cycle where it shows in the count. Second-order cost
  nil — but only after the first cut shipped `FINDING_GRADES` as a typed global
  and drove `unwatched_exemptions` five-to-six within one test run, the fifth
  instance, paid in-cycle this time.

## North-star delta

- **No avoidance or tracking number moved — seventy-first consecutive instrument
  cycle.** Scenes able to contribute an avoidance number: 5, reportable: 4.
- What moved: the durable record's own error rate is now measured (6/99) rather
  than discovered one accident at a time, and two cycles of work that never left
  the machine are pushed.

## Key learnings

- **A self-report written before the work finishes is a prediction, and the
  journal's Artifacts block is entirely self-reports.** Every other section is
  prose nobody can check; these three lines are checkable and nobody checked
  them for 99 cycles.
- **A control made of positives cannot tell you the false-positive rate.** The
  first cut reproduced all three known cases and was still wrong twice.
- **Two accepted rules can prescribe opposite spellings.** D-089 predicts
  conclusions are invisible because they are naturally spelled as comparisons;
  D-104 requires derivations be named at the call site, which forces membership
  into the conclusion. Following the second breaks the first.
- **The failure mode that leaves no trace is the one worth an instrument.** A
  red test, a red CI, a failed push gate all announce themselves. A cycle that
  simply stops announces nothing, and its journal reads identically to a
  complete one.

## Recommended next 1–3 priorities

1. **Run `cycle_artifacts` in the push gate**, not just as a test — the check
   that would have caught 18:00 belongs where the cycle ends, not where it is
   read.
2. **Repair the 6 unsupported rows** — either append the missing TSV rows
   retroactively (with honest `unmeasured` counts) or correct the journals.
3. **Grade the third Artifacts claim, `Files touched`**, against the branch diff
   — the 18:00 journal listed the TSV there too, so that line is wrong at least
   once and is currently unchecked.

## Artifacts

- PR: #67 (existing — 95th consecutive cycle writing into it, no new review cost)
- Files touched: `eval/mppi_sandbox/cycle_artifacts.py` (new),
  `eval/mppi_sandbox/tests/test_cycle_artifacts.py` (new),
  `eval/mppi_sandbox/tests/test_guard_reflexivity.py`,
  `eval/mppi_sandbox/tests/test_magnitude_census.py`, `docs/decisions.md`,
  `docs/deliberations.md`, `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV row appended: yes
