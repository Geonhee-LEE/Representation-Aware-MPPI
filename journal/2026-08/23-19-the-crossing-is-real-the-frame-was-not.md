# The crossing is real — the frame the bearing was read in was not the robot's

- **Cycle**: 2026-08-23 19:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: Q-190 — is `cafe_obstacle_crossing_v0` a fair test bed for lateral avoidance?
- **Phase**: P5
- **Status**: keep

## What I tried

- **Reading A (zero sim)**: read every actor's course straight out of the
  scenario yaml and measured `|c_hat . t_hat|`, its share along the reference
  path tangent. This settles Q-190 option (a) — "the scene named crossing never
  crosses" — without touching the simulator.
- **Reading B (the same 32 logged runs, ~20 s)**: predicted D-446's
  `bearing_tangent_frac` from the **velocities alone**. For two constant-velocity
  bodies the range is stationary exactly when the separation is orthogonal to
  the relative velocity, so at closest approach `|u . t_hat| = |v_rel x t_hat| /
  |v_rel|` — a quantity that knows nothing about where either body is.
- Measured the identity's **precondition** directly (`cpa_orthogonality =
  |(h-p)_hat . v_rel_hat|`, exactly 0 at a true closest approach) rather than
  inferring it from the residual, so a failure could be attributed.
- New module `eval/mppi_sandbox/crossing_geometry.py` + 11 unit tests. Zero
  controller lines changed; zero new scenarios.

## What worked / what failed

- **(a) is refuted exactly.** All five actors run `|c_hat . t_hat| = 0.0000` at
  0.75 m/s, dead perpendicular to the path. The scene crosses as named, so the
  four null lateral sweeps on it (D-430 / D-433 / D-440 / D-446) are statements
  about the controller, not artefacts of the yaml.
- **The identity first came out UNEXPLAINED, and that was the useful part.**
  Measured 0.956 / 0.929 against a prediction of 0.750 / 0.743 — a **one-sided**
  +0.2 residual on all 32 seeds. Not scatter; a bias.
- **The precondition ruled out the obvious culprit.** `cpa_orthogonality` is
  0.006-0.133 (mean 0.044 / 0.051): the deciding instant genuinely *is* a
  stationary point of the range, so (CPA) applies and the instant is not at
  fault. Measuring the precondition instead of inferring it is what made this
  step one command rather than one cycle.
- **The gap is a frame difference.** D-446 reads the bearing from the **foot**
  on the reference path — correct for its own identity `gain = -d . u`, which is
  an expansion about the foot. (CPA) is about the **robot**. Read from the robot
  the same 32 instants give **0.741 / 0.729** against the predicted 0.750 /
  0.743: mean |gap| 0.030 / 0.035, max 0.096, **KINEMATIC on 16/16 seeds in both
  arms** at bands 0.10 and 0.20 (PARTIAL at 0.05).
- **My own a-priori number was wrong and the measurement caught it.** I wrote
  `0.75/hypot(0.75, 0.3) = 0.928` into the docstring from the yaml's
  `target_speed_mps: 0.3` and noted it matched D-446's 0.929 "to three
  decimals". The robot actually runs at **0.70-0.80 m/s** in these runs, so the
  agreement was a coincidence between a wrong prediction and a
  differently-framed measurement. The docstring is corrected to the measurement.

## North-star delta

- **A published magnitude is corrected, and its verdict's margin shrinks.**
  D-446's "the hazard sits essentially on the path ahead" is a foot-frame
  reading; the encounter's own figure is **0.73**, just above the isotropic
  split 0.707, not near 1. D-446's ladder (0.50 / 0.707 / 0.85) returned TIMING
  at all three rungs; against robot-origin values (range 0.622-0.816) the
  **0.85 rung would carry no tangential votes at all**. TIMING survives at the
  two lower rungs — it is not overturned — but on a smaller margin than the
  0.956 advertised.
- **The geometry is shown to generalise off this scene.** The identity contains
  no scene, so "tangential bearing at closest approach" is a property of any
  crossing where the actor is the faster body. That is what licenses carrying
  D-446's lever call to future scenarios instead of re-measuring per scene.
- No metric on the acceptance matrix moved: this is a measurement-validity
  cycle, not a controller cycle.

## Key learnings

- **Two correct readings in different frames are not comparable, and nothing in
  either one says so.** Both `avoidance_budget`'s foot bearing and this module's
  robot bearing are right for their own identity. The error would have been
  silent — the numbers are the same *type* and differ by a plausible-looking
  0.2. Pinned with a test in both directions (on-path they coincide; off-path
  the foot reading is strictly larger).
- **Measure a precondition, do not infer it.** `cpa_orthogonality` cost one dot
  product and converted "UNEXPLAINED, cause unknown" into "the instant is fine,
  look at the frame" inside the same 20-second run.
- **A prediction written before the measurement earns its keep by being wrong.**
  Had I only computed the measured side, the 0.2 bias would have read as
  agreement with D-446 and nothing would have been found.
- **`target_speed_mps` in the yaml is not the speed the robot runs.** 0.3
  declared, 0.70-0.80 observed. Anything deriving a number from the declared
  value is deriving it from a value the sim does not honour — worth a follow-up.

## Suite: red once, repaired, re-run

- First recorded suite: **4158 passed, 1 failed** (1451.77s, 14 shards). The
  single red was `test_lam_dependence::test_two_sites_are_not_tests_and_neither
  _bills_a_sim` — `crossing_geometry.measure_arm` is the **eighth** non-test lam
  site, the fifth consecutive reading-module to enter.
- `census_preempt` caught the *other* drift at the stage (`lam_site_census`
  95 → 96, ~2 s) but not this one, and not the two pins derived from it
  (`weighting_at_shipped`, `decides - defaults`), which went red **after** a
  clean pre-empt pass. Q-183's eighth data point, and the second cycle running
  where the cost landed exactly in the pre-empt's own `UNCOVERED` line.
- D-446's comment instructed the next reading-module cycle to take **option
  (c)** instead of absorbing again. It was not taken, and the reason is a real
  conflict rather than a shortcut: the file states (c)'s trigger **twice** and
  the two disagree — the older one (sim-billing **and un-recordable**) does not
  fire here, the newer one (fifth consecutive reading-module) does. Filed as
  **Q-192**. Implementing (c) moves the `exemption_registry` census, which is
  its own cycle's work.
- Chose repair + second suite over a deliberate strand: the repair is a literal
  with a 85 s standalone verification, so ~25 min of *this* cycle is cheaper
  than the ~35 min of the *next* one that 17:00's strand cost 18:00.

## Recommended next 1-3 priorities

1. **Re-take D-446's lever ladder in the robot frame** (same 32 runs, no new
   sim). D-446's TIMING rests on foot-frame values; the robot-frame range
   0.622-0.816 straddles its own 0.85 rung. One re-scoring says whether the
   verdict is band-stable in the frame the physics is stated in.
2. **Q-191: why does the robot run at 0.70-0.80 m/s when the scenario declares
   `target_speed_mps: 0.3`?** Every scene-derived expectation on this branch is
   computed from the declared value.
3. **Q-192 — delete one of option (c)'s two conflicting triggers**, then decide
   with Q-183 whether the non-test lam site list should be *derived* rather than
   listed. Both are now eight-data-point problems and they share a prescription.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic, PR #67)
- Files touched: eval/mppi_sandbox/crossing_geometry.py, eval/mppi_sandbox/tests/test_crossing_geometry.py, docs/decisions.md, docs/deliberations.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: yes
