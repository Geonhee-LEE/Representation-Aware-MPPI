# The published both-on cell is attract, not cancelling

- **Cycle**: 2026-08-14 15:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `Q-148-replace` Re-place Q-148's both-on cell against D-258's rollout root
- **Phase**: P3
- **Status**: keep

## What I tried

- Executed D-258's unexecuted consequence — it moved the cancelling root onto the
  planner's support and closed by saying the A/B's arm weights were "derived from
  a superseded support" without re-deriving them.
- Shipped `eval/mppi_sandbox/both_on_cell.py`: places a both-on cell against the
  `ROLLOUT` band and grades its **sign**, with a three-outcome vocabulary
  (`REPEL` / `ATTRACT` / `INDETERMINATE`) because the root is a band and a sign
  is only settled if it is settled for every root in it.
- Reported the sign as its own quantity, not only the headroom magnitude — the
  `research/feed.md` 12:00 SOMBRL entry (`2511.20066`) attaches a sublinear-regret
  guarantee to the attract weighting specifically, so direction is reportable.
- 10 pytest cases in `tests/test_both_on_cell.py`, pinned to D-258's band.

## What worked / what failed

- **The error is in the sign, not the magnitude.** D-256's `0.3587` sits *below*
  the whole rollout band `[0.6386, 0.8347]`, so the cell placed as *cancelling*
  is robustly `ATTRACT` on the planner's support — every root in the band puts
  the summed split negative. D-258's `2.79x → ~1.34x` framing could not surface
  this: both are headroom on the repel side of a root the cell is not on the
  repel side of.
- **It does not resolve everywhere, and the survey says so.** Across D-257's own
  radii: `ATTRACT` ×5, `INDETERMINATE` at `r=0.3` (band `[0.1704, 0.5770]`
  contains the published ratio), `UNPLACEABLE` at `r=1.25`. So the claim shipped
  is the weaker-but-true `published_cell_is_never_repel`, and the per-radius
  stability predicate is kept reading `False` rather than dropped.
- **I had `headroom` inverted and the published numbers caught it.** My first
  definition (`root / ratio`) gave 0.7475 at 1:1 where D-258 reports `1.34x`.
  Requiring the property to reproduce *both* published factors (`1/0.3587 =
  2.79`, `1/0.7475 = 1.34`) is what found it — a test pinned to a number the
  branch already published is worth more than one pinned to my own arithmetic.
- Suite green on this tree; the count is re-taken after the doc writes (D-043).

## North-star delta

- **No closed-loop movement** — this is still a cost-field reading, not a sim.
  The A/B itself remains blocked on PR #68's occlusion scene for the seventh cycle.
- **One planned experiment corrected before it ran.** The four-arm A/B would have
  spent its both-on arm at a ratio believed to sit at the crossing and in fact
  sitting robustly on the attract side — i.e. a second attract arm, and the arm
  D-256 added the cell to avoid duplicating.

## Key learnings

- **A magnitude can be right and its direction unasked.** Three cycles reported
  this cell as a headroom factor and none reported which side of zero it was on;
  the sign was one subtraction away the whole time. The feed entry is what made
  the direction a *reportable*, which is Phase 0 doing its job.
- **A band-valued root makes "which side" a three-way question.** Collapsing to
  the band mean would have called `r=0.3` attract on a band that straddles.
  `INDETERMINATE` is the price of placing the cell where the arms contend — the
  maximally-contended ratio is the least sign-resolved one by construction.
- **`UNPLACEABLE` had to propagate.** Substituting the grid root at `r=1.25` is
  D-258 alternative (b), and it is tempting precisely because the grid answers.

## Recommended next 1–3 priorities

1. Pick the replacement ratio for the both-on arm — sign-robust (outside the
   bracket) or maximally-contended (`band.mean`, sign-unresolved). This is a
   Q-148 decision, not a measurement; the bracket is now computable per radius.
2. `inert-probe-budget` — the five withdrawn pins cost an ordering discipline
   every cycle on this branch; decide whether to buy them back with a shard pass.
3. Merge PR #68 (user) — the A/B has been blocked on its scene for seven cycles.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: `eval/mppi_sandbox/both_on_cell.py`, `eval/mppi_sandbox/tests/test_both_on_cell.py`, `docs/decisions.md`, `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV row appended: yes
