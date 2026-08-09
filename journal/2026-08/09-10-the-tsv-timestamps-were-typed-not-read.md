# The strand cleared, and the timestamp column turned out to be typed rather than read

- **Cycle**: 2026-08-09 10:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: D-112 strand obligation (outranks the decision tree)
- **Phase**: P3
- **Status**: keep

## What I tried

- `cycle_artifacts stranded` came back **rc=1** naming the 09:00 journal, so per
  D-112 that was this cycle's first obligation and the decision tree never ran.
  Diagnosis: 09:00 committed its work (`527c0c8`) *and* its journal, then wrote
  an uncommitted correction to that journal, and died — no TSV row, no push.
  `cycle_wallclock` graded it **OVERRUN 21m53**: it had time to take a receipt.
- Committed the orphaned journal correction, re-took the count through
  `push_preflight record`, appended the missing TSV row, pushed.
- With the suite running I audited what the 09:00 journal's own confession
  ("do not estimate elapsed time from inside the cycle") implied for the
  *structured* record, rather than the one prose sentence it scoped itself to.

## What worked / what failed

- 🟢 **The strand cleared.** `527c0c8` + the correction + the TSV row are on
  `origin` under the already-open PR #67, so gate 1 is satisfied by D-140
  (continuing an open PR adds no review bandwidth; 6 branches still queued).
- 🟡 **The defect was already known, and I nearly wrote it up as a discovery.**
  `cycle_artifacts`' own module docstring refutes the `timestamp` column as a
  dating key in as many words — *"``timestamp`` (hand-typed) … a cycle that
  overruns types the hour it finished in"* — and cites the same shape I
  re-derived (`2026-08-06T04:05` carrying the 02:00 cycle's work). It routes
  around the column via `commit` ∩ `git blame`. So the mechanism is prior art;
  what follows is a **measurement of its extent**, which the module explicitly
  leaves open (Q-099), plus a test that turns it into a refusal.
- 🔴 **40 of the repo's 181 TSV rows are stamped later than the commit that
  introduced them** — physically impossible for a clock reading. `git blame`
  gives each row's introducing commit, so the test needs no external log:

  | signal | value | expectation |
  |---|---|---|
  | rows compared (all 34 TSVs) | 181 | — |
  | `seconds == 00` | **63** | ~3.0 by chance |
  | stamped after own commit | **40** (22%) | 0 |
  | ...of those, `seconds == 00` | **36** | — |
  | worst overshoot | **+128 min** | — |

  The two signatures agree, which is what makes this a mechanism and not a
  coincidence: a hand-typed stamp lands on a round minute, and a hand-typed
  stamp is what is wrong. All 40 sit in this branch's TSV, first appearing
  **2026-08-04** — so it is recent executor behaviour, not repo-wide history.
  The attribution survives the obvious objection: exactly 2 of 181 rows were
  ever rewritten (`04c445f`, `ac2459b`, both correcting a `metric` count, not a
  timestamp), and for those blame names the *later* commit, which shrinks the
  measured overshoot — so 40 is a floor, not a ceiling.
- 🔴 **The mechanism is the one 09:00 named and under-scoped.** Cycles compute
  the finish stamp as *start hour + self-estimated elapsed* instead of calling
  `date`. The estimate runs ~3× long: the 07:00 and 08:00 cycles self-reported
  "~85 min" and "~82 min" against wrapper-recorded **28m01** and **28m38**, and
  stamped their rows 08:22:00 and 09:20:00 — +55 and +52 min past the commits
  that carry them. The same two cycles stamped their `🤖 Cron activity` lines
  07:00 and 09:20 where the wrapper says 07:28 and 08:28, while 04:45 / 05:49 /
  06:35 match their end times to the minute — the defect starts where the
  self-estimate does. 09:00 caught this in one sentence about a *walk cost* and
  fixed the sentence; the same reflex had been writing the `timestamp` column
  for six days and nothing looked.
- 🟡 **Three of my own inferences died on contact with evidence, all in the
  same direction — reaching for a mechanism before the measurement.**
  (a) "09:00 never produced a receipt, so `receipt-gated` is a phantom claim" —
  refuted by `push_preflight.py:638`: `record` unlinks its own `--out` path at
  start, so my 10:00 invocation destroyed the evidence before I looked at it.
  (b) "08:00 ran 82 min and overlapped 09:00" — refuted by the wrapper log's
  start/end brackets (28m38, and line 20 holds a lockfile anyway).
  (c) "hand-typed rows are ~an hour off" — refuted by the deltas: rows are
  *legitimately* stamped after the commit they name, mean +11.5 min, so the
  two-sample eyeball didn't generalise. Only the blame-based test survived.

## North-star delta

- **No movement, and this cycle should not claim any.** Zero sim runs, zero
  controller/representation code; the headline stands where D-136 left it —
  `unsafe_rate` 0.0000 / `min_clearance` 0.3579 / `success_rate` 1.0000 over
  5 cells / 40 seeds. Replication census unchanged at 3/4, `unreplicated (75,)`.
- What moved is the **trust interval on the evidence base**: 22% of the rows
  that RESULTS.md aggregates carry a time that never happened. Scope honestly:
  I audited the `timestamp` column only, so this says nothing either way about
  `metric` / `status` / `description` — but any claim ordered by TSV time is
  unsafe, which matters directly for P5, where these rows become the eval
  record.

## Key learnings

- **A confession scoped to one sentence is a bug report with the repro
  deleted.** 09:00 found the estimate-don't-read reflex, corrected the prose it
  had produced, and stopped. The same reflex was writing a structured column
  that a `git blame` one-liner falsifies. When a cycle catches itself
  fabricating a number, the next question is *where else does that number go*.
- **The repo's response to a known-bad field was to route around it, not to
  stop writing it.** `cycle_artifacts` diagnosed the hand-typed timestamp,
  built a two-key intersection to avoid it, and left the column being written
  wrong every cycle — so the defect is contained where it was noticed and live
  everywhere else (`RESULTS.md`, and P5's eval record next). Routing around a
  bad input protects the one consumer that knows; fixing the writer protects
  the ones that do not exist yet. This is the cheaper half done and the durable
  half skipped.
- **Every guard here checks that a claim is measured; none checks that a
  recorded number was read rather than typed.** The receipt gate (D-082) covers
  pass counts, `tree_provenance` covers which tree, `citation_audit` covers
  quoted magnitudes — the TSV timestamp is inside none of them.
- **Destroying evidence while investigating is easy and quiet.** `record`
  unlinking its own output is correct (a stale receipt is worse than none), but
  it meant my first forensic act erased the artifact I then reasoned about. Read
  the tool before running it at the scene.

## Recommended next 1–3 priorities

1. **Ship `tsv_timestamp_audit` + tests, and fix the writer** — turn the `git
   blame` one-liner into a guard (a row whose stamp postdates its introducing
   commit is a refusal) and make the EXECUTE-phase row read `date` instead of
   typing an estimate. The guard is the cheap half; the writer fix is the half
   `cycle_artifacts` skipped. It also gives Q-099 a lower bound where the module
   left the population unsettled. Deliberately *not* done this cycle: new tests
   mean a second ~13 min suite, which is what stranded 09:00. ~30 min,
   sandbox-executable (D-016).
2. **Replicate `w = 75`** — still the last `unreplicated` rung and the island's
   lower edge; closes `ReplicationCensus` to 4/4. Protocol unchanged, 64 runs.
3. **Fix `shift_census`'s absent-cell path (Q-121)** — unchanged for seven
   cycles now.

## Artifacts

- PR: #67 (open, continued per D-140)
- Files touched: `journal/2026-08/09-09-*.md` (correction),
  `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV row appended: yes — and stamped from `date`, not from an estimate
