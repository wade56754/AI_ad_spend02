"""
向后兼容层 - database_models.py

本文件为过渡期兼容层,保证原有代码 `from backend.models.database_models import X` 仍然可用。

⚠️ 已废弃 (DEPRECATED):
建议新代码使用 `from backend.models import X` 替代。

本文件将在下一个大版本中移除。

重构说明：
- 所有模型已按业务域拆分到独立文件
- 添加了完整的 relationship 关系
- 引入了 Enum 类型支持
- 抽取了通用 Mixin

新的模块结构：
- backend/models/base.py        # Base, Mixin, Enum
- backend/models/users.py       # User
- backend/models/channels.py    # Channel, ChannelPerformance
- backend/models/projects.py    # Project, ChannelReview, ChannelAccountRequest
- backend/models/ad_accounts.py # AdAccount, AccountStatusHistory, AccountAlert
- backend/models/reports.py     # DailyReport, AdSpendDaily
- backend/models/finance.py     # TopupRequest, LedgerEntry, ReconciliationBatch, ReconciliationDetail
- backend/models/audit.py       # AuditLog
- backend/models/__init__.py    # 汇总导出
"""

import warnings

# 发出弃用警告
warnings.warn(
    "database_models.py is deprecated. "
    "Please use 'from backend.models import X' instead of "
    "'from backend.models.database_models import X'. "
    "This file will be removed in the next major version.",
    DeprecationWarning,
    stacklevel=2
)

# 从新的模块结构导入所有内容
from .base import Base

# 导入所有模型类
from .core.user import User
from .core.channel import Channel, ChannelReview, ChannelPerformance
from .core.project import Project
from .accounts.account_request import ChannelAccountRequest
from .accounts.ad_account import AdAccount
from .accounts.account_history import AccountStatusHistory, AccountAlert
from .workflow.daily_report import DailyReport
from .workflow.ad_spend import AdSpendDaily
from .workflow.topup_request import TopupRequest
from .finance import LedgerEntry, ReconciliationBatch, ReconciliationDetail
from .audit import AuditLog

# 导出所有模型（保持向后兼容）
__all__ = [
    'Base',
    'User',
    'Channel',
    'ChannelPerformance',
    'Project',
    'ChannelReview',
    'ChannelAccountRequest',
    'AdAccount',
    'AccountStatusHistory',
    'AccountAlert',
    'DailyReport',
    'AdSpendDaily',
    'TopupRequest',
    'LedgerEntry',
    'ReconciliationBatch',
    'ReconciliationDetail',
    'AuditLog',
]
