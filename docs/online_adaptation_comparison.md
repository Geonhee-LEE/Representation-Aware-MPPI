# Online-Adaptation Mechanisms for P2 Residual Dynamics — Comparison

_Phase P2 research evaluation · 2026-06-09 · decision-input for D-009 online-adaptation wrapper_

**Question**: D-009 commits the build-first residual model to an **offline-frozen**
MLP-ensemble (K=3). The next open design question (north-star "미관측 분포 / 모든 환경")
is *online fidelity*: once the robot leaves the synthetic-unicycle training
distribution, how does the residual adapt without breaking the MPPI rollout budget?
This doc compares four online-adaptation levers and recommends one as the U2-stage
wrapper on top of the frozen ensemble.

**Sources newly added to the candidate pool** (research/feed.md, researcher cycle 020):
- **Function-encoder + RLS** — [Zero to Autonomy (Ward et al., arXiv 2509.12516)](https://arxiv.org/abs/2509.12516):
  represent dynamics as a learned **basis of functions**; online, treat the basis
  coefficients as latent states and update them by **recursive least squares** from
  streaming `(s,a,s_next)` odometry. No gradient inner-loop, constant-time per step.
  Validated on a **Clearpath Jackal** (our platform) under an ice-rink terrain shift.
- **Low-rank 2nd-order online** — [Adapting Neural Robot Dynamics on the Fly (Altawaitan & Atanasov, arXiv 2604.04039)](https://arxiv.org/abs/2604.04039):
  offline-trained incremental neural model + **low-rank second-order** (Gauss-Newton-style)
  online parameter update on a small adapted subspace. Real quadrotor, predictive
  tracking under novel payload/wind.

Baselines already analyzed in this repo:
- **MAML** — [`docs/maml_residual_adaptation_analysis.md`](maml_residual_adaptation_analysis.md)
  (arXiv 2504.16369): meta-trained init θ₀ + 1–5 gradient inner-steps on 5–20 transitions.
- **Plain ensemble** — D-009 build-first: K independent MLP heads, no online update;
  variance = epistemic signal only.

---

## Comparison table

| Axis | Function-encoder + RLS | Low-rank 2nd-order | MAML | Plain ensemble (D-009) |
|---|---|---|---|---|
| **Inference-time cost** | Constant-time RLS update (matrix of basis dim, ~K²); **rollout-budget-safe** | Low-rank GN step on adapted subspace; moderate, periodic | 1–5 gradient steps per adapt event; heaviest online | Zero (no online update) |
| **Data to adapt** | Streaming odometry, recursive (1 sample at a time) | Small online batch | 5–20 transitions per adapt event | N/A — does not adapt |
| **Gradient-free online?** | ✅ Yes (RLS, closed-form) | ⚠️ 2nd-order (no backprop-through-time, but curvature) | ❌ No (inner-loop SGD) | ✅ Trivially (no update) |
| **MPPI rollout integration** | Frozen basis evaluated in batched rollout; coefficients are extra latent state updated **outside** the rollout loop — clean separation | Adapted params swapped between control cycles; rollout uses current params | Adapted θ' swapped per adapt event; inner-loop must run off the hot path | Native — matmul, already in scaffold |
| **Our-platform evidence** | ✅ **Clearpath Jackal**, terrain shift (direct) | Quadrotor (transfer claim, not ground robot) | Generic MPC sim + manipulator | Sim only (ours) |
| **Composes with frozen ensemble?** | ✅ RLS adapts coefficients on top of frozen basis; ensemble var still gives epistemic | ✅ Adapts a low-rank delta over frozen weights | ⚠️ Re-frames the model as meta-init; ensemble heads would each need meta-training | Is the baseline |
| **Implementation complexity** | Medium — needs basis training (function-encoder), then RLS is ~30 LOC | Medium-high — low-rank Jacobian/curvature bookkeeping | High — meta-training task distribution + inner/outer loops | Lowest (done) |

---

## Reading of the table

1. **Plain ensemble does not adapt.** It quantifies *where* the model is uncertain
   (epistemic var → P3 channel) but never corrects the residual online. It is the
   floor, not a competitor — the wrapper sits **on top** of it.

2. **Function-encoder + RLS is the strongest fit for our constraints.** Three reasons
   line up with D-009's intent:
   - *Rollout-budget-safe*: the online update is a closed-form RLS step outside the
     batched rollout; the rollout itself stays a frozen-basis matmul (the property
     D-009 picked the MLP-ensemble for in the first place).
   - *Gradient-free*: no PyTorch inner-loop on the hot path — removes the single
     biggest objection to MAML for a real-time controller.
   - *Direct platform evidence*: Jackal + terrain shift is the closest published
     analogue to "cafe → small_city → real rosbag" generalization.

3. **Low-rank 2nd-order is the credible #2.** It also composes with a frozen offline
   model and avoids full backprop, but the published evidence is a quadrotor (different
   excitation/identifiability regime than a slow diff-drive), and the curvature
   bookkeeping is heavier. Keep as fallback if the function-encoder basis proves hard
   to train on unicycle data.

4. **MAML stays deferred (consistent with D-009's U2 note).** Its inner-loop gradient
   steps are the wrong shape for a per-cycle MPPI controller, and it requires an
   explicit task distribution at meta-train time (the same `--meta` dataset work that
   is itself still backlog). Strong for episodic sim-to-real, weak for continuous
   online drift.

---

## Recommendation (decision-input, not a new ADR)

**Adopt function-encoder + RLS as the candidate U2 online-adaptation wrapper over the
D-009 frozen MLP-ensemble; hold low-rank 2nd-order as the documented fallback; keep
MAML deferred to episodic sim-to-real only.**

Rationale: it is the only candidate that adapts online *without* paying gradient cost
inside the control loop, it preserves the rollout-native property D-009 was chosen for,
and it has the only on-platform (Jackal) validation in the set.

This is **not** yet a committed architecture — it gates on the D-009 build landing
(scaffold PR #44 + dataset PR #23 on main). Recorded as an open question for the
deliberation log so it is picked up when online adaptation becomes the active stage.

### Sequencing note
The online layer is meaningless until the offline frozen ensemble exists and is
trainable. Order: **(1)** land PR #44/#23 → **(2)** train + freeze ensemble →
**(3)** measure OOD rollout drift (does it actually diverge enough to need adaptation?)
→ **(4)** only then wire RLS. Step (3) is the empirical gate — adopt the wrapper only
if measured drift justifies it, not preemptively.

---

## What would change this recommendation

- If function-encoder basis training fails to converge on the low-dimensional unicycle
  residual (`[x,y,θ,v,ω] → [dx,dy,dθ]`), fall back to low-rank 2nd-order.
- If P2 stays purely in-distribution sim (no rosbag / no terrain shift in scope yet),
  the entire online layer is premature — the frozen ensemble + epistemic var is enough,
  and this comparison is shelved until P3/P4 introduce real distribution shift.
- If OOD rollout drift (sequencing step 3) measures below the MPPI cost's sensitivity
  threshold, no online adaptation is warranted at all.

**Refs**: D-009 ([`docs/decisions.md`](decisions.md)), [`docs/maml_residual_adaptation_analysis.md`](maml_residual_adaptation_analysis.md),
TODO `374c5d39`, research/feed.md (PRMPPI 2601.02948, RAY-TOLD 2604.27450 — online-learning entries).
