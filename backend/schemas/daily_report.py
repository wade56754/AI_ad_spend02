"""
日报管理相关的Pydantic模型
Version: 1.0
Author: Claude协作开发
"""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field, ConfigDict, field_validator, computed_field

from schemas.response import PaginationMeta, DateRange


class DailyReportCreateRequest(BaseModel):
    """日报创建请求"""
    model_config = ConfigDict(from_attributes=True)

    report_date: date = Field(..., description="报表日期")
    ad_account_id: int = Field(..., gt=0, description="广告账户ID")
    campaign_name: Optional[str] = Field(None, max_length=200, description="广告系列名称")
    ad_group_name: Optional[str] = Field(None, max_length=200, description="广告组名称")
    ad_creative_name: Optional[str] = Field(None, max_length=200, description="广告创意名称")
    impressions: int = Field(0, ge=0, description="展示次数")
    clicks: int = Field(0, ge=0, description="点击次数")
    spend: Decimal = Field(0, ge=0, decimal_places=2, description="消耗金额")
    conversions: int = Field(0, ge=0, description="转化次数")
    new_follows: int = Field(0, ge=0, description="新增粉丝数")
    cpa: Optional[Decimal] = Field(None, ge=0, decimal_places=2, description="CPA")
    roas: Optional[Decimal] = Field(None, ge=0, decimal_places=2, description="ROAS")
    notes: Optional[str] = Field(None, max_length=1000, description="备注说明")

    @field_validator('report_date')
    def validate_report_date(cls, v):
        """验证报表日期"""
        from datetime import timedelta
        if v > date.today():
            raise ValueError('报表日期不能是未来日期')
        # 允许修改过去30天的数据
        if v < date.today() - timedelta(days=30):
            raise ValueError('报表日期不能超过30天前')
        return v

    @field_validator('clicks')
    def validate_clicks_vs_impressions(cls, v, info):
        """验证点击次数不能大于展示次数"""
        if 'impressions' in info.data and v > info.data['impressions']:
            raise ValueError('点击次数不能大于展示次数')
        return v

    @field_validator('conversions')
    def validate_conversions_vs_clicks(cls, v, info):
        """验证转化次数不能大于点击次数"""
        if 'clicks' in info.data and v > info.data['clicks']:
            raise ValueError('转化次数不能大于点击次数')
        return v


class DailyReportUpdateRequest(BaseModel):
    """日报更新请求"""
    model_config = ConfigDict(from_attributes=True)

    campaign_name: Optional[str] = Field(None, max_length=200)
    ad_group_name: Optional[str] = Field(None, max_length=200)
    ad_creative_name: Optional[str] = Field(None, max_length=200)
    impressions: Optional[int] = Field(None, ge=0)
    clicks: Optional[int] = Field(None, ge=0)
    spend: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    conversions: Optional[int] = Field(None, ge=0)
    new_follows: Optional[int] = Field(None, ge=0)
    cpa: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    roas: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    notes: Optional[str] = Field(None, max_length=1000)

    @field_validator('clicks')
    def validate_clicks_vs_impressions(cls, v, info):
        """验证点击次数不能大于展示次数"""
        if v is not None and 'impressions' in info.data and info.data['impressions'] is not None:
            if v > info.data['impressions']:
                raise ValueError('点击次数不能大于展示次数')
        return v

    @field_validator('conversions')
    def validate_conversions_vs_clicks(cls, v, info):
        """验证转化次数不能大于点击次数"""
        if v is not None and 'clicks' in info.data and info.data['clicks'] is not None:
            if v > info.data['clicks']:
                raise ValueError('转化次数不能大于点击次数')
        return v


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
    """日报响应"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    report_date: date
    ad_account_id: int
    ad_account_name: str
    ad_account_number: str
    campaign_name: Optional[str]
    ad_group_name: Optional[str]
    ad_creative_name: Optional[str]
    impressions: int
    clicks: int
    spend: Decimal
    conversions: int
    new_follows: int
    cpa: Optional[Decimal]
    roas: Optional[Decimal]
    status: str  # pending, approved, rejected
    notes: Optional[str]
    audit_notes: Optional[str]
    audit_user_id: Optional[int]
    audit_user_name: Optional[str]
    audit_time: Optional[datetime]
    created_by: int
    created_by_name: str
    created_at: datetime
    updated_at: datetime

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
        return self.spend / Decimal(self.clicks)

    @computed_field
    @property
    def conversion_rate(self) -> Decimal:
        """计算转化率"""
        if self.clicks == 0:
            return Decimal('0')
        return Decimal(self.conversions) / Decimal(self.clicks) * 100


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
    ctr: Decimal  # Overall click-through rate
    conversion_rate: Decimal  # Overall conversion rate
    cpc: Optional[Decimal]  # Cost per click

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

    row_number: int
    error_code: str
    error_message: str
    invalid_data: Optional[dict] = None


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