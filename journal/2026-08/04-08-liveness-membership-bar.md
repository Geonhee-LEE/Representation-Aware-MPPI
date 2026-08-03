# The liveness bar tested the fixture, not the act — and the derivation's whole yield was that false positive

- **Cycle**: 2026-08-04 08:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — register `unregistered_local_only` as a third `guard_direction.Probe` (D-054 → Q-068 (c))
- **Phase**: P3
- **Status**: keep

## What I tried

- Took STATE #1, the decided outcome of Q-068: promote the one guard D-054
  measured *derivable and alive but unprobed* into `guard_direction.PROBES`.
- Before writing the entry, read the candidate's liveness the way a probe would
  have to — **both sides** of its derived act, in the enriched fixture. That
  read is not something D-054 performed; `validate` only looked after.
- The reading did not move. Repaired the bar in both modules that carry it
  (`liveness_derivation.validate`, `guard_direction.check_liveness`), re-scored,
  and pinned the corrected numbers plus a regression test for the loud-fixture
  case.

## What worked / what failed

- 🔴 **The candidate is not alive.** In the enriched fixture,
  `unregistered_local_only` reads `{docs/decisions.md, docs/deliberations.md}`
  **before any act runs** — `build_enriched_repo` copies the real `docs/` in.
  Its derived act (write `eval/control.txt` in the worktree) leaves the reading
  at the same 2 elements, unmoved, never naming its subject. It scored `LIVE`
  on somebody else's population.
- 🔴 **The bar was the defect, and it is shared.** `validate`'s test was
  `reading is non-empty`, inherited verbatim from
  `guard_direction.check_liveness`. That cannot separate *the act woke the
  guard* from *the fixture was already loud*. Membership is the test —
  the same correction `Direction.verdict` already carries one layer up, which
  this layer never received.
- 🔴 **Net yield of the derivation over the typed table: 0, not +1.** The
  number has now been read three ways, each smaller: `reach_gap` **6**
  (readable) → D-054 **1** (non-empty after) → **0** (the act produced the
  reading). The guards that survive are exactly the two written by hand.
- ✅ **The two typed probes pass the stricter bar unchanged.** No `ProbeError`,
  all 10 direction readings and the masking table identical. The old bar was
  equivalent *on those two* — their fixture reads empty before their act —
  which is precisely why twenty-odd cycles never noticed.
- ✅ `INERT` is scored apart from `DEAD`, and the distinction is load-bearing:
  `pre_epoch_commits` reads empty (nothing there), `unregistered_local_only`
  reads 2 (the fixture's, not its own).

## North-star delta

- **No avoidance or tracking number moved — twenty-third consecutive instrument
  cycle.** Scenes able to contribute an avoidance number: 5, reportable: 4 —
  unchanged.
- What moved is a *retraction*: D-054's headline "+1" is withdrawn to 0, by
  measurement rather than by re-reading. The repair STATE #1 asked for is not
  shippable, and the reason is now a red test rather than a paragraph.

## Key learnings

- **When a verdict's bar is one-sided, check what it is a bar on.** "Non-empty
  after" is a statement about the fixture unless the fixture is known silent.
  Both modules asserted it; only one had earned it.
- **A bar can be correct on its whole population and still be wrong.** n = 2,
  both silent-before, so the weak and strong bars agreed everywhere they were
  ever evaluated. The third guard was the first datum that could distinguish
  them — which is an argument for measuring a proposal on a *new* member, not
  for trusting agreement on the old ones.
- **Fixtures that copy real surfaces carry real content into the reading.**
  `build_enriched_repo` copies `docs/` and `scripts/` from the live repo, so
  every guard reading those surfaces starts loud and its fixture reading is a
  function of whatever the repo happens to contain today (Q-070).

## Recommended next 1–3 priorities

1. **Re-audit every other `LIVE`/pass verdict in the package for a one-sided
   bar** — the same "non-empty after" shape may sit in `probe_reach`'s
   `VERDICT_READABLE` and in the epistemic-reach screens.
2. **Q-070: make the enriched fixture synthetic rather than copied**, or state
   why a fixture whose contents track the live repo is acceptable.
3. **Q-069 stands unchanged** — split the `NO_REGISTRY` 9 by blocking layer.
   Its motivation is stronger now: the derived numerator is 2, all of it
   already typed.

## Artifacts
- PR: pending merge (`autoresearch/p3-epistemic-shadow-cost-critic`, #67)
- Files touched: `eval/mppi_sandbox/liveness_derivation.py`,
  `eval/mppi_sandbox/guard_direction.py`,
  `eval/mppi_sandbox/tests/test_liveness_derivation.py`,
  `eval/mppi_sandbox/tests/test_guard_direction.py`, `docs/decisions.md`,
  `docs/deliberations.md`
- TSV row appended: yes
