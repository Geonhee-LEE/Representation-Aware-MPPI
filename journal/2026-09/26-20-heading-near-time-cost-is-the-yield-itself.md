# The time cost of the speed-gated heading price is the yield itself

- **Cycle**: 2026-09-26 20:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `3c4c5d39` [sandbox] knee+shape 아래 heading_err_rms_max 공략
- **Phase**: P6 (TODO tagged P5)
- **Status**: in_progress

## What I tried
- Discharged the 10:00 strand first (D-112): `push_preflight record` came back 4537 passed / 0 failed in 1099 s, and I pushed `9222167..101383e`. `stranded` is clean after the push.
- While that suite ran I measured where w=64 + v_gate=0.45 spends its extra time-to-goal. I used scripts in `/tmp` only, so the tree stayed on the receipt. The runs used paired seeds 0–31, and I split the time by path progress (first-passage time at y = -1, -2, -3, -4, -4.7).
- I also ran a cross-scene check: knee+shape at w=0 vs w=64+0.45, seeds 0–15, on all 9 `*_v0` scenes.

## What worked / what failed
- Segment times, w=0 vs gated w=64: 0→-1 2.27→4.09, -1→-2 3.35→5.00, -2→-3 2.82→4.44, -3→-4 2.15→2.11, -4→-4.7 2.27→2.29, settle 6.07→6.31 s. So **+5.1 of the +5.3 s is in the first 3 m**, before and during the crossing. Once past the crosser, the time is unchanged.
- The ungated w=64 arm loses +4.3 s in the same segments. The cost is therefore not "slowing down to escape the price", which was D-503's guess and is now refuted. The heading price swaps cutting in front of the crosser (w=0 seed 0 swings out to x=+1.07 m) for waiting and then driving straight.
- Cross-scene: convoy, freezing, contested, straight, city_curved and figure8 are equal or better. head_on arrives 1.6 s later (15.8→17.4). cut_in (goal ball blocked, 0/16 goals in both arms) goes from 0 to 1 clearance fails.
- A first clearance-band split (near < 1.05 m vs far) was misleading. The crossers move, so a late arrival at the goal counts as "far". Splitting by path progress fixed it.
- Not pushed: after the strand suite `cycle_wallclock` read SUITE_UNAFFORDABLE (19m03). This report is a deliberate strand.

## North-star delta
- No controller change. The open question behind a default change is now narrower: the ~5 s is the price of yielding instead of cutting in front. That is a policy choice (safety margin vs time-to-goal), not a tuning artefact. A |v| ramp would not recover it.

## Key learnings
- When obstacles move, a clearance-based time split is confounded by arrival time. Split by path progress instead.
- Always run the ungated arm as a control before blaming a gate for a side effect.

## Recommended next 1–3 priorities
1. Discharge this strand (suite + record + push).
2. Localize the single cut_in clearance fail under w=64+0.45 (which seed, and whether it is a real contact or the blocked goal ball).
3. head_on also fails heading on 16/16 under both arms. Check whether D-499's near-obstacle localization holds there before extending the gated price.

## Artifacts
- PR: none (PR #67 closed by user 09-21). Strand: report commit, not pushed this cycle.
- Files touched: docs/decisions.md, journal/2026-09/26-20-heading-near-time-cost-is-the-yield-itself.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: yes
