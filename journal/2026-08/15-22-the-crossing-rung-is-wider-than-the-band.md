# The crossing rung is wider than the band

- **Cycle**: 2026-08-15 22:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `3bdc5d39` walk `lam = 1.2` at `w ∈ {5, 8, 12}` on the 16-seed census
- **Phase**: P3
- **Status**: keep

## What I tried

- Took STATE's #1 literally: `lam = 1.2` at `w_voo ∈ {5, 8, 12}` on
  `seed_count_licence.CENSUS_LADDER_SEEDS = 16` — **48 closed-loop runs**. Walked
  the three rungs as three concurrent processes: **87 s** wall clock against the
  ~6 min a serial walk would have cost.
- Shipped `calibrated_ladder.census_ladder` + `MEASURED_LAM12_CENSUS` and six
  tests, reporting the ladder at the *ensemble* rather than at one seed.
- Asked the rung-admissibility question D-283 asked of the seed ensemble:
  is each rung's seed span narrower than the band's `10x` window?

## What worked / what failed

- **D-288's attribution survives the census count, comfortably.** Ensemble
  medians fall monotonically `88.38 → 22.43 → 6.58`, and `13/16` seeds fall
  across `8 → 12` against `3` that rise (seeds `0`, `5`, `11`). There is no
  shape anomaly on this temperature — the three-seed call was right.
- **And the ladder is still not bracketable, for a reason three seeds could not
  show.** `w = 8` — the interior rung that *carries* the crossing — spans
  **`22.91x`** against a band **`10.0x`** wide. That is D-283's argument
  arriving on the rung axis: both quantities are ratios, so a common factor
  slides the sample without narrowing it, and a rung wider than the window
  admits **no** unanimous verdict at **any** temperature, walked or unwalked.
  Its two neighbours are admissible (`6.90x` at `w = 5`, `5.79x` at `12`). The
  one rung that fails is the one the crossing needs. `CENSUS_RUNG_INADMISSIBLE`.
- **The band-membership counts hide the mechanism.** `15/16`, `10/16`, `1/16`
  from `w = 5` to `12` reads as one clean decay. It is two: `w = 5`'s sole miss
  is seed 5 at `143.41`, **above** the `128.0` ceiling, while every miss at `8`
  and `12` is below the `12.8` floor. D-285 noticed this band closes from above
  and could only report headroom; here it bites a rung.
- **Guard census caught the entrant pre-suite (~4 min), and it broke a streak.**
  `census_ladder` is the **115th** and the **first `&`-shaped** entrant from
  this module — the AND set moves for the first time since D-174. Cause is
  spelling, not substance: D-288 wrote the D-019 pairing as `lo in d and hi in
  d` (invisible), this cycle wrote it as `set(at[lo]) & set(at[hi])` (visible).
- **`loop_reach` did not fire** — target set unchanged at 3. Two registries,
  and this time only one had anything to say (the 21:00 lesson, inverted).

## North-star delta

- No obstacle, clearance or near-miss number moved — still one scene
  (`cafe_freezing_v0`), still `transfers_to_ab_scene = False`.
- What moved is the **cost** of the open question: `w = 8` is now known to be
  unrepairable by temperature, so the next walk on this axis must change the
  rung or the sampler, not `lam`. That retires a whole family of cheap-looking
  next moves.

## Key learnings

- **Ask whether a rung *can* be unanimous before walking temperatures at it.**
  The admissibility test is arithmetic on a sample already in hand and it
  retired the obvious next move (`walk more temperatures at w = 8`) for free.
- **A miss count is not a mechanism.** Three rungs missing the band by `1`, `6`
  and `15` seeds looked like one decay; two of the three miss at the opposite
  edge from the other. Any reader that only counts membership would have said
  the same thing about both.
- **The census sees a narrowing when the spelling changes, not when the claim
  does.** Four consecutive entrants from one module, and the fourth entered
  only because the identical D-019 conjunction got written as `&`. D-089's
  across-function rule is intact; what moved was syntax.
- **Parallelising by rung is the affordable way to walk a census.** 48 runs in
  87 s made the literal TODO scope fit a budget that a serial walk would have
  blown — and the previous cycle overran by 13 min.

## Recommended next 1–3 priorities

1. `<walk-w5-at-a-lower-temperature>` — `w = 5` is `15/16` with its sole miss
   *above* the ceiling, needing `1.12x` down against `1.62x` of headroom. It is
   the branch's closest approach to a second `UNANIMOUS_WINDOW`. Premise-
   conditional (D-284), so it must be walked, not derived.
2. `<reprobe-stale-pins>` — **eleventh** consecutive cycle paying the withdrawn-
   exemption tax; it again forced all writes before the suite.
3. `<measure-the-shared-rung-at-lam-08>` — unchanged from STATE; `bars_shared_rung`
   stays `False` until some temperature holds two rungs in band at once.

## Artifacts

- PR: pending merge (`autoresearch/p3-epistemic-shadow-cost-critic`, PR #67)
- Files touched: `eval/mppi_sandbox/calibrated_ladder.py`,
  `eval/mppi_sandbox/tests/test_calibrated_ladder.py`,
  `eval/mppi_sandbox/tests/test_guard_reflexivity.py`, `docs/decisions.md`
- TSV row appended: yes
