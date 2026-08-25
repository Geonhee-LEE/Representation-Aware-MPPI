# Narrowing is not discrimination — the narrow key cut the population 3.5× and moved the composition 1.4 points

- **Cycle**: 2026-08-11 13:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — measure the narrow key (call + recorded return value) over the 599-function population
- **Phase**: P3
- **Status**: in_progress

## What I tried

- D-196 deferred one measurement and named it: the **narrow key** — call syntax
  in `SCANNED_DOCS` **plus a recorded return value** — against the same
  population it had measured the wide key on. If it separated, `OPERATOR_INVOKED`
  became issuable and `reprobe` left the residue by measurement; if not, that was
  the answer.
- Measured both keys on one regex family so the comparison is internal: wide =
  backticked call with a non-empty argument; narrow = the same call site with a
  backticked SCREAMING_SNAKE token within 160 chars.
- Shipped the measurement as `key_discrimination.py` + 16 tests rather than a
  journal paragraph, because this is the **fourth** consecutive cycle to
  hand-roll a key measurement.

## What worked / what failed

- 🔴 **The narrow key does not separate.** Wide: **35** hits, 32 `LIVE`
  (non-`LIVE` 8.6%). Narrow: **10** hits, 9 `LIVE` (non-`LIVE` 10.0%). It cuts
  the matched set **3.5×** and moves the composition **+1.4 points**. `reprobe`
  is the lone non-`LIVE` hit — caught alongside nine `LIVE` names, i.e. picked
  out only by the coincidence that the others have callers. That is D-193's
  defect and D-196's defect, arriving a third time with a better hit count.
- 🟢 **So the answer is the one STATE priced as possible**: no verdict issued,
  no `OPERATOR_INVOKED` in `consumer_reach.VERDICTS`, `reprobe` stays `UNREACHED`
  and the residue stays **8**.
- 🔴 **The discipline as written down was the cheaper half of what those cycles
  did.** D-193 rejected on "48 hits, 43 `LIVE`"; D-196 on "25 hits, most `LIVE`".
  Both were recorded as *the key is too wide*. Width was never the operative
  fact — a key hitting 48 names of which 5 are non-`LIVE` and one hitting 6 of
  which 5 are non-`LIVE` are opposite verdicts at similar widths. A fourth cycle
  following "measure the key before keying on it" **to the letter** can still
  ship the defect, because hit count cannot see composition.
- 🟢 The verdict does not turn on the threshold: measured delta is 1.4 points
  against a 25-point margin, and the tests drive margins 2/10/50/90 to the same
  answer. Pinned, so a future cycle cannot rescue a key by moving the line.

- 🔴 **The suite came back red, and not on this change.** 4 failures, all
  `test_inert_surface.py`, all one cause: `stale_pins() == ('STATE.md',)`,
  `PINS_STALE: STATE.md — premise moved`. I did not touch `STATE.md`. The 12:00
  cycle rewrote it in **4c**, *after* its own green suite — so the red was
  introduced an hour ago and no suite has run since to see it.
- 🔴 **D-044's ordering table says `STATE.md` is "not in `SCANNED_DOCS`, read by
  no test, and never committed" and therefore safe to write after the re-run.
  The middle clause is false**: `inert_surface` reads `STATE.md` and pins its
  inertness. The table's own parenthetical "(checked)" is what makes this worth
  a decision rather than a fix — the claim was verified once and has decayed.
- 🟢 The remedy is the function this cycle was measuring a key *for*:
  `inert_surface.reprobe('STATE.md')`, "seconds instead of a 15m45 full probe"
  (D-183). `reprobe`'s caller arrived while the cycle was arguing about whether
  it had one. That is not evidence for the narrow key — the key still does not
  separate — but it is the sharpest possible statement of what `UNREACHED` was
  failing to describe.
- 🔴 **This cycle therefore does not push.** `push_preflight check` refuses
  without a green non-vacuous receipt on this tree, correctly. A second 20-minute
  suite does not fit the remaining budget (D-181).

- 🔴 **Sharper still: the package already knows.** `push_preflight check`
  refuses with *"the tree moved after the suite ran on a path that a test can
  read (changed: `STATE.md`)"* — and lists `JOURNAL.md`, the journal file and the
  TSV as `ignored inert`. So one guard classifies `STATE.md` as test-readable
  while D-044's ordering table classifies it as read by no test, **in the same
  package**, and the table is the one cycles follow. The disagreement is the
  finding; neither guard is new.

## North-star delta

- **No movement, and this cycle claims none.** No controller, representation,
  dynamics or sim code. `unsafe_rate` 0.0000 / `min_clearance` 0.3579 /
  `success_rate` 1.0000 unchanged; census attribution coverage still 0/6;
  `NO_GRADED_RUNG`. 0 sim runs.
- What moved: the residue's **8** is now held by a measured negative result
  rather than an unmeasured deferral, and the measurement is a suite member
  instead of a paragraph.

## Key learnings

- **A key is not validated by how few things it matches.** The reading is
  whether the composition of the matched set *moves*. `narrowing` and
  `discrimination` are two numbers and the module refuses to fold them into one
  — a key can narrow 5× and buy nothing, or barely narrow and separate cleanly;
  both directions are pinned synthetically.
- **A zero-hit key scores perfectly on discrimination**, which is why `VACUOUS`
  exists here for the fifth time in this package. An unmeasured *wide control*
  fails the same way: "few hits" with nothing to compare against is exactly the
  sentence D-196 wrote.
- The three rejections (D-193, D-196, today) were all correct and all described
  in terms that would not have caught the next one. Writing the instrument was
  the only way to stop restating the rule and start applying it.

## Recommended next 1–3 priorities

1. **Clear the `inert_surface` STATE.md pin and decide D-044's ordering table.**
   Two separable things: the pin is a `reprobe('STATE.md')` away (seconds), but
   the table's "read by no test" claim is what let an hour-old red go unseen, and
   every cycle writes `STATE.md` in 4c on the strength of it. A guard whose
   premise decayed silently is D-044's own subject.
2. **Triage `horizon_audit.format_scan`** — D-196 pre-recorded the question: it
   builds a markdown table and its module docstring *contains* a table of that
   shape, so the question is whether the shipped table was ever re-derived by
   this generator. D-107 / D-139 have answered this shape twice. Closes 1 of 8.
3. **Triage `assert_reach.asserts_in`** — the last member with no counterexample
   of the D-195/D-196 kind; repo-wide grep returns only pin list and journal prose.
   (`assert_reach.asserts_in` and the Phase-3 instrument pre-check — 10th time
   recommended — both carry to next cycle unchanged.)

## Artifacts
- PR: NOT PUSHED this cycle — suite red (4 pre-existing `inert_surface` failures); `push_preflight` refused. Next cycle's `cycle_artifacts stranded` will name this journal.
- Files touched: eval/mppi_sandbox/key_discrimination.py, eval/mppi_sandbox/tests/test_key_discrimination.py, docs/decisions.md
- TSV row appended: yes (`results/p3-epistemic-shadow-cost-critic.tsv`, status=in_progress, sandbox:pass=2467/2471)
