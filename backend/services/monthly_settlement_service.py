"""
月度结算服务层 - TASK-FIN-003 月度锁账

SoT Reference:
- STATE_MACHINE.md v2.9 §13.1 (月度结算状态机)
- DATA_SCHEMA.md v5.7 §3.7.1 (monthly_settlements 表)
- BUSINESS_RULES.md v5.0 (BR-FIN-007: 锁定后不可改)
- MASTER.md v4.8 §2.4 (CEO: 月度锁账确认)

状态机 (4状态):
pending → confirmed → locked → archived
    ↑          ↓
    └──────────┘ (退回修正)

角色权限:
- pending → confirmed: finance, admin
- confirmed → locked: ceo, admin
- confirmed → pending: finance, admin (退回)
- locked → archived: admin

计算公式:
- total_spend: SUM(daily_reports.real_spend) WHERE status='final_locked'
- total_conversions: SUM(daily_reports.conversions_final) WHERE status='final_locked'
- total_revenue: total_conversions × projects.unit_price
- gross_profit: total_revenue - total_spend
- average_cpl: total_spend / total_conversions

Version: 1.0
Author: Claude Code (TASK-FIN-003)
"""

from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional, Tuple, Dict, Any
from uuid import UUID

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, func, extract

from backend.models import User, Project, DailyReport
from backend.models.finance.monthly_settlement import MonthlySettlement
from backend.models.base import DailyReportStatus, ProjectStatus
from backend.core.state_machine import (
    SETTLEMENT_STATE_MACHINE,
    SettlementStatus,
    StateTransitionError,
)
from backend.schemas.monthly_settlement import (
    MonthlySettlementGenerateRequest,
    MonthlySettlementBatchGenerateRequest,
    MonthlySettlementConfirmRequest,
    MonthlySettlementLockRequest,
    MonthlySettlementRejectRequest,
    MonthlySettlementUpdateRequest,
    MonthlySettlementResponse,
    MonthlySettlementStatistics,
)
from backend.exceptions.custom_exceptions import (
    ResourceNotFoundError,
    PermissionDeniedError,
    BusinessLogicError,
    ResourceConflictError,
)


class MonthlySettlementService:
    """
    月度结算服务类

    职责:
    1. 生成月度结算记录 (从日报聚合)
    2. 财务确认 (pending → confirmed)
    3. CEO 锁定 (confirmed → locked)
    4. 退回修正 (confirmed → pending)
    5. 年度归档 (locked → archived)
    """

    # 状态流转定义 (STATE_MACHINE.md v2.9 §13.1)
    STATE_TRANSITIONS = {
        "pending": ["confirmed"],
        "confirmed": ["locked", "pending"],  # pending 为退回
        "locked": ["archived"],
        "archived": [],  # 终态
    }

    def __init__(self, db: Session):
        self.db = db

    def _validate_transition(self, from_status: str, to_status: str) -> bool:
        """验证状态流转是否合法"""
        allowed = self.STATE_TRANSITIONS.get(from_status, [])
        return to_status in allowed

    # ========== 查询方法 ==========

    def get_by_id(self, settlement_id: int) -> Optional[MonthlySettlement]:
        """根据 ID 获取月度结算"""
        return (
            self.db.query(MonthlySettlement)
            .options(
                joinedload(MonthlySettlement.project),
                joinedload(MonthlySettlement.confirmed_by_user),
                joinedload(MonthlySettlement.locked_by_user),
            )
            .filter(MonthlySettlement.id == settlement_id)
            .first()
        )

    def get_by_project_month(
        self, project_id: int, settlement_month: date
    ) -> Optional[MonthlySettlement]:
        """根据项目和月份获取月度结算"""
        month_start = settlement_month.replace(day=1)
        return (
            self.db.query(MonthlySettlement)
            .filter(
                MonthlySettlement.project_id == project_id,
                MonthlySettlement.settlement_month == month_start,
            )
            .first()
        )

    def list_settlements(
        self,
        project_id: Optional[int] = None,
        status: Optional[str] = None,
        start_month: Optional[date] = None,
        end_month: Optional[date] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[MonthlySettlement], int]:
        """
        查询月度结算列表

        Args:
            project_id: 项目ID (可选)
            status: 状态过滤 (可选)
            start_month: 开始月份 (可选)
            end_month: 结束月份 (可选)
            page: 页码
            page_size: 每页数量

        Returns:
            (settlements, total_count)
        """
        query = self.db.query(MonthlySettlement).options(
            joinedload(MonthlySettlement.project),
            joinedload(MonthlySettlement.confirmed_by_user),
            joinedload(MonthlySettlement.locked_by_user),
        )

        # 过滤条件
        if project_id:
            query = query.filter(MonthlySettlement.project_id == project_id)
        if status:
            query = query.filter(MonthlySettlement.status == status)
        if start_month:
            query = query.filter(
                MonthlySettlement.settlement_month >= start_month.replace(day=1)
            )
        if end_month:
            query = query.filter(
                MonthlySettlement.settlement_month <= end_month.replace(day=1)
            )

        # 总数
        total = query.count()

        # 分页
        settlements = (
            query.order_by(
                MonthlySettlement.settlement_month.desc(),
                MonthlySettlement.project_id,
            )
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        return settlements, total

    def get_statistics(
        self,
        settlement_month: Optional[date] = None,
        project_id: Optional[int] = None,
    ) -> MonthlySettlementStatistics:
        """获取月度结算统计"""
        query = self.db.query(MonthlySettlement)

        if settlement_month:
            query = query.filter(
                MonthlySettlement.settlement_month == settlement_month.replace(day=1)
            )
        if project_id:
            query = query.filter(MonthlySettlement.project_id == project_id)

        settlements = query.all()

        # 统计
        stats = {
            "total_settlements": len(settlements),
            "pending_count": sum(
                1 for s in settlements if s.status == SettlementStatus.PENDING.value
            ),
            "confirmed_count": sum(
                1 for s in settlements if s.status == SettlementStatus.CONFIRMED.value
            ),
            "locked_count": sum(
                1 for s in settlements if s.status == SettlementStatus.LOCKED.value
            ),
            "total_spend": sum((s.total_spend or Decimal("0")) for s in settlements),
            "total_revenue": sum(
                (s.total_revenue or Decimal("0")) for s in settlements
            ),
            "total_profit": sum((s.gross_profit or Decimal("0")) for s in settlements),
            "by_status": [],
        }

        # 按状态统计
        status_counts = {}
        for s in settlements:
            status_counts[s.status] = status_counts.get(s.status, 0) + 1
        stats["by_status"] = [
            {"status": k, "count": v} for k, v in status_counts.items()
        ]

        return MonthlySettlementStatistics(**stats)

    # ========== 生成方法 ==========

    def generate_settlement(
        self,
        request: MonthlySettlementGenerateRequest,
        current_user: User,
    ) -> MonthlySettlement:
        """
        生成单个项目的月度结算

        从 final_locked 状态的日报聚合数据

        Args:
            request: 生成请求
            current_user: 当前用户

        Returns:
            MonthlySettlement 实例

        Raises:
            ResourceNotFoundError: 项目不存在
            ResourceConflictError: 该月结算已存在
        """
        # 1. 验证项目
        project = (
            self.db.query(Project).filter(Project.id == request.project_id).first()
        )
        if not project:
            raise ResourceNotFoundError(f"项目 {request.project_id} 不存在")

        # 2. 检查是否已存在
        month_start = request.settlement_month.replace(day=1)
        existing = self.get_by_project_month(request.project_id, month_start)
        if existing:
            raise ResourceConflictError(
                f"项目 {request.project_id} 的 {month_start.strftime('%Y-%m')} 月结算已存在"
            )

        # 3. 聚合日报数据
        spend_data = self._aggregate_daily_reports(request.project_id, month_start)

        # 4. 创建结算记录
        settlement = MonthlySettlement(
            project_id=request.project_id,
            settlement_month=month_start,
            total_spend=spend_data["total_spend"],
            total_conversions=spend_data["total_conversions"],
            status=SettlementStatus.PENDING.value,
            notes=request.notes,
        )

        # 5. 计算收入、毛利、CPL
        unit_price = project.unit_price or Decimal("0")
        settlement.calculate_metrics(unit_price)

        self.db.add(settlement)
        self.db.commit()
        self.db.refresh(settlement)

        return settlement

    def batch_generate_settlements(
        self,
        request: MonthlySettlementBatchGenerateRequest,
        current_user: User,
    ) -> List[MonthlySettlement]:
        """
        批量生成月度结算

        Args:
            request: 批量生成请求
            current_user: 当前用户

        Returns:
            生成的 MonthlySettlement 列表
        """
        month_start = request.settlement_month.replace(day=1)

        # 获取项目列表
        if request.project_ids:
            projects = (
                self.db.query(Project).filter(Project.id.in_(request.project_ids)).all()
            )
        else:
            # 获取所有活跃项目
            projects = (
                self.db.query(Project)
                .filter(Project.status == ProjectStatus.ACTIVE.value)
                .all()
            )

        settlements = []
        for project in projects:
            # 检查是否已存在
            existing = self.get_by_project_month(project.id, month_start)
            if existing:
                continue

            # 聚合数据
            spend_data = self._aggregate_daily_reports(project.id, month_start)

            # 创建结算
            settlement = MonthlySettlement(
                project_id=project.id,
                settlement_month=month_start,
                total_spend=spend_data["total_spend"],
                total_conversions=spend_data["total_conversions"],
                status=SettlementStatus.PENDING.value,
            )

            unit_price = project.unit_price or Decimal("0")
            settlement.calculate_metrics(unit_price)

            self.db.add(settlement)
            settlements.append(settlement)

        self.db.commit()
        for s in settlements:
            self.db.refresh(s)

        return settlements

    def _aggregate_daily_reports(
        self, project_id: int, settlement_month: date
    ) -> Dict[str, Any]:
        """
        从日报聚合月度数据

        SoT: DATA_SCHEMA.md v5.7 §3.7.1
        - total_spend: SUM(real_spend) WHERE status='final_locked'
        - total_conversions: SUM(conversions_final) WHERE status='final_locked'
        """
        # 计算月份范围
        year = settlement_month.year
        month = settlement_month.month
        if month == 12:
            next_month = date(year + 1, 1, 1)
        else:
            next_month = date(year, month + 1, 1)

        # 聚合查询
        result = (
            self.db.query(
                func.coalesce(func.sum(DailyReport.real_spend), Decimal("0")).label(
                    "total_spend"
                ),
                func.coalesce(func.sum(DailyReport.conversions_final), 0).label(
                    "total_conversions"
                ),
            )
            .filter(
                DailyReport.project_id == project_id,
                DailyReport.report_date >= settlement_month,
                DailyReport.report_date < next_month,
                DailyReport.status == DailyReportStatus.FINAL_LOCKED.value,
            )
            .first()
        )

        return {
            "total_spend": result.total_spend if result else Decimal("0"),
            "total_conversions": result.total_conversions if result else 0,
        }

    # ========== 状态流转方法 ==========

    def confirm_settlement(
        self,
        settlement_id: int,
        request: MonthlySettlementConfirmRequest,
        current_user: User,
    ) -> MonthlySettlement:
        """
        财务确认月度结算 (pending → confirmed)

        权限: finance, admin

        Args:
            settlement_id: 结算ID
            request: 确认请求
            current_user: 当前用户

        Raises:
            ResourceNotFoundError: 结算不存在
            PermissionDeniedError: 无权限
            BusinessLogicError: 状态不允许确认
        """
        settlement = self.get_by_id(settlement_id)
        if not settlement:
            raise ResourceNotFoundError(f"月度结算 {settlement_id} 不存在")

        # 权限检查: finance, admin
        if current_user.role not in ["finance", "admin", "ceo"]:
            raise PermissionDeniedError("仅财务或管理员可确认月度结算")

        # 状态检查
        if settlement.status != SettlementStatus.PENDING.value:
            raise BusinessLogicError(f"当前状态 {settlement.status} 不允许确认，需为 pending 状态")

        # 状态转换
        try:
            SETTLEMENT_STATE_MACHINE.transition(
                settlement,
                settlement.status,
                SettlementStatus.CONFIRMED.value,
                user_role=current_user.role,
            )
        except StateTransitionError as e:
            raise BusinessLogicError(str(e))

        settlement.confirmed_at = date.today()
        settlement.confirmed_by = current_user.id
        if request.notes:
            settlement.notes = (settlement.notes or "") + f"\n[确认] {request.notes}"

        self.db.commit()
        self.db.refresh(settlement)

        return settlement

    def lock_settlement(
        self,
        settlement_id: int,
        request: MonthlySettlementLockRequest,
        current_user: User,
    ) -> MonthlySettlement:
        """
        CEO 锁定月度结算 (confirmed → locked)

        权限: ceo, admin

        Args:
            settlement_id: 结算ID
            request: 锁定请求
            current_user: 当前用户

        Raises:
            ResourceNotFoundError: 结算不存在
            PermissionDeniedError: 无权限 (需 CEO/admin)
            BusinessLogicError: 状态不允许锁定
        """
        settlement = self.get_by_id(settlement_id)
        if not settlement:
            raise ResourceNotFoundError(f"月度结算 {settlement_id} 不存在")

        # 权限检查: ceo, admin
        if current_user.role not in ["ceo", "admin"]:
            raise PermissionDeniedError("仅老板或管理员可锁定月度结算")

        # 状态检查
        if settlement.status != SettlementStatus.CONFIRMED.value:
            raise BusinessLogicError(f"当前状态 {settlement.status} 不允许锁定，需为 confirmed 状态")

        # 状态转换
        try:
            SETTLEMENT_STATE_MACHINE.transition(
                settlement,
                settlement.status,
                SettlementStatus.LOCKED.value,
                user_role=current_user.role,
            )
        except StateTransitionError as e:
            raise BusinessLogicError(str(e))

        settlement.locked_at = date.today()
        settlement.locked_by = current_user.id
        if request.notes:
            settlement.notes = (settlement.notes or "") + f"\n[锁定] {request.notes}"

        self.db.commit()
        self.db.refresh(settlement)

        return settlement

    def reject_settlement(
        self,
        settlement_id: int,
        request: MonthlySettlementRejectRequest,
        current_user: User,
    ) -> MonthlySettlement:
        """
        退回月度结算 (confirmed → pending)

        权限: finance, admin

        Args:
            settlement_id: 结算ID
            request: 退回请求
            current_user: 当前用户
        """
        settlement = self.get_by_id(settlement_id)
        if not settlement:
            raise ResourceNotFoundError(f"月度结算 {settlement_id} 不存在")

        # 权限检查
        if current_user.role not in ["finance", "admin", "ceo"]:
            raise PermissionDeniedError("仅财务或管理员可退回月度结算")

        # 状态检查
        if settlement.status != SettlementStatus.CONFIRMED.value:
            raise BusinessLogicError(f"当前状态 {settlement.status} 不允许退回，需为 confirmed 状态")

        # 状态转换
        try:
            SETTLEMENT_STATE_MACHINE.transition(
                settlement,
                settlement.status,
                SettlementStatus.PENDING.value,
                user_role=current_user.role,
            )
        except StateTransitionError as e:
            raise BusinessLogicError(str(e))

        settlement.notes = (settlement.notes or "") + f"\n[退回] {request.reason}"

        self.db.commit()
        self.db.refresh(settlement)

        return settlement

    def archive_settlement(
        self,
        settlement_id: int,
        current_user: User,
    ) -> MonthlySettlement:
        """
        归档月度结算 (locked → archived)

        权限: admin

        Args:
            settlement_id: 结算ID
            current_user: 当前用户
        """
        settlement = self.get_by_id(settlement_id)
        if not settlement:
            raise ResourceNotFoundError(f"月度结算 {settlement_id} 不存在")

        # 权限检查
        if current_user.role != "admin":
            raise PermissionDeniedError("仅管理员可归档月度结算")

        # 状态检查
        if settlement.status != SettlementStatus.LOCKED.value:
            raise BusinessLogicError(f"当前状态 {settlement.status} 不允许归档，需为 locked 状态")

        # 状态转换
        try:
            SETTLEMENT_STATE_MACHINE.transition(
                settlement,
                settlement.status,
                SettlementStatus.ARCHIVED.value,
                user_role=current_user.role,
            )
        except StateTransitionError as e:
            raise BusinessLogicError(str(e))

        self.db.commit()
        self.db.refresh(settlement)

        return settlement

    # ========== 更新方法 ==========

    def update_settlement(
        self,
        settlement_id: int,
        request: MonthlySettlementUpdateRequest,
        current_user: User,
    ) -> MonthlySettlement:
        """
        更新月度结算 (仅 pending 状态可更新)

        Args:
            settlement_id: 结算ID
            request: 更新请求
            current_user: 当前用户
        """
        settlement = self.get_by_id(settlement_id)
        if not settlement:
            raise ResourceNotFoundError(f"月度结算 {settlement_id} 不存在")

        # 状态检查
        if settlement.status != SettlementStatus.PENDING.value:
            raise BusinessLogicError(f"当前状态 {settlement.status} 不允许更新，需为 pending 状态")

        # 更新字段
        if request.total_spend is not None:
            settlement.total_spend = request.total_spend
        if request.total_conversions is not None:
            settlement.total_conversions = request.total_conversions
        if request.notes is not None:
            settlement.notes = request.notes

        # 重新计算收入、毛利、CPL
        project = (
            self.db.query(Project).filter(Project.id == settlement.project_id).first()
        )
        unit_price = project.unit_price if project else Decimal("0")
        settlement.calculate_metrics(unit_price)

        self.db.commit()
        self.db.refresh(settlement)

        return settlement

    def recalculate_settlement(
        self,
        settlement_id: int,
        current_user: User,
    ) -> MonthlySettlement:
        """
        重新计算月度结算 (从日报重新聚合)

        仅 pending 状态可重新计算
        """
        settlement = self.get_by_id(settlement_id)
        if not settlement:
            raise ResourceNotFoundError(f"月度结算 {settlement_id} 不存在")

        if settlement.status != SettlementStatus.PENDING.value:
            raise BusinessLogicError(f"当前状态 {settlement.status} 不允许重新计算，需为 pending 状态")

        # 重新聚合
        spend_data = self._aggregate_daily_reports(
            settlement.project_id, settlement.settlement_month
        )

        settlement.total_spend = spend_data["total_spend"]
        settlement.total_conversions = spend_data["total_conversions"]

        # 重新计算
        project = (
            self.db.query(Project).filter(Project.id == settlement.project_id).first()
        )
        unit_price = project.unit_price if project else Decimal("0")
        settlement.calculate_metrics(unit_price)

        self.db.commit()
        self.db.refresh(settlement)

        return settlement
