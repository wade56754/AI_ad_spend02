"""
对账管理数据模型
Version: 1.0
Author: Claude协作开发
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Optional, List, Dict, Any
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict, field_validator


class ReconciliationStatus(str, Enum):
    """对账状态枚举"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    EXCEPTION = "exception"
    RESOLVED = "resolved"


class MatchStatus(str, Enum):
    """匹配状态枚举"""
    PENDING = "pending"
    MATCHED = "matched"
    AUTO_MATCHED = "auto_matched"
    MANUAL_REVIEW = "manual_review"
    EXCEPTION = "exception"
    RESOLVED = "resolved"


class ReconciliationBatchStatus(str, Enum):
    """对账批次状态枚举"""
    PENDING = ReconciliationStatus.PENDING
    PROCESSING = ReconciliationStatus.PROCESSING
    COMPLETED = ReconciliationStatus.COMPLETED
    EXCEPTION = ReconciliationStatus.EXCEPTION
    RESOLVED = ReconciliationStatus.RESOLVED


class AdjustmentType(str, Enum):
    """调整类型枚举 - 对齐 DATA_SCHEMA.md v5.2"""
    INCREASE = "increase"    # 增加调整
    DECREASE = "decrease"    # 减少调整
    WRITEOFF = "writeoff"    # 核销


class AdjustmentReason(str, Enum):
    """调整原因枚举"""
    DATA_ERROR = "data_error"
    CURRENCY_FLUCTUATION = "currency_fluctuation"
    ROUNDING_DIFFERENCE = "rounding_difference"
    TIME_DELAY = "time_delay"
    PLATFORM_ERROR = "platform_error"
    MANUAL_ADJUSTMENT = "manual_adjustment"
    OTHER = "other"


class ReportType(str, Enum):
    """报告类型枚举"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


# ========== 请求模型 ==========

class ReconciliationBatchCreateRequest(BaseModel):
    """创建对账批次请求"""
    model_config = ConfigDict(from_attributes=True)

    reconciliation_date: date = Field(..., description="对账日期")
    channel_ids: Optional[List[int]] = Field(None, description="渠道ID列表，为空则对所有渠道")
    auto_match: bool = Field(True, description="是否自动匹配")
    threshold: Optional[Decimal] = Field(None, ge=0, decimal_places=2, description="差异阈值")
    notes: Optional[str] = Field(None, max_length=1000, description="备注说明")

    @field_validator('reconciliation_date')
    @classmethod
    def validate_reconciliation_date(cls, v):
        """验证对账日期"""
        today = date.today()
        if v > today:
            raise ValueError('对账日期不能是未来日期')
        # 限制对账不能早于30天前
        if v < today - timedelta(days=30):
            raise ValueError('对账日期不能早于30天前')
        return v

    @field_validator('threshold')
    @classmethod
    def validate_threshold(cls, v):
        """验证阈值格式"""
        if v is not None and v.as_tuple().exponent < -2:
            raise ValueError('阈值最多保留2位小数')
        return v


class ReconciliationDetailReviewRequest(BaseModel):
    """审核对账差异请求"""
    model_config = ConfigDict(from_attributes=True)

    action: str = Field(..., pattern="^(approve|reject|investigate)$", description="审核动作")
    is_matched: bool = Field(..., description="是否确认匹配")
    match_status: Optional[str] = Field(None, pattern="^(matched|exception|resolved)$", description="匹配状态")
    review_notes: Optional[str] = Field(None, max_length=1000, description="审核说明")
    auto_confidence: Optional[Decimal] = Field(None, ge=0, le=1, decimal_places=2, description="自动匹配置信度")
    difference_type: Optional[str] = Field(None, max_length=50, description="差异类型")
    difference_reason: Optional[str] = Field(None, max_length=1000, description="差异原因")

    @field_validator('auto_confidence')
    @classmethod
    def validate_confidence(cls, v, info):
        """验证置信度"""
        if v is not None and info.data.get('action') == 'auto_matched':
            if v < 0.8:
                raise ValueError('自动匹配的置信度不能低于0.8')
        return v


class ReconciliationAdjustmentCreateRequest(BaseModel):
    """创建调整记录请求 - 对齐 DATA_SCHEMA.md v5.2"""
    model_config = ConfigDict(from_attributes=True)

    adjustment_type: str = Field(..., pattern="^(increase|decrease|writeoff)$", description="调整类型")
    adjustment_amount: Decimal = Field(..., decimal_places=2, description="调整金额")
    adjustment_reason: str = Field(..., max_length=100, description="调整原因")
    detailed_reason: Optional[str] = Field(None, max_length=1000, description="详细原因说明")
    # 以下字段为向后兼容保留，但不再是必填
    original_amount: Optional[Decimal] = Field(None, decimal_places=2, description="原始金额（可选）")
    evidence_url: Optional[str] = Field(None, max_length=500, description="证据文件URL")
    notes: Optional[str] = Field(None, max_length=1000, description="备注")

    @field_validator('adjustment_amount')
    @classmethod
    def validate_adjustment_amount(cls, v):
        """验证调整金额格式"""
        if v.as_tuple().exponent < -2:
            raise ValueError('调整金额最多保留2位小数')
        return v


class ReconciliationReportGenerateRequest(BaseModel):
    """生成对账报告请求"""
    model_config = ConfigDict(from_attributes=True)

    batch_id: Optional[int] = Field(None, description="批次ID，为空则生成报告")
    report_type: str = Field(..., pattern="^(daily|weekly|monthly)$", description="报告类型")
    report_period_start: date = Field(..., description="报告开始日期")
    report_period_end: date = Field(..., description="报告结束日期")
    include_charts: bool = Field(True, description="是否包含图表")
    format_type: str = Field("excel", pattern="^(excel|pdf|json)$", description="报告格式")

    @field_validator('report_period_end')
    @classmethod
    def validate_date_range(cls, v, info):
        """验证日期范围"""
        start_date = info.data.get('report_period_start')
        if start_date and v < start_date:
            raise ValueError('结束日期不能早于开始日期')

        # 限制报告周期
        delta = v - start_date
        if info.data.get('report_type') == 'daily' and delta.days > 1:
            raise ValueError('日报报告周期不能超过1天')
        elif info.data.get('report_type') == 'weekly' and delta.days > 7:
            raise ValueError('周报报告周期不能超过7天')
        elif info.data.get('report_type') == 'monthly' and delta.days > 31:
            raise ValueError('月报报告周期不能超过31天')
        return v


# ========== 响应模型 ==========

class ReconciliationBatchResponse(BaseModel):
    """
    对账批次响应

    与 ReconciliationBatch 模型对齐 (DATA_SCHEMA.md v5.2)
    """
    model_config = ConfigDict(from_attributes=True)

    id: int
    batch_code: str = Field(..., alias="batch_no", description="批次代码")
    period_start: date = Field(..., description="对账期间开始")
    period_end: date = Field(..., description="对账期间结束")
    status: str = Field(..., description="状态 (5状态机)")
    total_system_spend: Optional[Decimal] = Field(None, description="系统总消耗")
    total_actual_spend: Optional[Decimal] = Field(None, description="实际总消耗")
    discrepancy: Optional[Decimal] = Field(None, description="差异金额")
    created_by: Optional[str] = Field(None, description="创建人ID")
    reviewed_by: Optional[str] = Field(None, description="审核人ID")
    closed_at: Optional[datetime] = Field(None, description="关闭时间")
    version: int = Field(1, description="乐观锁版本号")
    created_at: datetime
    updated_at: datetime

    # 计算字段（非数据库字段）
    discrepancy_rate: Optional[float] = Field(None, description="差异率百分比")

    # 兼容别名
    @property
    def batch_no(self) -> str:
        return self.batch_code

    @property
    def reconciliation_date(self) -> date:
        return self.period_end

    @property
    def total_platform_spend(self) -> Optional[Decimal]:
        return self.total_system_spend

    @property
    def total_internal_spend(self) -> Optional[Decimal]:
        return self.total_actual_spend

    @property
    def total_difference(self) -> Optional[Decimal]:
        return self.discrepancy


class ReconciliationBatchListResponse(BaseModel):
    """对账批次列表响应"""
    items: List[ReconciliationBatchResponse]
    meta: dict


class ReconciliationDetailResponse(BaseModel):
    """
    对账详情响应

    与 ReconciliationDetail 模型对齐 (DATA_SCHEMA.md v5.2)
    """
    model_config = ConfigDict(from_attributes=True)

    id: int
    batch_id: int
    ad_account_id: int
    system_spend: Decimal = Field(..., description="系统消耗")
    actual_spend: Decimal = Field(..., description="实际消耗")
    discrepancy: Decimal = Field(..., description="差异金额")
    status: str = Field(..., description="状态 (pending/confirmed/adjusted)")
    notes: Optional[str] = Field(None, description="备注")
    version: int = Field(1, description="乐观锁版本号")
    created_at: datetime
    updated_at: datetime

    # 计算属性
    discrepancy_rate: Optional[float] = Field(None, description="差异率百分比")
    has_discrepancy: Optional[bool] = Field(None, description="是否存在差异")

    # 关联数据（可选，通过 relationship 填充）
    ad_account_name: Optional[str] = Field(None, description="广告账户名称")
    project_name: Optional[str] = Field(None, description="项目名称")
    channel_name: Optional[str] = Field(None, description="渠道名称")

    # 兼容别名
    @property
    def platform_spend(self) -> Decimal:
        return self.system_spend

    @property
    def internal_spend(self) -> Decimal:
        return self.actual_spend

    @property
    def spend_difference(self) -> Decimal:
        return self.discrepancy

    @property
    def match_status(self) -> str:
        return self.status

    @property
    def is_matched(self) -> bool:
        return abs(self.discrepancy) < Decimal('0.01')


class ReconciliationDetailListResponse(BaseModel):
    """对账详情列表响应"""
    items: List[ReconciliationDetailResponse]
    meta: dict


class ReconciliationAdjustmentResponse(BaseModel):
    """
    调整记录响应

    与 ReconciliationAdjustment 模型对齐 (DATA_SCHEMA.md v5.2)
    """
    model_config = ConfigDict(from_attributes=True)

    id: int
    detail_id: int
    adjustment_type: str = Field(..., description="调整类型 (increase/decrease/writeoff)")
    amount: Decimal = Field(..., description="调整金额")
    reason: Optional[str] = Field(None, description="调整原因")
    created_by: Optional[str] = Field(None, description="创建人ID")
    version: int = Field(1, description="乐观锁版本号")
    created_at: datetime
    updated_at: datetime

    # 兼容别名
    @property
    def adjustment_amount(self) -> Decimal:
        return self.amount

    @property
    def adjustment_reason(self) -> Optional[str]:
        return self.reason


class ReconciliationStatisticsResponse(BaseModel):
    """对账统计响应"""
    model_config = ConfigDict(from_attributes=True)

    # 总体统计
    total_batches: int = Field(0, description="总对账批次数")
    completed_batches: int = Field(0, description="已完成批次")
    exception_batches: int = Field(0, description="异常批次")
    resolved_batches: int = Field(0, description="已解决批次")

    # 账户统计
    total_accounts: int = Field(0, description="总账户数")
    matched_accounts: int = Field(0, description="匹配账户数")
    mismatched_accounts: int = Field(0, description="差异账户数")

    # 金额统计
    total_platform_spend: Decimal = Field(0, description="平台总消耗")
    total_internal_spend: Decimal = Field(0, description="内部总消耗")
    total_difference: Decimal = Field(0, description="总差异金额")
    total_adjustments: Decimal = Field(0, description="总调整金额")
    net_difference: Optional[Decimal] = Field(None, description="净差异（调整后）")

    # 效率统计
    auto_match_rate: float = Field(0, description="自动匹配率(%)")
    manual_review_rate: float = Field(0, description="人工审核率(%)")
    resolution_rate: float = Field(0, description="问题解决率(%)")
    avg_processing_time_hours: float = Field(0, description="平均处理时间(小时)")
    difference_rate: float = Field(0, description="差异率(%)")

    # 趋势数据
    monthly_trends: List[Dict[str, Any]] = Field(default_factory=list, description="月度趋势")
    daily_trends: List[Dict[str, Any]] = Field(default_factory=list, description="日度趋势")
    top_difference_reasons: List[Dict[str, Any]] = Field(default_factory=list, description="TOP5差异原因")
    channel_performance: List[Dict[str, Any]] = Field(default_factory=list, description="渠道对账表现")
    top_mismatched_accounts: List[Dict[str, Any]] = Field(default_factory=list, description="TOP10差异账户")


class ReconciliationReportResponse(BaseModel):
    """
    对账报告响应

    与 ReconciliationReport 模型对齐 (DATA_SCHEMA.md v5.2)
    """
    model_config = ConfigDict(from_attributes=True)

    id: int
    batch_id: int
    report_type: str = Field(..., description="报告类型 (daily/weekly/monthly)")
    period_start: date = Field(..., description="报告期间开始")
    period_end: date = Field(..., description="报告期间结束")
    metrics: Optional[str] = Field(None, description="报告指标(JSON)")
    report_url: Optional[str] = Field(None, description="报告文件URL")
    generated_by: Optional[str] = Field(None, description="生成人ID")
    generated_at: Optional[datetime] = Field(None, description="生成时间")
    created_at: datetime
    updated_at: datetime

    # 计算属性
    metrics_dict: Optional[Dict[str, Any]] = Field(None, description="报告指标字典")

    # 兼容别名
    @property
    def report_period_start(self) -> date:
        return self.period_start

    @property
    def report_period_end(self) -> date:
        return self.period_end


class ReconciliationReportListResponse(BaseModel):
    """对账报告列表响应"""
    items: List[ReconciliationReportResponse]
    meta: dict


# ========== 简化模型 ==========

class ReconciliationBatchSummary(BaseModel):
    """对账批次摘要"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    batch_no: str
    reconciliation_date: date
    status: str
    total_accounts: int
    match_rate: float
    total_difference: Decimal
    created_at: datetime


class ReconciliationDetailSummary(BaseModel):
    """对账详情摘要"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    ad_account_name: str
    platform_spend: Decimal
    internal_spend: Decimal
    spend_difference: Decimal
    is_matched: bool
    match_status: str
    created_at: datetime


class ReconciliationExportData(BaseModel):
    """对账导出数据"""
    batch_no: str
    reconciliation_date: str
    ad_account_name: str
    project_name: str
    channel_name: str
    platform_spend: float
    internal_spend: float
    spend_difference: float
    percentage_difference: float
    is_matched: bool
    match_status: str
    difference_type: Optional[str]
    difference_reason: Optional[str]
    reviewed_by: Optional[str]
    reviewed_at: Optional[str]
    resolved_by: Optional[str]
    resolved_at: Optional[str]
    created_at: str


class ReconciliationMismatchAnalysis(BaseModel):
    """差异分析模型"""
    model_config = ConfigDict(from_attributes=True)

    account_id: int
    account_name: str
    total_mismatches: int
    recent_mismatches: List[dict]
    common_difference_types: List[str]
    total_difference_amount: Decimal
    suggested_actions: List[str]


class ReconciliationTrendData(BaseModel):
    """对账趋势数据"""
    model_config = ConfigDict(from_attributes=True)

    date: date
    total_accounts: int
    matched_accounts: int
    matched_rate: float
    total_difference: Decimal
    auto_matched_count: int
    manual_review_count: int


# ========== OpenSpec: add-reconciliation-control-center ==========
# 以下为对账中控模块新增的 Schema 定义
# SoT Reference: DATA_SCHEMA.md v5.4 §3.5.5, §3.5.6, §3.5.7

class SettlementRuleType(str, Enum):
    """结算规则类型"""
    TIERED = "tiered"    # 阶梯计价
    MARKUP = "markup"    # 加成计价


class BalanceSnapshotSource(str, Enum):
    """余额快照来源"""
    MANUAL = "manual"   # 手工录入
    API = "api"         # API 拉取
    IMPORT = "import"   # 批量导入


class ReconciliationIssueType(str, Enum):
    """对账差异类型"""
    TOPUP_MISMATCH = "topup_mismatch"           # 充值差异
    SPEND_MISMATCH = "spend_mismatch"           # 消耗差异
    DEPOSIT_CHANGE = "deposit_change"           # 押款变化
    BALANCE_ANOMALY = "balance_anomaly"         # 余额异常
    SNAPSHOT_MISSING = "snapshot_missing"       # 快照缺失
    CONSERVATION_FAILED = "conservation_failed" # 守恒校验失败
    OTHER = "other"                             # 其他


class ReconciliationIssueStatus(str, Enum):
    """
    对账差异单状态

    状态流转白名单 (STATE_MACHINE.md §11.4):
    - open -> assigned
    - assigned -> investigating
    - investigating -> resolved, assigned
    - resolved -> closed, investigating
    - closed (终态)
    """
    OPEN = "open"                   # 待处理（初始态）
    ASSIGNED = "assigned"           # 已分配
    INVESTIGATING = "investigating" # 调查中
    RESOLVED = "resolved"           # 已处理
    CLOSED = "closed"               # 已关闭（终态）


class ReconciliationIssueResolutionType(str, Enum):
    """差异单处理类型"""
    DATA_CORRECTION = "data_correction"     # 数据修正
    LEDGER_ADJUSTMENT = "ledger_adjustment" # 账本调整
    EXTERNAL_CONFIRM = "external_confirm"   # 外部确认（代理商/甲方）
    WRITE_OFF = "write_off"                 # 核销
    FALSE_POSITIVE = "false_positive"       # 误报


# ========== 结算规则 Schemas ==========

class SettlementRuleBase(BaseModel):
    """结算规则基础模型"""
    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., max_length=100, description="规则名称")
    rule_type: SettlementRuleType = Field(..., description="规则类型: tiered/markup")
    config: Dict[str, Any] = Field(..., description="规则配置JSON")
    effective_from: date = Field(..., description="生效开始日")
    effective_to: Optional[date] = Field(None, description="生效结束日")


class SettlementRuleCreate(SettlementRuleBase):
    """创建结算规则请求"""

    @field_validator('effective_to')
    @classmethod
    def validate_effective_period(cls, v, info):
        """验证生效期间"""
        if v is not None:
            effective_from = info.data.get('effective_from')
            if effective_from and v <= effective_from:
                raise ValueError('生效结束日必须晚于生效开始日')
        return v

    @field_validator('config')
    @classmethod
    def validate_config(cls, v, info):
        """验证配置格式"""
        rule_type = info.data.get('rule_type')
        if rule_type == SettlementRuleType.TIERED:
            if 'tiers' not in v or not isinstance(v['tiers'], list):
                raise ValueError('阶梯规则必须包含 tiers 数组')
        elif rule_type == SettlementRuleType.MARKUP:
            if 'markup_type' not in v or 'markup_value' not in v:
                raise ValueError('加成规则必须包含 markup_type 和 markup_value')
        return v


class SettlementRuleUpdate(BaseModel):
    """更新结算规则请求"""
    model_config = ConfigDict(from_attributes=True)

    name: Optional[str] = Field(None, max_length=100, description="规则名称")
    config: Optional[Dict[str, Any]] = Field(None, description="规则配置JSON")
    effective_to: Optional[date] = Field(None, description="生效结束日")


class SettlementRuleResponse(SettlementRuleBase):
    """结算规则响应"""
    id: int
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # 计算属性
    is_effective: Optional[bool] = Field(None, description="当前是否生效")


class SettlementRuleListResponse(BaseModel):
    """结算规则列表响应"""
    items: List[SettlementRuleResponse]
    meta: dict


# ========== 余额快照 Schemas ==========

class BalanceSnapshotBase(BaseModel):
    """余额快照基础模型"""
    model_config = ConfigDict(from_attributes=True)

    ad_account_id: int = Field(..., description="广告账户ID")
    snapshot_date: date = Field(..., description="快照日期")
    balance: Decimal = Field(..., ge=0, description="当日余额")
    deposit: Decimal = Field(Decimal("0.00"), ge=0, description="当日押款")
    source: BalanceSnapshotSource = Field(BalanceSnapshotSource.MANUAL, description="数据来源")
    notes: Optional[str] = Field(None, max_length=500, description="备注")


class BalanceSnapshotCreate(BalanceSnapshotBase):
    """创建余额快照请求"""

    @field_validator('snapshot_date')
    @classmethod
    def validate_snapshot_date(cls, v):
        """验证快照日期"""
        if v > date.today():
            raise ValueError('快照日期不能是未来日期')
        return v


class BalanceSnapshotBatchCreate(BaseModel):
    """批量创建余额快照请求"""
    model_config = ConfigDict(from_attributes=True)

    snapshots: List[BalanceSnapshotCreate] = Field(..., min_length=1, description="快照列表")


class BalanceSnapshotResponse(BalanceSnapshotBase):
    """余额快照响应"""
    id: int
    remaining_balance: Decimal = Field(..., description="剩余可用 = balance - deposit")
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None


class BalanceSnapshotListResponse(BaseModel):
    """余额快照列表响应"""
    items: List[BalanceSnapshotResponse]
    meta: dict


# ========== 对账差异单 Schemas ==========

class ReconciliationIssueBase(BaseModel):
    """对账差异单基础模型"""
    model_config = ConfigDict(from_attributes=True)

    reconciliation_batch_id: Optional[int] = Field(None, description="对账批次ID")
    ad_account_id: Optional[int] = Field(None, description="广告账户ID")
    issue_date: date = Field(..., description="差异日期")
    issue_type: ReconciliationIssueType = Field(..., description="差异类型")
    expected_amount: Optional[Decimal] = Field(None, description="预期金额")
    actual_amount: Optional[Decimal] = Field(None, description="实际金额")


class ReconciliationIssueCreate(ReconciliationIssueBase):
    """创建对账差异单请求"""
    attachments: Optional[List[str]] = Field(None, description="附件URL列表")

    @field_validator('issue_date')
    @classmethod
    def validate_issue_date(cls, v):
        """验证差异日期"""
        if v > date.today():
            raise ValueError('差异日期不能是未来日期')
        return v


class ReconciliationIssueAssign(BaseModel):
    """分配差异单请求"""
    model_config = ConfigDict(from_attributes=True)

    assigned_to: str = Field(..., description="分配给用户ID (UUID)")
    sla_deadline: Optional[datetime] = Field(None, description="SLA 截止时间")


class ReconciliationIssueResolve(BaseModel):
    """处理差异单请求"""
    model_config = ConfigDict(from_attributes=True)

    resolution_type: ReconciliationIssueResolutionType = Field(..., description="处理类型")
    resolution_note: Optional[str] = Field(None, max_length=1000, description="处理说明")
    attachments: Optional[List[str]] = Field(None, description="附件URL列表")


class ReconciliationIssueResponse(ReconciliationIssueBase):
    """对账差异单响应"""
    id: int
    difference_amount: Optional[Decimal] = Field(None, description="差异金额 (computed)")
    status: ReconciliationIssueStatus = Field(..., description="状态")
    assigned_to: Optional[str] = None
    assigned_at: Optional[datetime] = None
    resolution_type: Optional[ReconciliationIssueResolutionType] = None
    resolution_note: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    attachments: Optional[List[str]] = None
    sla_deadline: Optional[datetime] = None
    sla_breached: Optional[bool] = Field(False, description="SLA 超时标记")
    created_at: Optional[datetime] = None
    created_by: Optional[str] = None
    updated_at: Optional[datetime] = None

    # 关联数据（可选）
    ad_account_name: Optional[str] = Field(None, description="广告账户名称")
    assignee_name: Optional[str] = Field(None, description="处理人姓名")
    resolver_name: Optional[str] = Field(None, description="处理完成人姓名")


class ReconciliationIssueListResponse(BaseModel):
    """对账差异单列表响应"""
    items: List[ReconciliationIssueResponse]
    meta: dict


class ReconciliationIssueSummary(BaseModel):
    """对账差异单统计摘要"""
    model_config = ConfigDict(from_attributes=True)

    total_issues: int = Field(0, description="总差异单数")
    open_issues: int = Field(0, description="待处理数")
    assigned_issues: int = Field(0, description="已分配数")
    investigating_issues: int = Field(0, description="调查中数")
    resolved_issues: int = Field(0, description="已处理数")
    closed_issues: int = Field(0, description="已关闭数")
    sla_breached_issues: int = Field(0, description="SLA 超时数")
    total_difference_amount: Decimal = Field(Decimal("0.00"), description="总差异金额")
    issues_by_type: Dict[str, int] = Field(default_factory=dict, description="按类型统计")