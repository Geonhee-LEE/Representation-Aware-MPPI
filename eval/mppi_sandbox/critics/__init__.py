# SPDX-License-Identifier: BSD-3-Clause
"""Cost critics that consume BEV representation channels (D-013 / D-014)."""

from .risk_inflation import RiskInflationCritic

__all__ = ["RiskInflationCritic"]
