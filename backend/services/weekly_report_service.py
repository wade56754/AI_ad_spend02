"""
周报 Service (TASK-WEEKLY-002, TASK-WEEKLY-003, TASK-WEEKLY-004)

SoT References:
- DATA_SCHEMA.md v5.6 §weekly_briefs
- B3-weekly-brief.md §6.2
- STATE_MACHINE.md v2.6 §13.2 (周报状态机)
- MASTER.md v4.6 §2.4 (6角色模型)

权限矩阵:
- project_owner: 创建/更新/提交自己项目的周报
- admin: 创建/更新/提交任意项目周报

Version: 1.2
"""

import logging
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import func
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
    ProjectMember,
)
from backend.schemas.weekly_report import WeeklyReportCreate, WeeklyReportUpdate, WeeklyReportResponse


logger = logging.getLogger(__name__)


def get_week_end(week_start: date) -> date:
    """根据周一获取周日"""
    return week_start + timedelta(days=6)


class WeeklyReportService:
    """
    周报管理服务 (TASK-WEEKLY-002)

    SoT: B3-weekly-brief.md §6.2
    """

    def __init__(self, db: Session):
        self.db = db

    def create_weekly_report(
        self,
        request: WeeklyReportCreate,
        current_user: User
    ) -> WeeklyBrief:
        """
        创建周报 (TASK-WEEKLY-002)

        业务规则:
        - BR-BRIEF-001: 每项目每周只能有一份周报
        - BR-BRIEF-002: project_owner 可创建自己项目的周报
        - BR-BRIEF-003: week_start_date 必须是周一

        错误处理:
        - BIZ_001: 该周周报已存在
        """
        logger.info(
            f"创建周报: user={current_user.email}, "
            f"project_id={request.project_id}, week={request.week_start_date}"
        )

        # 验证权限 (MASTER.md v4.6 §2.4)
        if current_user.role not in [UserRole.ADMIN.value, UserRole.PROJECT_OWNER.value, "admin", "project_owner"]:
            raise PermissionDeniedError("权限不足：只有项目负责人或管理员可以创建周报")

        # 验证项目存在
        project = self.db.query(Project).filter(Project.id == request.project_id).first()
        if not project:
            raise ResourceNotFoundError(f"项目 {request.project_id} 不存在")

        # project_owner 只能创建自己项目的周报
        if current_user.role in [UserRole.PROJECT_OWNER.value, "project_owner"]:
            if not self._is_project_owner(current_user.id, request.project_id):
                raise PermissionDeniedError("权限不足：只能创建自己负责的项目周报")

        # BR-BRIEF-001: 检查唯一性 - 同一项目同一周不可重复创建
        existing = self.db.query(WeeklyBrief).filter(
            WeeklyBrief.project_id == request.project_id,
            WeeklyBrief.week_start == request.week_start_date
        ).first()

        if existing:
            raise BusinessLogicError(
                f"该周周报已存在 (项目 {request.project_id}, 周 {request.week_start_date})"
            )

        # 计算周结束日期
        week_end = get_week_end(request.week_start_date)

        # 获取周数据汇总
        summary = self._aggregate_weekly_data(request.project_id, request.week_start_date, week_end)

        # 创建周报
        brief = WeeklyBrief(
            project_id=request.project_id,
            week_start=request.week_start_date,
            week_end=week_end,
            submitter_id=current_user.id,
            status=WeeklyBriefStatus.DRAFT.value,
            weekly_spend=summary['spend'],
            weekly_conversions=summary['conversions'],
            weekly_cpl=summary['cpl'],
            achievements=request.achievements,
            issues=request.issues,
            solutions=request.solutions,
            next_week_plan=request.next_week_plan,
        )

        try:
            self.db.add(brief)
            self.db.commit()
            self.db.refresh(brief)
        except IntegrityError as e:
            self.db.rollback()
            # 可能是唯一约束冲突
            if 'uq_weekly_briefs_project_week' in str(e):
                raise BusinessLogicError("该周周报已存在")
            raise

        logger.info(f"周报创建成功: id={brief.id}")
        return brief

    def get_weekly_report(
        self,
        report_id: int,
        current_user: User
    ) -> WeeklyBrief:
        """
        获取周报详情 (TASK-WEEKLY-003)

        权限:
        - admin: 所有周报
        - project_owner: 自己项目的周报
        """
        brief = self.db.query(WeeklyBrief).options(
            joinedload(WeeklyBrief.project),
            joinedload(WeeklyBrief.submitter)
        ).filter(WeeklyBrief.id == report_id).first()

        if not brief:
            raise ResourceNotFoundError(f"周报 {report_id} 不存在")

        # 权限检查
        if current_user.role not in ["admin", UserRole.ADMIN.value]:
            if current_user.role in [UserRole.PROJECT_OWNER.value, "project_owner"]:
                if not self._is_project_owner(current_user.id, brief.project_id):
                    raise PermissionDeniedError("权限不足：无法查看该周报")
            else:
                raise PermissionDeniedError("权限不足：无法查看该周报")

        return brief

    def update_weekly_report(
        self,
        report_id: int,
        request: WeeklyReportUpdate,
        current_user: User
    ) -> WeeklyBrief:
        """
        更新周报 (TASK-WEEKLY-003)

        业务规则:
        - 只能更新 draft 状态的周报
        - project_owner 只能更新自己项目的周报
        - 更新时自动刷新汇总数据

        错误处理:
        - RES-001: 周报不存在
        - BIZ_002: 只能编辑草稿状态的周报
        - PERM-001: 权限不足
        """
        logger.info(
            f"更新周报: user={current_user.email}, report_id={report_id}"
        )

        # 获取周报
        brief = self.get_weekly_report(report_id, current_user)

        # 验证状态 - 只能更新 draft 状态
        if brief.status != WeeklyBriefStatus.DRAFT.value:
            raise BusinessLogicError("只能编辑草稿状态的周报")

        # 验证权限 - project_owner 只能更新自己项目
        if current_user.role in [UserRole.PROJECT_OWNER.value, "project_owner"]:
            if not self._is_project_owner(current_user.id, brief.project_id):
                raise PermissionDeniedError("权限不足：只能编辑自己负责的项目周报")

        # 更新内容字段 (只更新提供的字段)
        if request.achievements is not None:
            brief.achievements = request.achievements
        if request.issues is not None:
            brief.issues = request.issues
        if request.solutions is not None:
            brief.solutions = request.solutions
        if request.next_week_plan is not None:
            brief.next_week_plan = request.next_week_plan

        # 刷新汇总数据
        summary = self._aggregate_weekly_data(brief.project_id, brief.week_start, brief.week_end)
        brief.weekly_spend = summary['spend']
        brief.weekly_conversions = summary['conversions']
        brief.weekly_cpl = summary['cpl']

        self.db.commit()
        self.db.refresh(brief)

        logger.info(f"周报更新成功: id={brief.id}")
        return brief

    def submit_weekly_report(
        self,
        report_id: int,
        current_user: User
    ) -> WeeklyBrief:
        """
        提交周报 (TASK-WEEKLY-004)

        状态机 (STATE_MACHINE.md v2.6 §13.2):
        - draft → submitted (终态)

        业务规则:
        - BR-SUBMIT-001: 只能提交 draft 状态的周报
        - BR-SUBMIT-002: project_owner 只能提交自己项目的周报
        - BR-SUBMIT-003: 提交时自动刷新汇总数据
        - BR-SUBMIT-004: Phase 1 无强制必填项

        错误处理:
        - RES-001: 周报不存在
        - BIZ_003: 周报已提交，不可重复提交
        - PERM-001: 权限不足
        """
        logger.info(
            f"提交周报: user={current_user.email}, report_id={report_id}"
        )

        # 获取周报 (含权限检查)
        brief = self.get_weekly_report(report_id, current_user)

        # BR-SUBMIT-001: 验证状态 - 只能提交 draft 状态
        if brief.status != WeeklyBriefStatus.DRAFT.value:
            raise BusinessLogicError("周报已提交，不可重复提交")

        # BR-SUBMIT-002: 验证权限 - project_owner 只能提交自己项目
        if current_user.role in [UserRole.PROJECT_OWNER.value, "project_owner"]:
            if not self._is_project_owner(current_user.id, brief.project_id):
                raise PermissionDeniedError("权限不足：只能提交自己负责的项目周报")

        # BR-SUBMIT-003: 刷新汇总数据
        summary = self._aggregate_weekly_data(brief.project_id, brief.week_start, brief.week_end)
        brief.weekly_spend = summary['spend']
        brief.weekly_conversions = summary['conversions']
        brief.weekly_cpl = summary['cpl']

        # 执行状态转换
        brief.status = WeeklyBriefStatus.SUBMITTED.value
        brief.submitter_id = current_user.id
        brief.submitted_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(brief)

        logger.info(f"周报提交成功: id={brief.id}, status={brief.status}")
        return brief

    def to_response(self, brief: WeeklyBrief) -> WeeklyReportResponse:
        """
        将 WeeklyBrief 模型转换为 WeeklyReportResponse

        字段映射:
        - week_start → week_start_date
        - week_end → week_end_date
        - submitter_id → created_by
        """
        return WeeklyReportResponse(
            id=brief.id,
            project_id=brief.project_id,
            project_name=brief.project.name if brief.project else None,
            week_start_date=brief.week_start,
            week_end_date=brief.week_end,
            status=brief.status,
            created_by=brief.submitter_id,
            created_by_name=brief.submitter.full_name if brief.submitter else None,
            weekly_spend=brief.weekly_spend,
            weekly_conversions=brief.weekly_conversions,
            weekly_cpl=brief.weekly_cpl,
            issues=brief.issues,
            next_week_plan=brief.next_week_plan,
            achievements=brief.achievements,
            solutions=brief.solutions,
            created_at=brief.created_at,
            updated_at=brief.updated_at,
            submitted_at=brief.submitted_at,
        )

    # ========== 私有方法 ==========

    def _is_project_owner(self, user_id: UUID, project_id: int) -> bool:
        """检查用户是否是项目负责人"""
        try:
            member = self.db.query(ProjectMember).filter(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == user_id,
                ProjectMember.role == 'owner'
            ).first()
            return member is not None
        except Exception:
            # ProjectMember 表可能不存在，回退检查 Project.owner_id
            project = self.db.query(Project).filter(Project.id == project_id).first()
            if project and hasattr(project, 'owner_id'):
                return project.owner_id == user_id
            return False

    def _aggregate_weekly_data(
        self,
        project_id: int,
        week_start: date,
        week_end: date
    ) -> dict:
        """
        汇总项目周数据

        SoT: B3-weekly-brief.md §2.4
        - 周消耗: SUM(ad_spend_daily.spend) WHERE date BETWEEN week_start AND week_end
        - 周进粉: SUM(daily_reports.conversions_final) WHERE date BETWEEN week_start AND week_end
        - 周 CPL: 周消耗 / 周进粉
        """
        # 获取项目下的账户
        account_ids = self.db.query(AdAccount.id).filter(
            AdAccount.project_id == project_id
        ).subquery()

        # 汇总消耗
        spend_result = self.db.query(
            func.coalesce(func.sum(AdSpendDaily.spend), 0)
        ).filter(
            AdSpendDaily.ad_account_id.in_(account_ids),
            AdSpendDaily.spend_date >= week_start,
            AdSpendDaily.spend_date <= week_end
        ).scalar()
        spend = Decimal(str(spend_result or 0))

        # 汇总进粉
        conversions_result = self.db.query(
            func.coalesce(func.sum(DailyReport.conversions_final), 0)
        ).filter(
            DailyReport.ad_account_id.in_(account_ids),
            DailyReport.report_date >= week_start,
            DailyReport.report_date <= week_end
        ).scalar()
        conversions = int(conversions_result or 0)

        # 计算 CPL
        cpl = Decimal('0')
        if conversions > 0:
            cpl = spend / Decimal(conversions)

        return {
            'spend': spend,
            'conversions': conversions,
            'cpl': cpl.quantize(Decimal('0.01'))
        }
