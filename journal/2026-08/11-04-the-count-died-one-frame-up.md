# The count D-187 shipped died one frame up

- **Cycle**: 2026-08-11 04:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — sweep for other `all()`/`any()` reductions that destroy a count
- **Phase**: P5
- **Status**: keep

## What I tried

- Applied STATE #3's folded screening pair to `all_reached` — *what does the
  estimator consume* **and** *does the producer already compute it* — asked
  once, as one step, rather than learned over two cycles.
- Swept every `all(...)`/`any(...)` over a per-seed population in
  `eval/mppi_sandbox/*.py`, not just the one STATE named.
- Shipped `SweepStats.n_reached` / `n_froze` with the same contradiction guard
  and the same non-back-filling `None` discipline as D-187's `n_in_band`.
- Followed the count *outward* to the object a census walk actually records.

## What worked / what failed

- 🔴 **The finding is not the one STATE asked for.** `all_reached` was the
  expected defect and it is real, but it is already solved one object over:
  `LamProbe.n_reached` was added 2026-08-02 (Q-042) for this exact asymmetry,
  and `lam_ladder` counts both halves straight off `runs`. The gate's two
  halves were fixed in two different objects, nine days apart, and neither fix
  reached the third.
- 🔴 **`WalkCount.from_sweep` had no non-test caller.** `barrier_ceiling._rung`
  builds the object a walk records, and it read `stats.ess_in_band` while
  dropping `stats.n_in_band`. So D-187's prospective claim — "a walk taken from
  here records `n_in_band` and pools as a point" — was **false as shipped**:
  `COUNT_EXACT` was reachable only from a hand-built `SweepStats` in a test.
  This is D-138's reader-only-contract shape (a field whose writer does not
  exist is a contract never verified) and the D-044 state where a check that
  cannot be cleared gets muted.
- 🟢 `Rung` now carries `n_in_band` / `n_reached`, exposes `n_out_of_band` /
  `n_froze`, and thereby satisfies `from_sweep`'s duck type — the constructor
  has a production caller for the first time. Pinned by a test that walks a
  counted rung to `POOLED_IDENTIFIED`.
- 🟢 **The sweep came back clean, which is a result.** The only per-seed
  reductions in the producer are the three in `ab.summarize`, and both counts
  now ride along. `calibrate_lam.completes_anywhere`'s `any()` reduces over
  *probes*, each of which already carries its own counts — screened, not a
  defect. No third site.
- 🟢 The contradiction guard is restated on `Rung` rather than inherited: a
  pass-through boundary is exactly where two independently-copied fields drift
  apart without either being wrong on its own.

## North-star delta

- **No movement, and this cycle claims none.** No controller, representation,
  dynamics, or sim code; 0 sim runs; census attribution coverage still 0/6.
  Suite **2410 passed**, 158 skipped, 1 xfailed, rc=0, 1116.68s.
- What moved is prospective, and it is the *same* prospective movement D-187
  claimed — which is the point. D-187 bought it on `SweepStats`; the walk path
  never touched that field, so the purchase did not clear until this cycle.
- The two historical refused rungs are untouched and still
  `POOLED_FLOOR_ONLY` — a 64-run re-walk, still a user-run.

## Key learnings

- **A count is not kept until the object that gets *recorded* keeps it.**
  Adding the field to the producer is half the fix; the other half is every
  frame between the producer and the record. D-187 shipped the first half and
  its journal claimed the whole thing.
- **"Does the producer compute it?" needs a third question: does anything
  *call* the consumer?** `from_sweep` was fully implemented, fully tested, and
  dead. Grepping for non-test callers of a new constructor is the cheap check
  that would have caught this at 03:00.
- The screening pair STATE #3 asked for did work — it took one step this time,
  not two. But it found a defect one frame outside where it was pointed, so
  the rule should be "screen the path, not the pair of endpoints".
- Five consecutive cycles have now found the previous cycle's premise wrong in
  the cheap direction. This one differs in kind: the premise was not mispriced,
  it was **incomplete in a way its own tests could not see**, because the tests
  built the input by hand.

## Recommended next 1–3 priorities

- Grep for other constructors/readers with **no non-test caller** — the
  `from_sweep` shape, generalised. `citation_audit`-style, 0 sim.
- Point the constitution's Phase-3 pin check at `inert_surface pins` and
  correct the stale 4a-ter prose (13 cycles old, doc-only, concrete instance
  recorded 03:00).
- Decide whether to re-walk the two refused rungs (64 runs, user-run).

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: `eval/mppi_sandbox/ab.py`, `eval/mppi_sandbox/barrier_ceiling.py`, `eval/mppi_sandbox/tests/test_completion_count_witness.py`
- TSV row appended: yes
