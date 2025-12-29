"""
Dashboard Service - 驾驶舱业务逻辑

SoT Reference: MASTER.md v4.4 - CEO Dashboard

Phase 3 性能优化 (TASK-PERF-001):
- Redis 缓存集成
- KPI/趋势数据缓存
"""

import logging
from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import func, and_
from sqlalchemy.orm import Session

from backend.models import User, DailyReport, Project, AdAccount
from backend.models.workflow.topup_request import TopupRequest
from backend.models.enums import DailyReportStatus, TopupRequestStatus, ProjectStatus

from backend.schemas.dashboard import (
    KpiData, KpiResponse, TrendItem, TrendResponse,
    ProjectRankingItem, RankingResponse, TodoItem, TodoResponse,
    AlertItem, DashboardSummary, DashboardDetail
)
from backend.core.phase_config import get_phase_config
from backend.core.cache import cache_manager

logger = logging.getLogger(__name__)


class DashboardService:
    """Dashboard 业务逻辑服务"""

    def __init__(self, db: Session):
        self.db = db

    # ============ 日期工具 ============

    @staticmethod
    def parse_period(period: Optional[str]) -> Tuple[date, date, str]:
        """
        解析统计周期

        Args:
            period: 周期字符串 (YYYY-MM) 或 None

        Returns:
            (start_date, end_date, period_str)
        """
        if period:
            try:
                year, month = map(int, period.split("-"))
                start_date = date(year, month, 1)
                if month == 12:
                    end_date = date(year + 1, 1, 1) - timedelta(days=1)
                else:
                    end_date = date(year, month + 1, 1) - timedelta(days=1)
                return start_date, end_date, period
            except (ValueError, AttributeError):
                pass

        # 默认当月
        today = date.today()
        start_date = today.replace(day=1)
        end_date = today
        return start_date, end_date, start_date.strftime("%Y-%m")

    @staticmethod
    def get_previous_period(start_date: date, end_date: date) -> Tuple[date, date]:
        """获取上一周期日期范围 (用于环比计算)"""
        days = (end_date - start_date).days + 1
        prev_end = start_date - timedelta(days=1)
        prev_start = prev_end - timedelta(days=days - 1)
        return prev_start, prev_end

    # ============ KPI 计算 ============

    def get_kpi(
        self,
        start_date: date,
        end_date: date,
        project_id: Optional[int] = None,
        include_comparison: bool = True
    ) -> KpiData:
        """
        获取 KPI 数据

        Args:
            start_date: 开始日期
            end_date: 结束日期
            project_id: 项目ID筛选
            include_comparison: 是否包含环比数据

        Returns:
            KpiData
        """
        # 基础查询
        query = self.db.query(
            func.coalesce(func.sum(DailyReport.raw_spend), Decimal("0.00")).label("total_spend"),
            func.coalesce(func.sum(DailyReport.conversions_final), 0).label("total_conversions"),
            func.coalesce(func.sum(DailyReport.follows_count), 0).label("total_follows")
        ).filter(
            DailyReport.report_date >= start_date,
            DailyReport.report_date <= end_date
        )

        # 项目筛选
        if project_id:
            query = query.join(
                AdAccount, AdAccount.id == DailyReport.ad_account_id
            ).filter(AdAccount.project_id == project_id)

        result = query.first()

        total_spend = result.total_spend if result else Decimal("0.00")
        total_conversions = result.total_conversions if result else 0
        total_follows = result.total_follows if result else 0

        # 计算收入 (从已锁定日报)
        revenue_query = self.db.query(
            func.coalesce(func.sum(
                DailyReport.conversions_final * DailyReport.unit_price
            ), Decimal("0.00"))
        ).filter(
            DailyReport.report_date >= start_date,
            DailyReport.report_date <= end_date,
            DailyReport.status == DailyReportStatus.FINAL_LOCKED.value
        )

        if project_id:
            revenue_query = revenue_query.join(
                AdAccount, AdAccount.id == DailyReport.ad_account_id
            ).filter(AdAccount.project_id == project_id)

        total_revenue = revenue_query.scalar() or Decimal("0.00")

        # 计算派生指标
        avg_cpl = None
        if total_follows > 0:
            avg_cpl = total_spend / Decimal(total_follows)

        roi = None
        profit_margin = None
        if total_spend > 0:
            roi = float((total_revenue - total_spend) / total_spend * 100)
        if total_revenue > 0:
            profit_margin = float((total_revenue - total_spend) / total_revenue)

        # 环比计算
        spend_change = None
        conversion_change = None
        cpl_change = None

        if include_comparison:
            prev_start, prev_end = self.get_previous_period(start_date, end_date)
            prev_kpi = self._get_raw_kpi(prev_start, prev_end, project_id)

            if prev_kpi["total_spend"] and prev_kpi["total_spend"] > 0:
                spend_change = float(
                    (total_spend - prev_kpi["total_spend"]) / prev_kpi["total_spend"] * 100
                )

            if prev_kpi["total_follows"] and prev_kpi["total_follows"] > 0:
                conversion_change = float(
                    (total_follows - prev_kpi["total_follows"]) / prev_kpi["total_follows"] * 100
                )

            if prev_kpi["avg_cpl"] and prev_kpi["avg_cpl"] > 0 and avg_cpl:
                cpl_change = float(
                    (avg_cpl - prev_kpi["avg_cpl"]) / prev_kpi["avg_cpl"] * 100
                )

        return KpiData(
            total_spend=total_spend,
            total_conversions=total_conversions,
            total_follows=total_follows,
            total_revenue=total_revenue,
            avg_cpl=avg_cpl,
            roi=roi,
            profit_margin=profit_margin,
            spend_change=spend_change,
            conversion_change=conversion_change,
            cpl_change=cpl_change
        )

    def _get_raw_kpi(
        self,
        start_date: date,
        end_date: date,
        project_id: Optional[int] = None
    ) -> dict:
        """获取原始 KPI 数据 (用于环比计算)"""
        query = self.db.query(
            func.coalesce(func.sum(DailyReport.raw_spend), Decimal("0.00")).label("total_spend"),
            func.coalesce(func.sum(DailyReport.follows_count), 0).label("total_follows")
        ).filter(
            DailyReport.report_date >= start_date,
            DailyReport.report_date <= end_date
        )

        if project_id:
            query = query.join(
                AdAccount, AdAccount.id == DailyReport.ad_account_id
            ).filter(AdAccount.project_id == project_id)

        result = query.first()
        total_spend = result.total_spend if result else Decimal("0.00")
        total_follows = result.total_follows if result else 0

        avg_cpl = None
        if total_follows > 0:
            avg_cpl = total_spend / Decimal(total_follows)

        return {
            "total_spend": total_spend,
            "total_follows": total_follows,
            "avg_cpl": avg_cpl
        }

    # ============ 趋势数据 ============

    def get_trend(
        self,
        start_date: date,
        end_date: date,
        project_id: Optional[int] = None,
        granularity: str = "day"
    ) -> List[TrendItem]:
        """
        获取消耗趋势数据

        Args:
            start_date: 开始日期
            end_date: 结束日期
            project_id: 项目ID筛选
            granularity: 粒度 (day/week/month)

        Returns:
            TrendItem 列表
        """
        # 按日聚合
        query = self.db.query(
            DailyReport.report_date,
            func.sum(DailyReport.raw_spend).label("spend"),
            func.sum(DailyReport.conversions_final).label("conversions"),
            func.sum(DailyReport.follows_count).label("follows")
        ).filter(
            DailyReport.report_date >= start_date,
            DailyReport.report_date <= end_date
        )

        if project_id:
            query = query.join(
                AdAccount, AdAccount.id == DailyReport.ad_account_id
            ).filter(AdAccount.project_id == project_id)

        query = query.group_by(DailyReport.report_date).order_by(DailyReport.report_date)

        results = query.all()

        items = []
        for row in results:
            cpl = None
            if row.follows and row.follows > 0:
                cpl = Decimal(str(row.spend or 0)) / Decimal(row.follows)

            items.append(TrendItem(
                report_date=row.report_date,
                spend=row.spend or Decimal("0.00"),
                conversions=row.conversions or 0,
                follows=row.follows or 0,
                cpl=cpl
            ))

        # TODO: 支持 week/month 粒度聚合

        return items

    # ============ 项目排行 ============

    def get_project_ranking(
        self,
        start_date: date,
        end_date: date,
        ranking_type: str = "spend",
        top_n: int = 10
    ) -> List[ProjectRankingItem]:
        """
        获取项目排行

        Args:
            start_date: 开始日期
            end_date: 结束日期
            ranking_type: 排名类型 (spend/cpl/roas)
            top_n: Top N

        Returns:
            ProjectRankingItem 列表
        """
        base_query = self.db.query(
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
        )

        # 排序
        if ranking_type == "spend":
            base_query = base_query.order_by(func.sum(DailyReport.raw_spend).desc())
        elif ranking_type == "cpl":
            # 按单粉成本降序 (最差排前面)
            base_query = base_query.having(
                func.sum(DailyReport.follows_count) > 0
            ).order_by(
                (func.sum(DailyReport.raw_spend) / func.sum(DailyReport.follows_count)).desc()
            )
        else:
            base_query = base_query.order_by(func.sum(DailyReport.raw_spend).desc())

        results = base_query.limit(top_n).all()

        # 获取项目名称
        project_ids = [row.project_id for row in results if row.project_id]
        projects = {}
        if project_ids:
            project_rows = self.db.query(Project.id, Project.name).filter(
                Project.id.in_(project_ids)
            ).all()
            projects = {p.id: p.name for p in project_rows}

        items = []
        for rank, row in enumerate(results, 1):
            if not row.project_id:
                continue

            cost_per_follow = None
            if row.total_follows and row.total_follows > 0:
                cost_per_follow = Decimal(str(row.total_spend or 0)) / Decimal(row.total_follows)

            items.append(ProjectRankingItem(
                project_id=row.project_id,
                project_name=projects.get(row.project_id, f"项目 #{row.project_id}"),
                total_spend=row.total_spend or Decimal("0.00"),
                total_follows=row.total_follows or 0,
                cost_per_follow=cost_per_follow,
                rank=rank
            ))

        return items

    # ============ 待办事项 ============

    def get_todos(self, user: Optional[User] = None) -> TodoResponse:
        """
        获取待办事项

        Args:
            user: 当前用户 (用于角色过滤)

        Returns:
            TodoResponse
        """
        items = []

        # 1. 待审核日报 (trend_pending + final_pending)
        pending_report_statuses = [
            DailyReportStatus.TREND_PENDING.value,
            DailyReportStatus.FINAL_PENDING.value
        ]
        pending_reports = self.db.query(func.count(DailyReport.id)).filter(
            DailyReport.status.in_(pending_report_statuses)
        ).scalar() or 0

        if pending_reports > 0:
            items.append(TodoItem(
                type="pending_report",
                label="待审核日报",
                count=pending_reports,
                priority="high" if pending_reports > 10 else "normal",
                items=[]
            ))

        # 2. 趋势异常日报
        trend_flagged = self.db.query(func.count(DailyReport.id)).filter(
            DailyReport.status == DailyReportStatus.TREND_FLAGGED.value
        ).scalar() or 0

        if trend_flagged > 0:
            items.append(TodoItem(
                type="trend_flagged",
                label="趋势异常日报",
                count=trend_flagged,
                priority="urgent",
                items=[]
            ))

        # 3. 待审批充值
        pending_topup_statuses = [
            TopupRequestStatus.PENDING_REVIEW.value,
            TopupRequestStatus.FINANCE_APPROVE.value
        ]
        pending_topups = self.db.query(func.count(TopupRequest.id)).filter(
            TopupRequest.status.in_(pending_topup_statuses)
        ).scalar() or 0

        if pending_topups > 0:
            items.append(TodoItem(
                type="pending_topup",
                label="待审批充值",
                count=pending_topups,
                priority="high" if pending_topups > 5 else "normal",
                items=[]
            ))

        total_count = sum(item.count for item in items)

        return TodoResponse(
            total_count=total_count,
            items=items
        )

    # ============ 告警 ============

    def get_alerts(self) -> List[AlertItem]:
        """获取告警列表"""
        alerts = []

        # 趋势异常告警
        trend_flagged = self.db.query(func.count(DailyReport.id)).filter(
            DailyReport.status == DailyReportStatus.TREND_FLAGGED.value
        ).scalar() or 0

        if trend_flagged > 0:
            alerts.append(AlertItem(
                type="trend_anomaly",
                severity="high",
                message=f"有 {trend_flagged} 个日报存在趋势异常，需人工复核"
            ))

        # 充值积压告警
        pending_topups = self.db.query(func.count(TopupRequest.id)).filter(
            TopupRequest.status.in_([
                TopupRequestStatus.PENDING_REVIEW.value,
                TopupRequestStatus.FINANCE_APPROVE.value
            ])
        ).scalar() or 0

        if pending_topups > 5:
            alerts.append(AlertItem(
                type="pending_approval",
                severity="medium",
                message=f"有 {pending_topups} 个充值申请待审批"
            ))

        return alerts

    # ============ 综合汇总 ============

    def get_summary(
        self,
        period: Optional[str] = None,
        project_id: Optional[int] = None
    ) -> DashboardSummary:
        """
        获取 Dashboard 综合汇总

        Args:
            period: 统计周期 (YYYY-MM)
            project_id: 项目ID筛选

        Returns:
            DashboardSummary
        """
        start_date, end_date, period_str = self.parse_period(period)

        # 项目统计
        total_projects = self.db.query(func.count(Project.id)).scalar() or 0
        active_projects = self.db.query(func.count(Project.id)).filter(
            Project.status == ProjectStatus.ACTIVE.value
        ).scalar() or 0
        suspended_projects = self.db.query(func.count(Project.id)).filter(
            Project.status == ProjectStatus.SUSPENDED.value
        ).scalar() or 0

        # KPI
        kpi = self.get_kpi(start_date, end_date, project_id)

        # 待办计数
        todos = self.get_todos()
        pending_reports = sum(
            item.count for item in todos.items
            if item.type in ["pending_report"]
        )
        trend_flagged_count = sum(
            item.count for item in todos.items
            if item.type == "trend_flagged"
        )
        pending_topups = sum(
            item.count for item in todos.items
            if item.type == "pending_topup"
        )

        # 告警
        alerts = self.get_alerts()

        # Phase 信息
        phase_config = get_phase_config()

        return DashboardSummary(
            period=period_str,
            start_date=start_date,
            end_date=end_date,
            total_projects=total_projects,
            active_projects=active_projects,
            suspended_projects=suspended_projects,
            kpi=kpi,
            pending_reports=pending_reports,
            pending_topups=pending_topups,
            trend_flagged_count=trend_flagged_count,
            alerts=alerts,
            current_phase=2 if phase_config.is_phase2_enabled() else 1
        )

    def get_detail(
        self,
        period: Optional[str] = None,
        top_n: int = 5
    ) -> DashboardDetail:
        """
        获取 Dashboard 详细数据

        Args:
            period: 统计周期
            top_n: Top N 项目数

        Returns:
            DashboardDetail
        """
        summary = self.get_summary(period)

        # 趋势数据
        trend_items = self.get_trend(summary.start_date, summary.end_date)
        trend = TrendResponse(
            period=summary.period,
            start_date=summary.start_date,
            end_date=summary.end_date,
            granularity="day",
            items=trend_items
        )

        # 消耗 Top N
        top_spend = self.get_project_ranking(
            summary.start_date, summary.end_date,
            ranking_type="spend", top_n=top_n
        )

        # CPL 最差 Top N
        worst_cpl = self.get_project_ranking(
            summary.start_date, summary.end_date,
            ranking_type="cpl", top_n=top_n
        )

        # 待办
        todos = self.get_todos()

        return DashboardDetail(
            summary=summary,
            trend=trend,
            top_spend_projects=top_spend,
            worst_cpl_projects=worst_cpl,
            todos=todos
        )


# ============ 缓存辅助函数 (Phase 3 TASK-PERF-001) ============


def _serialize_kpi(kpi: KpiData) -> Dict[str, Any]:
    """序列化 KpiData 为可缓存的字典"""
    return {
        "total_spend": str(kpi.total_spend) if kpi.total_spend else None,
        "total_conversions": kpi.total_conversions,
        "total_follows": kpi.total_follows,
        "total_revenue": str(kpi.total_revenue) if kpi.total_revenue else None,
        "avg_cpl": str(kpi.avg_cpl) if kpi.avg_cpl else None,
        "roi": kpi.roi,
        "profit_margin": kpi.profit_margin,
        "spend_change": kpi.spend_change,
        "conversion_change": kpi.conversion_change,
        "cpl_change": kpi.cpl_change,
    }


def _deserialize_kpi(data: Dict[str, Any]) -> KpiData:
    """反序列化字典为 KpiData"""
    return KpiData(
        total_spend=Decimal(data["total_spend"]) if data.get("total_spend") else Decimal("0"),
        total_conversions=data.get("total_conversions", 0),
        total_follows=data.get("total_follows", 0),
        total_revenue=Decimal(data["total_revenue"]) if data.get("total_revenue") else Decimal("0"),
        avg_cpl=Decimal(data["avg_cpl"]) if data.get("avg_cpl") else None,
        roi=data.get("roi"),
        profit_margin=data.get("profit_margin"),
        spend_change=data.get("spend_change"),
        conversion_change=data.get("conversion_change"),
        cpl_change=data.get("cpl_change"),
    )


def _serialize_trend(items: List[TrendItem]) -> List[Dict[str, Any]]:
    """序列化趋势数据"""
    return [
        {
            "report_date": item.report_date.isoformat(),
            "spend": str(item.spend) if item.spend else "0",
            "conversions": item.conversions,
            "follows": item.follows,
            "cpl": str(item.cpl) if item.cpl else None,
        }
        for item in items
    ]


def _deserialize_trend(data: List[Dict[str, Any]]) -> List[TrendItem]:
    """反序列化趋势数据"""
    return [
        TrendItem(
            report_date=date.fromisoformat(item["report_date"]),
            spend=Decimal(item["spend"]) if item.get("spend") else Decimal("0"),
            conversions=item.get("conversions", 0),
            follows=item.get("follows", 0),
            cpl=Decimal(item["cpl"]) if item.get("cpl") else None,
        )
        for item in data
    ]


async def get_kpi_cached(
    db: Session,
    start_date: date,
    end_date: date,
    project_id: Optional[int] = None,
    ttl: int = 60
) -> KpiData:
    """
    获取 KPI 数据 (带缓存)

    Args:
        db: 数据库会话
        start_date: 开始日期
        end_date: 结束日期
        project_id: 项目ID筛选
        ttl: 缓存过期时间 (秒)

    Returns:
        KpiData
    """
    # 构建缓存键
    cache_key = cache_manager.make_key(
        "dashboard", "kpi",
        start_date.isoformat(),
        end_date.isoformat(),
        str(project_id or "all")
    )

    # 尝试从缓存获取
    cached = await cache_manager.get(cache_key)
    if cached:
        logger.debug(f"KPI 缓存命中: {cache_key}")
        return _deserialize_kpi(cached)

    # 查询数据库
    service = DashboardService(db)
    kpi = service.get_kpi(start_date, end_date, project_id)

    # 写入缓存
    await cache_manager.set(cache_key, _serialize_kpi(kpi), ttl=ttl)
    logger.debug(f"KPI 缓存写入: {cache_key}")

    return kpi


async def get_trend_cached(
    db: Session,
    start_date: date,
    end_date: date,
    project_id: Optional[int] = None,
    granularity: str = "day",
    ttl: int = 120
) -> List[TrendItem]:
    """
    获取趋势数据 (带缓存)

    Args:
        db: 数据库会话
        start_date: 开始日期
        end_date: 结束日期
        project_id: 项目ID筛选
        granularity: 粒度
        ttl: 缓存过期时间 (秒)

    Returns:
        TrendItem 列表
    """
    # 构建缓存键
    cache_key = cache_manager.make_key(
        "dashboard", "trend",
        start_date.isoformat(),
        end_date.isoformat(),
        str(project_id or "all"),
        granularity
    )

    # 尝试从缓存获取
    cached = await cache_manager.get(cache_key)
    if cached:
        logger.debug(f"趋势缓存命中: {cache_key}")
        return _deserialize_trend(cached)

    # 查询数据库
    service = DashboardService(db)
    items = service.get_trend(start_date, end_date, project_id, granularity)

    # 写入缓存
    await cache_manager.set(cache_key, _serialize_trend(items), ttl=ttl)
    logger.debug(f"趋势缓存写入: {cache_key}")

    return items


async def get_summary_cached(
    db: Session,
    period: Optional[str] = None,
    project_id: Optional[int] = None,
    ttl: int = 60
) -> DashboardSummary:
    """
    获取 Dashboard 汇总 (带缓存)

    注意: 待办/告警等实时性要求高的数据不缓存
    """
    # 构建缓存键
    cache_key = cache_manager.make_key(
        "dashboard", "summary",
        period or "current",
        str(project_id or "all")
    )

    # 尝试从缓存获取
    cached = await cache_manager.get(cache_key)
    if cached:
        logger.debug(f"汇总缓存命中: {cache_key}")
        # 重新获取实时数据
        service = DashboardService(db)
        todos = service.get_todos()
        alerts = service.get_alerts()

        # 合并缓存的静态数据和实时数据
        start_date, end_date, period_str = DashboardService.parse_period(period)
        kpi = _deserialize_kpi(cached["kpi"])

        return DashboardSummary(
            period=cached["period"],
            start_date=date.fromisoformat(cached["start_date"]),
            end_date=date.fromisoformat(cached["end_date"]),
            total_projects=cached["total_projects"],
            active_projects=cached["active_projects"],
            suspended_projects=cached["suspended_projects"],
            kpi=kpi,
            pending_reports=sum(item.count for item in todos.items if item.type == "pending_report"),
            pending_topups=sum(item.count for item in todos.items if item.type == "pending_topup"),
            trend_flagged_count=sum(item.count for item in todos.items if item.type == "trend_flagged"),
            alerts=alerts,
            current_phase=cached["current_phase"]
        )

    # 查询数据库
    service = DashboardService(db)
    summary = service.get_summary(period, project_id)

    # 只缓存静态部分
    cache_data = {
        "period": summary.period,
        "start_date": summary.start_date.isoformat(),
        "end_date": summary.end_date.isoformat(),
        "total_projects": summary.total_projects,
        "active_projects": summary.active_projects,
        "suspended_projects": summary.suspended_projects,
        "kpi": _serialize_kpi(summary.kpi),
        "current_phase": summary.current_phase,
    }
    await cache_manager.set(cache_key, cache_data, ttl=ttl)
    logger.debug(f"汇总缓存写入: {cache_key}")

    return summary


async def invalidate_dashboard_cache(
    project_id: Optional[int] = None,
    period: Optional[str] = None
):
    """
    失效 Dashboard 相关缓存

    在以下场景调用:
    - 日报提交/审核
    - 充值申请状态变更
    - 项目状态变更

    Args:
        project_id: 指定项目ID
        period: 指定周期
    """
    patterns = [
        "ai_ads:dashboard:kpi:*",
        "ai_ads:dashboard:trend:*",
        "ai_ads:dashboard:summary:*",
    ]

    for pattern in patterns:
        await cache_manager.delete_pattern(pattern)

    logger.info(f"Dashboard 缓存已失效: project_id={project_id}, period={period}")
