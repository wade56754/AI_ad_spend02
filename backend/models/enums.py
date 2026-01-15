"""
业务枚举类型定义

本模块定义所有状态字段的枚举类型，确保类型安全和IDE自动补全。
所有枚举值必须与数据库 CHECK 约束保持一致。
"""
from enum import Enum


class UserRole(str, Enum):
    """
    用户角色枚举

    必须与 MASTER.md v4.6 §2.4 和 AUTH_SPEC.md v2.1 §2.2 保持严格一致。
    6 个业务角色（PRD v5.1 移除了 supervisor）:

    | 业务角色 | 技术枚举 | 权限级别 |
    |---------|----------|---------|
    | ceo | CEO | L6 (最高) |
    | admin | ADMIN | L5 |
    | project_owner | PROJECT_OWNER | L4 |
    | finance | FINANCE | L3 |
    | account_manager | ACCOUNT_MANAGER | L2 |
    | pitcher | MEDIA_BUYER | L1 (最低) |

    废弃说明 (PRD v5.1):
    - supervisor → 职责合并到 project_owner
    - data_operator → 职责合并到 project_owner/finance

    SoT Reference: MASTER.md v4.6 §2.4, AUTH_SPEC.md v2.1 §2.2
    """
    CEO = "ceo"                          # 老板 - 资金安全、公司盈亏、最终决策
    ADMIN = "admin"                      # 系统管理员 - 系统配置、全局审计
    PROJECT_OWNER = "project_owner"      # 项目负责人 - 项目盈亏、资金使用效率、日报审核
    FINANCE = "finance"                  # 财务 - 资金出入准确、数据真实
    ACCOUNT_MANAGER = "account_manager"  # 户管 - 账户分配、账户状态监控
    MEDIA_BUYER = "media_buyer"          # 投手(pitcher) - CPL达标、日报准确

    # 废弃角色 - 仅用于向后兼容，新代码禁止使用
    # @deprecated PRD v5.1: 使用 PROJECT_OWNER 替代
    DATA_OPERATOR = "data_operator"      # [废弃] 原主管角色，已合并到 project_owner


class ChannelStatus(str, Enum):
    """渠道状态枚举"""
    ACTIVE = "active"
    INACTIVE = "inactive"


class ProjectStatus(str, Enum):
    """
    项目状态枚举

    必须与 STATE_MACHINE.md v2.6 第5章保持严格一致。
    状态流程: draft → active → suspended → archived
    终态: archived

    SoT Reference: STATE_MACHINE.md v2.6 §5
    """
    DRAFT = "draft"            # 草稿
    ACTIVE = "active"          # 进行中
    SUSPENDED = "suspended"    # 暂停
    ARCHIVED = "archived"      # 已归档（终态）

    def can_transition_to(self, target: 'ProjectStatus') -> bool:
        """
        检查是否可以转换到目标状态

        状态流转规则（基于 STATE_MACHINE.md v2.6 第5章）：
        - draft -> active, archived
        - active -> suspended, archived
        - suspended -> active, archived
        - archived -> (终态，不可转换)
        """
        transitions = {
            self.DRAFT: [self.ACTIVE, self.ARCHIVED],
            self.ACTIVE: [self.SUSPENDED, self.ARCHIVED],
            self.SUSPENDED: [self.ACTIVE, self.ARCHIVED],
            self.ARCHIVED: [],  # 终态
        }
        return target in transitions.get(self, [])


class FulfillmentStatus(str, Enum):
    """
    项目履约状态枚举

    必须与 BUSINESS_RULES.md v4.6 BR-PROJ-006 保持严格一致。
    履约状态: running → fulfilled
    终态: fulfilled (不可回退)

    SoT Reference: BUSINESS_RULES.md v4.6 §4.3.1, BI-06
    """
    RUNNING = "running"        # 履约中 - 项目正在投放
    FULFILLED = "fulfilled"    # 已履约 - 终态，可确认收入

    def can_transition_to(self, target: 'FulfillmentStatus') -> bool:
        """
        检查是否可以转换到目标状态

        状态流转规则（基于 BUSINESS_RULES.md v4.6 BR-PROJ-006）：
        - running -> fulfilled
        - fulfilled -> (终态，不可回退)
        """
        transitions = {
            self.RUNNING: [self.FULFILLED],
            self.FULFILLED: [],  # 终态
        }
        return target in transitions.get(self, [])


class FulfillmentReason(str, Enum):
    """
    履约结束原因枚举

    必须与 BUSINESS_RULES.md v4.6 BI-06 保持严格一致。
    履约完成当且仅当满足以下任一条件:
    - spend_exhausted: 广告费消耗完
    - client_stopped: 甲方明确喊停

    SoT Reference: BUSINESS_RULES.md v4.6 §1.5.2, BI-06
    """
    SPEND_EXHAUSTED = "spend_exhausted"  # 消耗完毕 - 预算全部投放完毕
    CLIENT_STOPPED = "client_stopped"    # 客户喊停 - 客户主动终止投放


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


class WeeklyBriefStatus(str, Enum):
    """
    周报状态枚举

    必须与 B3-weekly-brief.md §2.5 保持严格一致。
    状态流程: draft → submitted
    终态: submitted
    """
    DRAFT = "draft"           # 草稿，可编辑
    SUBMITTED = "submitted"   # 已提交，不可修改
