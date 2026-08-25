# The gate fired on the write order that mandates the offence

- **Cycle**: 2026-08-07 06:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — fix D-108's two bills (no Notion; 103rd cycle without MCP permission)
- **Phase**: P5 (first cycle of the P5 window; work is still P3 branch debt)
- **Status**: keep

## What I tried

- **Gate 1 evaluated, not inherited**: queue = **6** (PRs #66/#67/#68/#69/#44/#23),
  so the 123rd consecutive `pr-queue-full` skip. Deadlock-breaker crit (b)
  re-checked against `docs/decisions.md` — the only PR-linked supersession
  (line 573) supersedes D-090's *recommendation*, not a PR. No candidate, so no
  self-heal. Escalation floor 08-10 00:54 not reached → no Telegram.
- **Repaired the already-queued branch anyway.** HEAD was red and unpushed; a fix
  pushed to #67's branch adds nothing to the review queue the gate protects.
- **Bill 1 (a)**: made `push_preflight.check`'s `UNSUPPORTED_CLAIM` population an
  injectable parameter (`frontier`), defaulting to the live read.
- **Bill 2 (b)**: re-probed the four `inert_surface` pins over their entrants.

## What worked / what failed

- ✅ **Bill 1's mechanism named precisely**: `check` grades four axes, three of
  which are functions of its arguments and one of which reads the working
  repository. Three tests calling `check()` to grade a *different* axis
  inherited it. And the trigger is not incidental — **D-044 orders the journal
  written at 4a and the TSV row appended last before push, with the suite at
  4a-ter in between**, so "a journal claims a row that does not exist yet" is
  true *by construction* at exactly the moment the constitution orders the run.
- 🔴 **The rejected fix was rejected on a measurement, and my argument for it was
  wrong twice.** Exempting the newest cycle by position (mirroring
  `cycle_artifacts.unpublished`) was going to be refused with "that empties the
  frontier". Asserted it — **failed**: the fixture's offence is not the newest
  journal. Moved the offence onto the newest journal — **failed again**, and this
  one is the finding below.
- 🔴 **The gate is already partly blind to the in-flight cycle, and D-108
  overstated its scope.** The last row in a branch's TSV is the one most likely
  to be **retroactive** (02:00 and 05:00 both appended one), and a retroactive
  row is precisely where the two dating keys disagree: `appended` dates it by
  `git blame` and hands it to the newest cycle, `records` reads the sha it
  carries and hands it to the older one. `unsupported` is their **intersection**,
  so on the newest cycle it goes quiet — measured: `appended` reads `HONOURED`,
  `records` reads `UNSUPPORTED`, frontier `()`. D-108's "exactly the ones a cycle
  can still repair" is true of the retrospective half only. Not repaired — either
  key alone re-imports the over-reporting the intersection exists to exclude.
  **Q-102**, pinned as an executed bound.
- ✅ **Bill 2 was one entrant, not eight.** All four pins re-took
  `INERT_COMPOSED`, gen 1 → 2, in **4.5 s total** — D-107 priced the re-take at
  ~3.5 min off an entrant set of 8 files; this one had **1**
  (`test_push_claim_gate.py`, plus `test_push_preflight.py` for `results/`).
  The estimate was an order of magnitude high and is corrected in the pin note.
- ✅ **No new test file**, deliberately: the two new tests went into the existing
  `test_push_claim_gate.py`, so (a) did not re-price the inert surface that (b)
  then re-pinned. STATE's "(a) before (b)" ordering held.

## North-star delta

- **No avoidance or tracking number moved — seventy-fourth consecutive instrument
  cycle.** Scenes able to contribute an avoidance number: 5, reportable: 4.
- What moved: HEAD is green and pushable again, and the push gate no longer
  fails by construction on its own constitution's write order.
- The 가려진-obstacle class still has exactly one working cost term (D-027), and
  every path to a real number is behind the 26-day merge stall.

## Key learnings

- **An axis that reads ambient state must be injectable, or every test that
  reaches it becomes a test about today's repository.** The tree axis had learned
  this already (`declared`); the population axis had not.
- **A guard whose offence is guaranteed by the process it guards is not a guard.**
  Worth checking new gates against D-044's write order before shipping them.
- **Two assertion failures were worth more than the passing version would have
  been.** The counterfactual I set out to pin was false, and the second failure
  surfaced a scope defect in D-108 that nobody had read.
- **A cost estimate carried in a docstring is a measurement's expiry date.**
  D-107's ~3.5 min was honest when taken and 47× wrong one day later.

## Recommended next 1–3 priorities

1. **Answer Q-102** — decide whether the frontier's newest-cycle blindness is a
   bound or a defect. It is the forward-looking half of D-108's gate.
2. **Grade the cycle that writes no journal at all** (04:00 on 08-07 left only a
   `/tmp` stamp) — `cycle_artifacts`' population is journals, so the earliest
   failure mode is silent.
3. **Fix D-044's ordering table: `results/*.tsv` IS test-read surface.** Its
   "(checked)" has been false since D-105 and bill 1 is what it costs.

## Artifacts

- PR: #67 (existing, branch pushed to)
- Files touched: `eval/mppi_sandbox/push_preflight.py`,
  `eval/mppi_sandbox/inert_surface.py`,
  `eval/mppi_sandbox/tests/test_push_claim_gate.py`,
  `eval/mppi_sandbox/tests/test_suite_coverage.py`,
  `eval/mppi_sandbox/tests/test_inert_surface.py`,
  `docs/decisions.md`, `docs/deliberations.md`
- TSV row appended: yes
- Suite receipt (re-taken after 4a/4a-bis per D-043; `verify` was correctly red
  on the Phase-3 stamp): **1343 passed, 156 skipped, 1 xfailed, rc=0** in 716.7 s
  — `sandbox:pass=1343/1343`, up from 1334/1340 (6 failed) at 05:00.
