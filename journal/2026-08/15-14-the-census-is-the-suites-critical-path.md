# The census subset is 8% of the files and 37% of the clock

- **Cycle**: 2026-08-15 14:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `<measure-q159>` Price the census subset properly (Q-159)
- **Phase**: P5
- **Status**: keep

## What I tried

- Took Q-159's own registered next action — the measurement D-280 refused to
  guess at: time the census test files under the **same sharding** as the full
  suite, since D-280's only affordable attempt ran them serially (400 s timeout)
  against a 14-shard 659 s control and therefore established nothing.
- Shipped `eval/mppi_sandbox/census_subset.py` + 13 tests. The population is
  **derived** from `exemption_control.REGISTRIES` and the split reuses
  `suite_shard.plan` / `default_jobs`, so subset and control cannot drift apart
  in concurrency — the precise defect being corrected.
- Made `Price` a different type from `push_preflight.Receipt` (no tree
  fingerprint, no counts), so no subset run can license a push by accident.

## What worked / what failed

- **243.5 s, 9 files in 9 shards, rc=0, against a 652 s full suite** →
  `SUBSET_MARGINAL`. Q-159's own thresholds say that is not option (a): the
  repair loop does not become cheap, it becomes 4.1 min.
- **The headline is the ratio, not the verdict.** The subset is **37.3%** of the
  suite's wall clock while being **7.9%** of its files (9 of 114). The census
  files are not a cheap corner of the suite — they *are* its critical path, and
  each one gets its own shard at 14 jobs, so the subset's floor is the slowest
  single census file and no further parallelism can lower it.
- **The derivation immediately corrected the question that asked for it.**
  D-280 (and Q-159, quoting it) both say "the 11 census test files". There are
  **9**: `REGISTRIES` holds 11 registries but `claim_scope` and `suite_memo`
  own two apiece. Nothing was watching that collapse because the count was
  prose, not a reading.
- The D-207 pin tax fired a **fourth** consecutive time — the same 5 pins
  (`STATE.md`, `JOURNAL.md`, `RESULTS.md`, `journal/`, `results/`) withdrawn
  because this cycle added a reader. Paid it by D-279's inverted write order
  (all local-only writes *before* the final suite) rather than by a second run.

## North-star delta

- **Zero, and that is now eight consecutive cycles.** No obstacle, path or
  clearance number moved. This is infrastructure that prices infrastructure.
- What it buys is a real budget number: a pin-moving cycle currently pays
  **21.7 min** of its 35 in pytest (two full suites); with a targeted repair
  loop that becomes **14.9 min**. The saving is **6.8 min ≈ 19% of budget** —
  material, but a fifth of what "make the repair loop cheap" implied.

## Key learnings

- **A subset's saving is bounded by its slowest member, not by its size.** The
  intuition behind a targeted runner is "9 files instead of 114, so ~8% of the
  cost". Under sharding that intuition is simply wrong: at 14 jobs each census
  file already runs alone, so the subset costs what its worst file costs. Any
  future "just run less of it" proposal on this suite should be priced against
  the slowest member first, which is one `--durations` read.
- **Q-159's thresholds were written before anyone knew the shape, and they still
  discriminated.** `< 3 min → (a)`, `near full → (b)/(c)` left the middle
  unnamed; the measurement landed exactly there. Encoding the third word
  (`SUBSET_MARGINAL`) rather than forcing a binary is what let the answer be
  "available but oversold" instead of a false yes or a false no.
- **The instrument corrected its own question's arithmetic.** Deriving the file
  set from the registry, rather than typing D-280's `11`, turned a prose tally
  into a reading and the tally was wrong. This is D-047 arriving one more time.

## Recommended next 1–3 priorities

1. **`<reprobe-stale-pins>`** — now **four** consecutive cycles have paid the
   withdrawn-exemption tax. D-259(a) priced `STATE.md` alone at >900 s, so it
   needs a cycle of its own and nothing else.
2. **Decide Q-159 in code or close it** — D-282 records the number and leans
   (c); shipping the targeted runner is a small wiring job on `census_subset`
   now that the price is known, but it is only worth it if pin-moving cycles
   stay frequent.
3. **Return to the branch's actual subject** — the epistemic shadow cost critic,
   untouched since 04:00 and still blocked on PR #68 for `cafe_blind_corner_v0`.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: `eval/mppi_sandbox/census_subset.py`, `eval/mppi_sandbox/tests/test_census_subset.py`, `docs/decisions.md`, `docs/deliberations.md`, `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV row appended: yes
