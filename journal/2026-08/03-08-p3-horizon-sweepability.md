# The rollout horizon is not a sweepable axis — and the freeze is a cause leave-one-out cannot see

- **Cycle**: 2026-08-03 08:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic` (26th consecutive write into PR #67, already in the queue)
- **TODO**: STATE #1 — run Q-043's `(w_voo, horizon)` 2×2 at a scale-matched weight
- **Phase**: P3
- **Status**: keep

## What I tried

- Took STATE #1, which D-029 had fully specified (crossing scene, `lam ∈ {1.6, 3.2}`, ratio ≤ 0.25, no window recalibration owed) and which was ungated on the crossing half.
- Before crossing `w_voo` with `horizon`, swept the **baseline** (`w_voo = 0`, every other weight shipped) down the horizon axis alone — the control the 2×2 needs and would not otherwise have had.
- The baseline turned out to fail, so the cycle became: locate the failure, attribute it by intervention, and check what the existing guards say about it.
- Shipped `eval/mppi_sandbox/horizon_audit.py` (`scan` / `cruise_ceiling` / `ablate` / `redundant_sets`), made `scale_match.exchange_rate` horizon-aware, and added an optional `max_steps` to `run.simulate` / `ab.run_arm`.

## What worked / what failed

- 🔴 **The 2×2 cannot be run.** Baseline cruise is 0.800 / 0.800 / 0.772 at `H = 15 / 30 / 34` and **0.1135 at `H = 35`** — a **6.8× collapse in one rung**, sustained through `H = 60`. It is a real edge, not a threshold artefact: `H = 34` still holds **96.6 %** of the shipped rung's cruise. The horizon axis has exactly one admissible rung, so the 2×2 degenerates to the 1×2 D-027 already ran, and Q-043's "lengthen the cone" branch is refuted at the *baseline*, before `w_voo` is involved at all.
- 🔴 **The finding worth carrying is about attribution, not horizons.** At `H = 45`: zeroing `w_collision` alone → cruise 0.1287, zeroing `w_obs_soft` alone → 0.1201, against intact 0.1331. That is **0.97× and 0.90× — not a small improvement but none**. Zeroing **both** → **0.7479, a 5.6× restoration**, back into the healthy band. The two obstacle terms are **substitutes**: each is independently sufficient to make standing still the cheapest plan at this horizon. **Leave-one-out credits each with ≈ 0 responsibility for a behaviour they jointly and entirely determine** — and `weight_units.measure`, D-028's instrument, is LOO by construction.
- 🔴 **D-028's damage guard passes on a frozen baseline.** `check_undamaged` is *relative* — probe length vs baseline length — and at `H = 45` both arms are frozen equally, so it reads `damage = 0.69` on an arm that is not driving. The number it then certifies is wrong in the flattering direction: a frozen robot presents a flat landscape, `rest` falls 163.6 → **38.8** from `H = 34` to `H = 45`, and the prescribed scale-matched weight (4.27) is **3.3× smaller** than the last healthy rung's (13.97).
- 🔴 **The weight axis would not have survived the horizon axis either.** Almost every term in `_cost` is a sum over `H`, so ratio-0.25 `w_voo` reads **7.00 / 10.74 / 13.97** at `H = 15 / 30 / 34` — **2.0× over a 2.3× horizon change**, the same order as the 2.11× `lam` swing D-029 called a fixed point. A 2×2 holding `w_voo` fixed down its horizon column confounds a weight change with a horizon change.
- ⚠️ **Both existing guards are silent on this class.** `all_reached` is **True on every frozen rung** (they do finish, 9× slower), so `assert_all_reached` is useless here and only `cruise_speed` separates the rungs — D-025 arriving a second time, D-026's `city_figure8_v0` signature. And **clearance improves monotonically through the collapse** (+0.0193 at `H = 34` → +0.3585 at `H = 60`, **18.6×**): read without the cruise column, the table says a longer horizon is safer.
- ✅ The truncated probe (`max_steps = 160`) gives a **verdict identical** to the full-timeout version on the ablation — same `redundant_sets` answer, ~5× cheaper. Both were run; the table in the module docstring is the full-timeout one.
- ⚠️ Honest cost: the new file is **122 s** of suite time, and trimming the ablation fixture to 1 seed bought only 15 s of that. The floor is three measurements that *must* run untruncated or they stop asserting what they assert (the frozen arm still reaching the goal; the two exchange rates at the frozen rung). That is the wrong direction while STATE #3 is open, and it is now an argument for a `slow` marker rather than for deleting evidence.

## North-star delta

- **No avoidance or tracking number moved** — and one previously-plausible route to moving one is now closed. That is the value: the horizon column of a 2×2 that would have been read as a `w_voo` result is unrunnable, and finding it out cost one cycle instead of one cycle plus a retraction.
- One new repo-wide safety fact: **`v_max` handicapping cannot control the horizon axis.** A handicap only lowers a speed limit; the frozen arm is slow by *choice*, not by limit. So the two horizons cannot be run at matched speed and the axis is not inconvenient but **unidentifiable**.
- Scenes able to contribute an avoidance number: **5**, reportable: **4** — unchanged.

## Key learnings

- **"Neither, but both" is a shape leave-one-out cannot represent.** The gap between "what does this weight add on the margin" and "what causes this behaviour" is exactly the size of the redundancy, and it is invisible in a LOO table because the table has no cell for it. Sweep the power set of a *short* suspect list when the singletons all read ≈ 0 and the behaviour plainly changed.
- **A relative guard cannot see that its own reference is broken.** D-028's damage check compares probe to baseline; when both are frozen it certifies the pair. Every ratio-against-a-baseline instrument in this repo needs an *absolute* precondition on the baseline in front of it — `cruise_ceiling` is that for this one.
- **Measure the control on the axis you intend to sweep, before you cross it with anything.** The whole cycle is the baseline column of a 2×2 that was never worth running. Cheap, and it would have been a retraction otherwise.
- **Ranking the mechanism by reading the cost function failed again**, for the second cycle running (D-026). My prior was "the `any`-over-`H` collision indicator fires more often at longer horizons"; the singleton ablation refutes it as a *sole* cause, and the early-step firing fractions (0.46–0.63 at `H = 34` vs 0.16–0.45 at `H = 38`) point the wrong way outright.

## Recommended next 1–3 priorities

1. **Mark or split the slow tests** (STATE #3, now worse — this cycle added ~90 s). The derailed/frozen-arm assertions are the bulk and they are the *evidence* for D-029 and D-030, so the fix is a `slow` marker with a fast default, not shorter caps.
2. **Reproduce the redundancy on a second scene** before Q-052's lean becomes a tool default. Redundancy may be a property of `(scene, horizon, lam)`, not of the term pair — at `H = 30` there is no freeze and so no redundancy either.
3. **Re-measure the self-vs-baseline denominator gap at the shipped `lam = 0.1`** (STATE #2, untouched and still unverified — D-028's exploratory read suggests the verdict *flips* there).

## Artifacts
- PR: #67 (existing, already in the review queue — no new PR opened)
- Files touched: `eval/mppi_sandbox/horizon_audit.py` (new), `eval/mppi_sandbox/tests/test_horizon_audit.py` (new), `eval/mppi_sandbox/run.py`, `eval/mppi_sandbox/ab.py`, `eval/mppi_sandbox/scale_match.py`, `docs/decisions.md` (D-030), `docs/deliberations.md` (Q-052)
- TSV row appended: yes
