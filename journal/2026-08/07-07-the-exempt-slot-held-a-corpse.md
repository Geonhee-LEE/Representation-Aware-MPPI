# The exempt slot held a corpse, not a cycle in flight

- **Cycle**: 2026-08-07 07:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #2 — answer Q-102 (the frontier's blindness to the newest cycle)
- **Phase**: P5
- **Status**: keep

## What I tried

- REVIEW opened on a contradiction: `STATE.md` said the 06:00 cycle was
  "**GREEN (1343/1343), pushed**", and `origin` was four commits behind. D-108,
  D-109 and both TSV rows were **stranded on disk**. The 06:00 cycle committed
  at 06:32 and died before its push.
- Asked the obvious question — why did no instrument say so? `cycle_artifacts.unpublished`
  exists precisely to grade "journal never reached origin". Ran it: **two cycles
  stranded (`07-03`, `07-06`), one reported.**
- Fixed the blindness rather than the incident: `unpublished(..., in_flight=)`
  and a new `frontier_stranded()`. Default behaviour unchanged.
- Pushed the four stranded commits plus this cycle's work.

## What worked / what failed

- **The exemption is sound; discarding its observation was the defect.**
  `unpublished` skips `ordered[-1]` because a cycle in flight has a journal and
  no push. True — *after* 4a. Before that write, the newest journal on disk
  belongs to the cycle that just **ended**, so a predecessor that died
  before pushing sits in the exempt slot and grades clean.
- **The window is exactly REVIEW**, which is the one moment the stranding is
  still cheap to repair. So the instrument is dark precisely when it would pay.
- 🔴 **This is Q-102, arriving by a second, independent mechanism.** Q-102 (06:00)
  described frontier blindness via the *two TSV dating keys* disagreeing on a
  retroactive row. This one needs no TSV and no dating key: it is the positional
  exemption alone. One symptom, two causes — Q-102's fix would not have caught it.
- **No second-order census cost**, which this package usually pays: 106 tests
  across `magnitude_census` / `guard_reflexivity` / `push_claim_gate` /
  `suite_coverage` unmoved. `unpublished`'s new narrowing is an inequality over a
  scalar, and `_is_set_valued` does not resolve it — invisible for D-079's reason.
- Kept the D-095 discipline: the incident is reproduced in a **scratch repo**
  fixture, not asserted against the working tree. The live reading discharges
  itself the moment anybody pushes.

## North-star delta

- **No avoidance or tracking number moved — seventy-fifth consecutive instrument
  cycle.** Scenes able to contribute an avoidance number: 5, reportable: 4.
- What did move, and it is not nothing: **four commits of green work that
  existed only on this machine are now on `origin`.** D-108 and D-109 were
  unreviewable for an hour.
- The detector that exists to catch exactly this now catches it.

## Key learnings

- **A positional proxy for "in flight" is only valid inside the window where the
  running cycle has already announced itself.** Outside it, the proxy points at
  a corpse. Any exemption inferred from order should state the window it assumes.
- **An exemption that *discards* its observation cannot be audited; one that
  reports it can.** D-038 said this about exclusions; the same argument applies
  to the exempt element itself. `frontier_stranded` costs one function.
- **`push_preflight` makes a bad push impossible and says nothing about an
  absent one.** Third confirmed instance (08-05 07:00, 08-05 11:00, 08-07 06:00).
  The gate is fail-closed on the wrong axis: no receipt ⇒ no push is exactly
  the behaviour that turns a dying cycle into a silent one.
- **STATE.md asserted a push that never happened, and nothing compares STATE's
  claims to the remote.** `cycle_artifacts` grades *journals*; the snapshot file
  is ungraded and it is the file the next cycle's REVIEW trusts most.

## Recommended next 1–3 priorities

1. **Have the executor call `unpublished(in_flight=None)` during REVIEW** — the
   parameter now exists and nothing passes it. An instrument with no caller is
   D-107's dark exemption again.
2. **Grade `STATE.md`'s push claim against the remote.** This cycle's entry point
   was a human noticing "pushed" was false; that should be a test.
3. **Pin `journal/` as a post-receipt write** (previous STATE #1, still unpaid —
   it is what makes every honest cycle run the suite twice).

## Artifacts

- PR: #67 (existing — this branch was already in the review queue)
- Files touched: `eval/mppi_sandbox/cycle_artifacts.py`,
  `eval/mppi_sandbox/tests/test_cycle_artifacts.py`, `docs/decisions.md`,
  `docs/deliberations.md`
- TSV row appended: yes
