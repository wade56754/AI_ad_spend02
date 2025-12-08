"""
SQLAlchemy 模型统一导出模块

本模块汇总导出所有 ORM 模型,支持：
1. 从 backend.models 导入所有模型
2. 保持向后兼容 (from backend.models import X)
3. 提供 Base 和 Enum 类型

重构版本：v2.0 (2025-11-19)
- 按业务域拆分模型文件
- 添加完整的 relationship 关系
- 引入 Enum 类型支持
- 抽取通用 Mixin
"""

# Base 类和 Mixin
from .base import (
    Base,
    TimestampMixin,
    CreatedAtMixin,
    SoftDeleteMixin,
    UserScopeMixin,
    AssignableMixin,
)

# Enum 枚举类型
from .base import (
    UserRole,
    ChannelStatus,
    ProjectStatus,
    ReviewStatus,
    AdAccountStatus,
    DailyReportStatus,
    TopupStatus,
    TransferRequestStatus,
    LedgerEntryType,
    ReconciliationBatchStatus,
    ReconciliationDetailStatus,
    ReconciliationAdjustmentType,
    AccountAlertStatus,
    AccountAlertSeverity,
)

# 用户模块
from .core.user import User

# 渠道模块
from .core.channel import Channel, ChannelReview, ChannelPerformance

# 项目模块
from .core.project import Project
from .core.project_member import ProjectMember
from .projects_fixed import ProjectExpense
from .accounts.account_request import ChannelAccountRequest

# 广告账户模块
from .accounts.ad_account import AdAccount
from .accounts.account_history import AccountStatusHistory, AccountAlert
from .accounts.account_extras import AccountPerformance, AccountDocument, AccountNote

# 报告模块
from .workflow.daily_report import DailyReport
from .workflow.ad_spend import AdSpendDaily

# 业务流程模块
from .workflow.topup_request import TopupRequest
from .workflow.transfer_request import TransferRequest
from .workflow.import_job import ImportJob

# 导入任务枚举
from .enums import ImportJobStatus, ImportJobType

# 充值相关辅助表（来自 topup_fixed.py）
from .topup_fixed import (
    TopupTransaction,
    TopupApprovalLog,
)

# 财务模块
from .finance import (
    LedgerEntry,
    ReconciliationBatch,
    ReconciliationDetail,
    ReconciliationAdjustment,
    ReconciliationReport,
    Supplier,
    SupplierStatus,
    PaymentMethod,
    Settlement,
    SettlementStatus,
    SettlementType,
    PaymentStatus,
)

# 审计模块
from .audit import AuditLog

# 日志模块
from .log import Log


# =====================================================================
# 统一导出所有模型
# =====================================================================

__all__ = [
    # Base 和 Mixin
    'Base',
    'TimestampMixin',
    'CreatedAtMixin',
    'SoftDeleteMixin',
    'UserScopeMixin',
    'AssignableMixin',

    # Enum 类型
    'UserRole',
    'ChannelStatus',
    'ProjectStatus',
    'ReviewStatus',
    'AdAccountStatus',
    'DailyReportStatus',
    'TopupStatus',
    'TransferRequestStatus',
    'LedgerEntryType',
    'ReconciliationBatchStatus',
    'ReconciliationDetailStatus',
    'ReconciliationAdjustmentType',
    'AccountAlertStatus',
    'AccountAlertSeverity',
    'ImportJobStatus',
    'ImportJobType',

    # 模型类
    'User',
    'Channel',
    'ChannelPerformance',
    'Project',
    'ProjectMember',
    'ProjectExpense',
    'ChannelReview',
    'ChannelAccountRequest',
    'AdAccount',
    'AccountStatusHistory',
    'AccountAlert',
    'AccountPerformance',
    'AccountDocument',
    'AccountNote',
    'DailyReport',
    'AdSpendDaily',
    'TopupRequest',
    'TransferRequest',
    'TopupTransaction',
    'TopupApprovalLog',
    'LedgerEntry',
    'ReconciliationBatch',
    'ReconciliationDetail',
    'ReconciliationAdjustment',
    'ReconciliationReport',
    'Supplier',
    'SupplierStatus',
    'PaymentMethod',
    'Settlement',
    'SettlementStatus',
    'SettlementType',
    'PaymentStatus',
    'AuditLog',
    'Log',
    'ImportJob',
]
