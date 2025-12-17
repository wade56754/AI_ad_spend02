"""API routers package."""

# 导入所有已启用的路由
from . import (
    health,
    projects,
    authentication,
    ad_spend,
    ad_accounts,
    channels,
    topup,
    daily_reports,
    suppliers,
    settlements,
    transfers,
    ledger,
    finance_profit,
    import_jobs,
    reconciliation,  # 对账管理
    reports,  # 报表管理
    agents,  # Agent 管理
)

__all__ = [
    "health",
    "projects",
    "authentication",
    "ad_spend",
    "ad_accounts",
    "channels",
    "topup",
    "daily_reports",
    "suppliers",
    "settlements",
    "transfers",
    "ledger",
    "finance_profit",
    "import_jobs",
    "reconciliation",
    "reports",
    "agents",
]



