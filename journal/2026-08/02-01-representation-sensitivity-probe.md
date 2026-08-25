# A seed-free probe that measures whether a cost term reads its representation — and a partial retraction of 00:00's verdict

- **Cycle**: 2026-08-02 01:00 KST
- **Branch**: none (gate 1 fired, **20th consecutive**) — measured in a throwaway worktree off `origin/main` + `#66`+`#67`+`#68`+`#69`
- **TODO**: none picked — SKIP path, `reason=pr-queue-full count=6`
- **Phase**: P3/P5 (calendar phase P4)
- **Status**: in_progress (result measured, cannot be committed until the queue drains)

## What I tried

- Gate 1 re-derived per-branch: **6 OPEN** (`#66/#67/#68/#69/#44/#23`), 0 pushed-but-PR-less, 0 branches
  in 24 h, daily-cap 0/10. `grep -cE '^\s*-?\s*\*\*Status\*\*:.*superseded' docs/decisions.md` → **0**,
  deadlock-breaker crit (b) still has no candidate; not forced. `.last_escalation` 07-31 22:01 → floor
  **08-03 22:01**, not re-sent. Last merge #64 @ 2026-07-12 → **20.5 d**. Merge recipe re-verified a
  **10th** time (#66↔#67 conflict on `test_risk_mppi.py` + `docs/deliberations.md`, resolve for #66).
- Took 00:00's recommendation **#2** (contract test) and **#3** (a scene with a modeled, visible
  obstacle) — the two items that do not need the queue.
- **Built the probe (#2).** 00:00 caught the bug with 30 s of *static* introspection on
  `_extra_cost`'s free variables. I turned that into a *measured*, seed-free invariant: hold the rollout
  batch **fixed** (256×30, generated with no reference to any scene), vary **only** the scene's
  obstacle content, and see whether the cost value moves. Five variants share start/goal/path/speed:
  `empty`, `visible_off`, `visible_on`, `hidden_far` (out of `sensing_range`), `occluded` (behind a
  nearer disc). The decisive contrast is `visible_on` vs `hidden_far` vs `occluded` — an obstacle is
  ahead in all three and **only the robot's knowledge of it differs**.
- `StockMPPI._cost` under the gate is carried as a **positive control**, so an "insensitive" verdict
  cannot be vacuous.
- **Built the presence family (#3)** — `probe_{empty,off_path,on_path}_v0.yaml`, geometry-matched, the
  only difference being the `dynamic_obstacles` block. These are the **first non-empty "nothing hidden"
  scenes** in the matrix. Closed-loop, N=16 paired by seed.

## What worked / what failed

**1. ✅ The probe is decisive, and it needs no seeds at all.**

| term (fixed batch) | empty | visible_off | visible_on | hidden_far | occluded | max\|Δ\| | verdict |
|---|---|---|---|---|---|---|---|
| `_cost` **(positive control)** | 684.71 | 703.63 | 11184.34 | 684.71 | 11184.34 | **1.06e+04** | READS the scene |
| `vg_mppi._extra_cost` | 0 | 0 | 0 | 0 | 0 | 0.00e+00 | BLIND |
| `proto_evg._extra_cost` | 219.2467 | 219.2467 | 219.2467 | 219.2467 | 219.2467 | **0.00e+00** | BLIND |
| `uniform_soft._extra_cost` | 184.2645 | ″ | ″ | ″ | ″ | 0.00e+00 | BLIND |
| `horizon_slow._extra_cost` | 183.6518 | ″ | ″ | ″ | ″ | 0.00e+00 | BLIND |
| `near_slow._extra_cost` | 149.2823 | ″ | ″ | ″ | ″ | 0.00e+00 | BLIND |

`proto_evg` is **bit-identical to the last digit** across a scene with nothing in it and a scene with an
unseen hazard 3 m ahead. Not "small" — *exactly* zero. The positive control moves by 1.06e+04 on the
same batch, so the instrument works.

**2. 🔴 Partial retraction of 00:00 (and of the STATE line it produced).** The positive-control row is
the surprise: **the visibility gate itself is genuinely representational.** `_cost` separates
`visible_on` from `hidden_far` by **10 499.6**, and `hidden_far` equals `empty` to the last digit
(684.7123 both) — an unobserved obstacle is *correctly* dropped from the planner's world. `occluded`
equals `visible_on` exactly, because the shadowed disc is dropped and the nearer one is not.
So "the P3 hypothesis has **zero** surviving quantitative support" (STATE, 00:00) is **too strong**.
The precise statement is: **the representation exists and provably changes the cost; the *response*
term named "epistemic" is what carries no representational content.** Representation ✓, reaction ✗.

**3. ✅ Recommendation #3 discharged — the toll is unchanged by a present, visible obstacle.**
Closed-loop, N=16, paired, toll = Δduration vs each arm's own `vg` baseline:

| arm | empty | off_path | on_path |
|---|---|---|---|
| `proto_evg` | +0.04 s (+0.3 %) | −0.03 s (−0.2 %) | +1.01 s (+6.2 %) |
| `horizon_slow` | −3.55 s (−22.7 %) | −4.11 s (−25.4 %) | −3.88 s (−23.7 %) |

`toll(on_path) − toll(empty)` = **+0.97 s, CI [−0.45, +2.39]** for `proto_evg` (and −0.33 s,
CI [−1.38, +0.73] for `horizon_slow`) — both include zero. Putting a real, fully-observed obstacle in
the robot's way does **not** move the "epistemic" toll. The open-loop probe carries into closed loop.

**4. ❌ My own mechanism hypothesis, refuted within the cycle.** `horizon_slow`'s unexplained speed-up
(00:00: −7.7 %) reproduces **much larger and on a completely different scene family**: −22 % to −25 %
across all three probe scenes, so it is not a curved-path artifact. I proposed a mechanism — the
terminal cost `w_terminal·d_goal²` demands progress, the distal penalty forbids making it late, so the
optimizer rushes early and MPPI executes only the early part. **Ablation kills it**: at
`w_terminal = 0` the speed-up *persists* at −21.5 % (30.0 → −24.3 %, 10.0 → −21.2 %, 0.0 → −21.5 %).
Reporting it dead rather than shipping the story. `h0_frac` is monotone in the penalised fraction
(0.25 → −22.8 %, 0.50 → −24.3 %, 0.75 → −15.8 %, 0.90 → −12.4 %), and the constraint any future
explanation must satisfy is: **uniform (near+distal) `v²` is slow; distal-only `v²` is fast.**

**5. ⚠️ New confound found in the baseline itself.** On a straight, empty 7 m path with
`target_speed = 0.9 m/s`, the `vg` baseline achieves **mean v = 0.441** and takes **15.7 s** against an
~7.8 s ideal — less than half target speed with `mean|cte| = 0.016` (i.e. not a tracking problem).
Every duration-based comparison in the last four cycles, including the +2.9 % vs +17.9 % headline, is
measured against this slow baseline.

## North-star delta

- **First reusable *instrument* rather than another result.** The probe is ~15 LOC of contract plus a
  variant table, runs in well under a second, needs no seeds, and would have caught the three-cycle
  error before the first measurement. It generalises to every future representation-bearing critic
  (`RiskInflationCritic`, `AleatoricRiskCritic`, the BEV channels) — each can be required to move
  under a change in the state it is named for.
- **The P3 picture is now more precise, not just more negative.** Three cycles of retraction had
  driven the claim to "zero support"; this cycle shows the visibility gate *does* carry the
  information (1.05e+04 separation, `hidden_far ≡ empty` exactly). The gap is specifically that no
  controller yet *reacts* to it in a way that beats a non-representational control arm.
- **The measured tolls are on softer ground than assumed** — a baseline running at 49 % of target
  speed makes "+2.9 % time cost" hard to interpret. This is a P5 harness prerequisite, not a P3 one.

## Key learnings

- **Introspection finds the bug; a positive control makes it a measurement.** The whole probe would
  have been worthless without `_cost` in the table — "everything is insensitive" is exactly what a
  broken probe also reports. The positive control is the load-bearing part.
- **"Zero support" was an over-correction.** Three consecutive retraction cycles built momentum toward
  the strongest negative claim available, and the one row I added as a *sanity check* falsified it.
  When a narrative is monotonically darkening, the sanity check is where the information is.
- **Refuting my own hypothesis inside the same cycle cost 40 s** (one `w_terminal` sweep) and was the
  single highest-value minute spent — 00:00 flagged this sign as unexplained, and the most natural
  explanation is now eliminated rather than left plausible.
- Fourth consecutive cycle in which the blocked queue cost nothing (~2 min CPU here). The record is
  now **13 uncommitted journal entries**, and this one *partially retracts* the previous one.

## Recommended next 1–3 priorities

1. **Land the probe as `test_cost_term_reads_its_named_state`** — highest value in the backlog now.
   Parameterise over the registry: every critic declares the state it is named for, and the test
   asserts a non-zero `max|Δ|` under a change to that state, with `_cost` as the in-test positive
   control. Supersedes 00:00's item 2 with a working implementation.
2. **Fix the baseline's 49 %-of-target speed before any further duration comparison** (finding 5).
   Until then `time_to_goal` deltas are measured against a controller that is not trying to hit its
   target speed. This now gates the P5 metric set.
3. **Correct the STATE/journal claim to "the gate is representational; the response is not"** when the
   queue drains — the on-disk record currently overstates the negative.
4. **Q-023 (raised, not self-authorized)**: should every representation-bearing critic be required to
   declare its input state in metadata, so the probe can be generated rather than hand-written?

## Artifacts

- PR: **none** — gate 1 (`pr-queue-full count=6`) blocks branch creation; result is uncommitted.
- Files touched: this journal entry + `STATE.md` / `JOURNAL.md` (local-only per D-011).
- TSV row appended: no (no branch).
- Prototype source + scenario yamls + raw JSON: `/tmp/proto_0802_01/`
  (`_proto_probe.py`, `_proto_presence.py`, `_proto_arms.py`, `probe_{empty,off_path,on_path}_v0.yaml`).
- Reproduce: merge `#66→#67→#68→#69` into a worktree off `origin/main` (resolve `#66↔#67` in favour of
  `#66`), drop `_proto_arms.py` into `controllers/` and the two `_proto_*.py` into `eval/mppi_sandbox/`,
  copy the three yamls into `eval/scenarios/`, then
  `python3 -m eval.mppi_sandbox._proto_probe` (< 1 s) and
  `python3 -m eval.mppi_sandbox._proto_presence` (~45 s).
