"""
CEO Dashboard Services

提供CEO仪表盘所需的业务服务。

Services:
- ProfitService: 利润计算服务 (v3 - cost = real_spend, 不含手续费)
- ProjectBalanceService: 项目余额服务
- CashStatusService: 公司现金状况服务
- CEODashboardService: 汇总服务

Version: 3.0
"""

from .profit_service import ProfitService
from .project_balance_service import ProjectBalanceService
from .cash_status_service import CashStatusService
from .ceo_dashboard_service import CEODashboardService

__all__ = [
    'ProfitService',
    'ProjectBalanceService',
    'CashStatusService',
    'CEODashboardService',
]
