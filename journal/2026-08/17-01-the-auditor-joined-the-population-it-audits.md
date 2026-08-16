# The auditor joined the population it audits — and only one of its two lists was a defect

- **Cycle**: 2026-08-17 01:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `3bec5d39-81e6` [sandbox] grep-the-axis-for-min-max-interval-assumptions
- **Phase**: P3
- **Status**: in_progress (repair real, **not pushed** — see below)

## What I tried

- Phase 1's `cycle_artifacts stranded` fired rc=1 and named the 00:00 journal.
  That outranks the decision tree, so this cycle picked nothing new — it cleared
  the strand instead.
- The strand was **not** a forgotten push. The 00:00 cycle committed D-312
  (`extremum_reading.py` + tests), the suite came back `3425 passed, 7 failed`,
  and `push_preflight` refused on the red receipt. Two commits sat local.
- All 7 failures are one self-caused root cause: `guard_reflexivity.guards()`
  classifies the new module's three functions as guards, so registry tallies
  pinned across five test files are short by it.
- Repaired all five, and wrote the two negative controls the
  `unwatched <= controlled` pin forces (`_hull_repaired_by`, `_site_classes`).

## What worked / what failed

- **The two new allow-lists are not the same kind of thing, and that is the
  finding.** `HULL_REPAIRED_BY` is a genuine one-directional exemption —
  `unrepaired_hulls` drops keys in it and nothing puts them back. `SITE_CLASSES`
  is on the unwatched list because `exemption_watchers` matches populations **by
  name**, and `sweep` binds its AST re-derivation to a local called `found`.
  `sweep` reconciles the list in *both* directions (`unregistered` goes red,
  `retired` is reported), so it is not an exemption at all — the reconciliation
  *is* the watcher, and the scan cannot see it.
- Both controls bite: `HULL_REPAIRED_BY` 0 → 2, `SITE_CLASSES` 0 → 1. The second
  also *demonstrates* the both-directions claim — deleting a registered key does
  not make the sweep quiet, it makes `unregistered` name the deleted key.
- **Two of D-312's three guards route to masking (20 → 22).** Every prior cycle
  was one-of-three or one-of-four. An auditor has to name what it lets through,
  so its exemptions are typed by construction.
- `liveness_derivation` census split across two layers (`NO_REGISTRY` 21 → 22,
  `NOT_PATHS` 4 → 5) with the numerator **unchanged at 4 for the ninth
  consecutive cycle**.
- Two process errors, both mine, both cost wall-clock: a `pkill -f` pattern wide
  enough to kill three unrelated pytest runs, and an `until [ -s file ]` wait
  that fired on the first progress dot instead of the summary line.


## ⚠️ Not pushed — the ripple has a second order, and the budget ended first

- Receipt: `3430 passed, 3 failed, 163 skipped, 1 xfailed in 1021.38s across 14
  shards`, rc=1. `push_preflight` refused on the red receipt (fail-closed,
  correct). Three commits now sit local: `ca61466`, `4a5d3d7`, `1150429`.
- **The repair is real and measurable**: `3425 passed / 7 failed` →
  `3430 passed / 3 failed`. Every one of the original seven is fixed. The three
  that remain are *different tests*, and they are the same root cause arriving
  one frame further out — my repair itself moved registries, and a second layer
  of pins reads those registries:
  - `test_the_census_names_what_it_does_not_cover` — `REGISTRIES` grew by the
    two entries I added.
  - `test_and_shaped_guards_are_exactly_these_four` — the running
    and-shaped-guard tally, which is *explicitly* maintained as a running count
    because "every instrument built to audit a population becomes a member of
    one" is the finding it records.
  - `test_not_paths_layer_names_a_real_registry` — `NOT_PATHS` 4 → 5 needs the
    new member's registry named, not just counted.
- **This was foreseeable and I did not foresee it.** The first-order tally fix
  is precedented fourteen times; that a *fix* to a registry census is itself a
  census-moving event is the same lemma applied once more, and nothing in the
  repair loop asks for it. The standing pre-suite check proposed above should
  therefore be run **twice** — once against the new module, once against the
  repair — or it only ever catches the first ripple.
- Budget: the suite ran 1021s against the 762s the budget was planned on,
  because my own parallel probe runs were still contending for CPU when it
  started. That is a self-inflicted 4 min and it is the difference between
  pushing and not.

## North-star delta

- **No movement toward the north star.** This is strand-clearing on the
  verification surface — no controller, cost, or representation code changed.
  And it did **not** reach `origin` — D-312's science is now local for a second
  cycle, on three commits instead of two. The gain is narrower than intended:
  the red count went 7 → 3 and the remaining three are named and cheap, so the
  next cycle starts from a diagnosis rather than a receipt.
- The honest read on D-312's own value is unchanged from 00:00: it retired a
  four-cycle bottleneck by showing the "defect class" was two things and one of
  them was not a defect.

## Key learnings

- **The red suite was not a failure of D-312 — it was D-312 working.** The
  package's most-reproduced finding is that an instrument built to audit a
  population joins one. A cycle that adds an auditor should now *budget* for the
  tally repair rather than discover it in the receipt.
- The cheap pre-empt exists and the 00:00 cycle ran and then cut it. One line —
  `[g.qualname for g in guards() if 'extremum' in g.qualname]` — costs ~0.3 s and
  would have named all three guards before the suite. That is worth a standing
  step, not a lesson repeated.
- `unwatched <= controlled` earned its keep for the second time: it forced two
  controls to be *written* rather than a count to be bumped, and writing the
  `SITE_CLASSES` one is what surfaced the by-name matching limit (Q-090).
- Nine consecutive cycles of new guards with **zero** derivable ones is no longer
  plausibly bad luck about individual guards. Q-069 should be re-read as a
  question about the convention, not about which layer blocks each case.

## Recommended next 1–3 priorities

1. Add the ~0.3 s `guards()` self-membership check as a standing pre-suite step
   for any cycle that adds a module — the pre-empt that was cut twice now.
2. Answer Q-090 together with Q-161 (both ask "add an axis/verdict to the
   scan?"); first count how many of the 8 unwatched lists are reconciled in both
   directions. Pure reading, no sim.
3. Return to the `K`-axis question the branch is actually about, now that D-312
   has retired the defect-class bottleneck.

## Artifacts
- PR: #67 (open) — **branch not pushed this cycle**; `1150429` sits local alongside `ca61466`, `4a5d3d7`
- Files touched: eval/mppi_sandbox/exemption_control.py, eval/mppi_sandbox/loop_reach.py, eval/mppi_sandbox/tests/test_guard_reflexivity.py, eval/mppi_sandbox/tests/test_exemption_control.py, eval/mppi_sandbox/tests/test_exemption_masking.py, eval/mppi_sandbox/tests/test_liveness_derivation.py, docs/decisions.md, docs/deliberations.md
- TSV row appended: yes (`sandbox:pass=3430/3433`, status=in_progress)
