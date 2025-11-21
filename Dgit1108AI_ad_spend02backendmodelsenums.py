"""
所有枚举类型定义 - 与 STATE_MACHINE.md 和 DATA_SCHEMA.md 对齐

本模块包含系统中所有状态字段的枚举定义：
- UserRole: 用户角色
- ChannelStatus, ProjectStatus, AdAccountStatus: 核心实体状态
- DailyReportStatus, TopupRequestStatus: 业务流程状态
- ReconciliationBatchStatus, ReconciliationDetailStatus: 财务状态
- AccountAlertStatus: 预警状态
- LedgerEntryType: 账本分录类型
- ChannelAccountRequestStatus, ChannelReviewStatus: 申请/审核状态
"""
from enum import Enum


class UserRole(str, Enum):
    """
    用户角色枚举
    
    与 RLS 权限策略对应
    """
    ADMIN = "admin"
    FINANCE = "finance"
    DATA_MANAGER = "data_manager"
    MEDIA_BUYER = "media_buyer"
    CLIENT = "client"


class ChannelStatus(str, Enum):
    """渠道状态"""
    ACTIVE = "active"
    INACTIVE = "inactive"


class ProjectStatus(str, Enum):
    """项目状态"""
    DRAFT = "draft"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"


class AdAccountStatus(str, Enum):
    """
    广告账户状态
    
    状态机转换规则（基于 STATE_MACHINE.md）：
    - NEW -> TESTING, ACTIVE, SUSPENDED
    - TESTING -> ACTIVE, SUSPENDED, DEAD
    - ACTIVE -> SUSPENDED, DEAD, ARCHIVED
    - SUSPENDED -> ACTIVE, DEAD
    - DEAD -> ARCHIVED
    - ARCHIVED -> (终态)
    """
    NEW = "new"
    TESTING = "testing"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DEAD = "dead"
    ARCHIVED = "archived"
    
    def can_transition_to(self, target: 'AdAccountStatus') -> bool:
        """
        检查是否可以转换到目标状态
        
        Args:
            target: 目标状态
            
        Returns:
            bool: 是否允许转换
        """
        transitions = {
            self.NEW: [self.TESTING, self.ACTIVE, self.SUSPENDED],
            self.TESTING: [self.ACTIVE, self.SUSPENDED, self.DEAD],
            self.ACTIVE: [self.SUSPENDED, self.DEAD, self.ARCHIVED],
            self.SUSPENDED: [self.ACTIVE, self.DEAD],
            self.DEAD: [self.ARCHIVED],
            self.ARCHIVED: [],  # 终态，不可转换
        }
        return target in transitions.get(self, [])


class DailyReportStatus(str, Enum):
    """日报状态"""
    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class TopupRequestStatus(str, Enum):
    """
    充值申请状态
    
    流程：draft -> pending_review -> finance_approve -> paid -> completed
    """
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    FINANCE_APPROVE = "finance_approve"
    PAID = "paid"
    COMPLETED = "completed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class ReconciliationBatchStatus(str, Enum):
    """对账批次状态"""
    DRAFT = "draft"
    PENDING = "pending"
    REVIEWING = "reviewing"
    CLOSED = "closed"


class ReconciliationDetailStatus(str, Enum):
    """对账明细状态"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    ADJUSTED = "adjusted"


class AccountAlertStatus(str, Enum):
    """账户预警状态"""
    OPEN = "open"
    ACK = "ack"
    RESOLVED = "resolved"


class LedgerEntryType(str, Enum):
    """总账分录类型"""
    TOPUP_RECEIVED = "topup_received"
    SPEND = "spend"
    ADJUSTMENT = "adjustment"


class ChannelAccountRequestStatus(str, Enum):
    """渠道开户申请状态"""
    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ChannelReviewStatus(str, Enum):
    """渠道评审状态"""
    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
