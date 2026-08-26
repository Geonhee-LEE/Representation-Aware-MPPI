# SPDX-License-Identifier: BSD-3-Clause
"""Q-116 (a): the calibration table records the weight it was measured at.

`lam_window_key._rows` has read a top-level `calibration_weight:` key since
D-134, and until D-138 **nothing wrote one**. A reader-only field is an
untested contract in the most literal sense: had `calibrate_lam` emitted
`calibrated_at:`, every lookup would still have graded `UNKEYED` and no test
would have noticed, because the only table either side ever saw was the shipped
one that has no such key at all.

So the load-bearing test here is the *round trip* — `to_yaml` writes, `lookup`
reads, and the two agree on both the spelling and the value. Everything else in
this file guards the ways the weight could get separated from the window it
describes.

No closed-loop sim: the ladder-walking half is covered by asserting the
`MPPIParams` handed to `seed_sweep`, which is the whole of what threading
`w_obs_soft` means. A real matrix pass is ~500 runs and belongs to the script,
not to CI (`test_lam_calibration_table`'s cost split).
"""

from __future__ import annotations

import dataclasses
import os

import pytest

from eval.mppi_sandbox import ab
from eval.mppi_sandbox import calibrate_lam as cal
from eval.mppi_sandbox import lam_window_key as lwk

SHIPPED = "eval/scenarios/lam_windows.yaml"


def _cell(scenario="cafe_head_on_v0.yaml", controller="stock_mppi",
          admissible=(0.2, 0.4, 0.8), weight=None) -> cal.SceneCalibration:
    """A cell with no probes — `to_yaml` reads `admissible` and the weight, and
    a probe-less cell keeps these tests off the simulator."""
    kwargs = {} if weight is None else {"w_obs_soft": weight}
    return cal.SceneCalibration(scenario=scenario, controller=controller,
                                admissible=tuple(admissible), **kwargs)


# --------------------------------------------------------------------------
# The round trip: writer and reader agree.
# --------------------------------------------------------------------------

@pytest.mark.parametrize("weight", [10.0, 100.0, 150.0])
def test_written_table_reads_back_on_key_at_the_weight_it_was_written_at(
        tmp_path, weight):
    """The contract that had no test. A table written at `w` must grade
    `ON_KEY` at `w` — otherwise the guard refuses its own generator's output
    and `lookup` can never return a usable window."""
    path = tmp_path / "windows.yaml"
    path.write_text(cal.to_yaml([_cell(weight=weight)], cal.DEFAULT_LADDER))

    look = lwk.lookup(str(path), "cafe_head_on_v0.yaml", "stock_mppi", weight)

    assert look.verdict == lwk.ON_KEY, str(look)
    assert look.measured_at == weight
    assert look.usable == (0.2, 0.4, 0.8)


def test_written_table_reads_back_off_key_at_any_other_weight(tmp_path):
    """The refusal has to survive the round trip too, or re-keying would buy a
    table that is trusted everywhere instead of at one weight."""
    path = tmp_path / "windows.yaml"
    path.write_text(cal.to_yaml([_cell(weight=100.0)], cal.DEFAULT_LADDER))

    look = lwk.lookup(str(path), "cafe_head_on_v0.yaml", "stock_mppi", 150.0)

    assert look.verdict == lwk.OFF_KEY, str(look)
    assert look.usable is None
    assert look.measured_at == 100.0        # the row still reports its own key


def test_default_weight_run_records_the_default_not_nothing(tmp_path):
    """A run that names no weight still measured at *some* weight. Omitting the
    field would leave `UNKEYED` — indistinguishable from the pre-D-138 table —
    for a run whose provenance is perfectly well known."""
    path = tmp_path / "windows.yaml"
    path.write_text(cal.to_yaml([_cell()], cal.DEFAULT_LADDER))

    look = lwk.lookup(str(path), "cafe_head_on_v0.yaml", "stock_mppi",
                      cal.default_weight())
    assert look.verdict == lwk.ON_KEY, str(look)
    assert look.measured_at == cal.default_weight()


def test_default_weight_tracks_the_controller_not_a_literal():
    """`default_weight()` and `lam_window_key.CALIBRATION_WEIGHT` describe the
    same number today; the point of deriving one is that it follows
    `MPPIParams` if the controller default ever moves."""
    from eval.mppi_sandbox.controllers.stock_mppi import MPPIParams

    assert cal.default_weight() == MPPIParams().w_obs_soft
    assert cal.default_weight() == lwk.CALIBRATION_WEIGHT


# --------------------------------------------------------------------------
# The weight cannot get separated from the window.
# --------------------------------------------------------------------------

def test_to_yaml_refuses_cells_measured_at_different_weights():
    """One top-level key cannot describe two weights. Writing the first cell's
    weight would hand every other row a provenance nobody measured (D-107)."""
    cells = [_cell(weight=10.0),
             _cell(scenario="cafe_obstacle_crossing_v0.yaml", weight=150.0)]

    with pytest.raises(ValueError, match="span 2 obstacle weights"):
        cal.to_yaml(cells, cal.DEFAULT_LADDER)


def test_refine_refuses_to_merge_rungs_from_another_weight():
    """Refinement re-measures extra rungs and merges them into the cell. At a
    different weight that silently puts two weights behind one window — the
    exact confound `calibration_weight` exists to rule out."""
    base = _cell(admissible=(), weight=10.0)

    with pytest.raises(ValueError, match="two.*weights"):
        cal.refine(base, "eval/scenarios/cafe_head_on_v0.yaml",
                   seeds=range(1), w_obs_soft=150.0)


def test_calibration_carries_its_weight_as_a_field():
    """Carried on the cell, not passed beside it: `to_yaml` reads the object,
    so there is no call path that emits a weight the run did not use."""
    assert "w_obs_soft" in {f.name for f in
                            dataclasses.fields(cal.SceneCalibration)}
    assert _cell(weight=150.0).w_obs_soft == 150.0


# --------------------------------------------------------------------------
# The ladder actually walks at the requested weight.
# --------------------------------------------------------------------------

def test_lam_ladder_threads_the_weight_into_mppi_params(monkeypatch):
    """`lam_ladder` owns the `params=` slot, so `w_obs_soft` could not be
    reached through `arm_kwargs` — that is why the table was stuck at one
    weight. Asserted on the params object rather than on a sim outcome: the
    claim is about plumbing, and a closed-loop run would price it at minutes.
    """
    seen = []

    def fake_sweep(scenario, controller, seeds, params=None, **kw):
        seen.append(params)
        return []

    monkeypatch.setattr(ab, "seed_sweep", fake_sweep)
    monkeypatch.setattr(ab, "summarize", lambda runs: _StubStats())

    ab.lam_ladder(object(), "stock_mppi", [0.4, 0.8], seeds=range(2),
                  w_obs_soft=150.0)

    assert [p.lam for p in seen] == [0.4, 0.8]
    assert {p.w_obs_soft for p in seen} == {150.0}


def test_lam_ladder_without_a_weight_keeps_the_controller_default(monkeypatch):
    seen = []

    def fake_sweep(scenario, controller, seeds, params=None, **kw):
        seen.append(params)
        return []

    monkeypatch.setattr(ab, "seed_sweep", fake_sweep)
    monkeypatch.setattr(ab, "summarize", lambda runs: _StubStats())

    ab.lam_ladder(object(), "stock_mppi", [0.4], seeds=range(2))

    assert seen[0].w_obs_soft == cal.default_weight()


class _StubStats:
    """Minimal stand-in for `ab.summarize`'s result — `lam_ladder` reads a few
    scalars off it and this file never asserts on them."""
    median_ess = float("nan")
    n_in_band = 0
    all_reached = False
    reached = 0
    n = 0


# --------------------------------------------------------------------------
# The shipped table is not hand-stamped.
# --------------------------------------------------------------------------

def test_the_shipped_table_is_keyed_by_measurement_and_not_by_hand():
    """The successor to `test_shipped_table_is_still_unkeyed`, which said
    "delete this test in the same commit that regenerates the table" and whose
    deletion is D-477.

    That test guarded the *cheap wrong move*: stamping a `calibration_weight:`
    onto the shipped table without re-walking it, which would hand ~24 resolved
    cells a provenance nobody derived (D-107). D-470 re-walked it for real —
    33.1 min, 8 controllers, 72 cells — so the header is now earned and the old
    assertion is simply false.

    **Deleting it outright would have been the mistake.** The property D-107
    cares about is not "unkeyed" but "keyed only by measurement", and that
    property survives the regeneration. What stands in for the header check is
    the table's own shape: a hand-stamp is a one-line edit to a file that
    otherwise still holds the pre-regeneration 3-controller matrix, so
    asserting the matrix *widened* is what a hand-stamp cannot fake.
    """
    if not os.path.exists(SHIPPED):
        pytest.skip(f"{SHIPPED} not generated")
    cells, weight = lwk._rows(SHIPPED)
    assert weight == 10, (
        f"{SHIPPED} records calibration_weight={weight}, expected 10 — the "
        f"D-470 regeneration was walked at w_obs_soft=10")
    controllers = {c["controller"] for c in cells}
    assert len(controllers) == 8, (
        f"{SHIPPED} is keyed but carries {len(controllers)} controller(s): "
        f"{sorted(controllers)}. A keyed header over a narrow matrix is the "
        f"hand-stamp D-107 refuses; re-run `calibrate_lam --w-obs-soft 10`")
    assert len(cells) == 72, f"expected 72 cells, read {len(cells)}"
