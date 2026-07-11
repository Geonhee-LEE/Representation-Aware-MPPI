# SPDX-License-Identifier: BSD-3-Clause
"""D-012 contract tests for the GT BEV producer."""

import numpy as np

from eval.mppi_sandbox.obstacles import CircleObstacle
from eval.mppi_sandbox.representations import (
    N_CHANNELS,
    GTBevProducer,
    RiskChannel,
)


def _producer(obstacles):
    return GTBevProducer(obstacles, grid_size=64, resolution=0.125,
                         sensing_range=5.0)


ROBOT = np.array([0.0, 0.0])


class TestStackContract:
    def test_channel_order_is_d012_canonical(self):
        assert [c.value for c in RiskChannel] == [0, 1, 2, 3, 4]
        assert RiskChannel.STATIC == 0
        assert RiskChannel.DYNAMIC == 1
        assert RiskChannel.TRAVERSABILITY == 2
        assert RiskChannel.EPISTEMIC == 3
        assert RiskChannel.ALEATORIC == 4

    def test_shapes_dtypes_and_no_nan(self):
        bev = _producer([CircleObstacle(1.0, 0.0)]).render(ROBOT, 0.0)
        assert bev.stack.shape == (N_CHANNELS, 64, 64)
        assert bev.stack.dtype == np.float32
        assert bev.mask.shape == (N_CHANNELS, 64, 64)
        assert bev.mask.dtype == bool
        assert not np.isnan(bev.stack).any()   # D-012: no NaN sentinel

    def test_aleatoric_is_all_unobserved_row(self):
        bev = _producer([CircleObstacle(1.0, 0.0)]).render(ROBOT, 0.0)
        assert not bev.mask[RiskChannel.ALEATORIC].any()
        assert (bev.stack[RiskChannel.ALEATORIC] == 0.0).all()


class TestEpistemic:
    def test_occlusion_shadow_has_higher_sigma_than_visible(self):
        ob = CircleObstacle(2.0, 0.0, radius=0.3)
        bev = _producer([ob]).render(ROBOT, 0.0)
        behind = bev.sample(RiskChannel.EPISTEMIC, np.array([[3.0, 0.0]]))
        beside = bev.sample(RiskChannel.EPISTEMIC, np.array([[3.0, 2.0]]))
        assert behind[0] == 1.0, "cell in shadow must be fully uncertain"
        assert beside[0] == 0.0, "visible cell at same range must be certain"

    def test_beyond_sensing_range_is_uncertain(self):
        producer = GTBevProducer([], grid_size=64, resolution=0.125,
                                 sensing_range=2.0)
        bev = producer.render(ROBOT, 0.0)
        far = bev.sample(RiskChannel.EPISTEMIC, np.array([[3.5, 0.0]]))
        near = bev.sample(RiskChannel.EPISTEMIC, np.array([[1.0, 0.0]]))
        assert far[0] == 1.0
        assert near[0] == 0.0

    def test_epistemic_mask_always_evaluated(self):
        bev = _producer([CircleObstacle(1.0, 0.0)]).render(ROBOT, 0.0)
        assert bev.mask[RiskChannel.EPISTEMIC].all()


class TestDynamicChannel:
    def test_anticipatory_risk_ahead_of_moving_obstacle(self):
        # walks +x at 1 m/s: from (1, 1) to (4, 1) over 3 s
        ob = CircleObstacle(1.0, 1.0, schedule=np.array(
            [[0.0, 1.0, 1.0], [3.0, 4.0, 1.0]]))
        bev = _producer([ob]).render(ROBOT, 0.0)
        ahead = bev.sample(RiskChannel.DYNAMIC, np.array([[2.5, 1.0]]),
                           unobserved_value=0.0)
        behind = bev.sample(RiskChannel.DYNAMIC, np.array([[-0.5, 1.0]]),
                            unobserved_value=0.0)
        assert ahead[0] > 0.3, "predicted sweep must carry risk"
        assert ahead[0] > behind[0] + 0.2, "risk is anticipatory, not trailing"

    def test_static_obstacle_lands_in_static_channel_not_dynamic(self):
        ob = CircleObstacle(1.5, 0.5)
        bev = _producer([ob]).render(ROBOT, 0.0)
        at = np.array([[1.5, 0.5]])
        assert bev.sample(RiskChannel.STATIC, at)[0] == 1.0
        assert bev.sample(RiskChannel.DYNAMIC, at,
                          unobserved_value=0.0)[0] == 0.0


class TestSampling:
    def test_out_of_grid_returns_pessimistic_prior(self):
        bev = _producer([]).render(ROBOT, 0.0)
        far = np.array([[100.0, 100.0]])
        assert bev.sample(RiskChannel.EPISTEMIC, far,
                          unobserved_value=1.0)[0] == 1.0
        assert bev.sample(RiskChannel.DYNAMIC, far,
                          unobserved_value=0.0)[0] == 0.0
