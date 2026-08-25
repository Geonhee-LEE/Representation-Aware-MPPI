# The slow job's ceiling was never the bug — a nested suite outgrew its own timeout

- **Cycle**: 2026-08-05 19:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `STATE-2` Redesign the fast/slow split — do NOT raise 120 to 240
- **Phase**: P3
- **Status**: keep

## What I tried

- Picked STATE #2 after STATE #1 (re-read this branch's CI) came back
  `PENDING` — the run on `664d27c` was 12 min in. Checking why the *previous*
  runs never concluded turned STATE #2 from a scheduling nit into the binding
  constraint on STATE #1: **`slow` is a required job, and it has been killed at
  its ceiling on every completed run**, so this branch cannot go green no
  matter what `fast` says.
- Read the killed job's **log** rather than its conclusion — 269 lines from
  `actions/jobs/92244019197/logs` (run `30987013397`).
- Built `eval/mppi_sandbox/nested_suite_cost.py` + 19 tests.

## What worked / what failed

- 🔴 **The log is the finding, and it is an inequality between two numbers in
  two files that were never compared.** The `fast` half's pytest step costs
  **1396 s** on CI (`Run eval suite (fast half)`, 08:57:31Z→09:20:47Z, run
  `30991167667`). The timeout guarding a *nested* suite run is **900 s**
  (`timeout: int = 900` on `predicate_vacuity.measure`, `predicate_inputs.measure`,
  `guard_vacuity.measure`). Those functions shell out to
  `python -m pytest DEFAULT_SUITE` — **the whole fast half**. So since the fast
  half crossed 900 s, every one of those calls times out *by construction*: not
  flakily, not on a slow runner, but arithmetically, on every run, forever.
- 🔴 **Three ceiling raises were all reacting to this crossing and none touched
  it.** D-084 took `fast` 10→30, D-085 took `slow` 60→120, and STATE carried
  "do not raise 120 to 240" as an instruction without a mechanism. The mechanism
  is that `grade()` **does not mention the job ceiling at all** — so no value of
  `timeout-minutes` can change the verdict. Raising to 240 buys more timeouts.
- 🔴 **Six red results have been invisible for twelve-plus runs.** A job killed
  at its ceiling prints no pytest summary, so `gh` publishes `cancelled` and
  `ci_verdict` grades `UNRUN` — both correct, both silent about failures the
  `-v` stream had *already published*. **Sixth instance of absence-read-as-clean,
  and the first where the hidden thing is already red** rather than merely
  unknown. The instrument named eight across the job; six are `test_exclusion_scope`.
- 🔴 **My first draft of the scan shipped a false positive and running it caught
  that.** It graded `_measure_scratch` (`timeout=300`) `DOOMED` against the
  1396 s full-suite duration — comparing a timeout to work that site does not
  do. Added a measured `subject` (`FULL_SUITE`/`SCRATCH`/`UNKNOWN_SUBJECT`); the
  arithmetic now runs only where the subjects match, pinned by a test.
- 🔴 **Two docstrings claimed the 1354 s gap was "two 900 s waits".** It is one
  wait plus 454 s of real work — 1354 ≠ 1800. Corrected before a test could pin
  it. `_quanta` deliberately grades such mixed gaps **0**, which understates the
  stall (46% measured vs a 38% floor) rather than rounding in its own favour.
- ✅ **The stall detector is falsifiable**: the same log grades `WORK` at
  quantum 600 and 1200 and `STALL` only at 900. A grader that said `STALL` for
  every log it could read would have measured nothing.
- ✅ 19/19 on the module. Pure text + AST — it spawns no subprocess, pinned by
  `test_this_module_spawns_no_subprocess`, since an instrument that diagnosed
  nested-suite cost by nesting a suite would also move the count it publishes.

## North-star delta

- **No avoidance or tracking number moved — fifty-seventh consecutive instrument
  cycle.** Scenes able to contribute an avoidance number: 5, reportable: 4.
- What moved is the *reachability* of a green authority reading. STATE #1 hoped
  the branch was one `fast` fix from green; it never was, because the other
  required job cannot finish. That hope is now measured and dead, which is worth
  more than the hope was.
- Six genuine test failures re-entered visibility after twelve-plus runs of
  being hidden behind a cancellation.

## Key learnings

- **A timeout is a claim about a subject, and both the subject and the guard
  have to be measured.** Nothing here was flaky and nothing was slow-because-big
  — 1396 > 900 is the whole defect, and it was invisible because the two numbers
  live in a workflow file and a function default.
- **A cancelled job is not a job with no results.** It is a job whose results
  were not *printed*. Every reader in this package reads the printed channel.
- **The dev box cannot reproduce this class at all**: locally the fast half is
  ~480 s, comfortably inside 900, so these tests pass here and can only fail
  there. Fourth cycle running where the defect was only visible on the surface
  that decides — the method is now 4-for-4.
- **Cost is quadratic in suite size.** Each instrument cycle lengthens the fast
  half, which is paid once per nested call site. `measure_attributed` (1800 s)
  is already `MARGINAL` at 78% consumed — the next one to fall.

## Recommended next 1–3 priorities

1. **Repair it, and do not do it by raising 900.** The load-bearing choice is
   whether the census needs the *whole* suite as its subject or only the tests
   that exercise the predicates; a session-scoped fixture collapsing the 6+
   nested runs into one is the cheap half, but one run still costs 1396 s.
2. **Re-read the six hidden `test_exclusion_scope` failures on their merits** —
   they have not been looked at since 2026-08-04 and nobody knows if they are
   the timeout or something else underneath it.
3. **Re-read this branch's CI** (STATE #1, carried) — but with the expectation
   that `slow` is still killed until (1) lands.

## Artifacts

- PR: #67 (open, 81st consecutive cycle writing into it)
- Files touched: `eval/mppi_sandbox/nested_suite_cost.py`,
  `eval/mppi_sandbox/tests/test_nested_suite_cost.py`, `docs/decisions.md`
- TSV row appended: yes
