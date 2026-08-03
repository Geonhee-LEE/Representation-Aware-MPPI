# A liveness act has four parts; `acts_of` supplies the one that was never hard

- **Cycle**: 2026-08-04 07:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — derive `Probe.liveness` from `guard_reflexivity.acts_of` (Q-068)
- **Phase**: P4 (instrument lane; north-star work still gate-1 blocked)
- **Status**: keep

## What I tried

- D-053 left the dynamic probe's reach bounded by a hand-written table of **2**
  `guard_direction.Probe` entries. Q-068 proposed deriving `Probe.liveness` from
  `guard_reflexivity.acts_of`, which already enumerates each guard's git/fs
  operations with scope. D-052 and D-053 both ended with the same instruction —
  **measure the derivable fraction before shipping the repair** — so this cycle
  measures it.
- `eval/mppi_sandbox/liveness_derivation.py`. Reading the two hand-written acts
  back shows each is a **triple**: `(scope, membership, subject)`.
  `_live_staged_declarations` = `INDEX`/`IN`/a member of `DECLARED_LOCAL_ONLY`;
  `_live_undeclared_drift` = `WORKTREE`/`OUT`/a tracked path outside it.
- `acts_of` supplies **one** of the three. `Act` carries
  `tool`/`verb`/`scope`/`site`/`spelling`, and for a filesystem act the spelling
  is the accessor name (`read_text`), not the path. Subject and membership come
  from a second derivation, over `Guard.typed_exemptions`: a `TYPED` exemption
  names the registry the subject must be inside (`AND`/`IN`) or outside
  (`SUB`/`NOT_IN`).
- Every derived recipe is **executed** in a scratch repo, not asserted — the
  same bar `guard_direction.check_liveness` sets for the typed ones.

## What worked / what failed

- ✅ **Both hand-written acts are re-derived exactly**, scope and membership.
  That is the evidence the derivation is real — and its ground truth has
  **n = 2**, the same smallness D-053 found in the table it replaces. Said out
  loud in the test rather than left to read as a validation over the pool.
- 🔴 **Derivable fraction: 4 of 16 root-addressable.** The census is a pinned
  partition: `DERIVED` 4 / `NO_SCOPE` **0** / `NO_REGISTRY` 9 / `NOT_PATHS` 3.
- 🔴 **The layer `acts_of` owns loses nobody, and it is not the binding one.**
  `NO_SCOPE` = 0 — scope is recoverable for all 16. The fraction collapses to 4
  entirely at the two layers `acts_of` says nothing about: 9 guards have no
  `TYPED` exemption naming a constant, and 3 more name a constant whose members
  are claim ids or reading labels, not paths. **Q-068 proposed deriving the part
  that was never the hard part.**
- 🔴 **A fourth part exists, and neither registry names it.**
  `pre_epoch_commits` recovers all three and still reads **empty**. Its
  population is bounded by `--until=<epoch>` over `origin/main..<ref>` — a
  *temporal and topological* precondition on the population, in neither
  `acts_of` (window) nor `Exemption` (registry). Checked against the D-032
  misdiagnosis shape: it reads empty through **all four** scopes, so the
  precedence table did not simply pick wrong.
- 🔴 **Net yield over the typed table: one guard.** D-053's `reach_gap` reported
  **6** readable-but-unprobed, which reads as six probes waiting to be written.
  Executed, the derivation adds exactly **1** (`unregistered_local_only`).
  Readable ≠ wakeable, and 6 → 1 is the size of that difference.
- ✅ `unranked_scopes()` = `()`, and `SCOPE_PRECEDENCE` is pinned equal to
  `guard_reflexivity`'s scope vocabulary minus `UNKNOWN` — so it is a table that
  cannot be outgrown by pool growth, unlike every table D-045/D-047/D-049 caught.
- ✅ First draft passed 12/12. Eleventh first draft in twelve cycles was wrong
  about its own population; this one was not. The difference is that the
  population was measured (`path_members` asks the filesystem whether a
  registry member exists) rather than spelled.
- 🔴 The module entered the registry it audits — pool **41 → 43** (`mutable_scope`,
  `unranked_scopes`). **D-046, 6th occurrence**, and the first adding two.

## North-star delta

- **No avoidance or tracking number moved — twenty-second consecutive instrument
  cycle.** Scenes able to contribute an avoidance number: 5, reportable: 4.
- What moved: "derive the probe table instead of typing it" went from a plan to
  a priced one — 4/16 derivable on paper, **3/16 alive**, **+1** over what is
  already typed. That is a small enough yield that the repair Q-068 proposed is
  not worth shipping as stated, which is what measuring first was for.

## Key learnings

- **When a proposal names the source to derive from, check which part of the
  target that source actually covers.** `acts_of` was the obvious answer and it
  covers the one layer that never fails. The binding constraint was two layers
  it does not touch.
- **A census verdict and an executed verdict are different numbers, and the
  gap is where the missing part lives.** 4 derivable, 3 alive; the one that
  died named a fourth component of a liveness act nobody had enumerated.
- **A readability measurement over-states a probe table's headroom.** D-053's
  6 was honest about what it measured; the thing it is tempting to read it as
  (6 probes available) is 1.
- **A table over a fixed vocabulary is a materially different risk from a table
  over a growing pool.** `SCOPE_PRECEDENCE` is hand-written and its mirror is
  clean *and stays clean* — pinning it against the vocabulary rather than the
  pool is what buys that.

## Recommended next 1–3 priorities

1. **Register `unregistered_local_only` as a third `guard_direction.Probe`** —
   the one guard this cycle proved wakeable and unprobed. Small, and it is the
   entire cash value of Q-068.
2. **Enumerate the fourth part.** `pre_epoch_commits` shows a liveness act also
   needs the population's *own window* (time range, ref topology). Ask how many
   of the 9 `NO_REGISTRY` guards are blocked by that rather than by the missing
   registry — the census currently attributes them all to layer 2.
3. **Extend the substrate measurement to `PACKAGE_SOURCE` (9 guards)** — still
   unbuilt, still unknown rather than known-small (carried from D-053).

## Artifacts

- PR: #67 (open, 49th consecutive cycle writing into it — no new review bandwidth)
- Files touched: `eval/mppi_sandbox/liveness_derivation.py`,
  `eval/mppi_sandbox/tests/test_liveness_derivation.py`, `docs/decisions.md`,
  `docs/deliberations.md`, `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV row appended: yes
