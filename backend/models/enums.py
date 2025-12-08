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
    合法角色：admin, finance, data_operator, account_manager, media_buyer, analyst
    """
    ADMIN = "admin"
    FINANCE = "finance"
    DATA_OPERATOR = "data_operator"  # 修改：data_manager → data_operator
    ACCOUNT_MANAGER = "account_manager"  # 新增：缺失的角色
    MEDIA_BUYER = "media_buyer"
    ANALYST = "analyst"  # 新增：测试中使用的角色


class ChannelStatus(str, Enum):
    """渠道状态枚举"""
    ACTIVE = "active"
    INACTIVE = "inactive"


class ProjectStatus(str, Enum):
    """
    项目状态枚举

    与 test_project_service.py 期望对齐：
    - planning: 规划中
    - active: 进行中
    - paused: 暂停
    - completed: 已完成
    - cancelled: 已取消
    """
    PLANNING = "planning"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


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
    """
    日报状态枚举（粉数确认状态机）

    必须与 STATE_MACHINE.md v2.6 第8章保持严格一致。
    8 状态流程：raw_submitted → trend_pending → trend_ok/trend_flagged
    → trend_resolved → final_pending → final_confirmed → final_locked
    """
    RAW_SUBMITTED = "raw_submitted"       # 投手提交原始粉数
    TREND_PENDING = "trend_pending"       # 等待趋势风控检查
    TREND_OK = "trend_ok"                 # 趋势正常
    TREND_FLAGGED = "trend_flagged"       # 趋势异常,需人工复核
    TREND_RESOLVED = "trend_resolved"     # 运营确认异常已解决
    FINAL_PENDING = "final_pending"       # 等待最终粉数确认
    FINAL_CONFIRMED = "final_confirmed"   # 最终粉数已确认
    FINAL_LOCKED = "final_locked"         # 已进入计费,锁定(终态)


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
    """
    对账批次状态枚举

    必须与 STATE_MACHINE.md v2.6 第4章（全局状态一览表）保持严格一致。
    流程: draft → pending_review → approved/needs_adjustment → completed
    """
    DRAFT = "draft"                         # 草稿
    PENDING_REVIEW = "pending_review"       # 待审核
    APPROVED = "approved"                   # 已批准
    NEEDS_ADJUSTMENT = "needs_adjustment"   # 需调整
    COMPLETED = "completed"                 # 已完成（终态）


class ReconciliationDetailStatus(str, Enum):
    """对账明细状态枚举"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    ADJUSTED = "adjusted"


class ReconciliationAdjustmentType(str, Enum):
    """
    对账调整类型枚举

    必须与 DATA_SCHEMA.md v5.2 第3.5.3节保持一致。
    """
    INCREASE = "increase"    # 增加调整
    DECREASE = "decrease"    # 减少调整
    WRITEOFF = "writeoff"    # 核销


class AccountAlertStatus(str, Enum):
    """账户预警状态枚举"""
    OPEN = "open"
    ACK = "ack"
    RESOLVED = "resolved"


class LedgerEntryType(str, Enum):
    """
    总账分录类型枚举

    必须与 LEDGER_SOT.md v1.1 第2.2节保持严格一致。
    PROJECT账本: REVENUE, TOPUP, REVERSAL
    SUPPLIER账本: COST, TOPUP, TRANSFER_OUT, TRANSFER_IN, REVERSAL
    """
    REVENUE = "REVENUE"              # 项目收入（PROJECT账本）
    COST = "COST"                    # 供应商成本（SUPPLIER账本）
    TOPUP = "TOPUP"                  # 充值（两账本通用）
    TRANSFER_OUT = "TRANSFER_OUT"    # 转出（SUPPLIER账本）
    TRANSFER_IN = "TRANSFER_IN"      # 转入（SUPPLIER账本）
    REVERSAL = "REVERSAL"            # 红冲（两账本通用）


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


class TransferRequestStatus(str, Enum):
    """
    死号余额迁移申请状态枚举

    必须与 STATE_MACHINE.md v2.6 第12章保持严格一致。
    状态流程: draft → pending_approval → approved/rejected → completed
    终态: rejected, completed
    """
    DRAFT = "draft"                    # 草稿
    PENDING_APPROVAL = "pending_approval"  # 待审批
    APPROVED = "approved"              # 已审批
    REJECTED = "rejected"              # 已拒绝（终态）
    COMPLETED = "completed"            # 已完成（终态）


class ImportJobStatus(str, Enum):
    """
    导入任务状态枚举

    状态流程: pending → processing → completed/failed
             pending → cancelled (admin only)
    终态: completed, failed, cancelled
    """
    PENDING = "pending"          # 待处理
    PROCESSING = "processing"    # 处理中
    COMPLETED = "completed"      # 已完成（终态）
    FAILED = "failed"            # 失败（终态）
    CANCELLED = "cancelled"      # 已取消（终态）


class ImportJobType(str, Enum):
    """
    导入任务类型枚举
    """
    FINANCE = "finance"                # 财务数据导入
    SPEND = "spend"                    # 消耗数据导入
    RECONCILIATION = "reconciliation"  # 对账数据导入
    DAILY_REPORT = "daily_report"      # 日报数据导入
