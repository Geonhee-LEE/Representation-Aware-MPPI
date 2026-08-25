# The count without the name cost three runs

- **Cycle**: 2026-08-07 17:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #2 — answer Q-104 (the `OVERRUN` mode)
- **Phase**: P5 (first full day)
- **Status**: keep

## What I tried

- Took the two Phase-1 readings. `cycle_artifacts stranded` clean; the new
  `cycle_wallclock` advisory graded the preceding run **61m26 against a 35-min
  budget, holding the lock through the 16:00 tick that never ran**. Q-104 is the
  standing question about exactly that mode, and its `다음 action` says the first
  cycle to re-observe `OVERRUN` executes it.
- Went to execute lean **(b)** (conditionalise the 4a-ter re-measurement on
  D-107's inert-surface skip) and **checked its premise first**. Q-104 states the
  34-min mode arises because "12분 suite 가 **두 번** 들어가야 한다". The record
  refutes it: 14:00 ran the suite once (746 s), 15:00 once (756 s), 02:00's
  recovery line says in as many words *"ONE run — D-107's removed second-suite tax
  did not recur"*. **The double-run Q-104 is built on stopped happening before
  Q-104 was written.** Lean (b) removes a cost nobody is paying.
- So asked where the 61 minutes actually went, and the 15:00 cycle's own cron
  line answers it without a new instrument: *"The suite went red once at 1
  failure (the expected census pin) and `push_preflight record` reports only
  counts, so locating it cost three narrowing runs; that is where the overrun
  went."*
- Fixed that instead: `parse_failures()` pulls the node ids out of pytest's
  `short test summary info` block, `Receipt.failed_nodes` carries them, and both
  the `record` CLI and the `RED` refusal print them. +8 tests into the **existing**
  `test_push_preflight.py`.

## What worked / what failed

- ✅ **The answer to Q-104 was in the log, not in its option set.** (a) raise the
  budget, (b) skip the re-measurement, (c) shard the suite — all three treat the
  cost as *suite time*. The measured overrun is **diagnostic latency**: one red
  test, four runs, ~50 min, of which three runs re-derived a string the first run
  had already printed to stdout and `parse_summary` threw away.
- ✅ **The grading dependency is the part that needed controls, not the regex.**
  `check()` still grades on the count. Two mirror tests pin it: a red receipt with
  *no* node ids stays `RED` (a regex miss cannot launder a red suite), and a green
  receipt with a *stray* node id stays `GREEN` (the diagnostic cannot invent one).
  Getting this backwards would have made a parser bug the way to license a bad push.
- ✅ **One end-to-end test over a real `pytest` subprocess.** Every other assertion
  reads a hand-written fixture and would survive pytest changing its summary
  format; this one would not, which is why it is there.
- 🔴 **Anchoring the regex is load-bearing and I nearly missed why.** This suite
  tests *gates*, so assertion text quoting the word `FAILED` is everywhere —
  `test_push_claim_gate` asserts on refusal strings. An unanchored match would
  have harvested node ids out of tracebacks. The negative control is a traceback
  that contains `FAILED nowhere.py::nope` and must not be picked up.
- 🔴 **Wrote a broken line into the test file via heredoc** and had to repair it
  before anything ran. Cost ~1 min; noted because the constitution's own advice
  this cycle was to cut scope, and self-inflicted repairs are the first thing that
  eats the cut.
- ✅ Census cost **nil**, 39th cycle: pool unchanged at **92**. Predicted in
  advance under D-089 — `parse_failures` narrows by `dict.fromkeys` (a dedup, not
  a set difference) and `_name_failures` by a slice; neither is a spelling the
  detector keys on. 123 pin tests green in 19 s.
- ✅ **No new test file, deliberately** — the 8 tests went into the existing
  `test_push_preflight.py`, so D-108's BILL 2 (a new file enters the reader scan
  and invalidates the inert-surface pins) is not re-purchased.

## North-star delta

- **No movement.** Eighty-first consecutive instrument cycle; no planner,
  representation, or avoidance metric changed. Today is day 1 of P5 and this is
  not P5 work.
- What it does buy is **cycle time**, which is the resource P5 needs: a red suite
  now costs one run to localise instead of four. Against the 15:00 measurement
  that is ~38 min returned to a 35-min budget — the difference between a cycle
  that can attempt a P5 deliverable and one that cannot.
- The merge queue is unchanged at 6 PRs / 26 days. This branch is already #67, so
  the push adds zero review bandwidth.

## Key learnings

- **Check a question's premise before executing its lean.** Q-104's three options
  all priced *suite runs*; the record says the suite ran once and the cost was
  *not knowing which test failed*. Two cycles had cited Q-104 without re-reading
  the arithmetic under it.
- **A journal's own prose is a measurement surface.** The datum that answered this
  was one sentence in the 15:00 cron line. No instrument was needed — the honest
  self-report of the previous cycle was the evidence, which is an argument for the
  reporting discipline paying rent, not just costing budget.
- **When adding a diagnostic beside a verdict, pin the direction of the
  dependency in both directions.** The useful failure mode is not "the diagnostic
  is wrong" but "the diagnostic quietly becomes the verdict".

## Recommended next 1–3 priorities

1. **Answer Q-106 — grade stability** (was STATE #1): mark per-axis stability in
   the `cycle_wallclock` reading (lean (c)). Still unaddressed.
2. **Retire Q-104's lean (b) explicitly** — the inert-surface conditionalisation
   is aimed at a second suite run that no longer happens; leaving it as the
   standing lean invites a future cycle to build it.
3. **Start a P5 deliverable that needs no merge** — the metric harness is the
   phase's whole content and the queue has blocked it for 26 days; find the slice
   that lives entirely in `eval/mppi_sandbox/` and needs nothing off main.

## Artifacts

- PR: pending merge (already-open #67, `autoresearch/p3-epistemic-shadow-cost-critic`)
- Files touched: `eval/mppi_sandbox/push_preflight.py`, `eval/mppi_sandbox/tests/test_push_preflight.py`, `docs/decisions.md`, `docs/deliberations.md`, `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV row appended: yes
