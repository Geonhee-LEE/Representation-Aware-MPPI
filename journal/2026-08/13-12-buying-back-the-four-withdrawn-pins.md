# Buying back three of the four withdrawn pins — and pricing the fourth

- **Cycle**: 2026-08-13 12:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — re-probe the four withdrawn inert-surface pins
- **Phase**: P5
- **Status**: keep

## What I tried

- Re-took the four pins `inert_surface staged` withdrew at 10:00 (`RESULTS.md`,
  `STATE.md`, `journal/`, `results/`) via `reprobe` — probe **only the entrants**
  and compose onto the standing verdict, rather than pay a full probe per pin.
- Three composed and are transcribed: `RESULTS.md` **INERT_COMPOSED** (1 entrant,
  `test_cycle_artifacts.py`, 22.6 s), `journal/` **INERT_COMPOSED** (2 entrants,
  367.5 s), `results/` **INERT_COMPOSED** (1 entrant, 0.9 s). All three now
  `inert() == True`; `leaking_pins()` stays empty.
- `STATE.md` was **not** re-taken. It sits at `generation == COMPOSITION_CAP - 1`,
  so `reprobe` correctly refuses to compose a fourth generation and falls back to
  the full 26-reader probe. One un-mutated pass over that set did not finish in
  120 s, and the module's own notes price sibling full probes at 15m45 / 17m57 —
  so the pair does not fit beside the 8.6-minute suite this cycle still owed.
  I stopped it deliberately rather than strand the cycle the way 10:00 did.

## What worked / what failed

- **The composition mechanism paid for itself where it was still available.**
  Two of the three re-takes cost under 25 s combined against a full-probe
  alternative measured in tens of minutes.
- **Entrant *count* does not predict re-take cost.** `results/` and `journal/`
  both took `test_quoted_counts.py` as an entrant; `results/` cost 0.9 s and
  `journal/` 367.5 s. Timed separately, `test_quoted_counts.py` alone runs in
  **0.25 s** — essentially all of `journal/`'s six minutes is its *other*
  entrant, `test_guard_reflexivity.py`.
- **I nearly published a false finding about my own instrument.** `results/`
  returning `INERT_COMPOSED` in 0.9 s looked like a probe my own kill-switch had
  spoiled, and I was about to discard it. Timing the entrant directly settled it
  in 0.4 s: the reading is real. The cheap check beat the plausible story.
- **The four pins did not decay independently.** One file,
  `test_quoted_counts.py`, is an entrant for `journal/`, `results/` **and**
  `STATE.md` — a single added test staled three pins at once.

## North-star delta

- **No capability moved.** This is instrument repair, and the honest reading is
  that it removes a per-cycle tax rather than moving the robot.
- 4 of 5 `POST_RECEIPT_WRITES` pins are live (`JOURNAL.md`, `RESULTS.md`,
  `results/`, `journal/`), so a cycle can once again write its 4a journal and TSV
  row **after** the receipt — i.e. state its own pass count. This cycle used that
  capability: the suite is green at **2734 passed / 158 skipped / 1 xfailed /
  0 failed** (511.12 s, 14 shards), and this sentence was written *after* the
  receipt rather than before it — precisely what 11:00 could not do.
- `STATE.md` remains withdrawn, so the D-043 order is **not** fully restored;
  4c still has to precede the suite. That is the residue, and it is named.

## Key learnings

- **`COMPOSITION_CAP` is a per-pin budget against a correlated failure mode.**
  Reader sets overlap heavily, so one new test file can push several pins toward
  the cliff simultaneously. The cap bounds each pin's inherited debt correctly
  and still lets the *portfolio* arrive at the expensive state together.
- **A pin's re-take price is a property of which files it carries, not how many
  entered** — so PLAN cannot price a re-take from the entrant tally, which is the
  number it can see cheaply. D-204 asked PLAN to price the cliff; this cycle says
  the tally it would price from is the wrong input.
- Stopping the unaffordable probe was the right call and is cheap to state: a
  stale pin is a *price*, not a leak (`leaking_pins() == ()` throughout).

## Recommended next 1–3 priorities

1. **Spend one dedicated cycle on `STATE.md`'s full 26-reader probe** — the only
   remaining withdrawn pin and the one blocking the D-043 order. Budget it as the
   cycle's single thrust; measure and record the true cost.
2. **Propose a capability successor to D-225** — unchanged from 11:00, and now
   with no instrument debt left to hide behind except the one item above.
3. **Audit the branch for claims resting on a point estimate inside an
   unresolved row** (the D-235 defect class). Reading only.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: `eval/mppi_sandbox/inert_surface.py`, `docs/decisions.md`, `journal/2026-08/13-12-buying-back-the-four-withdrawn-pins.md`, `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV row appended: yes
