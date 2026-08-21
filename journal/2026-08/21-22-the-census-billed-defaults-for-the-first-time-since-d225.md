# The census billed `defaults` for the first time since D-225

- **Cycle**: 2026-08-21 22:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — carried; the obligation was again the strand, not the pick
- **Phase**: P3
- **Status**: in_progress

## What I tried

- Phase 1 Step 0 returned `rc=1` for the second consecutive cycle: **two**
  stranded journals now (20:00 and 21:00), three commits ahead of `origin`, one
  tree never graded. The 21:00 cycle spent a full 22-minute suite to discover
  *why* the strand would not clear — `3982 passed, 3 failed`, all three in
  `test_default_lam_sites.py` — and correctly declined to push red.
- So this cycle's scope was exactly one thing: make the three census pins true.
  `cycle_wallclock review` said the 21:00 run had 31m27 and still did not
  publish, i.e. cut scope — so I cut everything except the repair.
- Read the four new sites rather than re-pinning blind. `test_collision_knee.py`
  contributes `_cost_at` (`simulates=False`) plus three sim-backed tests.

## What worked / what failed

- **The repair direction was the real decision, and the file's own history
  argues both ways.** D-124/D-167 repaired entrants by *naming the rung* and
  recorded a nil bill on `defaults`; D-225/D-234/D-264/D-265/D-266 accepted the
  drift and re-pinned. The tiebreak here is semantic: D-410's measured claim is
  what the shipped configuration does when *only* the collision knee moves, so
  naming an off-default `lam` at those three sites would have made them measure
  a temperature the journal's 2-scene × 3-margin × 3-seed walk never ran at.
  Re-pinning is the honest direction; naming would have bought a prettier
  census by falsifying the arm.
- **`_cost_at` is a stronger inert-allowlist member than the three already
  there.** Those never use the rung; this one *cannot* — it calls `ctrl._cost()`
  directly and `lam` is the softmax temperature applied to that function's
  output. There is no path from the code under test to a temperature.
- **The margin narrowed for the first time in nine cycles: 38 → 34.** Every
  entrant since D-383 widened it from the `decides` side, and six consecutive
  cycles of that had been read in the docstrings as "compliance is now the
  habit". D-410 is a counterexample: entrants arrive silent about their rung
  when the module's subject *is* the shipped configuration. That is not a
  compliance regression, and the pin comment now says so explicitly rather than
  letting the next reader infer a backslide.
- **The allowlist's stated property is what failed.** Its docstring says a new
  inert entrant "has to be added here in the same commit". D-410's commit added
  the site and not the entry — which is the mechanism working (it went red) but
  also the reason the branch lost two cycles.
- **`census_preempt` read CLEAN again and again could not have helped.** Its
  `UNCOVERED` line names `inert_surface pins` and three others; the `lam`-sites
  census is in the *covered* five, but it re-derives from source and the pins it
  compares against are the literals I was editing — so it goes green the moment
  the edit is consistent, which is after the fact, not before.
- **`inert_surface staged` returned `STAGED_MOVED` (5 pins).** Under D-315's
  order this is a price, not a failure: every REPORT write lands before the
  receipt, so the tree the suite grades is the tree that ships.

## North-star delta

- **No movement on the robot.** This is pure verification-surface repair — not
  one line of controller or representation code changed.
- **But it unblocks a real result.** D-410's finding (achieved clearance tracks
  the priced knee 1:1; `min_distance_to_obstacle` goes 6/6 green at 0.30 m; the
  arm's first all-seven-checks pass on `cafe_obstacle_crossing_v0` seed 0)
  has been finished and unshippable on disk for two cycles. Clearing the strand
  is what lets it reach CI.

## Key learnings

- **A red strand costs two cycles minimum, and the second one is avoidable.**
  The 21:00 cycle spent 22 min of suite to *learn* the failure; a `-k`-free run
  of `test_default_lam_sites.py` alone costs **51 s** and would have named all
  three failures. When `stranded` reports an ungraded tree, run the census file
  first and the suite second — the census is where this package's own drift
  lands, thirteen-plus cycles running.
- **"Which repair" is a semantic question the count cannot answer.** Both
  repairs make the pins green. Only one keeps D-410's measurement true. A
  future cycle re-pinning under time pressure should read the entrant's subject
  before choosing, because the cheap repair (name a rung, keep `defaults` nil)
  is the wrong one whenever the module's whole point is the shipped default.

## Recommended next 1–3 priorities

1. **Push and let CI grade it** — the branch carries D-409/D-410/D-411 and PR #67
   is already open, so this adds no review load.
2. **`cafe_cut_in_v0` fails `goal_reached` at every margin** (D-410) — a second,
   independent blocker that no knee setting touches. That is the next real
   thrust.
3. **Consider a cheap `stranded`-time census probe** so an ungraded-tree strand
   costs 51 s to diagnose instead of a 22-min suite.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/tests/test_default_lam_sites.py, docs/decisions.md, journal/2026-08/21-22-*.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: yes
