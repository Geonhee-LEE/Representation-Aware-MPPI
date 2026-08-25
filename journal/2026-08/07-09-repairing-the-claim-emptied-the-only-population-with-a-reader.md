# Repairing the claim emptied the only population with a reader

- **Cycle**: 2026-08-07 09:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: 07:00 journal #1 / Q-103(a) — give the stranding reading a caller
- **Phase**: P5
- **Status**: keep

## What I tried

- REVIEW opened on the same contradiction for the **third** consecutive cycle,
  one commit worse each time: `origin` at `ff2fe42` (02:00), local `HEAD` at
  `c53f587`, **six** commits and four cycles' work stranded on disk. The 08:00
  journal says *"five stranded commits … reached `origin`"* and
  `TSV row appended: yes`; both are false, and it wrote them while its own
  subject was cycles that do exactly that.
- Took Q-103's lean (a): `cycle_artifacts.stranded` = `unpublished` with the
  positional exemption declined, a `stranded` subcommand that exits non-zero on
  a finding, and a Phase 1 **step 0** in `auto_research.md` that runs it before
  reading anything.
- Named the residue the push gate structurally cannot reach:
  `unwatched_strandings` = stranded ∖ unsupported.
- Appended the two missing TSV rows (D-110, D-111) — the gate refuses on
  unsupported claims and that is what it was refusing on.

## What worked / what failed

- ✅ **The reading found what three REVIEWs missed, in 3 seconds**: 4 stranded,
  2 of them invisible to the push gate. `07-03` and `07-06` had been sitting
  there **six hours**, graded `HONOURED`, with the 06:00 `STATE.md` saying
  "pushed" on top of them.
- 🔴 **Then repairing the claims emptied the gate's population while changing
  nothing about the stranding.** Measured before and after appending the two
  rows: frontier `[07:00, 08:00]` → `[]`, stranded `[03:00, 06:00, 07:00,
  08:00]` → **unchanged**, and all four moved into `unwatched`. So the act that
  licenses the push is also the act that makes the branch look clean to the only
  population anybody consumes. **The gate does not measure stranding; it
  measures dishonesty about stranding, and those come apart exactly when a cycle
  is honest.** This is the argument for step 0 that I had not expected to be able
  to *measure* — I set out to wire a caller and got a demonstration that the gate
  could never have been that caller.
- ✅ **The renderer takes its populations instead of reading the repo**, so the
  wording is testable without a scratch git repo. `report`'s wording had no test
  until D-105 for exactly the opposite reason.
- 🔴 **My first test asserted the header's wording and was wrong, not the code**:
  I counted the word `unwatched` expecting 2 (header + marker); the header says
  "invisible to the push gate". Retargeted the assertion at the marker itself,
  which is the thing that must be per-row, and added the header count separately.
- ✅ **`stranded` delegates rather than re-derives**, pinned by a source test:
  a stranding rule spelled twice drifts the moment `published`'s
  unreadable-remote handling changes under one copy (D-045/D-047).

## North-star delta

- **No avoidance or tracking number moved — seventy-sixth consecutive instrument
  cycle.** Scenes able to contribute an avoidance number: 5, reportable: 4.
- What moved: four cycles of finished work (D-108…D-111) stopped being stranded,
  and the failure mode that stranded them now has a reader that runs before the
  cycle can spend its budget.

## Key learnings

- **A gate that fails closed on dishonesty is not a detector of the thing lied
  about.** Clearing the lie clears the gate; the underlying fact is untouched and
  now unwatched. Any guard phrased over *claims* has this shape.
- **The set with no reader is a set difference, not a file nobody wrote.** Both
  `unsupported` and `stranded` have readers; `stranded ∖ unsupported` had none,
  and that is where two cycles hid for six hours.
- **`STATE.md` saying "pushed" is prose, and three REVIEWs believed it.** Step 0
  works because it asks git instead of asking the previous cycle. Q-103's other
  half — grading the snapshot's push claim as a *test* — is still unpaid.

## Recommended next 1–3 priorities

1. **Grade `STATE.md`'s push claim against the remote** — Q-103(c), the half not
   paid here. This cycle's entry point was noticing "pushed" was false by hand,
   three cycles running; that should be an assertion.
2. **Find out why the last four cycles never reached the push**, given
   `git push --dry-run` succeeds. Budget exhaustion at a 12-min suite is the
   hypothesis and nothing has measured it; the cron log has the wall times.
3. **Grade the `Metric:` commit trailer against the receipt** — `86e699b` shipped
   `Metric: sandbox:pass=pending-4a-ter` and nothing reads commit trailers.

## Artifacts
- PR: #67 (open — this branch was already in the review queue)
- Files touched: `eval/mppi_sandbox/cycle_artifacts.py`,
  `eval/mppi_sandbox/tests/test_cycle_artifacts.py`,
  `scripts/prompts/auto_research.md`, `docs/decisions.md`,
  `docs/deliberations.md`, `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV row appended: yes
