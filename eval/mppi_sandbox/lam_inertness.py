# SPDX-License-Identifier: BSD-3-Clause
"""Which arms the `lam` ladder can actually move — and why 8 cells admit the shipped default.

STATE carried this bottleneck for five cycles: :data:`operating_point.SHIPPED_LAM`
= ``0.1`` is admissible in exactly **8 of 72** reportable cells, all of them
`essps_mppi`, one per scene. The proposed first cut was to read those 8 windows
and classify ``0.1`` as sitting at a window **edge** (a calibration boundary
effect) or in its **interior** (a real property of the arm).

Both options are refuted by the read, because the windows have no edge on the
ladder. All 8 admit **every rung**::

    ('cafe_convoy_v0.yaml',            'essps_mppi') -> (0.05 … 6.4)   8 of 8
    ('cafe_freezing_v0.yaml',          'essps_mppi') -> (0.05 … 6.4)   8 of 8
    ('cafe_head_on_v0.yaml',           'essps_mppi') -> (0.05 … 6.4)   8 of 8
    ('cafe_obstacle_contested_v0.yaml','essps_mppi') -> (0.05 … 6.4)   8 of 8
    ('cafe_obstacle_crossing_v0.yaml', 'essps_mppi') -> (0.05 … 6.4)   8 of 8
    ('cafe_straight_v0.yaml',          'essps_mppi') -> (0.05 … 6.4)   8 of 8
    ('city_curved_v0.yaml',            'essps_mppi') -> (0.05 … 6.4)   8 of 8
    ('city_figure8_v0.yaml',           'essps_mppi') -> (0.05 … 6.4)   8 of 8

The mechanism, and it is not a calibration fact
------------------------------------------------
`controllers.essps_mppi` is `RiskMPPI` with :meth:`_softmax_lam` overridden to
**solve** the temperature per iteration (D-325). The override reads
``self.target_fraction`` and the step's cost vector; it reads ``self.p.lam``
only on a fallback path its own docstring says "for a non-degenerate cost vector
cannot happen". So the temperature the ladder sweeps **never reaches the
softmax**. :func:`probe` measures exactly that — the same cost vector through
the same method at the ladder's two endpoints:

    essps_mppi   lam=0.05 -> 4.571501   lam=6.4 -> 4.571501    inert
    stock_mppi   lam=0.05 -> 0.05       lam=6.4 -> 6.4         responds

Eight identical outputs across a 128x input range is not robustness. It is a
swept parameter that the arm does not read.

What that costs the census
--------------------------
Three consequences, and only the first was asked for.

1. **"admissible at the shipped default" is not a property of ``0.1`` here.**
   ``0.05`` has the *same* support — the same 8 cells, by
   :func:`rung_support` — and so does every other rung. The 8 is a count of the
   scenes `essps_mppi` completes, not of the temperatures it tolerates. A
   ladder cannot calibrate an arm that does not read it, so these 8 rows are
   **vacuous as calibration**: they record a window for an axis with no effect.

2. **``operating_point.ladder_census`` over-states responsive support at every
   rung by exactly the inert cells.** Its shipped table reads
   ``0.2 -> 42 cells``; the responsive count is 42 - 8 = 34.
   :func:`rung_support` returns the partition rather than the total so a caller
   cannot quote the inflated number by accident.

3. **It bears on P5's baseline choice, which is the decision this fed.**
   `essps_mppi` is the only arm admissible at the repo's shipped default, which
   reads as the safe baseline until you notice *why*. Choosing it as P5's
   baseline would pick the one arm whose reported temperature-robustness is an
   artifact of non-response — and D-325 already priced its real cost: perfect
   band compliance bought with **1.37x** the steps to the same endpoint, and
   time-to-goal is a north-star metric where band compliance is not.

Scope, stated because the probe is narrower than the conclusion
---------------------------------------------------------------
:func:`probe` calls ``_softmax_lam`` directly on a **synthetic** cost vector
(:func:`probe_cost`, a seeded gamma draw) at one scene. That is a measurement of
the method, not of an episode: it establishes that the passed ``lam`` does not
reach the returned temperature, which is the whole claim. It does **not** claim
the solved temperature is scene-independent — it plainly is not, since it is a
function of the step's costs. Nothing here simulates a rollout, so the reading
is the same on every machine.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .controllers import REGISTRY, make_controller
from .controllers.stock_mppi import MPPIParams
from .operating_point import SHIPPED_LAM, windows
from .scenario import load_scenario

REPO_ROOT = Path(__file__).resolve().parents[2]

#: The scene the probe constructs on. Any scene works — `_softmax_lam` reads
#: the cost vector it is handed, not the scenario — so this is named for
#: reproducibility rather than chosen for signal. `cafe_straight_v0` is the
#: repo's simplest scene and every arm constructs on it.
PROBE_SCENE = "eval/scenarios/cafe_straight_v0.yaml"

#: The ladder's endpoints. Probing the extremes rather than adjacent rungs
#: makes the negative result as strong as the ladder allows: a 128x input
#: range that moves the output by nothing.
PROBE_LAMS: tuple[float, float] = (0.05, 6.4)

#: Sample count the probe's cost vector is drawn at — `MPPIParams.samples` is
#: 256, but ESS-targeting only needs a non-degenerate spread and 32 keeps the
#: root-find fast. Read from nothing: a probe constant, not a plant fact.
PROBE_K = 32


def probe_cost(k: int = PROBE_K) -> np.ndarray:
    """A fixed, non-degenerate cost vector.

    Seeded and gamma-shaped: ESS-targeting needs a spread of costs to solve
    against (a constant vector has ESS ``K`` at every temperature and would
    make *every* arm look inert), and a fixed seed makes the probe's numbers
    quotable.
    """
    return np.random.default_rng(0).gamma(2.0, 1.0, k) * 10.0


@dataclass(frozen=True)
class LamResponse:
    """What one arm's ``_softmax_lam`` returned at the ladder's two endpoints."""

    controller: str
    lam_lo: float
    lam_hi: float
    out_lo: float
    out_hi: float

    @property
    def responds(self) -> bool:
        """Whether the passed temperature reached the softmax at all."""
        return self.out_lo != self.out_hi

    @property
    def passes_through(self) -> bool:
        """Whether the arm returns the passed temperature verbatim.

        Distinguished from :attr:`responds` on purpose: an arm could scale or
        clip the passed value and still be calibratable. Nothing in the
        registry currently does, and a future one that did would be a third
        verdict rather than a silent member of either existing one.
        """
        return self.out_lo == self.lam_lo and self.out_hi == self.lam_hi

    def __str__(self) -> str:
        verdict = "responds" if self.responds else "INERT"
        return (f"{self.controller:<18} lam={self.lam_lo:<6g} -> {self.out_lo:<10.6g} "
                f"lam={self.lam_hi:<6g} -> {self.out_hi:<10.6g}  {verdict}")


def probe(controller: str, scene: str | Path = PROBE_SCENE,
          cost: np.ndarray | None = None) -> LamResponse:
    """Run one arm's ``_softmax_lam`` at both endpoints of the same ladder.

    The two calls use freshly constructed controllers so no per-step state
    (`essps_mppi` keeps a `lam_log`) can carry between them.
    """
    vec = probe_cost() if cost is None else cost
    lo, hi = PROBE_LAMS
    outs = []
    for lam in (lo, hi):
        arm = make_controller(controller, load_scenario(str(scene)), seed=0,
                              params=MPPIParams(lam=lam))
        outs.append(float(arm._softmax_lam(vec)))
    return LamResponse(controller, lo, hi, outs[0], outs[1])


def responses(scene: str | Path = PROBE_SCENE) -> tuple[LamResponse, ...]:
    """One :class:`LamResponse` per registered arm, in registry order."""
    return tuple(probe(name, scene) for name in REGISTRY)


def inert_arms(scene: str | Path = PROBE_SCENE) -> tuple[str, ...]:
    """Arms the `lam` ladder cannot move.

    Derived by measurement, not transcribed: an arm that later starts or stops
    reading ``p.lam`` moves this set without anyone remembering to edit it.
    """
    return tuple(r.controller for r in responses(scene) if not r.responds)


@dataclass(frozen=True)
class Cell:
    """One calibration row, graded against its own ladder."""

    scene: str
    controller: str
    admissible: tuple[float, ...]
    ladder: tuple[float, ...]

    @property
    def saturated(self) -> bool:
        """Every rung the cell was walked at is admissible.

        Saturation is the *observable* an inert arm produces, and the two are
        checked against each other rather than assumed equal — a responsive arm
        on a forgiving scene could saturate too, and that would be a real
        finding rather than a bookkeeping error.
        """
        return bool(self.ladder) and set(self.admissible) == set(self.ladder)

    @property
    def empty(self) -> bool:
        return not self.admissible


def cells(root: Path | None = None) -> tuple[Cell, ...]:
    """Every calibration row, with its per-cell ladder attached.

    :func:`operating_point.windows` drops the ladder, and the ladder is what
    ``saturated`` needs — a window of 8 rungs means nothing until you know
    whether 8 or 17 were tried.
    """
    import yaml

    from .operating_point import WINDOW_FILES

    out: list[Cell] = []
    for rel in WINDOW_FILES:
        doc = yaml.safe_load(((root or REPO_ROOT) / rel).read_text(encoding="utf-8"))
        default_ladder = tuple(doc.get("ladder") or ())
        for c in doc.get("cells", ()):
            out.append(Cell(
                scene=Path(c["scenario"]).name,
                controller=c["controller"],
                admissible=tuple(c.get("admissible") or ()),
                ladder=tuple(c.get("ladder") or default_ladder),
            ))
    return tuple(out)


def saturated_cells(root: Path | None = None) -> tuple[Cell, ...]:
    return tuple(c for c in cells(root) if c.saturated)


@dataclass(frozen=True)
class RungSupport:
    """Which cells admit one rung, split by whether the arm reads the rung."""

    rung: float
    inert: tuple[tuple[str, str], ...]
    responsive: tuple[tuple[str, str], ...]

    @property
    def total(self) -> int:
        """What ``operating_point.ladder_census`` reports for this rung."""
        return len(self.inert) + len(self.responsive)

    @property
    def vacuous(self) -> bool:
        """No arm that reads the ladder admits this rung."""
        return not self.responsive

    def __str__(self) -> str:
        tag = "  <-- NO responsive support" if self.vacuous else ""
        return (f"lam={self.rung:<6g} {self.total:>3d} cells "
                f"= {len(self.responsive):>3d} responsive + {len(self.inert):>2d} inert{tag}")


def rung_support(rung: float, root: Path | None = None,
                 scene: str | Path = PROBE_SCENE) -> RungSupport:
    """Partition the cells admitting ``rung`` by arm responsiveness."""
    inert = set(inert_arms(scene))
    hit = [(s, c) for (s, c), adm in windows(root).items() if rung in adm]
    return RungSupport(
        rung=rung,
        inert=tuple(sorted(k for k in hit if k[1] in inert)),
        responsive=tuple(sorted(k for k in hit if k[1] not in inert)),
    )


def shipped_lam_support(root: Path | None = None,
                        scene: str | Path = PROBE_SCENE) -> RungSupport:
    """The bottleneck's own question, as one call."""
    return rung_support(SHIPPED_LAM, root, scene)


def report(root: Path | None = None, scene: str | Path = PROBE_SCENE) -> str:
    rows = ["lam response, per registered arm "
            f"(same cost vector, lam {PROBE_LAMS[0]:g} vs {PROBE_LAMS[1]:g}):", ""]
    rows += [f"  {r}" for r in responses(scene)]

    inert = inert_arms(scene)
    rows += ["", f"inert arms: {list(inert) or 'none'}", ""]

    ladder = sorted({r for c in cells(root) for r in c.ladder})
    rows.append("admissible-rung census, split by responsiveness:")
    for rung in ladder:
        rows.append(f"  {rung_support(rung, root, scene)}")

    sat = saturated_cells(root)
    sat_inert = [c for c in sat if c.controller in inert]
    rows += [
        "",
        f"saturated cells (window == ladder): {len(sat)}",
        f"  … of which on an inert arm:        {len(sat_inert)}",
        "",
        f"shipped lam = {SHIPPED_LAM:g}: {shipped_lam_support(root, scene)}",
    ]
    return "\n".join(rows)


if __name__ == "__main__":
    print(report())
