# SPDX-License-Identifier: BSD-3-Clause
"""BEV representation producers for the sandbox.

Channel order and unobserved-mask semantics follow the canonical
multi-channel risk BEV stack contract (docs/decisions.md D-012,
docs/multi_channel_risk_bev_stack.md): fixed 5-row order, indices are
append-only, observability travels as an explicit boolean mask (never a
NaN sentinel), unimplemented channels publish an all-unobserved row.
"""

from __future__ import annotations

from enum import IntEnum


class RiskChannel(IntEnum):
    """D-012 canonical channel order. Append-only — never reuse or shift."""
    STATIC = 0
    DYNAMIC = 1
    TRAVERSABILITY = 2
    EPISTEMIC = 3
    ALEATORIC = 4


N_CHANNELS = len(RiskChannel)

from .gt_bev import BevStack, GTBevProducer  # noqa: E402

__all__ = ["RiskChannel", "N_CHANNELS", "BevStack", "GTBevProducer"]
