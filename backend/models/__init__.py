"""
AI广告代投系统 - 数据模型
导出所有数据模型类
"""

# 导入所有模型
from .ad_account import AdAccount
from .ad_spend_daily import AdSpendDaily
from .ai_monitoring import (
    AIAnomalyDetection,
    AccountLifecyclePrediction,
    MonitoringRule
)
from .channels import Channel
from .daily_report import DailyReport, DailyReportAuditLog
from .ledger import LedgerEntry
from .log import Log
from .notifications import (
    Notification,
    NotificationTemplate,
    SystemConfig,
    AuditLog
)
from .projects import Project, ProjectMember, ProjectExpense
from .reconciliation_extended import (
    ReconciliationBatch,
    ReconciliationDetail,
    ReconciliationDifference
)
from .topup import TopupRequest, TopupTransaction, TopupApprovalLog, Topup
from .users import Role, User

# 为了向后兼容，创建别名
Reconciliation = ReconciliationDetail

# 为了向后兼容，继续导出所有模型
__all__ = [
    # 核心业务模型
    "Project",
    "ProjectMember",
    "ProjectExpense",
    "Channel",
    "AdAccount",
    "User",
    "Role",

    # 日报和消耗模型
    "DailyReport",
    "DailyReportAuditLog",
    "AdSpendDaily",

    # 充值和财务模型
    "Topup",  # 向后兼容别名
    "TopupRequest",
    "TopupTransaction",
    "TopupApprovalLog",
    "LedgerEntry",

    # 对账模型
    "Reconciliation",
    "ReconciliationBatch",
    "ReconciliationDetail",
    "ReconciliationDifference",

    # AI监控模型
    "AIAnomalyDetection",
    "AccountLifecyclePrediction",
    "MonitoringRule",

    # 通知和系统模型
    "Notification",
    "NotificationTemplate",
    "SystemConfig",
    "AuditLog",

    # 日志模型
    "Log",
]