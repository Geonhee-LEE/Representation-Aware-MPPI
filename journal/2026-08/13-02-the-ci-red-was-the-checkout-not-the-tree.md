# The CI red was the checkout, not the tree

- **Cycle**: 2026-08-13 02:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `q137-ci` Call `ci_verdict` in Phase 1 / read the first CI verdict in thirteen runs
- **Phase**: P3
- **Status**: keep

## What I tried

- Read the CI run D-227's shard was supposed to unblock. It **worked**: all 8
  `fast` shards reached a verdict (slowest 23m28, under the 30-min ceiling),
  ending twelve consecutive cancellations. The verdict was **red** — 19 failures
  across 5 shards, against a local suite that was green 2699/2857 on the *same
  tree*.
- Refused to attribute the red before partitioning it. Built the discriminator:
  a clone at **full depth with no receipt store**, which separates "CI lacks the
  history" from "CI lacks the gitignored store".
- Measured 18 of the 19 failures passing in that clone, and shipped the fix the
  measurement pointed at: `fetch-depth: 0` on both suite jobs.
- Added `ci_checkout.py` + 17 tests so the setting is pinned by a reading rather
  than by a comment.

## What worked / what failed

- **The partition was clean and it inverted the obvious reading.** 16 failures
  (`assert_reach` ×9, `cycle_artifacts` ×4, `push_claim_gate` ×2,
  `inert_surface` ×1) plus `tsv_timestamp` and `paired_step` — and that 4-file
  subset reports **110 passed in 10.78s** at full depth, which is a targeted
  run and not a suite count. Exactly one failure survives: `test_quoted_counts.py
  ::test_the_reach_is_a_boundary_the_receipts_derive_not_a_constant`, which
  reads `results/receipts/`. That directory is **gitignored by decision**, so no
  checkout config can fix it (Q-138).
- **`actions/checkout@v4` declared no `fetch-depth` in either job.** The suite
  reads history as data — `cycle_artifacts` assigns rows by commit date,
  `tsv_timestamp` classifies typed-vs-clock-read against it, `assert_reach`
  takes readings at the run commit — so CI was running those modules over a
  **one-commit graph** while local ran them over 636. Neither side was buggy.
- **The timing gap is the louder half and I did not chase it.** Shard 1 spent
  **753s** in CI on tests that take **10.78s** at full depth here. If shallow
  checkout is also what made the suite slow, then it — not suite size — may be
  the real cause of the twelve cancellations, and D-227's 8-way shard treated a
  symptom. Recorded as Q-138; **not claimed**, because I did not measure it.
- No census bill: 187 passed across the four census files with the new test file
  in place.

## North-star delta

- **No planner movement.** Zero controller / representation / dynamics code
  changed; this is the 18th consecutive instrument-repair cycle.
- **The authority over every planner claim on this branch is restored in
  principle.** D-224/D-225/D-226/D-227 have rested on local receipts alone since
  2026-08-11T23:28Z. This is the first cycle that can expect a CI verdict that
  *means* something — but the confirmation is pending, not delivered.

## Key learnings

- **A green local suite and a red CI suite can both be correct.** The project's
  constitution says CI "is the only authority for the pushed tree" — true, and
  incomplete: CI is only an authority over the tree if it is handed the same
  *corpus*. For a suite that reads its own repository, the commit graph is part
  of the input, and checkout depth silently truncates it.
- **The absent-key lesson has now cost twice.** `declared_ceiling` exists
  because an absent `timeout-minutes` is a default, not an absence.
  `fetch-depth` is the identical shape and was read the identical wrong way.
  `ci_checkout` states it once more; the third instance should generalise the
  rule rather than add a fourth module.
- **Thirteen runs of silence hid a structural fact, not a flake.** The suite had
  been unable to pass in CI for as long as anyone could not see it. Q-137's
  proposal — call `ci_verdict` in Phase 1 — would have surfaced this on the
  first cycle; it surfaced by chance on the second, again.

## Recommended next 1–3 priorities

1. **Read the next CI run and confirm the partition** — the fix is a prediction
   (18 of 19 clear) and the run decides it. If the timing also collapses, Q-138
   answers itself and D-227's shard becomes reversible.
2. **Q-138: decide the receipt-store test's CI status** — skip-when-absent vs
   commit a datable fixture. One test, needs judgment, not budget.
3. **Wire `ci_verdict fetch_latest` into Phase 1 (Q-137)** — still unbuilt,
   still the cheapest item, and this cycle is its second argument.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: `.github/workflows/sandbox-ci.yml`, `eval/mppi_sandbox/ci_checkout.py`, `eval/mppi_sandbox/tests/test_ci_checkout.py`, `docs/decisions.md`, `docs/deliberations.md`
- TSV row appended: yes
