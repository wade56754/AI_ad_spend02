"""
Schema 层标准模式 - AI 广告代投系统
Version: 1.0
SoT Reference: API_SOT.md v9.0, DATA_SCHEMA.md v5.2

本文件展示 Pydantic Schema 的标准写法，供 AI 代码生成参考。

关键模式：
1. 使用 Pydantic v2 语法 (BaseModel, Field, ConfigDict)
2. 字段命名对齐 SoT 数据流规范 (raw/real/final)
3. 验证器使用 @field_validator 装饰器
4. 响应模型使用 computed_field 计算字段
"""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional, Any
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict, field_validator, computed_field


# === 请求 Schema ===

class ExampleCreateRequest(BaseModel):
    """
    创建请求 Schema

    字段命名遵循 SoT 三数据流规范:
    - xxx_raw: raw 数据流（投手提交）
    - xxx_real: real 数据流（运营录入）
    - xxx_final: final 数据流（运营确认）

    SoT: API_SOT.md v9.0 Section X.X
    """
    model_config = ConfigDict(from_attributes=True)

    # 必填字段 - 使用 ... 表示必填
    name: str = Field(..., min_length=1, max_length=100, description="名称")
    amount: Decimal = Field(..., ge=0, description="金额 DECIMAL(15,2)")
    report_date: date = Field(..., description="报表日期（不能是未来日期）")

    # 可选字段 - 使用 None 默认值
    description: Optional[str] = Field(None, max_length=500, description="描述")
    tags: List[str] = Field(default_factory=list, description="标签列表")

    # 关联字段 - 使用 gt=0 确保正整数
    account_id: int = Field(..., gt=0, description="关联账户ID")

    # 字段验证器
    @field_validator('report_date')
    @classmethod
    def validate_report_date(cls, v):
        """报表日期不能是未来日期 (BIZ_201)"""
        if v > date.today():
            raise ValueError(f'报表日期 {v} 不能大于今天 {date.today()}')
        return v

    @field_validator('amount')
    @classmethod
    def validate_amount_precision(cls, v):
        """金额精度校验 - 最多2位小数"""
        if v is not None:
            # 确保最多2位小数
            return Decimal(str(v)).quantize(Decimal('0.01'))
        return v


class ExampleUpdateRequest(BaseModel):
    """
    更新请求 Schema

    注意：所有字段都是可选的，仅更新提供的字段
    """
    model_config = ConfigDict(from_attributes=True)

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    tags: Optional[List[str]] = None


class ExampleQueryParams(BaseModel):
    """
    查询参数 Schema

    用于列表接口的筛选参数
    """
    model_config = ConfigDict(from_attributes=True)

    # 分页
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页条数")

    # 筛选
    status: Optional[str] = Field(None, description="状态筛选")
    start_date: Optional[date] = Field(None, description="开始日期")
    end_date: Optional[date] = Field(None, description="结束日期")

    # 排序
    sort_by: str = Field("created_at", description="排序字段")
    sort_order: str = Field("desc", pattern="^(asc|desc)$", description="排序方向")

    @field_validator('end_date')
    @classmethod
    def validate_date_range(cls, v, info):
        """结束日期必须大于等于开始日期"""
        if v and info.data.get('start_date'):
            if v < info.data['start_date']:
                raise ValueError('结束日期必须大于等于开始日期')
        return v


# === 响应 Schema ===

class ExampleResponse(BaseModel):
    """
    响应 Schema

    特点：
    - 使用 computed_field 计算派生字段
    - 包含关联对象的嵌套响应
    """
    model_config = ConfigDict(from_attributes=True)

    # 基础字段
    id: int
    name: str
    description: Optional[str] = None
    amount: Decimal
    status: str

    # 时间字段
    created_at: datetime
    updated_at: Optional[datetime] = None

    # 关联字段（简化）
    account_id: int
    account_name: Optional[str] = None  # 从关联对象获取

    # 计算字段
    @computed_field
    @property
    def status_display(self) -> str:
        """状态显示名称"""
        status_map = {
            "draft": "草稿",
            "pending_review": "待审核",
            "approved": "已审批",
            "rejected": "已拒绝",
        }
        return status_map.get(self.status, self.status)

    @computed_field
    @property
    def amount_display(self) -> str:
        """金额格式化显示"""
        return f"¥{self.amount:,.2f}"


class ExampleListResponse(BaseModel):
    """列表响应 Schema"""
    model_config = ConfigDict(from_attributes=True)

    items: List[ExampleResponse]
    total: int
    page: int
    page_size: int

    @computed_field
    @property
    def total_pages(self) -> int:
        """总页数"""
        return (self.total + self.page_size - 1) // self.page_size


# === 嵌套 Schema ===

class AccountBrief(BaseModel):
    """账户简要信息（用于嵌套）"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    code: str


class ExampleDetailResponse(ExampleResponse):
    """
    详情响应 Schema（扩展基础响应）

    包含更多详细信息和关联对象
    """
    # 额外详情字段
    notes: Optional[str] = None
    tags: List[str] = Field(default_factory=list)

    # 嵌套关联对象
    account: Optional[AccountBrief] = None

    # 审计信息
    created_by: Optional[int] = None
    created_by_name: Optional[str] = None
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None


# === 批量操作 Schema ===

class ExampleBatchRequest(BaseModel):
    """批量操作请求"""
    model_config = ConfigDict(from_attributes=True)

    ids: List[int] = Field(..., min_length=1, max_length=100, description="ID列表")
    action: str = Field(..., description="操作类型")


class ExampleImportError(BaseModel):
    """导入错误信息"""
    row_number: int = Field(..., description="行号")
    error_code: str = Field(..., description="错误码")
    error_message: str = Field(..., description="错误信息")
    field_name: Optional[str] = Field(None, description="字段名")
    invalid_value: Optional[str] = Field(None, description="无效值")
    suggestion: Optional[str] = Field(None, description="修复建议")


class ExampleBatchImportResponse(BaseModel):
    """批量导入响应"""
    success_count: int = Field(..., description="成功数量")
    error_count: int = Field(..., description="失败数量")
    errors: List[ExampleImportError] = Field(default_factory=list, description="错误列表")
