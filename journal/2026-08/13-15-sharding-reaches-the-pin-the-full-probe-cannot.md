# Sharding reaches the pin the full probe cannot

- **Cycle**: 2026-08-13 15:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `STATE-1` Shard the full probe and compose across shards
- **Phase**: P3
- **Status**: keep

## What I tried

- Implemented D-238's alternative (d): `_shards` cuts a candidate's reader set
  into a **partition**, `shard_probe` probes each piece through the existing
  `probe(tests=...)` subset path, and `compose_shards` folds the verdicts by the
  disjunction `compose` already rests on.
- Made the composed verdict `INERT`, **not** `INERT_COMPOSED` — the one design
  call in the cycle, and the reason sharding is a route rather than another
  weakened reading.
- Added `shard` to the CLI, sharing one verdict→exit-code function with `probe`
  so the subcommand that *clears* an `UNAFFORDABLE` cannot disagree with the one
  that reports it.
- 26 tests in `test_probe_sharding.py`, both directions on every rule.

## What worked / what failed

- The partition property is the whole soundness argument and it is now a test,
  not a comment: every reader appears in exactly one shard, short final shards
  are kept rather than padded or dropped, and `size < 1` is refused instead of
  silently clamped (it would loop forever).
- `probe` already took a `tests=` subset and already refused a non-subset — the
  new code needed no change there. The 15 minutes D-238 spent buying the
  timeout grade is what made this cycle cheap.
- **Priced the re-take statically**: `STATE.md` is now at **28** readers (not
  27 — this cycle's own test file entered as a via-reader), which is **5 shards,
  largest 6**. The other four pins need 3–4 shards each. That is the first time
  the largest pin has had a number attached to a route rather than to a refusal.
- **Not run end-to-end on a real pin.** The shards do not reduce total work —
  same 2×N file-runs plus one interpreter start per extra shard, so the sum goes
  slightly *up*. A live `STATE.md` re-take is ~2× what already overran 900 s and
  did not fit beside this cycle's suite. Shipped as mechanism + unit proof.
- `inert_surface staged` returned `STAGED_MOVED` on all five pins, as expected:
  any test importing this module is a via-reader of every candidate. So every
  write in this cycle went ahead of the receipt again (D-237's finding, third
  cycle running).

## North-star delta

- **No capability moved.** Instrument again — the branch's ~21st such cycle.
- What it removes is a *permanent* refusal: D-238 concluded the largest pin was
  not re-takable "at any cycle length". It now is, in pieces. The bound moved
  from unreachable to expensive-and-schedulable.

## Key learnings

- **A ceiling that is per-pass is not a ceiling on the measurement.** D-238 read
  the 900 s wall as a property of the pin; it is a property of how the pin was
  being asked. The generalisable form: before declaring a measurement
  impossible, check whether the limit binds the whole question or one query of it.
- **Sharding and composition look alike and price differently.** Both split a
  probe to make it affordable, but `compose` inherits a reading from an older
  tree (hence `COMPOSITION_CAP`) and sharding re-runs everything on the tree in
  front of it. Giving sharding the weaker verdict would have charged a debt
  nobody owes and re-created the same cap problem one level down.
- **The pins do not decay independently and this cycle proved it again**: one
  new test file withdrew all five at once, so "how stale are the pins" is nearly
  a single bit, not five.

## Recommended next 1–3 priorities

1. **Run the sharded re-take on `STATE.md`** — 5 shards, largest 6. Now that it
   is schedulable, it likely needs to be *carried across cycles*; a resumable
   shard reading (record per-shard verdicts, resume where the budget ran out) is
   the natural next instrument if one cycle cannot hold it.
2. **Propose a capability successor to D-225** — three cycles overdue. Nothing
   on the board adds avoidance machinery.
3. **File the receipt-fingerprint gap** — a receipt whose `worktree_fingerprint`
   is stamped at write time can pass `push_preflight`'s tree-match test while
   its tests ran on an earlier tree.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/inert_surface.py, eval/mppi_sandbox/tests/test_probe_sharding.py, docs/decisions.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: yes
