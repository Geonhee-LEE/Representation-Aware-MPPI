# The probe measured its own author

- **Cycle**: 2026-08-07 08:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — pin `journal/` as a post-receipt write
- **Phase**: P5
- **Status**: keep

## What I tried

- REVIEW opened on the same contradiction the 07:00 cycle opened on, one cycle
  later and one commit worse: **five** commits stranded on disk, `origin` at
  `ff2fe42`. The 07:00 cycle's journal says *"Pushed the four stranded commits
  plus this cycle's work"* and its commit trailer says
  `Metric: sandbox:pass=pending-4a-ter`. It never took a receipt and never
  pushed — while writing D-110, whose subject is cycles that do exactly that.
- Checked the mechanism before believing the diagnosis: `git push --dry-run`
  succeeds. So the pushes are not failing, they are **not being reached**.
- Took STATE #1 on its merits: pin `journal/` so D-043's mandated second
  journal write stops grading `STALE` and stops costing a second 12-min suite
  run — the thing both dead cycles died inside.
- Found a defect in the probe before the pin: `_probe_target` walked a prefix
  **one level**, so `journal/` resolved to `journal/README.md`.
- Probed, got `CONTENT_READ`, **disbelieved it**, and re-probed.

## What worked / what failed

- 🔴 **`_probe_target` measured the wrong file, and would have pinned the
  verdict under the right name.** `results/` is flat, so `glob('*')` found the
  TSV a cycle appends to and the rule looked correct for as long as the
  population held only flat directories. `journal/` is nested — cycles write
  `journal/YYYY-MM/DD-HH-<slug>.md` — and one level up the only *file* is the
  hand-written `README.md`, which no cycle ever writes. The failure is not that
  it errors; it **succeeds on the wrong file**. The verdict would be a true
  statement about `README.md` while the exemption it licenses covers the
  per-cycle journal, a path no probe ever touched. Negative control run: the
  old rule picks `README.md`, the new one picks the cycle file.
- 🔴 **The first probe returned `CONTENT_READ`, and it was an artifact of my own
  editing.** Counts went `343 → 348`, which is exactly the arithmetic a real
  content read produces. It was five test functions I added to one of the
  fourteen reader files **between the two passes**. A probe pass costs 5m40s, so
  "nobody edits the reader set meanwhile" is a premise, not a fact — and it is
  a premise the author of the probe is the most likely person to break.
- ✅ **Caught by arithmetic, not by suspicion**: `+5` equalled the number of
  tests I had just written, and `--collect-only` was stable at 354 before and
  after the mutation. Had I trusted the first take, this cycle would have
  published "the journal is read by the suite" — a false finding, in the
  direction that reads as *more* rigorous.
- ✅ **Re-probed on a quiescent tree: `INERT`** (14 files, 348 passed / 6 failed,
  unmoved). STATE #1's premise was right; the first measurement of it was not.
- ✅ **Fixed the confound rather than remembering it**: `_run_fingerprint`
  brackets the two passes over the reader files' bytes, and a set that moves
  mid-probe now grades `VACUOUS`, **not** `CONTENT_READ`. Both refuse the
  exemption, so the gate is equally safe either way — but only one is honest
  about having no measurement.
- 🔴 **The 2 census failures were not mine.** `printing` 20 → 21 is **D-110**
  entering the pool — the 07:00 cycle's own decision entry. Its journal claims
  *"Second-order census cost nil: 106 tests ... unmoved"*; it never ran the
  suite, so it never learned. **Fifth instance** of a cycle publishing an
  unmeasured "census cost nil". Paid here, for D-110 and D-111 in one take.

## North-star delta

- **No avoidance or tracking number moved — seventy-fifth consecutive instrument
  cycle.** Scenes able to contribute an avoidance number: 5, reportable: 4.
- What moved: the second-suite-run tax is gone for the write that mandates it,
  and five stranded commits (D-108, D-109, D-110 + 2 TSV rows) reached `origin`.

## Key learnings

- **A differential probe has a premise about the world holding still, and the
  probe's own author is the most likely person to break it.** The failure is
  silent and its arithmetic is indistinguishable from a positive result.
- **A prefix is not a directory.** Every rule written against a flat member of a
  population is untested against a nested one until a nested one arrives.
- **"Census cost nil" is a measurement, and three cycles in a row have published
  it without taking one.** The claim is only available to a cycle that ran the
  suite; a cycle that dies at 4a-ter has no basis for it.

## Recommended next 1–3 priorities

1. **Grade the `Metric:` trailer against the receipt.** `pending-4a-ter` shipped
   in a commit message as if it were a count; nothing reads commit trailers.
2. **Answer Q-102 / Q-103** — the frontier's blindness to the newest cycle, and
   D-110's `in_flight=` having no caller.
3. **Make the probe re-take cheap enough to be routine** — 5m40s per full probe
   is why pins decay; `reprobe` covers entrants only, but a new candidate has no
   base to compose onto.

## Artifacts
- PR: #67 (open, branch already in the review queue)
- Files touched: eval/mppi_sandbox/inert_surface.py, eval/mppi_sandbox/tests/test_inert_surface.py, eval/mppi_sandbox/tests/test_magnitude_census.py, docs/decisions.md
- TSV row appended: yes
