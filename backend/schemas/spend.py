"""
消耗导入数据模型
Version: 1.0 (Financial SoT Phase 2)
Author: Claude Code

SoT 对齐:
- FINANCIAL_SOT_DESIGN.md v1.0: 消耗事件模型
- DATA_SCHEMA.md v5.3: financial_events 表结构
- STATE_MACHINE.md v2.6: 事件状态机 (raw → pending → confirmed → posted → reversed)
- ERROR_CODES_SOT.md v2.1: BIZ_500-599 导入相关错误码
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict, field_validator

# 从 models 导入标准枚举，避免重复定义
from backend.models.finance.financial_event import EventType, EventStatus, SourceType


# ========== 枚举类型 ==========

class TeamCodeEnum(str, Enum):
    """团队代码枚举"""
    SZ = "SZ"  # 深圳团队
    ZZ = "ZZ"  # 郑州团队


class SpendImportColumnMapping(str, Enum):
    """消耗导入列映射枚举"""
    ACCOUNT_ID = "account_id"
    ACCOUNT_NAME = "account_name"
    TODAY_MAX = "today_max"
    YESTERDAY_MAX = "yesterday_max"
    SPEND = "spend"
    EVENT_DATE = "event_date"


# ========== 请求模型 ==========

class SpendImportRequest(BaseModel):
    """消耗 Excel 导入请求元数据"""
    model_config = ConfigDict(from_attributes=True)

    team_code: TeamCodeEnum = Field(..., description="团队代码 (SZ/ZZ)")
    event_date: Optional[date] = Field(None, description="事件日期 (默认从文件名/数据推断)")
    dry_run: bool = Field(False, description="是否为试运行 (仅验证不导入)")
    skip_duplicates: bool = Field(True, description="跳过重复记录")
    column_mapping: Optional[Dict[str, str]] = Field(
        None,
        description="自定义列名映射 (key=标准列名, value=Excel列名)"
    )

    @field_validator('team_code')
    @classmethod
    def validate_team_code(cls, v):
        """验证团队代码"""
        if isinstance(v, str):
            v = TeamCodeEnum(v.upper())
        return v


class SpendEventCreate(BaseModel):
    """手动创建消耗事件请求"""
    model_config = ConfigDict(from_attributes=True)

    ad_account_id: int = Field(..., gt=0, description="广告账户ID")
    supplier_id: int = Field(..., gt=0, description="供应商ID")
    event_date: date = Field(..., description="事件日期")
    amount: Decimal = Field(..., ge=0, le=Decimal("10000000"), description="消耗金额")
    fee_amount: Optional[Decimal] = Field(None, ge=0, description="手续费 (为空则自动计算)")
    currency: str = Field("USD", max_length=3, description="币种")

    # 扩展数据
    today_max: Optional[Decimal] = Field(None, ge=0, description="当日最大消耗")
    yesterday_max: Optional[Decimal] = Field(None, ge=0, description="前日最大消耗")
    notes: Optional[str] = Field(None, max_length=500, description="备注")

    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v):
        """验证金额精度"""
        if v.as_tuple().exponent < -4:
            raise ValueError('金额最多保留4位小数')
        return v

    @field_validator('event_date')
    @classmethod
    def validate_event_date(cls, v):
        """验证事件日期不能是未来日期"""
        if v > date.today():
            raise ValueError('事件日期不能是未来日期')
        return v


class SpendEventBatchRequest(BaseModel):
    """批量操作消耗事件请求 (基类)"""
    model_config = ConfigDict(from_attributes=True)

    event_ids: List[UUID] = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="事件ID列表 (最多1000条)"
    )
    notes: Optional[str] = Field(None, max_length=500, description="操作备注")


class SpendEventValidateRequest(SpendEventBatchRequest):
    """验证消耗事件请求 (raw → pending)"""
    force: bool = Field(False, description="强制验证 (忽略警告)")


class SpendEventConfirmRequest(SpendEventBatchRequest):
    """确认消耗事件请求 (pending → confirmed)"""
    pass


class SpendEventPostRequest(SpendEventBatchRequest):
    """入账消耗事件请求 (confirmed → posted)"""
    post_date: Optional[date] = Field(None, description="入账日期 (默认为今天)")


class SpendEventReverseRequest(BaseModel):
    """冲正消耗事件请求 (posted → reversed)"""
    model_config = ConfigDict(from_attributes=True)

    event_id: UUID = Field(..., description="事件ID")
    reason: str = Field(..., min_length=5, max_length=500, description="冲正原因")


class SpendEventBatchReverseRequest(BaseModel):
    """批量冲正消耗事件请求 (posted → reversed)"""
    model_config = ConfigDict(from_attributes=True)

    event_ids: List[UUID] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="事件ID列表 (最多100条)"
    )
    reason: str = Field(..., min_length=5, max_length=500, description="冲正原因")


class SpendEventExportRequest(BaseModel):
    """消耗事件导出请求"""
    model_config = ConfigDict(from_attributes=True)

    event_status: Optional[EventStatus] = Field(None, description="事件状态筛选")
    team_id: Optional[UUID] = Field(None, description="团队ID筛选")
    supplier_id: Optional[int] = Field(None, description="供应商ID筛选")
    start_date: Optional[date] = Field(None, description="开始日期")
    end_date: Optional[date] = Field(None, description="结束日期")
    format: str = Field("xlsx", description="导出格式 (xlsx/csv)")


class SpendEventQueryRequest(BaseModel):
    """查询消耗事件请求"""
    model_config = ConfigDict(from_attributes=True)

    event_status: Optional[EventStatus] = Field(None, description="事件状态筛选")
    team_id: Optional[UUID] = Field(None, description="团队ID筛选")
    supplier_id: Optional[int] = Field(None, description="供应商ID筛选")
    ad_account_id: Optional[int] = Field(None, description="广告账户ID筛选")
    start_date: Optional[date] = Field(None, description="开始日期")
    end_date: Optional[date] = Field(None, description="结束日期")
    source_type: Optional[SourceType] = Field(None, description="来源类型筛选")

    # 分页
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页数量")


# ========== 响应模型 - 基础项 ==========

class SpendEventResponse(BaseModel):
    """消耗事件响应"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    event_type: str = EventType.SPEND.value
    event_status: str

    # 来源追溯
    source_type: Optional[str]
    source_ref: Optional[str]
    idempotency_key: str

    # 金额字段
    amount: Decimal
    fee_amount: Decimal
    gross_amount: Optional[Decimal]
    currency: str
    event_date: date

    # 关联实体
    team_id: Optional[UUID]
    team_code: Optional[str] = None
    buyer_id: Optional[UUID]
    buyer_code: Optional[str] = None
    supplier_id: Optional[int]
    supplier_name: Optional[str] = None
    ad_account_id: Optional[int]
    ad_account_name: Optional[str] = None
    project_id: Optional[int]
    project_name: Optional[str] = None

    # 扩展数据 (SPEND 特有)
    today_max: Optional[Decimal] = None
    yesterday_max: Optional[Decimal] = None
    fee_rate: Optional[Decimal] = None

    # 审计字段
    created_by: Optional[UUID]
    created_by_name: Optional[str] = None
    confirmed_by: Optional[UUID]
    confirmed_by_name: Optional[str] = None
    confirmed_at: Optional[datetime]
    posted_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class SpendEventSimple(BaseModel):
    """简化的消耗事件模型 (用于列表)"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    event_status: str
    amount: Decimal
    fee_amount: Decimal
    currency: str
    event_date: date
    ad_account_id: Optional[int]
    ad_account_name: Optional[str] = None
    supplier_name: Optional[str] = None
    created_at: datetime


# ========== 响应模型 - 导入结果 ==========

class ImportRowError(BaseModel):
    """导入行错误"""
    row_number: int = Field(..., description="行号")
    column: Optional[str] = Field(None, description="列名")
    value: Optional[str] = Field(None, description="原始值")
    error_code: str = Field(..., description="错误码")
    error_message: str = Field(..., description="错误信息")


class ImportRowWarning(BaseModel):
    """导入行警告"""
    row_number: int = Field(..., description="行号")
    column: Optional[str] = Field(None, description="列名")
    warning_code: str = Field(..., description="警告码")
    warning_message: str = Field(..., description="警告信息")


class SpendImportResultResponse(BaseModel):
    """消耗导入结果响应"""
    model_config = ConfigDict(from_attributes=True)

    # 导入统计
    total_rows: int = Field(0, description="总行数")
    valid_rows: int = Field(0, description="有效行数")
    invalid_rows: int = Field(0, description="无效行数")
    duplicate_rows: int = Field(0, description="重复行数")
    imported_rows: int = Field(0, description="成功导入行数")
    skipped_rows: int = Field(0, description="跳过行数")

    # 金额统计
    total_amount: Decimal = Field(Decimal("0"), description="总消耗金额")
    total_fee: Decimal = Field(Decimal("0"), description="总手续费")
    total_gross: Decimal = Field(Decimal("0"), description="总含费金额")

    # 错误和警告
    errors: List[ImportRowError] = Field(default_factory=list, description="错误列表")
    warnings: List[ImportRowWarning] = Field(default_factory=list, description="警告列表")

    # 导入的事件ID
    event_ids: List[UUID] = Field(default_factory=list, description="导入的事件ID列表")

    # 元数据
    file_name: Optional[str] = Field(None, description="文件名")
    team_code: Optional[str] = Field(None, description="团队代码")
    import_date: datetime = Field(default_factory=datetime.utcnow, description="导入时间")
    dry_run: bool = Field(False, description="是否为试运行")


# ========== 响应模型 - 验证结果 ==========

class ValidationError(BaseModel):
    """验证错误"""
    event_id: UUID = Field(..., description="事件ID")
    error_code: str = Field(..., description="错误码")
    error_message: str = Field(..., description="错误信息")
    field: Optional[str] = Field(None, description="字段名")


class ValidationWarning(BaseModel):
    """验证警告"""
    event_id: UUID = Field(..., description="事件ID")
    warning_code: str = Field(..., description="警告码")
    warning_message: str = Field(..., description="警告信息")


class SpendEventValidateResponse(BaseModel):
    """验证消耗事件响应"""
    model_config = ConfigDict(from_attributes=True)

    # 验证统计
    total_events: int = Field(0, description="总事件数")
    valid_events: int = Field(0, description="有效事件数")
    invalid_events: int = Field(0, description="无效事件数")
    transitioned_events: int = Field(0, description="状态变更事件数")

    # 错误和警告
    errors: List[ValidationError] = Field(default_factory=list, description="错误列表")
    warnings: List[ValidationWarning] = Field(default_factory=list, description="警告列表")

    # 结果
    success: bool = Field(..., description="验证是否成功")
    message: str = Field(..., description="结果消息")


# ========== 响应模型 - 确认/入账结果 ==========

class SpendEventBatchResponse(BaseModel):
    """批量操作消耗事件响应 (基类)"""
    model_config = ConfigDict(from_attributes=True)

    total_events: int = Field(0, description="总事件数")
    success_events: int = Field(0, description="成功事件数")
    failed_events: int = Field(0, description="失败事件数")

    # 失败详情
    failed_details: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="失败详情 [{event_id, error_code, error_message}]"
    )

    success: bool = Field(..., description="操作是否成功")
    message: str = Field(..., description="结果消息")


class SpendEventConfirmResponse(SpendEventBatchResponse):
    """确认消耗事件响应"""
    confirmed_at: datetime = Field(default_factory=datetime.utcnow, description="确认时间")


class SpendEventPostResponse(SpendEventBatchResponse):
    """入账消耗事件响应"""
    posted_at: datetime = Field(default_factory=datetime.utcnow, description="入账时间")
    ledger_entries_created: int = Field(0, description="创建的分录数")
    total_amount: Decimal = Field(Decimal("0"), description="总入账金额")


class SpendEventReverseResponse(BaseModel):
    """冲正消耗事件响应"""
    model_config = ConfigDict(from_attributes=True)

    event_id: UUID
    original_amount: Decimal
    reversed_at: datetime
    reversal_ledger_entries: int = Field(0, description="冲正分录数")
    reason: str
    success: bool
    message: str


class SpendEventBatchReverseResponse(BaseModel):
    """批量冲正消耗事件响应"""
    model_config = ConfigDict(from_attributes=True)

    total_events: int = Field(0, description="总事件数")
    success_events: int = Field(0, description="成功冲正数")
    failed_events: int = Field(0, description="失败冲正数")

    # 金额统计
    total_reversed_amount: Decimal = Field(Decimal("0"), description="总冲正金额")
    reversal_ledger_entries: int = Field(0, description="冲正分录数")

    # 失败详情
    failed_details: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="失败详情 [{event_id, error_code, error_message}]"
    )

    # 结果
    reversed_at: datetime = Field(default_factory=datetime.utcnow, description="冲正时间")
    reason: str = Field(..., description="冲正原因")
    success: bool = Field(..., description="操作是否成功")
    message: str = Field(..., description="结果消息")


class SpendTemplateResponse(BaseModel):
    """消耗导入模板响应"""
    model_config = ConfigDict(from_attributes=True)

    file_name: str = Field(..., description="文件名")
    file_content: str = Field(..., description="Base64 编码的文件内容")
    columns: List[str] = Field(..., description="模板列名")
    sample_data: List[Dict[str, Any]] = Field(default_factory=list, description="示例数据")


# ========== 响应模型 - 列表 ==========

class SpendEventListResponse(BaseModel):
    """消耗事件列表响应"""
    model_config = ConfigDict(from_attributes=True)

    items: List[SpendEventResponse] = Field(default_factory=list, description="事件列表")
    meta: Dict[str, Any] = Field(default_factory=dict, description="分页元数据")


class SpendEventListMeta(BaseModel):
    """列表分页元数据"""
    total: int = Field(0, description="总数")
    page: int = Field(1, description="当前页")
    page_size: int = Field(20, description="每页数量")
    total_pages: int = Field(0, description="总页数")


# ========== 响应模型 - 统计 ==========

class SpendStatisticsResponse(BaseModel):
    """消耗统计响应"""
    model_config = ConfigDict(from_attributes=True)

    # 总体统计
    total_events: int = Field(0, description="总事件数")
    raw_events: int = Field(0, description="原始状态数")
    pending_events: int = Field(0, description="待确认数")
    confirmed_events: int = Field(0, description="已确认数")
    posted_events: int = Field(0, description="已入账数")
    reversed_events: int = Field(0, description="已冲正数")

    # 金额统计
    total_amount: Decimal = Field(Decimal("0"), description="总消耗金额")
    total_fee: Decimal = Field(Decimal("0"), description="总手续费")
    total_gross: Decimal = Field(Decimal("0"), description="总含费金额")
    posted_amount: Decimal = Field(Decimal("0"), description="已入账金额")

    # 日期范围
    earliest_date: Optional[date] = Field(None, description="最早日期")
    latest_date: Optional[date] = Field(None, description="最近日期")

    # 按团队统计
    by_team: List[Dict[str, Any]] = Field(default_factory=list, description="按团队统计")

    # 按供应商统计
    by_supplier: List[Dict[str, Any]] = Field(default_factory=list, description="按供应商统计")


# ========== 导出模型 ==========

class SpendEventExport(BaseModel):
    """消耗事件导出模型"""
    model_config = ConfigDict(from_attributes=True)

    event_date: date
    team_code: Optional[str]
    supplier_name: Optional[str]
    ad_account_id: Optional[int]
    ad_account_name: Optional[str]
    amount: Decimal
    fee_amount: Decimal
    gross_amount: Optional[Decimal]
    currency: str
    event_status: str
    created_at: datetime
    confirmed_at: Optional[datetime]
    posted_at: Optional[datetime]
