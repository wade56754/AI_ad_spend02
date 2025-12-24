"""
AdSpend Schemas - 外部消耗数据导入 (重构版)

SoT References:
- DATA_SCHEMA.md v5.3 (ad_spend_daily 表)
- API_SOT.md v9.3 (消耗数据 API)

依赖代码块:
- pagination: PaginationMeta
- response-envelope: 标准响应格式

Version: 2.0
Author: Claude Code
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List, Any, Dict
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict, field_validator


# ============ 基础模型 ============

class AdSpendBase(BaseModel):
    """AdSpend 基础字段"""
    source_platform: str = Field(..., min_length=1, max_length=50, 
                                 description="数据来源平台: facebook/google/tiktok/manual")
    ad_account_code: str = Field(..., min_length=1, max_length=100,
                                description="广告账户外部代码")
    spend_date: date = Field(..., description="消耗日期")
    spend_amount: Decimal = Field(default=Decimal("0.00"), ge=0, 
                                  description="消耗金额")
    currency: str = Field(default="CNY", max_length=10, 
                         description="货币代码: CNY/USD/HKD")
    impressions: int = Field(default=0, ge=0, description="曝光量")
    clicks: int = Field(default=0, ge=0, description="点击量")
    conversions: int = Field(default=0, ge=0, description="转化数")


# ============ 请求模型 ============

class AdSpendCreateRequest(AdSpendBase):
    """创建单条消耗记录"""
    ad_account_id: Optional[int] = Field(None, description="关联的内部广告账户ID")
    raw_payload: Optional[Dict[str, Any]] = Field(None, description="原始导入数据")


class AdSpendBatchImportRequest(BaseModel):
    """批量导入消耗数据"""
    records: List[AdSpendCreateRequest] = Field(..., min_length=1, max_length=1000,
                                                description="消耗记录列表 (最多1000条)")
    skip_errors: bool = Field(default=True, description="是否跳过错误继续导入")
    source: str = Field(default="api", description="导入来源: api/csv/manual")


class AdSpendQueryParams(BaseModel):
    """查询参数"""
    model_config = ConfigDict(extra="ignore")
    
    spend_date_start: Optional[date] = Field(None, description="开始日期")
    spend_date_end: Optional[date] = Field(None, description="结束日期")
    source_platform: Optional[str] = Field(None, description="平台筛选")
    ad_account_code: Optional[str] = Field(None, description="账户代码筛选")
    ad_account_id: Optional[int] = Field(None, description="内部账户ID筛选")
    currency: Optional[str] = Field(None, description="货币筛选")
    min_amount: Optional[Decimal] = Field(None, ge=0, description="最小金额")
    max_amount: Optional[Decimal] = Field(None, ge=0, description="最大金额")


# ============ 响应模型 ============

class AdSpendResponse(BaseModel):
    """单条消耗记录响应"""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    source_platform: str
    ad_account_code: str
    ad_account_id: Optional[int] = None
    spend_date: date
    spend_amount: Decimal
    currency: str
    impressions: int
    clicks: int
    conversions: int
    raw_payload: Optional[Dict[str, Any]] = None
    imported_by: Optional[UUID] = None
    imported_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    
    # 计算字段
    cpc: Optional[Decimal] = Field(None, description="单次点击成本")
    ctr: Optional[Decimal] = Field(None, description="点击率")
    cvr: Optional[Decimal] = Field(None, description="转化率")
    
    @field_validator("spend_amount", mode="before")
    @classmethod
    def convert_decimal(cls, v):
        if v is not None:
            return Decimal(str(v))
        return v


class AdSpendListResponse(BaseModel):
    """消耗记录列表响应 (分页)"""
    # CodeBlock: CB-BE-001 (Pagination)
    items: List[AdSpendResponse]
    total: int
    page: int
    page_size: int
    pages: int


class AdSpendBatchImportResponse(BaseModel):
    """批量导入响应"""
    total_count: int = Field(..., description="总记录数")
    success_count: int = Field(..., description="成功导入数")
    error_count: int = Field(..., description="失败数")
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="错误详情")
    imported_ids: List[str] = Field(default_factory=list, description="成功导入的ID列表")
    processing_time_seconds: float = Field(default=0, description="处理耗时(秒)")


class AdSpendStatisticsResponse(BaseModel):
    """消耗统计响应"""
    total_spend: Decimal = Field(default=Decimal("0.00"), description="总消耗")
    total_impressions: int = Field(default=0, description="总曝光")
    total_clicks: int = Field(default=0, description="总点击")
    total_conversions: int = Field(default=0, description="总转化")
    avg_cpc: Optional[Decimal] = Field(None, description="平均CPC")
    avg_ctr: Optional[Decimal] = Field(None, description="平均CTR")
    record_count: int = Field(default=0, description="记录数")
    date_range: Optional[Dict[str, date]] = Field(None, description="日期范围")
    by_platform: Optional[Dict[str, Decimal]] = Field(None, description="按平台统计")
    by_currency: Optional[Dict[str, Decimal]] = Field(None, description="按货币统计")


class AdSpendAggregateResponse(BaseModel):
    """消耗聚合响应 (按日期/平台/账户)"""
    group_key: str = Field(..., description="分组键")
    group_value: str = Field(..., description="分组值")
    total_spend: Decimal
    total_impressions: int
    total_clicks: int
    total_conversions: int
    record_count: int
