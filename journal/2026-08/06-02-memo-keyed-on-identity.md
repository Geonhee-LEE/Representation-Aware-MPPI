# The memo ships — and the key it was told to use was not identity

- **Cycle**: 2026-08-06 02:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — ship the memo (14 of 18 nested runs, ~326 min)
- **Phase**: P3
- **Status**: keep

## What I tried

- Built `eval/mppi_sandbox/suite_memo.py`: a process-scoped memo that runs a
  nested suite command once per `(argv, cwd, recorder **text**, population,
  tree digest)`, and wired `predicate_vacuity._run_recorder` and
  `predicate_inputs._run_recorder` — the two frames under all 18 measured
  spawns — through it.
- Before using D-092's `collapse_key` as the memo key, checked what it keys on.
  It reads the **argv**. Extended the ledger's recorder to capture, at spawn
  time, the digest of the plugin *file* each `-p NAME` resolves to on
  `PYTHONPATH` and of the `PREDICATE_VACUITY_SITES` payload, and folded both
  into `collapse_key`.
- Split the recorders' `{}` return into `None` (the run never dumped) and `{}`
  (it ran and observed nothing) so the memo can refuse the first and cache the
  second.
- Verified end-to-end on a real selection, and re-measured the ledger.

## What worked / what failed

- 🔴 **`collapse_key` was argv-identity, and its docstring claimed command
  identity.** `predicate_vacuity` installs `_PLUGIN` and `_PLUGIN_ATTRIBUTED`
  under the **one** name `predicate_vacuity_plugin`, by writing whichever is
  wanted into a temp dir on `PYTHONPATH`. The argv names the recorder; it does
  not carry it. The population travels in an env var no argv mentions. Today
  the plain and attributed censuses differ in their `--ignore` sets, so the
  argv key separated them **by accident** — call `measure_attributed` with the
  exclusions and a memo keyed on D-092's key serves a value census an
  attributed reading. `key_conflation`'s own defect class, in the key written
  to avoid it.
- ✅ **The number survived the sharpening**: identity-keyed, the ledger still
  reads **18 runs / 4 classes / 14 removed**. What changed is not the count but
  what it is a count *of* — and that was not knowable before it was measured
  both ways.
- ✅ **The memo works in the real path**: same command twice → `6.63 s` then
  **`0.0085 s`**, one spawn. Same argv with the *attributed* recorder → a
  second spawn, correctly.
- 🔴 **The recorders returned `{}` for two different events** — "timed out /
  wrote no dump" and "ran fine, observed nothing". Momentary before; a cache
  keyed on it makes it **permanent**, serving one timeout for the rest of the
  session as the finding *this predicate is never called*. Fifth naming of
  absence-as-result in this package (`UNPOPULATED`, `UNRUN`, `UNCOLLECTED`,
  `UNIDENTIFIED`) and the first found by asking what a cache would freeze.
- 🔴 **The saving is not in the local pass count.** The 18 spawns live in
  `slow`-marked tests; the local fast half skips them, so today's green suite
  is evidence the memo *breaks nothing*, not evidence it saves anything. The
  saving rests on the ledger plus the end-to-end probe above.
- ✅ **An unknown identity now refuses to be a duplicate**: `Ledger.duplicates`
  returns `-1` and `verdict()` reads `UNIDENTIFIED` when a spawn's recorder
  text was not captured. Under-counting *classes* is the direction that reads
  clean, so it may not be guessed.
- 🔁 **Census cost, 28th consecutive cycle — and the first paid by
  registration rather than by widening a pin.** The new module arrived with 7
  red tests: two allow-lists (`TREE_SUFFIXES`, `TREE_SKIP`) unwatched, a new
  AND-shaped guard, `DERIVED` 4 → 5, and two `UNRUNNABLE` pairs. Both lists are
  now tampered through `suite_memo.digest_scope` (registries 9 → **11**,
  tampers 8 → **10**, all ten `BITES`), and `tree_digest` reads its scope at
  call time so `exemption_masking` can screen it instead of skipping it. Four
  of the seven pins then went green **without being touched** — the guard
  entered `DERIVED`, the bucket that is derivable from a module-level registry,
  which is where the last five entrants did *not* land.

## North-star delta

- No avoidance or tracking number moved — **sixty-first** consecutive
  instrument cycle. Scenes able to contribute an avoidance number: 5,
  reportable: 4.
- The larger half of the `slow` repair is now **shipped**, not just measured:
  ~326 min of the 419 min over-run is removed by identity alone.
- Still `INSUFFICIENT`. 6 × 1396 s = **8376 s vs 7200 s**; the ceiling raise
  remains mandatory and is now the only thing between this branch and a CI
  reading.

## Key learnings

- **A key is a claim, and this one was checked against its own subject.** The
  instruction said "key on `collapse_key`". Reading what `collapse_key` reads
  cost ten minutes and changed the key; taking the instruction at face value
  would have shipped a cache that is correct only because of an accident in an
  `--ignore` list.
- **Caching converts transient conflations into permanent ones.** The `{}`
  ambiguity had been harmless for as long as every call paid for its own run.
  Any memo added on top of an ambiguous return value freezes the ambiguity —
  worth asking of the next one before, not after.
- **A saving measured on a subject the local suite skips must say so.** Green
  here means "nothing broke". It does not mean "326 min saved", and the two
  are one sentence apart in a report.

## Recommended next 1–3 priorities

1. **Raise the `slow` ceiling above 8376 s with headroom** — the remaining half
   of D-089 option (a), and now the *only* remaining half.
2. **Teach `suite_runners()` the call-site timeout** so the signature scan stops
   excluding `guard_vacuity.measure`.
3. **Make `push_preflight record` unlink its `--out` before running** — a fixed
   path makes a stale receipt indistinguishable from a fresh one.

## Artifacts

- PR: pending merge (`autoresearch/p3-epistemic-shadow-cost-critic`, #67)
- Files touched: `eval/mppi_sandbox/suite_memo.py` (new),
  `eval/mppi_sandbox/tests/test_suite_memo.py` (new),
  `eval/mppi_sandbox/nested_run_ledger.py`,
  `eval/mppi_sandbox/predicate_vacuity.py`,
  `eval/mppi_sandbox/predicate_inputs.py`,
  `eval/mppi_sandbox/tests/test_nested_run_ledger.py`, `docs/decisions.md`
- TSV row appended: yes
