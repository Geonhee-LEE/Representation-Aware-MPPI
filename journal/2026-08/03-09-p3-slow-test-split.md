# The suite split at fixture scope — and the CI that had been red for 24 hours

- **Cycle**: 2026-08-03 09:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic` (in-queue, PR #67)
- **TODO**: STATE #1 / Q-051 — mark or split the slow tests (gate-1 blocked; no Notion)
- **Phase**: P3
- **Status**: keep

## What I tried

- Took STATE #1 (`slow` marker) because it was the only ungated item and it
  compounds every cycle it is deferred. Before writing anything, checked the
  branch's actual CI — which no cycle had done.
- Measured the suite per-file in parallel (the one-process run blew a 900 s
  `timeout` before flushing its `--durations` report), marked the 51 tests over
  a 2.0 s `call` threshold, and measured again.
- That fell short, so profiled the *remainder*, found the real cost unit, and
  redid the marking at class scope over a 3.0 s all-phases threshold.
- Shipped `eval/conftest.py` (`slow` marker, `--slow` opt-in, two anti-silence
  guards) and split `sandbox-ci.yml` into `fast` + `slow` jobs.

## What worked / what failed

- 🔴 **The premise of STATE #1 was wrong, in the expensive direction.**
  `gh pr checks 67` reads **fail**. The branch's CI has been red for **14
  consecutive runs** since 2026-08-02T10:09Z, and the last six were killed at
  exactly **10m15–17s** by the job's `timeout-minutes: 10`. For 24 hours every
  cycle reported `sandbox:pass=357/357` from a **local** run while D-016's
  actual verification gate was failing. STATE annotated #68/#69 with "CI green"
  and #67 with nothing — the absence was the signal, and nobody read it.
  (The eight earlier runs ended in `failure` at 5–8 min, a different regime;
  logs have expired and every file passes locally now, so I am **recording that
  and not explaining it**.)
- 🔴 **Per-test marking does not remove a class-scoped fixture's cost — pytest
  recharges it to the first surviving sibling.** Marking 51 tests by `call` time
  cut 628 s → **338 s** only. Profiling the remainder showed the single largest
  item was a **97.65 s `setup`** in a class whose every `call` was under 2 s, so
  it was never a candidate. My measurement was blind by construction: the grep
  kept `--durations`' `call` rows and dropped `setup`/`teardown`.
- ✅ Re-measuring with all phases aggregated **per scope** gave the right unit —
  36 classes + 6 module-level functions over 3.0 s. Fast half: **628 s → 115 s**
  (230 passed / 127 skipped / 1 xfailed).
- ✅ Collection splits exactly **127 slow + 231 fast = 358**, so the `slow` CI
  job cannot pass vacuously — the failure mode that would have made this change
  a silent coverage cut instead of a split.
- ⚠️ I first set the slow job's timeout to the measured figure (30 min). That is
  the same mistake the old job made. A one-process run costs ~1.5× the sum of
  its per-file runs, and the runner is slower than this box — corrected to 60.

## North-star delta

- **No avoidance or tracking number moved.** Pure infrastructure.
- But the head-of-line PR's verification gate goes from **failing** to running,
  which is a precondition for any number on this branch being believed at all.
  26 cycles of D-027…D-030 evidence sat behind a red check.
- Every later cycle's local verification drops from >10 min to **115 s**.

## Key learnings

- **The absence of an annotation is not the absence of a problem.** STATE listed
  "CI green" on two PRs and nothing on the third for 26 cycles. A field that is
  sometimes omitted cannot be read as a negative — which is why Q-053 leans on
  *naming the surface in the metric string* rather than on remembering to look.
- **A cost that hides in `setup` is invisible to any instrument that reads
  `call`.** Same shape as D-030's relative-guard blind spot and D-028's
  denominator: the instrument was fine, its *scope* was wrong. Marking below
  the fixture boundary moves cost rather than removing it.
- **Measure after the intervention, not just before.** The 2.0 s pass looked
  right on paper and delivered less than half of what it promised; only
  re-profiling the remainder exposed why.
- **Do not set a ceiling to the measured value of the thing it bounds.** That is
  precisely how the 10-minute CI timeout became the thing under test.

## Recommended next 1–3 priorities

1. **Confirm the `slow` CI job green on the pushed commit** — this cycle
   verified the fast half and the selection counts; the slow half's local run
   was still going at cycle end (result appended to the TSV next cycle).
2. **Q-053's minimal repair: rename the metric string to name its surface**
   (`sandbox:pass=` → `sandbox-local:pass=`), so "local only, no CI" is visible
   in `RESULTS.md` instead of inferable from a missing STATE annotation.
3. **Reproduce D-030's redundancy on a second scene** (was STATE #2) — now the
   top *technical* ungated item.

## Artifacts

- PR: #67 (in queue, gate-1 blocked 52nd cycle) — no new review bandwidth spent
- Files touched: `eval/conftest.py` (new), 18 × `eval/mppi_sandbox/tests/test_*.py`
  (+48 lines, markers + imports only), `.github/workflows/sandbox-ci.yml`,
  `docs/decisions.md` (D-031), `docs/deliberations.md` (Q-051 resolved, Q-053 filed)
- TSV row appended: yes
