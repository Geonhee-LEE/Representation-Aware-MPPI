# The cure test was single-edge, and both windows dissolve under an in-band one

- **Cycle**: 2026-08-16 12:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `3bec5d39` decompose-the-lam-window-the-same-way
- **Phase**: P3
- **Status**: keep

## What I tried

- Built the ceiling mirror STATE asked for: `_ceiling_decomposition`, with
  `max_frac = median_frac * upper_spread` sharing `median_frac` exactly with
  the floor identity, so a column is one position and two tails.
- Ran D-299's substitution on the `lam` window (`{1.0, 1.1}`, exits `0.9`
  through the floor and `1.15` through the ceiling) — the *different*-edge
  dual of the same-edge question. **Zero sim runs.**
- Measured before writing the argument (D-186), and the measurement moved the
  scope: the cure test itself was unsound, so it was fixed for both axes and
  `same_edge_decomposition` re-read through it.

## What worked / what failed

- **The `lam` window does not decompose: `LAM_WINDOW_UNDECIDED`, and the two
  exits are undecided in *opposite* directions.** Below (`0.9`) is cured by
  **neither** — its span is `16.56x` against a `10.0x` band, so it is
  span-inadmissible in D-283's sense and no single factor puts it in band:
  the run's position leaves the minimum at `0.968x` of the floor *and* throws
  the maximum to `1.60x` of the ceiling. Above (`1.15`) is cured by **both**
  (`0.899x` and `0.917x` of the ceiling) because its miss is thin — `9.4%`
  over. Two factors that each suffice attribute nothing.
- **The cure test was asking the wrong question, and the `lam` axis is where
  that became visible.** It tested whether the column's *original* edge miss
  was gone. `K = 80` lent the run's position clears the floor at `2.29x` — and
  lands at `1.15x` of the **ceiling**. It was never in band, so it was never
  cured. Fixed to an in-band test, which is not a stricter hurdle but the
  definition of the property: `min` and `max` bracket every seed, so
  `floor <= min and max <= ceil` *is* membership unanimity.
- **So D-299 narrows: `SAME_EDGE_TWO_MECHANISMS` → `SAME_EDGE_UNDECIDED`,
  attributions `("neither", "spread")`.** Every number D-299 published is
  unchanged and still in the payload; the predicate reading them was wrong.
  `K = 176`'s spread attribution survives intact.
- Both synthetic `ONE_CURVE` constructions still return `ONE_CURVE` under the
  new test, on both axes — the verdicts are not constants (D-241).
- 172/172 in the module; 4 new tests, 2 rewritten.

## North-star delta

- **No robot-facing number moved.** No obstacle, clearance, near-miss or CTE
  reading; one scene (`cafe_freezing_v0`), `transfers_to_ab_scene = False`,
  still blocked on PR #68. Zero new sim runs.
- What moved is a **retraction**: the strongest claim on this branch from the
  last three cycles was a double dissociation, and it was an artifact of the
  scoring rule. The instrument is now sound and says *less*.

## Key learnings

- **A cure test has to be scored on the property the window is made of.** The
  window is unanimous *membership*; the test scored *one edge*. That gap is
  invisible on a same-edge window — which is exactly where the test was born —
  and becomes load-bearing the moment the other edge is in play. Generalising
  an instrument to a second axis is how you find out what it was assuming.
- **The two axes now agree on the weaker answer**, and neither is a
  refutation: D-290's "different edges, different mechanisms" and D-299's
  "same edge, two mechanisms" are both *unsupported*, not disproven. What
  would decide either is a column that misses by more than one factor's worth,
  or a below-column narrow enough to be admissible. Neither exists yet.
- **Phase 0's feed entry predicted the shape of this fix** (`research/feed.md`,
  the Cheraghi Pouria et al. calibration-loss re-admission): emit a *(position, spread)
  pair per edge* rather than one refined verdict string, plus a separability
  check that the two statistics are not tracking the same sampling noise. The
  payload now emits the pair. **The separability check is not done** — both
  statistics come from the same 16-seed ensemble, so they share sampling
  noise, and that is the honest gap in this cycle's instrument.

## Recommended next 1–3 priorities

- **Separability check on the (position, spread) pair** — the feed's caveat,
  now the sharpest open hole: are the two factors independent enough on a
  16-seed ensemble to attribute anything, or is `UNDECIDED` partly noise?
  Leave-one-seed-out on the existing columns, zero new runs.
- **Walk a column that misses by more than one factor's worth** — `lam = 1.2`
  or `1.25` above the run (`1.25` misses with 2 seeds and the narrowest span
  on the axis). If a thicker miss decides, `UNDECIDED` was resolution, not
  structure.
- Unchanged: PR #68 is the only path to any A/B-scene reading.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/calibrated_ladder.py, eval/mppi_sandbox/tests/test_calibrated_ladder.py, docs/decisions.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: yes
