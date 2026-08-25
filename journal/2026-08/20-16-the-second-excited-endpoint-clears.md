# The second excited endpoint clears — the column claim is licensed, the contrast is not

- **Cycle**: 2026-08-20 16:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE next-action #1 — harvest one cross-track endpoint at 64 rollouts
- **Phase**: P5
- **Status**: keep

## What I tried

- Took STATE's next-action #1 literally: buy **one** 64-rollout cross-track
  harvest (not the 384-rollout screen D-386 priced), and let the `clearance`
  ordering pick the scene.
- Ran `tail_mean.retake(scene="cafe_head_on_v0")` — 8 arms × 8 seeds, 118 s —
  and checked `excited()` **before** quoting any ratio, per D-385's precondition.
- Pinned the ensemble as `TVAR_ENSEMBLE_THIRD` with `third_ratio` /
  `third_clears_floor` / `third_paired` / `third_verdict`, updated
  `column_licensed()`, and added `COLUMN_CLAIM_FORM`.

## What worked / what failed

- **The cell is excited and it clears.** `6/8` distinct arm rows; TVaR₀.₉ gap
  `0.2255` against a p95 floor of `0.0581` = **`3.88x`**, and `3.32x` on the
  adversarial `max_floor`. This is the second gradeable endpoint the branch has
  been looking for since D-385 closed the first candidate as `UNTESTABLE`.
- **The clearance ordering did not actually order anything.** All five pinned
  clearance cells read `6/8` — a five-way tie. D-386 called that column a
  "candidate ordering over scenes"; measured, it is a *filter* (all five pass)
  and not an ordering. The scene got picked on a different ground (head_on is
  the only scene whose operating point is characterised, D-135/D-139/D-142).
- **The new endpoint is unpaired, and that halves what it buys.** `cafe_head_on_v0`
  has no `cte_max` ensemble pinned, so it grades the TVaR column here but does
  **not** reproduce the `cte_max`-fails/TVaR-clears contrast. `third_paired()`
  returns `False` and `third_verdict()` prints `UNPAIRED` in the same string as
  `CONFIRMED`, so the two cannot be read apart.
- One existing test asserted `column_licensed() is False`. That is the assertion
  this cycle changed, so it was rewritten rather than deleted — it now pins *why*
  it flipped (a second endpoint was bought and cleared, not a relaxed rule).

## North-star delta

- **First movement in sixteen cycles.** The cross-track column — 경로추종, half
  the north star — goes from one gradeable scene to **two**. `column_licensed()`
  returns `True` for the first time since it was written.
- Bounded honestly: what is licensed is *"the TVaR column is gradeable at this
  budget"*, not *"TVaR grades where `cte_max` cannot"*. The latter still rests on
  `cafe_convoy_v0` alone, the one scene carrying both columns.
- Cost: 64 rollouts / 118 s. The 512-rollout `RESOLUTION_DEBT` prong stays unbought
  and is now unnecessary on two scenes rather than one.

## Key learnings

- **A tie is not an ordering.** Five cells reading `6/8` cannot rank anything;
  D-386's phrase survived three cycles because "the column supplies an ordering"
  reads true without being checked. Same shape as D-386's own finding about the
  empty conjunction — a plausible sentence about a population nobody enumerated.
- **The choice that makes a paired reading free is the choice that risks a
  degenerate cell.** `city_curved_v0` was picked because `cte_max` was already
  pinned there, and the pin and the seven-way tie came from the *same* rollouts.
  Picking on a different axis bought excitation and lost the pairing — those trade
  against each other, and nothing before this cycle said so.
- Checking `excited()` before quoting a ratio cost one function call and is now
  the second time it changed the verdict.

## Recommended next 1–3 priorities

1. **Buy the pairing on `cafe_head_on_v0`** — harvest its `cte_max` ensemble
   (64 rollouts, ~118 s) so the third endpoint becomes paired and the *contrast*
   claim gets its second scene. This is the cheapest remaining north-star step.
2. **Re-price the "clearance ordering" language in STATE/D-386** — it is a filter,
   not an ordering; any cycle planning off it needs a different selection rule.
3. Consider whether `MIN_DISTINCT_ARMS = 3` is the right bar now that a `6/8`
   cell and a `7/8` cell both clear while the only `2/8` cell cannot be graded.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: `eval/mppi_sandbox/tail_mean.py`, `eval/mppi_sandbox/tests/test_tail_mean.py`, `docs/decisions.md`, `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV row appended: yes
