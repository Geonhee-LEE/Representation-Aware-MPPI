# What the suite actually spends: 59% of it is the project checking itself

- **Cycle**: 2026-08-26 03:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `Q-203` derive which lam tests actually roll out (discharge + compare)
- **Phase**: P3
- **Status**: in_progress

## What I tried

- **D-112 Step 0 fired rc=1 and took the cycle.** Three commits from 02:00
  (`5010a3f`, `1d8be44`, `d580e0a`) sat finished-but-unpushed: the 02:00 receipt
  came back red on four censuses, the cycle repaired all four, verified them
  green individually in 15.60 s, and then correctly refused to push on a
  partial check. One full-suite receipt licenses all three commits; nothing
  needed re-deriving.
- **Ran `lam_rollout compare` on the sidecar 02:00 had already paid for.**
  STATE's next-actionable #2 called this "seconds, no suite" and it was — but
  the log lives at `/tmp/suite-receipt.json.log`, which this cycle's own receipt
  overwrites, so the first act was `cp` to `/tmp/lam-durations-0226-02.log`.
  A free reading that a later step destroys is not free; it is free *once*.
- Read the composition of the measured set rather than just its size, which is
  where the actual finding was hiding.

## What worked / what failed

- **The comparison refutes the instrument D-473 shipped one cycle earlier:
  `both=15 derived_only=69 measured_only=230`.** The static walk names 84
  tests; the measured set holds 245; they share 15. D-473's headline — "a
  static walk finds 84 tests" — is true only in the sense that the walk emits
  84 names. 82% of them are not in the expensive population, and the walk misses
  94% of it.
- **But the two instruments are not measuring the same thing, and that is the
  real finding.** `measured_rollout_tests` thresholds on **duration ≥ 1.0 s**,
  which is a proxy for "rolls out" and a poor one. The top measured entries are
  not rollouts at all: `test_guard_reflexivity::test_report_names_its_own_findings`
  at **304.40 s**, then five `test_exemption_masking` entries at 167–242 s. Those
  are meta-guards — the project checking its own checking. Near-disjointness is
  what you get when a static rollout walk is compared against a wall-clock
  threshold; it indicts the proxy, not only the walk.
- **I got the quantification wrong on the first pass and caught it before the
  receipt — the corrected number is much larger.** The first reading summed all
  526 nodes across the log for 3837.2 s and reported meta-guards at 59.3%. That
  sum is not a suite total: `nproc` is 16 but **xdist is not installed**, so the
  14 `--durations=40` blocks are not workers — they are **nested pytest runs**
  spawned by meta-guard tests, each printing its own truncated top-40. Summing
  across them double-counts (an inner run's time is *contained in* the outer
  test's reported duration) and no single block is a complete census.
- **Read correctly, block 10 is the outer session — its top-40 sums to 1280.5 s
  against the receipt's 1281.95 s wall.** So the whole suite is ~40 tests plus
  noise. Within it: **22 meta-guard tests = 1248.1 s = 97.5%.** And it narrows
  further to one file — **16 `test_exemption_masking` tests = 1133.5 s = 88.4%
  of the entire suite**, six of them 165–242 s each. The largest test that is
  not a meta-guard is **12.5 s**.
- **So the rollout tests are, to a first approximation, free.** Four cycles have
  been spent trying to enumerate the lam rollout cascade in order to make the
  8-controller install affordable. The install is unaffordable because of
  `test_exemption_masking`, and no amount of rollout enumeration would ever have
  named it.
- **So Q-203's plan had the marker on the wrong set, and the right move is
  smaller than a marker scheme.** The stated goal was to mark rollout tests
  `@pytest.mark.slow` so `-m "not slow"` separates table assertions from rollout
  assertions and makes the install fit in one cycle. Marking the derived 84
  would buy back single-digit seconds. Deferring or reshaping *one file* buys
  back 88.4% — a 1282 s suite becomes ~150 s, which changes what a cycle can
  afford more than any of the last four cycles' work did.
- **No marker applied this cycle, deliberately.** `cycle_wallclock review`
  opened with the previous run at 40m58 against a 35-min budget and said cut
  scope. The discharge is the obligation; editing test files ahead of the one
  receipt that licenses three commits would risk a second red for a change that
  is not yet decided (which set gets the marker is now an open question, not a
  known answer).

## North-star delta

- **No movement on the metrics, and a cost finding that bears on all of them.**
  The P5 headline is still computed over 2/8 of the controller axis. P5 entry is
  2026-09-03 — eight days. The reason the axis has not widened is budget, and
  **88.4% of that budget is one guard file**. This is the first cycle in four
  that names something whose removal would visibly change what fits in 35
  minutes.
- Three commits' worth of finished work stopped being invisible: the strand is
  discharged, so `lam_rollout` and the four census repairs are on origin and in
  PR #67 rather than on one machine's disk.

## Key learnings

- **A free reading has an expiry.** The 02:00 sidecar was already paid for, but
  it sits at the exact path this cycle's receipt rewrites. STATE said "the log
  is already paid for"; it did not say "and the next receipt eats it". Copy
  first, read second — the ordering is one command and the alternative is
  re-buying 21 minutes.
- **Comparing two instruments tells you about the weaker one, and you do not
  know in advance which that is.** D-473 shipped the static walk as the answer
  and the duration reading as the free cross-check. The cross-check turned out
  to be the one measuring something else entirely — a ≥1 s threshold is a
  *cost* oracle, not a *rollout* oracle. Both readings are useful; they are just
  not answers to the same question, and `compare`'s three-way split silently
  presents them as if they were.
- **A parsed log has a shape, and `parse_durations` throws it away.** The
  function merges 14 blocks into one dict keyed by node id. That is correct for
  "what did this node cost" and wrong for "what did the suite cost", because the
  blocks are nested rather than parallel — and nothing in the reading says which
  it is. I summed the merged dict, got a plausible number (3837 s vs a 1282 s
  wall — a 3× discrepancy sitting in plain sight), and wrote it into a commit
  before checking `nproc` against whether xdist was even installed. The tell was
  there in the first reading and I needed a second pass to see it.
- **The expensive population was never the one under investigation, and it is
  narrower than "meta-guards".** Four cycles chased the rollout cascade to make
  the install affordable. It is one file — `test_exemption_masking` — at 88.4%.
  Worth stating plainly: that file exists to check that guard exemptions do not
  mask each other, which is a guard about guards about guards.
- Confirming D-473's own closing note from the other direction: a clean pass
  with a stated scope is not a clean tree, and a *named* set with a plausible
  size is not the *relevant* set.

## Recommended next 1–3 priorities

1. **Go straight at `test_exemption_masking` (Q-205)** — 1133.5 s of a 1281.95 s
   suite, 16 tests, six of them 165–242 s. Read *why* it is slow before deciding
   what to do: if it spawns a nested pytest per pair, the fix is likely a shared
   session-scoped run rather than a marker. A marker scheme over 84 rollout
   tests is now clearly the wrong lever and should not be built.
2. **Then re-measure the wall clock and say what a cycle can afford** — the
   whole point of four cycles of enumeration was a budget number. If the suite
   drops to ~150 s, the 8-controller install stops needing a marker scheme at
   all and D-457's 16+8 price can simply be paid.
3. **Then install the 8-controller table** — premise measured (D-472), collision
   resolution chosen (D-471 (b)). Unconfirmed for a fifth cycle.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: journal/2026-08/26-03-what-the-suite-actually-spends.md, journal/2026-08/26-02-name-what-rolls-out.md, docs/deliberations.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: yes
