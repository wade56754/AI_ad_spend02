"""
财务服务模块

包含:
- ProfitService: 利润聚合与报表服务 (PROFIT_SOT.md v1.1)
"""

from .profit_service import ProfitService, get_profit_service

__all__ = [
    "ProfitService",
    "get_profit_service",
]
