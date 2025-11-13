"""
对账管理数据模型
Version: 1.0
Author: Claude协作开发
"""

from datetime import date, datetime
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
    """调整类型枚举"""
    SPEND_ADJUSTMENT = "spend_adjustment"
    DATE_ADJUSTMENT = "date_adjustment"


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
    """创建调整记录请求"""
    model_config = ConfigDict(from_attributes=True)

    adjustment_type: str = Field(..., pattern="^(spend_adjustment|date_adjustment)$", description="调整类型")
    original_amount: Decimal = Field(..., decimal_places=2, description="原始金额")
    adjustment_amount: Decimal = Field(..., decimal_places=2, description="调整金额")
    adjustment_reason: str = Field(..., max_length=100, description="调整原因")
    detailed_reason: str = Field(..., min_length=1, max_length=1000, description="详细原因说明")
    evidence_url: Optional[str] = Field(None, max_length=500, description="证据文件URL")
    notes: Optional[str] = Field(None, max_length=1000, description="备注")

    @field_validator('adjustment_amount')
    @classmethod
    def validate_adjustment_amount(cls, v):
        """验证调整金额格式"""
        if v.as_tuple().exponent < -2:
            raise ValueError('调整金额最多保留2位小数')
        return v

    @field_validator('adjusted_amount')
    @classmethod
    def validate_adjusted_amount(cls, v, info):
        """确保调整后金额正确"""
        if v is not None:
            original = info.data.get('original_amount', Decimal('0'))
            adjustment = info.data.get('adjustment_amount', Decimal('0'))
            calculated = original + adjustment
            if abs(calculated - v) > Decimal('0.01'):
                raise ValueError(f'调整后金额应为{calculated}，不是{v}')
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
    """对账批次响应"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    batch_no: str
    reconciliation_date: date
    status: str
    total_accounts: int
    matched_accounts: int
    mismatched_accounts: int
    total_platform_spend: Decimal
    total_internal_spend: Decimal
    total_difference: Decimal
    auto_matched: int
    manual_reviewed: int
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_by: int
    created_by_name: str
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    # 添加辅助字段
    match_rate: Optional[float] = Field(None, description="匹配率百分比")
    difference_rate: Optional[float] = Field(None, description="差异率百分比")
    processing_duration: Optional[float] = Field(None, description="处理时长(小时)")


class ReconciliationBatchListResponse(BaseModel):
    """对账批次列表响应"""
    items: List[ReconciliationBatchResponse]
    meta: dict


class ReconciliationDetailResponse(BaseModel):
    """对账详情响应"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    batch_id: int
    ad_account_id: int
    ad_account_name: str
    project_id: int
    project_name: str
    channel_id: int
    channel_name: str

    # 平台数据
    platform_spend: Decimal
    platform_currency: str
    platform_data_date: Optional[date]

    # 内部数据
    internal_spend: Decimal
    internal_currency: str
    internal_data_date: Optional[date]

    # 差异信息
    spend_difference: Decimal
    exchange_rate: Decimal
    percentage_difference: Optional[float] = Field(None, description="差异百分比")
    is_matched: bool
    match_status: str
    difference_type: Optional[str]
    difference_reason: Optional[str]
    auto_confidence: Decimal

    # 审核信息
    reviewed_by: Optional[int]
    reviewed_by_name: Optional[str]
    reviewed_at: Optional[datetime]
    review_notes: Optional[str]
    resolved_by: Optional[int]
    resolved_by_name: Optional[str]
    resolved_at: Optional[datetime]
    resolution_method: Optional[str]
    resolution_notes: Optional[str]

    created_at: datetime
    updated_at: datetime


class ReconciliationDetailListResponse(BaseModel):
    """对账详情列表响应"""
    items: List[ReconciliationDetailResponse]
    meta: dict


class ReconciliationAdjustmentResponse(BaseModel):
    """调整记录响应"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    detail_id: int
    batch_id: int
    adjustment_type: str
    original_amount: Decimal
    adjustment_amount: Decimal
    adjusted_amount: Decimal
    adjustment_reason: str
    detailed_reason: str
    evidence_url: Optional[str]
    approved_by: int
    approved_by_name: str
    approved_at: datetime
    finance_approved: bool
    finance_approved_by: Optional[int]
    finance_approved_by_name: Optional[str]
    finance_approved_at: Optional[datetime]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime


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
    """对账报告响应"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    batch_id: Optional[int]
    report_type: str
    report_period_start: date
    report_period_end: date
    report_data: Dict[str, Any]
    chart_data: Optional[Dict[str, Any]]
    summary_data: Dict[str, Any]
    file_path: Optional[str]
    generated_by: int
    generated_by_name: str
    generated_at: datetime
    file_size: Optional[int] = None  # 文件大小（字节）


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