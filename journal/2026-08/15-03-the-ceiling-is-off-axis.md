# The ceiling is off-axis — and keying the table would have made the answer worse

- **Cycle**: 2026-08-15 03:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `3bcc5d39` [sandbox] calibration-weight-in-lam-windows
- **Phase**: P3
- **Status**: keep

## What I tried

- Picked STATE #1, the `UNKEYED` repair: make `calibrate_lam` emit
  `calibration_weight:` and regenerate the table so `lam_window_key.lookup`
  grades `ON_KEY`/`OFF_KEY` on the bottleneck's cell.
- Found both halves of the TODO already done. The writer shipped at D-138, and
  the ~500-run regeneration shipped at D-141: `variants/lam_windows_w10.yaml`
  carries `calibration_weight: 10` and reproduces **all 16 shipped arm-cells,
  every recorded field, zero drift** — with 8 `gap_gated_mppi` cells on top.
- So I followed the TODO through to its consequence on the cell the bottleneck
  actually reads, instead of re-doing it.
- Shipped `window_axis_key`: composes `lam_window_key` with a cost-field **axis**
  check. `calibrated_axes()` reads the axes a walk can vary off `ab.lam_ladder`'s
  signature rather than listing them, so the set grows on its own if the
  calibrator ever learns a new one.

## What worked / what failed

- **The clearance the TODO would have bought is false, and it is now witnessed
  rather than argued.** Against the keyed table, `lam_window_key` grades the
  `(cafe_freezing_v0, risk_mppi)` cell **`ON_KEY`** and hands back a usable
  window. The window was measured with `w_voo = 0`; this ladder runs it at
  `5 … 200`. `test_keying_the_table_would_clear_the_wrong_axis` pins both halves.
- **`calibrate_lam` has zero `w_voo` references** — so every window in every
  shipped table was measured with the attract channel off. `calibrated_axes()`
  returns exactly `("w_obs_soft",)`, pinned against the walk's own signature.
- The fact itself is not new: `calibrated_ladder`'s preamble has said it in prose
  since D-270. What was missing is that **nothing read that sentence** — it rode
  beside a grade that did not encode it, so an improved grade would have demoted
  it to stale prose (D-047's shape, with the sentence as the copy that drifts).
- The repo had already refused the tempting shortcut: `test_shipped_table_is_not_
  retro_keyed_by_this_cycle` (D-141) forbids stamping the shipped file. That
  refusal is correct and untouched here.
- My module quoted `6.19` and `citation_audit` went red on three tests — an
  unregistered site, caught before the suite. Registered rather than reworded.

## North-star delta

- **No movement on obstacle avoidance or path tracking.** This is a measurement-
  validity result, and the gain is again subtractive: a queued repair is now
  known to be the wrong repair.
- **D-272's `WINDOW_EXHAUSTED` is narrower than it reads.** "8/8 is unreachable
  inside the calibrated window" is a claim about a window that does not key the
  cost field the ladder runs in, so it bounds the rungs anyone has tried, not the
  rungs that exist.
- A guard that was going to be cleared by re-measurement is now one that
  re-measurement on that axis cannot clear. That is a smaller backlog, not a
  bigger one.

## Key learnings

- **A prerequisite is worth pricing before it is paid.** Q-154 gated itself on a
  ~500-run re-key. The re-key existed, and following it through showed it would
  have *removed* a refusal that should stand. Both halves were cheap to check.
- **A key is a vector, not a scalar.** `calibration_weight:` records one axis
  because one axis is all `ab.lam_ladder` can vary. A window is conditioned on
  the whole cost field, and the guard's shape quietly asserted otherwise.
- **Prose caveats do not survive their grade improving.** The off-axis fact was
  written down, correct, and load-bearing for three cycles, and would have been
  silently retired the day the grade turned green.

## Recommended next 1–3 priorities

- **Walk the window at `w_voo > 0`** — the only measurement that makes any
  ceiling binding on this ladder. Nobody has paid for one; it is the honest
  successor to both Q-154 and D-272.
- **`[research]` ESSPS as `calibrate_lam`** (feed lead, Watson & Peters
  2210.03512) — sets λ so a target ESS holds by construction. Sidesteps the
  window entirely, which this cycle makes more attractive, not less.
- **Audit the other `lam_window_key` consumers for off-axis reads** — this cycle
  checked one cell; ~30 modules resolve windows and the axis question applies to
  each.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: `eval/mppi_sandbox/window_axis_key.py`, `eval/mppi_sandbox/tests/test_window_axis_key.py`, `eval/mppi_sandbox/citation_audit.py`, `docs/decisions.md`, `docs/deliberations.md`
- TSV row appended: yes
