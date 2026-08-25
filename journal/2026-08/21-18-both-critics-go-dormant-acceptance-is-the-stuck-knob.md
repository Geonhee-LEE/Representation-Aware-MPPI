# Both epistemic-arm critics go dormant — the stuck knob was never the weight

- **Cycle**: 2026-08-21 18:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `disposition` Answer the disposition question as a `Q-NNN → D`
- **Phase**: P3
- **Status**: keep

## What I tried

- Cleared the strand first: 17:00 finished `b204c62` (D-407) and never pushed. Its
  journal and TSV row were both on disk and graded `DISCHARGE_PUSH` (honest), so the
  repair was a receipt plus a push, not a re-run.
- Took the disposition decision STATE named as the single next claude-actionable,
  rather than buying the fourth sweep D-407 explicitly declined. `cycle_wallclock
  review` reported the preceding run at 19m41 without publishing and told me to cut
  scope; a prose decision is the deliverable that fits that budget.
- Re-read the three cycles of measurement (D-405 / D-406 / D-407) looking for the
  fact that discriminates between the three options, instead of arguing them on
  their merits.

## What worked / what failed

- **The discriminating fact was already in the table and nobody had used it**:
  `pass=0/5` on **both** scenes at **every** weight, for both critics. D-407's
  framing ("scene-keyed table vs geometry gating vs retirement") is a question about
  how to *tune* `w_voo`, and all three answers are bets that some setting of it
  moves acceptance. The measurements say no setting does.
- So the sign inversion, which read as the hard problem, is a second-order effect:
  `w_voo` moves `cte_rms` and clearance around inside a region where the run fails
  anyway. Choosing (a) or (b) would have bought a calibration axis for a knob whose
  output metric has never changed.
- `w_epist` is inert at 2000 across two measurements **11 weeks apart** — that half
  needed no new argument, only someone to write the disposition down.
- What I did *not* do: delete either critic. Retirement-as-deletion is code plus test
  churn, and this cycle's budget was one 20-minute suite. D-408 decides the
  *disposition* (dormant, default `0.0`, out of the sweep rotation); deletion is a
  separate cheap follow-up that can be picked cold.

## North-star delta

- **No movement on the measured numbers, and that is the finding.** Acceptance is
  `0/5` on both scenes regardless of either critic's weight — the north star's
  "물체회피 완벽" is blocked by something upstream of the epistemic arm.
- Three cycles of sweep output are converted from open measurement into a shipped
  state: both weights stay `0.0` for a *measured* reason, not only D-027's
  ablation-invariance argument.
- Removes an axis from the calibration matrix instead of adding one — the (a) branch
  would have multiplied it by scene.

## Key learnings

- **When every option in a trade-off assumes the same thing, check the assumption
  before ranking the options.** (a), (b) and (c) all presumed `w_voo` could matter;
  the `pass=0/5` column refuted the premise more cheaply than any comparison of the
  three.
- A knob that moves secondary metrics (`cte_rms`, clearance) while the primary metric
  is pinned at failure is a knob measured in the wrong regime. Sweeps there produce
  real, reproducible, useless numbers — D-405's 5-seed table looked trustworthy for
  exactly this reason.
- The next question is not "which critic weight" but "why is `pass` 0/5 at
  *baseline*" — that is a scenario/acceptance-threshold question, not a cost-critic
  question, and it is upstream of everything the last three cycles measured.

## Recommended next 1–3 priorities

1. **Diagnose `pass=0/5` at baseline** on `cafe_obstacle_crossing_v0` — is it a
   genuine planner failure or an acceptance threshold no run has ever been able to
   meet? Nothing downstream is interpretable until this is known.
2. **Delete `ShadowCostCritic` + `ObservationValueCritic`** per D-408's disposition,
   with the sandbox tests updated — mechanical, pickable cold.
3. **Fix or document `run.py`'s exit code** (`rc=1` on a complete run with
   `pass=false`) — carried from 17:00, still a live trap for sweep harnesses.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: journal/2026-08/21-18-*.md, docs/decisions.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: yes
