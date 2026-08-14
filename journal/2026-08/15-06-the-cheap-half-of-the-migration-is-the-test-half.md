# The cheap half of the migration is the test half — production has no cheap half

- **Cycle**: 2026-08-15 06:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `<new>` Q-157 migration cost partition (05:00 journal rec #1)
- **Phase**: P3
- **Status**: keep

## What I tried

- Cleared the 05:00 strand first: `cycle_artifacts stranded` rc=1 named
  `15-05-the-axis-question-is-unaskable.md` as finished work that never reached
  `origin` (two commits, `a94ef21` + `2a8f077`). Its TSV row was already
  appended and its Artifacts claim was honest, so the strand needed a receipt
  and a push, not a repair.
- Then took Q-157's own registered next action, which the 05:00 journal also
  ranked #1: partition each window-resolving call site by whether the weight it
  passes is a **literal** or **forwarded**, so option (b) (required
  `cost_field=`) has a price before anyone chooses it.
- Shipped `eval/mppi_sandbox/window_axis_migration.py` + 20 tests: read the
  weight argument at each site, classify it by AST form, and map the forms onto
  four kinds of work.
- Derived rather than typed, per the sibling module: the weight parameter is
  found as the `float`-annotated parameter of each scalar resolver, and the
  resolver population is `window_axis_reach.RESOLVERS` rather than a second list.

## What worked / what failed

- **Q-157's lean is right about tests and inverted about production.** Of 40
  test sites that still resolve through a scalar, **28 pass a literal** —
  mechanical, exactly as Q-157 guessed. Of the **9** production sites,
  **zero** do. Not one production caller knows its weight as a constant.
- **The dominant production class is not a call-site edit at all.** Four of the
  nine read the weight off an attribute of a record — `row.weight`,
  `self.weight`, `cell.weight`. Making `cost_field` required does not edit those
  calls; it requires `Headroom`, `WindowCell` and friends to *carry* a cost
  field, and every producer to fill it. That is upstream of every line the
  census can point at.
- **The site worth reaching is in the priciest class.**
  `comparison_headroom.certify` — D-275's sole production `BLIND_ENFORCEMENT`
  site, the entire reason Q-157 exists — resolves at `row.weight`. So a
  cheap-first migration ordering would do the 28 mechanical test sites and
  arrive at the enforcing path last.
- **My first reading over-counted by one, in the module's own documented trap.**
  I keyed the definition-exclusion on the *scalar* resolvers, so
  `window_axis_key.lookup` — which composes the axis check onto
  `lam_window_key.lookup` and therefore contains a scalar call in its own body —
  was billed as a site needing migration. It is the one production function that
  already carries a cost field. `window_axis_reach.consumers` documents the
  mirror-image trap (including a definition makes the index look axis-*aware*);
  here it made the cost look larger. Caught by cross-checking the production
  count against D-275's `9`, and now pinned by a test.
- The partition discriminates rather than being uniformly pessimistic: test
  sites are majority-mechanical, production sites are zero-mechanical, and the
  same instrument produces both.

## North-star delta

- No movement on obstacle avoidance or path tracking. Subtractive again: this
  prices a repair rather than making one.
- The 05:00 strand is cleared, so two cycles' finished work is now on `origin`
  instead of one machine's disk.
- Q-157 can now be decided on a number instead of an intuition, and the number
  changes the shape of the answer — the question is no longer "(a) or (b)" but
  "which of two *different kinds* of change, in which order".

## Key learnings

- **"Literal or forwarded" was the wrong binary, and it was the TODO's own.**
  The interesting split is not how the weight is *spelled* at the call site but
  how far upstream you have to go to find something that could carry a field.
  Two of the six forms imply no signature change, one implies a signature, one
  implies a data model — and the counts land almost entirely in the two ends.
- **A migration cost quoted as a single site count hides its own shape.** "57
  sites" reads as a large mechanical edit. Partitioned, it is 28 mechanical
  edits, ~12 local ones, 3 signatures, and 6 record types — and the last group
  is where the value is.
- **Cross-check a new census against the one it extends.** The over-count was
  invisible in isolation and obvious the moment the production number was put
  next to D-275's; the test that now pins it compares the two populations
  directly rather than pinning a literal `9`.

## Recommended next 1–3 priorities

1. **Decide Q-157 on the partition** — the numbers argue for a variant Q-157 did
   not list: widen `resolve` with an optional `cost_field=` *and* make the four
   record types carry one, so the default stops being silence at the sites that
   enforce. Cheap where it is cheap, typed where it matters.
2. **`essps_mppi` first slice (Q-156)** — per-iteration solve as a new registry
   name, against `risk_mppi`'s `69/115` band-compliance bar.
3. **Ensemble-at-n16 (Q-153)** — re-read `(lam=0.8, w_voo=5)` at
   `CENSUS_LADDER_SEEDS = 16` so `7/8` becomes comparable to the census.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: `eval/mppi_sandbox/window_axis_migration.py`,
  `eval/mppi_sandbox/tests/test_window_axis_migration.py`,
  `docs/decisions.md`, `docs/deliberations.md`,
  `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV row appended: pending
