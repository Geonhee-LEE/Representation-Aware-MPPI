# retreat_gain has a floor between 30 and 100, then a decade-wide plateau

- **Cycle**: 2026-10-09 10:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `3c4c5d39` heading_err_rms_max under knee+shape (progress sub-thread: promotion check)
- **Phase**: P6
- **Status**: keep

## What I tried
- Measured the two scenes D-514 skipped (cut_in, city_figure8_v0) at n=16 under w0 and under w10+k100, with knee+shape band 0.30 and yaml acceptance.
- Swept `progress_retreat_gain` k ∈ {30, 100, 300, 1000} on head_on and crossing at n=16.
- Pinned the floor in `test_retreat_gain_plateau.py`: head_on seed 7 collides at k=30 and holds the band at k=300. Lam census forwards 50→51.

## What worked / what failed
- k=100, 300 and 1000 are the same arm on both scenes: head_on T 12.2–12.4 s, clr 0.30; crossing 16/16, T 17.8 s.
- At k=30, head_on seed 7 collides (clr −0.077 m). Below the floor the retreat comes back as a collision, not as a slow run.
- cut_in and figure8_v0 fail 0/16 on both arms (goal ball blocked / scene defect). No regression and no gain.
- The global default was not flipped. The flip would add zero passes, because head_on, cut_in and figure8_v0 fail on every arm, and it would break D-027's inert-default invariant.

## North-star delta
- The candidate tracking arm is now fully characterised on all 9 shipped scenes plus figure8_v1. It costs nothing anywhere and helps on crossing, curved and figure8_v1.
- The safe gain range is known (k ≥ 100). The candidate value is k=300, the middle of the plateau.
- Pass count is unchanged. The remaining failures (head_on min_distance, cut_in goal ball, figure8_v0) are arm-independent.

## Key learnings
- A gain sweep can show a safety floor, not only a performance knee. A value set at the knee (100) sits right on the edge of a collision.
- The remaining red cells on the matrix are no longer controller questions. head_on's 0.30 min_distance band and cut_in's blocked goal ball are scene/acceptance questions, and the user already owns the head_on one.

## Recommended next 1–3 priorities
- Make `completion_percent` monotone/windowed so a shortcut cannot read completion=1.0 on city_figure8_v1 (STATE item 2).
- Register `w_progress=10, progress_retreat_gain=300` as a named sandbox arm so the matrix can report it beside stock.
- Retire city_figure8_v0 from the shipped matrix in favour of v1 (D-509 scene defect).

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/tests/test_retreat_gain_plateau.py, eval/mppi_sandbox/tests/test_default_lam_sites.py, docs/decisions.md
- TSV row appended: yes
