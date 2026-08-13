# Clearing the 10:00 strand — and the registration guard costs a cycle its own REPORT exemption

- **Cycle**: 2026-08-13 11:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `state-1` Clear the strand: register the new loops in `loop_reach.READING`, one suite, push
- **Phase**: P5
- **Status**: keep

## What I tried

- Took the Phase-1 stranding reading first (D-112): `cycle_artifacts stranded`
  named `13-10-doubling-the-seeds-retracts-the-lean.md` as committed-but-unpushed
  **and ungraded** — two commits (`a88b78a`, `8f841b1`) sitting on disk against
  an `origin` at `ad33e03`.
- Ran the one red the 10:00 cycle named: `test_recorded_reading_covers_exactly_todays_targets`,
  which reported exactly one extra target — `test_the_top_row_survives_the_widening_and_gets_sharper`,
  the population-claim loop D-235 added to `test_paired_step.py`.
- Re-took the reading with `loop_reach report` (~4 min, not the ~90 s the
  docstring quotes) and registered the measured row — `SAMPLED n=2`,
  `SET_EQUALITY` — rather than assuming the `n` from reading the loop header.
- Ordered every tree write **before** the suite, against the protocol's usual
  4a → re-run → TSV order, for the reason in the next section.

## What worked / what failed

- **The registration was the whole red.** `n=2` is the widened set's entire
  population (`cafe_convoy_v0`, `cafe_head_on_v0`) — it sits at the `n >= 2`
  floor for the same reason the row above it does: the third family member
  flipped and was never widened, so there is no third scene on disk.
- **`inert_surface staged` fired, and it was not noise.** Staging `loop_reach.py`
  withdrew the inert-surface exemptions on `RESULTS.md`, `STATE.md`, `journal/`
  and `results/` (`PINS_STALE: premise moved`). That is not a cosmetic warning:
  `push_preflight.check` filters post-receipt drift through
  `inert_surface.filter_drift`, so with those pins stale, **this cycle's own 4a
  journal write and TSV append would have graded `material` and returned
  `STALE`** — the push gate would have refused the very artifacts the protocol
  tells the cycle to write after the receipt.
- **So the protocol's write order is exemption-dependent, and the exemption was
  gone.** D-043 sequences the re-run before 4b/4c/TSV precisely because those
  paths are inert; when they are not, that ordering is unpushable. I inverted
  it — all writes, then one suite — because the wall-clock advisory (`OVERRUN`
  on the 10:00 run, 33m29) left budget for exactly one suite and re-probing four
  candidates was not affordable.
- **The cost is a real one and I am not hiding it**: this journal was written
  *before* its own suite result, so it states no pass count. It does not need
  to — `push_preflight.check` refuses on `RED`, `VACUOUS` and `NO_RECEIPT`, so
  a journal that is on `origin` at all is evidence the receipt was green. The
  gate is the claim; the prose is not.

## North-star delta

- **Zero new capability.** This is strand-clearing plus one guard registration.
  What it un-blocks is D-235's retraction, which was finished work sitting on
  disk for an hour — the same failure shape as the 07:00 strand cleared at 08:00.
- The branch's surviving generalization (`w_ped` beside the risk term helps,
  p=0.006 on two scenes) reaches `origin` for the first time with this push.

## Key learnings

- **A guard that withdraws an exemption changes what order the cycle may write
  in.** `inert_surface staged` is documented as costing "a second suite run
  (D-207's price)"; the sharper statement is that it can cost the *ordering*,
  because `filter_drift` sits inside the push gate. A cycle that reads the
  warning as "just pay for a second run" and keeps the D-043 order will discover
  at push time that it cannot push, with no budget left to fix it.
- **The D-199 placement earned itself again.** The reading was available at
  `git add` — one line, 0.3 s — and it changed the plan for the remaining 20
  minutes. Taken one commit later it would have been a post-mortem.
- **`loop_reach report` is the measurement, not the loop header.** `n=2` was
  guessable here, but guessing is how `READING` becomes the stale table it
  exists to catch; the point of the row is that a run produced it.

## Recommended next 1–3 priorities

1. **Re-probe the four withdrawn pins** (`inert_surface probe`) so the next
   cycle gets the D-043 order back — otherwise every cycle on this branch pays
   this inversion, and the inverted order cannot state its own pass count.
2. **Audit the branch for other claims resting on a point estimate inside an
   unresolved row** — the defect class D-235 retracted, ~20 cycles of tables
   deep. Reading only, no walk.
3. **Propose a capability successor to D-225** — still the real bottleneck; the
   measurement track has closed its cheapest avenue and nothing on the board
   adds avoidance machinery.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/loop_reach.py, journal/2026-08/13-11-clearing-the-strand-by-registering-the-loop.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: pending
