# The three-arm head-to-head ran, and D-217's headline changed sign when the risk term was removed

- **Cycle**: 2026-08-12 14:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — run the three-arm head-to-head (shadow / geometric-null /
  predicted-geometry) at matched λ and paired seeds, timeout rate beside clearance
- **Phase**: P3
- **Status**: keep

## What I tried

- Built `eval/mppi_sandbox/three_arm.py`: the three arms of the branch's
  geometry axis — *neither* (`w_epist`), *geometry now* (`w_geom`), *geometry
  predicted* (`w_ped`) — walked on all 3 eligible scenes at matched `lam = 0.8`
  and 6 paired seeds against a shared baseline.
- Made the verdict **joint over clearance and completion** rather than
  clearance-with-a-completion-footnote. `BOUGHT_WITH_FREEZE` outranks
  `IMPROVED`; this is the feed's PGIF metric-selection critique (82 % collisions
  → 59 % timeouts, headline "0 % collisions") encoded as a predicate.
- Denominated every arm against an **empty** baseline (`w_risk = 0.0`) so each
  knob is read alone. D-217 did not: both its arms carried the shipped
  `w_risk = 40.0`.

## What worked / what failed

- 🔴 **The headline finding is a negative one, and it is about D-217's own
  number.** `predicted` reads **WORSE on all three scenes** — including
  `cafe_obstacle_crossing_v0`, where D-217 reported 0.007 → 0.382 m one cycle
  ago. The cause is the denomination, and the 2×2 that separates them is clean
  (6 paired seeds, `lam = 0.8`, worst-case clearance, m):

  | | `w_ped = 0` | `w_ped = 50` | step |
  |---|---|---|---|
  | `w_risk = 40` | 0.0068 | 0.3823 | **+0.3755** |
  | `w_risk = 0`  | 0.0202 | 0.0010 | **−0.0192** |

  D-217 reproduces **exactly** in the top row, so this is not a contradiction of
  its measurement — it is a bound on its claim. The `w_ped` step changes
  **sign** when the risk term is removed: PGIF's field is an *interaction* with
  the BEV risk term, not a main effect. The bottom row also says the risk term
  *alone* costs worst-case clearance (0.0202 → 0.0068) — **the pair wins where
  neither member does.**
- 🟢 **`geometric` (the static-geometry null) is the only arm that improves on
  every scene** — +0.033 / +0.409 / +0.020 m, completion 6/6 everywhere. The
  `geometric_null` attribution worry gets sharper, not softer: the arm carrying
  no learned channel, no motion model and no uncertainty estimate is the one
  that wins outright.
- 🟢 **`shadow` read `INERT` on the crossing scene** — byte-identical
  trajectories, exactly D-021. The verdict reports it as `INERT` rather than
  `TIED`, which is the distinction that matters: it moved on `cafe_convoy_v0`
  (+0.158 m), so the inertness is scene-dependent, not a property of the critic.
- 🟢 **Zero `BOUGHT_WITH_FREEZE` across all 9 readings** — completion is 6/6 for
  every arm on every scene. The freezing tax is genuinely not being paid at
  these densities. That is a real (if narrow) safety result and the guard that
  would have caught the opposite was in place before the numbers were seen.
- 🔴 **The suite went red on four tests and two of them were real signal, not
  pin drift.** This is the third time in four cycles that a guard firing on new
  code was reporting a defect rather than announcing itself. (1)
  `test_lam_dependence` put `three_arm.py` in its "not a test and bills no sim"
  list — because `read_arm` closed over `params` inside a local `walk()`, which
  the static detector cannot see through, so it scored two `DEFAULTS`: **the
  census billed the temperature as unnamed one line below where it was named.**
  Threading it as a keyword flipped both to `FORWARDS` and cleared the list back
  to its two documented artifacts. (2) `test_consumer_reach` found
  `risk_interaction` shipped with **zero callers** — the 2×2 it computes is this
  module's headline, and it was reachable only from prose. `main()` now prints
  it. Only the remaining two (`decides` 78→81, `forwards` 23→27, `total`
  159→166) were the census walking into its own population, for the twelfth
  consecutive cycle.
- 🔴 **Cost discipline cut the deliverable.** `head_to_head()` is 3m40 and
  `risk_interaction()` is 1m10 — neither is in the suite. The verdict logic is
  tested synthetically (15 tests, 3.0 s); the measured tables live in the module
  docstring and here, and re-taking them is a CLI action. A future cycle that
  wants these numbers in CI has to pay for them.

## North-star delta

- **The branch's first three-arm comparison, and it inverted its own most recent
  headline.** Net movement on 물체회피 is *negative-going-honest*: the capability
  claim D-217 booked is now bounded to a composition (`w_risk = 40` present),
  not to the PGIF term.
- The arm that actually holds clearance on all three eligible scenes at zero
  completion cost is the **no-learning geometric null**. For a project whose
  hypothesis is "representation quality upper-bounds control quality", that is
  the uncomfortable reading and it is the one to chase.
- Completion held 6/6 in 36 of 36 arm-walks — the freezing tax is bounded below
  at these densities.

## Key learnings

- **A one-cycle-old capability headline was denominated against a non-empty
  baseline and nobody wrote that down.** D-217's journal says "`w_ped` 0 → 50";
  it does not say "with `w_risk = 40` under both". The number was correct and the
  claim was wider than the number. The cheap fix is structural: an arm set that
  states its own baseline composition (`ARMS` here does, and a test pins
  `w_risk == 0.0` so it cannot silently drift back).
- **Isolating the knobs is what found it.** Had I reused D-217's controller
  factory the head-to-head would have reproduced its table and reported a
  three-arm win. The disagreement only exists because the denomination changed.
- **Interaction effects are now on this branch's map and were not before.** Every
  comparison the branch has run is one-knob-at-a-time against a fixed
  composition; none of them can see a term that only works in company.
- **"The guard is announcing itself" is the wrong first hypothesis, and this is
  the third cycle in four to prove it.** Two of four reds were defects in the new
  code — one of them (`params` invisible at the call site) is *the same class of
  mistake* as the finding this cycle's headline is about: a temperature that is
  set correctly but not legible where it is used. Reading the bill before paying
  it cost about three minutes and changed the diff twice.

## Recommended next 1–3 priorities

1. **Walk the full `w_risk` × `w_ped` 2×2 on all three eligible scenes** — the
   sign flip is measured on one scene. If it holds on three, "PGIF is an
   interaction term" is a branch-level result; if it does not, it is a scene
   property.
2. **Put the geometric null's three-scene sweep on a CI-affordable budget** — it
   is the arm that won everywhere and the only one whose result is currently
   untested. 2 seeds × 3 scenes is ~35 s.
3. **Re-probe the stale `journal/` and `results/` pins** (carried from last
   cycle, still unpaid).

## Suite

- Suite 1 **RED**: 2618 passed / 4 failed, 487.80 s, 14 shards. Two reds were
  real defects in this cycle's code (see above), two were census pins.
- Suite 2 **GREEN**: **2623 passed** / 157 skipped / 1 xfailed, 486.78 s, 14 shards.
- `verify` / `declared` both flagged exactly one path — *this journal file*,
  edited after the stamp. That is a **D-044 ordering slip I made**: 4a's write
  belongs before the re-run, and I appended the red-suite finding after it.
  `journal/` is in `citation_audit.EXCLUDED_SURFACES` and no test references the
  file (checked by grep, not asserted), so 2623 is a true statement about the
  code tree the PR ships — but the ordering rule exists so that sentence does
  not have to be written, and next cycle should not have to write it either.
- ~44 min against a 35-min budget — **OVERRUN by ~9 min**. Cause is nameable and
  is not the same as last cycle's: the D-181 elapsed reading said
  `SUITE_UNAFFORDABLE` at 23m42, and I ran a second suite anyway because the
  alternative was stranding a finished journal. The advisory's purpose is to
  publish; here the only path to publishing was the second suite. What actually
  cost the budget was the 3m40 `head_to_head()` walk taken *before* any test
  existed — measure-then-test inverted the cheap order.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/three_arm.py, eval/mppi_sandbox/tests/test_three_arm.py, docs/decisions.md
- TSV row appended: pending
