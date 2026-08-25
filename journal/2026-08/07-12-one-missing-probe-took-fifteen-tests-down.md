# One missing probe took fifteen tests down, and six cycles never saw it

- **Cycle**: 2026-08-07 12:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — enumerate the 9 failures + 6 errors on a quiescent tree
- **Phase**: P5
- **Status**: keep

## What I tried

- Phase 1 step 0 fired again: `cycle_artifacts stranded` rc=1, **six** cycles
  (03:00…11:00) never on `origin`, all six graded *unwatched* (Artifacts claims
  honest, so the push gate structurally cannot see them). Clearing it outranks
  the decision tree, and clearing it meant making the tree green.
- Ran the full suite **in the background** and blocked on it in the foreground.
  The three prior attempts hit the 10-minute tool ceiling against a 733 s suite;
  a backgrounded run polled by a bounded foreground wait has no ceiling and
  cannot end the turn mid-wait (the 09:00/10:00 self-termination).
- Enumerated, then fixed: registered the missing probe, re-pinned five census
  counts, and re-took the three stale `inert_surface` pins.

## What worked / what failed

- ✅ **The 15 red tests were one bill, not fifteen.** All 6 errors and 4 of the
  failures came from a single `ProbeError: no probe for revocable guard(s):
  cycle_artifacts.unwatched_strandings` — D-112 shipped the guard and never
  registered a probe, and `readings()` refuses wholesale rather than per-guard,
  so one omission took its whole test file plus four census pins down. Two
  thirds of the branch's redness was one unpaid registration.
- 🔴 **The pin ran three cycles unread, and that is the new failure mode.**
  D-112 and D-113 each entered the guard census and neither ran the pin that
  prices entrants — both died before their receipt. A census only charges an
  entrant if somebody runs it; a cycle that cannot reach its own suite cannot be
  charged. `len(pool)` sat wrong from 03:00 until now.
- 🔴 **`COMPOSITION_CAP` made one new test file cost 34 minutes.** `STATE.md`
  and `results/` were at generation 2, so `reprobe` fell back to full probes:
  15m45 and 17m57. `journal/` was at generation 0 and composed in **0.5 s** for
  the same single entrant. Same cause, same cycle, a 2000× cost spread decided
  entirely by generation.
- ✅ **The new probe reads `NAMES_OFFENCE` on both subjects** — a guard that
  works. Its fixture had to set `origin/<branch>` *mid-history*: `_remote_has`
  tests for the path in the remote ref, so a stranding is the gap between local
  and remote and a fixture that pushes everything has no gap to read.
- ⚠️ I lost ~9 minutes to a `ModuleNotFoundError` — running the re-take script
  from `/tmp` puts `/tmp` on `sys.path[0]`, not the repo.

## North-star delta

- **No movement.** Pure instrument repair; no planner, representation, or
  avoidance metric changed. Seventy-eighth consecutive instrument cycle.
- The one real delta is that the branch is **pushable again** — six cycles of
  finished work (D-108…D-113) reach `origin` instead of accumulating on disk.

## Key learnings

- A guard registry that refuses wholesale converts one missing entry into a
  file-wide outage. `readings()` raising `ProbeError` before any probe runs is
  why 6 errors and 4 failures shared one cause — worth asking whether it should
  degrade per-guard instead.
- The stranding reading is now load-bearing twice over: it caught its own
  author's omission. But the guard it added is the thing that had no probe, so
  D-112 shipped a detector and a defect in the same commit.
- Background-plus-foreground-block is the pattern for anything over 10 minutes
  here. It is what let this cycle read a 733 s suite that three others could not.

## Recommended next 1–3 priorities

1. **Wire `cycle_wallclock` into REVIEW** — it shipped in D-113 with no caller
   (Q-103's exact defect, now two cycles old).
2. **Decide whether `COMPOSITION_CAP` should be raised or the pins auto-re-taken**
   — measured cost of the cap is 34 min per test-file addition at generation 2.
3. **Make `readings()` degrade per-guard** rather than raising on the first
   unprobed guard, so one missing probe costs one test, not fifteen.

## Artifacts
- PR: #67 (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/guard_direction.py, eval/mppi_sandbox/inert_surface.py, eval/mppi_sandbox/tests/test_guard_direction.py, eval/mppi_sandbox/tests/test_guard_reflexivity.py, eval/mppi_sandbox/tests/test_liveness_derivation.py
- TSV row appended: yes
