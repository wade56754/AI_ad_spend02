"""
利润模块 API 路由 (TASK-PROFIT-001)

SoT References:
- MASTER.md v4.4 §2.4 (7角色模型)
- BUSINESS_RULES.md v3.2 §4.9 BR-PROFIT
- BR-PROFIT.md v1.0

端点列表：
- GET /projects - 获取项目利润报表列表

利润计算公式 (BR-PROFIT):
- BR-PROFIT-001: per_lead 模式: 收入 = conversions_final × unit_price
- BR-PROFIT-002: fee_rate 模式: 收入 = ad_spend × service_rate
- BR-PROFIT-003: 成本 = ad_spend + 手续费
- BR-PROFIT-004: 毛利 = 收入 - 成本

权限矩阵 (MASTER.md v4.4 §2.4):
- ceo: 所有项目（只读）
- finance: 所有项目
- project_owner: 自己负责的项目

Version: 1.0
"""

import logging
from datetime import date
from decimal import Decimal
from typing import Optional, List

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.core.db import get_db
from backend.core.dependencies import get_current_user, require_role
from backend.core.response import success_response, error_response
from backend.models import User, Project, DailyReport
from backend.schemas.profit import (
    ProjectProfitItem,
    ProfitGranularity,
    PeriodInfo,
)
from backend.schemas.response import PaginationMeta


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/profit", tags=["profit"])


# ============ Schema 定义 (TASK-PROFIT-001) ============

from pydantic import BaseModel, Field, ConfigDict
from typing import Literal


class ProjectProfitReportItem(BaseModel):
    """
    项目利润报表条目 (TASK-PROFIT-001)

    SoT: BR-PROFIT.md v1.0 §3
    """
    model_config = ConfigDict(from_attributes=True)

    project_id: int = Field(..., description="项目ID")
    project_name: str = Field(..., description="项目名称")
    billing_model: str = Field(..., description="计费模式: per_lead | fee_rate")

    # 核心指标
    conversions: int = Field(0, description="转化数（进粉数）")
    ad_spend: Decimal = Field(Decimal("0.00"), description="广告消耗")
    revenue: Decimal = Field(Decimal("0.00"), description="收入")
    cost: Decimal = Field(Decimal("0.00"), description="成本（含手续费）")
    gross_profit: Decimal = Field(Decimal("0.00"), description="毛利")
    profit_margin_pct: Optional[float] = Field(None, description="毛利率(%)")

    # 辅助信息
    unit_price: Optional[Decimal] = Field(None, description="单粉价格 (per_lead)")
    service_rate: Optional[float] = Field(None, description="服务费率 (fee_rate)")
    fee_rate: float = Field(0.08, description="渠道手续费率")
    cpl: Optional[Decimal] = Field(None, description="CPL (消耗/进粉)")
    cpl_warning: Optional[str] = Field(None, description="CPL 警告 (BR-PROFIT-006)")


class ProjectProfitReportListResponse(BaseModel):
    """
    项目利润报表列表响应 (TASK-PROFIT-001)
    """
    model_config = ConfigDict(from_attributes=True)

    items: List[ProjectProfitReportItem] = Field(default_factory=list, description="项目列表")
    period: PeriodInfo = Field(..., description="查询周期")
    summary: "ProjectProfitSummary" = Field(..., description="汇总信息")
    meta: PaginationMeta = Field(..., description="分页信息")


class ProjectProfitSummary(BaseModel):
    """
    项目利润汇总 (TASK-PROFIT-001)
    """
    model_config = ConfigDict(from_attributes=True)

    total_projects: int = Field(0, description="项目总数")
    total_conversions: int = Field(0, description="总转化数")
    total_ad_spend: Decimal = Field(Decimal("0.00"), description="总广告消耗")
    total_revenue: Decimal = Field(Decimal("0.00"), description="总收入")
    total_cost: Decimal = Field(Decimal("0.00"), description="总成本")
    total_gross_profit: Decimal = Field(Decimal("0.00"), description="总毛利")
    avg_profit_margin_pct: Optional[float] = Field(None, description="平均毛利率(%)")


# 解决前向引用
ProjectProfitReportListResponse.model_rebuild()


# ============ GET /projects ============

@router.get(
    "/projects",
    summary="获取项目利润报表列表",
    description="""
获取项目利润报表列表。

**利润计算公式** (BR-PROFIT.md v1.0):
- per_lead 模式: 收入 = conversions_final × unit_price
- fee_rate 模式: 收入 = ad_spend × service_rate
- 成本 = ad_spend + 手续费
- 毛利 = 收入 - 成本

**权限控制** (MASTER.md v4.4):
- ceo: 所有项目
- finance: 所有项目
- project_owner: 仅自己负责的项目
""",
    responses={
        200: {"description": "查询成功"},
        400: {"description": "参数错误 (BIZ_701)"},
        403: {"description": "权限不足 (AUTH_403)"},
    }
)
async def get_project_profit_report(
    start_date: date = Query(..., description="开始日期"),
    end_date: date = Query(..., description="结束日期"),
    billing_model: Optional[str] = Query(None, description="计费模式筛选: per_lead | fee_rate"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(require_role(["admin", "ceo", "finance", "project_owner"])),
    db: Session = Depends(get_db),
):
    """
    获取项目利润报表列表 (TASK-PROFIT-001)

    SoT Reference: BR-PROFIT.md v1.0

    利润计算逻辑:
    - BR-PROFIT-001: per_lead 收入 = conversions_final × unit_price
    - BR-PROFIT-002: fee_rate 收入 = ad_spend × service_rate
    - BR-PROFIT-003: 成本 = ad_spend + 手续费
    - BR-PROFIT-004: 毛利 = 收入 - 成本
    - BR-PROFIT-005: CPL = 消耗 / 进粉
    - BR-PROFIT-006: 进粉 < 5 时标记"低量不稳定"
    """
    logger.info(
        f"GET /profit/projects: user={current_user.email}, "
        f"start_date={start_date}, end_date={end_date}"
    )

    # 参数校验
    if end_date < start_date:
        return error_response(
            code="BIZ_701",
            message="结束日期不能早于开始日期",
            status_code=400
        )

    # 构建项目查询 (STATE_MACHINE.md v2.6: active | archived)
    project_query = db.query(Project).filter(Project.status.in_(["active", "archived"]))

    # 权限过滤 (MASTER.md v4.4 §2.4)
    if current_user.role == "project_owner":
        # project_owner 只能看自己负责的项目
        project_query = project_query.filter(Project.owner_id == current_user.id)

    if project_id:
        project_query = project_query.filter(Project.id == project_id)

    if billing_model:
        # 注: Project 使用 settlement_type 字段
        project_query = project_query.filter(Project.settlement_type == billing_model)

    # 获取项目列表
    projects = project_query.all()

    # 计算每个项目的利润
    items = []
    total_conversions = 0
    total_ad_spend = Decimal("0.00")
    total_revenue = Decimal("0.00")
    total_cost = Decimal("0.00")
    total_gross_profit = Decimal("0.00")

    for project in projects:
        item = _calculate_project_profit(
            db=db,
            project=project,
            start_date=start_date,
            end_date=end_date,
        )
        items.append(item)

        total_conversions += item.conversions
        total_ad_spend += item.ad_spend
        total_revenue += item.revenue
        total_cost += item.cost
        total_gross_profit += item.gross_profit

    # 计算平均毛利率
    avg_profit_margin_pct = None
    if total_revenue > 0:
        avg_profit_margin_pct = float(total_gross_profit / total_revenue * 100)

    # 分页
    total_items = len(items)
    total_pages = (total_items + page_size - 1) // page_size if page_size > 0 else 0
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_items = items[start_idx:end_idx]

    # 构建响应
    response_data = ProjectProfitReportListResponse(
        items=paginated_items,
        period=PeriodInfo(
            start=start_date,
            end=end_date,
        ),
        summary=ProjectProfitSummary(
            total_projects=total_items,
            total_conversions=total_conversions,
            total_ad_spend=total_ad_spend,
            total_revenue=total_revenue,
            total_cost=total_cost,
            total_gross_profit=total_gross_profit,
            avg_profit_margin_pct=avg_profit_margin_pct,
        ),
        meta=PaginationMeta(
            total=total_items,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        ),
    )

    return success_response(
        data=response_data.model_dump(),
        message="查询成功"
    )


# ============ GET /company (TASK-PROFIT-004) ============

@router.get(
    "/company",
    summary="获取公司利润汇总",
    description="""
获取公司利润汇总报表。

**公司利润公式** (MASTER.md v4.6 §4.5.10):
- 公司利润 = 总收入 - 总支出
- 总支出 = ad_topup + ad_support + overhead

**权限控制**:
- 仅 ceo/admin 可查看
""",
    responses={
        200: {"description": "查询成功"},
        400: {"description": "参数错误 (BIZ_701)"},
        403: {"description": "权限不足 (AUTH_403)"},
    }
)
async def get_company_profit_report(
    start_date: date = Query(..., description="开始日期"),
    end_date: date = Query(..., description="结束日期"),
    current_user: User = Depends(require_role(["admin", "ceo"])),
    db: Session = Depends(get_db),
):
    """
    获取公司利润汇总 (TASK-PROFIT-004)

    SoT Reference: MASTER.md v4.6 §4.5.10

    权限: 仅 ceo/admin

    公式:
    - 公司利润 = 总收入 - 总支出
    - 总支出 = ad_topup + ad_support + overhead
    """
    from backend.services.finance.profit_service import ProfitService

    logger.info(
        f"GET /profit/company: user={current_user.email}, "
        f"start_date={start_date}, end_date={end_date}"
    )

    # 参数校验
    if end_date < start_date:
        return error_response(
            code="BIZ_701",
            message="结束日期不能早于开始日期",
            status_code=400
        )

    # 调用 Service
    service = ProfitService(db)
    result = service.get_company_profit_report(
        start_date=start_date,
        end_date=end_date,
    )

    return success_response(
        data=result,
        message="查询成功"
    )


def _calculate_project_profit(
    db: Session,
    project: Project,
    start_date: date,
    end_date: date,
) -> ProjectProfitReportItem:
    """
    计算单个项目的利润 (TASK-PROFIT-001)

    SoT: BR-PROFIT.md v1.0 §3

    公式:
    - BR-PROFIT-001: per_lead 收入 = conversions_final × unit_price
    - BR-PROFIT-002: fee_rate 收入 = ad_spend × service_rate
    - BR-PROFIT-003: 成本 = ad_spend + 手续费
    - BR-PROFIT-004: 毛利 = 收入 - 成本
    """
    # 聚合日报数据 (仅 final_locked 状态)
    result = db.query(
        func.coalesce(func.sum(DailyReport.conversions_final), 0).label("conversions"),
        func.coalesce(func.sum(DailyReport.real_spend), 0).label("spend"),
    ).filter(
        DailyReport.project_id == project.id,
        DailyReport.report_date >= start_date,
        DailyReport.report_date <= end_date,
        DailyReport.status == "final_locked",
    ).first()

    conversions = int(result.conversions or 0)
    ad_spend = Decimal(str(result.spend or 0))

    # 获取项目配置
    unit_price = getattr(project, 'unit_price', None) or Decimal("0")
    service_rate = getattr(project, 'service_rate', None)
    # 注: Project 使用 settlement_type 字段 (fixed/tiered/markup)
    # 映射: fixed/tiered -> per_lead, markup -> fee_rate
    settlement_type = getattr(project, 'settlement_type', 'fixed') or 'fixed'
    billing_model = 'fee_rate' if settlement_type == 'markup' else 'per_lead'
    fee_rate = 0.08  # 默认渠道手续费率

    # BR-PROFIT-001/002: 计算收入
    if billing_model == "fee_rate" and service_rate:
        # fee_rate 模式: 收入 = ad_spend × service_rate
        revenue = ad_spend * Decimal(str(service_rate))
    else:
        # per_lead 模式: 收入 = conversions × unit_price
        revenue = Decimal(str(conversions)) * unit_price

    # BR-PROFIT-003: 成本 = ad_spend + 手续费
    fee = ad_spend * Decimal(str(fee_rate))
    cost = ad_spend + fee

    # BR-PROFIT-004: 毛利 = 收入 - 成本
    gross_profit = revenue - cost

    # 计算毛利率
    profit_margin_pct = None
    if revenue > 0:
        profit_margin_pct = float(gross_profit / revenue * 100)

    # BR-PROFIT-005: CPL = 消耗 / 进粉
    cpl = None
    cpl_warning = None
    if conversions > 0:
        cpl = ad_spend / Decimal(str(conversions))
        # BR-PROFIT-006: 进粉 < 5 时标记
        if conversions < 5:
            cpl_warning = "低量不稳定"

    return ProjectProfitReportItem(
        project_id=project.id,
        project_name=project.name,
        billing_model=billing_model,
        conversions=conversions,
        ad_spend=ad_spend,
        revenue=revenue,
        cost=cost,
        gross_profit=gross_profit,
        profit_margin_pct=profit_margin_pct,
        unit_price=unit_price if billing_model == "per_lead" else None,
        service_rate=float(service_rate) if service_rate and billing_model == "fee_rate" else None,
        fee_rate=fee_rate,
        cpl=cpl,
        cpl_warning=cpl_warning,
    )
