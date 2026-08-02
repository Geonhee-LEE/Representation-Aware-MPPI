# Q-017's most promising thread dies at n=24 — and the inertness had the wrong cause

- **Cycle**: 2026-08-02 11:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE item #1 — re-measure Q-017's direction at n=24 under the corrected update
- **Phase**: P3
- **Status**: keep

## What I tried

- Built a corrected-update `risk_mppi` without touching any shipped controller:
  `class CorrectedRiskMPPI(RiskMPPI, _CorrectedStock)` — C3 puts `RiskMPPI.command`
  (which renders the BEV) ahead of the corrected `StockMPPI.command`, so the Q-032
  one-line fix is expressed once and the shipped code stays byte-identical.
- Ran shadow-on (`w_epist=200`) vs shadow-off, paired by seed, n=24, under **both**
  update forms — the measurement STATE called "the single most valuable open thread".
- Applied the **Q-028 rescope protocol** before reporting: 4 perturbations (lateral
  hazard offsets 0.3 / 0.6 m, along-path shift to −1.2 m, `w_path=3`) × n=24 × 2 arms
  × 2 update forms.
- Probed *why* the rescoped arms tie, by instrumenting `_extra_cost`'s per-sample spread.

## What worked / what failed

- 🔴 **The n=8 signal does not survive n=24.** 7 farther / 0 closer at n=8 became
  **15 / 5 / 3 tied, p = 0.041** at n=24. One seed flipping gives 14/6, p = 0.115 —
  the significance is one sample wide. Under the shipped update: 10/12/2, p = 0.83.

  | rescope (n=24, sign test on completing seeds) | shipped | corrected (Q-032) |
  |---|---|---|
  | centred obstacle (control) | 10/12/2 p=0.83 | **15/5/3 p=0.041** |
  | geometry `offset=0.3` | 0/0/24 **tied** | 0/0/24 **tied** |
  | geometry `offset=0.6` | 0/0/24 **tied** | 0/0/24 **tied** |
  | geometry along-path `−1.2` | 10/10/4 p=1.00 | 13/7/4 p=0.26 |
  | cost `w_path=3` | 0/0/24 **tied** | 0/0/24 **tied** |

- 🔴 **Q-017's recorded explanation of the inertness is wrong.** The 07-13 entry
  attributed it to "가산항이 재분배할 weight 가 없다" — softmax-weighted E[σ] ≈ 0. At
  `offset=0.3` the per-sample shadow-cost spread is **larger** than on the centred
  scene (mean 197 / max 2000 vs mean 55 / max 2800 cost units) and the executed
  trajectory is **bit-identical** between `w_epist` 200 and 0, on every seed. The term
  prices samples very differently and changes nothing.
- ✅ **The actual mechanism is homotopy indifference.** A centred hazard leaves
  pass-left and pass-right nearly cost-tied; the `lam=0.1` softmax sits on a knife edge
  that any large additive term tips. Move the hazard 0.3 m off-centre — no controller
  knob touched — and one homotopy wins outright, and the shadow term cannot bridge the
  gap however much spread it carries.
- ✅ **Landed green and additive**: 3 tests, no existing assertion touched → **#66 merge
  recipe unchanged**. Asserted on `risk_mppi` *as shipped*, since the bit-identity holds
  under both update forms, so it survives whether or not a later cycle applies the Q-032
  fix. Includes a positive control, so a bug disabling `w_epist` everywhere cannot pass.
  Suite **81 → 84 passed + 1 xfailed**.
- ⚠️ One seed (0) misses the goal tolerance by 7 cm under the corrected update on the
  centred scene (`d_goal` 0.274 vs tol 0.20). Dropped from the sign test on both arms;
  it does not carry the result (the remaining 23 give the same 15/5).

## North-star delta

- **Negative, and it removes a false lead rather than adding a capability.** The
  headline P3 claim that additive epistemic cost steers a planner away from occluded
  space is now measured as **knife-edge amplification, not steering** — and the one
  scene where it is measurable is the same degenerate class **Q-027 already ruled
  inadmissible** for safety claims (its oracle grazes at 1 cm). Two independent
  admissibility filters now point at the same scene.
- Concretely: `w_epist` has **no demonstrated clearance benefit** on any geometry where
  the baseline has a real preference. Q-017 answer (a) is closer to refuted than to open.

## Key learnings

- **A confirmed direction at n=8 is not a direction.** 7/0 → 15/5 is exactly the decay
  a small sample predicts, and the n=8 read was recorded as the project's top thread.
  The seed-ensemble doctrine (Q-030) is about *power*, not just about seed 0.
- **"The term has no signal" and "the term has no effect" are different claims, and the
  cheap one is usually wrong.** Measuring the per-sample spread cost one instrumented
  run and overturned a fourteen-cycle-old explanation. Where a term is inert, measure
  the term before theorizing about the geometry.
- **Inertness that tracks homotopy indifference is a `lam` story, not a representation
  story** — which ties this to Q-024 (should `lam` be free at all?). If the additive
  channel can only bite where the softmax is already undecided, then raising `lam`, not
  enriching σ, is the lever that would make it bite.
- **The Q-028 rescope protocol paid for itself the first time it was applied to a
  positive result.** p = 0.041 on the control scene would have been reportable without it.

## Recommended next 1–3 priorities

1. **Test the `lam` corollary** — sweep `lam` on the `offset=0.3` scene and check whether
   `w_epist` becomes non-inert as the softmax de-concentrates. Decides whether (a) is
   *unusable* or merely *mis-tuned*, and it is the cheapest discriminator available.
2. **Revert Q-017 to `open`** in `docs/deliberations.md` with the corrected mechanism,
   replacing the "nothing to redistribute" text. Still **gate-1 blocked** — `#66` wins
   that file in the chain resolution, so it must land after the drain.
3. **Raise Q-033** — is a scene where the baseline is homotopy-indifferent admissible as
   evidence for *any* cost-term claim? Same shape as Q-027, different failure mode.

## Artifacts

- PR: #67 (existing, already in queue — no new review bandwidth)
- Files touched: `eval/mppi_sandbox/tests/test_shadow_cost_seed_robustness.py`
- TSV row appended: yes (`results/p3-epistemic-shadow-cost-critic.tsv`, `b98ba8a`)
