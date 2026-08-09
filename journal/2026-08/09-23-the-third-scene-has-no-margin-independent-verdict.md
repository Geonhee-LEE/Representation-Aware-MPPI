# The census closes at 0/3 — and the one scene that can be re-graded has no margin-independent verdict

- **Cycle**: 2026-08-09 23:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — walk `cafe_obstacle_crossing_v0` at `w = 250`, λ = 0.8, both arms, seeds 0–31
- **Phase**: P5
- **Status**: keep

## What I tried

- Spent the 64-run walk D-163 bought the right to spend: `cafe_obstacle_crossing_v0`,
  the one rung `crossing_screen` grades `TRANSPLANTS` (`w = 250`), at the band's
  own λ = 0.8, the scene's own margin 0.30 m, seeds 0–31 per arm. ~2 min of sim.
- Graded it through the existing objects — `reproduction_at` / `MarginSweep` /
  `censoring_direction` — rather than a new primitive, then swept every
  threshold the 64 recorded clearances can express.
- Added `margin_decides` + `margin_verdict_counts`: whether a rung's verdict
  survives the choice of threshold at all.

## What worked / what failed

- 🟢 **The walk is fully admissible** — 64/64 reached goal, 64/64 weighted
  inside the ESS band. The screen's licence held: this is a real operating
  point, not a number `assert_ess_in_band` would refuse.
- 🔴 **The third scene is a third dead end, and the census closes at 0/3.**
  `NO_HEADROOM_SAFE`, both arms at a `FLOOR`, `FLOOR_CENSORED` in both blocks —
  convoy's failure mode exactly. All three eligible scenes (D-159) are now
  measured and **not one admits a two-sided rung at its declared margin**. The
  successor question's population is exhausted; this is its honest close.
- 🟢 **But crossing's dead end is the first *repairable* one.** Its arms overlap
  by **0.1866 m** where convoy's are disjoint (−0.0198 m) and the band's
  tightest rungs overlap by 7.6/9.9 mm. Its sweep finds **46** two-sided
  thresholds over [0.9712, 1.0906] — the first non-empty two-sided window ever
  recorded outside the published band. Re-grading can finally be *asked*.
- 🔴 **Asked, it does not answer.** Over those 46 thresholds the rung reads
  `SIGN_REVERSED` **15** / `NO_SEPARATION_TO_REPRODUCE` **14** /
  `NOT_REPRODUCED` **10** / `REPRODUCED` **7** — four verdicts, no majority,
  and the mechanism's own direction the **rarest**. The modal outcome of
  re-grading is *the two seed blocks separating in opposite directions*. There
  is no margin-independent verdict here to be flattered by a good threshold.
- 🟢 **`margin_decides` is not a rename of `MarginSweep.held`, and the test says
  why.** `held` is 14/46 — but the recorded verdict *is* the vacuity one, so
  `held` counts margins agreeing that there was nothing to reproduce, while the
  other 32 disagree with each other too. Read alone it would look like a 30%
  stability fraction. Pinned by a test computing both.
- 🔴 **Convoy's 32-against-32 clearance separation does not carry.** On crossing
  the same two arms are tied — means 1.0229 (stock) vs 1.0211 (risk) — with the
  **risk arm marginally worse**. The repo's widest mechanism separation is a
  one-scene fact.
- 🟡 `MARGIN_INERT` is reachable but no shipped scene produces it, so it is
  proved by a synthetic sweep. My first synthetic was wrong — a monotone 0..31
  ramp gives two seed blocks that do not overlap *each other*, so `two_sided`
  was empty and the corner untested. `i % 16` fixed it; the reason is now a
  comment, since it is the same trap a future author would hit.

## North-star delta

- **Zero movement in the safety headline, and this cycle is the one that says
  the headline may not be reachable this way.** `unsafe_rate` **0.0000** /
  `min_clearance` **0.3579** / `success_rate` **1.0000**, unchanged. On all
  three eligible scenes every run clears its declared margin by a wide margin,
  so the statistic the branch reports has no room to move on any of them.
- The census is a **negative** result and it is worth its cost: it closes a
  question that had been open since D-157 rather than leaving it to be
  re-derived a fourth time.

## Key learnings

- **A single declared margin cannot be read as *the* result on a scene whose
  verdict is margin-dependent.** Crossing is the first case where this is
  demonstrable rather than a worry, because it is the first scene with enough
  arm overlap for the question to be well-posed.
- **"Repairable" and "repaired" are different findings.** Two cycles established
  that head_on and convoy cannot be re-graded into a two-sided test. The natural
  next inference — that a scene which *can* be re-graded would yield one — is
  now measured and false.
- **The clearance-separation result was scene-specific.** Any future claim built
  on convoy's disjoint arms needs a second scene before it generalizes; this one
  supplies the counter-example rather than the confirmation.
- The feed's 2026-08-09 20:00 entry (uncertainty as a risk signal, r = 0.108)
  is now less dismissible than its single-author workshop provenance suggested:
  this cycle independently finds the risk arm *not* safer on the third scene.

## Recommended next 1–3 priorities

1. **Ask whether the declared margins are the instrument at fault** — all three
   scenes are `FLOOR`/`CEILING` censored, i.e. every declared margin is either
   far below or far above what the arms produce. A margin chosen *from* the
   recorded clearances is the only route left to a scorable comparison.
2. **Run the feed's one-variable ablation** (2607.16591): a plain min-lidar
   term in the same slot as the epistemic term, same scenes, same seeds. The
   negative result above makes this cheap to motivate and it is directly
   sandbox-runnable.
3. **Re-measure the `w = 250` crossing cell at 16 seeds** — this walk's licence
   still rests on an 8-seed table row (carried from D-163, unaddressed).

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/scene_transplant.py, eval/mppi_sandbox/tests/test_scene_transplant.py, docs/decisions.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: pending
