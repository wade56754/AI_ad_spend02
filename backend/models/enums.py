"""
业务枚举类型定义

本模块定义所有状态字段的枚举类型，确保类型安全和IDE自动补全。
所有枚举值必须与数据库 CHECK 约束保持一致。
"""
from enum import Enum


class UserRole(str, Enum):
    """
    用户角色枚举

    必须与 STATE_MACHINE.md 第2章保持严格一致。
    合法角色：admin, finance, data_operator, account_manager, media_buyer
    """
    ADMIN = "admin"
    FINANCE = "finance"
    DATA_OPERATOR = "data_operator"  # 修改：data_manager → data_operator
    ACCOUNT_MANAGER = "account_manager"  # 新增：缺失的角色
    MEDIA_BUYER = "media_buyer"


class ChannelStatus(str, Enum):
    """渠道状态枚举"""
    ACTIVE = "active"
    INACTIVE = "inactive"


class ProjectStatus(str, Enum):
    """项目状态枚举"""
    DRAFT = "draft"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"


class AdAccountStatus(str, Enum):
    """广告账户状态枚举"""
    NEW = "new"
    TESTING = "testing"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DEAD = "dead"
    ARCHIVED = "archived"

    def can_transition_to(self, target: 'AdAccountStatus') -> bool:
        """
        检查是否可以转换到目标状态

        状态流转规则（基于 STATE_MACHINE.md v2.5 第 14.5 章）：
        - new -> testing, active, suspended, dead, archived
        - testing -> active, suspended, dead, archived
        - active -> suspended, dead, archived
        - suspended -> active, dead, archived
        - dead -> archived
        - archived -> (终态，不可转换)
        """
        transitions = {
            self.NEW: [self.TESTING, self.ACTIVE, self.SUSPENDED, self.DEAD, self.ARCHIVED],
            self.TESTING: [self.ACTIVE, self.SUSPENDED, self.DEAD, self.ARCHIVED],
            self.ACTIVE: [self.SUSPENDED, self.DEAD, self.ARCHIVED],
            self.SUSPENDED: [self.ACTIVE, self.DEAD, self.ARCHIVED],
            self.DEAD: [self.ARCHIVED],
            self.ARCHIVED: [],
        }
        return target in transitions.get(self, [])


class DailyReportStatus(str, Enum):
    """日报状态枚举"""
    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class TopupRequestStatus(str, Enum):
    """充值申请状态枚举"""
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    FINANCE_APPROVE = "finance_approve"
    PAID = "paid"
    COMPLETED = "completed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class ReconciliationBatchStatus(str, Enum):
    """对账批次状态枚举"""
    DRAFT = "draft"
    PENDING = "pending"
    REVIEWING = "reviewing"
    CLOSED = "closed"


class ReconciliationDetailStatus(str, Enum):
    """对账明细状态枚举"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    ADJUSTED = "adjusted"


class AccountAlertStatus(str, Enum):
    """账户预警状态枚举"""
    OPEN = "open"
    ACK = "ack"
    RESOLVED = "resolved"


class LedgerEntryType(str, Enum):
    """账本条目类型枚举"""
    TOPUP_RECEIVED = "topup_received"
    SPEND = "spend"
    ADJUSTMENT = "adjustment"


class ChannelAccountRequestStatus(str, Enum):
    """渠道账户申请状态枚举"""
    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ChannelReviewStatus(str, Enum):
    """渠道审核状态枚举"""
    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
