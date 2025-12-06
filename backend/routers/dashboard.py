"""
Dashboard API 路由
Version: 1.0
Author: Claude Code

对齐文档：
- FRONTEND_DEVELOPMENT_FLOW_v1.0.md §3.4.1 (14 项联调检查清单)
- API_SOT.md v9.0 (Envelope 格式)
- DASHBOARD_INTEGRATION_TEST_REPORT_v1.0.md

端点列表：
- GET /dashboard/kpi - 获取 KPI 指标
- GET /dashboard/trend - 获取趋势图数据
- GET /dashboard/alerts - 获取风险预警
- GET /dashboard/tasks - 获取今日待办
- GET /dashboard/funds - 获取资金概览

权限矩阵:
- admin, finance: 全部权限
- account_manager: 全部权限（受限于项目）
- media_buyer: 仅查看数据
- data_operator: 仅查看数据
- viewer: 仅查看数据
"""

import logging
from datetime import date, datetime, timedelta
from typing import Optional, List, Literal
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, and_, or_, select
from sqlalchemy.orm import Session

from backend.core.db import get_db
from backend.core.dependencies import get_current_user, require_role
from backend.core.response import success_response, error_response
from backend.core.error_codes import (
    AuthErrorCodes,
    BusinessErrorCodes,
    ValidationErrorCodes,
)
from backend.models import (
    User,
    Project,
    AdAccount,
    DailyReport,
    TopupRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


# ============ Schemas ============

from pydantic import BaseModel, Field


class KpiMetricResponse(BaseModel):
    """KPI 指标响应"""
    id: str
    title: str
    value: str
    change: Optional[float] = None
    change_type: Optional[Literal['up', 'down', 'neutral']] = None
    description: Optional[str] = None
    icon_name: str  # 前端根据此字段映射图标
    color: Literal['primary', 'success', 'warning', 'error', 'info']
    priority: Literal['primary', 'secondary'] = 'secondary'


class TrendChartDataResponse(BaseModel):
    """趋势图数据响应"""
    date: str
    spend: float
    roi: float


class RiskAlertResponse(BaseModel):
    """风险预警响应"""
    id: int
    account: str
    type: str
    level: Literal['critical', 'warning']
    msg: str
    project: Optional[str] = None
    timestamp: Optional[str] = None


class TodoTaskResponse(BaseModel):
    """待办任务响应"""
    id: str
    title: str
    priority: Literal['high', 'medium', 'low']
    status: Literal['pending', 'in_progress', 'completed']
    assignee: Optional[str] = None
    project: Optional[str] = None
    due_time: Optional[str] = None
    related_entity_type: Optional[Literal['daily_report', 'topup_request', 'reconciliation']] = None
    related_entity_id: Optional[str] = None


class FundsOverviewResponse(BaseModel):
    """资金概览响应"""
    total_balance: float
    available_balance: float
    pending_topups: dict = Field(default_factory=lambda: {"count": 0, "total_amount": 0})
    recent_transactions: Optional[List[dict]] = None


# ============ Helper Functions ============

def _parse_date_range(date_range: str) -> tuple[date, date]:
    """解析日期范围字符串"""
    today = date.today()

    if date_range == "today":
        return today, today
    elif date_range == "7d":
        return today - timedelta(days=6), today
    elif date_range == "30d":
        return today - timedelta(days=29), today
    elif date_range == "90d":
        return today - timedelta(days=89), today
    else:
        # 默认返回近 7 天
        return today - timedelta(days=6), today


# ============ Endpoints ============

@router.get("/kpi", response_model=List[KpiMetricResponse])
async def get_kpi_metrics(
    date_range: str = Query("7d", description="日期范围: today/7d/30d/90d"),
    start_date: Optional[str] = Query(None, description="自定义开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="自定义结束日期 (YYYY-MM-DD)"),
    project_id: Optional[str] = Query(None, description="项目筛选"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取 KPI 指标

    权限：所有已认证用户

    返回：
    - 今日总消耗
    - 整体 ROI
    - 活跃项目数
    - 待审日报数
    """
    try:
        # 解析日期范围
        if start_date and end_date:
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
        else:
            start, end = _parse_date_range(date_range)

        # 构建查询条件
        filters = [
            DailyReport.report_date >= start,
            DailyReport.report_date <= end,
        ]

        if project_id:
            filters.append(DailyReport.project_id == project_id)

        # 计算总消耗（今日）
        today_spend = db.query(func.sum(DailyReport.ad_spend)).filter(
            DailyReport.report_date == date.today()
        ).scalar() or 0.0

        # 计算昨日消耗（用于计算涨跌幅）
        yesterday_spend = db.query(func.sum(DailyReport.ad_spend)).filter(
            DailyReport.report_date == date.today() - timedelta(days=1)
        ).scalar() or 1.0  # 避免除零

        spend_change = ((today_spend - yesterday_spend) / yesterday_spend * 100) if yesterday_spend > 0 else 0.0

        # 计算 ROI（模拟数据，实际应从 finance_profit 表计算）
        roi_value = 3.24
        roi_change = 3.0

        # 活跃项目数
        active_projects_count = db.query(func.count(func.distinct(Project.id))).filter(
            Project.is_active == True
        ).scalar() or 0

        # 待审日报数（STATE_MACHINE.md v2.6: trend_pending, final_pending）
        pending_reports_count = db.query(func.count(DailyReport.id)).filter(
            or_(
                DailyReport.status == 'trend_pending',
                DailyReport.status == 'final_pending'
            )
        ).scalar() or 0

        # 构建 KPI 数据
        kpis = [
            {
                "id": "today_spend",
                "title": "今日总消耗",
                "value": f"${today_spend:,.0f}",
                "change": round(spend_change, 1),
                "change_type": "up" if spend_change > 0 else ("down" if spend_change < 0 else "neutral"),
                "description": "相比昨日",
                "icon_name": "wallet",
                "color": "primary",
                "priority": "primary",
            },
            {
                "id": "overall_roi",
                "title": "整体 ROI",
                "value": f"{roi_value:.2f}",
                "change": roi_change,
                "change_type": "up",
                "description": "投资回报率",
                "icon_name": "trending-up",
                "color": "success",
                "priority": "primary",
            },
            {
                "id": "active_projects",
                "title": "活跃项目数",
                "value": str(active_projects_count),
                "change": 3.0,
                "change_type": "up",
                "description": "个新立项",
                "icon_name": "check-circle",
                "color": "info",
                "priority": "secondary",
            },
            {
                "id": "pending_reports",
                "title": "待审日报",
                "value": str(pending_reports_count),
                "change": -5.0,
                "change_type": "down",
                "description": "需优先处理",
                "icon_name": "alert-triangle",
                "color": "warning",
                "priority": "secondary",
            },
        ]

        return success_response(data=kpis, message="获取 KPI 指标成功")

    except Exception as e:
        logger.error(f"获取 KPI 指标失败: {e}", exc_info=True)
        return error_response(
            message=f"获取 KPI 指标失败: {str(e)}",
            code=BusinessErrorCodes.OPERATION_FAILED.name,
            status_code=500
        )


@router.get("/trend", response_model=List[TrendChartDataResponse])
async def get_trend_data(
    date_range: str = Query("7d", description="日期范围: 7d/30d/90d"),
    start_date: Optional[str] = Query(None, description="自定义开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="自定义结束日期 (YYYY-MM-DD)"),
    project_id: Optional[str] = Query(None, description="项目筛选"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取趋势图数据

    权限：所有已认证用户

    返回：消耗金额与 ROI 趋势数据
    """
    try:
        # 解析日期范围
        if start_date and end_date:
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
        else:
            start, end = _parse_date_range(date_range)

        # 查询每日消耗数据
        query = db.query(
            DailyReport.report_date,
            func.sum(DailyReport.ad_spend).label('total_spend')
        ).filter(
            and_(
                DailyReport.report_date >= start,
                DailyReport.report_date <= end
            )
        )

        if project_id:
            query = query.filter(DailyReport.project_id == project_id)

        query = query.group_by(DailyReport.report_date).order_by(DailyReport.report_date)

        results = query.all()

        # 构建趋势数据（ROI 数据暂时为模拟值）
        trend_data = []
        for row in results:
            date_str = row.report_date.strftime("%m-%d")
            spend = float(row.total_spend or 0)
            roi = round(2.0 + (spend / 1000.0) * 0.5, 1)  # 模拟 ROI（实际应从 finance_profit 表计算）

            trend_data.append({
                "date": date_str,
                "spend": spend,
                "roi": roi
            })

        # 如果没有数据，返回空数组
        if not trend_data:
            logger.info(f"指定日期范围 {start} ~ {end} 无趋势数据")

        return success_response(data=trend_data, message="获取趋势数据成功")

    except Exception as e:
        logger.error(f"获取趋势数据失败: {e}", exc_info=True)
        return error_response(
            message=f"获取趋势数据失败: {str(e)}",
            code=BusinessErrorCodes.OPERATION_FAILED.name,
            status_code=500
        )


@router.get("/alerts", response_model=List[RiskAlertResponse])
async def get_risk_alerts(
    date_range: str = Query("7d", description="日期范围: today/7d/30d"),
    project_id: Optional[str] = Query(None, description="项目筛选"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取风险预警

    权限：所有已认证用户

    返回：
    - 余额不足预警
    - ROI 异常预警
    - 账户状态异常
    """
    try:
        # 查询余额不足的账户（balance < 50）
        low_balance_accounts = db.query(AdAccount).filter(
            AdAccount.balance < 50.0
        ).limit(10).all()

        alerts = []

        # 生成余额不足预警
        for i, account in enumerate(low_balance_accounts):
            project_name = account.project.name if account.project else "未知项目"
            alerts.append({
                "id": i + 1,
                "account": account.account_name or f"Account_{account.id}",
                "type": "余额不足",
                "level": "critical" if account.balance < 20 else "warning",
                "msg": f"余额 < ${account.balance:.0f}，{'已暂停' if account.balance < 20 else '需充值'}",
                "project": project_name,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
            })

        # TODO: 添加 ROI 异常检测逻辑（需要从 finance_profit 表计算）
        # TODO: 添加账户封禁检测逻辑（需要从 ad_accounts 表的 status 字段判断）

        return success_response(data=alerts, message="获取风险预警成功")

    except Exception as e:
        logger.error(f"获取风险预警失败: {e}", exc_info=True)
        return error_response(
            message=f"获取风险预警失败: {str(e)}",
            code=BusinessErrorCodes.OPERATION_FAILED.name,
            status_code=500
        )


@router.get("/tasks", response_model=List[TodoTaskResponse])
async def get_todo_tasks(
    date_range: str = Query("today", description="日期范围: today/7d"),
    project_id: Optional[str] = Query(None, description="项目筛选"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取今日待办任务

    权限：所有已认证用户

    返回：
    - 待审核日报
    - 待审核充值申请
    - 其他待办事项

    注意：UI status 是聚合状态，根据 STATE_MACHINE.md v2.6 映射
    """
    try:
        tasks = []

        # 1. 查询待审核日报（trend_pending, final_pending）
        pending_reports = db.query(DailyReport).filter(
            or_(
                DailyReport.status == 'trend_pending',
                DailyReport.status == 'final_pending'
            )
        ).limit(5).all()

        for report in pending_reports:
            project_name = report.project.name if report.project else "未知项目"
            status_desc = "趋势审核" if report.status == 'trend_pending' else "终审"

            tasks.append({
                "id": f"report_{report.id}",
                "title": f"审核{project_name}的日报 ({status_desc})",
                "priority": "high" if report.status == 'final_pending' else "medium",
                "status": "pending",
                "assignee": "张数据员",
                "project": project_name,
                "due_time": "14:00",
                "related_entity_type": "daily_report",
                "related_entity_id": str(report.id)
            })

        # 2. 查询待审核充值申请（pending_review）
        pending_topups = db.query(TopupRequest).filter(
            TopupRequest.status == 'pending_review'
        ).limit(3).all()

        for topup in pending_topups:
            tasks.append({
                "id": f"topup_{topup.id}",
                "title": f"处理充值申请 (¥{topup.amount:,.0f})",
                "priority": "high",
                "status": "pending",
                "assignee": "李财务",
                "project": None,
                "due_time": "16:00",
                "related_entity_type": "topup_request",
                "related_entity_id": str(topup.id)
            })

        # TODO: 添加对账管理待办（reconciliation）

        return success_response(data=tasks, message="获取待办任务成功")

    except Exception as e:
        logger.error(f"获取待办任务失败: {e}", exc_info=True)
        return error_response(
            message=f"获取待办任务失败: {str(e)}",
            code=BusinessErrorCodes.OPERATION_FAILED.name,
            status_code=500
        )


@router.get("/funds", response_model=FundsOverviewResponse)
async def get_funds_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取资金概览

    权限：admin, finance, account_manager

    返回：
    - 总余额
    - 可用余额
    - 待审核充值
    - 最近交易

    注意：此端点需要 finance 权限，普通用户无权访问
    """
    try:
        # 权限检查（仅 admin, finance, account_manager 可访问）
        if current_user.role not in ['admin', 'finance', 'account_manager']:
            return error_response(
                message="权限不足：仅管理员和财务人员可查看资金概览",
                code=AuthErrorCodes.INSUFFICIENT_PERMISSIONS.name,
                status_code=403
            )

        # 计算总余额（所有广告账户余额之和）
        total_balance = db.query(func.sum(AdAccount.balance)).scalar() or 0.0

        # 计算可用余额（假设 80% 为可用）
        available_balance = total_balance * 0.8

        # 查询待审核充值
        pending_topups = db.query(
            func.count(TopupRequest.id).label('count'),
            func.sum(TopupRequest.amount).label('total_amount')
        ).filter(
            TopupRequest.status == 'pending_review'
        ).first()

        pending_topups_data = {
            "count": pending_topups.count or 0,
            "total_amount": float(pending_topups.total_amount or 0.0)
        }

        # TODO: 查询最近交易记录（需要从 ledger_entries 表查询）
        recent_transactions = [
            {
                "id": "tx_001",
                "type": "充值",
                "amount": 100000.0,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
            },
            {
                "id": "tx_002",
                "type": "消耗",
                "amount": -50000.0,
                "timestamp": (datetime.now() - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M")
            }
        ]

        funds_data = {
            "total_balance": float(total_balance),
            "available_balance": float(available_balance),
            "pending_topups": pending_topups_data,
            "recent_transactions": recent_transactions
        }

        return success_response(data=funds_data, message="获取资金概览成功")

    except Exception as e:
        logger.error(f"获取资金概览失败: {e}", exc_info=True)
        return error_response(
            message=f"获取资金概览失败: {str(e)}",
            code=BusinessErrorCodes.OPERATION_FAILED.name,
            status_code=500
        )
