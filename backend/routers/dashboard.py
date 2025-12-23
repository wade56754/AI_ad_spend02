"""
CEO Dashboard API 路由

提供老板驾驶舱汇总数据，包括：
- 项目总览
- 消耗/收入汇总
- 待处理事项
- 异常告警

权限：仅 admin/ceo 可访问

SoT Reference: MASTER.md v4.4 §6.5
"""

import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy import func, and_, or_
from sqlalchemy.orm import Session, joinedload

from backend.core.db import get_db
from backend.core.dependencies import get_current_user
from backend.core.response import success_response, error_response, StandardResponse
from backend.core.error_codes import SystemErrorCodes
from backend.core.role_mapping import role_in_list, normalize_role
from backend.core.phase_config import get_phase_config

from backend.models import User, DailyReport, Project, AdAccount
from backend.models.workflow.topup_request import TopupRequest
from backend.models.enums import DailyReportStatus, TopupRequestStatus, ProjectStatus

from pydantic import BaseModel, Field, ConfigDict

# 创建 logger 实例
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboards", tags=["dashboards"])


# ============ Schema 定义 ============

class AlertItem(BaseModel):
    """告警项"""
    type: str = Field(..., description="告警类型: budget_warning/trend_anomaly/pending_approval")
    severity: str = Field("medium", description="严重程度: low/medium/high/critical")
    project_id: Optional[int] = None
    project_name: Optional[str] = None
    message: str = Field(..., description="告警消息")
    created_at: Optional[datetime] = None


class CEODashboardSummary(BaseModel):
    """CEO 驾驶舱汇总响应"""
    model_config = ConfigDict(from_attributes=True)

    # 时间范围
    period: str = Field(..., description="统计周期，如 2024-12")
    start_date: date
    end_date: date

    # 项目统计
    total_projects: int = Field(0, description="项目总数")
    active_projects: int = Field(0, description="活跃项目数")
    suspended_projects: int = Field(0, description="暂停项目数")

    # 消耗统计
    total_spend: Decimal = Field(Decimal("0.00"), description="总消耗")
    total_revenue: Decimal = Field(Decimal("0.00"), description="总收入（conversions × unit_price）")
    profit_margin: Optional[float] = Field(None, description="利润率 = (revenue - spend) / revenue")

    # 待处理事项
    pending_reports: int = Field(0, description="待审核日报数")
    pending_topups: int = Field(0, description="待审批充值数")
    trend_flagged_count: int = Field(0, description="趋势异常日报数")

    # 告警列表
    alerts: List[AlertItem] = Field(default_factory=list, description="告警列表")

    # Phase 信息
    current_phase: int = Field(1, description="当前 Phase (1 或 2)")


class ProjectRankingItem(BaseModel):
    """项目排名项"""
    model_config = ConfigDict(from_attributes=True)

    project_id: int
    project_name: str
    total_spend: Decimal = Decimal("0.00")
    total_follows: int = 0
    cost_per_follow: Optional[Decimal] = None
    roas: Optional[float] = None


class CEODashboardDetail(BaseModel):
    """CEO 驾驶舱详细数据"""
    model_config = ConfigDict(from_attributes=True)

    summary: CEODashboardSummary
    top_spend_projects: List[ProjectRankingItem] = Field(default_factory=list)
    worst_roas_projects: List[ProjectRankingItem] = Field(default_factory=list)


# ============ 权限检查 ============

def require_ceo_access(current_user: User = Depends(get_current_user)) -> User:
    """
    CEO 驾驶舱权限检查

    仅允许以下角色访问：
    - admin
    - ceo (映射到 admin)

    使用 role_in_list 支持等价角色
    """
    allowed_roles = ["admin", "ceo"]

    if not role_in_list(current_user.role, allowed_roles):
        logger.warning(
            f"User {current_user.id} ({current_user.role}) denied access to CEO dashboard"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "AUTH_500",
                "message": "CEO 驾驶舱仅限老板和管理员访问"
            }
        )

    return current_user


# ============ API 端点 ============

@router.get(
    "/ceo/summary",
    response_model=StandardResponse[CEODashboardSummary],
    summary="CEO 驾驶舱汇总",
    description="获取 CEO 驾驶舱汇总数据，包括项目统计、消耗统计、待处理事项、告警列表"
)
async def get_ceo_dashboard_summary(
    period: Optional[str] = Query(None, description="统计周期 (YYYY-MM)，默认当月"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_ceo_access)
):
    """
    CEO 驾驶舱汇总 API

    权限：仅 admin/ceo 可访问

    返回：
    - 项目总数、活跃项目数
    - 总消耗、总收入、利润率
    - 待审核日报数、待审批充值数
    - 异常告警列表

    Phase 1 行为：
    - 仅展示数据，不阻断任何操作
    """
    try:
        logger.info(
            f"CEO dashboard summary request: user={current_user.id}, period={period}"
        )

        # 解析统计周期
        if period:
            try:
                year, month = map(int, period.split("-"))
                start_date = date(year, month, 1)
                if month == 12:
                    end_date = date(year + 1, 1, 1) - timedelta(days=1)
                else:
                    end_date = date(year, month + 1, 1) - timedelta(days=1)
            except (ValueError, AttributeError):
                start_date = date.today().replace(day=1)
                end_date = date.today()
                period = start_date.strftime("%Y-%m")
        else:
            start_date = date.today().replace(day=1)
            end_date = date.today()
            period = start_date.strftime("%Y-%m")

        # ========== 项目统计 ==========
        total_projects = db.query(func.count(Project.id)).scalar() or 0

        active_projects = db.query(func.count(Project.id)).filter(
            Project.status == ProjectStatus.ACTIVE.value
        ).scalar() or 0

        suspended_projects = db.query(func.count(Project.id)).filter(
            Project.status == ProjectStatus.SUSPENDED.value
        ).scalar() or 0

        # ========== 消耗统计（从日报聚合）==========
        spend_query = db.query(
            func.coalesce(func.sum(DailyReport.raw_spend), Decimal("0.00")).label("total_spend"),
            func.coalesce(func.sum(DailyReport.conversions_final), 0).label("total_conversions")
        ).filter(
            DailyReport.report_date >= start_date,
            DailyReport.report_date <= end_date
        ).first()

        total_spend = spend_query.total_spend if spend_query else Decimal("0.00")
        total_conversions = spend_query.total_conversions if spend_query else 0

        # 计算收入（假设平均单价，实际应从项目配置获取）
        # 这里简化为：从 final_locked 日报计算收入
        revenue_query = db.query(
            func.coalesce(func.sum(
                DailyReport.conversions_final * DailyReport.unit_price
            ), Decimal("0.00")).label("total_revenue")
        ).filter(
            DailyReport.report_date >= start_date,
            DailyReport.report_date <= end_date,
            DailyReport.status == DailyReportStatus.FINAL_LOCKED.value
        ).first()

        total_revenue = revenue_query.total_revenue if revenue_query else Decimal("0.00")

        # 计算利润率
        profit_margin = None
        if total_revenue and total_revenue > 0:
            profit = total_revenue - total_spend
            profit_margin = float(profit / total_revenue)

        # ========== 待处理事项 ==========
        # 待审核日报（需要 data_operator 处理的状态）
        pending_reports = db.query(func.count(DailyReport.id)).filter(
            DailyReport.status.in_([
                DailyReportStatus.TREND_PENDING.value,
                DailyReportStatus.TREND_FLAGGED.value,
                DailyReportStatus.FINAL_PENDING.value
            ])
        ).scalar() or 0

        # 趋势异常数
        trend_flagged_count = db.query(func.count(DailyReport.id)).filter(
            DailyReport.status == DailyReportStatus.TREND_FLAGGED.value
        ).scalar() or 0

        # 待审批充值
        pending_topups = db.query(func.count(TopupRequest.id)).filter(
            TopupRequest.status.in_([
                TopupRequestStatus.PENDING_REVIEW.value,
                TopupRequestStatus.FINANCE_APPROVE.value
            ])
        ).scalar() or 0

        # ========== 告警列表 ==========
        alerts: List[AlertItem] = []

        # 告警 1: 趋势异常日报
        if trend_flagged_count > 0:
            alerts.append(AlertItem(
                type="trend_anomaly",
                severity="high",
                message=f"有 {trend_flagged_count} 个日报存在趋势异常，需人工复核"
            ))

        # 告警 2: 待审批充值积压
        if pending_topups > 5:
            alerts.append(AlertItem(
                type="pending_approval",
                severity="medium",
                message=f"有 {pending_topups} 个充值申请待审批"
            ))

        # 告警 3: 获取消耗超预算的项目
        # （简化实现：检查项目是否有预算字段）
        # 此处需要 Project 模型有 budget 字段，暂时跳过

        # 获取 Phase 信息
        phase_config = get_phase_config()

        # 构建响应
        summary = CEODashboardSummary(
            period=period,
            start_date=start_date,
            end_date=end_date,
            total_projects=total_projects,
            active_projects=active_projects,
            suspended_projects=suspended_projects,
            total_spend=total_spend,
            total_revenue=total_revenue,
            profit_margin=profit_margin,
            pending_reports=pending_reports,
            pending_topups=pending_topups,
            trend_flagged_count=trend_flagged_count,
            alerts=alerts,
            current_phase=2 if phase_config.is_phase2_enabled() else 1
        )

        logger.info(
            f"CEO dashboard summary: total_projects={total_projects}, "
            f"active={active_projects}, spend={total_spend}, "
            f"pending_reports={pending_reports}, alerts={len(alerts)}"
        )

        return success_response(data=summary)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error in CEO dashboard summary: {e}")
        return error_response(
            code=SystemErrorCodes.INTERNAL_ERROR.code,
            message="获取驾驶舱数据失败",
            status_code=SystemErrorCodes.INTERNAL_ERROR.status_code
        )


def _build_ceo_summary(
    period: Optional[str],
    db: Session
) -> CEODashboardSummary:
    """
    内部函数：构建 CEO Dashboard 汇总数据

    被 summary 和 detail 端点共用
    """
    # 解析统计周期
    if period:
        try:
            year, month = map(int, period.split("-"))
            start_date = date(year, month, 1)
            if month == 12:
                end_date = date(year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = date(year, month + 1, 1) - timedelta(days=1)
        except (ValueError, AttributeError):
            start_date = date.today().replace(day=1)
            end_date = date.today()
            period = start_date.strftime("%Y-%m")
    else:
        start_date = date.today().replace(day=1)
        end_date = date.today()
        period = start_date.strftime("%Y-%m")

    # 项目统计
    total_projects = db.query(func.count(Project.id)).scalar() or 0
    active_projects = db.query(func.count(Project.id)).filter(
        Project.status == ProjectStatus.ACTIVE.value
    ).scalar() or 0
    suspended_projects = db.query(func.count(Project.id)).filter(
        Project.status == ProjectStatus.SUSPENDED.value
    ).scalar() or 0

    # 消耗统计
    spend_query = db.query(
        func.coalesce(func.sum(DailyReport.raw_spend), Decimal("0.00")).label("total_spend"),
        func.coalesce(func.sum(DailyReport.conversions_final), 0).label("total_conversions")
    ).filter(
        DailyReport.report_date >= start_date,
        DailyReport.report_date <= end_date
    ).first()

    total_spend = spend_query.total_spend if spend_query else Decimal("0.00")

    # 计算收入
    revenue_query = db.query(
        func.coalesce(func.sum(
            DailyReport.conversions_final * DailyReport.unit_price
        ), Decimal("0.00")).label("total_revenue")
    ).filter(
        DailyReport.report_date >= start_date,
        DailyReport.report_date <= end_date,
        DailyReport.status == DailyReportStatus.FINAL_LOCKED.value
    ).first()

    total_revenue = revenue_query.total_revenue if revenue_query else Decimal("0.00")

    # 计算利润率
    profit_margin = None
    if total_revenue and total_revenue > 0:
        profit = total_revenue - total_spend
        profit_margin = float(profit / total_revenue)

    # 待处理事项
    pending_reports = db.query(func.count(DailyReport.id)).filter(
        DailyReport.status.in_([
            DailyReportStatus.TREND_PENDING.value,
            DailyReportStatus.TREND_FLAGGED.value,
            DailyReportStatus.FINAL_PENDING.value
        ])
    ).scalar() or 0

    trend_flagged_count = db.query(func.count(DailyReport.id)).filter(
        DailyReport.status == DailyReportStatus.TREND_FLAGGED.value
    ).scalar() or 0

    pending_topups = db.query(func.count(TopupRequest.id)).filter(
        TopupRequest.status.in_([
            TopupRequestStatus.PENDING_REVIEW.value,
            TopupRequestStatus.FINANCE_APPROVE.value
        ])
    ).scalar() or 0

    # 告警列表
    alerts: List[AlertItem] = []
    if trend_flagged_count > 0:
        alerts.append(AlertItem(
            type="trend_anomaly",
            severity="high",
            message=f"有 {trend_flagged_count} 个日报存在趋势异常，需人工复核"
        ))
    if pending_topups > 5:
        alerts.append(AlertItem(
            type="pending_approval",
            severity="medium",
            message=f"有 {pending_topups} 个充值申请待审批"
        ))

    # Phase 信息
    phase_config = get_phase_config()

    return CEODashboardSummary(
        period=period,
        start_date=start_date,
        end_date=end_date,
        total_projects=total_projects,
        active_projects=active_projects,
        suspended_projects=suspended_projects,
        total_spend=total_spend,
        total_revenue=total_revenue,
        profit_margin=profit_margin,
        pending_reports=pending_reports,
        pending_topups=pending_topups,
        trend_flagged_count=trend_flagged_count,
        alerts=alerts,
        current_phase=2 if phase_config.is_phase2_enabled() else 1
    )


@router.get(
    "/ceo/detail",
    response_model=StandardResponse[CEODashboardDetail],
    summary="CEO 驾驶舱详细数据",
    description="获取 CEO 驾驶舱详细数据，包括汇总 + 项目排名"
)
async def get_ceo_dashboard_detail(
    period: Optional[str] = Query(None, description="统计周期 (YYYY-MM)"),
    top_n: int = Query(5, ge=1, le=20, description="Top N 项目数"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_ceo_access)
):
    """
    CEO 驾驶舱详细数据 API

    返回：
    - 汇总数据
    - 消耗 Top N 项目
    - ROAS 最差 Top N 项目
    """
    try:
        # 构建汇总数据
        summary = _build_ceo_summary(period, db)

        # 解析日期范围
        start_date = summary.start_date
        end_date = summary.end_date

        # ========== 消耗 Top N 项目 ==========
        top_spend_query = db.query(
            AdAccount.project_id,
            func.sum(DailyReport.raw_spend).label("total_spend"),
            func.sum(DailyReport.follows_count).label("total_follows")
        ).join(
            DailyReport, DailyReport.ad_account_id == AdAccount.id
        ).filter(
            DailyReport.report_date >= start_date,
            DailyReport.report_date <= end_date,
            AdAccount.project_id.isnot(None)
        ).group_by(
            AdAccount.project_id
        ).order_by(
            func.sum(DailyReport.raw_spend).desc()
        ).limit(top_n).all()

        # 获取项目名称
        project_ids = [row.project_id for row in top_spend_query if row.project_id]
        projects = {
            p.id: p.name
            for p in db.query(Project.id, Project.name).filter(Project.id.in_(project_ids)).all()
        } if project_ids else {}

        top_spend_projects = []
        for row in top_spend_query:
            if row.project_id:
                cost_per_follow = None
                if row.total_follows and row.total_follows > 0:
                    cost_per_follow = Decimal(str(row.total_spend)) / Decimal(row.total_follows)

                top_spend_projects.append(ProjectRankingItem(
                    project_id=row.project_id,
                    project_name=projects.get(row.project_id, f"项目 #{row.project_id}"),
                    total_spend=row.total_spend or Decimal("0.00"),
                    total_follows=row.total_follows or 0,
                    cost_per_follow=cost_per_follow
                ))

        # ========== ROAS 最差项目（按单粉成本排序）==========
        worst_roas_query = db.query(
            AdAccount.project_id,
            func.sum(DailyReport.raw_spend).label("total_spend"),
            func.sum(DailyReport.follows_count).label("total_follows")
        ).join(
            DailyReport, DailyReport.ad_account_id == AdAccount.id
        ).filter(
            DailyReport.report_date >= start_date,
            DailyReport.report_date <= end_date,
            AdAccount.project_id.isnot(None),
            DailyReport.follows_count > 0  # 排除零进粉
        ).group_by(
            AdAccount.project_id
        ).having(
            func.sum(DailyReport.follows_count) > 0
        ).order_by(
            (func.sum(DailyReport.raw_spend) / func.sum(DailyReport.follows_count)).desc()
        ).limit(top_n).all()

        worst_roas_projects = []
        for row in worst_roas_query:
            if row.project_id:
                cost_per_follow = None
                if row.total_follows and row.total_follows > 0:
                    cost_per_follow = Decimal(str(row.total_spend)) / Decimal(row.total_follows)

                worst_roas_projects.append(ProjectRankingItem(
                    project_id=row.project_id,
                    project_name=projects.get(row.project_id, f"项目 #{row.project_id}"),
                    total_spend=row.total_spend or Decimal("0.00"),
                    total_follows=row.total_follows or 0,
                    cost_per_follow=cost_per_follow
                ))

        detail = CEODashboardDetail(
            summary=summary,
            top_spend_projects=top_spend_projects,
            worst_roas_projects=worst_roas_projects
        )

        return success_response(data=detail)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error in CEO dashboard detail: {e}")
        return error_response(
            code=SystemErrorCodes.INTERNAL_ERROR.code,
            message="获取驾驶舱详细数据失败",
            status_code=SystemErrorCodes.INTERNAL_ERROR.status_code
        )
