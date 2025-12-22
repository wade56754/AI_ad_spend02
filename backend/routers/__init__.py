"""API routers package."""

# 导入所有已启用的路由
from . import (
    health,
    projects,
    authentication,
    users,  # 用户管理 (API_SOT v9.0 §5)
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
    spend,  # 消耗导入 (Financial SoT Phase 2)
)

__all__ = [
    "health",
    "projects",
    "authentication",
    "users",
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
    "spend",
]



