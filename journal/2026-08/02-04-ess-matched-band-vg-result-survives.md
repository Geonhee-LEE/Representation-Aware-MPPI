# SKIP (23rd): both prior temperatures were broken instruments — an in-band one exists, and #69's result survives it without a handicap

- **Cycle**: 2026-08-02 04:00 KST
- **Branch**: none (gate 1 — measurement only, nothing pushed)
- **TODO**: none picked — `EXECUTOR_SKIP reason=pr-queue-full count=6`
- **Phase**: P3
- **Status**: in_progress (uncommitted measurement)

## What I tried

- Re-derived gate 1 from scratch: **6 OPEN** (#66/#67/#68/#69/#44/#23), 0 pushed-but-PR-less,
  0 branches in 24 h. Last merge #64 @ 2026-07-12T14:00:41Z → **20.6 d**. Deadlock-breaker crit (b):
  `grep -cE '^\s*-?\s*\*\*Status\*\*:.*superseded' docs/decisions.md` → **0**; not forced.
  `.last_escalation` 07-31 22:01 → 72 h floor **08-03 22:01**, escalation not re-sent.
- Took **Q-025** (raised 03:00: ESS is arm-dependent — is a fixed-`lam` ablation admissible at all?).
  Swept `lam ∈ {0.1, 0.3, 1, 3, 10, 30, 100}` × {`stock`, `vg`} on `cafe_blind_approach_v0`,
  logging softmax **ESS** per arm, against a healthy band of 5–30 % of `samples` (13–77 of 256).
- Replicated #69's collision comparison at **N=24** at the in-band temperature, with Fisher's exact.
- Measured **goal completion** explicitly, to test whether the safe arm is merely the immobile one.
- Reused the `/tmp/scratch_p3merge` worktree from 03:00 — no re-resolution of the #66↔#67 conflict.

## What worked / what failed

- **✅ Both previously-used temperatures are pathological, in opposite directions.** `lam=0.1`
  gives ESS **3.2** (`stock`) / **5.4** (`vg`) of 256 — MPPI collapsed to argmin-over-noise, as
  02:00 found. But 03:00's fix, `lam=100`, gives **194** / **224** of 256 — a *near-uniform*
  softmax, i.e. the update is approximately the mean of zero-mean noise and the optimizer is barely
  selecting. **03:00 traded a degenerate instrument for an inert one**; neither is a legal
  operating point, which is why its duration numbers should not be trusted either.
- **✅ An in-band temperature exists and is narrow.** `lam=0.3` → `stock` **37.7** (15 %), `vg`
  **54.3** (21 %) — both inside 13–77. `lam=1` is already at/over the edge (85 / 135).
- **✅ The result survives ESS-matching, and this time the speed match is free.** At `lam=0.3`,
  N=24: `vg` **5/24** collisions vs `stock` **0/24**, **Fisher one-sided p = 0.0248**, at
  mean_v **0.206 vs 0.202** — a **+1.5 %** gap, speed-matched *by construction with no `v_max`
  handicap applied*. At `lam=1`: **8/24 vs 0/24, p = 0.0019**, speed gap **−0.2 %**. 03:00 needed a
  hand-applied handicap at a temperature that was itself illegal; the claim no longer needs either.
- **✅ The collision *direction* is temperature-invariant** — across all 7 temperatures `stock`
  collides **0/4 every time**, `vg` at 5 of 7. This is the sharpest contrast yet with the duration
  orderings, which reverse. Coarse binary outcomes with a control arm survive; fine-grained
  cross-arm orderings do not.
- **✅ Not the immobility artifact.** The obvious objection — both arms average 0.20 m/s and run the
  full 36 s at `lam≤1`, so is "safe" just 03:00's brake-on-reveal control (0/24 but never arrives)?
  — is refuted by measurement: **12/12 seeds reach the goal**, final distance **0.078 m**
  (`stock`) / **0.064 m** (`vg`), at every temperature tested including `lam=100`.
- **⚠️ Duration is not usable on this scene.** At `lam≤1` every `stock` seed runs exactly 36.00 s
  while sitting 0.078 m from the goal — the arclength `STOP_COMPLETION` criterion is not met even
  though the goal is reached. Any time-to-goal metric read off this scenario at these temperatures
  is measuring the stop criterion, not the controller.
- **⚠️ The oracle's margin is still thin**: `stock` mean min-clearance **+0.012 m** at `lam=0.3`.
  03:00's caveat stands — "the oracle clears" remains a marginal, not comfortable, result.

## North-star delta

- **The one surviving quantitative P3 result is now materially stronger.** It held at
  `lam=100` only with a hand-applied speed handicap; it now holds at a **legal, in-band
  temperature**, with **natural speed matching**, at **two** temperatures, with **both arms
  reaching the goal**. p = 0.0248 (`lam=0.3`) and p = 0.0019 (`lam=1`).
- Concretely: restricting what the planner can see raises collisions **0/24 → 5/24** while the
  robot moves at the same speed and completes the same task. That is the core hypothesis, measured.
- **No movement on the merge queue** — 23rd consecutive skip; this remains uncommitted, now **16**
  journal entries deep.

## Key learnings

- **"Both arms at the same `lam`" and "both arms at a *valid* `lam`" are different requirements,
  and the second is the binding one.** 03:00 achieved the first (210–225 for everything) and
  concluded the instrument was fixed. It was matched and simultaneously wrong. An ablation needs an
  admissibility check on the optimizer's own health, not just parity between arms.
- **ESS has two failure modes and the project has now hit both.** Low ESS = argmin over noise
  (high variance, seed-chasing); high ESS = uniform averaging (no optimization). The useful check
  is a **band**, not a floor — STATE's item #1 (`test_ess_is_not_degenerate`, "ESS ≥ a fraction of
  samples") would have caught `lam=0.1` and **passed** `lam=100`, missing this cycle's finding.
  That item should be rewritten as a two-sided band before it lands.
- **Sweep the nuisance parameter rather than fixing it.** Three cycles argued about which single
  `lam` was correct. Seven runs of 4 seeds settled it and simultaneously produced the robustness
  evidence — the invariance of the collision direction across all 7 — that no single-temperature
  run could have produced.
- **Ask whether the safe arm is safe or merely stopped.** The cheap goal-distance check separated
  this result from the brake-on-reveal endpoint. It should be a standing assertion, not a
  per-cycle recollection.

## Recommended next 1–3 priorities

1. **Rewrite STATE item #1 as a two-sided band test** — `test_ess_within_admissible_band`, asserting
   `0.05·K ≤ ESS ≤ 0.5·K` for every registered controller. As specified ("ESS ≥ a fraction") it
   would have passed `lam=100`.
2. **Add a goal-reached assertion to every safety comparison** — a collision-rate claim is void if
   the safer arm did not complete the task. Cheap; would have pre-empted 03:00's dead-end control.
3. **Commit the record.** 16 journal entries, this ESS band, and a now-doubly-controlled p = 0.0248
   result live only in `/tmp`.

## Artifacts

- PR: none (gate 1; nothing pushed)
- Files touched: none in-repo. Scripts + raw JSON in `/tmp/proto_0802_04/`
  (`_essmatch.py`, `_partb.py`, `_goal.py`, `sweep.json`, `partb.json`, `goal.json`);
  scratch merge reused at `/tmp/scratch_p3merge`
- TSV row appended: no (no branch)
