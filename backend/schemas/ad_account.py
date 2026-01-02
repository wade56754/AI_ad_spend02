"""
广告账户管理数据模型
Version: 1.0
Author: Claude协作开发
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Dict, Any
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict, field_validator


class AccountStatus(str, Enum):
    """账户状态枚举"""

    NEW = "new"
    TESTING = "testing"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DEAD = "dead"
    ARCHIVED = "archived"


class Platform(str, Enum):
    """平台枚举"""

    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    GOOGLE = "google"
    TIKTOK = "tiktok"
    SNAPCHAT = "snapchat"
    TWITTER = "twitter"
    LINKEDIN = "linkedin"
    PINTEREST = "pinterest"


class AlertType(str, Enum):
    """预警类型枚举"""

    BUDGET_EXCEEDED = "budget_exceeded"
    LOW_PERFORMANCE = "low_performance"
    ACCOUNT_RISK = "account_risk"
    PAYMENT_ISSUE = "payment_issue"
    POLICY_VIOLATION = "policy_violation"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"


class AlertSeverity(str, Enum):
    """预警严重程度枚举"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DocumentType(str, Enum):
    """文档类型枚举"""

    CONTRACT = "contract"
    INVOICE = "invoice"
    SCREENSHOT = "screenshot"
    REPORT = "report"
    IDENTITY = "identity"
    PAYMENT_PROOF = "payment_proof"
    OTHER = "other"


class NoteType(str, Enum):
    """备注类型枚举"""

    GENERAL = "general"
    IMPORTANT = "important"
    WARNING = "warning"
    SUCCESS = "success"
    INFO = "info"


# ========== 请求模型 ==========


class AdAccountCreateRequest(BaseModel):
    """创建广告账户请求"""

    model_config = ConfigDict(from_attributes=True)

    account_id: str = Field(..., min_length=1, max_length=255, description="平台账户ID")
    name: str = Field(..., min_length=1, max_length=255, description="账户名称")
    platform: Platform = Field(..., description="广告平台")
    platform_account_id: Optional[str] = Field(
        None, max_length=255, description="平台内部账户ID"
    )
    platform_business_id: Optional[str] = Field(
        None, max_length=255, description="商务管理器ID"
    )
    project_id: int = Field(..., description="项目ID")
    channel_id: int = Field(..., description="渠道ID")
    assigned_user_id: int = Field(..., description="负责投手ID")
    daily_budget: Optional[Decimal] = Field(
        None, ge=0, decimal_places=2, description="日预算"
    )
    total_budget: Optional[Decimal] = Field(
        None, ge=0, decimal_places=2, description="总预算"
    )
    currency: str = Field("USD", max_length=3, description="货币单位")
    timezone: Optional[str] = Field(None, max_length=50, description="时区设置")
    country: Optional[str] = Field(None, max_length=2, description="国家代码")
    account_type: Optional[str] = Field(None, max_length=50, description="账户类型")
    payment_method: Optional[str] = Field(None, max_length=50, description="支付方式")
    billing_information: Optional[Dict[str, Any]] = Field(None, description="账单信息")
    auto_monitoring: bool = Field(True, description="自动监控")
    alert_thresholds: Optional[Dict[str, Any]] = Field(None, description="预警阈值设置")
    notes: Optional[str] = Field(None, max_length=2000, description="备注")
    tags: Optional[List[str]] = Field(None, description="标签列表")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")


class AdAccountUpdateRequest(BaseModel):
    """更新广告账户请求"""

    model_config = ConfigDict(from_attributes=True)

    name: Optional[str] = Field(None, min_length=1, max_length=255, description="账户名称")
    assigned_user_id: Optional[int] = Field(None, description="负责投手ID")
    daily_budget: Optional[Decimal] = Field(
        None, ge=0, decimal_places=2, description="日预算"
    )
    total_budget: Optional[Decimal] = Field(
        None, ge=0, decimal_places=2, description="总预算"
    )
    currency: Optional[str] = Field(None, max_length=3, description="货币单位")
    timezone: Optional[str] = Field(None, max_length=50, description="时区设置")
    country: Optional[str] = Field(None, max_length=2, description="国家代码")
    account_type: Optional[str] = Field(None, max_length=50, description="账户类型")
    payment_method: Optional[str] = Field(None, max_length=50, description="支付方式")
    billing_information: Optional[Dict[str, Any]] = Field(None, description="账单信息")
    auto_monitoring: bool = Field(True, description="自动监控")
    alert_thresholds: Optional[Dict[str, Any]] = Field(None, description="预警阈值设置")
    notes: Optional[str] = Field(None, max_length=2000, description="备注")
    tags: Optional[List[str]] = Field(None, description="标签列表")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")


class AdAccountStatusUpdateRequest(BaseModel):
    """更新账户状态请求"""

    model_config = ConfigDict(from_attributes=True)

    status: AccountStatus = Field(..., description="新状态")
    status_reason: Optional[str] = Field(None, max_length=1000, description="状态变更原因")
    change_source: str = Field(
        "manual", pattern="^(manual|automatic|system)$", description="变更来源"
    )
    notes: Optional[str] = Field(None, max_length=1000, description="备注")


class AdAccountBudgetUpdateRequest(BaseModel):
    """更新账户预算请求"""

    model_config = ConfigDict(from_attributes=True)

    daily_budget: Optional[Decimal] = Field(
        None, ge=0, decimal_places=2, description="日预算"
    )
    total_budget: Optional[Decimal] = Field(
        None, ge=0, decimal_places=2, description="总预算"
    )
    reason: str = Field(..., min_length=1, max_length=500, description="预算调整原因")


class AccountAssignRequest(BaseModel):
    """
    账户分配请求 - TASK-ACC-002

    SoT Ref:
    - BR-ACCT-002: 账户分配唯一性
    - BR-ACCT-005: 分配记录审计
    - API_SOT.md v9.7 §8: POST /api/v1/ad-accounts/{account_id}/assign
    """

    model_config = ConfigDict(from_attributes=True)

    pitcher_id: UUID = Field(..., description="目标投手ID（必须是 media_buyer 角色）")
    reason: Optional[str] = Field(None, max_length=500, description="分配原因（审计用）")


class AccountAssignResponse(BaseModel):
    """账户分配响应"""

    model_config = ConfigDict(from_attributes=True)

    account_id: int = Field(..., description="广告账户ID")
    account_name: str = Field(..., description="账户名称")
    previous_owner_id: Optional[UUID] = Field(None, description="原负责人ID")
    previous_owner_name: Optional[str] = Field(None, description="原负责人名称")
    new_owner_id: UUID = Field(..., description="新负责人ID")
    new_owner_name: str = Field(..., description="新负责人名称")
    assigned_at: datetime = Field(..., description="分配时间")
    assigned_by: UUID = Field(..., description="操作人ID")


class AccountAlertCreateRequest(BaseModel):
    """创建账户预警请求"""

    model_config = ConfigDict(from_attributes=True)

    alert_type: AlertType = Field(..., description="预警类型")
    severity: AlertSeverity = Field(..., description="严重程度")
    title: str = Field(..., min_length=1, max_length=255, description="预警标题")
    message: str = Field(..., min_length=1, max_length=2000, description="预警消息")
    trigger_condition: Optional[Dict[str, Any]] = Field(None, description="触发条件")
    notify_users: Optional[List[int]] = Field(None, description="通知用户列表")


class AccountAlertUpdateRequest(BaseModel):
    """更新账户预警请求"""

    model_config = ConfigDict(from_attributes=True)

    status: str = Field(
        ..., pattern="^(active|acknowledged|resolved|ignored)$", description="预警状态"
    )
    resolution: Optional[str] = Field(None, max_length=1000, description="解决方案")


class AccountNoteCreateRequest(BaseModel):
    """创建账户备注请求"""

    model_config = ConfigDict(from_attributes=True)

    title: str = Field(..., min_length=1, max_length=255, description="备注标题")
    content: str = Field(..., min_length=1, max_length=2000, description="备注内容")
    note_type: NoteType = Field(NoteType.GENERAL, description="备注类型")
    priority: int = Field(1, ge=1, le=5, description="优先级(1-5)")


class AccountDocumentCreateRequest(BaseModel):
    """创建账户文档请求"""

    model_config = ConfigDict(from_attributes=True)

    document_type: DocumentType = Field(..., description="文档类型")
    document_name: str = Field(..., min_length=1, max_length=255, description="文档名称")
    file_path: str = Field(..., max_length=500, description="文件路径")
    description: Optional[str] = Field(None, max_length=1000, description="文档描述")
    tags: Optional[List[str]] = Field(None, description="标签列表")
    is_public: bool = Field(False, description="是否公开")
    shared_users: Optional[List[int]] = Field(None, description="共享用户列表")


# ========== 响应模型 ==========


class AdAccountResponse(BaseModel):
    """广告账户响应"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    account_id: str
    name: str
    platform: str
    platform_account_id: Optional[str]
    platform_business_id: Optional[str]
    project_id: int
    project_name: Optional[str] = None
    channel_id: int
    channel_name: Optional[str] = None
    assigned_user_id: int
    assigned_user_name: Optional[str] = None
    status: AccountStatus
    status_reason: Optional[str]
    last_status_change: Optional[datetime]

    # 生命周期
    created_date: Optional[datetime]
    activated_date: Optional[datetime]
    suspended_date: Optional[datetime]
    dead_date: Optional[datetime]
    archived_date: Optional[datetime]

    # 预算信息
    daily_budget: Optional[Decimal]
    total_budget: Optional[Decimal]
    remaining_budget: Optional[Decimal]
    setup_fee: Optional[Decimal]
    setup_fee_paid: bool

    # 账户信息
    currency: str
    timezone: Optional[str]
    country: Optional[str]
    account_type: Optional[str]
    payment_method: Optional[str]

    # 性能数据
    total_spend: Decimal
    total_leads: int
    avg_cpl: Optional[Decimal]
    best_cpl: Optional[Decimal]

    # 监控设置
    auto_monitoring: bool
    alert_thresholds: Optional[Dict[str, Any]]

    # 管理信息
    notes: Optional[str]
    tags: Optional[List[str]]
    created_by: int
    created_by_name: Optional[str]
    created_at: datetime
    updated_at: datetime

    # 计算字段
    days_active: Optional[int] = Field(None, description="活跃天数")
    budget_utilization: Optional[float] = Field(None, description="预算使用率")
    recent_spend_7d: Optional[Decimal] = Field(None, description="近7天消耗")
    recent_leads_7d: Optional[int] = Field(None, description="近7天潜在客户数")


class AdAccountListResponse(BaseModel):
    """广告账户列表响应"""

    items: List[AdAccountResponse]
    meta: dict


class AccountStatusHistoryResponse(BaseModel):
    """账户状态历史响应"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    account_id: int
    old_status: Optional[str]
    new_status: str
    change_reason: Optional[str]
    changed_at: datetime
    changed_by: int
    changed_by_name: Optional[str]
    change_source: str
    performance_data: Optional[Dict[str, Any]]
    notes: Optional[str]


class AccountAlertResponse(BaseModel):
    """账户预警响应"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    account_id: int
    account_name: Optional[str]
    alert_type: AlertType
    severity: AlertSeverity
    title: str
    message: str
    status: str
    trigger_condition: Optional[Dict[str, Any]]
    trigger_value: Optional[Decimal]
    threshold_value: Optional[Decimal]
    acknowledged_by: Optional[int]
    acknowledged_by_name: Optional[str]
    acknowledged_at: Optional[datetime]
    resolution: Optional[str]
    resolved_by: Optional[int]
    resolved_by_name: Optional[str]
    resolved_at: Optional[datetime]
    notify_users: Optional[List[int]]
    notification_sent: bool
    created_at: datetime
    updated_at: datetime


class AccountDocumentResponse(BaseModel):
    """账户文档响应"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    account_id: int
    account_name: Optional[str]
    document_type: DocumentType
    document_name: str
    file_path: str
    file_size: Optional[int]
    file_type: Optional[str]
    description: Optional[str]
    tags: Optional[List[str]]
    status: str
    uploaded_by: int
    uploaded_by_name: Optional[str]
    uploaded_at: datetime
    is_public: bool
    shared_users: Optional[List[int]]
    created_at: datetime
    updated_at: datetime


class AccountNoteResponse(BaseModel):
    """账户备注响应"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    account_id: int
    account_name: Optional[str]
    title: str
    content: str
    note_type: NoteType
    priority: int
    is_resolved: bool
    resolved_at: Optional[datetime]
    created_by: int
    created_by_name: Optional[str]
    created_at: datetime


class AdAccountStatisticsResponse(BaseModel):
    """广告账户统计响应"""

    model_config = ConfigDict(from_attributes=True)

    # 总体统计
    total_accounts: int = Field(0, description="总账户数")
    active_accounts: int = Field(0, description="活跃账户数")
    suspended_accounts: int = Field(0, description="暂停账户数")
    dead_accounts: int = Field(0, description="死亡账户数")
    new_accounts: int = Field(0, description="新账户数")

    # 性能统计
    total_spend: Decimal = Field(0, description="总消耗")
    total_leads: int = Field(0, description="总潜在客户数")
    avg_cpl: Decimal = Field(0, description="平均单粉成本")
    best_cpl: Decimal = Field(0, description="最佳单粉成本")

    # 预算统计
    total_budget: Decimal = Field(0, description="总预算")
    total_daily_budget: Decimal = Field(0, description="总日预算")
    budget_utilization: float = Field(0, description="预算使用率")

    # 平台分布
    platform_distribution: List[Dict[str, Any]] = Field(
        default_factory=list, description="平台分布"
    )

    # 状态分布
    status_distribution: List[Dict[str, Any]] = Field(
        default_factory=list, description="状态分布"
    )

    # 趋势数据
    monthly_trends: List[Dict[str, Any]] = Field(
        default_factory=list, description="月度趋势"
    )
    weekly_performance: List[Dict[str, Any]] = Field(
        default_factory=list, description="周度表现"
    )

    # TOP数据
    top_performers: List[Dict[str, Any]] = Field(
        default_factory=list, description="TOP表现账户"
    )
    low_performers: List[Dict[str, Any]] = Field(
        default_factory=list, description="表现较差账户"
    )

    # 预警统计
    active_alerts: int = Field(0, description="活跃预警数")
    critical_alerts: int = Field(0, description="严重预警数")


# ========== 简化模型 ==========


class AdAccountSummary(BaseModel):
    """广告账户摘要"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    account_id: str
    name: str
    platform: str
    status: AccountStatus
    total_spend: Decimal
    total_leads: int
    avg_cpl: Optional[Decimal]
    created_at: datetime


class AdAccountMini(BaseModel):
    """广告账户迷你信息"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    account_id: str
    name: str
    platform: str
    status: AccountStatus
    assigned_user_id: int
    assigned_user_name: Optional[str] = None


# ========== 账户转移 (TASK-ACC-003) ==========


class AccountTransferRequest(BaseModel):
    """
    账户转移请求 - TASK-ACC-003

    将账户从当前投手转移到另一个投手。
    与 assign_account 的区别：转移要求账户已有负责人，且必须填写转移原因。

    SoT Ref:
    - BR-ACCT-002: 账户分配唯一性（每账户仅一个负责人）
    - BR-ACCT-005: 分配记录审计
    - API_SOT.md v9.7 §8: POST /api/v1/ad-accounts/{account_id}/transfer
    """

    model_config = ConfigDict(from_attributes=True)

    target_pitcher_id: UUID = Field(
        ..., description="目标投手ID（必须是 media_buyer/pitcher 角色）"
    )
    reason: str = Field(..., min_length=5, max_length=500, description="转移原因（必填，用于审计）")
    notes: Optional[str] = Field(None, max_length=1000, description="附加备注")

    @field_validator("reason")
    @classmethod
    def validate_reason(cls, v: str) -> str:
        """验证转移原因不能为空或仅包含空白字符"""
        if not v or not v.strip():
            raise ValueError("转移原因不能为空")
        return v.strip()


class AccountTransferResponse(BaseModel):
    """
    账户转移响应 - TASK-ACC-003

    SoT Ref:
    - BR-ACCT-005: 分配记录审计（审计日志字段）
    """

    model_config = ConfigDict(from_attributes=True)

    # 账户信息
    account_id: int = Field(..., description="广告账户ID")
    account_name: str = Field(..., description="账户名称")
    account_code: str = Field(..., description="平台账户ID")

    # 转移详情
    previous_pitcher_id: UUID = Field(..., description="原负责人ID")
    previous_pitcher_name: str = Field(..., description="原负责人名称")
    new_pitcher_id: UUID = Field(..., description="新负责人ID")
    new_pitcher_name: str = Field(..., description="新负责人名称")

    # 审计信息
    transferred_at: datetime = Field(..., description="转移时间")
    transferred_by: UUID = Field(..., description="操作人ID")
    transferred_by_name: str = Field(..., description="操作人名称")
    reason: str = Field(..., description="转移原因")

    # 审计日志ID（可用于后续追溯）
    audit_log_id: Optional[int] = Field(None, description="审计日志ID")


# ========== 死号处理 (TASK-ACC-004) ==========


class MarkDeadRequest(BaseModel):
    """
    标记死号请求 - TASK-ACC-004

    将广告账户标记为死号状态。死号只能进行余额迁移，不能再进行日报、充值等操作。

    SoT Ref:
    - STATE_MACHINE.md v2.9 §7.1: 账户状态机 (dead 为终态之一)
    - BR-ACCT-006: 停用账户禁止操作（死号仅允许余额迁移）
    - API_SOT.md v9.0 §8: POST /api/v1/ad-accounts/{account_id}/mark-dead
    """

    model_config = ConfigDict(from_attributes=True)

    reason: str = Field(
        ..., min_length=5, max_length=500, description="标记死号原因（必填，用于审计）"
    )
    notes: Optional[str] = Field(None, max_length=1000, description="附加备注")
    transfer_balance: bool = Field(False, description="是否需要后续进行余额迁移（仅作标记，不自动执行）")

    @field_validator("reason")
    @classmethod
    def validate_reason(cls, v: str) -> str:
        """验证死号原因不能为空或仅包含空白字符"""
        if not v or not v.strip():
            raise ValueError("死号原因不能为空")
        return v.strip()


class MarkDeadResponse(BaseModel):
    """
    标记死号响应 - TASK-ACC-004

    SoT Ref:
    - BR-ACCT-005: 状态变更记录审计
    - STATE_MACHINE.md §7.2: 所有状态变更写入 account_status_history
    """

    model_config = ConfigDict(from_attributes=True)

    # 账户信息
    account_id: int = Field(..., description="广告账户ID")
    account_name: str = Field(..., description="账户名称")
    account_code: str = Field(..., description="平台账户ID")
    platform: str = Field(..., description="广告平台")
    project_id: int = Field(..., description="所属项目ID")
    project_name: Optional[str] = Field(None, description="所属项目名称")

    # 状态变更详情
    previous_status: str = Field(..., description="原状态")
    new_status: str = Field(default="dead", description="新状态（固定为 dead）")
    marked_at: datetime = Field(..., description="标记时间")
    marked_by: UUID = Field(..., description="操作人ID")
    marked_by_name: str = Field(..., description="操作人名称")
    reason: str = Field(..., description="死号原因")

    # 账户快照（死号时刻的关键数据）
    final_balance: Optional[Decimal] = Field(None, description="最终余额")
    total_spend: Decimal = Field(..., description="累计消耗")
    total_leads: int = Field(..., description="累计粉数")

    # 后续操作提示
    needs_balance_transfer: bool = Field(False, description="是否需要余额迁移")
    balance_transfer_url: Optional[str] = Field(None, description="余额迁移 API 地址（如有余额）")

    # 审计信息
    audit_log_id: Optional[int] = Field(None, description="审计日志ID")
    status_history_id: Optional[int] = Field(None, description="状态历史记录ID")
