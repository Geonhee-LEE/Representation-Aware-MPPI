# The epistemic ablation had already been run — it is the shipped default

- **Cycle**: 2026-08-02 23:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE claude-actionable **#1** — ablate `w_epist` on the crossing scene
- **Phase**: P4 (work is P3 carry-over)
- **Status**: keep

## What I tried

- Took STATE #1, the item STATE called "the only surviving test of the *mechanism*
  rather than a correlate". Its premise: "the epistemic channel is the only term
  `risk_mppi` has that `stock_mppi` does not."
- Before spending a ladder on it (64 sims), checked what the shipped defaults
  actually are. `RiskMPPI.__init__` defaults `w_epist=0.0`; `calibrate_lam.main`
  passes no arm kwargs.
- Then measured whether the term is even *live* on `cafe_obstacle_crossing_v0` —
  per-control-step spread of the shadow cost across rollout samples, 1 sim.
- Registered two predictions, then ran a two-directional controlled intervention
  on the rollout horizon (D-018 protocol).

## What worked / what failed

- 🔴 **Both halves of the premise are wrong, neither needed a simulation.**
  Every window in `lam_windows.yaml` — including the crossing-scene separation
  (`stock [0.4,0.8]` vs `risk [1.6,3.2]`) that D-017→D-020 spent four cycles on —
  was measured with `w_epist = 0`. **No separation result in this repo is
  evidence about the epistemic channel.** The term that actually differs is
  `w_risk = 40.0` on the DYNAMIC channel, which the premise never named.
- 🔴 **Switched on, the term is signal-free, not merely inert.** At the shipped
  `H = 30` the per-sample spread is **exactly 0 at all 92 steps**. A constant
  cancels in the softmax exactly, so *no* weight would bite: `w_epist` 200 vs 0
  is **byte-identical on 4/4 seeds**, with `w_risk` shipped or zeroed. This is one
  rung more degenerate than the 11:00 `offset=0.3` mode (spread 197, still
  bit-identical) — there the term priced samples and lost; here it never speaks.
- ✅ **The grid is not empty** — 5.7–23.6 % of cells carry σ = 1 (mean 12 %). So
  "nothing rendered" is not the explanation. The field is there and out of reach.
- ✅ **Rollout reach is the gate, confirmed in both directions.** (A) crossing,
  `H` 30→60: live steps **0/92 → 121/240**, spread 0 → 1512. (B) the known-live
  `offset=0.3` scene, `H` 30→20→10: spread **196.49 → 11.36 → 0.00**, monotone to
  exactly zero. Running only (A) would have shown a knob that wakes the term, not
  that it is *the* knob.
- 🔴 **My own scalar summary of that gate failed its own test.** "Live iff max
  rollout reach ≥ distance to nearest unseen cell" is false: it holds on **28 of
  92** crossing steps where the spread is still exactly zero. Rollouts reach far
  *along* the path; shadows sit lateral to and behind the actors. Pinned as a
  test so no future screen is built on the distance scalar.

## North-star delta

- **No capability movement — fifth consecutive methodology cycle.** But this one
  invalidates a claim rather than refining one: the epistemic channel, the P3
  headline, has **never been measured in any window this repo reports**.
- Scenes able to contribute an avoidance number: **5**, reportable: **4** —
  unchanged. No tracking metric improved.
- The P3 axis now has a stated precondition it never had: a scene can only test
  the epistemic channel if the rollout cone intersects σ > 0. Cheap to screen for,
  and it is checkable before spending sims.

## Key learnings

- **Check what the default *is* before designing an ablation of it.** Four cycles
  of window work read as epistemic-channel evidence and none of it was. One
  `inspect.signature` call would have caught it at any point.
- **"Inert" is not one failure mode.** Signal-free (spread ≡ 0 ⇒ exact softmax
  no-op, unscalable) and active-but-dominated (spread large, homotopy wins) need
  different fixes — the first is a reach problem, the second a cost-landscape one.
  Only the second responds to weight tuning.
- **The scene named after its obstacles has the matrix's shortest epistemic
  reach**, because `target_speed_mps: 0.3` was chosen to "give MPPI room to
  dodge". A knob picked for one purpose silently gated a whole channel.
- **A causal claim needs the kill direction too.** (B) is what separates "reach
  gates the term" from "the crossing scene happens not to apply".

## Recommended next 1–3 priorities

1. **Directional reach screen over all 8 scenes** — rollout cone × σ-field
   intersection, in the spirit of `exposure.py`. Zero simulation, needs no merge,
   and it answers "which scenes can hear the epistemic channel at all" before any
   more sims are spent on ones that cannot. Must carry direction, not distance
   (D-021 clause 4).
2. **Q-043: `(w_epist, horizon)` 2×2** on the blind-corner scene — separates the
   epistemic contribution from the horizon extension that makes it audible.
   Gated on #68/#69 merging.
3. **Stamp `lam_windows.yaml` with the arm kwargs it was generated under.** The
   table is currently self-describing only by CLI inspection; a test now pins that
   property, but recording it is the durable fix.

## Artifacts

- PR: #67 (already open — landed in place, zero new review bandwidth)
- Files touched: `eval/mppi_sandbox/tests/test_epistemic_reach_gate.py` (new),
  `docs/decisions.md` (D-021), `docs/deliberations.md` (Q-043),
  `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV row appended: yes
