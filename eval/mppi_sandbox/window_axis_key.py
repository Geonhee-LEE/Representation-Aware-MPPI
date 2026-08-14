# SPDX-License-Identifier: BSD-3-Clause
"""A λ window is keyed by **one** cost-field axis. Which axis is the caller moving?

`lam_window_key` asks "was this window measured at the weight you are about to
run at", and answers it against `calibration_weight:` — a scalar, and a scalar
of `w_obs_soft`. That is the right question for a caller that varies the barrier
weight. This branch's ladder does not: `calibrated_ladder` walks **`w_voo`**,
the epistemic attract channel, with `w_obs_soft` sitting at its `MPPIParams`
default the whole way.

So the two guards' verdicts come apart, and the direction they come apart in is
the dangerous one.

Why keying the table would make the answer *worse*
--------------------------------------------------

The shipped `lam_windows.yaml` grades `UNKEYED`, and Q-154 asked what happens
when that is cleared — the standing TODO being to emit `calibration_weight:` so
lookups grade `ON_KEY`/`OFF_KEY` instead. Follow that through on the cell the
bottleneck actually reads. `calibrated_ladder.window_is_keyed` resolves
`(cafe_freezing_v0, risk_mppi)` at `calibrate_lam.default_weight()` — i.e. at
`w_obs_soft = 10`. The keyed regeneration
(`eval/scenarios/variants/lam_windows_w10.yaml`, D-141) records
`calibration_weight: 10` and reproduces all 16 shipped cells field-for-field.
Point the lookup at it and `measured_at == weight`, so the verdict is
**`ON_KEY`** and `usable` stops being `None`.

That clearance would be false. The window was measured with `w_voo = 0` — the
attract channel off — and this ladder runs it at `5`, `20`, `50`, `200`. The
temperature divides a cost spread; changing which terms are *in* that spread is
not a smaller perturbation than changing one term's weight, and `w_voo = 200`
is the rung D-027 measured at `6.19x` the baseline spread. `ON_KEY` would
certify a window against an operating point whose cost field the calibration
never contained, and it would do it while looking maximally rigorous.

The fact is not new. `calibrated_ladder`'s preamble has said it in prose since
D-270: *"It was in fact measured at `MPPIParams.w_obs_soft` with `w_voo = 0`,
and this ladder walks `w_voo` up to `200` — a different cost field."* What was
missing is that nothing **read** that sentence. The caveat rode along beside a
grade that did not encode it, so the day the grade improved the sentence would
have been quietly demoted to stale prose — D-047's shape exactly, and the
sentence would have been the copy that drifts.

So the answer to Q-154 does not depend on the key
-------------------------------------------------

Q-154 asked whether the window's `0.8` ceiling is binding on this ladder, and
made `calibration-weight-in-lam-windows` a prerequisite on the reasoning that an
`UNKEYED` window's ceiling cannot be judged. This module withdraws the
prerequisite. The ceiling is **off-axis** for a `w_voo` ladder in both key
states: `UNKEYED` refuses because nothing is recorded, `ON_KEY` would clear on
an axis the caller is not moving, and neither is a statement about `w_voo`. No
amount of keying the `w_obs_soft` axis produces one — that needs a walk with
`w_voo` held at the ladder's value, which nobody has paid for.

That makes D-272's `WINDOW_EXHAUSTED` **narrower** than it reads, and this is
the useful half. "8/8 is unreachable inside the calibrated window" is a claim
about a window that does not key the cost field the ladder runs in, so it bounds
the rungs anyone has tried, not the rungs that exist.

What this deliberately does not do
----------------------------------

  * **Extrapolate across axes.** There is no rule here for how a window moves
    when `w_voo` rises, because nobody has measured one. `OFF_AXIS` is a
    refusal, in the same shape as `OFF_KEY`, and for the same reason: the
    lookup cannot know it is on a benign cell until somebody pays to find out.
  * **Re-grade `lam_window_key`.** That guard's answer about `w_obs_soft` is
    correct and stays as it is. This composes with it — :class:`AxisLookup`
    carries both verdicts — rather than replacing a working check with a wider
    one that would then own two failure modes.
  * **Declare `w_voo` special.** The axis set is read off the walk
    (:func:`calibrated_axes`), not typed here, so an axis the calibrator learns
    to vary stops being off-axis without anybody editing this file.
"""

from __future__ import annotations

import inspect
from dataclasses import dataclass
from typing import Mapping

from . import lam_window_key as lwk

#: The caller moves only axes the walk varied, and the keyed axis agrees. The
#: window is usable, with no more caveat than `ON_KEY` already carries.
ON_AXIS = "ON_AXIS"

#: The caller sets a non-default value on a cost-field axis the calibration
#: **never varied**. Refuses regardless of what the keyed axis says — this is
#: the verdict that survives the table being keyed.
OFF_AXIS = "OFF_AXIS"

#: Refusing verdicts of this module. `lam_window_key.REFUSALS` still applies on
#: its own axis; :class:`AxisLookup` refuses under the union.
REFUSALS = frozenset({OFF_AXIS})


def calibrated_axes() -> tuple[str, ...]:
    """The cost-field axes a calibration walk can vary, read off the walk.

    `ab.lam_ladder` is the one entry point every table in this repo was
    generated through, and its cost-field parameters are exactly the axes a
    generated window can be keyed on. Reading them by signature rather than
    listing them here is what keeps this module from becoming the second
    statement that goes stale (D-047): the day someone threads `w_voo` down to
    `MPPIParams` the way D-138 threaded `w_obs_soft`, this set grows on its own
    and the cells that were off-axis stop being so.

    `lam` is excluded because it is the ladder's *independent variable*, not a
    cost-field axis the window is conditioned on.
    """
    from . import ab

    params = inspect.signature(ab.lam_ladder).parameters
    skip = {"scenario", "controller", "lams", "seeds", "arm_kwargs"}
    return tuple(n for n, p in params.items()
                 if n not in skip
                 and p.kind is not inspect.Parameter.VAR_KEYWORD)


def axis_default(axis: str) -> float:
    """The value an axis holds when a walk does not name it — i.e. the value it
    was at while every recorded window was measured.

    Derived from `MPPIParams` for the same no-second-statement reason as
    `calibrate_lam.default_weight`, which is this function at one axis. Axes
    that are not `MPPIParams` fields (the epistemic channels are `run_arm`
    kwargs, not params) default to `0.0` — off, which is what "the calibration
    did not have this term" means.
    """
    from .controllers.stock_mppi import MPPIParams

    return float(getattr(MPPIParams(), axis, 0.0))


@dataclass(frozen=True)
class AxisLookup:
    """One window resolved against the whole cost field a caller will run in.

    Composes `lam_window_key.WindowLookup` rather than re-deriving it: the two
    guards answer about different axes and must not be able to disagree about
    the axis they share.
    """

    key: lwk.WindowLookup
    #: The caller's cost field: axis -> value it will run at.
    cost_field: Mapping[str, float]
    #: Axes the walk could vary, at the time of the lookup.
    axes: tuple[str, ...]

    @property
    def off_axis(self) -> tuple[str, ...]:
        """Axes the caller moves off default that the walk never varied."""
        return tuple(sorted(
            a for a, v in self.cost_field.items()
            if a not in self.axes and float(v) != axis_default(a)))

    @property
    def verdict(self) -> str:
        """`OFF_AXIS` wins over every `lam_window_key` verdict it can co-occur
        with, because it is the one a better-keyed table does not clear."""
        return OFF_AXIS if self.off_axis else ON_AXIS

    @property
    def usable(self) -> tuple[float, ...] | None:
        """The window, or `None` under **either** guard's refusal."""
        if self.verdict in REFUSALS:
            return None
        return self.key.usable

    def __str__(self) -> str:
        off = ",".join(self.off_axis) or "-"
        return (f"{self.key} :: {self.verdict} "
                f"[off_axis={off} axes={list(self.axes)}]")


def lookup(path: str, scenario: str, controller: str,
           cost_field: Mapping[str, float]) -> AxisLookup:
    """Resolve a window against a caller's full cost field.

    `cost_field` names every weight the caller will run at, not just the
    barrier one — that is the whole difference from `lam_window_key.lookup`,
    which takes a scalar and therefore cannot be handed the information needed
    to notice an off-axis run.
    """
    axes = calibrated_axes()
    keyed_axis = axes[0] if axes else "w_obs_soft"
    return AxisLookup(
        key=lwk.lookup(path, scenario, controller,
                       float(cost_field.get(keyed_axis,
                                            axis_default(keyed_axis)))),
        cost_field=dict(cost_field), axes=axes)


#: The cost field `calibrated_ladder`'s operating point actually runs in:
#: D-270/D-271's `(lam = 0.8, w_voo = 5)` cell, with the barrier weight left at
#: the `MPPIParams` default the whole ladder through. Recorded here so the
#: Q-154 answer below is a lookup and not a sentence.
LADDER_FIELD: dict[str, float] = {"w_obs_soft": 10.0, "w_voo": 5.0}

#: The keyed regeneration of the shipped matrix (D-141). Named so the Q-154
#: answer can be taken against the *best available* table rather than against
#: the unkeyed one — the point being that it does not help.
KEYED_TABLE = "eval/scenarios/variants/lam_windows_w10.yaml"


def q154(path: str = KEYED_TABLE) -> AxisLookup:
    """Is the window's `0.8` ceiling binding on this branch's `w_voo` ladder?

    Taken against the **keyed** table by default, which is the load-bearing
    choice: answering against the unkeyed shipped file would leave the reader
    unable to tell an off-axis refusal from a missing-key one, and the whole
    finding is that clearing the key does not clear this.
    """
    from .calibrated_ladder import WINDOW_KEY

    return lookup(path, WINDOW_KEY[0], WINDOW_KEY[1], LADDER_FIELD)
