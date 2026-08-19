# The discharge suite was never exclusive — it can grade two cycles at once

- **Cycle**: 2026-08-19 09:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: Q-169 — `cycle_artifacts claim` rc=2 on a strand-discharge push
- **Phase**: P3
- **Status**: keep

## What I tried

- Step 0 read `stranded` → **rc=1**: `11b5a19` (08:00's own journal + Q-169 + TSV
  row) was on disk with `origin/<branch>` at `8c7cb99`. Complete strand — nothing
  to append, only a push, exactly as 08:00 predicted in its own journal.
- Rejected 08:00's framing that "discharge and new work were mutually exclusive."
  That is true only for work done **during** the suite. Work done **before** it
  is inside the receipt: D-315's `receipt last` ordering means one suite grades
  the strand commit *and* this cycle's commit, because the receipt binds the
  worktree, not a commit range.
- Spent the freed budget on 08:00's own priority #3: implemented Q-169's lean
  option (a) — `cycle_artifacts.discharge_push()` + the `claim` rc=2 → rc=0
  `DISCHARGE_PUSH` branch, ~45 LOC with docstring, 1 test.
- Ordered the cycle 4a → 4a-bis → 4b/4c → TSV → commit → receipt → push.

## What worked / what failed

- **The patch holds the line Q-169 asked for.** `discharge_push` takes no
  argument naming what is being pushed — it re-reads `identification` (already
  called by `claim`) and `unwatched_strandings`, so there is no new place a cycle
  can lie. No new census either: it is a conjunction of two existing readings,
  which is why it dodges the self-reference tax Q-168 flags.
- **The honest/lying split is load-bearing and tested.** The exemption keys on
  `unwatched_strandings` (stranded ∧ *not* `unsupported`), not on `stranded`. An
  over-claiming stranded cycle is the rc=1 case first and still fails closed —
  the test drives exactly that transition by flipping `01-12-c2`'s Artifacts line
  to `yes` and asserting the exemption vanishes.
- **The widening I did not take**: "any push with no 4a" would also exempt a
  cycle that died before REPORT. That cycle has no journal *because it did no
  REPORT*; that is the failure, not an exemption from it. The finished, honest,
  unpushed journal on `HEAD` is what distinguishes a discharge.
- Cost: 0.11 s for the two tests. The 21-minute suite was owed to the strand
  regardless, so the patch's marginal verification cost this cycle was zero.

## North-star delta

- **No movement on the acceptance matrix.** No controller changed, no scene
  swept. The two swept columns (D-357 clearance, D-358 cross-track) are where
  D-358 left them; the 5 vacuous `cte_rms_max` bars are still vacuous.
- **Movement on throughput, which is what has actually been costing columns.**
  Two consecutive cycles (08:00, 09:00) were consumed by strands, and the
  mechanism that consumed them — the gate refusing the discharge push — now
  returns rc=0 on its own. The next strand costs a push, not a hand-judgement.
- Honest accounting: this is infra, not MPPI knowledge. Its claim on the north
  star is that the last two cycles bought zero columns and the reason was this.

## Key learnings

- **08:00's "mutually exclusive" was a real error worth naming.** It read the
  receipt's worktree binding as forbidding *all* work during a discharge cycle.
  What the binding forbids is work committed **after** the receipt. Move the
  work before it and the same suite pays for both. This cycle is the
  demonstration: a strand discharged and a Q resolved on one 1299 s suite.
- **A gate that a cycle must hand-judge is on its way to being muted** (D-044).
  08:00 read rc=2, reasoned correctly about it, and pushed anyway — the right
  call, and also precisely the habit that makes the *next* rc=2 get waved
  through without the reasoning. Encoding the judgement is what keeps the `&&`
  meaning "nobody has to remember".
- **rc=2 vs rc=1 earned its keep.** D-199 split them for `inert_surface staged`;
  the payoff landed here, in a different module, because the split made "too
  early" a state that could be *re-examined* rather than a failure. A boolean
  gate would have had no room for this patch.

## Recommended next 1–3 priorities

1. **STATE #1c — sweep `cte_max` (peak) from the pinned `CTE_SEED0` rollouts.**
   Unchanged and still the last free column: 4 scenes declare it, the rollouts
   already exist, so it costs zero new sim time. Two cycles of strand repair
   have now deferred it three times.
2. **Q-168 — turn on `--durations` in the next `push_preflight record`.** The
   suite runs anyway; the top-10 table is a free by-product and would tell the
   next diagnosing cycle what a scoped re-run actually costs (D-348: 318 s vs
   7.21 s, 44×).
3. **Q-170 (new)** — whether the receipt should bind a commit range instead of
   the worktree, which is the general form of the mistake 08:00 made.

## Artifacts

- PR: #67 (already open) — https://github.com/Geonhee-LEE/Representation-Aware-MPPI/pull/67
- Files touched: `eval/mppi_sandbox/cycle_artifacts.py`, `eval/mppi_sandbox/tests/test_cycle_artifacts.py`, `docs/decisions.md`, `docs/deliberations.md`, `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV row appended: yes
