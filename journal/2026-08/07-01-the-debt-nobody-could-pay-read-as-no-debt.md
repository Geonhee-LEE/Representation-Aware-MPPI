# The exemption instrument was dark for four cycles, and the reason was an unmeasured price

- **Cycle**: 2026-08-07 01:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #3 — "`results/*.tsv` IS test-read surface now; D-044's ordering table has gone stale"
- **Phase**: P5
- **Status**: keep

## What I tried

- Went to fix D-044's ordering table, which claims `results/*.tsv` is "read by
  no test (checked)" while `cycle_artifacts` (D-105) demonstrably reads it.
- Asked `inert_surface` rather than the table, since that module exists
  precisely to *derive* the inert set instead of typing it. It answered that
  **all four** pins were stale, not just `results/` — so the instrument was
  grading nothing and every cycle since 08-06 06:00 had paid a second full
  suite run.
- Measured the reader-set deltas, found them monotone (8 files entered, none
  left), and built the incremental re-take that fact licenses: `entrants()`,
  `departures()`, `compose()`, `reprobe()`, verdict `INERT_COMPOSED`, and a
  `COMPOSITION_CAP` so a composed pin cannot carry inherited debt forever.
- Re-took all four pins over their entrants and transcribed the verdicts.

## What worked / what failed

- 🔴 **HEAD was red before I touched anything, and D-106's own push is what
  made it red.** `test_a_second_silent_cycle_makes_the_first_one_red` asserted
  that `journal/2026-08/06-18-*.md` is unpublished — a live reading of the
  repository, not an invariant. Last cycle pushed the branch, the journal
  became published, the finding was **discharged**, and the test went red for
  the one outcome it existed to encourage. Replaced with a constructed
  four-cycle scratch repo (two pushed, two not) that asserts the positional
  latency rule, plus the negative control it never had — one silent cycle alone
  must *not* be a finding.
- 🔴 **The decay was never silent. It was named, and the name was accepted.**
  I first wrote this up as "nothing said so"; that is false and the tests
  refute it — `stale_pins` reported it and four tests asserted it by name. What
  actually happened is worse: the reading *a re-probe is owed and is not
  affordable in a cycle* was carried for four cycles as a documented condition,
  so the instrument sat dark under a green suite. **A named debt nobody can pay
  reads exactly like a debt nobody has.**
- 🔴 **And the price that justified accepting it was never measured.** The
  superseded test reasoned "one probe costs hours" because `STATE.md`'s readers
  include nested-suite spawners. That contradicted the module's own pin note
  (~34 min for all four, D-095), and it answered the wrong question anyway: a
  stale pin does not need a full probe, only what **entered** since. Measured:
  8 entrant files, worst single file 48 s, **~3.5 min for all four re-takes**.
  The debt was affordable the whole time and nobody had priced it.
- ✅ **All four re-take `INERT_COMPOSED`**, outcomes unmoved across the
  mutation (131 / 34 / 34 / 109). `stale_pins()` is `()`, `inert()` is true for
  all four, and `filter_drift` ignores exactly the write set D-044's Phase-4
  order produces. The second-suite-run tax is gone.
- ✅ **STATE #3 answered by measurement, and both halves of it are true at
  once.** `cycle_artifacts` *does* read `results/*.tsv`, so D-044's "(checked)"
  is false **as a static claim** — and the probe says that read does not move an
  outcome, so the exemption survives. The ordering rule does not need changing;
  the *basis* did, from a hand-check to a measurement.
- 🔴 **Composition is weaker than measurement and is spelled so.** The carried
  half was measured on `d6b60c8`; `readers_key` is a set of *names*, so a reader
  that keeps its name and changes content is invisible to the premise check.
  Hence the distinct verdict, `Pin.carried`, and the cap — priced and bounded
  rather than absorbed into `INERT`.
- 🔁 **Census cost, 35th cycle: pool 22 → 24, `NO_REGISTRY` 13 → 15.** One
  entrant is `reprobe`, genuinely new. The other is **`probe`, which is not** —
  it gained a `tests` parameter and a guard clause, changing nothing about what
  it computes and everything about whether the scan sees it narrowing. Second
  cycle in a row of a pool member entering by **spelling** (D-106's
  `misscored_probes`). Numerator unchanged at 4.

## North-star delta

- **No avoidance or tracking number moved — seventy-third consecutive
  instrument cycle.** Scenes able to contribute an avoidance number: 5,
  reportable: 4, unchanged.
- What did move is per-cycle cost: the second full suite run every cycle has
  paid since 08-06 06:00 is removed, which is ~10 min back on a 15 min EXECUTE
  budget. That is throughput, not capability.
- HEAD is green again, and it was red on arrival for a reason no CI run would
  have attributed correctly.

## Key learnings

- **A test whose subject is `origin` cannot be asserted in a repo whose `origin`
  the cycle itself moves.** The 06-18 assertion was red *because the project did
  the right thing*, and a test that a correct action turns red is read as a
  regression by whoever meets it next.
- **A debt that is named, priced as unaffordable, and never re-priced is
  indistinguishable from an absent debt.** The staleness was visible in three
  places for four cycles. What made it survive was one unmeasured cost estimate
  sitting in a docstring.
- **Ask what the *delta* costs, not what the measurement costs.** The full probe
  really is expensive; re-taking a stale pin never needed one. The 10× came from
  changing the question, not from optimising the answer.
- Composition buys affordability with an un-re-measured premise. That is a fine
  trade *if it is capped* — uncapped it reproduces the exact decay it repairs,
  wearing a measurement's clothes.

## Recommended next 1–3 priorities

1. **Correct D-044's ordering-table wording** in the constitution: the TSV row
   is `results/`-covered and *is* test-read surface, exempt by a probe rather
   than by "read by no test (checked)". The order itself stays.
2. **Pay the mirror debt** (`disputed` is `unsupported`'s `^` to its `&`) —
   carried three cycles now.
3. **Make `readers_key` content-sensitive**, or state its name-only bound as a
   reading: a reader that changes content under a fixed name is exactly the
   drift a composed pin cannot see.

## Artifacts

- PR: #67 (open, this branch)
- Files touched: eval/mppi_sandbox/inert_surface.py, eval/mppi_sandbox/tests/test_inert_surface.py, eval/mppi_sandbox/tests/test_cycle_artifacts.py, eval/mppi_sandbox/tests/test_liveness_derivation.py, docs/decisions.md, journal/2026-08/07-01-the-debt-nobody-could-pay-read-as-no-debt.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: yes
