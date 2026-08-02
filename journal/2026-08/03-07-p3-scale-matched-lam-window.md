# A scale-matched `w_voo` arm keeps the recorded `lam` window — the naive weight doesn't move it, it deletes it

- **Cycle**: 2026-08-03 07:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic` (PR #67, already in queue)
- **TODO**: STATE #1 — calibrate a `lam` window for an arm that actually carries `w_voo`
- **Phase**: P3
- **Status**: keep

## What I tried

- D-021 established every window in `lam_windows.yaml` was measured with the
  epistemic channel **off**, so no clearance number from a `w_voo` arm was a
  controller comparison. D-027 shipped the term, D-028 said which denominator
  its weight must be priced against. This ran the missing measurement.
- Built `scale_match.py`: `exchange_rate` measures a term's spread-per-unit
  against the arm it is **added to**, `weight_for_ratio` inverts it,
  `check_undamaged` refuses when the probe weight already derailed the arm.
- Calibrated four arms over `calibrate_lam.DEFAULT_LADDER` (0.05 → 6.4, a
  **128× span**), 8 seeds/rung, on `cafe_obstacle_crossing_v0` / `risk_mppi`:
  baseline (control, **re-measured** not quoted), scale-matched fixed
  (`w_voo = 5.43`), ratio-held-per-rung (3.41–7.17), and naive (`w_voo = 200`).
- Then swept the weight at the two admissible rungs to locate the boundary.

## What worked / what failed

- ✅ **The window does not move.** baseline **[1.6, 3.2]** — reproducing the
  recorded table exactly, which is what licenses reading the other columns.
  Scale-matched fixed: **[1.6, 3.2]**. Ratio-held per rung: **[1.6, 3.2]**.
  STATE #1's premise is **answered in the negative for shippable weights** —
  the recorded windows transfer and the A/B needs no per-arm recalibration.
- 🔴 **The naive weight is a temperature *kill*, not a temperature *shift*.**
  D-027's phrase "disguised temperature change" implies a window that moved
  somewhere. It didn't: `w_voo = 200` is out of band at **every rung of a 128×
  ladder** (median ESS 1.00 at six of eight, 1.80 at the top). The repo had
  previously seen an empty window only on a *defective scene*
  (`cafe_cut_in_v0`); this is one induced by a **weight** on a scene that is
  healthy in the next column. Raising `lam` does not buy it back.
- 🔴 **Boundary located.** In ratio units (`lam = 1.6` reference), at the two
  admissible rungs: 0.13 → 8/8, 8/8 · 0.25 → 8/8, 8/8 · **0.50 → 1/8, 8/8**
  (half the window gone) · **1.00 → 0/8, 1/8** · 2.00 and 4.66 → 0/8, 0/8. Full
  window survives to **ratio ≈ 0.25**; ratio 1 — the line `TermSpread.ratio`'s
  docstring already named as the danger condition — is confirmed, and the
  *practical* ceiling sits **4× below** it.
- 🔴 **The prescription is a fixed point.** `per_unit` moves only **1.12×**
  across the 128× ladder (a constant of the critic) while `rest` falls
  **2.26×** (188.0 → 83.1), so the scale-matched weight inherits the
  denominator's swing: **2.11×** end to end (5.43 at `lam = 0.1`, 3.41 at 3.2).
  "Scale-match, then calibrate" is circular in principle.
- ⚠️ **And that fixed point bought nothing here** — holding the ratio fixed per
  rung produced the *same* window as holding the weight fixed. Recorded as an
  honest negative so the next reader doesn't pay for the per-rung protocol.
- ⚠️ **Suite wall-clock is drifting.** 328 → **343 passed** (+15, 1 xfailed) but
  the run is now **504 s**, against the 145.6 s recorded a few cycles ago. This
  file contributes ~120 s of it (the `w_voo = 200` assertions each derail to the
  1000-step cap). D-016's "seconds, no ROS needed" is no longer true of the
  whole suite.

## North-star delta

- **No avoidance or tracking number moved** — this was a protocol measurement.
- But it **unblocks** one: the epistemic A/B no longer needs a per-arm `lam`
  calibration, which was the stated gate on every `w_voo` clearance number.
- One new repo-wide safety fact: a cost weight can render a healthy scene
  non-calibratable, and the threshold is now a number (ratio ≈ 0.25 to keep the
  full window) rather than a caution.

## Key learnings

- **"Disguised temperature change" and "uncalibratable" are different claims,
  and only the second one was true.** The first invites a search for a better
  `lam`; a 128× ladder says there isn't one. Checking whether the window *moved*
  or *vanished* cost one extra column and changed the prescription.
- **A ratio's two halves can have opposite sensitivity to the same knob.** The
  numerator was a property of the term, the denominator a property of the
  temperature — which is what made a two-step recipe circular. Worth checking on
  any normalized statistic before treating it as a pipeline stage.
- **Extrapolation fails exactly where it doesn't matter.** D-028 pinned the
  closed-loop rate moving 2.1× between w = 1 and w = 200; but 200 is four ratio
  units past where the window is already empty. Measured 1.005–1.221× over the
  usable range — the cheap unit probe is sound for every weight worth shipping.
- **Re-measuring the control caught nothing this time, and that is the point.**
  The baseline reproduced `lam_windows.yaml` exactly. Cheap insurance that turns
  three other columns from suggestive into readable.

## Recommended next 1–3 priorities

1. **Run Q-043's `(w_voo, horizon)` 2×2** at a scale-matched weight — now fully
   specified (weight ≤ ratio 0.25, `lam ∈ {1.6, 3.2}`) and no longer gated on a
   window calibration. Still gated on #68/#69 for the blind-corner scene.
2. **Re-measure the self-vs-baseline denominator gap at the shipped `lam = 0.1`**
   (STATE #2) — D-028's stronger claim (the verdict *flips*) is still unverified.
3. **Mark or split the slow tests.** The suite is 504 s; the derailed-arm
   assertions are the bulk. A `slow` marker with a fast default would restore
   D-016's promise without deleting coverage.

## Artifacts

- PR: #67 (already open — no new review bandwidth)
- Files touched: `eval/mppi_sandbox/scale_match.py` (new),
  `eval/mppi_sandbox/tests/test_scale_match.py` (new), `docs/decisions.md` (D-029)
- TSV row appended: yes
