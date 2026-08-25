# SPDX-License-Identifier: BSD-3-Clause
"""The calibration sweep must *offer* every registry controller (D-469).

`baseline_matrix.admission_gap` (D-467) names the controllers the recorded
table cannot admit anywhere, and on 2026-08-25 it named six of eight. That
reading is about the **table**; these tests are about the **offer set** that
feeds it, which is the upstream half D-467 could not see.

The distinction is the whole point. A controller with an empty admissible
window has been measured and found unplaceable — `NO_ADMISSIBLE_LAM`, a
verdict. A controller that was never handed to the sweep has no verdict at all,
and `lam_for_cell` reports it as `LAM_UNCALIBRATED`, which reads like a
property of the controller and is in fact a property of a literal someone typed
in August. Measured this cycle: all six of the missing controllers return an
admissible `(0.2, 0.4)` on `cafe_straight_v0`, so every one of the six was the
second thing wearing the first thing's clothes.
"""

from __future__ import annotations

import inspect

from ..calibrate_lam import default_controllers
from ..controllers import REGISTRY


def test_offer_set_is_the_whole_registry():
    """Nothing in the registry is un-offered.

    This is the assertion the typed literal could not make. `DEFAULT_CONTROLLERS`
    was written 2026-08-02 with two names; five of the six controllers it went
    on to miss were added *after* that date, so the gap opened silently on each
    arrival with no test anywhere going red.
    """
    assert set(default_controllers()) == set(REGISTRY)


def test_offer_set_is_derived_and_not_a_typed_copy():
    """D-047: the offer set must read the registry, not restate it.

    A `set(...) == set(...)` equality alone is satisfiable by re-typing the
    eight names, which would pass today and re-stale on the ninth controller —
    exactly how the last one survived four additions. So this pins the
    *mechanism*: the function body has to reach `REGISTRY`, and must not carry
    a literal tuple/list/set of controller names.
    """
    src = inspect.getsource(default_controllers)
    body = src.split('"""')[-1]           # drop the docstring's prose
    assert "REGISTRY" in body, "offer set no longer derives from the registry"
    for name in REGISTRY:
        assert f'"{name}"' not in body and f"'{name}'" not in body, (
            f"{name!r} is typed into the offer set — that is the D-047 shape "
            "this function exists to retire"
        )


def test_offer_set_is_sorted_and_deduplicated():
    """Cell ordering in the emitted table follows this sequence, so a set's
    non-deterministic iteration order would make two identical sweeps produce
    two different files and defeat `test_lam_window_regeneration`."""
    offered = default_controllers()
    assert list(offered) == sorted(set(offered))


def test_calibrate_matrix_defaults_to_the_offer_set():
    """The default has to flow to the caller that actually walks the ladder.

    `calibrate_matrix`'s signature default is `None` (a function cannot be a
    default argument without freezing at import time), so the resolution
    happens in the body — and a refactor that drops that line would restore the
    old behaviour with every test above still green.
    """
    from ..calibrate_lam import calibrate_matrix

    sig = inspect.signature(calibrate_matrix)
    assert sig.parameters["controllers"].default is None
    assert "default_controllers()" in inspect.getsource(calibrate_matrix)
