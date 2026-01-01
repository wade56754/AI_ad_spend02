"""
周报管理业务逻辑层 (重构版)

SoT References:
- B3-weekly-brief.md §6.2 业务逻辑
- MASTER.md v4.4 §2.4 (7角色模型)
- DATA_SCHEMA.md v5.3 (weekly_briefs 表)

依赖代码块:
- permission-filter: 权限过滤
- kpi-calculator: CPL 计算

权限矩阵 (MASTER.md v4.8 §2.4 - 6角色模型):
- ceo, admin: 全部周报
- finance: 全部周报 (只读)
- project_owner: 自己负责的项目周报
- pitcher: 无权访问
- account_manager: 无权访问

Version: 2.0
Author: Claude Code
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, or_, func, desc
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError

from backend.exceptions.custom_exceptions import (
    BusinessLogicError,
    ResourceNotFoundError,
    PermissionDeniedError,
    ResourceConflictError,
)
from backend.models import (
    WeeklyBrief,
    WeeklyBriefStatus,
    Project,
    User,
    DailyReport,
    AdSpendDaily,
    AdAccount,
    UserRole,
)
from backend.schemas.weekly_brief import (
    WeeklyBriefCreateRequest,
    WeeklyBriefUpdateRequest,
    WeeklyBriefResponse,
    WeeklyBriefStatsResponse,
    WeeklySummaryResponse,
    WeeklyTrendData,
    LastWeekData,
    DailyBreakdown,
)


def get_week_end(week_start: date) -> date:
    """根据周一获取周日"""
    return week_start + timedelta(days=6)


def get_week_label(week_start: date) -> str:
    """获取周次标签 (如 "2025年第51周")"""
    year, week_num, _ = week_start.isocalendar()
    return f"{year}年第{week_num}周"


class WeeklyBriefService:
    """周报管理服务类"""

    def __init__(self, db: Session):
        self.db = db

    # ========== 创建周报 ==========

    def create_weekly_brief(
        self, request: WeeklyBriefCreateRequest, current_user: User
    ) -> WeeklyBrief:
        """
        创建周报

        业务规则 (B3-weekly-brief.md §7.1):
        - BR-BRIEF-001: 每项目每周只能有一份周报
        - BR-BRIEF-002: 只有 project_owner 可创建
        - BR-BRIEF-003: week_start 必须是周一
        - BR-BRIEF-004: 创建时自动汇总周消耗/进粉
        """
        # 验证权限
        if current_user.role not in [
            UserRole.ADMIN.value,
            UserRole.PROJECT_OWNER.value,
        ]:
            raise PermissionDeniedError("权限不足：只有项目负责人可以创建周报")

        # 验证项目存在
        project = (
            self.db.query(Project).filter(Project.id == request.project_id).first()
        )
        if not project:
            raise ResourceNotFoundError(f"项目 {request.project_id} 不存在")

        # 检查权限：项目负责人只能创建自己项目的周报
        if current_user.role == UserRole.PROJECT_OWNER.value:
            if not self._is_project_owner(current_user.id, request.project_id):
                raise PermissionDeniedError("权限不足：只能创建自己负责的项目周报")

        # 检查唯一性
        existing = (
            self.db.query(WeeklyBrief)
            .filter(
                WeeklyBrief.project_id == request.project_id,
                WeeklyBrief.week_start == request.week_start,
            )
            .first()
        )
        if existing:
            raise ResourceConflictError(
                f"项目 {request.project_id} 在 {request.week_start} 周已有周报"
            )

        # 计算周结束日期
        week_end = get_week_end(request.week_start)

        # 获取周数据汇总
        summary = self._aggregate_weekly_data(
            request.project_id, request.week_start, week_end
        )

        # 创建周报
        brief = WeeklyBrief(
            project_id=request.project_id,
            week_start=request.week_start,
            week_end=week_end,
            submitter_id=current_user.id,
            status=WeeklyBriefStatus.DRAFT.value,
            weekly_spend=summary["spend"],
            weekly_conversions=summary["conversions"],
            weekly_cpl=summary["cpl"],
            achievements=request.achievements,
            issues=request.issues,
            solutions=request.solutions,
            next_week_plan=request.next_week_plan,
        )

        self.db.add(brief)
        self.db.commit()
        self.db.refresh(brief)

        return brief

    # ========== 更新周报 ==========

    def update_weekly_brief(
        self, brief_id: int, request: WeeklyBriefUpdateRequest, current_user: User
    ) -> WeeklyBrief:
        """
        更新周报

        业务规则:
        - 只能更新草稿状态的周报
        - 项目负责人只能更新自己项目的周报
        """
        brief = self.get_weekly_brief(brief_id, current_user)

        # 验证状态
        if not brief.is_draft:
            raise BusinessLogicError("只能编辑草稿状态的周报")

        # 验证权限
        if current_user.role == UserRole.PROJECT_OWNER.value:
            if not self._is_project_owner(current_user.id, brief.project_id):
                raise PermissionDeniedError("权限不足：只能编辑自己负责的项目周报")

        # 更新内容
        if request.achievements is not None:
            brief.achievements = request.achievements
        if request.issues is not None:
            brief.issues = request.issues
        if request.solutions is not None:
            brief.solutions = request.solutions
        if request.next_week_plan is not None:
            brief.next_week_plan = request.next_week_plan

        # 刷新汇总数据
        summary = self._aggregate_weekly_data(
            brief.project_id, brief.week_start, brief.week_end
        )
        brief.weekly_spend = summary["spend"]
        brief.weekly_conversions = summary["conversions"]
        brief.weekly_cpl = summary["cpl"]

        self.db.commit()
        self.db.refresh(brief)

        return brief

    # ========== 提交周报 ==========

    def submit_weekly_brief(self, brief_id: int, current_user: User) -> WeeklyBrief:
        """
        提交周报

        业务规则 (B3-weekly-brief.md §7.2):
        - BR-BRIEF-010: Phase 1 无强制必填
        - BR-BRIEF-011: 提交后状态变为 submitted，不可修改
        - BR-BRIEF-012: 提交时记录 submitted_at
        """
        brief = self.get_weekly_brief(brief_id, current_user)

        # 验证状态
        if not brief.is_draft:
            raise BusinessLogicError("只能提交草稿状态的周报")

        # 验证权限
        if current_user.role == UserRole.PROJECT_OWNER.value:
            if not self._is_project_owner(current_user.id, brief.project_id):
                raise PermissionDeniedError("权限不足：只能提交自己负责的项目周报")

        # 刷新汇总数据
        summary = self._aggregate_weekly_data(
            brief.project_id, brief.week_start, brief.week_end
        )
        brief.weekly_spend = summary["spend"]
        brief.weekly_conversions = summary["conversions"]
        brief.weekly_cpl = summary["cpl"]

        # 提交
        brief.submit(current_user.id)

        self.db.commit()
        self.db.refresh(brief)

        return brief

    # ========== 获取周报 ==========

    def get_weekly_brief(self, brief_id: int, current_user: User) -> WeeklyBrief:
        """获取周报详情"""
        brief = (
            self.db.query(WeeklyBrief)
            .options(joinedload(WeeklyBrief.project), joinedload(WeeklyBrief.submitter))
            .filter(WeeklyBrief.id == brief_id)
            .first()
        )

        if not brief:
            raise ResourceNotFoundError(f"周报 {brief_id} 不存在")

        # 权限检查
        if not self._can_access_brief(current_user, brief):
            raise PermissionDeniedError("权限不足：无法查看该周报")

        return brief

    def get_weekly_briefs(
        self,
        current_user: User,
        week_start: Optional[date] = None,
        project_id: Optional[int] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[WeeklyBrief], int]:
        """
        获取周报列表

        权限过滤:
        - ceo/admin: 全部
        - project_owner: 自己项目或全部
        - finance: 全部 (只读)
        """
        query = self.db.query(WeeklyBrief).options(
            joinedload(WeeklyBrief.project), joinedload(WeeklyBrief.submitter)
        )

        # 权限过滤
        query = self._apply_permission_filter(query, current_user)

        # 筛选条件
        if week_start:
            query = query.filter(WeeklyBrief.week_start == week_start)
        if project_id:
            query = query.filter(WeeklyBrief.project_id == project_id)
        if status:
            query = query.filter(WeeklyBrief.status == status)

        # 统计总数
        total = query.count()

        # 分页
        briefs = (
            query.order_by(desc(WeeklyBrief.week_start), WeeklyBrief.project_id)
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        return briefs, total

    # ========== 统计 ==========

    def get_weekly_brief_stats(
        self, current_user: User, week_start: Optional[date] = None
    ) -> WeeklyBriefStatsResponse:
        """
        获取周报统计

        对齐 B3-weekly-brief.md §4.2
        """
        # 默认使用本周
        if not week_start:
            today = date.today()
            week_start = today - timedelta(days=today.weekday())

        week_end = get_week_end(week_start)

        # 获取活跃项目数
        project_query = self.db.query(func.count(Project.id)).filter(
            Project.status == "active"
        )
        # 应用权限过滤
        if current_user.role == UserRole.PROJECT_OWNER.value:
            project_ids = self._get_user_project_ids(current_user.id)
            project_query = project_query.filter(Project.id.in_(project_ids))

        total_projects = project_query.scalar() or 0

        # 获取周报统计
        brief_query = self.db.query(WeeklyBrief).filter(
            WeeklyBrief.week_start == week_start
        )
        # 应用权限过滤
        brief_query = self._apply_permission_filter(brief_query, current_user)

        submitted_count = brief_query.filter(
            WeeklyBrief.status == WeeklyBriefStatus.SUBMITTED.value
        ).count()

        draft_count = brief_query.filter(
            WeeklyBrief.status == WeeklyBriefStatus.DRAFT.value
        ).count()

        # 计算提交率
        submission_rate = Decimal("0")
        if total_projects > 0:
            submission_rate = Decimal(submitted_count) / Decimal(total_projects) * 100

        # 计算总消耗
        total_spend = brief_query.with_entities(
            func.coalesce(func.sum(WeeklyBrief.weekly_spend), 0)
        ).scalar() or Decimal("0")

        return WeeklyBriefStatsResponse(
            total_projects=total_projects,
            submitted_count=submitted_count,
            draft_count=draft_count,
            submission_rate=submission_rate,
            total_weekly_spend=total_spend,
        )

    # ========== 周数据汇总 ==========

    def get_project_weekly_summary(
        self, project_id: int, week_start: date, current_user: User
    ) -> WeeklySummaryResponse:
        """
        获取项目周数据汇总

        对齐 B3-weekly-brief.md §4.2 项目周数据汇总
        """
        # 验证项目存在
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ResourceNotFoundError(f"项目 {project_id} 不存在")

        # 权限检查
        if current_user.role == UserRole.PROJECT_OWNER.value:
            if not self._is_project_owner(current_user.id, project_id):
                raise PermissionDeniedError("权限不足：无法查看该项目数据")

        week_end = get_week_end(week_start)
        last_week_start = week_start - timedelta(days=7)
        last_week_end = week_end - timedelta(days=7)

        # 本周数据
        current = self._aggregate_weekly_data(project_id, week_start, week_end)

        # 上周数据
        last = self._aggregate_weekly_data(project_id, last_week_start, last_week_end)

        # 计算趋势
        trends = None
        last_week_data = None
        if last["spend"] > 0 or last["conversions"] > 0:
            last_week_data = LastWeekData(
                spend=last["spend"], conversions=last["conversions"], cpl=last["cpl"]
            )
            trends = WeeklyTrendData(
                spend_change=self._calc_change(current["spend"], last["spend"]),
                conversions_change=self._calc_change(
                    Decimal(current["conversions"]), Decimal(last["conversions"])
                ),
                cpl_change=self._calc_change(current["cpl"], last["cpl"]),
            )

        # 获取每日明细
        daily_breakdown = self._get_daily_breakdown(project_id, week_start, week_end)

        # 目标 CPL
        target_cpl = getattr(project, "target_cpl", None)
        cpl_vs_target = None
        if target_cpl and target_cpl > 0 and current["cpl"] > 0:
            cpl_vs_target = (current["cpl"] - target_cpl) / target_cpl * 100

        return WeeklySummaryResponse(
            project_id=project_id,
            project_name=project.name,
            week_start=week_start,
            week_end=week_end,
            weekly_spend=current["spend"],
            weekly_conversions=current["conversions"],
            weekly_cpl=current["cpl"],
            target_cpl=target_cpl,
            cpl_vs_target=cpl_vs_target,
            last_week=last_week_data,
            trends=trends,
            daily_breakdown=daily_breakdown,
        )

    # ========== 私有方法 ==========

    def _aggregate_weekly_data(
        self, project_id: int, week_start: date, week_end: date
    ) -> dict:
        """
        汇总项目周数据

        SoT: B3-weekly-brief.md §2.4
        - 周消耗: SUM(ad_spend_daily.spend) WHERE date BETWEEN week_start AND week_end
        - 周进粉: SUM(daily_reports.conversions) WHERE date BETWEEN week_start AND week_end
        - 周 CPL: 周消耗 / 周进粉
        """
        # 获取项目下的账户
        account_ids = (
            self.db.query(AdAccount.id)
            .filter(AdAccount.project_id == project_id)
            .subquery()
        )

        # 汇总消耗
        spend_result = (
            self.db.query(func.coalesce(func.sum(AdSpendDaily.spend), 0))
            .filter(
                AdSpendDaily.ad_account_id.in_(account_ids),
                AdSpendDaily.spend_date >= week_start,
                AdSpendDaily.spend_date <= week_end,
            )
            .scalar()
        )
        spend = Decimal(str(spend_result or 0))

        # 汇总进粉
        conversions_result = (
            self.db.query(func.coalesce(func.sum(DailyReport.conversions_final), 0))
            .filter(
                DailyReport.ad_account_id.in_(account_ids),
                DailyReport.report_date >= week_start,
                DailyReport.report_date <= week_end,
            )
            .scalar()
        )
        conversions = int(conversions_result or 0)

        # 计算 CPL
        cpl = Decimal("0")
        if conversions > 0:
            cpl = spend / Decimal(conversions)

        return {
            "spend": spend,
            "conversions": conversions,
            "cpl": cpl.quantize(Decimal("0.01")),
        }

    def _get_daily_breakdown(
        self, project_id: int, week_start: date, week_end: date
    ) -> List[DailyBreakdown]:
        """获取每日明细"""
        account_ids = (
            self.db.query(AdAccount.id)
            .filter(AdAccount.project_id == project_id)
            .subquery()
        )

        results = (
            self.db.query(
                AdSpendDaily.spend_date,
                func.coalesce(func.sum(AdSpendDaily.spend), 0).label("spend"),
            )
            .filter(
                AdSpendDaily.ad_account_id.in_(account_ids),
                AdSpendDaily.spend_date >= week_start,
                AdSpendDaily.spend_date <= week_end,
            )
            .group_by(AdSpendDaily.spend_date)
            .order_by(AdSpendDaily.spend_date)
            .all()
        )

        # 获取进粉数据
        conversions_data = {}
        conv_results = (
            self.db.query(
                DailyReport.report_date,
                func.coalesce(func.sum(DailyReport.conversions_final), 0).label(
                    "conversions"
                ),
            )
            .filter(
                DailyReport.ad_account_id.in_(account_ids),
                DailyReport.report_date >= week_start,
                DailyReport.report_date <= week_end,
            )
            .group_by(DailyReport.report_date)
            .all()
        )
        for row in conv_results:
            conversions_data[row.report_date] = row.conversions

        return [
            DailyBreakdown(
                date=row.spend_date,
                spend=Decimal(str(row.spend)),
                conversions=conversions_data.get(row.spend_date, 0),
            )
            for row in results
        ]

    def _calc_change(self, current: Decimal, previous: Decimal) -> Decimal:
        """计算环比变化百分比"""
        if previous == 0:
            return Decimal("0")
        return ((current - previous) / previous * 100).quantize(Decimal("0.1"))

    def _is_project_owner(self, user_id: UUID, project_id: int) -> bool:
        """检查用户是否是项目负责人"""
        # 这里需要根据实际的项目成员表来判断
        # 简化实现：检查 Project.owner_id 或 ProjectMember
        from backend.models import ProjectMember

        member = (
            self.db.query(ProjectMember)
            .filter(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == user_id,
                ProjectMember.role == "owner",
            )
            .first()
        )
        return member is not None

    def _get_user_project_ids(self, user_id: UUID) -> List[int]:
        """获取用户负责的项目 ID 列表"""
        from backend.models import ProjectMember

        results = (
            self.db.query(ProjectMember.project_id)
            .filter(ProjectMember.user_id == user_id, ProjectMember.role == "owner")
            .all()
        )
        return [r.project_id for r in results]

    def _can_access_brief(self, user: User, brief: WeeklyBrief) -> bool:
        """检查用户是否可以访问周报"""
        # 管理员可以访问所有
        if user.role in [UserRole.ADMIN.value]:
            return True

        # 财务可以查看所有 (只读)
        if user.role == UserRole.FINANCE.value:
            return True

        # 项目负责人只能访问自己项目的
        if user.role == UserRole.PROJECT_OWNER.value:
            return self._is_project_owner(user.id, brief.project_id)

        # project_owner/ceo 可以访问项目 (MASTER.md v4.8 §2.4)
        if user.role in ["project_owner", "ceo"]:
            return True

        return False

    def _apply_permission_filter(self, query, user: User):
        """
        应用权限过滤 (MASTER.md v4.8 §2.4)

        - ceo, admin, finance, project_owner: 全部周报
        - pitcher, account_manager: 无权访问
        """
        # 管理员、财务、项目负责人、ceo 可以访问所有
        if user.role in ["admin", "finance", "project_owner", "ceo"]:
            return query

        # 项目负责人只能访问自己项目的
        if user.role == UserRole.PROJECT_OWNER.value:
            project_ids = self._get_user_project_ids(user.id)
            return query.filter(WeeklyBrief.project_id.in_(project_ids))

        # 其他角色：不允许访问
        return query.filter(False)
