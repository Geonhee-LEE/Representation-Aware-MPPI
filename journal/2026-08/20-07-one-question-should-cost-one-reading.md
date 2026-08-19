# One question should cost one reading

- **Cycle**: 2026-08-20 07:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `3c1c5d39` [sandbox] `cycle_artifacts stranded` 가 commit strand 도 보게 하기 (run 0회)
- **Phase**: P3
- **Status**: keep

## What I tried

- Added `commit_strand()` to `cycle_artifacts` — `git rev-list origin/<branch>..HEAD`
  read beside the existing journal-file census, plus `commit_strand_report()` as
  its renderer.
- Wired it into the `stranded` subcommand so **either** census raises. Until now
  the module had the parameter-shaped half of this (D-110's `in_flight`) but no
  commit half at all.
- Six tests, zero rollouts. The load-bearing one is a constructed repo in the
  **D-378 shape** — every journal on origin, one later commit that only *modified*
  one of them — which is the exact tree 06:00 was carrying.

## What worked / what failed

- The new reading fires on this cycle's own inherited commit (`8b2c9f9`, D-378's
  carried bookkeeping) and names it with its subject line. That is the case it
  was built for, and it was available one cycle after being measured.
- **The D-378 blindness reproduces in a fixture.** `stranded()` returns `()` and
  `commit_strand()` returns one sha against the same constructed tree. Both
  assertions are in one test on purpose: dropping the first would let a
  `commit_strand` that merely duplicated the journal census pass.
- `None` vs `()` is the whole correctness surface on the git side. An unpushed
  branch has no `origin/<branch>` to diff, and reading that absence as "nothing
  ahead" would hand every fresh branch a clean bill on the one reading built to
  catch unpushed work. `None` is reported in the text and **excluded from the
  verdict** — rc=1 has to stay clearable by a push (D-044), and no push clears
  "git could not answer".
- `census_preempt` 5/5 CLEAN before and after; the change adds no CLI entry
  point, so `loop_reach`'s 89 population claims and the 130-guard tally are
  untouched. This is the blast-radius check `kd-shape-fix` warns about, and it
  is the reason that P2 item was *not* picked at a 17-minute suite price.
- 84 tests in `test_cycle_artifacts.py`, up from 78.

## North-star delta

- **Zero.** This is guard machinery about guard machinery — no MPPI cost term,
  no representation channel, no scenario metric. The span from D-370 through
  D-379 has moved none of those, and this cycle does not pretend otherwise.
- The one defensible thing it buys is cheaper: the question "is this cycle's
  output on origin" now costs **one** reading instead of three (`stranded`,
  `push_preflight probe`, and a hand-run `git rev-list`), which is time back for
  cycles that could spend it on the north star.

## Key learnings

- **A census is scoped to its keys, and its honesty says nothing about its
  reach.** `stranded` was never wrong; it answered a question about *files*
  while the caller was asking one about *work*. rc=0 from a correct instrument
  is the most expensive kind of clean reading, because nothing prompts a second
  look.
- The in-flight exemption needed **no** commit-side counterpart, and noticing
  that saved the harder half of the design. `stranded`'s stated precondition —
  it runs at REVIEW, before 4a — already implies every commit on disk belongs to
  a finished cycle. The exemption exists because journals are written mid-cycle;
  commits ahead of origin at REVIEW time have no such window.
- D-378's carried commit turned this cycle into its own test case. The finding
  it raises is *correct* and its repair is exactly what D-378 mandated anyway
  (ride this cycle's receipt), so the new gate and the standing decision agree
  rather than fight.

## Recommended next 1–3 priorities

1. **Answer the branch-scope question** (user-blocked). Ten consecutive cycles,
   zero north-star movement. This is the top item on the branch and no executor
   cycle can move it.
2. **`kd-shape-fix`** (P2) — still unpaid. Measure the 130-guard blast radius
   with `census_preempt` *before* editing, per its own TODO body.
3. Fold `push_preflight probe`'s `OTHER_TREE` into the same reading, so the
   receipt-vs-HEAD question joins the strand question rather than sitting beside it.

## Artifacts
- PR: #67 (already open — D-140: continuing on an open PR adds nothing to the queue)
- Files touched: `eval/mppi_sandbox/cycle_artifacts.py`, `eval/mppi_sandbox/tests/test_cycle_artifacts.py`, `docs/decisions.md`, `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV row appended: yes
