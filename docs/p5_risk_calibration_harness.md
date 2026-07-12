# P5 Risk-Calibration Harness — one sweep for all P3 uncertainty knobs

_Phase P3→P5 bridge · 2026-06-27 · the P3 risk/uncertainty design lane is complete but
every knob it introduced was **deferred to P5 with no shared owner**. This doc fixes the
single calibration surface so P5 wires **one** sweep harness instead of five ad-hoc ones.
Design/spec only — no code, no dependency on the (merge-blocked) P2 ensemble. Consumes
the existing quantitative output [`run_metrics.md`](run_metrics.md) /
[`path_tracking_metrics.md`](path_tracking_metrics.md) and the two risk critics
([`margin_inflation_cost_critic_interface.md`](margin_inflation_cost_critic_interface.md),
[`aleatoric_risk_cost_critic_interface.md`](aleatoric_risk_cost_critic_interface.md)).
The harness-ownership decision below was **promoted to D-015** (2026-06-29, once #55 merged
and [`decisions.md`](decisions.md) became conflict-free); the open question is **promoted to
Q-013** in [`deliberations.md`](deliberations.md)._

## 0. What this doc closes

The P3 variance→safety lane left **five tuning knobs, each parked in a different
deliberation, none owning the calibration procedure**:

| # | knob | symbol | where deferred | what it controls |
|---|---|---|---|---|
| 1 | epistemic margin gain | `k_margin_per_sigma` (`k`) | Q-008 | meters of obstacle-margin inflation per unit epistemic σ |
| 2 | aleatoric chance level | `chance_delta` (`δ`) → `z(δ)` | Q-012 | target per-point collision probability (Gaussian quantile) |
| 3 | aleatoric CVaR fraction | `cvar_alpha` (`α`) | Q-012 | worst-tail fraction when `risk_measure=cvar` |
| 4 | epistemic norm reference | `σ²_ref` | Q-009 | held-out **OOD** percentile normalizing the epistemic `[0,1]` map |
| 5 | aleatoric norm reference | `σ²_ref_ale` | Q-011 (degeneracy) | typical **in-distribution** predictive-variance scale |

Each upstream doc says the same thing — *"value is P5; ship a documented default, never a
silent literal."* What none of them says is **how P5 actually picks the values**, i.e.
against *which* measured outcome, swept *how*, on *which* scenarios. Five independent grid
searches would (a) duplicate launch/aggregation plumbing five times, (b) miss the
**cross-knob coupling** that is the entire point — `k` and `δ`/`α` both tighten the same
clearance, so tuning them in isolation double-counts safety and over-shrinks the corridor.
This doc specifies the single harness that sweeps the joint vector and scores it against
one metric set.

## 1. The decision: one harness owns the joint sweep (→ D-015)

**Decision.** A single calibration harness `eval/calibrate_risk.py` owns the joint sweep
of all five knobs. It does **not** introduce a new metric or a new launch path — it is a
thin driver that (a) writes a knob-vector into the two critics' config, (b) invokes the
existing `run_metrics`-instrumented launch per scenario, (c) reads back the existing
`runs/<run_id>.json`, (d) appends one row per (knob-vector × scenario) to a sweep TSV.

**Why one harness, not five.** The knobs are **not separable** on the metric they share:

- `k·σ` (epistemic) and `z(δ)·σ_ale` (aleatoric) both subtract from the *same* effective
  clearance `d_eff` in the *same* rollout cost. Tuning `k` against near-miss with `δ` fixed,
  then `δ` against near-miss with `k` fixed, converges to a **different, more conservative**
  operating point than jointly tuning `(k, δ)` — each blames the other's residual near-miss
  on itself and over-inflates. The coupling lives in the metric, so the sweep must too.
- `σ²_ref` / `σ²_ref_ale` set the **scale** the gains act on (they normalize σ before
  `k`/`z(δ)` multiply a denormalized `sigma_raw`). A 2× change in `σ²_ref` is first-order
  equivalent to a 2× change in `k` for the *cost* effect — so `σ²_ref` and `k` are
  **partially redundant** and must be swept on a shared grid or the result is unidentifiable.

**Why a driver, not a new eval.** `run_metrics.py` already emits the only quantitative JSON
the project has, and `path_tracking_metrics.py` already defines the path-following half.
The harness reuses both verbatim — it adds **search**, not **measurement**. This keeps the
P5 metric definition single-sourced (north-star "완벽" gets pinned in *one* place, §3) and
makes the `cost_weight=0` / `k=0` / `δ`-default no-op baseline a free row in the same sweep.

**Alternatives rejected.** (a) Five per-knob notebooks — duplicates plumbing, blind to
coupling. (b) Overload an existing critic's gain to fold both routes into one weight —
already rejected as D-013/D-014 (entangles epistemic & aleatoric, kills the clean `=0`
ablation). (c) Online/Bayesian auto-tuning inside the planner — out of scope for a first
calibration; the harness stays an **offline batch sweep** producing a frozen config.

## 2. Inputs the harness writes (the knob vector)

One sweep point is a vector over the §0 table, written into the two critic configs in
`config/nav2_mppi_params.yaml` before each run:

```yaml
# RiskInflationCritic   (epistemic — margin_inflation_cost_critic_interface.md §4)
k_margin_per_sigma: <k>          # Q-008   grid: {0.0, 0.5, 1.0, 1.5}  (0.0 = baseline row)
max_inflation_m:    0.4          # safety clamp, NOT swept (== inflation_radius)
# AleatoricRiskCritic   (aleatoric — aleatoric_risk_cost_critic_interface.md §5)
risk_measure:       <chance|cvar>
chance_delta:       <δ>          # Q-012   grid: {0.20, 0.10, 0.05, 0.01}  → z = {0.84,1.28,1.64,2.33}
cvar_alpha:         <α>          # Q-012   grid: {0.20, 0.10, 0.05}  (only when risk_measure=cvar)
max_tighten_m:      0.4          # safety clamp, NOT swept
# normalization references (channel renderers — set once, then frozen for the gain sweep)
sigma2_ref:         <σ²_ref>     # Q-009   epistemic, from OOD percentile (no OOD set yet → swept as scale proxy)
sigma2_ref_ale:     <σ²_ref_ale> # Q-011   aleatoric, settable today from training-set predictive var
```

**Sweep-cost discipline.** A full 5-D grid is combinatorial; do **not** run it. The
normalization refs are **scale** knobs and the gains are **multiplier** knobs on that scale,
so fix the refs at their documented defaults (`σ²_ref_ale` is settable today from training
variance once #44 lands; `σ²_ref` stays a documented placeholder until an OOD set exists)
and sweep **only `(k, δ)`** as the primary 4×4 plane, with `cvar_alpha` as a secondary
1-D sweep on the heavy-tail scenarios only. That is **~16 + 3 points × N scenarios**, not
`4·4·3·…`. Refs get a *separate*, later sensitivity pass once the gain plane is located.
This is the open question logged as Q-013 below (coordinate-plane vs full grid vs
coordinate-descent) — default = the 2-D `(k,δ)` plane.

## 3. Outputs the harness scores against (the metric vector)

The objective is the north-star pair: **물체회피** (obstacle avoidance) AND **경로추종**
(path tracking), read from the existing JSON — no new metric is defined here.

| axis | metric | source | direction |
|---|---|---|---|
| obstacle | `near_miss_count` (per run) | `run_metrics` (P5 obstacle half) | ↓ minimize |
| obstacle | `collision` / `success` (0/1) | `run_metrics` | success ↑ |
| tracking | `cte_rms`, `heading_err_rms` | `path_tracking_metrics.summary` | ↓ minimize |
| tracking | `time_to_goal` / `time_deviation_final` | `path_tracking_metrics.summary` | ↓ (don't freeze) |
| smoothness | `jerk_lat`, `jerk_lon`, `accel_var` | `path_tracking_metrics.summary` | ↓ minimize |
| σ-calibration | `ece_global`, reliability-diagram coverage | σ source (P2 ensemble or predictor head) vs realized outcomes | → calibrated (coverage ≈ stated confidence) |
| σ-calibration | `brier_score`, `log_score` (proper scoring) | σ collision-risk predictions vs binary collision events | ↓ minimize — *strictly-proper*: tests sharpness, not just mean coverage |

**The calibration tension this exposes.** Tightening (`k`↑, `δ`↓) trades **near-miss ↓**
against **time-to-goal ↑ / cte_rms ↑** (the robot detours around inflated phantom margins).
The harness's job is to surface the **Pareto front** of (near-miss, time-to-goal) over the
`(k, δ)` plane per scenario, not to collapse it to a single scalar prematurely — the
weighting of "avoid harder" vs "arrive faster" is a north-star value judgment the user
makes *after* seeing the front, not a constant baked into the sweep. (A scalarization can
be added later once the user picks the trade rate; v0 emits the raw front.)

**Scenario set.** Reuse `eval/scenarios/*.yaml` — the `cafe_*` set already spans the
obstacle classes (`straight`, `obstacle_crossing`, `head_on`, `cut_in`, `convoy`,
`freezing`) and `city_*` the open-outdoor regime. The sweep runs the **same knob vector
across all scenarios** so a config can't overfit one map; the per-scenario rows make
env-specific divergence visible (a `k` good for `cafe` may over-detour in `small_city`).

## 3½. The uncovered axis — is the σ we tune *against* itself calibrated? (deferred Q-015)

Every knob in §2 is a **consumer** of the ensemble/predictor σ: `k·σ`, `z(δ)·σ_ale`,
and the two `σ²_ref` scales all assume the σ handed up from P2 (or a downstream
pedestrian-covariance predictor at P4) is a **trustworthy** number whose reported spread
matches empirical coverage. The metric vector in §3 scores only **downstream outcomes**
(near-miss, time-to-goal, cte, jerk) — it never asks whether that σ's stated confidence is
*true*. If σ is mis-calibrated (a Gaussian head that says "68%" but actually covers 50%),
the whole `(k, δ)` sweep silently absorbs the miscalibration into the gain: the harness
finds a `k` that *compensates* for a bad σ on one scenario and mis-generalizes on the next,
and the frozen config is uninterpretable (is `k=1.3` because the geometry needs it, or
because σ was 1.3× under-confident?). Four independent 2026-07-02 feed entries converge on
exactly this gap from different function classes:

- **Rethinking-Gaussian** (`arxiv:2603.10407`) — recalibrate a *parametric* Gaussian
  predictor upstream (KDE-of-confidence → Chi-squared matching loss) **before** the
  chance term consumes its covariance; score reliability/ECE as its own metric.
- **OCULAR** (`arxiv:2605.13028`, WAFR 2026) — *perception-conditioned, per-cell* conformal
  calibration of dynamics σ from BEV/semantic features, with a coverage guarantee that
  varies with what the representation sees (a direct P2→P3 handoff: turn the ensemble σ
  into a guaranteed *local* set, not a homogeneous one).
- **Scenario-aware UQ** (`arxiv:2512.05682`) — *distribution-free* conformal intervals on
  the predictor output + a reliable/unreliable **segmentation** so only the untrustworthy
  horizon tail is inflated, not the whole tube.
- **How-Human-Motion-Prediction-Quality** (`arxiv:2601.09856`, 80-subject study) —
  eval-honesty: rank any σ-emitting forecaster on **closed-loop + human-comfort** outcomes,
  never on ADE/FDE (mean-accuracy) alone; calibration ≠ accuracy.

**The fork this opens (Q-015).** Does the calibration harness need a **σ-calibration
stage + a calibration-quality metric axis** *upstream* of the §2 gain sweep, or does the
`(k, δ)` gain sweep alone suffice by absorbing miscalibration into the gain? If a stage is
warranted, three sub-options mirror the feed's function classes: (a) **parametric
recalibration** (Rethinking-Gaussian) — cheapest, but assumes a Gaussian head; (b)
**global conformal** coverage set — distribution-free, one quantile for the whole field;
(c) **perception-conditioned local conformal** (OCULAR) — per-cell, matches the core
representation hypothesis but needs a BEV-feature similarity metric and drops the
linear-Gaussian proof for our nonlinear residual+ensemble. And the metric side: add
**reliability-diagram / ECE / interval-coverage** as a *scored calibration axis* alongside
(near-miss, time-to-goal) in §3, so the harness reports "is σ calibrated *here*" separately
from "did the gain avoid the obstacle."

**Why this is distinct from Q-013 and D-015.** Q-013 asks *how to sweep* the consumer gains
(2-D plane vs full grid); D-015 assigns *one owner* to that sweep. Neither questions whether
the σ being consumed is calibrated at all — both treat σ as a given input. Q-015 sits
**upstream** of both: it is about validating/calibrating the *input* to the sweep, and about
adding a calibration-quality *metric* the sweep currently lacks.

> **Promoted to [`deliberations.md`](deliberations.md) as Q-015 (2026-07-05, once #58 merged
> and cleared the D-011 same-file trap).** Lean and next-action as above. The canonical stub
> is the authoritative record; this §3½ is the inline context that motivated it.

### Q-015 update: proper scoring rules as the strictly-proper calibration criterion

**DUCCT-MPPI (2026-07-07 feed, arxiv:2605.28330)** introduces **proper scoring rules
(Brier score, logarithmic score)** as the evaluation methodology for collision-risk
predictions — a stronger criterion than ECE/reliability-diagram coverage. ECE tests *mean
accuracy*: a calibrated-but-uninformative uniform distribution (say p=0.5 everywhere) passes
ECE. Proper scoring rules are *strictly proper* — they reward both calibration **and
sharpness** (the reported probability mass is concentrated at the true outcome), so a
distribution that reports 0.5 when the true risk is 0.95 takes a larger penalty than one
that reports 0.95 confidently and is right. The `brier_score` and `log_score` rows added to
§3 implement this: they score σ-derived collision-risk predictions against realized binary
collision events in each closed-loop rollout. DUCCT-MPPI reports +28% navigation success
over MC-MPPI baselines using this evaluation framework.

**Biased Dreams (2026-07-04 feed, arxiv:2604.25416)** adds a structural warning: in
learned-latent models, an "attractor" toward densely-trained regions can cause the epistemic
σ to *never fire* in the OOD/미관측 tail — aggregate ECE and aggregate Brier/log score will
certify a σ that is over-confident precisely in the tail (the latent stays near trained
attractors and never signals alarm). **The calibration-quality metric axis must be stratified
by representation density**: score ECE/Brier/log *conditioned on cell representation density*
(in-distribution vs OOD/unobserved cells), not only as a flat aggregate. A harness that
scores only overall ECE is a necessary but not sufficient check for the 미관측-distribution
clause of the north star. Concretely: partition the metric by occupancy-grid cells into
"seen ≥ N times in training" vs "seen < N times" and report per-stratum Brier/log.

### Dual-uncertainty UT extension (P3+ / P4 candidate)

DUCCT-MPPI's architecture has two independent uncertainty arms in the MPPI chance-constraint
cost: (1) a **Monte-Carlo pedestrian-prediction arm** (structural twin of DRA-MPPI
[[2506.21205]]) and (2) an **Unscented Transform localization-uncertainty arm** that propagates
robot pose uncertainty (AMCL particle spread) through the dynamics and into the rollout
collision probability. The project's current P3 channels cover model uncertainty
(epistemic/aleatoric) and obstacle-geometry uncertainty; robot localization uncertainty is a
third source that becomes load-bearing in tight café passages where AMCL covariance is
non-negligible (a 5 cm position spread inflates effective corridor width by ≈10 cm, which
can close a 30 cm gap entirely).

**P3+ borrow (non-blocking)**: add a localization-uncertainty margin term driven by the
AMCL covariance trace (approximation: UT propagation of a Gaussian pose belief through the
differential-drive kinematic step, yielding a per-step position spread `σ_loc`). Fold into
the chance-constraint cost as a third tightening term alongside `k·σ_epi` and `z(δ)·σ_ale`:
`d_eff = d − k·σ_epi − z(δ)·σ_ale − z(δ_loc)·σ_loc`. Does not require a new BEV channel —
it reads the existing AMCL `pose_covariance` directly. Candidate for Q-016 (localization-unc
vs P3 epistemic/aleatoric scope boundary — does the UT arm belong in a P3 critic or a P4
dynamic-risk extension?) once `deliberations.md` is conflict-free.

## 4. What stays out of scope (v0)

- **No online tuning, no learning the knobs** — offline batch sweep → frozen config only.
- **No new launch path** — reuses `include_run_metrics:=true` (`run_metrics.md`); the
  harness only templates the critic config and shells the existing launch per run.
- **No σ²_ref OOD calibration** — blocked on a held-out OOD/rosbag set that doesn't exist
  yet (epistemic §"`σ²_ref` source"). Until then `σ²_ref` is frozen at its default and the
  gain sweep proceeds; the ref pass is a later cycle.
- **No real numbers this cycle** — this is the *design* of the harness. It cannot run
  until (a) the P2 ensemble lands on main so the channels render, and (b) the two critics
  are implemented. It is the spec a P5 cycle picks up cold once those unblock.

## 5. Open question (promoted to Q-013 in `deliberations.md`, 2026-06-29)

> `[uncertainty]` **Sweep strategy for the coupled knob vector**: full 5-D grid (rejected —
> combinatorial) vs the **2-D `(k, δ)` plane with frozen refs** (this doc's default) vs
> **coordinate-descent** (cheaper, but can stall in the coupled valley `k`/`σ²_ref` create).
> Trade-off: grid is unbiased but `O(n^5)`; the plane assumes refs are separable from gains
> (true to first order, §1); coordinate-descent is cheapest but the `k`↔`σ²_ref` redundancy
> is exactly the kind of coupling it handles worst. **Lean**: ship the 2-D `(k,δ)` plane
> with refs frozen at documented defaults; add a 1-D ref sensitivity pass only if the front
> moves under a ±2× ref perturbation. **Next action**: a P5 cycle resolves this against the
> first measured `(k,δ)` Pareto front, then promotes to a D-NNN.

## 6. Acceptance (when P5 can call this done)

1. `eval/calibrate_risk.py` exists, templates the two critics' config from a knob vector,
   runs `run_metrics`-instrumented launches over `eval/scenarios/*.yaml`, aggregates to
   `results/calibration-<date>.tsv` (one row per knob-vector × scenario).
2. The `k=0, cost_weight=0` baseline row reproduces the current no-critic numbers
   byte-for-byte (proves the harness adds search, not behavior).
3. A `(k, δ)` Pareto front of (near-miss, time-to-goal) is emitted per scenario.
4. The chosen operating point is written back as the **documented default** in
   `nav2_mppi_params.yaml`, replacing the `0.0` placeholders — closing Q-008 / Q-009 /
   Q-011 / Q-012 with measured values, and resolving Q-013's sweep strategy.
5. A **σ-calibration-quality row** is included in the sweep output: `ece_global` /
   reliability-diagram coverage + `brier_score` / `log_score` over closed-loop
   collision-risk predictions, stratified by representation density (in-distribution vs
   OOD/unobserved cells). Resolves the "add ECE/coverage metric axis immediately" action
   from Q-015 Lean (§3½) and adopts DUCCT-MPPI's strictly-proper evaluation methodology.

---

_Cross-refs: [`run_metrics.md`](run_metrics.md) · [`path_tracking_metrics.md`](path_tracking_metrics.md) ·
[`margin_inflation_cost_critic_interface.md`](margin_inflation_cost_critic_interface.md) ·
[`aleatoric_risk_cost_critic_interface.md`](aleatoric_risk_cost_critic_interface.md) ·
[`multi_channel_risk_bev_stack.md`](multi_channel_risk_bev_stack.md) ·
[`decisions.md`](decisions.md) D-009/D-013/D-014/**D-015** ·
[`deliberations.md`](deliberations.md) Q-008/Q-009/Q-011/Q-012/**Q-013** (+ **Q-015** deferred inline §3½ — σ-calibration axis, promote once #58 merges) ·
DUCCT-MPPI arxiv:2605.28330 (proper scoring rules — §3 σ-calibration rows + §3½ Q-015 update) ·
Biased Dreams arxiv:2604.25416 (density-stratified calibration check — §3½)._
