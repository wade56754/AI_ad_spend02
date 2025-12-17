"""
利润聚合与报表服务 (对齐 PROFIT_SOT.md v1.1)

服务职责:
- 利润聚合计算: 基于 ledger_entries 和 daily_reports 聚合收入/成本/毛利
- 多维度报表: 项目级 / 账户级 / 整体级利润表
- 周期聚合: 支持日度 / 月度聚合
- 报表快照: 支持生成不可变的报表快照

业务规则引用:
- BR-PROFIT-001: 聚合数据来源限定 (仅 final_locked 日报, 仅 REVENUE/COST 分录)
- BR-PROFIT-002: 毛利计算公式 gross_profit = total_revenue - total_cost
- BR-PROFIT-003: 聚合数据只读原则 (仅通过 generate API 写入)
- BR-PROFIT-004: 锁定后禁止刷新 (除非 force_refresh=True 且 admin)
- BR-PROFIT-005: 周期参数校验
- BR-PROFIT-006: 收入来源限定 (仅 REVENUE, 禁止 TOPUP)
- BR-PROFIT-007: 成本来源限定 (仅 COST, 禁止 TRANSFER)
- BR-PROFIT-008: 毛利率边界处理 (revenue=0 时 margin=0)

数据来源:
- total_revenue: SUM(ledger_entries.amount WHERE entry_type='REVENUE')
- total_cost: ABS(SUM(ledger_entries.amount WHERE entry_type='COST'))
- total_conversions: SUM(daily_reports.conversions_final WHERE status='final_locked')
- total_real_spend: SUM(daily_reports.real_spend WHERE status='final_locked')
- total_topup: SUM(ledger_entries.amount WHERE entry_type='TOPUP') - 仅统计,不参与利润
"""

import logging
from contextlib import contextmanager
from datetime import date, datetime, timezone, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional, Any, Tuple
from uuid import UUID

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from backend.exceptions.custom_exceptions import (
    BusinessLogicError,
    ResourceNotFoundError,
    ResourceConflictError,
)
from backend.models.finance.profit import (
    ProfitAggregate,
    ProfitReportSnapshot,
    ProfitPeriodType,
    ProfitReportType,
    ProfitReportStatus,
)
from backend.models.finance.ledger import LedgerEntry
from backend.models.workflow.daily_report import DailyReport
from backend.models.core.project import Project
from backend.models.accounts.ad_account import AdAccount


logger = logging.getLogger(__name__)


class ProfitService:
    """
    利润聚合服务类

    职责:
    - 生成/刷新利润聚合数据 (generate_period_aggregates)
    - 查询利润聚合数据 (get_period_aggregates)
    - 创建/更新报表快照 (create_or_update_snapshot)
    - 查询报表快照列表 (list_snapshots)
    - 锁定报表快照 (lock_snapshot)

    引用: PROFIT_SOT.md v1.1, LEDGER_SOT.md v1.1, STATE_MACHINE.md v2.6
    """

    # 日期范围最大限制 (BR-PROFIT-005 延伸)
    MAX_DATE_RANGE_DAYS = 366

    # 毛利率小数位数和舍入规则 (BR-PROFIT-008)
    MARGIN_DECIMAL_PLACES = 4
    AMOUNT_DECIMAL_PLACES = 2

    def __init__(self, db: Session):
        """
        初始化服务

        Args:
            db: SQLAlchemy Session 实例
        """
        self.db = db

    @contextmanager
    def transaction(self):
        """事务上下文管理器"""
        try:
            yield
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            logger.error(f"Transaction failed: {e}")
            raise

    # =========================================================================
    # 核心方法: 生成利润聚合
    # =========================================================================

    def generate_period_aggregates(
        self,
        period_type: str,
        period_start: date,
        period_end: date,
        project_id: Optional[int] = None,
        *,
        overwrite: bool = False,
        force_refresh: bool = False,
        user_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """
        生成/刷新指定周期的利润聚合数据

        业务规则:
        - BR-PROFIT-001: 仅聚合 final_locked 日报和 REVENUE/COST 分录
        - BR-PROFIT-004: 锁定后禁止刷新 (除非 force_refresh=True)
        - BR-PROFIT-005: 周期参数校验

        Args:
            period_type: 周期类型 ('daily', 'weekly', 'monthly')
            period_start: 周期开始日期
            period_end: 周期结束日期
            project_id: 指定项目ID (可选, None 表示全量聚合)
            overwrite: 是否覆盖已存在的聚合记录
            force_refresh: 是否强制刷新已锁定的数据 (需 admin 权限)
            user_id: 操作用户ID

        Returns:
            dict: 聚合结果摘要
            {
                "generated_count": int,
                "period": {"type": str, "start": date, "end": date},
                "summary": {...}
            }

        Raises:
            BusinessLogicError: PROFIT_001 周期参数无效
            BusinessLogicError: PROFIT_002 开始日期不能是未来
            ResourceNotFoundError: PROFIT_003 项目不存在
            ResourceConflictError: PROFIT_004 周期已锁定
        """
        logger.info(
            f"generate_period_aggregates: type={period_type}, "
            f"start={period_start}, end={period_end}, project_id={project_id}, "
            f"overwrite={overwrite}, force_refresh={force_refresh}"
        )

        # 1. 参数校验 (BR-PROFIT-005)
        self._validate_period_params(period_type, period_start, period_end)

        # 2. 验证项目存在性 (PROFIT_003)
        if project_id is not None:
            project = self.db.query(Project).filter(Project.id == project_id).first()
            if not project:
                raise ResourceNotFoundError(
                    message=f"项目不存在: project_id={project_id}",
                    error_code="PROFIT_003",
                    details={"project_id": project_id}
                )

        # 3. 检查是否已锁定 (BR-PROFIT-004)
        existing_locked = self._get_existing_locked_aggregates(
            period_type, period_start, period_end, project_id
        )
        if existing_locked and not force_refresh:
            raise ResourceConflictError(
                message="周期已锁定，无法刷新",
                error_code="PROFIT_004",
                details={
                    "period_type": period_type,
                    "period_start": str(period_start),
                    "period_end": str(period_end),
                    "locked_at": str(existing_locked[0].locked_at) if existing_locked else None
                }
            )

        # 4. 执行聚合计算
        with self.transaction():
            # 4.1 清理旧数据 (如果 overwrite=True 或 force_refresh=True)
            if overwrite or force_refresh:
                self._delete_existing_aggregates(
                    period_type, period_start, period_end, project_id
                )

            # 4.2 获取需要聚合的项目列表
            target_projects = self._get_target_projects(project_id)

            # 4.3 执行聚合
            generated_count = 0
            summary_totals = {
                "total_revenue": Decimal("0"),
                "total_cost": Decimal("0"),
                "gross_profit": Decimal("0"),
                "total_conversions": 0,
            }

            for proj in target_projects:
                # 项目级聚合
                project_agg = self._aggregate_for_project(
                    period_type, period_start, period_end, proj.id
                )
                if project_agg:
                    self.db.add(project_agg)
                    generated_count += 1
                    summary_totals["total_revenue"] += project_agg.total_revenue
                    summary_totals["total_cost"] += project_agg.total_cost
                    summary_totals["gross_profit"] += project_agg.gross_profit
                    summary_totals["total_conversions"] += project_agg.total_conversions

                    # 账户级聚合 (如果是日度聚合)
                    if period_type == ProfitPeriodType.DAILY.value:
                        account_aggs = self._aggregate_for_accounts(
                            period_type, period_start, period_end, proj.id
                        )
                        for acc_agg in account_aggs:
                            self.db.add(acc_agg)
                            generated_count += 1

            # 4.4 全局聚合 (project_id=None)
            if project_id is None:
                global_agg = self._aggregate_global(
                    period_type, period_start, period_end
                )
                if global_agg:
                    self.db.add(global_agg)
                    generated_count += 1

            self.db.flush()

        logger.info(
            f"generate_period_aggregates completed: generated_count={generated_count}"
        )

        return {
            "generated_count": generated_count,
            "period": {
                "type": period_type,
                "start": str(period_start),
                "end": str(period_end),
            },
            "summary": {
                "total_projects": len(target_projects),
                "total_revenue": str(summary_totals["total_revenue"]),
                "total_cost": str(summary_totals["total_cost"]),
                "gross_profit": str(summary_totals["gross_profit"]),
            },
        }

    # =========================================================================
    # 核心方法: 查询利润聚合
    # =========================================================================

    def get_period_aggregates(
        self,
        period_type: str,
        period_start: date,
        period_end: date,
        project_id: Optional[int] = None,
        ad_account_id: Optional[int] = None,
        *,
        include_accounts: bool = False,
    ) -> Dict[str, Any]:
        """
        查询指定周期的利润聚合数据

        Args:
            period_type: 周期类型
            period_start: 周期开始日期
            period_end: 周期结束日期
            project_id: 项目ID筛选
            ad_account_id: 账户ID筛选
            include_accounts: 是否包含账户明细

        Returns:
            dict: 聚合数据
            {
                "period": {...},
                "summary": {...},
                "by_project": [...],
                "is_locked": bool
            }

        Raises:
            BusinessLogicError: PROFIT_001 周期参数无效
            ResourceNotFoundError: PROFIT_005 指定周期无数据
        """
        logger.info(
            f"get_period_aggregates: type={period_type}, "
            f"start={period_start}, end={period_end}"
        )

        # 参数校验
        self._validate_period_params(period_type, period_start, period_end)

        # 构建查询
        query = self.db.query(ProfitAggregate).filter(
            and_(
                ProfitAggregate.period_type == period_type,
                ProfitAggregate.period_start >= datetime.combine(period_start, datetime.min.time()),
                ProfitAggregate.period_end <= datetime.combine(period_end, datetime.max.time()),
            )
        )

        if project_id is not None:
            query = query.filter(ProfitAggregate.project_id == project_id)
        if ad_account_id is not None:
            query = query.filter(ProfitAggregate.ad_account_id == ad_account_id)

        aggregates = query.all()

        if not aggregates:
            raise ResourceNotFoundError(
                message="指定周期无数据",
                error_code="PROFIT_005",
                details={
                    "period_type": period_type,
                    "period_start": str(period_start),
                    "period_end": str(period_end),
                }
            )

        # 汇总计算
        summary = self._calculate_summary(aggregates)

        # 按项目分组
        by_project = self._group_by_project(aggregates, include_accounts)

        # 检查是否锁定
        is_locked = any(agg.is_locked for agg in aggregates)

        return {
            "period": {
                "type": period_type,
                "start": str(period_start),
                "end": str(period_end),
            },
            "summary": summary,
            "by_project": by_project,
            "is_locked": is_locked,
        }

    # =========================================================================
    # 核心方法: 报表快照管理
    # =========================================================================

    def create_or_update_snapshot(
        self,
        report_type: str,
        period_month: date,
        generated_by: UUID,
        project_id: Optional[int] = None,
        *,
        lock: bool = False,
    ) -> ProfitReportSnapshot:
        """
        创建或更新报表快照

        Args:
            report_type: 报表类型 ('monthly_summary', 'project_detail', 'account_detail')
            period_month: 报表月份 (月初日期)
            generated_by: 生成人ID
            project_id: 项目ID (可选)
            lock: 是否直接锁定

        Returns:
            ProfitReportSnapshot: 创建/更新的快照对象
        """
        logger.info(
            f"create_or_update_snapshot: type={report_type}, "
            f"month={period_month}, project_id={project_id}"
        )

        # 查询对应周期的聚合数据
        period_start = period_month.replace(day=1)
        # 计算月末
        if period_month.month == 12:
            period_end = period_month.replace(year=period_month.year + 1, month=1, day=1)
        else:
            period_end = period_month.replace(month=period_month.month + 1, day=1)
        period_end = period_end.replace(day=1) - timedelta(days=1)  # TODO: 需要 import timedelta

        aggregates = self.db.query(ProfitAggregate).filter(
            and_(
                ProfitAggregate.period_type == ProfitPeriodType.MONTHLY.value,
                ProfitAggregate.period_start >= datetime.combine(period_start, datetime.min.time()),
                ProfitAggregate.period_end <= datetime.combine(period_end, datetime.max.time()),
            )
        )

        if project_id is not None:
            aggregates = aggregates.filter(ProfitAggregate.project_id == project_id)

        aggregates = aggregates.all()

        # 构建报表数据
        report_data = self._build_report_data(aggregates, period_month)

        with self.transaction():
            # 查找现有快照
            existing = self.db.query(ProfitReportSnapshot).filter(
                and_(
                    ProfitReportSnapshot.report_type == report_type,
                    ProfitReportSnapshot.period_month == period_month.strftime("%Y-%m"),
                    ProfitReportSnapshot.project_id == project_id,
                )
            ).first()

            if existing:
                # 更新
                existing.report_data = report_data
                existing.generated_at = datetime.now(timezone.utc)
                existing.generated_by = generated_by
                if lock:
                    existing.status = ProfitReportStatus.LOCKED.value
                snapshot = existing
            else:
                # 创建
                snapshot = ProfitReportSnapshot(
                    report_type=report_type,
                    period_month=period_month.strftime("%Y-%m"),
                    project_id=project_id,
                    report_data=report_data,
                    generated_by=generated_by,
                    status=ProfitReportStatus.LOCKED.value if lock else ProfitReportStatus.DRAFT.value,
                )
                self.db.add(snapshot)

            self.db.flush()

        logger.info(f"Snapshot created/updated: id={snapshot.id}")
        return snapshot

    def list_snapshots(
        self,
        project_id: Optional[int] = None,
        report_type: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[ProfitReportSnapshot]:
        """
        查询报表快照列表

        Args:
            project_id: 项目ID筛选
            report_type: 报表类型筛选
            status: 状态筛选

        Returns:
            list: 快照列表
        """
        query = self.db.query(ProfitReportSnapshot)

        if project_id is not None:
            query = query.filter(ProfitReportSnapshot.project_id == project_id)
        if report_type is not None:
            query = query.filter(ProfitReportSnapshot.report_type == report_type)
        if status is not None:
            query = query.filter(ProfitReportSnapshot.status == status)

        return query.order_by(ProfitReportSnapshot.generated_at.desc()).all()

    def lock_snapshot(
        self,
        snapshot_id: int,
        confirmed_by: UUID,
    ) -> ProfitReportSnapshot:
        """
        锁定报表快照

        Args:
            snapshot_id: 快照ID
            confirmed_by: 确认人ID

        Returns:
            ProfitReportSnapshot: 锁定后的快照

        Raises:
            ResourceNotFoundError: 快照不存在
        """
        logger.info(f"lock_snapshot: id={snapshot_id}")

        snapshot = self.db.query(ProfitReportSnapshot).filter(
            ProfitReportSnapshot.id == snapshot_id
        ).first()

        if not snapshot:
            raise ResourceNotFoundError(
                message=f"快照不存在: id={snapshot_id}",
                error_code="PROFIT_005",
                details={"snapshot_id": snapshot_id}
            )

        with self.transaction():
            snapshot.status = ProfitReportStatus.LOCKED.value
            snapshot.confirmed_at = datetime.now(timezone.utc)
            snapshot.confirmed_by = confirmed_by
            self.db.flush()

        logger.info(f"Snapshot locked: id={snapshot_id}")
        return snapshot

    # =========================================================================
    # 辅助方法: 参数校验
    # =========================================================================

    def _validate_period_params(
        self,
        period_type: str,
        period_start: date,
        period_end: date,
    ) -> None:
        """
        校验周期参数 (BR-PROFIT-005)

        Raises:
            BusinessLogicError: PROFIT_001 周期参数无效
            BusinessLogicError: PROFIT_002 开始日期不能是未来
            BusinessLogicError: PROFIT_008 日期范围超出限制
        """
        # 校验 period_type
        valid_types = [pt.value for pt in ProfitPeriodType]
        if period_type not in valid_types:
            raise BusinessLogicError(
                message=f"周期类型无效: {period_type}, 有效值: {valid_types}",
                error_code="PROFIT_001",
                details={"period_type": period_type, "valid_types": valid_types}
            )

        # 校验 period_start <= period_end
        if period_start > period_end:
            raise BusinessLogicError(
                message="开始日期必须 <= 结束日期",
                error_code="PROFIT_001",
                details={"period_start": str(period_start), "period_end": str(period_end)}
            )

        # 校验 period_start 不是未来日期
        today = date.today()
        if period_start > today:
            raise BusinessLogicError(
                message="开始日期不能是未来日期",
                error_code="PROFIT_002",
                details={"period_start": str(period_start), "today": str(today)}
            )

        # 校验日期范围不超过限制
        date_range = (period_end - period_start).days
        if date_range > self.MAX_DATE_RANGE_DAYS:
            raise BusinessLogicError(
                message=f"日期范围超出限制: {date_range} > {self.MAX_DATE_RANGE_DAYS}",
                error_code="PROFIT_008",
                details={"date_range_days": date_range, "max_days": self.MAX_DATE_RANGE_DAYS}
            )

        # 校验 monthly 类型的日期格式
        if period_type == ProfitPeriodType.MONTHLY.value:
            if period_start.day != 1:
                raise BusinessLogicError(
                    message="月度聚合的开始日期必须是月初",
                    error_code="PROFIT_001",
                    details={"period_start": str(period_start), "day": period_start.day}
                )
            # TODO: 验证 period_end 是月末 (复杂逻辑,暂时跳过)

    # =========================================================================
    # 辅助方法: 聚合计算
    # =========================================================================

    def _get_existing_locked_aggregates(
        self,
        period_type: str,
        period_start: date,
        period_end: date,
        project_id: Optional[int],
    ) -> List[ProfitAggregate]:
        """获取已锁定的聚合记录"""
        query = self.db.query(ProfitAggregate).filter(
            and_(
                ProfitAggregate.period_type == period_type,
                ProfitAggregate.period_start >= datetime.combine(period_start, datetime.min.time()),
                ProfitAggregate.period_end <= datetime.combine(period_end, datetime.max.time()),
                ProfitAggregate.is_locked == True,
            )
        )
        if project_id is not None:
            query = query.filter(ProfitAggregate.project_id == project_id)
        return query.all()

    def _delete_existing_aggregates(
        self,
        period_type: str,
        period_start: date,
        period_end: date,
        project_id: Optional[int],
    ) -> int:
        """删除已存在的聚合记录"""
        query = self.db.query(ProfitAggregate).filter(
            and_(
                ProfitAggregate.period_type == period_type,
                ProfitAggregate.period_start >= datetime.combine(period_start, datetime.min.time()),
                ProfitAggregate.period_end <= datetime.combine(period_end, datetime.max.time()),
            )
        )
        if project_id is not None:
            query = query.filter(ProfitAggregate.project_id == project_id)

        count = query.delete(synchronize_session=False)
        logger.info(f"Deleted {count} existing aggregates")
        return count

    def _get_target_projects(self, project_id: Optional[int]) -> List[Project]:
        """获取需要聚合的项目列表"""
        query = self.db.query(Project)
        if project_id is not None:
            query = query.filter(Project.id == project_id)
        return query.all()

    def _aggregate_for_project(
        self,
        period_type: str,
        period_start: date,
        period_end: date,
        project_id: int,
    ) -> Optional[ProfitAggregate]:
        """
        执行项目级聚合

        业务规则:
        - BR-PROFIT-001: 仅聚合 final_locked 日报
        - BR-PROFIT-006: 收入仅来自 REVENUE
        - BR-PROFIT-007: 成本仅来自 COST
        - BR-PROFIT-002: gross_profit = revenue - cost
        - BR-PROFIT-008: margin = profit/revenue * 100 (HALF_UP)
        """
        # 获取项目下的所有账户
        accounts = self.db.query(AdAccount).filter(
            AdAccount.project_id == project_id
        ).all()

        if not accounts:
            logger.debug(f"No accounts for project {project_id}")
            return None

        account_ids = [a.id for a in accounts]

        # 聚合 daily_reports (仅 final_locked) - BR-PROFIT-001
        daily_report_agg = self.db.query(
            func.coalesce(func.sum(DailyReport.conversions_final), 0).label("total_conversions"),
            func.coalesce(func.sum(DailyReport.real_spend), Decimal("0")).label("total_real_spend"),
        ).filter(
            and_(
                DailyReport.ad_account_id.in_(account_ids),
                DailyReport.report_date >= period_start,
                DailyReport.report_date <= period_end,
                DailyReport.status == "final_locked",  # BR-PROFIT-001
            )
        ).first()

        # 聚合 ledger_entries - REVENUE (BR-PROFIT-006)
        revenue_sum = self.db.query(
            func.coalesce(func.sum(LedgerEntry.amount), Decimal("0")).label("total_revenue")
        ).filter(
            and_(
                LedgerEntry.ad_account_id.in_(account_ids),
                LedgerEntry.entry_date >= datetime.combine(period_start, datetime.min.time()),
                LedgerEntry.entry_date <= datetime.combine(period_end, datetime.max.time()),
                LedgerEntry.entry_type == "REVENUE",
            )
        ).scalar() or Decimal("0")

        # 聚合 ledger_entries - COST (BR-PROFIT-007)
        # 注意: COST 金额在 ledger 中是负数,取绝对值
        cost_sum = self.db.query(
            func.coalesce(func.sum(func.abs(LedgerEntry.amount)), Decimal("0")).label("total_cost")
        ).filter(
            and_(
                LedgerEntry.ad_account_id.in_(account_ids),
                LedgerEntry.entry_date >= datetime.combine(period_start, datetime.min.time()),
                LedgerEntry.entry_date <= datetime.combine(period_end, datetime.max.time()),
                LedgerEntry.entry_type == "COST",
            )
        ).scalar() or Decimal("0")

        # 聚合 TOPUP (仅统计,不参与利润) - BR-PROFIT-006
        topup_sum = self.db.query(
            func.coalesce(func.sum(LedgerEntry.amount), Decimal("0")).label("total_topup")
        ).filter(
            and_(
                LedgerEntry.ad_account_id.in_(account_ids),
                LedgerEntry.entry_date >= datetime.combine(period_start, datetime.min.time()),
                LedgerEntry.entry_date <= datetime.combine(period_end, datetime.max.time()),
                LedgerEntry.entry_type == "TOPUP",
            )
        ).scalar() or Decimal("0")

        # 聚合 TRANSFER_IN / TRANSFER_OUT
        transfer_in_sum = self.db.query(
            func.coalesce(func.sum(LedgerEntry.amount), Decimal("0"))
        ).filter(
            and_(
                LedgerEntry.ad_account_id.in_(account_ids),
                LedgerEntry.entry_date >= datetime.combine(period_start, datetime.min.time()),
                LedgerEntry.entry_date <= datetime.combine(period_end, datetime.max.time()),
                LedgerEntry.entry_type == "TRANSFER_IN",
            )
        ).scalar() or Decimal("0")

        transfer_out_sum = self.db.query(
            func.coalesce(func.sum(func.abs(LedgerEntry.amount)), Decimal("0"))
        ).filter(
            and_(
                LedgerEntry.ad_account_id.in_(account_ids),
                LedgerEntry.entry_date >= datetime.combine(period_start, datetime.min.time()),
                LedgerEntry.entry_date <= datetime.combine(period_end, datetime.max.time()),
                LedgerEntry.entry_type == "TRANSFER_OUT",
            )
        ).scalar() or Decimal("0")

        # 计算毛利 (BR-PROFIT-002)
        total_revenue = Decimal(str(revenue_sum))
        total_cost = Decimal(str(cost_sum))
        gross_profit = total_revenue - total_cost

        # 计算毛利率 (BR-PROFIT-008)
        gross_margin_pct = self._calculate_margin_pct(gross_profit, total_revenue)

        # 创建聚合记录
        aggregate = ProfitAggregate(
            period_type=period_type,
            period_start=datetime.combine(period_start, datetime.min.time()),
            period_end=datetime.combine(period_end, datetime.max.time()),
            project_id=project_id,
            ad_account_id=None,  # 项目级聚合,账户ID为空
            total_revenue=self._round_amount(total_revenue),
            total_cost=self._round_amount(total_cost),
            gross_profit=self._round_amount(gross_profit),
            gross_margin_pct=gross_margin_pct,
            total_conversions=int(daily_report_agg.total_conversions or 0),
            total_real_spend=self._round_amount(Decimal(str(daily_report_agg.total_real_spend or 0))),
            total_topup=self._round_amount(Decimal(str(topup_sum))),
            transfer_in=self._round_amount(Decimal(str(transfer_in_sum))),
            transfer_out=self._round_amount(Decimal(str(transfer_out_sum))),
            is_locked=False,
        )

        logger.debug(
            f"Project {project_id} aggregate: revenue={total_revenue}, "
            f"cost={total_cost}, profit={gross_profit}, margin={gross_margin_pct}"
        )

        return aggregate

    def _aggregate_for_accounts(
        self,
        period_type: str,
        period_start: date,
        period_end: date,
        project_id: int,
    ) -> List[ProfitAggregate]:
        """
        执行账户级聚合 (用于日度聚合)

        业务规则:
        - BR-PROFIT-001: 仅聚合 final_locked 日报
        - BR-PROFIT-006: 收入仅来自 REVENUE
        - BR-PROFIT-007: 成本仅来自 COST

        Args:
            period_type: 周期类型
            period_start: 开始日期
            period_end: 结束日期
            project_id: 项目ID

        Returns:
            List[ProfitAggregate]: 账户级聚合记录列表
        """
        # 获取项目下的所有账户
        accounts = self.db.query(AdAccount).filter(
            AdAccount.project_id == project_id
        ).all()

        if not accounts:
            return []

        aggregates = []

        for account in accounts:
            # 聚合 daily_reports (仅 final_locked)
            daily_report_agg = self.db.query(
                func.coalesce(func.sum(DailyReport.conversions_final), 0).label("total_conversions"),
                func.coalesce(func.sum(DailyReport.real_spend), Decimal("0")).label("total_real_spend"),
            ).filter(
                and_(
                    DailyReport.ad_account_id == account.id,
                    DailyReport.report_date >= period_start,
                    DailyReport.report_date <= period_end,
                    DailyReport.status == "final_locked",
                )
            ).first()

            # 聚合 ledger_entries - REVENUE
            revenue_sum = self.db.query(
                func.coalesce(func.sum(LedgerEntry.amount), Decimal("0"))
            ).filter(
                and_(
                    LedgerEntry.ad_account_id == account.id,
                    LedgerEntry.entry_date >= datetime.combine(period_start, datetime.min.time()),
                    LedgerEntry.entry_date <= datetime.combine(period_end, datetime.max.time()),
                    LedgerEntry.entry_type == "REVENUE",
                )
            ).scalar() or Decimal("0")

            # 聚合 ledger_entries - COST
            cost_sum = self.db.query(
                func.coalesce(func.sum(func.abs(LedgerEntry.amount)), Decimal("0"))
            ).filter(
                and_(
                    LedgerEntry.ad_account_id == account.id,
                    LedgerEntry.entry_date >= datetime.combine(period_start, datetime.min.time()),
                    LedgerEntry.entry_date <= datetime.combine(period_end, datetime.max.time()),
                    LedgerEntry.entry_type == "COST",
                )
            ).scalar() or Decimal("0")

            # 聚合 TOPUP
            topup_sum = self.db.query(
                func.coalesce(func.sum(LedgerEntry.amount), Decimal("0"))
            ).filter(
                and_(
                    LedgerEntry.ad_account_id == account.id,
                    LedgerEntry.entry_date >= datetime.combine(period_start, datetime.min.time()),
                    LedgerEntry.entry_date <= datetime.combine(period_end, datetime.max.time()),
                    LedgerEntry.entry_type == "TOPUP",
                )
            ).scalar() or Decimal("0")

            # 聚合 TRANSFER_IN / TRANSFER_OUT
            transfer_in_sum = self.db.query(
                func.coalesce(func.sum(LedgerEntry.amount), Decimal("0"))
            ).filter(
                and_(
                    LedgerEntry.ad_account_id == account.id,
                    LedgerEntry.entry_date >= datetime.combine(period_start, datetime.min.time()),
                    LedgerEntry.entry_date <= datetime.combine(period_end, datetime.max.time()),
                    LedgerEntry.entry_type == "TRANSFER_IN",
                )
            ).scalar() or Decimal("0")

            transfer_out_sum = self.db.query(
                func.coalesce(func.sum(func.abs(LedgerEntry.amount)), Decimal("0"))
            ).filter(
                and_(
                    LedgerEntry.ad_account_id == account.id,
                    LedgerEntry.entry_date >= datetime.combine(period_start, datetime.min.time()),
                    LedgerEntry.entry_date <= datetime.combine(period_end, datetime.max.time()),
                    LedgerEntry.entry_type == "TRANSFER_OUT",
                )
            ).scalar() or Decimal("0")

            # 计算毛利
            total_revenue = Decimal(str(revenue_sum))
            total_cost = Decimal(str(cost_sum))
            gross_profit = total_revenue - total_cost
            gross_margin_pct = self._calculate_margin_pct(gross_profit, total_revenue)

            # 只有有数据时才创建聚合记录
            if (total_revenue > 0 or total_cost > 0 or
                daily_report_agg.total_conversions > 0 or
                Decimal(str(daily_report_agg.total_real_spend or 0)) > 0):

                aggregate = ProfitAggregate(
                    period_type=period_type,
                    period_start=datetime.combine(period_start, datetime.min.time()),
                    period_end=datetime.combine(period_end, datetime.max.time()),
                    project_id=project_id,
                    ad_account_id=account.id,
                    total_revenue=self._round_amount(total_revenue),
                    total_cost=self._round_amount(total_cost),
                    gross_profit=self._round_amount(gross_profit),
                    gross_margin_pct=gross_margin_pct,
                    total_conversions=int(daily_report_agg.total_conversions or 0),
                    total_real_spend=self._round_amount(Decimal(str(daily_report_agg.total_real_spend or 0))),
                    total_topup=self._round_amount(Decimal(str(topup_sum))),
                    transfer_in=self._round_amount(Decimal(str(transfer_in_sum))),
                    transfer_out=self._round_amount(Decimal(str(transfer_out_sum))),
                    is_locked=False,
                )
                aggregates.append(aggregate)

                logger.debug(
                    f"Account {account.id} aggregate: revenue={total_revenue}, "
                    f"cost={total_cost}, profit={gross_profit}"
                )

        return aggregates

    def _aggregate_global(
        self,
        period_type: str,
        period_start: date,
        period_end: date,
    ) -> Optional[ProfitAggregate]:
        """执行全局聚合 (跨所有项目)"""
        # 聚合所有账户的 daily_reports
        daily_report_agg = self.db.query(
            func.coalesce(func.sum(DailyReport.conversions_final), 0).label("total_conversions"),
            func.coalesce(func.sum(DailyReport.real_spend), Decimal("0")).label("total_real_spend"),
        ).filter(
            and_(
                DailyReport.report_date >= period_start,
                DailyReport.report_date <= period_end,
                DailyReport.status == "final_locked",
            )
        ).first()

        # 聚合所有 REVENUE
        revenue_sum = self.db.query(
            func.coalesce(func.sum(LedgerEntry.amount), Decimal("0"))
        ).filter(
            and_(
                LedgerEntry.entry_date >= datetime.combine(period_start, datetime.min.time()),
                LedgerEntry.entry_date <= datetime.combine(period_end, datetime.max.time()),
                LedgerEntry.entry_type == "REVENUE",
            )
        ).scalar() or Decimal("0")

        # 聚合所有 COST
        cost_sum = self.db.query(
            func.coalesce(func.sum(func.abs(LedgerEntry.amount)), Decimal("0"))
        ).filter(
            and_(
                LedgerEntry.entry_date >= datetime.combine(period_start, datetime.min.time()),
                LedgerEntry.entry_date <= datetime.combine(period_end, datetime.max.time()),
                LedgerEntry.entry_type == "COST",
            )
        ).scalar() or Decimal("0")

        # 聚合所有 TOPUP
        topup_sum = self.db.query(
            func.coalesce(func.sum(LedgerEntry.amount), Decimal("0"))
        ).filter(
            and_(
                LedgerEntry.entry_date >= datetime.combine(period_start, datetime.min.time()),
                LedgerEntry.entry_date <= datetime.combine(period_end, datetime.max.time()),
                LedgerEntry.entry_type == "TOPUP",
            )
        ).scalar() or Decimal("0")

        total_revenue = Decimal(str(revenue_sum))
        total_cost = Decimal(str(cost_sum))
        gross_profit = total_revenue - total_cost
        gross_margin_pct = self._calculate_margin_pct(gross_profit, total_revenue)

        aggregate = ProfitAggregate(
            period_type=period_type,
            period_start=datetime.combine(period_start, datetime.min.time()),
            period_end=datetime.combine(period_end, datetime.max.time()),
            project_id=None,  # 全局聚合
            ad_account_id=None,
            total_revenue=self._round_amount(total_revenue),
            total_cost=self._round_amount(total_cost),
            gross_profit=self._round_amount(gross_profit),
            gross_margin_pct=gross_margin_pct,
            total_conversions=int(daily_report_agg.total_conversions or 0),
            total_real_spend=self._round_amount(Decimal(str(daily_report_agg.total_real_spend or 0))),
            total_topup=self._round_amount(Decimal(str(topup_sum))),
            transfer_in=Decimal("0"),  # 全局级不统计转账
            transfer_out=Decimal("0"),
            is_locked=False,
        )

        return aggregate

    # =========================================================================
    # 辅助方法: 计算逻辑
    # =========================================================================

    def _calculate_margin_pct(
        self,
        gross_profit: Decimal,
        total_revenue: Decimal,
    ) -> Optional[Decimal]:
        """
        计算毛利率 (BR-PROFIT-008)

        公式: gross_margin_pct = (gross_profit / total_revenue) * 100
        边界处理: revenue = 0 时返回 None (或 0)

        Args:
            gross_profit: 毛利
            total_revenue: 总收入

        Returns:
            Decimal or None: 毛利率 (保留 4 位小数)
        """
        if total_revenue == 0:
            # BR-PROFIT-008: 当 revenue = 0 时,毛利率为 None (或 0)
            return None

        margin = (gross_profit / total_revenue) * Decimal("100")
        # HALF_UP 四舍五入到 4 位小数
        return margin.quantize(
            Decimal(f"0.{'0' * self.MARGIN_DECIMAL_PLACES}"),
            rounding=ROUND_HALF_UP
        )

    def _round_amount(self, amount: Decimal) -> Decimal:
        """金额四舍五入到 2 位小数"""
        return amount.quantize(
            Decimal(f"0.{'0' * self.AMOUNT_DECIMAL_PLACES}"),
            rounding=ROUND_HALF_UP
        )

    def _calculate_summary(
        self,
        aggregates: List[ProfitAggregate],
    ) -> Dict[str, Any]:
        """计算汇总数据"""
        total_revenue = sum(a.total_revenue for a in aggregates)
        total_cost = sum(a.total_cost for a in aggregates)
        gross_profit = sum(a.gross_profit for a in aggregates)
        total_conversions = sum(a.total_conversions for a in aggregates)
        total_real_spend = sum(a.total_real_spend for a in aggregates)
        total_topup = sum(a.total_topup for a in aggregates)

        margin_pct = self._calculate_margin_pct(gross_profit, total_revenue)

        return {
            "total_revenue": str(total_revenue),
            "total_cost": str(total_cost),
            "gross_profit": str(gross_profit),
            "gross_margin_pct": str(margin_pct) if margin_pct is not None else "0",
            "total_conversions": total_conversions,
            "total_real_spend": str(total_real_spend),
            "total_topup": str(total_topup),
            "report_count": len(aggregates),
        }

    def _group_by_project(
        self,
        aggregates: List[ProfitAggregate],
        include_accounts: bool = False,
    ) -> List[Dict[str, Any]]:
        """按项目分组聚合数据"""
        # 过滤出项目级聚合 (ad_account_id is None)
        project_aggs = [a for a in aggregates if a.ad_account_id is None and a.project_id is not None]

        result = []
        for agg in project_aggs:
            project_data = {
                "project_id": agg.project_id,
                "revenue": str(agg.total_revenue),
                "cost": str(agg.total_cost),
                "gross_profit": str(agg.gross_profit),
                "gross_margin_pct": str(agg.gross_margin_pct) if agg.gross_margin_pct else "0",
                "conversions": agg.total_conversions,
                "real_spend": str(agg.total_real_spend),
            }

            if include_accounts:
                # 查找该项目的账户级聚合
                account_aggs = [
                    a for a in aggregates
                    if a.project_id == agg.project_id and a.ad_account_id is not None
                ]
                project_data["accounts"] = [
                    {
                        "account_id": aa.ad_account_id,
                        "revenue": str(aa.total_revenue),
                        "cost": str(aa.total_cost),
                        "conversions": aa.total_conversions,
                    }
                    for aa in account_aggs
                ]
            else:
                project_data["accounts"] = []

            result.append(project_data)

        return result

    def _build_report_data(
        self,
        aggregates: List[ProfitAggregate],
        period_month: date,
    ) -> Dict[str, Any]:
        """构建报表快照数据"""
        summary = self._calculate_summary(aggregates)
        details = self._group_by_project(aggregates, include_accounts=True)

        return {
            "period": {
                "year": period_month.year,
                "month": period_month.month,
            },
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "summary": summary,
            "details": details,
        }


# =========================================================================
# 便捷函数
# =========================================================================

def get_profit_service(db: Session) -> ProfitService:
    """获取 ProfitService 实例"""
    return ProfitService(db)
