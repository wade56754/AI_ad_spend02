"""
广告账户管理数据模型
Version: 1.0
Author: Claude协作开发
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Dict, Any
from enum import Enum

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
    platform_account_id: Optional[str] = Field(None, max_length=255, description="平台内部账户ID")
    platform_business_id: Optional[str] = Field(None, max_length=255, description="商务管理器ID")
    project_id: int = Field(..., description="项目ID")
    channel_id: int = Field(..., description="渠道ID")
    assigned_user_id: int = Field(..., description="负责投手ID")
    daily_budget: Optional[Decimal] = Field(None, ge=0, decimal_places=2, description="日预算")
    total_budget: Optional[Decimal] = Field(None, ge=0, decimal_places=2, description="总预算")
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
    daily_budget: Optional[Decimal] = Field(None, ge=0, decimal_places=2, description="日预算")
    total_budget: Optional[Decimal] = Field(None, ge=0, decimal_places=2, description="总预算")
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
    change_source: str = Field("manual", pattern="^(manual|automatic|system)$", description="变更来源")
    notes: Optional[str] = Field(None, max_length=1000, description="备注")


class AdAccountBudgetUpdateRequest(BaseModel):
    """更新账户预算请求"""
    model_config = ConfigDict(from_attributes=True)

    daily_budget: Optional[Decimal] = Field(None, ge=0, decimal_places=2, description="日预算")
    total_budget: Optional[Decimal] = Field(None, ge=0, decimal_places=2, description="总预算")
    reason: str = Field(..., min_length=1, max_length=500, description="预算调整原因")


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

    status: str = Field(..., pattern="^(active|acknowledged|resolved|ignored)$", description="预警状态")
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
    platform_distribution: List[Dict[str, Any]] = Field(default_factory=list, description="平台分布")

    # 状态分布
    status_distribution: List[Dict[str, Any]] = Field(default_factory=list, description="状态分布")

    # 趋势数据
    monthly_trends: List[Dict[str, Any]] = Field(default_factory=list, description="月度趋势")
    weekly_performance: List[Dict[str, Any]] = Field(default_factory=list, description="周度表现")

    # TOP数据
    top_performers: List[Dict[str, Any]] = Field(default_factory=list, description="TOP表现账户")
    low_performers: List[Dict[str, Any]] = Field(default_factory=list, description="表现较差账户")

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