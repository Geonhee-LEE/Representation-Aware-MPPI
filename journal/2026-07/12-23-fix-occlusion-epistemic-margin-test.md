# Occlusion epistemic-margin test: red CI fixed, D-013 closed-loop inertness confirmed and recorded (Q-017)

- **Cycle**: 2026-07-12 23:00 KST
- **Branch**: `autoresearch/p3-fix-occlusion-epistemic-margin-test`
- **TODO**: `39ac5d39` [sandbox] risk_mppi epistemic margin occlusion 실패 테스트 수정
- **Phase**: P3 (executed during P4 window — P0 red-CI fix takes precedence)
- **Status**: keep

## What I tried

- Reproduced the red test on main: `test_epistemic_margin_widens_berth_in_occlusion_geometry` — k=0.4 vs k=0.0 clearances identical to 1e-12 (0.00788 m both).
- Instrumented the sim: with k=0.4 only **0.04 % of rollout points ever receive margin > 0** (max 3.1 % in a single step); max trajectory perturbation 0.9 mm.
- Probed the σ field directly: shadow rendering and `RiskInflationCritic.margin` are contract-correct (σ=1 in shadow, margin=0.4 there, 0 on visible flank). The mechanism, not the wiring, is inert.
- Ran a two-disc occluder-pair geometry designed to favor the mechanism (hidden disc behind an on-path occluder, B_y ∈ {-2.5, -2.7, -3.0} × seeds {0,1}): gain = +0.0000, +0.0000, +0.0109/-0.0176 (noise-signed).
- Replaced the closed-loop test with a rollout-cost contract test (`test_epistemic_margin_prices_shadowed_corridor`): shadowed hover rollout must cross the collision threshold only under k·σ (cost gap > w_collision), visible-flank rollout must cost exactly the same. Removed now-unused `min_clearance` import.
- Recorded the negative result as **Q-017** in `docs/deliberations.md`.

## What worked / what failed

- Root cause is structural, not a bug: **horizon-visibility race**. Rollouts (~1.2 m lookahead at 0.4 m/s) only reach the occlusion shadow after the robot has committed to the visible side, and the shadow rotates off-path as it swerves. In a disc world, "where the robot goes next" ≈ "what it can currently see", so σ-at-rollout-point margin against *known* obstacles almost never binds.
- The test's expectation was wrong for the mechanism: global min-clearance is achieved beside the obstacle where σ=0 by construction — k·σ cannot widen a visible graze, ever.
- New contract test passes deterministically; full suite **57/57 green** (was 30/31 + 1 fail).

## North-star delta

- Sandbox CI on main goes red → green: the D-016 primary verification surface is trustworthy again for every future PR.
- Negative knowledge: the D-013 epistemic consumption path, as implemented, does **not** contribute to the '가려진 obstacle' class of the north star in closed loop. Claiming it did would have been false; Q-017 now scopes what replaces it.

## Key learnings

- Margin inflation on known obstacles and pricing entry into unknown space are different mechanisms; occlusion response needs the latter (additive `w_epist·σ` cost, σ(x,u) action-conditioned query, or speed modulation — Q-017 trade-off).
- Closed-loop "moves the needle" tests need a measured effect size before being enshrined in CI; mechanism-level cost-contract tests are the robust tier below them.
- The two-disc experiment matters as much as the fix: it rules out "just pick a better geometry" as a rescue for the current mechanism.

## Recommended next 1–3 priorities

1. **Sandbox additive epistemic shadow-entry critic** (`w_epist`·σ additive cost, same GT BEV channel) + closed-loop A/B vs k·σ margin — answers Q-017 (a); Backlog TODO created.
2. Create the queued `[research]`-prefixed Notion TODOs (STATE claude-actionable #1) — now feasible with `notion-create-pages` granted.
3. P4-T02 Gazebo dynamic scenario YAML v1 (5/10/20 actor density) — P4-lane progress, no P2 dep.

## Artifacts

- PR: pending merge (autoresearch/p3-fix-occlusion-epistemic-margin-test)
- Files touched: eval/mppi_sandbox/tests/test_risk_mppi.py, docs/deliberations.md
- TSV row appended: yes
