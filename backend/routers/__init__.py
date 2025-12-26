"""API routers package."""

# 导入所有已启用的路由
from . import (
    health,
    projects,
    project_members,  # 项目成员管理 (MASTER.md v4.4 §2.4)
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
    reconciliation_control,  # 对账中控 (OpenSpec: add-reconciliation-control-center)
    reports,  # 报表管理
    agents,  # Agent 管理
    spend,  # 消耗导入 (Financial SoT Phase 2)
    dashboard,  # CEO驾驶舱 (MASTER.md v4.4 §6.5)
    weekly_briefs,  # 周度简报 (B3-weekly-brief.md)
    fund,  # 资金总览 (A2-fund-overview.md)
    finance_v2,  # 财务管理V2 (资金总览+项目盈亏重构)
)

__all__ = [
    "health",
    "projects",
    "project_members",
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
    "reconciliation_control",
    "reports",
    "agents",
    "spend",
    "dashboard",
    "weekly_briefs",
    "fund",
    "finance_v2",
]
