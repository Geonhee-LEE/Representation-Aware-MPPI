# The re-take priced itself out — and the probe threw the price away

- **Cycle**: 2026-08-13 14:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — re-take `STATE.md`'s pin with its full probe
- **Phase**: P3
- **Status**: keep

## What I tried

- Took STATE #1 as the dedicated single-thrust cycle it asked for: `STATE.md`
  sits at `generation == COMPOSITION_CAP - 1` with 4 entrants, so `reprobe`
  falls back to the full `probe()` — **27 readers, not the 26 STATE priced**
  (`test_licence_recall.py` entered from the 13:00 cycle).
- Started that probe at 8 min elapsed and held every write for it, because
  `probe` re-derives its reader set afterwards and grades `VACUOUS` if the set
  moved mid-measurement — "no other work" is a mechanical constraint here, not
  a scheduling preference.
- It ran 15 minutes and died: `subprocess.TimeoutExpired` on the **first**
  pass, against `_run`'s hard 900 s ceiling.
- Ported the finding into the module rather than the journal alone: a new
  `UNAFFORDABLE` verdict, `_run` returning `None` instead of raising, and a
  CLI exit code of 2.

## What worked / what failed

- **The re-take is not expensive, it is impossible as written.** A probe needs
  two passes and the *un-mutated* one alone exceeds 900 s. No cycle length
  fixes that — a 60-minute budget would still hit the per-pass ceiling. STATE
  had this priced as "a dedicated cycle"; the measurement says the price is
  not payable at all through this code path.
- **The 15 minutes bought a fact and the CLI discarded it.** The run ended in a
  stack trace, so nothing recorded that the re-take had even been attempted —
  the next cycle would have read the same withdrawn pin, priced it the same
  wrong way, and paid the same 15 minutes. That is the actual defect, and it is
  the one thing here that generalises.
- The crash landed *before* the mutation write, so `STATE.md` was never
  modified and the tree is clean — luck, not design, and the second-pass case
  is now covered by a test that asserts the `finally` restore.
- 12 new tests, both directions on every rule (timeout graded / real run still
  parsed, first-pass and second-pass timeouts, compose propagating and not
  shadowing the ordinary branch).

## North-star delta

- **No capability moved.** This is instrument work, and the branch has now
  spent ~20 cycles there.
- What it removes is a recurring 15-minute tax: the next cycle to read this pin
  gets `UNAFFORDABLE` and an exit code instead of re-earning a traceback.

## Key learnings

- **A pin can age past the point where its own re-take mechanism reaches it.**
  `COMPOSITION_CAP` bounds un-re-measured generations on the assumption that
  the full probe is always available as the fallback. At 27 readers it is not.
  The cap and the probe's per-pass ceiling are two limits that were never
  checked against each other, and `STATE.md` is where they crossed.
- **"Expensive" and "unaffordable" are different readings and the module had
  only one word for both.** `VACUOUS` would have absorbed this, which is why
  the verdict is distinct — the next cycle's move differs: re-scope the probe,
  don't withdraw the pin.
- Writing this file's docstring against `POST_RECEIPT_WRITES` rather than
  respelling the pinned paths is D-237 applied on purpose — spelling them here
  would have withdrawn the very pins the cycle is about.

## Recommended next 1–3 priorities

1. **Re-scope the probe so the largest pin is reachable** — shard the reader
   set and compose across shards, or probe per-reader with early exit. The
   disjunction `compose` already relies on makes sharding sound.
2. **Propose a capability successor to D-225** — unchanged from STATE, and now
   overdue by another cycle.
3. Audit the branch for claims resting on a point estimate inside an
   unresolved row (D-235's retracted class). Reading only, cheap.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: `eval/mppi_sandbox/inert_surface.py`, `eval/mppi_sandbox/tests/test_probe_affordability.py`, `docs/decisions.md`, `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV row appended: yes
