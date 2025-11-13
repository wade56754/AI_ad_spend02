"""
充值管理数据模型
Version: 1.0
Author: Claude协作开发
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict, field_validator


class TopupUrgencyLevel(str, Enum):
    """充值紧急程度枚举"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class TopupStatus(str, Enum):
    """充值状态枚举"""
    PENDING = "pending"
    DATA_REVIEW = "data_review"
    FINANCE_APPROVE = "finance_approve"
    REJECTED = "rejected"
    PAID = "paid"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class PaymentMethod(str, Enum):
    """支付方式枚举"""
    BANK_TRANSFER = "bank_transfer"
    ALIPAY = "alipay"
    WECHAT = "wechat"
    PAYPAL = "paypal"
    CREDIT_CARD = "credit_card"
    OTHER = "other"


# ========== 请求模型 ==========

class TopupRequestCreate(BaseModel):
    """创建充值申请请求"""
    model_config = ConfigDict(from_attributes=True)

    ad_account_id: int = Field(..., gt=0, description="广告账户ID")
    requested_amount: Decimal = Field(..., gt=0, le=100000, description="申请金额(单笔上限10万)")
    currency: str = Field("USD", max_length=10, description="货币类型")
    urgency_level: TopupUrgencyLevel = Field(TopupUrgencyLevel.NORMAL, description="紧急程度")
    reason: str = Field(..., min_length=1, max_length=1000, description="充值原因")
    notes: Optional[str] = Field(None, max_length=1000, description="补充说明")
    expected_date: Optional[date] = Field(None, description="期望到账日期")

    @field_validator('expected_date')
    @classmethod
    def validate_expected_date(cls, v):
        """验证期望日期不能早于明天"""
        if v:
            from datetime import datetime, timedelta
            tomorrow = (datetime.now() + timedelta(days=1)).date()
            if v < tomorrow:
                raise ValueError('期望到账日期最早为明天')
        return v

    @field_validator('requested_amount')
    @classmethod
    def validate_amount(cls, v):
        """验证金额格式"""
        if v.as_tuple().exponent < -2:
            raise ValueError('金额最多保留2位小数')
        return v


class TopupDataReviewRequest(BaseModel):
    """数据员审核请求"""
    model_config = ConfigDict(from_attributes=True)

    action: str = Field(..., pattern="^(approve|reject)$", description="审核动作：approve或reject")
    notes: Optional[str] = Field(None, max_length=1000, description="审核说明")


class TopupFinanceApprovalRequest(BaseModel):
    """财务审批请求"""
    model_config = ConfigDict(from_attributes=True)

    action: str = Field(..., pattern="^(approve|reject)$", description="审批动作：approve或reject")
    actual_amount: Optional[Decimal] = Field(None, gt=0, le=100000, description="实际打款金额")
    payment_method: Optional[PaymentMethod] = Field(None, description="打款方式")
    notes: Optional[str] = Field(None, max_length=1000, description="审批说明")

    @field_validator('actual_amount')
    @classmethod
    def validate_actual_amount(cls, v, info):
        """如果审批通过，实际金额不能为空"""
        if info.data.get('action') == 'approve' and v is None:
            raise ValueError('审批通过时必须填写实际打款金额')
        return v


class TopupMarkPaidRequest(BaseModel):
    """标记已打款请求"""
    model_config = ConfigDict(from_attributes=True)

    transaction_id: Optional[str] = Field(None, max_length=100, description="交易流水号")
    notes: Optional[str] = Field(None, max_length=1000, description="备注")


class TopupReceiptUploadRequest(BaseModel):
    """上传打款凭证请求"""
    model_config = ConfigDict(from_attributes=True)

    receipt_url: str = Field(..., max_length=500, description="凭证文件URL")
    transaction_id: Optional[str] = Field(None, max_length=100, description="交易流水号")
    notes: Optional[str] = Field(None, max_length=1000, description="备注")


# ========== 响应模型 ==========

class TopupRequestResponse(BaseModel):
    """充值申请响应"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    request_no: str
    ad_account_id: int
    ad_account_name: str
    project_id: int
    project_name: str
    requested_amount: Decimal
    actual_amount: Optional[Decimal]
    currency: str
    urgency_level: str
    reason: str
    notes: Optional[str]
    status: str
    requested_by: int
    requested_by_name: str
    data_reviewed_by: Optional[int]
    data_reviewed_by_name: Optional[str]
    data_reviewed_at: Optional[datetime]
    data_review_notes: Optional[str]
    finance_approved_by: Optional[int]
    finance_approved_by_name: Optional[str]
    finance_approved_at: Optional[datetime]
    finance_approve_notes: Optional[str]
    paid_at: Optional[datetime]
    completed_at: Optional[datetime]
    expected_date: Optional[date]
    payment_method: Optional[str]
    transaction_id: Optional[str]
    receipt_url: Optional[str]
    created_at: datetime
    updated_at: datetime


class TopupRequestListResponse(BaseModel):
    """充值申请列表响应"""
    items: List[TopupRequestResponse]
    meta: dict


class TopupTransactionResponse(BaseModel):
    """充值交易响应"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    request_id: int
    request_no: str
    transaction_no: str
    amount: Decimal
    currency: str
    payment_method: str
    payment_account: Optional[str]
    transaction_date: datetime
    receipt_file: Optional[str]
    notes: Optional[str]
    created_by: int
    created_by_name: str
    created_at: datetime


class TopupApprovalLogResponse(BaseModel):
    """审批日志响应"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    request_id: int
    action: str
    actor_id: int
    actor_name: str
    actor_role: str
    notes: Optional[str]
    previous_status: Optional[str]
    new_status: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    created_at: datetime


class TopupStatisticsResponse(BaseModel):
    """充值统计响应"""
    model_config = ConfigDict(from_attributes=True)

    # 总体统计
    total_requests: int = Field(0, description="总申请数")
    pending_requests: int = Field(0, description="待审核数")
    data_review_requests: int = Field(0, description="数据审核中数")
    finance_approve_requests: int = Field(0, description="财务审批中数")
    approved_requests: int = Field(0, description="已批准数")
    paid_requests: int = Field(0, description="已打款数")
    completed_requests: int = Field(0, description="已完成数")
    rejected_requests: int = Field(0, description="已拒绝数")

    # 金额统计
    total_amount_requested: Decimal = Field(0, description="申请总金额")
    total_amount_approved: Decimal = Field(0, description="批准总金额")
    total_amount_paid: Decimal = Field(0, description="实付总金额")

    # 效率统计
    avg_processing_time_hours: float = Field(0, description="平均处理时间(小时)")
    avg_data_review_time_hours: float = Field(0, description="数据审核平均时间")
    avg_finance_approval_time_hours: float = Field(0, description="财务审批平均时间")
    success_rate: float = Field(0, description="成功率(百分比)")

    # 紧急程度统计
    urgent_requests: int = Field(0, description="紧急申请数")
    high_requests: int = Field(0, description="高优先级申请数")
    overdue_requests: int = Field(0, description="逾期未处理数")

    # 趋势数据
    monthly_stats: List[dict] = Field(default_factory=list, description="月度统计")
    top_projects: List[dict] = Field(default_factory=list, description="充值金额TOP5项目")
    top_accounts: List[dict] = Field(default_factory=list, description="充值频次TOP5账户")


class TopupDashboardResponse(BaseModel):
    """充值仪表板响应"""
    model_config = ConfigDict(from_attributes=True)

    # 待办事项
    pending_reviews: int = Field(0, description="待数据审核")
    pending_approvals: int = Field(0, description="待财务审批")
    pending_payments: int = Field(0, description="待打款")
    overdue_items: int = Field(0, description="逾期项")

    # 今日数据
    today_requests: int = Field(0, description="今日申请数")
    today_amount: Decimal = Field(0, description="今日申请金额")
    today_completed: int = Field(0, description="今日完成数")

    # 本月数据
    month_requests: int = Field(0, description="本月申请数")
    month_amount: Decimal = Field(0, description="本月申请金额")
    month_completed: int = Field(0, description="本月完成数")

    # 近期申请
    recent_requests: List[TopupRequestResponse] = Field(default_factory=list)

    # 统计摘要
    statistics: TopupStatisticsResponse


# ========== 简化模型 ==========

class TopupRequestSimple(BaseModel):
    """简化的充值申请模型（用于下拉列表等）"""
    id: int
    request_no: str
    ad_account_name: str
    requested_amount: Decimal
    currency: str
    status: str
    urgency_level: str
    created_at: datetime


class AdAccountBalance(BaseModel):
    """账户余额模型"""
    ad_account_id: int
    ad_account_name: str
    current_balance: Decimal
    currency: str
    max_balance: Decimal
    available_topup: Decimal  # 可充值金额


class TopupRequestExport(BaseModel):
    """充值申请导出模型"""
    model_config = ConfigDict(from_attributes=True)

    request_no: str
    project_name: str
    ad_account_name: str
    requested_amount: Decimal
    actual_amount: Optional[Decimal]
    currency: str
    status: str
    urgency_level: str
    requested_by_name: str
    data_reviewed_by_name: Optional[str]
    finance_approved_by_name: Optional[str]
    created_at: datetime
    data_reviewed_at: Optional[datetime]
    finance_approved_at: Optional[datetime]
    paid_at: Optional[datetime]
    completed_at: Optional[datetime]
    payment_method: Optional[str]
    transaction_id: Optional[str]