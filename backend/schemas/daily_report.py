"""
日报管理相关的Pydantic模型
Version: 1.0
Author: Claude协作开发
"""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field, ConfigDict, field_validator, computed_field

from backend.schemas.response import PaginationMeta, DateRange


class DailyReportCreateRequest(BaseModel):
    """
    日报创建请求 - 对齐 API_SOT.md v9.0 第 9.2 节

    字段命名遵循 SoT 三数据流规范:
    - conversions_raw / raw_spend: raw 数据流（投手提交）
    - real_spend: real 数据流（运营录入）
    - conversions_final: final 数据流（运营确认）
    """
    model_config = ConfigDict(from_attributes=True)

    # 必填字段
    report_date: date = Field(..., description="报表日期（≤今天）")
    ad_account_id: int = Field(..., gt=0, description="广告账户ID")
    conversions_raw: int = Field(..., ge=0, description="原始粉数（raw数据流）")
    raw_spend: Decimal = Field(..., ge=0, description="原始消耗（raw数据流）DECIMAL(15,2)")

    # 可选字段
    campaign_name: Optional[str] = Field(None, max_length=200, description="广告系列名称")
    ad_group_name: Optional[str] = Field(None, max_length=200, description="广告组名称")
    ad_creative_name: Optional[str] = Field(None, max_length=200, description="广告创意名称")
    impressions: int = Field(0, ge=0, description="展示次数/曝光量")
    clicks: int = Field(0, ge=0, description="点击次数")
    notes: Optional[str] = Field(None, max_length=1000, description="备注说明")

    # NOTE: 报表日期验证（BIZ_201）移至 service 层，以返回正确的 HTTP 状态码和错误码
    # Pydantic 验证会返回 422，而业务规则要求返回 400 + BIZ_201

    @field_validator('clicks')
    def validate_clicks_vs_impressions(cls, v, info):
        """验证点击次数不能大于展示次数"""
        if 'impressions' in info.data and info.data['impressions'] is not None:
            if v > info.data['impressions']:
                raise ValueError('点击次数不能大于展示次数')
        return v


class DailyReportUpdateRequest(BaseModel):
    """日报更新请求 - 仅允许更新 raw 数据流字段"""
    model_config = ConfigDict(from_attributes=True)

    campaign_name: Optional[str] = Field(None, max_length=200)
    ad_group_name: Optional[str] = Field(None, max_length=200)
    ad_creative_name: Optional[str] = Field(None, max_length=200)
    impressions: Optional[int] = Field(None, ge=0)
    clicks: Optional[int] = Field(None, ge=0)
    conversions_raw: Optional[int] = Field(None, ge=0, description="原始粉数（raw数据流）")
    raw_spend: Optional[Decimal] = Field(None, ge=0, description="原始消耗（raw数据流）")
    notes: Optional[str] = Field(None, max_length=1000)

    @field_validator('clicks')
    def validate_clicks_vs_impressions(cls, v, info):
        """验证点击次数不能大于展示次数"""
        if v is not None and 'impressions' in info.data and info.data['impressions'] is not None:
            if v > info.data['impressions']:
                raise ValueError('点击次数不能大于展示次数')
        return v


class RealSpendRequest(BaseModel):
    """
    录入 real 消耗请求 - API_SOT.md v9.0 第 9.5 节

    PUT /api/v1/daily-reports/{report_id}/real-spend
    """
    model_config = ConfigDict(from_attributes=True)

    real_spend: Decimal = Field(..., ge=0, description="真实消耗（从供应商后台获取）")
    fee: Decimal = Field(Decimal("0.00"), ge=0, description="手续费（默认0.00）")


class DailyReportAuditRequest(BaseModel):
    """日报审核请求"""
    model_config = ConfigDict(from_attributes=True)

    audit_notes: Optional[str] = Field(None, max_length=500, description="审核说明")


class DailyReportBatchImportRequest(BaseModel):
    """批量导入日报请求"""
    model_config = ConfigDict(from_attributes=True)

    reports: List[DailyReportCreateRequest] = Field(..., max_items=100, description="日报列表")
    skip_errors: bool = Field(False, description="是否跳过错误继续导入")


class DailyReportQueryParams(BaseModel):
    """日报查询参数"""
    model_config = ConfigDict(from_attributes=True)

    report_date_start: Optional[date] = Field(None, description="开始日期")
    report_date_end: Optional[date] = Field(None, description="结束日期")
    ad_account_id: Optional[int] = Field(None, gt=0, description="广告账户ID")
    status: Optional[str] = Field(None, pattern="^(pending|approved|rejected)$", description="审核状态")
    media_buyer_id: Optional[int] = Field(None, gt=0, description="投手ID")
    project_id: Optional[int] = Field(None, gt=0, description="项目ID")

    @field_validator('report_date_end')
    def validate_date_range(cls, v, info):
        """验证日期范围"""
        if v and 'report_date_start' in info.data and info.data['report_date_start']:
            if v < info.data['report_date_start']:
                raise ValueError('结束日期不能小于开始日期')
        return v


class DailyReportResponse(BaseModel):
    """
    日报响应 - 对齐 API_SOT.md v9.0 第 9.2 节 Response Schema

    包含三数据流字段:
    - conversions_raw / raw_spend: raw 数据流
    - real_spend: real 数据流
    - conversions_final: final 数据流
    """
    model_config = ConfigDict(from_attributes=True)

    # 基础字段
    id: int
    report_date: date
    ad_account_id: int
    status: str  # 8状态机状态

    # 聚合字段（可选，JOIN 查询时填充）
    ad_account_name: Optional[str] = None
    project_id: Optional[int] = None
    project_name: Optional[str] = None

    # 广告信息
    campaign_name: Optional[str] = None
    ad_group_name: Optional[str] = None
    ad_creative_name: Optional[str] = None

    # 指标字段
    impressions: int = 0
    clicks: int = 0

    # 三数据流字段
    conversions_raw: int = 0  # raw 数据流 - 原始粉数
    raw_spend: Decimal = Decimal("0.00")  # raw 数据流 - 原始消耗
    real_spend: Decimal = Decimal("0.00")  # real 数据流 - 真实消耗
    fee: Decimal = Decimal("0.00")  # 手续费
    conversions_final: int = 0  # final 数据流 - 最终粉数

    # 计费字段
    unit_price: Optional[Decimal] = None

    # 趋势风控字段
    trend_flag: Optional[str] = "normal"
    trend_flag_reason: Optional[str] = None
    trend_resolution_note: Optional[str] = None

    # 备注
    notes: Optional[str] = None

    # 用户信息
    created_by: Optional[str] = None  # UUID
    created_by_name: Optional[str] = None

    # 时间戳
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @computed_field
    @property
    def ctr(self) -> Decimal:
        """计算点击率"""
        if self.impressions == 0:
            return Decimal('0')
        return Decimal(self.clicks) / Decimal(self.impressions) * 100

    @computed_field
    @property
    def cpc(self) -> Optional[Decimal]:
        """计算单次点击成本"""
        if self.clicks == 0:
            return None
        return self.raw_spend / Decimal(self.clicks)

    @computed_field
    @property
    def conversion_rate(self) -> Decimal:
        """计算转化率"""
        if self.clicks == 0:
            return Decimal('0')
        return Decimal(self.conversions_raw) / Decimal(self.clicks) * 100


class DailyReportListResponse(BaseModel):
    """日报列表响应"""
    items: List[DailyReportResponse]
    meta: PaginationMeta


class DailyReportStatisticsResponse(BaseModel):
    """日报统计响应"""
    model_config = ConfigDict(from_attributes=True)

    date_range: DateRange
    total_reports: int
    approved_reports: int
    rejected_reports: int
    pending_reports: int
    total_spend: Decimal
    total_impressions: int
    total_clicks: int
    total_conversions: int
    total_new_follows: int
    avg_cpa: Optional[Decimal]
    avg_roas: Optional[Decimal]

    @computed_field
    @property
    def ctr(self) -> Decimal:
        """计算整体点击率"""
        if self.total_impressions == 0:
            return Decimal('0')
        return Decimal(self.total_clicks) / Decimal(self.total_impressions) * 100

    @computed_field
    @property
    def conversion_rate(self) -> Decimal:
        """计算整体转化率"""
        if self.total_clicks == 0:
            return Decimal('0')
        return Decimal(self.total_conversions) / Decimal(self.total_clicks) * 100

    @computed_field
    @property
    def cpc(self) -> Optional[Decimal]:
        """计算平均单次点击成本"""
        if self.total_clicks == 0:
            return None
        return self.total_spend / Decimal(self.total_clicks)


class DailyReportExportResponse(BaseModel):
    """日报导出响应"""
    model_config = ConfigDict(from_attributes=True)

    file_name: str
    file_size: int
    download_url: str
    export_time: datetime
    file_type: str = Field("xlsx", description="文件类型")


# 批量导入错误响应
class DailyReportImportError(BaseModel):
    """导入错误详情"""
    model_config = ConfigDict(from_attributes=True)

    row_number: int = Field(..., description="错误所在行号")
    error_code: str = Field(..., description="错误码")
    error_message: str = Field(..., description="错误描述")
    field_name: Optional[str] = Field(None, description="出错的字段名")
    invalid_value: Optional[str] = Field(None, description="无效的值")
    suggestion: Optional[str] = Field(None, description="修复建议")
    invalid_data: Optional[dict] = Field(None, description="整行无效数据")


class DailyReportBatchImportResponse(BaseModel):
    """批量导入响应"""
    model_config = ConfigDict(from_attributes=True)

    total_count: int
    success_count: int
    error_count: int
    errors: List[DailyReportImportError]
    imported_ids: List[int]
    processing_time_seconds: float


# 审核日志响应
class DailyReportAuditLogResponse(BaseModel):
    """审核日志响应"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    daily_report_id: int
    action: str  # created, updated, approved, rejected
    old_status: Optional[str]
    new_status: Optional[str]
    audit_user_id: int
    audit_user_name: str
    audit_time: datetime
    audit_notes: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]