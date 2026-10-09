"""D-515: `progress_retreat_gain` has a floor between 30 and 100, then a plateau.

D-514 left `w_progress=10 + progress_retreat_gain=100` as a candidate tracking
default and asked for two things before promoting it: the scenes D-514 skipped,
and a gain sweep. Knee+shape band 0.30, seeds 0-15, yaml acceptance, measured
2026-10-09 10:00:

    scene              arm        pass   T med   clr min
    head_on            k=30       0/16   12.1    -0.08   (seed 7 collides)
    head_on            k=100      0/16   12.3     0.30
    head_on            k=300      0/16   12.4     0.30
    head_on            k=1000     0/16   12.2     0.30
    crossing           k=30..1000 16/16  17.8     0.30   (identical)
    cut_in             w0 / k100  0/16    --      0.30   (goal ball blocked, both)
    city_figure8_v0    w0 / k100  0/16    0.0     inf    (scene defect, both)

So the gain is not a dial past 100: k=100 through k=1000 are the same arm. Below
that the retreat comes back as a *collision*, not as a slow run. At k=30, seed 7
backs up less than at k=1 but still gets caught by the oncoming pedestrian.
k=300 is the promotion value because it sits in the middle of a decade-wide
plateau instead of on its lower edge.

Not promoted to the global default: D-027 keeps every knob inert at its default,
and head_on, cut_in and figure8_v0 fail on every arm, so the flip buys no pass.

Cost: 2 integrations.
"""
import pytest

from eval.mppi_sandbox import ab
from eval.mppi_sandbox.controllers.stock_mppi import MPPIParams
from eval.mppi_sandbox.scenario import load_scenario

HEAD_ON = "eval/scenarios/cafe_head_on_v0.yaml"
BAND = 0.30
SEED = 7


@pytest.fixture(scope="module")
def clearance():
    sc = load_scenario(HEAD_ON)
    p = MPPIParams(collision_margin=BAND, obs_barrier_band=BAND)
    return {k: ab.run_arm(sc, "stock_mppi", SEED, params=p, w_progress=10.0,
                          progress_retreat_gain=k).clearance
            for k in (30.0, 300.0)}


def test_gain_below_the_floor_collides(clearance):
    assert clearance[30.0] < 0.0                           # -0.077 m


def test_gain_on_the_plateau_holds_the_band(clearance):
    assert clearance[300.0] > BAND - 0.02
