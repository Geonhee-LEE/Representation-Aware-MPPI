# SPDX-License-Identifier: BSD-3-Clause
"""Rate-over-seeds aggregator: run one (scenario, controller) across N seeds and
report **collision / near-miss / pass rate**, not a single-seed clearance number.

Motivation (STATE 2026-07-16, cycle p3-visibility-gated-obstacle-cost): on the
sandbox's agile diff-drive plant with a strong `w_collision` barrier, the
single-run **min-clearance saturates at the barrier floor** — it does *not*
separate an oracle controller from an epistemic-blind one on a late-reveal
occlusion scene. The signal that *does* separate them is stochastic: over a seed
sweep the blind controller collides on some fraction of seeds while the oracle
clears all of them (e.g. `vg_mppi` 3/8 vs `stock_mppi` 0/8 on
`cafe_blind_approach_v0`). This module makes that fraction a first-class metric
so P5's occlusion axis can score **rate over seeds** rather than surviving
clearance.

Schema is aggregation-only: it reuses `run_scenario`'s per-seed result verbatim
and derives rates from the `min_obstacle_clearance` / `pass` fields — it adds no
new simulation behavior, so a single-seed sweep reproduces `run_scenario`
numbers exactly.

CLI:
    python -m eval.mppi_sandbox.seed_sweep eval/scenarios/cafe_straight_v0.yaml \
        --controller stock_mppi --seeds 8 --near-miss-m 0.10 \
        --run-id straight-stock-sweep --out-dir runs
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from .run import run_scenario

# Default near-miss band: a positive clearance strictly below this many metres is
# a "near miss" (did not collide, but grazed inside the safety margin). 0.10 m is
# one third of the r=0.3 footprint — tunable per scenario acceptance later.
DEFAULT_NEAR_MISS_M = 0.10


def _classify(clearance: float, near_miss_m: float) -> str:
    """collision (<0) / near_miss (0 ≤ c < near_miss_m) / safe (≥ near_miss_m)."""
    if clearance < 0.0:
        return "collision"
    if clearance < near_miss_m:
        return "near_miss"
    return "safe"


def seed_sweep(scenario_path: str | Path, *, controller: str = "stock_mppi",
               seeds=range(8), near_miss_m: float = DEFAULT_NEAR_MISS_M,
               run_id: str | None = None, out_dir: str | Path | None = None,
               **controller_kwargs) -> dict:
    """Run `controller` on `scenario_path` once per seed; aggregate outcome rates.

    Returns a dict with per-seed rows and the sweep-level rates. `seeds` may be
    any iterable of ints (e.g. `range(8)` or `[0, 3, 7]`). Rates are fractions in
    [0, 1] over the number of seeds actually run.
    """
    seeds = [int(s) for s in seeds]
    if not seeds:
        raise ValueError("seed_sweep needs at least one seed")
    if near_miss_m < 0.0:
        raise ValueError("near_miss_m must be non-negative")

    per_seed = []
    for s in seeds:
        r = run_scenario(scenario_path, controller=controller, seed=s,
                         run_id=None, out_dir=None, **controller_kwargs)
        clearance = r["min_obstacle_clearance"]
        per_seed.append({
            "seed": s,
            "min_obstacle_clearance": clearance,
            "collision": r["collision"],
            "pass": r["pass"],
            "outcome": _classify(clearance, near_miss_m),
        })

    n = len(per_seed)
    n_collision = sum(1 for p in per_seed if p["outcome"] == "collision")
    n_near_miss = sum(1 for p in per_seed if p["outcome"] == "near_miss")
    # `pass` is None for scenarios with no hard acceptance checks; count only
    # explicit True so pass_rate stays meaningful (None → not a pass).
    n_pass = sum(1 for p in per_seed if p["pass"] is True)
    finite_clear = [p["min_obstacle_clearance"] for p in per_seed]

    result = {
        "run_id": run_id or f"{Path(scenario_path).stem}-{controller}-sweep",
        "started_at": datetime.now(timezone.utc).astimezone().isoformat(),
        "backend": "mppi_sandbox",
        "kind": "seed_sweep",
        "scenario": str(scenario_path),
        "controller": controller,
        "controller_kwargs": controller_kwargs,
        "seeds": seeds,
        "n_seeds": n,
        "near_miss_m": near_miss_m,
        "collision_rate": n_collision / n,
        "near_miss_rate": n_near_miss / n,
        # unsafe = collided OR grazed: the headline occlusion-sensitivity number.
        "unsafe_rate": (n_collision + n_near_miss) / n,
        "pass_rate": n_pass / n,
        "clearance_min": min(finite_clear),
        "clearance_mean": sum(finite_clear) / n,
        "per_seed": per_seed,
    }
    if out_dir is not None:
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        (out / f"{result['run_id']}.json").write_text(
            json.dumps(result, indent=2) + "\n")
    return result


def _parse_seeds(spec: str) -> list[int]:
    """`8` → range(8); `0,3,7` → those seeds; `2-5` → 2..5 inclusive."""
    spec = spec.strip()
    if "," in spec:
        return [int(x) for x in spec.split(",") if x.strip() != ""]
    if "-" in spec:
        lo, hi = spec.split("-", 1)
        return list(range(int(lo), int(hi) + 1))
    return list(range(int(spec)))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("scenario", help="path to eval/scenarios/*.yaml")
    ap.add_argument("--controller", default="stock_mppi")
    ap.add_argument("--seeds", default="8",
                    help="count (8), list (0,3,7), or range (2-5)")
    ap.add_argument("--near-miss-m", type=float, default=DEFAULT_NEAR_MISS_M)
    ap.add_argument("--run-id", default=None)
    ap.add_argument("--out-dir", default="runs")
    ap.add_argument("--ctrl-arg", action="append", default=[],
                    metavar="KEY=VALUE",
                    help="controller kwarg, e.g. --ctrl-arg w_risk=15")
    args = ap.parse_args(argv)
    kwargs = {}
    for pair in args.ctrl_arg:
        key, value = pair.split("=", 1)
        try:
            kwargs[key] = float(value)
        except ValueError:
            kwargs[key] = value
    result = seed_sweep(args.scenario, controller=args.controller,
                        seeds=_parse_seeds(args.seeds),
                        near_miss_m=args.near_miss_m,
                        run_id=args.run_id, out_dir=args.out_dir, **kwargs)
    # Print the aggregate without the (potentially long) per-seed block.
    head = {k: v for k, v in result.items() if k != "per_seed"}
    print(json.dumps(head, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
