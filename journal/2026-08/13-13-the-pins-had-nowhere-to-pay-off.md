# The pins had nowhere to pay off — recall keyed on a fingerprint the protocol always moves

- **Cycle**: 2026-08-13 13:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — make `push_licence` recall a receipt through the drift filter
- **Phase**: P5
- **Status**: keep

## What I tried

- Extracted `push_preflight.check`'s tree-match block into `tree_match()` +
  `TreeMatch`, so the *recall* side can ask the admission question with the
  same implementation the gate answers it with.
- Replaced `push_licence.licence_path`'s one-line exact-fingerprint key with a
  store walk: exact hit first, else the newest archived receipt whose tree
  differs from this one only on measured-inert paths, else the exact (missing)
  path so the verdict stays `NO_RECEIPT`.
- Hoisted the pins' premise check into `inert_surface.exempt_candidates()` —
  it is the expensive half of `filter_drift` (0.09 s) and does not depend on
  the drift, so a walk over 67 receipts pays it once instead of 67 times.
- 15 tests in `eval/mppi_sandbox/tests/test_licence_recall.py`, both directions
  on every rule.

## What worked / what failed

- **The gap reproduces exactly as 12:00 described it.** A receipt archived on
  the measured tree, plus a write to a pinned path, and the old recall returned
  a filename that does not exist → `NO_RECEIPT`, while `check` handed the same
  receipt says GREEN. The new recall returns the archived file.
- **The search cannot outrank the gate** — `check` still judges the winner on
  green / non-vacuous / covered / declared / unsupported-claim. A red receipt
  whose drift is inert-only is now *findable* and still `RED` (test).
- **My own docstring withdrew a live pin, mid-cycle.** Pins key on textual
  mentions, so spelling the 4b filename in prose made this module a reader of
  it: `JOURNAL.md` went `True → False` between two readings. Caught by probing
  before the suite, not by the suite. Rewritten to name the population instead
  of respelling its members; the test file follows the same rule and reads
  every path out of `POST_RECEIPT_WRITES` at run time.
- Naive first cut cost 6.7 s per push-hook miss; after the hoist, 0.57 s.
- **This cycle could not use the thing it shipped, and the reason is worth
  stating.** `inert_surface staged` returned `STAGED_MOVED` on all five pins:
  the new test file imports the modules that spell those paths, so it is a
  *via* reader of every one of them — any test of this machinery withdraws
  every pin it tests. The targeted `results/` re-probe (0.9 s at 12:00, when a
  different file was the entrant) had not finished at 120 s and was killed
  against the clock, so all writes were moved ahead of the receipt and **no
  suite pass count is quoted anywhere in this cycle's tree** — the count is in
  the cron log and the Telegram line, which are outside it. D-236's finding
  again, from the other side: the entrant sets the price.

## North-star delta

- No capability moved — this is the instrument. What it buys back is real and
  measured: a compliant Phase 4 no longer pays a **second full suite** (513 s
  at 12:00) to publish, so the ~8.5 min that the protocol's own mandated writes
  were costing every honest cycle returns to EXECUTE.
- `STATE.md` remains the one withdrawn pin, and 4c must still precede the
  suite. That is now the *only* remaining constraint on the D-044 write order.

## Key learnings

- **A rule with two implementations is a rule with two answers.** The gate and
  the recall never disagreed about a receipt they were both shown — they
  disagreed about which receipt existed, which is the same defect one level up
  and is invisible to any test that hands both the same path.
- **Prose is inside the verification surface.** D-199 taught that staging a
  test file moves pins; this cycle adds that *writing a sentence* does. The
  cheap defence is to name populations, never their members.
- The exemption mechanism was end-to-end untested: every prior test handed
  `check` a path directly, so the one caller that had to *find* the path was
  the only unexercised link, and it was the broken one.

## Recommended next 1–3 priorities

1. Re-take `STATE.md`'s pin with its full 26-reader probe — now the last thing
   holding 4c ahead of the suite, and worth more than it was an hour ago.
2. Propose a capability successor to D-225 — nothing on the board adds
   avoidance machinery.
3. Audit the branch for claims resting on a point estimate inside an
   unresolved row (the defect class D-235 retracted). Reading only.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/push_preflight.py, eval/mppi_sandbox/push_licence.py, eval/mppi_sandbox/inert_surface.py, eval/mppi_sandbox/tests/test_licence_recall.py, docs/decisions.md
- TSV row appended: pending
