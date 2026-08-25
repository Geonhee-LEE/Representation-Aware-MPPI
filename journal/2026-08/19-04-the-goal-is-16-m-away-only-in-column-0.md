# The goal is 16 m away only in column 0 — the endpoint was always the goal

- **Cycle**: 2026-08-19 04:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `3c0c5d39` [sandbox] sc.goal = [0, -4.5] 인데 8 seed 전부 ~16 m 떨어진 곳에서 끝난다
- **Phase**: P3
- **Status**: keep

## What I tried

- Took the TODO's three hypotheses for why `convoy` seeds end ~16 m from
  `sc.goal = [0, -4.5]` — (1) coordinate order / frame mix-up, (2) episode not
  completing, (3) `goal` is a dead field — and tried to decide between them by
  reading `scenario.load_scenario`, `run.simulate`'s stop condition, and
  `ab.reached_goal`, then dumping trajectories rather than arguing from prose.
- Dumped the endpoint of all 8 seeds on **both** arms (`w_epist` 0 and 200) on
  `cafe_convoy_v0` — 16 closed-loop runs, ~55 s, no new machinery.
- Checked the `max_steps` plumbing (`seed_sweep(**arm_kwargs) → run_arm →
  simulate`) as the candidate mechanism for D-354's 661.5-vs-151.6 step gap.

## What worked / what failed

- **All three hypotheses are refuted, and the answer is a fourth: the
  observation was an artifact of reading the wrong column.** `traj` rows are
  `[t, x, y, yaw, v, ω]` and `ab.COL_XY` is `slice(1, 3)`. The probe reported
  `traj[-1, 0]` as "end_x" and `traj[-1, 1]` as "end_y" — a **one-column
  shift**. So the reported `end_x` 13.7–18.9 is **`t_final` in seconds**, and
  the reported `end_y ≈ 0.04` is the true **x**, which is ≈ 0 exactly as a path
  down the y-axis requires. The arithmetic closes on itself: the same probe
  reported steps 138–190, and 138–190 × `SIM_DT = 0.1` **is** 13.8–19.0.
- **The measured endpoint is the goal.** Over 8 seeds × 2 arms:
  `x ∈ [-0.010, +0.018]`, `y ∈ [-4.479, -4.464]` against `goal = (0, -4.5)` at
  `goal_xy_tol = 0.2`. `reached_goal = 8/8` on both arms is therefore **correct
  and earned**, not the false positive STATE named as "the prime suspect".
- **`sc.goal` is live, not dead code** — it is read twice per run, in
  `simulate`'s stop condition (`dxy ≤ xy_tol` conjoined with `completion ≥
  0.992`) and in `reached_goal`. Hypothesis 3 was checkable statically and is
  simply false.
- **The step gap is bounded but not closed.** My reproduction gives mean
  **131.0** (baseline) / **138.1** (shadow) steps — the same order as D-353's
  151.6 and nowhere near D-354's 661.5. So D-353's configuration is the one
  that reproduces and D-354's is the outlier; the 661.5 remains unexplained,
  but it is now the *anomaly* rather than a reason to suspend D-353.
- **Separate latent finding, not acted on**: `expected_duration_s` is **absent
  from 4 of 9 scenario yamls** — `cafe_convoy_v0`, `cafe_cut_in_v0`,
  `cafe_freezing_v0`, `cafe_head_on_v0` — so each silently inherits
  `load_scenario`'s `30.0` default and a 1200-step cap, while
  `cafe_obstacle_crossing_v0` declares 25 s and gets 1000. The timeout cap
  differs across the scenes this branch compares **by omission, not by design**.

## North-star delta

- **A standing threat to every clearance number on this branch is discharged.**
  The TODO's own framing was that "이 branch 의 모든 clearance 수치가 여기에
  걸려 있다" — if episodes ran only part of the intended path, `min_clearance`
  (a whole-trajectory minimum) would be measuring a different quantity than
  the north star's 경로추종 완주. Measured: the episodes complete. D-352/D-353's
  `+0.1856 m` is taken over a **finished** path.
- **This also clears the precondition the research feed named.** The 00:00 MRPB
  entry made `p_o` (fraction of episode inside `d_safe`) conditional on
  "termination first: `p_o` presumes the episode completes, and STATE says ours
  may not." It does complete — so the time-normalised metric is now unblocked.
- No new controller capability; this is a measurement-validity result.

## Key learnings

- **A derived quantity reported without its units is unfalsifiable prose.**
  "Ends 16 m away" survived two cycles (D-352 discovered it, D-353 re-confirmed
  it) and a Notion TODO because nobody asked *16 m in what*. One `print` of the
  full row killed it. The tell was available the whole time — steps and
  "end_x" differed by exactly the factor `SIM_DT`.
- **Hypothesis lists inherit the framing of the observation that generated
  them.** All three of the TODO's candidates presupposed the endpoint was real;
  none of them was "the endpoint reading is wrong". When the cheap check is
  *re-measure the observable* rather than *explain the observable*, do that
  first — it costs a run and can delete the whole question.
- **A control that fails to reproduce is a claim about the probe as much as
  the tree** (the inverse of D-354's own lesson). D-354 suspended every
  `convoy` magnitude because its control disagreed with D-353. An independent
  third reading now sides with D-353, which is what makes the disagreement
  attributable to D-354's probe rather than to the scene.
- Scenario defaults that are *silently* inherited are a comparison hazard: four
  scenes share a timeout cap nobody wrote down for them.

## Recommended next 1–3 priorities

1. **Declare `expected_duration_s` explicitly in the 4 scenarios that omit it**
   — convoy/cut_in/freezing/head_on currently inherit 30.0 s by accident, so
   the timeout cap this branch compares across differs by omission.
2. **Compute the `p_o`-shaped observable on `convoy`** (fraction of episode
   steps with clearance < `d_safe`, `d_safe` from our own footprint, not
   MRPB's 0.34 m) at the same 8 seeds — the feed's suggested action, now
   unblocked because termination is confirmed.
3. **Widen the `convoy` cross-track result to 16 seeds** — D-353's `cte_rms`
   −12.6 % is 5/8, still the weakest link in the branch's headline.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: journal/2026-08/19-04-the-goal-is-16-m-away-only-in-column-0.md, docs/decisions.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: pending
