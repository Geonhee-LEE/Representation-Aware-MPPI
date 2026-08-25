# The baseline MPPI update credits control authority the rollout never had

- **Cycle**: 2026-08-02 10:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic` (PR #67, in place)
- **TODO**: STATE claude-actionable **#9** — "fix `stock_mppi.command` to weight the realized perturbation, not the raw noise"
- **Phase**: P3
- **Status**: keep

Gate 1 fired for the **29th** time (queue 6: #66/#67/#68/#69/#44/#23; **20.9 d**
since #64 merged). Deadlock-breaker re-derived from scratch: `grep -c
'\*\*Status\*\*:.*superseded' docs/decisions.md` → **0**, criterion (b) still has no
candidate, not forced. `.last_escalation` 2026-07-31 22:01 (msg#760) → 72 h floor
**08-03 22:01**, escalation not re-sent. Fourth consecutive cycle applying the
same precedent: write into a PR **already in the queue**, which costs no new
review bandwidth.

## What I tried

- Took STATE item #9 at face value and went to confirm the defect before fixing it.
  `StockMPPI.command` rolls out `clip(U + noise)` but updates `U += Σ w_k · noise_k`.
  The two agree only where the clip does not bind.
- Instrumented the shipped controller (byte-identical update, plus per-tick clip
  bookkeeping) and measured how hard the clip actually binds, over full closed-loop
  runs on three scenes × 4 seeds.
- Implemented the one-line correction (`eps = controls - U`, weight `eps`) and ran it
  head-to-head against the shipped form over a 12-seed ensemble on four scenes, then
  on a path-blocking obstacle scene at n=16.
- Landed the *measurement* rather than the fix, as 6 tests.

## What worked / what failed

- **🔴 The defect is real and it is not a corner case.** On `cafe_straight_v0`,
  **22–29 %** of sampled `v` elements hit `v_min=0`, 4–9 % hit `v_max`, 8–15 % of
  `omega` clips — and **99.1–100 % of the softmax weight mass sits on samples with at
  least one clipped element**. The mis-credited increment reaches **1.39** per element
  against `sigma_v = 0.15`. The bias runs toward whichever bound saturates: down into
  `v_min` on the slow cafe scenes (Σgap_v −0.52…−1.05), **up** into `v_max` on
  `city_curved_v0` (+0.54…+0.81).
- **🔴 It is expensive on path tracking.** Corrected vs shipped, 12 seeds:
  `cafe_straight_v0` realizes **0.233 → 0.312 m/s** against a 0.4 target
  (**58 % → 78 %**), duration **12.82 → 9.50 s**; `cafe_obstacle_crossing_v0`
  **0.311 → 0.404 m/s**, **16.09 → 12.22 s**. This is very likely the mechanism behind
  02:00's "speed is decoupled from `target_speed`", which was attributed elsewhere.
- **🔴 But the fix is NOT a uniform win, and that is what stopped me landing it.** On a
  path-blocking obstacle scene (3 m straight, obstacle dead-centre, n=16) the corrected
  arm went **16/16 → 15/16** on completion and median clearance **+0.0299 → +0.0117 m**.
  The one lost seed is seed 0 — it stalls in front of the obstacle until t=56 s of a
  60 s budget, then breaks free too late (max completion 0.912).
- **🔴 Applying it turns #67 red — 5 tests fail, and two of those failures are findings,
  not breakage.** `test_direction_is_a_coin_flip_not_a_clearance_gain` goes to
  **7 farther / 0 closer**: under a corrected baseline the shadow-cost critic shows a
  *near-systematic clearance gain* where the broken baseline showed a coin flip
  (10/12/2 at n=24). If that survives n=24 it is a **stronger** Q-017 result than the
  one currently on the branch — but it is not assertable at n=8 and I had no budget to
  settle it.
- **✅ Landed green and additive**: `test_mppi_update_consistency.py`, suite
  **76 → 81 passed + 1 xfailed**. Five characterization tests pin how hard the clip
  binds (so the defect is measured, not asserted away), plus a **strict-xfail**
  statement of the Williams invariant as a closed-loop equivalence against a corrected
  reference implementation. No existing assertion touched → **merge recipe unchanged**.
- **⚠️ A hand-derived tick-0 check does not detect this defect** — my first attempt
  XPASSed. At `t=0` the plan sits at `target_speed` with `omega=0`, the clip binds on
  ~0.4 % of elements, and the `lam=0.1` softmax concentrates on unclipped samples, so
  the first-tick update gap is numerically zero. It is a closed-loop accumulation and
  has to be measured as one.
- **⚠️ Q-032 is NOT in `docs/deliberations.md`.** #66 wins that file in the documented
  chain resolution, so anything written there from #67 is discarded at merge. The
  durable record is this entry plus the test module's docstring. Same blocked status as
  the Q-017 revert.

## North-star delta

- **No new controller behaviour — but this is not zero-impact instrument work either.**
  The reference arm of **every** P3 A/B in the queue realizes 58 % of its commanded
  speed for a reason that is now identified and measured. Every "the blind arm drives
  faster / slower than the oracle" statement in #68 and #69 was made against a baseline
  whose speed is set by a bug rather than by its cost function.
- **A concrete, quantified re-baseline obligation now exists**, with a CI-enforced
  trigger. The strongest result in the queue is unchanged: #69's blind arm collides
  0/24 → 14/24 at 0.83× the oracle's speed.

## Key learnings

- **Confirm a backlog item's premise before executing it — this is the second cycle
  running that the premise moved.** 08:00 found "sole cause of #67's red CI" inverted by
  one `gh run view`; here item #9's fix is correct in form and *still* should not be
  applied yet, because correctness of the update and improvement of the benchmark turned
  out to be different questions. "The code is wrong" does not imply "fixing it now is
  right."
- **A correctness fix that moves a shared baseline is a re-baseline, not a fix.** The
  one-line change is right by Williams et al. and matches what nav2's `mppi_controller`
  actually computes, but it silently re-scores three unmerged PRs. One thrust per branch
  applies to *semantics*, not just to file count.
- **strict-xfail is the right shape for a known defect you are deliberately not fixing.**
  It is green today, states the correct invariant executably rather than in prose, and
  fails the moment someone fixes the code — converting a silent drift into a forced,
  explicit re-baseline.
- **The broken baseline may have been masking a real P3 effect.** The shadow-cost
  direction result flips from non-directional to 7/8 one-way under the corrected update.
  That is the single most interesting thread this cycle opened and it is unresolved.

## Recommended next 1–3 priorities

1. **Re-measure Q-017's direction at n=24 under the corrected update** — 7/8 one-way at
   n=8 is suggestive, not reportable. If it holds, the shadow-cost critic has a real
   clearance effect that the update defect was hiding.
2. **Dedicated branch for the update fix + full re-baseline** of #67/#68/#69's numbers,
   once the chain merges. Delete the xfail as part of it. Do not stack.
3. **Raise Q-032 formally** on a branch outside the #66-wins conflict set — "is a
   correctness fix to a shared baseline admissible mid-queue, or must it wait for a
   drained queue?"

## Artifacts

- PR: #67 (edited in place, no new queue depth) — https://github.com/Geonhee-LEE/Representation-Aware-MPPI/pull/67
- Files touched: `eval/mppi_sandbox/tests/test_mppi_update_consistency.py` (new),
  `results/p3-epistemic-shadow-cost-critic.tsv`
- Commit: `3dd558c`
- TSV row appended: yes
- Probes (uncommitted, `/tmp/proto_0802_10/`): `_probe.py` + `clip.json` (clip activity),
  `_ab.py` + `ab.json` (4-scene n=12 A/B), `_obst.py` + `obst.json` (n=16 obstacle scene)
