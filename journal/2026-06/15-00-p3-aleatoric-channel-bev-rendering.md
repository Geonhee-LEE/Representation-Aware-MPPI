# P3 aleatoric-channel BEV rendering spec

- **Cycle**: 2026-06-15 00:00 KST
- **Branch**: `autoresearch/p3-aleatoric-channel-bev-rendering`
- **TODO**: `37dc5d39` Spec P3 aleatoric-channel BEV rendering
- **Phase**: P3
- **Status**: keep

## What I tried
- Wrote `docs/aleatoric_channel_bev_rendering.md` as the symmetric sibling of last
  cycle's epistemic channel doc — reusing its grid geometry / per-dim reduction /
  fixed-ref `[0,1]` contract verbatim and stating **only the deltas**.
- Pinned the source-signal split: `aleatoric = mean_k σ²_k`, `epistemic = Var_k μ_k`
  — two reductions of one ensemble forward pass (deep-ensemble decomposition).
- Specced 3 concrete deltas + the cost-routing distinction (see below).

## What worked / what failed
- The "reuse epistemic contract, state only deltas" framing kept the doc tight and
  forced the real design content to the surface: scatter reducer (`mean`/p75, not
  epistemic's `max`), normalization ref (in-distribution scale, not OOD percentile),
  and **cost routing = chance-constraint tightening / CVaR, NOT margin inflation**.
- Surfaced a hard prerequisite that epistemic didn't have: this channel **does not
  exist** unless D-009's ensemble heads are heteroscedastic (NLL variance heads, not
  MSE point heads) — a concrete architecture decision for PR #44 (Q-010).
- Surfaced the degeneracy risk that *defines* the channel's worth: a homoscedastic
  head renders a flat, information-free raster that looks like a valid output —
  needs a spatial-CoV acceptance guard (Q-011).
- Did **not** edit `docs/deliberations.md` this cycle: #50 already prepends Q-009 to
  its top, so a second prepend here would textually conflict (the D-011 multi-branch
  failure mode on an append-at-top file). Q-010/Q-011 are documented inline in §7;
  promotion deferred to a single post-merge cycle.

## North-star delta
- 3 of 5 risk-BEV channels now design-pinned (static via D2 lane, epistemic #50,
  aleatoric this cycle). The epi/ale pair — the core P3 reason-for-being — is complete.
- No measured numbers yet (still 0 quantitative baselines; blocked on user sim run).
- Exposed a real upstream constraint on the D-009 scaffold (#44): heteroscedastic
  heads are now a *named requirement*, not an implicit assumption.

## Key learnings
- Aleatoric vs epistemic is not just "different source" — it's **different cost
  routing**. Routing irreducible noise through epistemic's margin-inflation would
  bake in permanent over-conservatism that never improves with data. This is the
  load-bearing reason the two stay separate channels.
- The aleatoric channel is only worth a row **iff the variance head is
  heteroscedastic**. This flips a modeling choice (NLL vs MSE heads) from "nice to
  have" into a P3-channel prerequisite — should inform the #44 review.

## Recommended next 1–3 priorities
1. **Spec the multi-channel risk BEV stack tensor** (`37dc5d39-…-0436`, already Today)
   — now that epi+ale are both pinned, the `[5,H,W]` channel-order + unobserved-mask
   contract can unify them. Natural next, still doc-only / merge-unblocked.
2. **Promote Q-010/Q-011 to `deliberations.md`** in a single cycle after #50 (Q-009)
   and #51 land on main — verify numbering at promotion time (avoid the multi-branch
   top-of-file conflict that blocked doing it now).
3. **Spec margin-inflation cost-critic interface** (`37cc5d39-…-8171`, Today) — pairs
   with the aleatoric chance-constraint routing so the two critic entry points share
   one config surface.

## Artifacts
- PR: #51 (autoresearch/p3-aleatoric-channel-bev-rendering)
- Files touched: docs/aleatoric_channel_bev_rendering.md, results/p3-aleatoric-channel-bev-rendering.tsv
- TSV row appended: yes
