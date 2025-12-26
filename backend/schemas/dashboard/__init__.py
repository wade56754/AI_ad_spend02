"""
Dashboard Schemas

Pydantic 模型用于 Dashboard API 响应。

包含:
- Legacy V1/V2 schemas (向后兼容)
- CEO Dashboard V3 schemas (毛利=收款-消耗)

Version: 3.0
"""

# Legacy schemas (V1/V2 向后兼容)
from ._legacy import (
    DashboardFilters,
    KpiData,
    KpiResponse,
    TrendItem,
    TrendResponse,
    ProjectRankingItem,
    RankingResponse,
    TodoItem,
    TodoResponse,
    AlertItem,
    DashboardSummary,
    DashboardDetail,
)

# CEO Dashboard V3 schemas
from .ceo import (
    CEOOverviewResponse,
    CashStatusResponse,
    ProfitSummaryResponse,
    ProjectBalanceResponse,
    ActionItemsResponse,
    ProjectRankingResponse,
    TrendDataResponse,
)

__all__ = [
    # Legacy
    'DashboardFilters',
    'KpiData',
    'KpiResponse',
    'TrendItem',
    'TrendResponse',
    'ProjectRankingItem',
    'RankingResponse',
    'TodoItem',
    'TodoResponse',
    'AlertItem',
    'DashboardSummary',
    'DashboardDetail',
    # V3 CEO
    'CEOOverviewResponse',
    'CashStatusResponse',
    'ProfitSummaryResponse',
    'ProjectBalanceResponse',
    'ActionItemsResponse',
    'ProjectRankingResponse',
    'TrendDataResponse',
]
