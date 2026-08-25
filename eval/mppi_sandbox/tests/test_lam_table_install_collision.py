# SPDX-License-Identifier: BSD-3-Clause
"""Installing the regenerated 8-controller table raises `WeightCollision`, and
that blocker is not in D-457's price.

D-470 spent **33.1 min** regenerating `lam_windows.yaml` over all 8 controllers
and parked the result in `results/readings/` rather than installing it, because
D-457 had priced the install at *16 reds plus 8 cascading* — a test-shape
cascade, every one of which is a `2 -> 8` literal or a piece of prose. STATE
then wrote "the compute standing between here and 8/8 is now **zero**".

The compute is zero. The install is still blocked, for a reason that has
nothing to do with the controller count:

    WeightCollision: w=10 claimed by both eval/scenarios/lam_windows.yaml
                     and eval/scenarios/variants/lam_windows_w10.yaml

The regenerated table records `calibration_weight: 10` — correctly, it *was*
walked at `w_obs_soft = 10` — and `lam_window_index.TABLES` already holds a
`w = 10` entry from D-141. `build_index` raises on the duplicate, so this is a
**collection error**, not a failure: `test_lam_window_index.py` builds the index
at import time and takes the whole module down with it before a single
controller-count assertion is reached. A cycle that installs the table and runs
the cheap targeted subset sees an opaque traceback, not the cascade it budgeted
for.

Why the blocker was invisible to every instrument that ran
-----------------------------------------------------------

The shipped table's *defence* against being stamped is
`test_lam_window_keying.py::test_shipped_table_is_still_unkeyed`, whose
docstring says "Delete this test in the same commit that regenerates the
table." Read alone, that is an instruction to keep the header and drop one
test — which is exactly the move that collides. The two constraints live in
different modules and neither names the other, so the conflict is only
observable from a tree where the install has already happened.

This is the D-317 / D-344 / D-433 / D-455 / D-457 shape once more, and this
time the missing population is not a set of pin sites but a set of *rules*: the
cascade census enumerated the sites that assert the table's **shape** and was
silent about the one that asserts its **identity**.

What this test buys
--------------------

0.1 s instead of an install plus a targeted subset. It reads the parked reading
off disk and asserts the collision is real, so the next cycle to pick the
install starts from a named decision rather than a traceback. It deliberately
does **not** pick the resolution — see the three options in
`test_the_collision_has_three_resolutions_and_none_is_free`, none of which is
verifiable without a full suite.

Delete this file in the same commit that installs the table.
"""

from __future__ import annotations

import glob
import os

import pytest

from eval.mppi_sandbox import lam_window_index as lwi
from eval.mppi_sandbox import lam_window_key as lwk

#: The parked 8-controller regeneration (D-470). Globbed rather than named so
#: a re-run under a later timestamp is still found — the reading is additive.
READING_GLOB = "results/readings/*-lam-windows-8-controller.yaml"

SHIPPED = "eval/scenarios/lam_windows.yaml"
W10_VARIANT = "eval/scenarios/variants/lam_windows_w10.yaml"


def _reading() -> str:
    hits = sorted(glob.glob(READING_GLOB))
    if not hits:
        pytest.skip(f"no parked regeneration matching {READING_GLOB}")
    return hits[-1]


# --------------------------------------------------------------------------
# The reading is what D-470 says it is
# --------------------------------------------------------------------------

def test_the_parked_reading_is_the_eight_controller_table():
    """Guards the premise. If the reading ever stops being 72 cells over 8
    controllers, every claim below is about a different file and the failure
    should say so here rather than surface as a confusing collision."""
    cells, weight = lwk._rows(_reading())
    controllers = {c["controller"] for c in cells}
    assert len(cells) == 72, f"expected 72 cells, read {len(cells)}"
    assert len(controllers) == 8, f"expected 8 controllers, read {sorted(controllers)}"
    assert weight == 10, (
        f"the reading records calibration_weight={weight}; the collision this "
        f"file pins is specific to w=10")


# --------------------------------------------------------------------------
# The collision
# --------------------------------------------------------------------------

def test_w10_is_already_claimed_by_a_variant():
    """The other half of the collision, asserted independently so a failure
    names which side moved."""
    if not os.path.exists(W10_VARIANT):
        pytest.skip(f"{W10_VARIANT} not present")
    assert W10_VARIANT in lwi.TABLES, (
        f"{W10_VARIANT} left TABLES — if it was retired deliberately that is "
        f"resolution (b) below, and this file should be deleted with it")
    _, weight = lwk._rows(W10_VARIANT)
    assert weight == 10


def test_installing_the_reading_verbatim_raises_weight_collision():
    """The blocker itself, without touching `eval/scenarios/`.

    `build_index` takes an explicit path sequence, so the install can be
    *simulated* by substituting the reading for the shipped table in `TABLES`.
    No file is written and no test outside this module is perturbed.
    """
    if not os.path.exists(W10_VARIANT):
        pytest.skip(f"{W10_VARIANT} not present")
    as_installed = tuple(
        _reading() if p == SHIPPED else p for p in lwi.TABLES)
    with pytest.raises(lwi.WeightCollision) as exc:
        lwi.build_index(as_installed)
    assert "w=10" in str(exc.value)
    assert os.path.basename(W10_VARIANT) in str(exc.value)


def test_the_shipped_table_is_why_the_index_builds_today():
    """Non-vacuity for the test above: the index builds *now* only because the
    shipped table is unkeyed. Without this, a future refactor that stopped
    reading `calibration_weight` at all would leave the collision test passing
    for the wrong reason."""
    _, weight = lwk._rows(SHIPPED)
    assert weight is None, (
        f"{SHIPPED} records calibration_weight={weight} — the install already "
        f"happened; delete this file")
    lwi.build_index()  # must not raise


# --------------------------------------------------------------------------
# The decision this file refuses to make
# --------------------------------------------------------------------------

def test_the_collision_has_three_resolutions_and_none_is_free():
    """Executable documentation, and the reason this file stops here.

    (a) **Install unkeyed** — strip `calibration_weight:` from the parent on
        install. Smallest diff; the index is untouched and the cascade is
        exactly the `2 -> 8` shape D-457 priced. Cost: the 72 cells ship with
        no recorded provenance, which is the thing D-107 and
        `test_shipped_table_is_still_unkeyed` exist to prevent, and it makes
        that test pass by keeping the file in the state the test calls wrong.

    (b) **Retire the w10 variant from `TABLES`** — the parent at `w = 10` is a
        strict superset (72 cells vs 24, 8 controllers vs 2), so the variant is
        subsumed. Cost: `test_table_merge.py` reads the variant by path, and
        every `w = 10` resolution in `test_lam_window_index.py` re-routes to a
        file nobody has re-derived those windows from. Unverifiable without a
        full suite.

    (c) **Drop the parent from `TABLES`** — keep it keyed but outside the
        index, leaving the variants as the sole weight-routed surface. Cost:
        the index's `unkeyed` bucket loses its only member, and
        `TableIndex.__str__` / the `NO_TABLE_AT_WEIGHT` narrative in the module
        docstring both describe a shipped-but-unkeyed table that would no
        longer exist.

    The assertion is that the three are still distinct — i.e. nobody has
    quietly performed one of them and left the other two as dead prose.
    """
    assert SHIPPED in lwi.TABLES, "resolution (c) was taken; update this file"
    assert W10_VARIANT in lwi.TABLES, "resolution (b) was taken; update this file"
    _, weight = lwk._rows(SHIPPED)
    assert weight is None, "resolution (a) was taken; delete this file"
