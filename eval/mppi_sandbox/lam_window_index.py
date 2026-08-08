# SPDX-License-Identifier: BSD-3-Clause
"""Which calibration table should a caller at `w_obs_soft = W` open?

`lam_window_key.lookup` answers "is *this* table on key for my weight" — it
takes a path and grades it. That was the right first half (D-134, guard first,
re-key later), and after D-141/D-142 the repo has the second half's raw
material: two generated tables, each recording the weight it was walked at
(`lam_windows_w10.yaml`, `lam_windows_w75.yaml`) and a shipped
`lam_windows.yaml` that records nothing. Nothing reads any of them. Every
`lookup` call site in the repo is a test.

That is the gap this module closes, and it is not a convenience wrapper. With
one table per weight, *the caller has to already know which file corresponds to
its weight* — and a caller that knows that does not need the guard, while a
caller that does not know it will open the wrong file and get a fully-`ON_KEY`
answer about somebody else's operating point. The guard is only load-bearing
once the file choice is made **from** the weight rather than beside it.

Why the refusal changes shape, and why that is the point
--------------------------------------------------------

Resolving through the index makes two of `lam_window_key`'s four refusals
structurally unreachable:

  * `OFF_KEY` cannot occur, because the index only ever hands `lookup` a table
    whose recorded weight already equals the caller's.
  * `UNKEYED` cannot occur, because a table with no `calibration_weight:` is
    not in the index at all.

Neither is softened — they are **converted** into :data:`NO_TABLE_AT_WEIGHT`,
which is the same refusal stated as an action. `OFF_KEY` tells a caller that the
file it happened to open is wrong; `NO_TABLE_AT_WEIGHT` tells it that no file is
right *and names the weights that are*, which is the difference between "your
number is untrustworthy" and "measure at 100, or run at 10 or 75". D-044 booked
what becomes of a check nobody can act on.

The excluded tables are named, not dropped
-------------------------------------------

An unkeyed table is excluded from the index, and :attr:`TableIndex.unkeyed`
lists it by path. Silently skipping it would make the shipped
`lam_windows.yaml`'s non-participation invisible — and that file is the one
~24 cells of the project's history were read from, so its absence from the
index is a *finding*, not an implementation detail. It stays unkeyed for
D-107's reason (keying it means re-running the matrix, not editing a header),
and D-141 has already shown the `w = 10` variant reproduces it exactly, so a
caller at `w = 10` loses nothing by being routed to the variant instead.

What the index deliberately does not do
----------------------------------------

  * **No nearest-weight fallback, no interpolation.** `lam_window_key` refuses
    these and D-142 is why: between `w = 10` and `w = 75`, 6 of 14 arm-cells
    move, and they do not move in one direction — `convoy`/risk moves *up*
    (`[0.2, 0.4] → [0.8]`), `crossing`/stock moves to an off-ladder bisect rung
    `[4.5255]`, `crossing`/risk closes entirely. There is no correction factor
    to apply, so any fallback would be a model of that motion wearing a
    lookup's clothes.
  * **No stored index.** :func:`build_index` derives weight → path by reading
    each file's own `calibration_weight:`. A checked-in mapping would be a
    second statement of a fact the files already carry, and D-047 named which
    of the two drifts.
  * **No preference between colliding tables.** Two tables keyed at the same
    weight is a repo-state error, not a tie to break — see
    :data:`WEIGHT_COLLISION`.

Q-119's schema fork, answered
------------------------------

Q-119 left open whether keyed calibration should be *file-per-weight* or a
single *weight-indexed* file. The answer this module takes is **both, at
different layers**: file-per-weight on disk, because each file is the artifact
of one ~1024-run measurement and provenance is per-run — merging two runs into
one file would put two measurements behind one mtime and one git blob. Weight-
indexed in the API, because that is the key callers actually hold. The index is
derived at read time, so adding a third weight is `calibrate_lam --w-obs-soft
100 --out …_w100.yaml` plus one entry in :data:`TABLES`, with no migration.

Typical use::

    res = resolve("cafe_obstacle_crossing_v0.yaml", "risk_mppi", 75.0)
    if res.usable is None:
        raise AssertionError(str(res))   # names the weights that would work
    for lam in res.usable:
        ...
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Mapping, Sequence

from eval.mppi_sandbox.lam_window_key import (
    EMPTY_WINDOW,
    NO_CELL,
    REFUSALS,
    WindowLookup,
    _rows,
    lookup,
)

#: Every calibration table the repo ships, keyed or not. The shipped
#: `lam_windows.yaml` is listed **on purpose** even though it can never be
#: resolved through: :attr:`TableIndex.unkeyed` reports it, and a table that is
#: merely omitted from this tuple is indistinguishable from one that does not
#: exist.
TABLES: tuple[str, ...] = (
    "eval/scenarios/lam_windows.yaml",
    "eval/scenarios/variants/lam_windows_w10.yaml",
    "eval/scenarios/variants/lam_windows_w75.yaml",
)

#: No table in the index was calibrated at the caller's weight. The window is
#: not "unknown to some tolerance" — it is unmeasured, and the resolution says
#: which weights *have* been measured so the caller can either move its
#: operating point onto one or schedule the calibration run.
NO_TABLE_AT_WEIGHT = "NO_TABLE_AT_WEIGHT"

#: Refusals reachable through :func:`resolve`. `OFF_KEY` and `UNKEYED` are
#: absent by construction (see the module docstring) — asserting that is what
#: :func:`reachable_verdicts` is for.
INDEX_REFUSALS = frozenset({NO_TABLE_AT_WEIGHT, NO_CELL, EMPTY_WINDOW})


class WeightCollision(ValueError):
    """Two tables claim the same `calibration_weight:`.

    Not resolved by preferring one — a duplicate weight means either a table
    was regenerated without replacing its predecessor, or two different
    measurements are both claiming to describe one operating point. Picking
    either silently would hand a caller a window whose provenance depends on
    tuple order.
    """


@dataclass(frozen=True)
class TableIndex:
    """weight → table path, plus the tables that could not be indexed."""

    by_weight: Mapping[float, str]
    #: Tables carrying no `calibration_weight:`, in :data:`TABLES` order.
    unkeyed: tuple[str, ...]

    @property
    def weights(self) -> tuple[float, ...]:
        """Calibrated weights, ascending — the domain of :func:`resolve`."""
        return tuple(sorted(self.by_weight))

    def __str__(self) -> str:
        keyed = ", ".join(f"{w:g}→{os.path.basename(p)}"
                          for w, p in sorted(self.by_weight.items()))
        return (f"TableIndex[{keyed or 'empty'}]"
                f" unkeyed={[os.path.basename(p) for p in self.unkeyed]}")


def build_index(paths: Sequence[str] = TABLES) -> TableIndex:
    """Read each table's own `calibration_weight:` and index by it.

    Raises :class:`WeightCollision` when two tables claim one weight.
    """
    by_weight: dict[float, str] = {}
    unkeyed: list[str] = []
    for path in paths:
        _, weight = _rows(path)
        if weight is None:
            unkeyed.append(path)
            continue
        if weight in by_weight:
            raise WeightCollision(
                f"w={weight:g} claimed by both {by_weight[weight]} and {path}")
        by_weight[weight] = path
    return TableIndex(by_weight=by_weight, unkeyed=tuple(unkeyed))


@dataclass(frozen=True)
class Resolution:
    """One `(scenario, controller, weight)` resolved against the whole index.

    Wraps the :class:`WindowLookup` the chosen table produced, or carries
    `inner=None` when no table was chosen at all. `usable` is `None` under
    every refusal, matching `lam_window_key`'s contract so a caller can move
    between the two without re-learning which attribute lies.
    """

    scenario: str
    controller: str
    weight: float
    #: The table consulted; `None` under :data:`NO_TABLE_AT_WEIGHT`.
    table: str | None
    #: The per-table lookup, `None` when no table was consulted.
    inner: WindowLookup | None
    #: Weights the index *does* carry, ascending. Present on every resolution,
    #: not just the refusing ones, because a caller logging a successful
    #: resolution still wants the domain it got lucky inside.
    available: tuple[float, ...]

    @property
    def verdict(self) -> str:
        return NO_TABLE_AT_WEIGHT if self.inner is None else self.inner.verdict

    @property
    def admissible(self) -> tuple[float, ...]:
        return () if self.inner is None else self.inner.admissible

    @property
    def usable(self) -> tuple[float, ...] | None:
        return None if self.verdict in REFUSALS | INDEX_REFUSALS \
            else self.admissible

    def __str__(self) -> str:
        have = ", ".join(f"{w:g}" for w in self.available) or "none"
        where = "no table" if self.table is None else os.path.basename(self.table)
        return (f"{self.scenario} {self.controller} w={self.weight:g} :: "
                f"{self.verdict} [window={list(self.admissible)} "
                f"table={where} calibrated_at={have}]")


def resolve(scenario: str, controller: str, weight: float,
            index: TableIndex | None = None) -> Resolution:
    """Pick the table calibrated at `weight` and look the cell up in it.

    The weight is matched exactly. That is not strictness for its own sake:
    D-142 measured 6 of 14 arm-cells moving between `w = 10` and `w = 75`, in
    both directions and by no common factor, so there is no tolerance within
    which two weights describe one window.
    """
    index = build_index() if index is None else index
    weight = float(weight)
    available = index.weights
    path = index.by_weight.get(weight)
    if path is None:
        return Resolution(scenario=os.path.basename(scenario),
                          controller=controller, weight=weight, table=None,
                          inner=None, available=available)
    inner = lookup(path, scenario, controller, weight)
    return Resolution(scenario=inner.scenario, controller=controller,
                      weight=weight, table=path, inner=inner,
                      available=available)


def coverage(index: TableIndex | None = None,
             ) -> dict[tuple[str, str], tuple[float, ...]]:
    """`(scenario, controller)` → the weights where that cell has a **usable**
    window.

    This is the whole point of indexing, stated as data: it is the project's
    first answer to "which operating points does the calibration actually
    cover", and the honest answer is patchy. A cell missing a weight here is
    not a bug — `crossing`/`risk_mppi` has a window at `w = 10` and none at
    `w = 75` (D-142), and `cut_in`'s cells have one at neither (Q-035) — but
    until now that patchiness was spread across two files nobody joined.
    """
    index = build_index() if index is None else index
    out: dict[tuple[str, str], list[float]] = {}
    for weight, path in sorted(index.by_weight.items()):
        cells, _ = _rows(path)
        for cell in cells:
            key = (os.path.basename(str(cell.get("scenario", ""))),
                   str(cell.get("controller", "")))
            out.setdefault(key, [])
            if resolve(key[0], key[1], weight, index).usable:
                out[key].append(weight)
    return {k: tuple(v) for k, v in sorted(out.items())}


def reachable_verdicts(index: TableIndex | None = None) -> frozenset[str]:
    """The verdicts :func:`resolve` can actually return over this index.

    Exists so the docstring's structural claim is *checked* rather than
    asserted in prose: routing through the index removes `OFF_KEY` and
    `UNKEYED` from the reachable set, and a future change that lets either back
    in — say, a fallback to the nearest weight, or indexing an unkeyed table
    under an assumed 10.0 — breaks a test instead of quietly widening what a
    caller can be handed.
    """
    index = build_index() if index is None else index
    absent = max(index.weights, default=0.0) + 1.0
    seen = {resolve("cafe_head_on_v0.yaml", "stock_mppi", absent, index).verdict}
    for weight, path in index.by_weight.items():
        cells, _ = _rows(path)
        for cell in cells:
            res = resolve(str(cell.get("scenario", "")),
                          str(cell.get("controller", "")), weight, index)
            seen.add(res.verdict)
        seen.add(resolve("nonexistent_scene.yaml", "stock_mppi",
                         weight, index).verdict)
    return frozenset(seen)
