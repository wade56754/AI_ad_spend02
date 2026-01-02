"""
项目管理相关的Pydantic模型 (重构版)

SoT Reference: API_SOT.md v9.3 §6 (Projects API)
SoT Reference: STATE_MACHINE.md v2.6 §5 (项目状态机: draft/active/suspended/archived)
SoT Reference: CORE_MODULES.md §4.5 (阶梯价格规则)

依赖代码块:
- response-envelope: 统一响应格式
- pagination: 分页参数

Version: 2.2 (添加阶梯定价)
"""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any, Union
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict, computed_field


# ========== 阶梯定价相关 Schema ==========


class PriceTier(BaseModel):
    """价格阶梯"""

    model_config = ConfigDict(from_attributes=True)

    min: int = Field(..., ge=0, description="最小数量（含）")
    max: Optional[int] = Field(None, description="最大数量（含），null 表示无上限")
    price: Decimal = Field(..., ge=0, description="该阶梯单价")


class PriceRules(BaseModel):
    """
    价格规则 (BUSINESS_RULES.md v4.6 BR-STL-004)

    type = 'fixed': 固定价格，使用 price 字段
    type = 'tiered': 阶梯价格，使用 tiers 字段
    type = 'markup': 加价模式，使用 markup_rate 字段

    calculation_mode:
    - 'daily': 按日计算阶梯
    - 'cumulative': 按累计计算阶梯

    SoT Reference: BUSINESS_RULES.md v4.6 §4.10.2
    """

    model_config = ConfigDict(from_attributes=True)

    type: str = Field(
        ...,
        pattern="^(fixed|tiered|markup)$",
        description="定价类型: fixed/tiered/markup (SoT: BR-STL-004)",
    )
    calculation_mode: Optional[str] = Field(
        "daily", pattern="^(daily|cumulative)$", description="阶梯计算模式"
    )
    price: Optional[Decimal] = Field(None, ge=0, description="固定价格（type=fixed时）")
    tiers: Optional[List[PriceTier]] = Field(None, description="阶梯价格（type=tiered时）")
    markup_rate: Optional[Decimal] = Field(
        None, ge=0, le=1, description="加价比例 0-1（type=markup时，如 0.20 = 20%）"
    )


# ========== 项目请求/响应 Schema ==========


class ProjectCreateRequest(BaseModel):
    """项目创建请求"""

    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., min_length=1, max_length=200, description="项目名称")
    client_name: str = Field(..., min_length=1, max_length=200, description="客户联系人姓名")
    client_company: str = Field(..., min_length=1, max_length=200, description="客户公司名称")
    description: Optional[str] = Field(None, max_length=1000, description="项目描述")
    budget: Optional[Decimal] = Field(None, ge=0, decimal_places=2, description="项目预算")
    currency: str = Field("USD", max_length=10, description="货币类型")
    start_date: Optional[date] = Field(None, description="项目开始日期")
    end_date: Optional[date] = Field(None, description="项目结束日期")
    account_manager_id: Optional[int] = Field(None, gt=0, description="项目经理ID")
    region: Optional[str] = Field(None, max_length=50, description="主要投放地区")
    unit_price: Optional[Decimal] = Field(
        None, ge=0, decimal_places=2, description="单粉价格"
    )
    # 阶梯定价 (v2.2)
    price_rules: Optional[PriceRules] = Field(None, description="阶梯价格规则")
    default_currency: str = Field("USD", max_length=10, description="项目默认币种")


class ProjectUpdateRequest(BaseModel):
    """项目更新请求 (BUSINESS_RULES.md v4.6)"""

    model_config = ConfigDict(from_attributes=True)

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    client_name: Optional[str] = Field(None, min_length=1, max_length=200)
    client_company: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    status: Optional[str] = Field(None, description="项目状态")
    budget: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    account_manager_id: Optional[int] = Field(None, gt=0)
    region: Optional[str] = Field(None, max_length=50, description="主要投放地区")
    unit_price: Optional[Decimal] = Field(
        None, ge=0, decimal_places=2, description="单粉价格"
    )
    # 阶梯定价 (v2.2)
    price_rules: Optional[PriceRules] = Field(None, description="阶梯价格规则")
    default_currency: Optional[str] = Field(None, max_length=10, description="项目默认币种")
    # 履约状态 (BUSINESS_RULES.md v4.6 BR-PROJ-006)
    # 注意: fulfillment_status 只能从 running -> fulfilled，不可回退
    fulfillment_status: Optional[str] = Field(
        None, pattern="^(running|fulfilled)$", description="履约状态"
    )
    fulfillment_reason: Optional[str] = Field(
        None, pattern="^(spend_exhausted|client_stopped)$", description="履约结束原因"
    )


class ProjectMarkFulfilledRequest(BaseModel):
    """
    标记项目履约完成请求

    SoT Reference: BUSINESS_RULES.md v4.6 BR-PROJ-006
    SoT Reference: BI-06 履约完成唯一判定条件

    履约状态转换: running -> fulfilled (不可逆)
    """

    model_config = ConfigDict(from_attributes=True)

    reason: str = Field(
        ...,
        pattern="^(spend_exhausted|client_stopped)$",
        description="履约结束原因: spend_exhausted(消耗完毕) / client_stopped(客户喊停)",
    )
    note: Optional[str] = Field(None, max_length=500, description="备注说明")


class ProjectMemberAssignRequest(BaseModel):
    """项目成员分配请求"""

    model_config = ConfigDict(from_attributes=True)

    user_id: Union[int, UUID] = Field(..., description="用户ID（支持int或UUID）")
    role: str = Field(
        ..., pattern="^(account_manager|media_buyer|analyst)$", description="角色"
    )


class ProjectExpenseRequest(BaseModel):
    """项目费用记录请求"""

    model_config = ConfigDict(from_attributes=True)

    expense_type: str = Field(..., description="费用类型")
    amount: Decimal = Field(..., gt=0, decimal_places=2, description="金额")
    description: Optional[str] = Field(None, max_length=500, description="费用说明")
    expense_date: date = Field(..., description="费用日期")


# 响应模型
class ProjectResponse(BaseModel):
    """项目响应 (BUSINESS_RULES.md v4.6)"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    client_name: str
    client_company: str
    description: Optional[str]
    status: str
    budget: Decimal
    currency: str
    start_date: Optional[date]
    end_date: Optional[date]
    account_manager_id: Optional[int]
    account_manager_name: Optional[str]
    # 新增字段 v2.1
    region: Optional[str] = None
    unit_price: Optional[Decimal] = None
    total_follows: int = 0  # 聚合的总进粉数 (来自日报)
    # 阶梯定价 v2.2
    price_rules: Optional[dict] = None  # JSON 原样返回
    default_currency: Optional[str] = "USD"
    # 履约状态字段 (BUSINESS_RULES.md v4.6 BR-PROJ-006)
    fulfillment_status: str = "running"  # running/fulfilled
    fulfillment_reason: Optional[str] = None  # spend_exhausted/client_stopped
    fulfilled_at: Optional[datetime] = None  # 履约完成时间 (UTC)
    # 原有字段
    total_spent: Decimal
    total_accounts: int
    active_accounts: int
    created_by: Optional[str]  # 修改为 Optional[str] 以支持 UUID（模型中是 UUID 类型）
    created_by_name: str
    created_at: datetime
    updated_at: datetime

    @computed_field
    @property
    def remaining_budget(self) -> Decimal:
        """剩余预算"""
        return max(Decimal("0"), self.budget - self.total_spent)

    @computed_field
    @property
    def budget_usage_percent(self) -> Decimal:
        """预算使用百分比"""
        if self.budget == 0:
            return Decimal("0")
        return (self.total_spent / self.budget) * 100


class ProjectMemberResponse(BaseModel):
    """项目成员响应"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: str  # 改为 str 以支持 UUID 字符串
    user_name: str
    user_email: str
    user_role: str
    project_role: str
    joined_at: datetime


class ProjectExpenseResponse(BaseModel):
    """项目费用响应"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    expense_type: str
    amount: Decimal
    description: Optional[str]
    expense_date: date
    created_by_name: str
    created_at: datetime


class ProjectListResponse(BaseModel):
    """项目列表响应"""

    items: List[ProjectResponse]
    meta: Dict[str, Any]


class ProjectStatisticsResponse(BaseModel):
    """
    项目统计响应 (BUSINESS_RULES.md v4.6)

    状态对齐 STATE_MACHINE.md v2.6 §5:
    - draft: 草稿
    - active: 活跃
    - suspended: 暂停
    - archived: 归档

    履约状态对齐 BUSINESS_RULES.md v4.6 BR-PROJ-006:
    - running: 履约中
    - fulfilled: 已履约
    """

    model_config = ConfigDict(from_attributes=True)

    total_projects: int
    active_projects: int
    suspended_projects: int  # SoT: suspended (原 paused)
    archived_projects: int  # SoT: archived (原 completed)
    draft_projects: int  # SoT: draft (新增)
    # 履约统计 (BUSINESS_RULES.md v4.6 BR-PROJ-006)
    fulfilled_projects: int = 0  # 已履约项目数
    running_projects: int = 0  # 履约中项目数
    total_budget: Decimal

    @computed_field
    @property
    def budget_utilization(self) -> Decimal:
        """预算利用率 (简化版，不依赖 total_spent)"""
        return Decimal("0")  # Phase 1: 仅占位，实际计算待 Phase 2


# ========== 项目仪表盘 Schema (TASK-PRJ-004) ==========


class DailyTrendItem(BaseModel):
    """每日趋势数据项"""

    model_config = ConfigDict(from_attributes=True)

    date: str = Field(..., description="日期 (YYYY-MM-DD)")
    spend: Decimal = Field(default=Decimal("0.00"), description="消耗金额")
    follows: int = Field(default=0, description="进粉数")
    conversions: int = Field(default=0, description="转化数")
    cpl: Optional[Decimal] = Field(None, description="单粉成本 (CPL)")


class AccountPerformance(BaseModel):
    """账户表现数据"""

    model_config = ConfigDict(from_attributes=True)

    account_id: int
    account_name: str
    platform: Optional[str] = None
    status: str
    spend: Decimal = Field(default=Decimal("0.00"))
    follows: int = Field(default=0)
    conversions: int = Field(default=0)
    cpl: Optional[Decimal] = None


class ProjectDashboardResponse(BaseModel):
    """
    项目仪表盘响应 (TASK-PRJ-004)

    包含:
    - KPI 汇总指标
    - 每日趋势数据 (近 30 天)
    - 账户表现排行
    """

    model_config = ConfigDict(from_attributes=True)

    # KPI 汇总
    total_spend: Decimal = Field(default=Decimal("0.00"), description="总消耗")
    total_follows: int = Field(default=0, description="总进粉数")
    total_conversions: int = Field(default=0, description="总转化数")
    avg_cpl: Optional[Decimal] = Field(None, description="平均单粉成本")
    budget_usage_percent: Decimal = Field(
        default=Decimal("0.00"), description="预算使用率 %"
    )

    # 趋势数据
    daily_trend: List[DailyTrendItem] = Field(
        default_factory=list, description="每日趋势 (近30天)"
    )

    # 账户表现
    account_performance: List[AccountPerformance] = Field(
        default_factory=list, description="账户表现排行"
    )

    # 元数据
    period_start: Optional[str] = Field(None, description="统计开始日期")
    period_end: Optional[str] = Field(None, description="统计结束日期")


# ========== 预付款管理 Schema (TASK-PRJ-005) ==========


class PrepaymentCreateRequest(BaseModel):
    """
    预付款入账请求

    TASK-PRJ-005: 预付款管理
    SoT Reference: DATA_SCHEMA.md v5.7 §3.4 (三本账体系 - 预付款账本)
    SoT Reference: BUSINESS_RULES.md v4.8 BR-FIN-004 (预收款≠收入)

    业务规则:
    - 预收款在履约完成前是负债，不是收入
    - 入账金额必须为正数
    - 入账日期不能是未来日期
    """

    model_config = ConfigDict(from_attributes=True)

    amount: Decimal = Field(
        ...,
        gt=0,
        decimal_places=2,
        description="入账金额（必须为正数）",
    )
    entry_date: date = Field(..., description="入账日期")
    notes: Optional[str] = Field(None, max_length=500, description="备注说明")


class PrepaymentReversalRequest(BaseModel):
    """
    预付款红冲请求

    红冲用于冲销错误的入账记录。

    业务规则:
    - 红冲金额必须为负数
    - 必须关联原入账记录ID
    """

    model_config = ConfigDict(from_attributes=True)

    reference_id: int = Field(..., gt=0, description="关联的原入账记录ID")
    amount: Decimal = Field(
        ...,
        lt=0,
        decimal_places=2,
        description="红冲金额（必须为负数）",
    )
    entry_date: date = Field(..., description="红冲日期")
    notes: Optional[str] = Field(None, max_length=500, description="红冲原因")


class PrepaymentResponse(BaseModel):
    """
    预付款记录响应

    TASK-PRJ-005: 预付款管理
    """

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="记录ID")
    project_id: int = Field(..., description="项目ID")
    project_name: Optional[str] = Field(None, description="项目名称")
    entry_type: str = Field(..., description="分录类型: TOPUP(入账)/REVERSAL(红冲)")
    amount: Decimal = Field(..., description="金额")
    balance_after: Decimal = Field(..., description="交易后余额")
    entry_date: date = Field(..., description="入账日期")
    reference_id: Optional[int] = Field(None, description="关联记录ID（红冲时）")
    notes: Optional[str] = Field(None, description="备注")
    created_by: Optional[int] = Field(None, description="操作人ID")
    operator_name: Optional[str] = Field(None, description="操作人姓名")
    created_at: datetime = Field(..., description="创建时间")


class PrepaymentListResponse(BaseModel):
    """预付款记录列表响应"""

    items: List[PrepaymentResponse]
    meta: Dict[str, Any] = Field(
        default_factory=lambda: {"total": 0, "page": 1, "page_size": 20}
    )


class PrepaymentBalanceResponse(BaseModel):
    """
    项目预付款余额响应

    TASK-PRJ-005: 预付款管理
    SoT Reference: DATA_SCHEMA.md v5.7 §3.4.4 (三本账体系)

    业务说明:
    - balance: 当前预付款余额（客户已付款但未消耗的金额）
    - total_topup: 累计入账总额
    - total_reversal: 累计红冲总额
    - entry_count: 流水记录数
    """

    model_config = ConfigDict(from_attributes=True)

    project_id: int = Field(..., description="项目ID")
    project_name: Optional[str] = Field(None, description="项目名称")
    balance: Decimal = Field(default=Decimal("0.00"), description="当前预付款余额")
    total_topup: Decimal = Field(default=Decimal("0.00"), description="累计入账总额")
    total_reversal: Decimal = Field(default=Decimal("0.00"), description="累计红冲总额")
    entry_count: int = Field(default=0, description="流水记录数")
    last_entry_date: Optional[date] = Field(None, description="最后入账日期")
