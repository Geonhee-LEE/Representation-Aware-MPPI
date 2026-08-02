# The sampler was never listening: lam=0.1 makes MPPI a greedy argmin picker

- **Cycle**: 2026-08-02 12:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic` (PR #67, in place)
- **TODO**: STATE claude-actionable **#1** — sweep `lam` on the `offset=0.3` scene
- **Phase**: P3
- **Status**: keep

## What I tried

- Gate 1 fired for the **31st** consecutive cycle (queue 6, 20.9 d since #64,
  deadlock-breaker still 0 candidates, escalation floor 08-03 22:01). Applied the
  now-sixth-consecutive precedent: write into a PR **already in the queue**, costing
  zero new review bandwidth.
- Took STATE item **#1**, which this file called *"the single most valuable open
  thread"*: does `w_epist` become non-inert on the `offset=0.3` geometry as the softmax
  de-concentrates? Instrumented ESS = 1/Σw² directly off the weights the controller
  used, swept `lam ∈ {0.1, 0.3, 1.0, 1.2, 1.5, 2.0, 2.5, 3.0, 10, 30, 100}` × geometry
  ∈ {0.0, 0.3, 0.6}.
- Re-ran the paired direction sweep at the in-band temperature, n=24, with the
  completion and speed-match guards from `ab`.

## What worked / what failed

- **🔴 The shipped baseline is degenerate.** At `lam = 0.1`, median ESS is **1.01 of
  K = 256**. `exp(-(cost-min)/0.1)` against costs spanning ~1e4 units underflows every
  weight but the argmin's, so `U += Σ w_k·noise_k` reduces to `U += noise[argmin]`.
  256 samples are drawn and **one** is used. This is a *second* baseline defect beside
  Q-032's raw-noise update, and it is not risk_mppi-specific — it applies to every
  controller in the registry.
- **🔴 11:00's homotopy-indifference explanation is superseded.** Raising `lam` to 1.2
  puts the `offset=0.3` scene at ESS 46 (inside the Q-026 band 12.8–128) with **no
  scene change whatsoever**, and the arms that were bit-identical on **24/24** seeds
  now differ on **every** seed. The term was not failing to bridge a decided homotopy.
  It was not being weighed at all. An additive cost is audible to a one-hot softmax
  only when it flips the argmin — which is exactly why it registered on the one
  geometry where the argmin was contested.
- **✅ But the direction still does not follow, and that is now a stronger result.**
  At `lam = 1.2`, n = 24, paired on `offset=0.3`: **10 farther / 5 closer / 9 tied,
  two-sided sign p = 0.30**, median Δclearance **0.0 m**, both arms complete every seed,
  speed-matched **0.98×**. Q-017 (a) is *audible and non-directional* — a cleaner
  refutation than 11:00's, because it is no longer confounded with a sampler that
  discards the term.
- **✅ The claim is bounded.** `offset=0.6` stays bit-identical at `lam=1.2` with the
  sampler fully able to hear the term. Temperature explains the 0.3 m case, not all of
  them.
- **🔴 Caught by our own doctrine**: `lam=30` drives ESS to ~225/256 (near-uniform ⇒
  `U += mean(noise) ≈ 0`) and the term goes inert again — a tidy two-sided audibility
  window. **But neither arm reaches the goal there**, so `ab.assert_all_reached` rules
  those runs inadmissible. The window is a real-looking observation with no admissible
  measurement behind it. Recorded as Q-034, *not* asserted.
- **✅ The admissible temperature is scene-dependent.** `lam=1.2` → ESS 46 at
  `offset=0.3` but **5.4** at `offset=0.0`. Moving one obstacle 0.3 m changes which
  temperatures are admissible at all.

## North-star delta

- **Negative-but-load-bearing, and it reaches past P3 into the baseline.** No new
  capability. But every closed-loop number this project has produced — #67, #68, #69,
  the Q-027/Q-028 rescope tables — was measured on a controller using 1 of its 256
  samples. That is not MPPI; it is random shooting with a 256-wide draw.
- Q-017 answer (a) moves from *"closer to refuted"* to **refuted at an admissible
  temperature**, which is the version that actually settles it.
- Suite **84 → 94 passed + 1 xfailed**; 10 tests, new file, no existing assertion
  touched → the `#66→#67` merge recipe is **unchanged**.

## Key learnings

- **"The term has no effect" had two candidate causes and we picked the wrong one
  twice.** 07-13 said *no signal to redistribute*; 11:00 refuted that and said
  *homotopy indifference*; both were properties attributed to the **scene** when the
  cause was a **controller hyperparameter**. The cheap tell was available the whole
  time — ESS is one line off the weights already being computed.
- **A tuning knob that decides which cost terms are audible is not a tuning knob.**
  This is Q-024 answered from the measurement side: `lam` is part of the critic
  contract. Any P3 claim of the form "channel X changes behaviour" is unfalsifiable
  without the ESS it was measured at.
- **A fixed-`lam` ablation across scenes is not a controlled comparison** (Q-025). It
  silently varies how much of the sample budget each scene uses.
- **The completion guard earned its keep against my own headline.** The two-sided
  audibility window was the prettiest thing this cycle found and `assert_all_reached`
  killed it before it reached a test. Instruments that only ever confirm you are not
  instruments.

## Recommended next 1–3 priorities

1. **Re-baseline `lam` alongside the Q-032 update fix, on one dedicated branch, once
   the queue drains.** These are the same job: two baseline defects that jointly
   re-score every unmerged PR. Do not stack; do not fix either mid-queue.
2. **Make ESS a reported field of every sandbox A/B** — `ab.summarize` should carry
   `median_ess` and `summarize` should refuse (or flag) an out-of-band arm. Turns
   Q-026 from a proposal into a default and is ~15 lines.
3. **Measure the high-`lam` end admissibly** (Q-034) — with a `v_max`/duration budget
   that lets a near-uniform-weight arm finish, or with the confirmation that it
   *cannot*, which is itself the answer.

## Artifacts

- PR: #67 (edited in place, no new queue depth)
- Files touched: `eval/mppi_sandbox/tests/test_softmax_temperature_audibility.py`,
  `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV row appended: yes (`a4f2a1f`, `sandbox:pass=94/94`, keep)
- Commit: `a4f2a1f`
