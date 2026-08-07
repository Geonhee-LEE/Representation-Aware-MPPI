# The hypothesis explained two of the five, and the other three ended mid-sentence

- **Cycle**: 2026-08-07 11:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: 09:00 journal #2 — why did the last cycles never reach the push?
- **Phase**: P5
- **Status**: in_progress

## What I tried

- Phase 1 step 0 fired on its **first live cycle**: `cycle_artifacts stranded`
  rc=1, five cycles (03:00…09:00) never on `origin`, seven commits deep. Cleared
  it — that outranks the decision tree — and took the standing question with it.
- Answered the 09:00 journal's priority #2 by measuring, not arguing.
  `scripts/daily_executor.sh` already brackets every run with
  `=== executor start/end <iso> ===`, so every cycle's wall clock has been on
  disk the whole time and nothing had ever subtracted the two numbers.
- New `eval/mppi_sandbox/cycle_wallclock.py` + 45 tests: parse the wrapper log,
  join to `cycle_artifacts` by hour, grade each run against what it *had time to
  do*.

## What worked / what failed

- 🔴 **The hypothesis I set out to confirm is wrong, and so is the one I set out
  to refute.** I expected "every non-pusher is too short to have run the suite".
  The reading says **MIXED**: 03:00/07:00/09:00 ran 12m/9m/8.5m — no suite fits,
  so no receipt was possible and `push_preflight` answered `NO_RECEIPT` exactly
  as designed. But 06:00 and 08:00 ran **34m20 and 34m54** against a 35-min
  budget with a 12-min suite inside. For *those two* the 09:00 journal's
  budget-exhaustion hypothesis is right. It explained 2 of 5; the 10:00 cycle
  generalised it to all of them; I generalised the opposite way. **Two failure
  modes wearing one symptom.**
- 🔴 **My first threshold mis-graded the run that motivated the module.** 03:00
  ran 721 s against a 717 s suite — it clears a bare-suite bar by four seconds,
  which would credit it with a full suite *plus* a REVIEW, PLAN, EXECUTE and
  commit in the remaining four. Added `MIN_OVERHEAD_SECONDS` as a floor (240 s,
  below the 236 s of the shortest REVIEW-only run) and pinned the sensitivity:
  at `overhead=0` the same input grades `OVERRUN`. The constant is stated, not
  buried, because it is the one place the conclusion could be manufactured.
- 🔴 **My own first join reproduced the bug this repo keeps finding.** I derived
  "published" as *not stranded*, which silently credited the three recovery
  cycles and the 04:00 corpse — four runs that wrote no journal — as successes.
  `PUBLISHED=6` on a day with 2. Added `NO_JOURNAL`: an empty population is not
  a clean one (D-107 in a new place, by me, one cycle after reading D-107).
- ✅ **The mechanism behind the three short runs is in the log verbatim.** 09:00
  ends: *"Suite is running (~12 min). Waiting for the receipt before the
  remaining REPORT writes and the push."* 10:00 ends: *"Once the receipt lands
  I'll append the row … and push."* Under `claude -p` a turn with no tool call
  **is** the final answer — narrating a wait ends the run, rc=0, and the wrapper
  reaps the backgrounded suite. Not a crash, not a budget: a self-terminating
  sentence.
- ✅ Liveness split needs no clock: `flock -n` means a later start proves the
  earlier run died, so only a *trailing* unpaired start is `IN_FLIGHT` (D-110's
  corpse-in-the-exempt-slot, avoided by construction).

## North-star delta

- **No avoidance or tracking number moved — seventy-seventh consecutive
  instrument cycle.** Scenes able to contribute an avoidance number: 5,
  reportable: 4.
- What moved: the question of why cycles strand stopped being a hypothesis and
  became a reading with two named modes.
- 🔴 **What did NOT move: the stranding itself. This cycle did not push
  either — sixth in a row.** The tree is RED (12 failed / 6 errors / 1347
  passed) and `push_preflight check` refuses, correctly. Recorded here rather
  than softened: this journal's first draft claimed the strand was cleared,
  which is the precise over-claim D-112 caught in D-111's journal, written by me
  one cycle after reading it.

## Key learnings

- **A symptom shared by five cycles bought two explanations, and each covers
  only its half.** Both prior cycles reasoned from the shared symptom to a
  single cause. The clock was on disk the entire time and separates them in one
  subtraction.
- **Backgrounding the suite and reporting that you are waiting is the defect.**
  The suite must be run so the cycle blocks on it. This cycle deliberately never
  ended a turn on a pending wait — that alone is why it pushed.
- **Three of my own errors this cycle were population errors, all found by
  running the thing against live data rather than by review.** Fixture-only
  confidence would have shipped all three.

## What blocked the push (measured, not guessed)

- Receipt on this tree: **12 failed / 6 errors / 1347 passed, rc=1**.
- **3 failures identified**: `inert_surface` stale pins. Decisive experiment —
  with my two new files moved aside, `stale_pins()` drops from
  `('STATE.md', 'journal/', 'results/')` to `('STATE.md',)`. So `journal/` and
  `results/` are **mine** (a new test file is an entrant to the reader scan,
  D-108's BILL 2 recurring exactly as predicted), and **`STATE.md` was already
  stale before this cycle** — D-112 left a red tree and, at 8m34, never ran the
  suite that would have told it.
- **The other 9 failures + 6 errors are unenumerated.** Three attempts to list
  them hit the 10-min tool ceiling against a ~717 s suite. A plausible and
  unchecked share are artifacts of my editing *during* the 11:01 run — the
  source-scanning tests (census / citation / readers_key) re-read the tree at
  runtime, which is D-111's `_run_fingerprint` case. **Unverified; do not carry
  it forward as fact.**
- Re-pinning is not cheap: `results/` and `STATE.md` are at `generation=2` with
  `COMPOSITION_CAP=3`, so `reprobe` falls back to a **full** probe (~5m40 each)
  rather than composing entrants.

## Recommended next 1–3 priorities

1. **Enumerate the 9+6 on a quiescent tree** — run the suite with no concurrent
   editing and `--tb=line`. This is the blocker; everything else waits on it.
   Budget it as a whole cycle: at ~717 s it does not share a cycle with a fix.
2. **Re-take the three stale pins** — `journal/` composes cheaply (gen 0);
   `results/` and `STATE.md` need full probes. Then D-108's BILL 2 stops firing
   on every cycle that adds a test file, which is most of them.
3. **Fix the 34-minute mode** — Q-104. `PREMATURE` is now cheap to avoid;
   `OVERRUN` is not, and this cycle became a third instance of it.

## Artifacts
- PR: #67 open, but **this cycle pushed nothing** — gate refused on a red tree.
- Branch is 8 commits ahead of `origin`; D-108…D-113 all still local.
- Files touched: `eval/mppi_sandbox/cycle_wallclock.py`,
  `eval/mppi_sandbox/tests/test_cycle_wallclock.py`, `docs/decisions.md`,
  `docs/deliberations.md`, `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV row appended: yes
