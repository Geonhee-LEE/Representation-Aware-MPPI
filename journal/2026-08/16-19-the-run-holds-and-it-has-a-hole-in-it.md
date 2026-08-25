# The run holds, and it has a hole in it

- **Cycle**: 2026-08-16 19:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `3bec5d39` [sandbox] respan-k96-at-32: 만장일치 run 의 마지막 미검증 member (~17 run)
- **Phase**: P3
- **Status**: keep

## What I tried

- Walked seeds `16..31` at `K = 96`, `lam = 1.15`, `w = 5` on `cafe_freezing_v0`
  — 17 runs (~40 s), same cell/scene/`sweep_seeds` body as every other column,
  with seed `0` re-run in the same call as a provenance check.
- Added `MEASURED_SEEDS_32_LAM115_K96_EXT` + `MEASURED_SEEDS_32_LAM115_K96`,
  extended `K_COLUMN_ROWS_N32` to five columns, froze D-306's four-column grid
  as `K_COLUMN_ROWS_N32_D306` and repointed D-306's test onto it.
- Re-read `ensemble_scaling_in_k` / `k_axis_bracket` / `attribution_separability`
  on the five-column grid, with the same five columns at `n = 16` (`SUB16`) as
  the control that separates "ensemble doubled" from "grid changed" (D-304's
  method).

## What worked / what failed

- **Provenance is a measurement, not a claim**: seed `0` came back `24.9722`,
  reproducing `MEASURED_SEEDS_16_LAM115_K96`'s row exactly, so the two halves
  are one column.
- **`K = 96` holds — `32/32`.** Every new seed clears the `0.05 × 96 = 4.8`
  floor; the closest is seed `21` at `5.8649` (`1.22x` of the floor). Span
  `5.330x` → `5.455x`, a `2.3%` widening — the **most ensemble-stable column on
  the axis**.
- **The question's two branches both missed what happened.** The TODO framed it
  as "either `96` exits (the whole run is an `n = 16` artifact) or it holds (the
  run is real and `128` was its edge)". It holds, and `128` is *not* the edge:
  `unanimous_k` goes `(96, 128, 160)` → `(96, 160)` with `128` inadmissible
  **between** them. The run is not a run; it is two columns with a hole.
- **The verdict cannot see the hole.** `k_axis_bracket` returns
  `K_BRACKET_OPEN_BELOW` with identical `run_bounds_open_intervals`
  (`(None, (160, 176))`) on *both* the contiguous SUB16 grid and the punctured
  `n = 32` one. Only `interior_inadmissible_k` `() → (128, 176)` records it.
- **Adding a column removed expressibility.** D-306 bought
  `SEPARABILITY_NOT_APPLICABLE → UNTESTABLE` by supplying a lower bound; with
  `96` present it is `NOT_APPLICABLE` again, because a non-contiguous run
  supplies no window shape. The gain was undone by the column meant to secure it.

## North-star delta

- **No movement in any robot-facing number.** 17 more closed-loop runs, all
  `reached_goal`, still one scene, still `transfers_to_ab_scene = False`, still
  blocked on PR #68 for any A/B reading — 34 days unchanged.
- What moved is negative and load-bearing: the contiguous-run object that five
  decisions (D-296 … D-306) reasoned about **does not exist at `n = 32`**, and
  the predicate that reported it cannot distinguish a run from a hole.

## Key learnings

- **D-303's proportionality claim does not survive five points.** It read the
  `n = 16` span bias as growing with the column's own width — `×1.18, ×1.80,
  ×2.11` at `160/176/192`, monotone on three points. On five it is not monotone
  in width: `96` is *wider* at `n = 16` than `160` (`5.330` vs `3.049`) yet moves
  *less* (`×1.02` vs `×1.18`), and `128` is narrower than `96` (`3.803`) yet moves
  the most on the axis (`×2.67`). "16-seed axes are flattened, not shifted" was a
  three-point coincidence; the widening is column-specific and unpredicted.
- **A verdict string that is identical across structurally different axes is not
  a reading.** `K_BRACKET_OPEN_BELOW` on a contiguous run and on a punctured one
  is the same failure mode as D-304's confound, one level up: the payload field
  that carries the distinction exists, and the headline field does not consult it.
- **"Is X an artifact?" is the wrong shape of question when the object itself may
  not be well-defined.** Both branches presupposed a contiguous run. The measured
  answer was neither.
- Ensemble-stability is **not** predicted by membership or by width: the column
  that moved least (`96`, `×1.02`) and the column that moved most (`128`,
  `×2.67`) were both `16/16` unanimous at `n = 16`.

## Recommended next 1–3 priorities

1. **Make the hole visible in the verdict** — `k_axis_bracket` should not return
   the same verdict + bounds for a contiguous run and a punctured one. Zero runs;
   a predicate change plus the pin this cycle left.
2. **Respan `K = 64` and `K = 80` at `n = 32`** — the two columns below the run.
   Every "exit below" statement on this axis is still an `n = 16` lower bound,
   and `96`'s stability shows the ensemble does not move all columns alike.
3. **Third ensemble for `K = 128` (`n = 48`)** — unchanged from D-306. The
   interior exit now carries more weight than when it was read as an edge, and
   it still rests on `10.142x` against a `10.0x` band (one seed, `1.4%`).

## Artifacts

- PR: #67 (open)
- Files touched: `eval/mppi_sandbox/calibrated_ladder.py`,
  `eval/mppi_sandbox/tests/test_calibrated_ladder.py`, `docs/decisions.md`,
  `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV row appended: yes
