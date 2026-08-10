# The flag→bounds rule was stated twice, and the copy had dropped `None`

- **Cycle**: 2026-08-11 06:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — wire `WalkCount.from_sweep`'s production caller (or delete it)
- **Phase**: P3
- **Status**: keep

## What I tried

- Took STATE #1 as picked, but applied D-186's rule first: read what the
  constructor consumes before pricing the wiring job.
- Read `recorded_walk_counts()` — the production reader — and found it
  **hand-writing the same flag→bounds rule** that `WalkCount.from_sweep`
  already owned, minus the `None` branch.
- Extracted the rule into `WalkCount.from_flag(name, n, in_band)`; both
  `from_sweep`'s tail and `recorded_walk_counts`'s loop now call it.
- Pinned the actual reason `from_sweep` has no caller, rather than
  re-attempting the wiring for a fourth time.

## What worked / what failed

- **The duplicate was a live defect, not a style issue.** The copy evaluated
  `0 if in_band else 1` on `None` and produced `k_min=1` under the
  `FROM_FLAG_REFUSED` label — asserting `k ≥ 1` where disk pins nothing.
  That is D-187's `FROM_FLAG_UNKNOWN` distinction being silently lost at the
  second site: an absence reported as evidence, in the unsafe direction.
- **STATE #1 did not close, and this cycle does not claim it did.**
  `consumer_reach` still reads `TEST_ONLY` on `from_sweep` (population now 5,
  `LIVE=4`, residue still exactly 1). `from_flag` is live; `from_sweep` is not.
- **The residue is not closable by editing, and that is now tested.** No
  on-disk record satisfies `from_sweep`'s contract — `CONVOY_W75_NULL` and
  `HEADON_W75_NULL` are `NullRung`s, `LOUDER_NULL` is a dict, and none carries
  `.n` or `.n_out_of_band`. The only consumable input is a walk that has not
  been taken (64 closed-loop runs, user-blocked, over the 2-minute sim limit).
- **Cost avoided, then paid anyway — for a different reason.** Killed the
  first suite ~1 min in on noticing the pending `docs/decisions.md` write is
  inside the test read surface; writing docs first is what D-044's ordering
  table prescribes and it was the right call. But the suite still came back
  red on `test_loop_reach.py::test_recorded_reading_covers_exactly_todays_targets`:
  the new agreement test loops over `(True, False, None)`, which enters
  `loop_reach`'s population-claim corpus, and the frozen `READING` no longer
  covered it. Took the reading, recorded the row (`SAMPLED n=21`), re-ran.
  Third consecutive cycle to pay for a second 18-minute suite.

## North-star delta

- Suite **2434 passed** (2429 + 5 new), rc=0.
- **No movement, and none claimed.** No controller, representation, dynamics
  or sim code; `unsafe_rate` 0.0000 / `min_clearance` 0.3579 / `success_rate`
  1.0000 unchanged. 0 sim runs.
- One latent mis-report removed from the licence reader — a `None` flag can no
  longer be pooled as a refusal.

## Key learnings

- **A rule with two statements drifts at the branch nobody exercises.** The
  two sites agreed on `True` and `False` and disagreed only on `None`, which
  is the input no current record produces — so the suite was green and the
  divergence was invisible. D-047's "one statement of itself" applies to
  *derivation rules*, not just registries.
- **"Give X a production caller" is only a wiring job if a production input
  exists.** Three cycles priced this as wiring; the constructor's input
  population on disk is empty. Checking the *inputs* — not the call sites —
  is what separates a wiring job from a blocked one.
- **The residue instrument was right to stay red.** Closing it by making a
  disk record fit the duck type is what D-188 did and D-189 caught.
- **The cheap pre-check must include the instruments that watch the corpus,
  not just the module under edit.** A 0.09 s run of
  `test_seed_count_licence.py` was green and bought nothing: the failure was
  in `test_loop_reach.py`, which watches *every* test file for new
  population-claim loops. Any cycle adding a looping assertion is editing
  that corpus whether it means to or not. The pre-check that would have paid
  here is `test_loop_reach.py` + `test_citation_audit.py` + the census pins —
  seconds, and they are the tests whose population is "the repo".

## Recommended next 1–3 priorities

1. Triage the 88 module-level public functions with no non-test caller
   (STATE #2, measured by D-189) — is there a large write-only instrument
   surface? 0 sim, one pass.
2. Decide `from_sweep`: keep as the re-walk landing site (user-blocked) or
   delete. The pinning test makes either choice cheap and explicit.
3. Point the constitution's Phase-3 pin check at `inert_surface pins` and
   correct the stale 4a-ter prose. Doc-only, now 16 cycles old.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/seed_count_licence.py, eval/mppi_sandbox/tests/test_seed_count_licence.py, docs/decisions.md
- TSV row appended: yes
