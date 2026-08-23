# The deviation goes sideways — Q-189 answers TIMING, unanimously

- **Cycle**: 2026-08-23 17:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `Q-189` deviation decomposition — where does the excursion go?
- **Phase**: P5
- **Status**: keep

## What I tried

- Built `eval/mppi_sandbox/avoidance_budget.py`: partition the excursion at the
  closest-approach instant against the **hazard bearing** rather than the path
  frame. With `d = p - f` and `u` the unit foot→hazard bearing,
  `away = -d·u` is the only part that buys clearance at first order and
  `away² + slide² == deviation²` is an exact partition.
- Reported `bearing_tangent_frac = |u·t̂|` — how much of the *bearing* lies
  along the path tangent. This is the non-degenerate path-frame question, and
  it is what separates STATE's two candidate levers.
- Took the reading over the existing 32 runs (2 arms × 16 seeds). **Zero new
  sim** beyond re-integration; no controller or cost source touched.
- 16 unit tests pinning the partition identity, the sign convention, and
  agreement with `avoidance_aim` on both index and `gain`.

## What worked / what failed

- **Q-189 answers TIMING, and it is not close.** `bearing_tangent_frac` = 0.956
  / 0.929 mean across arms, **range 0.800–1.000** — the hazard sits essentially
  *on the path ahead* at the deciding instant in all 32 runs. Verdict is TIMING
  at all three bands (0.50 / 0.707 / 0.85) in both arms; the only band that
  even splits is 0.85 in the `w_heading=32` arm (13/16), still TIMING.
- **Where the metres go, stated directly**: `slide_frac` = 0.956 / 0.929, and
  `corr(deviation, slide)` = **+0.995 / +0.991**. Essentially every additional
  metre of excursion lands in the component orthogonal to the hazard bearing.
  Meanwhile `corr(deviation, away)` = **−0.870 / −0.926**: the *bigger* the
  excursion, the *less* of it points away. `away` is outright negative in 2/16
  and 4/16 seeds — those swerve toward the hazard.
- **D-445's saturation is reproduced from geometry with no controller in the
  loop.** A test pins it: sliding `d` across a bearing of length `R` buys
  exactly `√(R²+d²) − R`, i.e. second-order. That is why 8× the deviation does
  not buy 8× the clearance, and why `gain` sat penned at 0.07–0.19 m.
- **The literal Q-189 framing was vacuous and is now pinned as such.** STATE
  asked for a tangent/normal split *of the deviation vector*; `foot_points`
  returns the nearest point, so `d ⊥ t̂` by construction. Measured
  `tangent_frac = 0.00e+00` in both arms. Pinned in a test so no future cycle
  re-derives it.
- **Census cost, and one clean catch**: `census_preempt` named the
  `lam_site_census` drift (`defaults` 94→95) **at the stage, for ~2 s**. Its
  two derived pins — `weighting_at_shipped` 73→74 and `decides−defaults` 12→11
  — are in its own `UNCOVERED` set and went red *after* a clean pre-empt pass.
  Repaired here, but that is the sixth data point for Q-183.

## North-star delta

- **The bottleneck's dichotomy is resolved, and the surviving lever is named**:
  not actor prediction, but the reference path's **time parameterisation**. On
  this scene the robot and the actor are on a collision course *along the path*,
  and lateral avoidance is structurally the wrong axis — no cost weight on a
  path-normal excursion can fix a tangential encounter.
- This retires cost-side tuning for `cafe_obstacle_crossing_v0` on principled
  grounds rather than by exhaustion: D-430 (`w_speed`), D-433 (`w_omega`),
  D-440 (`w_heading`) all failed, and the geometry now says why they had to.
- No controller/cost source changed; no metric moved. 32 integrations, ~20 s.

## Key learnings

- **A decomposition is only informative in a frame the quantity is free to move
  in.** The path frame was fixed by construction; the bearing frame was free.
  The same 32 runs answered nothing in one frame and answered decisively in the
  other, at identical cost.
- **The second-order term is the whole saturation story.** `gain` never had to
  be small because the controller was weak — sliding orthogonally buys
  `√(R²+d²) − R` and nothing else. That is a geometric ceiling, not a tuning
  gap, and it explains four cycles of null sweeps at once.
- **`census_preempt`'s `UNCOVERED` line is not a footnote.** It read CLEAN on
  the two pins that then went red. Six data points now (D-317/344/436, 11:00,
  15:00, this cycle); the fix is derivation, not a longer list.

## Recommended next 1–3 priorities

1. **Q-189 follow-through — is the encounter tangential *by scenario design*?**
   Measure the actor's crossing angle relative to the path in
   `cafe_obstacle_crossing_v0`. If the actor crosses nearly along the path,
   the scene is a *speed* conflict wearing a crossing scene's name, and the
   fair test for lateral avoidance is a different scenario.
2. **Speed-axis arm** — the first lever this reading actually licenses: an arm
   that modulates reference speed (slow/stop) rather than lateral offset, on
   the same 16 seeds. Directly falsifiable against the 0.14 m gain ceiling.
3. **Q-183 — derive `census_preempt`'s coverage.** Sixth data point this cycle,
   and the two that bled are in its own printed `UNCOVERED` list.

## Artifacts
- PR: #67 (existing — D-140, no new branch, no new PR)
- Files touched: `eval/mppi_sandbox/avoidance_budget.py`,
  `eval/mppi_sandbox/tests/test_avoidance_budget.py`,
  `eval/mppi_sandbox/tests/test_default_lam_sites.py`
- TSV row appended: yes
