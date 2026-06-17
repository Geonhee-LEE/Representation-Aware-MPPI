# P3 multi-channel risk BEV stack tensor contract

- **Cycle**: 2026-06-17 23:00 KST
- **Branch**: `autoresearch/p3-multi-channel-risk-bev-stack-tensor`
- **TODO**: `37dc5d39` Spec multi-channel risk BEV stack tensor [5,H,W] channel order + unobserved-mask channel
- **Phase**: P3
- **Status**: keep

## What I tried
- Wrote `docs/multi_channel_risk_bev_stack.md` — the canonical owner of the `[5,H,W]`
  risk-stack contract the epistemic (#50) + aleatoric (#51) docs only forward-referenced.
- Fixed the `RiskChannel` index order (static/dynamic/traversability/epistemic/aleatoric),
  the `[C,H,W]` explicit unobserved-mask (NaN-distinct-from-zero), per-channel routing,
  and partial-stack handling (unimplemented rows = all-unobserved).
- Added D-012 codifying the order + mask decision. Kept O-1/O-2/O-3 inline.

## What worked / what failed
- The two merged/queued channel docs already designated this TODO as the contract owner,
  so the doc closed a real forward-reference debt rather than inventing scope.
- Caught a live conflict trap: open #50 touches `deliberations.md` AND `README.md` AND
  the snapshot files — so I deliberately edited **neither** deliberations.md nor README.md
  (would re-create the D-011 concurrent-prepend conflict). Only the new doc + decisions.md
  (which #50 does not touch) went on the branch. Diff verified snapshot-clean.
- Corrected a stale-STATE belief: queue is **5, not 6** (a transient `gh` failure had
  mis-counted the merged-today #51 aleatoric branch as pushed-but-PR-less). Merges are
  flowing (#51 today, #49 06-14, #47 06-12) — the "9-day merge deadlock" in STATE has eased.

## North-star delta
- + The single MPPI-cost input interface for the P3 risk field is now pinned (channel
  order frozen, observability semantics decided) — every later channel renderer plugs in
  without re-negotiating the cost critic's input.
- + The unobserved-mask decision directly serves the 미관측/가려진 axis (a cell never seen
  is no longer silently zero-risk) — the exact gap today's feed (CMPC occlusion, DUCCT
  localization uncertainty) flags. No code/sim movement (design-only).

## Key learnings
- Before editing any append-at-top shared doc (deliberations/README/decisions), check
  which **open** PRs already touch it — #50's file list was the deciding input this cycle.
  decisions.md was safe; the other two were not.
- The P3 design lane is converging: channels (epi/ale) → **stack contract (this)** →
  cost-critic interface (next). The remaining doc step is the margin-inflation interface.

## Recommended next 1–3 priorities
1. **Spec the margin-inflation cost-critic interface** (`37cc5d39-…-8171`, Today) — now the
   stack contract it consumes exists; this is the natural next + last P3 design-lane doc.
2. **Promote Q-010/Q-011 (+ O-1/O-2/O-3) to deliberations.md** once #50 merges — batch all
   deferred Q's in one post-merge cycle to avoid the concurrent-prepend conflict.
3. (user) Merge the P3 doc PRs (#50 epistemic, #52 this) + the P2 build-path cluster
   (#44→#45→#23) so the EnsembleResidualDynamics code lane unblocks.

## Artifacts
- PR: https://github.com/Geonhee-LEE/Representation-Aware-MPPI/pull/52 (pending merge)
- Files touched: docs/multi_channel_risk_bev_stack.md, docs/decisions.md, results/p3-multi-channel-risk-bev-stack-tensor.tsv
- TSV row appended: yes
