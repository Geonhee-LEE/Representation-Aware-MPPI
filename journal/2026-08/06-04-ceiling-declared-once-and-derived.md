# The ceiling raise, derived — and there is room for exactly one more instrument

- **Cycle**: 2026-08-06 04:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — raise the `slow` ceiling above the collapsed floor, with headroom
- **Phase**: P3
- **Status**: in_progress

## What I tried

- Did the raise D-092 proved mandatory: `timeout-minutes: 120 → 360` on the
  `slow` job, discharging the 1176 s `INSUFFICIENT` that has blocked this
  branch's CI since 2026-08-04.
- Built `eval/mppi_sandbox/declared_ceiling.py` so the number is **derived**
  rather than chosen: the requirement is the measured collapsed floor times a
  headroom factor, and the declared value is read from the workflow — the only
  place it is enforced — instead of from `nested_suite_cost`'s hand-typed copy.
- Added `runway()`: how many more full-suite runner classes fit under the
  platform's own job kill before *no* `timeout-minutes` value works.
- Re-anchored the four tests that went red, each of which turned out to be a
  claim about the **old** ceiling rather than about the thing it named.

## What worked / what failed

- 🔴 **The runway is 1, and I had estimated 2.** At 7 runner classes the
  requirement is 325.7 min and still declarable; at 8 it is 372.3 min and no
  value works. This branch adds runner classes at roughly one per three cycles,
  so the next instrument module that shells out to the full suite ends the
  ceiling as a repair mechanism entirely. My estimate was wrong by the whole
  remaining margin — which is the reason it is a function and not a sentence.
- ✅ **This is why the raise goes to 360 and not to the 280 the requirement
  alone justifies.** A ceiling is a kill switch, not a reservation: it costs
  nothing when the job finishes early. Declaring 280 would buy exactly one more
  raise cycle. Taking the whole remaining runway now means the next red reading
  is `UNENFORCEABLE` — a different problem with a different fix (co-install the
  recorders, or cut the census subject), not a fourth number bump.
- 🔴 **The ceiling was stated twice and I found a third.** `timeout-minutes` is
  enforced in the workflow; `nested_suite_cost.SLOW_CEILING_SECONDS = 120 * 60`
  is a copy every `grade()` in the package measures against; and
  `test_ci_verdict.FIXTURE_CAPS` pins a third. D-047's defect class. `agreement()`
  now grades the copy against the workflow and a test pins `AGREES`.
- 🔴 **One of the four red tests was violating its own module's documented
  rule.** `ci_verdict.job_caps`' docstring warns that a historical run must be
  metered against *its epoch's* caps — and `test_caps_are_read_from_the_real_workflow`
  asserted `job_caps() == FIXTURE_CAPS`, i.e. live caps equal fixture-epoch caps.
  It passed for two days only because no ceiling had moved since the fixtures
  were taken. It now asserts over the job **names** (the rename guard it was
  written for) and `FIXTURE_CAPS` is frozen at its epoch where it belongs.
- 🔴 **A passing test stopped discriminating and would have stayed green.**
  `test_sufficiency_is_certified_from_the_upper_bound_not_the_ledger` feeds an
  optimistic 1-class ledger and requires `INSUFFICIENT`. Under the raised
  ceiling *both* bounds fit, so it would have passed whichever bound the code
  consulted — a pass that tests nothing. Re-graded against the ceiling where the
  upper bound does not fit. The other two reds (D-092's headline, D-089's burn
  share) are true statements about the 7200 s ceiling and are now pinned to it
  explicitly, with live companions asserting what changed.
- ⚠️ **The 360 cap is declared, not measured here.** This session had no network
  permission to fetch the documented limit, so it enters as an *input*:
  `runway(cap_minutes=None)` returns `None` rather than a number, and `grade`
  reads `CAP_UNVERIFIED` instead of `UNENFORCEABLE`. It is corroborated inside
  the repo — `ci_verdict.job_caps`' docstring, written by an earlier cycle,
  names the same 360-min default — which is provenance, not verification.
  Declaring 360 is safe under every reading of the cap (equal to the default, or
  clamped by the platform, or conservative), which is the other reason it is the
  value to pick.

- 🔁 **Census cost, 29th consecutive cycle — and the first paid by this
  entry's *prose* rather than by its code.** The D-094 text spelled the headroom
  factor as a decimal, and that spelling is the same number D-038's registered
  `horizon_weight_swing_cited` claim uses. A bare numeral carries no token either
  way, so `citation_audit` could not tell a new quantity from a citation of the
  old one and put it in the **rejected-by-silence** bucket — exactly the drift
  that test exists to catch. Raising the threshold is the one move it forbids,
  so what changed is my spelling.
- 🔴 **Then the first draft of the paragraph explaining that collision quoted
  the colliding number, taking the suite from 1 red to 4.** One of the three new
  hits was written as a multiple, which scores as a genuine citation candidate
  rather than a bare mention. Explaining a spelling collision requires writing
  the spelling, and writing it is what the audit catches — so the paragraph now
  names the claim and never writes the numeral at all. `key_conflation`'s defect
  class (one spelling, two unrelated quantities), the same shape D-093 found
  inside `collapse_key`, caught here in prose before it reached the PR. The
  residual limitation is real: a bare numeral is not a citation, and the silent
  bucket is where ambiguous spellings accumulate.

## North-star delta

- **No avoidance or tracking number moved — sixty-second consecutive instrument
  cycle.** Scenes able to contribute an avoidance number: 5, reportable: 4.
- What moved: `nested_run_ledger.grade()` reads `SUFFICIENT` for the first time.
  The CI path from this branch to a verdict is, as far as any local instrument
  can tell, now unobstructed — the last arithmetic blocker is gone.
- The cost of that is now bounded and named: **one** more full-suite runner
  class before the ceiling stops being a repair at all.

## Key learnings

- **A number that tracks a live value cannot also be evidence about a past
  one.** Three of the four reds were findings silently re-pointed at whatever
  the workflow says today. Pinning the epoch is what keeps a measurement a
  measurement after the thing it measured is fixed.
- **Raising a threshold can make a test stop discriminating without making it
  fail.** The upper-bound-vs-ledger test went green for the wrong reason; only
  reading *why* each red was red surfaced it. Blanket-updating the four to match
  the new numbers would have shipped it.
- **The cheapest guard against a two-place constant is to read the enforcing
  place.** Deriving `SLOW_CEILING_SECONDS` away entirely would be better still;
  `agreement()` is the checked-copy fallback and says so.
- **Estimate, then run, then report the run.** The runway estimate was off by
  100% in the direction that reads comfortable.

## Recommended next 1–3 priorities

1. **Read this branch's CI with `ci_verdict` once the push lands.** Every local
   blocker is discharged; the authority has not spoken since 2026-08-04 and only
   a real run can confirm the raise did what the arithmetic says.
2. **Derive `SLOW_CEILING_SECONDS` away** — `declared_ceiling.ceiling_seconds()`
   exists; the copy remains only because changing an import-time constant mid-
   cycle was the riskier half.
3. **Treat `runway() == 1` as a standing constraint on new instruments**: the
   next module that shells out to `DEFAULT_SUITE` should co-install with an
   existing recorder rather than declare a new full-suite runner.

## Artifacts

- PR: pending merge (`autoresearch/p3-epistemic-shadow-cost-critic`, PR #67)
- Files touched: `.github/workflows/sandbox-ci.yml`,
  `eval/mppi_sandbox/declared_ceiling.py`,
  `eval/mppi_sandbox/nested_suite_cost.py`,
  `eval/mppi_sandbox/tests/test_declared_ceiling.py`,
  `eval/mppi_sandbox/tests/test_ci_verdict.py`,
  `eval/mppi_sandbox/tests/test_nested_run_ledger.py`,
  `eval/mppi_sandbox/tests/test_nested_suite_cost.py`
- TSV row appended: yes
