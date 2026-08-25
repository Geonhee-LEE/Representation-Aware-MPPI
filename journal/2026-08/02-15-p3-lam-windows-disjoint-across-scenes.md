# No shared `lam` is scene-specific — but no fixed `lam` serves the matrix either

- **Cycle**: 2026-08-02 15:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE claude-actionable **#2** — is no-shared-`lam` scene-specific or general?
- **Phase**: P3
- **Status**: keep

## What I tried

- Gate 1 fired for the **34th** consecutive cycle (queue 6 = #66/#67/#68/#69/#44/#23,
  **20.9 d** since the last merge). Applied the standing precedent for the **ninth**
  cycle: land on **#67, already in the queue** — zero new review bandwidth.
- Swept a 12-rung `lam` ladder at n = 8 on three surfaces: the **centred** hazard with
  `risk_mppi` and with `stock_mppi`, and the obstacle-free **`cafe_straight_v0`** with
  `stock_mppi`. 14:00 had measured only `offset = 0.3`.
- Filled the two holes in 14:00's own ladder on `offset = 0.3` (`lam` 2.5 and 4.0), and
  extended the `cafe_straight` ladder *downward* to 0.05 after the first pass came back
  0/8 everywhere — a ladder that starts too high looks identical to a scene with no
  admissible window.
- Shipped `ab.lam_ladder` / `ab.LamProbe` / `ab.admissible_lams`, the fourth cycle in a
  row to hand-roll this sweep.

## What worked / what failed

- **✅ It is scene-specific — option (c) survives.** The centred variant of the same
  hazard, same controller, is shared-admissible at `lam = 5.0` (**both** arms 8/8), and
  `stock_mppi` there is admissible on **two adjacent rungs** (4.0 and 5.0). So 13:00's
  `lam = 5.0` was not a knife edge, and Q-035's option (c) — retire `offset = 0.3` as an
  ablation surface — is still available.
- **🔴 The obstacle-free baseline is the real finding.** `cafe_straight_v0` has a
  comfortable window (per-seed spread ~**1.2×**) at `lam ≈ 0.2 – 0.4` — roughly **20×
  below** the hazard scenes' 4.0 – 5.0. The windows are **disjoint**, and each scene
  fails the band from the *opposite* side at the other's temperature: at `lam = 0.3` the
  centred hazard sits at ESS ~1.2 of K = 256 (one-hot), at `lam = 5.0` `cafe_straight`
  sits at ~227 (near-uniform). **No fixed `lam` can be admissible across the repo's own
  scenario matrix**, whichever value is picked.
- **✅ My first sweep was wrong and the cheap check caught it.** The 0.8→8.0 ladder said
  `cafe_straight` was 0/8 at every rung, which reads as "another pathological scene". It
  is the opposite — the scene is the *best-behaved* one and the ladder simply started 2×
  above its window. One extra downward pass converted a false pathology into the
  disjointness result.
- **✅ 14:00's claim survives its own gap-fill.** `lam` 2.5 → 0/8, 4.0 → 2/8 on
  `offset = 0.3`. Fourteen rungs now, none admissible.
- **🔴 CI cost is up 60%.** Suite **116 → 125 passed + 1 xfailed**, but **81 s → 130 s**;
  the new file alone is 50 s (6 seed sweeps at n = 8). Still additive — new file, no
  existing assertion touched, **#66 merge recipe unchanged** — but this is the first
  cycle where the sandbox suite got materially slower, and two more files like it would
  put the "seconds, no ROS needed" claim in D-016 under real pressure.

## North-star delta

- **No movement on avoidance or tracking.** Third consecutive cycle spent on measurement
  validity rather than capability.
- The standing caveat is now **strictly larger**, not merely restated. It was "every
  closed-loop number was measured at a bad `lam`", then "on one scene no `lam` works".
  It is now: **the fixed-`lam` protocol cannot be repaired by choosing a better value**,
  because two scenes already in the repo need temperatures 20× apart. Any cross-scene
  ablation table this project publishes is uncontrolled unless `lam` is calibrated
  per scene — which the deferred re-baseline (Q-032) now has to do.
- One thing got **cheaper**: `assert_ess_in_band` could say a comparison ran at a bad
  temperature but not which to use. `lam_ladder` closes that, so per-scene calibration
  is now a call rather than a cycle.

## Key learnings

- **A negative result from a search needs its search bounds justified, not just its
  method.** "0/8 at all twelve temperatures" and "the ladder is in the wrong decade"
  produce identical output. The habit that saved it was checking the *shipped default*
  (`lam = 0.1`) against the ladder's floor and noticing 0.8 was already 8× above it.
- **The scene axis and the seed axis are not independent** — they compose through one
  measurable quantity. A band is reachable when the ESS-vs-`lam` curve crosses it more
  slowly than the seeds scatter. Measured: `cafe_straight` crosses the band's 10× width
  over ~3.7× in `lam` at 1.2× spread (admissible); `offset = 0.3` crosses it over ~1.7×
  in `lam` at up to 18× spread (never admissible). That ratio — not "has obstacles" — is
  what predicts admissibility, and it is a property of the scene's cost landscape, i.e.
  exactly the thing an ablation is supposed to hold fixed.
- **The fourth hand-roll is the reliable signal to move a primitive into `ab`** — same
  count that moved ESS itself at 13:00. Worth treating as a rule rather than a
  coincidence.
- **New open question (Q-036, not filed — see Artifacts).** If `lam` must be calibrated
  per scene, is a cross-scene aggregate (`sandbox:pass=N/M`, collision rate over the
  matrix) meaningful at all, or does every scene become its own separate experiment whose
  numbers may not be pooled? This bears directly on the P5 metric harness and is a
  bigger question than Q-035.

## Recommended next 1–3 priorities

1. **Settle the Q-035 fork** (still STATE #1, still unanswered): widen the band / per-seed
   `lam` / retire `offset = 0.3`. This cycle removed one unknown — the pathology is
   scene-specific, so (c) is viable and is now the cheapest of the three.
2. **File Q-036 and Q-035's answer in `docs/deliberations.md`** — blocked, not skipped:
   #66 and #67 both prepend a *different* Q-017 at the same offset, so any further
   prepend enlarges a hunk the user must hand-resolve. Needs a branch off main after the
   queue drains.
3. **Calibrate `lam` per scene across the whole scenario matrix** using `lam_ladder`, and
   record the per-scene admissible window in the scenario yaml — this is the concrete
   deliverable the re-baseline (Q-032) needs before it can pick temperatures at all.

## Artifacts

- PR: **#67** (existing, pushed in place) — https://github.com/Geonhee-LEE/Representation-Aware-MPPI/pull/67
- Files touched: `eval/mppi_sandbox/ab.py`, `eval/mppi_sandbox/tests/test_lam_admissibility_is_scene_specific.py`, `results/p3-epistemic-shadow-cost-critic.tsv`
- Commits: `5aae268`, `08effc0`
- TSV row appended: yes (`sandbox:pass=125/125`, keep)
- **Not** written: `docs/deliberations.md` (Q-035 answer + Q-036) — deferred per STATE #4,
  #66 conflict set. Pending deliberations backlog is now **2** entries.
