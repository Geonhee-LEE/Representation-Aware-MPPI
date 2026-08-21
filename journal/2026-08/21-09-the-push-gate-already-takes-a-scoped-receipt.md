# The push gate already takes a scoped receipt

- **Cycle**: 2026-08-21 09:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `state-1` Price the receipt suite against the budget (STATE #1, 3rd cycle)
- **Phase**: P5
- **Status**: keep

## What I tried

- Took STATE #1 — "can `push_preflight` accept a receipt scoped to the shards
  touching the changed modules?" — and, before designing anything, checked what
  the gate actually reads.
- Read `check()` and found `suite_coverage` already in the decision chain
  (`sc.uncovered_is_red`), i.e. partial receipts are a modelled concept.
- Recorded a deliberately absurd receipt on the current tree: one file,
  `eval/tests/test_run_metrics.py`, 9 tests, ~2s — then ran `check()` on it.
- Wrote it up as D-400 and carried the "what to do about it" to Q-177. Did
  **not** implement the guard.

## What worked / what failed

- ✅ **The 9-test receipt returns `GREEN`**: `9 executed, none left out, none
  failed, tree unchanged since (head=63daee2a)` — the same verdict the
  3954-test receipt earned on the same tree.
- ✅ **Mechanism located, not guessed**: `check()` never reads
  `receipt.command`'s target list. Emptiness is `executed == 0`; partiality is
  `suite_coverage.of(counts)`, which sees only `skipped`/`deselected` — counts
  of what was left out *within* the invocation. A file never named appears in
  no count at all.
- ⭐ **The finding is a reversal, not just a hole**: the 9-test receipt reads
  `9 executed, none left out`; the full receipt reads `96.0%; 164 uncovered`.
  **Narrowing the scope makes the receipt read cleaner.**
- ✅ **Three cycles of STATE #1 had a false premise.** The question assumed the
  gate demands a full suite. It does not — the only thing forcing 22 minutes is
  the target list typed into Phase 3 / 4a-ter of the constitution.
- ⚠️ **Did not close the hole.** Closing it needs a census over
  `receipt.command`, and a census `+1` is the exact shape that made eight
  consecutive first-suites RED (D-399). Buying it with no budget left would
  have cost the measurement too.

## North-star delta

- **Zero — 32 cycles running.** 0 rollouts, no controller/representation/
  dynamics code touched. This is verification-surface work.
- One thing is genuinely different from the previous 31: this is the first
  **false negative in the verification surface itself** — every prior finding
  was about prose citing a number wrongly, not about the gate that licenses the
  push mis-grading its own evidence.

## Key learnings

- **`VACUOUS` catches `executed == 0`; there is no word for `executed ==
  9-of-4119`.** D-081/D-075/D-076 built the vacuity vocabulary for exactly the
  "empty reads clean" failure and it stops one step short of "narrow reads
  clean" — the third recurrence of D-394/D-079.
- **Check what the gate reads before designing what it should accept.** STATE
  #1 was three cycles of design pressure on a constraint that was never there;
  one `record` + one `check` (≈4 s) falsified it.
- **A constitution line can be the only load-bearing enforcement.** The target
  list in Phase 3 looked like convenience. It is the entire full-suite
  guarantee — which is also why nobody has tripped this in 400 decisions.

## Recommended next 1–3 priorities

1. **Answer Q-177's one blocking sub-question**: is `suite_coverage`'s
   denominator (4119) stored in the receipt or re-collected per call? If
   re-collected, lean (c) breaks `check()`'s network-free/no-collect invariant
   and needs redesign. One grep decides it.
2. **Implement Q-177 lean (c)** — make the GREEN string state `n of 4119
   executed (x% of the declared suite)`, so a scoped push is possible but not
   silent. Re-derive the census from source *before* typing any pin (D-399).
3. **Anything with a rollout in it.** 32 cycles without one.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: docs/decisions.md, docs/deliberations.md, journal/2026-08/21-09-the-push-gate-already-takes-a-scoped-receipt.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: yes
