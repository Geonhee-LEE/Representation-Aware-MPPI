# A two-arm A/B needs a shared temperature — and the out-of-band arm is the flattered one

- **Cycle**: 2026-08-02 19:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE claude-actionable **#1** — answer Q-039 (is a single-`lam` two-arm A/B admissible?)
- **Phase**: P3
- **Status**: keep

## What I tried

- Took the Q-039 question 18:00 filed and split it into a **structural** half
  (what protocol does the calibration table permit for a controller *pair*?)
  and an **empirical** half (what does the choice actually cost?).
- Shipped `ab.ab_temperature` / `assert_single_lam_ab` / `ABTemperature.lam_for`
  — pair-level verdict resolved off `lam_windows.yaml` *before* any run.
- Ran `cafe_obstacle_crossing_v0` under three temperature protocols, same
  scene / seeds / arms, changing only `lam`, and compared paired clearance.
- Recorded the outcome as **D-017** (`docs/decisions.md`) since it changes how
  every A/B on this branch may be reported.

## What worked / what failed

- ✅ **The generalisation is the same move one level up.** Q-035: a scene is an
  ablation surface for a *controller* iff its window is non-empty. Q-039: a
  scene is a **single-temperature** A/B surface for a *controller pair* iff the
  **intersection** of their windows is non-empty. Matrix partition pinned as
  strict set equality — **6 shared / 1 per_arm / 1 unreportable**.
- 🔴 **The empirical half is the part worth having, and it is not what I
  expected.** Direction survives every protocol; **magnitude does not**:

  | protocol | arms in band | paired Δ (risk − stock) | sign |
  |---|---|---|---|
  | single `lam=0.4` | stock only (risk ESS **3.92**, floor 12.8) | **+0.0957 m** | 7/1 |
  | single `lam=1.6` | risk only | +0.0368 m | 8/0 |
  | per-arm 0.8/1.6 | **both** | +0.0492 m | 7/1 |

  Running `risk_mppi` below its floor — where the update is near-argmin over
  K = 256 draws — **inflates by 1.9× the clearance gap it is credited with**.
  The two protocols in which risk runs *in band* agree with each other far
  better than either does with the one that does not, so the spread is the
  band exit and not seed noise (pinned as its own test).
- ✅ **Neither option is a clean ablation, and the guard says so.** Single-`lam`
  hides an unbounded confound; per-arm carries a temperature difference that is
  **bounded by the gap and reportable**. Hence `lam_for` minimises that gap in
  **log-space** (0.8/1.6 = 2×, not the equally admissible 0.4/3.2 = 8×) —
  temperature acts multiplicatively, so a linear metric would misrank the pairs.
- ✅ **Cheap where it can be.** 10 structural tests are table-only and free; the
  cost is the 2 empirical ones. Suite **156 → 168 passed + 1 xfailed**,
  **132.5 s → 145.6 s**. Memoizing the per-`(arm, lam)` sweeps cut the new file
  from 25 s to **11.7 s** — the three protocols share four of their six arms.
- ⏸️ **Did not touch `docs/deliberations.md`** — #66 and #67 already prepend a
  different Q-017 at the same offset (STATE #7). `docs/decisions.md` is
  untouched by every other queued PR, so D-017 lands conflict-free there.

## North-star delta

- **No capability movement — this is measurement validity again**, but it is the
  first result that puts a *number* on how wrong an out-of-band A/B is (1.9×)
  rather than only declaring it inadmissible.
- **It narrows rather than voids the queued branches**: #67/#68/#69's *direction*
  claims survive a single-`lam` protocol; their *effect-size* headlines do not.
  Previously Q-039 threatened all of them equally.
- 물체회피/경로추종 metrics unchanged. 8 scenes still calibrate the same way.

## Key learnings

- **"Inadmissible" and "wrong in a known direction" are different findings, and
  the second is worth the extra 30 s of simulation.** The guard alone would have
  said "don't do that"; the measurement says *what it costs and which way it
  leans* — and the arm that is out of band is the one that looks **better**,
  which is the dangerous orientation.
- **When two protocols are both confounded, prefer the one whose confound is
  bounded and nameable.** That is the whole argument for per-arm temperature,
  and it generalises past `lam`.
- **A precondition that can be checked from a table should never be checked by
  simulating.** `assert_ess_in_band` catches this defect *after* paying for the
  sweep, per arm; `assert_single_lam_ab` catches it before, per pair.
- Confirms the 18:00 lesson from the other side: the crossing scene keeps being
  the one that breaks things, and **still no explanation for why it and not
  `cafe_convoy_v0`** (same five obstacles) — now the highest-value open item.

## Recommended next 1–3 priorities

1. **Find what makes the crossing scene different from `cafe_convoy_v0`** — it is
   now the *only* `per_arm` cell in the matrix, so whatever distinguishes it
   predicts when per-arm temperatures are needed. Candidate: staggered /
   counter-flow schedules vs a formation that passes once. One `lam_windows.yaml`
   read plus one scripted variant.
2. **Apply D-017 to the re-baseline** — #67/#68/#69's headlines are effect-size
   claims; restate them as direction claims or re-run per-arm. Part of the
   dedicated baseline-fix branch, not stacked.
3. **Give `city_curved_v0` / `city_figure8_v0` obstacles** (screen with
   `goal_ball_clearance` first) — unchanged from 18:00, still #3.

## Artifacts
- PR: #67 (in place — gate 1 fired, 38th; zero new review bandwidth)
- Files touched: `eval/mppi_sandbox/ab.py`, `eval/mppi_sandbox/tests/test_ab_temperature_protocol.py`, `docs/decisions.md`, `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV row appended: yes
