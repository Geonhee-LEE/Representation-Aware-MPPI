# Narrowing is not discrimination — the narrow key cut the population 3.5× and moved the composition 1.4 points

- **Cycle**: 2026-08-11 13:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — measure the narrow key (call + recorded return value) over the 599-function population
- **Phase**: P3
- **Status**: keep

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

1. **Triage `horizon_audit.format_scan`** — D-196 pre-recorded the question: it
   builds a markdown table and its module docstring *contains* a table of that
   shape, so the question is whether the shipped table was ever re-derived by
   this generator. D-107 / D-139 have answered this shape twice. Closes 1 of 8.
2. **Triage `assert_reach.asserts_in`** — the last member with no counterexample
   of the D-195/D-196 kind; repo-wide grep returns only pin list and journal prose.
3. **Add the instrument pre-check to the constitution's Phase-3 step** — ~120
   passed in 29–57s against a 19-minute full suite. Doc-only. **10th time recommended.**

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/key_discrimination.py, eval/mppi_sandbox/tests/test_key_discrimination.py, docs/decisions.md
- TSV row appended: pending
