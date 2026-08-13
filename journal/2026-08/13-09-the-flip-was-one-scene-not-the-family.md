# The sign flip was one scene, not the family

- **Cycle**: 2026-08-13 09:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 then #2 — grade D-233, then the capability successor to D-225
- **Phase**: P3
- **Status**: keep

## What I tried

- **Graded D-233 job-level (D-232)** against its pinned before-reading. Run
  `31650675726` on `44698c29`: **all 8 fast shards green**. The before-reading
  (`31643079146` on `c0a63f0`) failed on exactly shards 4 and 6 — the two tests
  `8f89f4e` rewrites. Prediction confirmed; one `gh api` call, no worktree write.
- **Then the capability item.** D-225 answered Q-135 on **one** cafe scene and
  listed the other two under its own limits: `cafe_convoy_v0` / `cafe_head_on_v0`
  still stood on the *unpaired* table. Its alternative (b) deferred them until
  the largest effect was known to survive. It survived, so the deferral was spent.
- Walked both scenes' 2×2 with the **same** six seeds, temperature, `PairedStep`
  class and resampler (~1m32/scene), recorded them as `WALK_CONVOY_6` /
  `WALK_HEADON_6`, and added `paired_interaction_verdict` — `interaction_verdict`
  graded on CI-separation instead of the `EPS_CLEARANCE` guard constant.

## What worked / what failed

- **Both walks reproduce D-219's published pairs to four decimals** — convoy
  `+0.1968 / −0.0055`, head-on `+0.0806 / −0.0002`. That is what makes this a
  re-reading rather than a second measurement, so what follows is the estimand's
  doing and not a different walk's.
- **The flip does not generalize.** Paired, guard-free:

  | scene | top (`w_risk=40`) | bottom (`w_risk=0`) | verdict |
  |---|---|---|---|
  | crossing | +0.3501 [+0.3181,+0.3936] 6/6 | **−0.0339 [−0.0443,−0.0235] 6/6** | `PAIRED_SIGN_FLIP` |
  | convoy | +0.1441 [+0.0978,+0.1957] 6/6 | +0.0159 [−0.0137,+0.0467] 4+/2− | `PAIRED_CONDITIONAL` |
  | head_on | +0.0606 [+0.0388,+0.0860] 6/6 | +0.0040 [−0.0033,+0.0122] 4+/2− | `PAIRED_CONDITIONAL` |

- **The two unflipped rows lean *positive*.** Not "negative but underpowered" —
  the point estimate is on the other side of zero on both. So the unpaired
  table's negative sign there does not weakly agree with the paired reading, it
  disagrees with it.
- **The top row is what generalizes**: `w_ped` beside the risk term helps on all
  three scenes, 6/6 unanimous, CI clear of zero. The narrowing is not "the 2×2
  dissolved".
- 24 cells, **6/6 completion in every one** — no row's step was bought by a
  robot that stopped moving.

## North-star delta

- One published table narrowed by measurement: `SIGN_FLIP` was a 3-scene claim,
  it is now a 1-scene claim with the other two graded `CONDITIONAL`.
- No planner capability added — this is a result about the risk term's
  behaviour, not new avoidance machinery. Honest reading: the branch's
  substantive claim got **smaller and better supported**, which is progress on
  the "완벽" definition P5 has to pin down, not on the controller.

## Key learnings

- **D-219 flagged this itself and was right.** Its alternative (b) said
  reporting the 3-scene flip as general would repeat D-217's error one level up;
  the negative rows were −0.0055 and **−0.0002 m**. A verdict whose materiality
  test is a tunable constant will call two ten-thousandths of a metre a
  direction. Replacing the threshold with CI-separation removes the knob.
- **A deferral with a stated trigger is cheap to collect.** D-225 wrote down
  exactly what would make the other two scenes worth walking. That made this
  cycle a 4-minute decision instead of a re-derivation.
- The instrument track is genuinely closed: D-233 green across all 8 shards,
  and this is the first capability reading in 25 cycles.

## Recommended next 1–3 priorities

1. **Update `three_arm`'s docstring table** (lines 74–76) — it still prints
   `SIGN_FLIP` on all three scenes as the module's own summary.
2. **Widen the two `CONDITIONAL` scenes past n=6** — at 4+/2− the sign test's
   floor (p=0.688) cannot resolve either way; these are the rows where more
   seeds would actually buy something (unlike the unanimous ones, already at
   the n=6 floor of 0.031).
3. **Refuse `git reset --hard` in the local-only audit (Q-141)** — unchanged.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/paired_step.py, eval/mppi_sandbox/tests/test_paired_step.py, docs/decisions.md
- TSV row appended: pending
