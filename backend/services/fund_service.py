"""
资金总览业务逻辑层 (重构版)

SoT References:
- MASTER.md v4.4 §4.5.5 资金口径定义
- MASTER.md v4.4 §2.4 (7角色模型)
- A2-fund-overview.md §2 数据需求
- LEDGER_SOT.md v1.1 (账本规则)

计算公式 (MASTER.md §4.5.5):
- 累计充值 = SUM(topup_record.amount WHERE status='completed')
- 累计消耗 = SUM(ad_spend_daily.spend)
- 当前余额 = 累计充值 - 累计消耗
- 应收款 = SUM(conversions × unit_price) - 累计回款
- 资金占用 = 累计充值 - 累计回款

权限矩阵 (MASTER.md v4.4 §2.4 - 7角色模型):
- ceo, finance: 全公司数据
- admin: 全公司数据 (只读)
- project_owner: 自己负责的项目
- account_manager: 账户余额部分
- supervisor: 团队相关数据

Version: 2.0
Author: Claude Code
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List, Optional, Tuple, Dict, Any
from uuid import UUID

from sqlalchemy import func, and_, or_, desc, asc, case
from sqlalchemy.orm import Session, joinedload

from backend.models import (
    User, Project, AdAccount, DailyReport,
    TopupRequest, Supplier, UserRole
)
# Note: AdSpendDaily is a placeholder, using DailyReport.raw_spend for spend data
from backend.models.enums import TopupRequestStatus
from backend.schemas.fund import (
    FundOverviewResponse,
    FundDistributionProjectsResponse,
    FundDistributionChannelsResponse,
    ReceivableListResponse,
    PaymentListResponse,
    ProjectFundItem,
    ChannelFundItem,
    ReceivableItem,
    PaymentItem,
    FundAlertItem,
    FundAlertsResponse,
)
from backend.exceptions.custom_exceptions import (
    PermissionDeniedError,
    ResourceNotFoundError,
)


class FundService:
    """
    资金总览服务类

    职责:
    - 计算资金概览指标
    - 提供资金分布数据
    - 生成资金预警

    权限矩阵 (MASTER.md v4.4 §2.4 - 7角色模型):
    - ceo, finance: 全公司数据
    - admin: 全公司数据 (只读)
    - project_owner: 自己负责的项目
    - account_manager: 账户余额部分
    - supervisor: 团队相关数据
    """

    # 资金占用率预警阈值
    OCCUPY_RATE_WARNING = Decimal("0.80")  # 80%
    OCCUPY_RATE_CRITICAL = Decimal("0.90")  # 90%

    def __init__(self, db: Session):
        self.db = db

    # ========== 资金概览 ==========

    def get_fund_overview(
        self,
        current_user: User,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None
    ) -> FundOverviewResponse:
        """
        获取资金概览

        计算 5 个核心资金指标 (MASTER.md §4.5.5)
        """
        # 权限检查
        self._check_overview_permission(current_user)

        # 构建日期范围
        if date_to is None:
            date_to = date.today()

        # 获取项目范围 (基于权限)
        project_ids = self._get_accessible_project_ids(current_user)

        # 1. 累计充值
        total_topup = self._calculate_total_topup(project_ids, date_from, date_to)

        # 2. 累计消耗
        total_spend = self._calculate_total_spend(project_ids, date_from, date_to)

        # 3. 当前余额
        current_balance = total_topup - total_spend

        # 4. 累计回款 (暂时从项目收入估算，待 receivable 表实现)
        total_received = self._calculate_total_received(project_ids, date_from, date_to)

        # 5. 应收款 = 预计收入 - 已回款
        total_revenue = self._calculate_total_revenue(project_ids, date_from, date_to)
        total_receivable = max(Decimal("0"), total_revenue - total_received)

        # 6. 资金占用
        fund_occupied = total_topup - total_received

        # 计算变化率 (与上月对比)
        topup_change, spend_change, balance_change = self._calculate_changes(
            project_ids, date_from, date_to
        )

        # 计算资金占用率
        occupy_rate = None
        if total_topup > 0:
            occupy_rate = float((fund_occupied / total_topup) * 100)

        # 待收款笔数 (简化实现: 统计有应收的项目数)
        pending_receivable_count = self._count_pending_receivables(project_ids)

        return FundOverviewResponse(
            total_topup=total_topup,
            total_spend=total_spend,
            current_balance=current_balance,
            total_receivable=total_receivable,
            total_received=total_received,
            fund_occupied=fund_occupied,
            topup_change=topup_change,
            spend_change=spend_change,
            balance_change=balance_change,
            occupy_rate=occupy_rate,
            pending_receivable_count=pending_receivable_count,
            date_from=date_from,
            date_to=date_to,
        )

    def _calculate_total_topup(
        self,
        project_ids: Optional[List[int]],
        date_from: Optional[date],
        date_to: Optional[date]
    ) -> Decimal:
        """计算累计充值"""
        query = self.db.query(func.coalesce(func.sum(TopupRequest.amount), Decimal("0")))

        # 只计算已完成的充值
        query = query.filter(TopupRequest.status == TopupRequestStatus.COMPLETED.value)

        if project_ids is not None:
            # 通过 ad_account -> project 关联
            query = query.join(AdAccount, TopupRequest.ad_account_id == AdAccount.id)
            query = query.filter(AdAccount.project_id.in_(project_ids))

        if date_from:
            query = query.filter(TopupRequest.created_at >= date_from)
        if date_to:
            query = query.filter(TopupRequest.created_at <= date_to + timedelta(days=1))

        result = query.scalar()
        return result if result else Decimal("0")

    def _calculate_total_spend(
        self,
        project_ids: Optional[List[int]],
        date_from: Optional[date],
        date_to: Optional[date]
    ) -> Decimal:
        """
        计算累计消耗

        使用 DailyReport.raw_spend 作为消耗数据源
        (AdSpendDaily 是占位符，待重构)
        """
        query = self.db.query(func.coalesce(func.sum(DailyReport.raw_spend), Decimal("0")))

        if project_ids is not None:
            query = query.join(AdAccount, DailyReport.ad_account_id == AdAccount.id)
            query = query.filter(AdAccount.project_id.in_(project_ids))

        if date_from:
            query = query.filter(DailyReport.report_date >= date_from)
        if date_to:
            query = query.filter(DailyReport.report_date <= date_to)

        result = query.scalar()
        return result if result else Decimal("0")

    def _calculate_total_revenue(
        self,
        project_ids: Optional[List[int]],
        date_from: Optional[date],
        date_to: Optional[date]
    ) -> Decimal:
        """
        计算预计收入 = SUM(conversions × unit_price)

        基于 daily_report.conversions 和 daily_report.unit_price
        (unit_price 在 DailyReport 表中，从项目继承)
        """
        query = self.db.query(
            func.coalesce(
                func.sum(DailyReport.conversions * DailyReport.unit_price),
                Decimal("0")
            )
        )

        # 只计算有单价的日报
        query = query.filter(DailyReport.unit_price.isnot(None))
        query = query.filter(DailyReport.unit_price > 0)

        if project_ids is not None:
            query = query.join(AdAccount, DailyReport.ad_account_id == AdAccount.id)
            query = query.filter(AdAccount.project_id.in_(project_ids))

        if date_from:
            query = query.filter(DailyReport.report_date >= date_from)
        if date_to:
            query = query.filter(DailyReport.report_date <= date_to)

        result = query.scalar()
        return result if result else Decimal("0")

    def _calculate_total_received(
        self,
        project_ids: Optional[List[int]],
        date_from: Optional[date],
        date_to: Optional[date]
    ) -> Decimal:
        """
        计算累计回款

        TODO: 待 receivable 表实现后更新
        目前暂时返回 0，或者可以从其他来源估算
        """
        # 暂时返回 0，待 receivable 表实现
        return Decimal("0")

    def _calculate_changes(
        self,
        project_ids: Optional[List[int]],
        date_from: Optional[date],
        date_to: Optional[date]
    ) -> Tuple[Optional[float], Optional[float], Optional[float]]:
        """计算与上月的变化率"""
        # 简化实现：暂时返回 None
        # TODO: 实现完整的月度对比逻辑
        return None, None, None

    def _count_pending_receivables(self, project_ids: Optional[List[int]]) -> int:
        """
        统计待收款笔数

        简化实现：统计有日报且有单价的活跃项目数
        """
        # 统计有日报且日报有单价的项目数
        query = self.db.query(func.count(func.distinct(AdAccount.project_id)))
        query = query.join(DailyReport, DailyReport.ad_account_id == AdAccount.id)
        query = query.filter(DailyReport.unit_price.isnot(None))
        query = query.filter(DailyReport.unit_price > 0)

        if project_ids is not None:
            query = query.filter(AdAccount.project_id.in_(project_ids))

        return query.scalar() or 0

    # ========== 资金分布 - 按项目 ==========

    def get_fund_distribution_by_projects(
        self,
        current_user: User,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "topup",
        order: str = "desc",
        date_from: Optional[date] = None,
        date_to: Optional[date] = None
    ) -> FundDistributionProjectsResponse:
        """获取按项目的资金分布"""
        # 权限检查
        self._check_overview_permission(current_user)

        # 获取可访问的项目
        project_ids = self._get_accessible_project_ids(current_user)

        # 构建基础查询
        query = self.db.query(Project).options(
            joinedload(Project.creator)
        )

        if project_ids is not None:
            query = query.filter(Project.id.in_(project_ids))

        # 获取总数
        total = query.count()

        # 分页
        offset = (page - 1) * page_size
        projects = query.offset(offset).limit(page_size).all()

        # 构建结果
        items = []
        total_topup_sum = Decimal("0")
        total_spend_sum = Decimal("0")
        total_balance_sum = Decimal("0")

        for project in projects:
            # 计算每个项目的资金数据
            project_topup = self._calculate_project_topup(project.id, date_from, date_to)
            project_spend = self._calculate_project_spend(project.id, date_from, date_to)
            project_balance = project_topup - project_spend
            project_revenue = self._calculate_project_revenue(project.id, date_from, date_to)

            # 获取项目的平均单价 (从日报)
            project_unit_price = self._get_project_unit_price(project.id)

            items.append(ProjectFundItem(
                project_id=project.id,
                project_name=project.name,
                owner_id=project.created_by,
                owner_name=project.creator.full_name if project.creator else None,
                total_topup=project_topup,
                total_spend=project_spend,
                balance=project_balance,
                receivable=project_revenue,
                received=Decimal("0"),  # TODO: 待 receivable 表实现
                unit_price=project_unit_price,
                is_pricing_pending=project_unit_price is None or project_unit_price <= 0,
            ))

            total_topup_sum += project_topup
            total_spend_sum += project_spend
            total_balance_sum += project_balance

        # 排序
        reverse = order == "desc"
        if sort_by == "topup":
            items.sort(key=lambda x: x.total_topup, reverse=reverse)
        elif sort_by == "spend":
            items.sort(key=lambda x: x.total_spend, reverse=reverse)
        elif sort_by == "balance":
            items.sort(key=lambda x: x.balance, reverse=reverse)

        return FundDistributionProjectsResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            summary={
                "total_topup": total_topup_sum,
                "total_spend": total_spend_sum,
                "total_balance": total_balance_sum,
            }
        )

    def _calculate_project_topup(
        self,
        project_id: int,
        date_from: Optional[date],
        date_to: Optional[date]
    ) -> Decimal:
        """计算单个项目的充值"""
        query = self.db.query(func.coalesce(func.sum(TopupRequest.amount), Decimal("0")))
        query = query.join(AdAccount, TopupRequest.ad_account_id == AdAccount.id)
        query = query.filter(AdAccount.project_id == project_id)
        query = query.filter(TopupRequest.status == TopupRequestStatus.COMPLETED.value)

        if date_from:
            query = query.filter(TopupRequest.created_at >= date_from)
        if date_to:
            query = query.filter(TopupRequest.created_at <= date_to + timedelta(days=1))

        return query.scalar() or Decimal("0")

    def _calculate_project_spend(
        self,
        project_id: int,
        date_from: Optional[date],
        date_to: Optional[date]
    ) -> Decimal:
        """
        计算单个项目的消耗

        使用 DailyReport.raw_spend 作为消耗数据源
        """
        query = self.db.query(func.coalesce(func.sum(DailyReport.raw_spend), Decimal("0")))
        query = query.join(AdAccount, DailyReport.ad_account_id == AdAccount.id)
        query = query.filter(AdAccount.project_id == project_id)

        if date_from:
            query = query.filter(DailyReport.report_date >= date_from)
        if date_to:
            query = query.filter(DailyReport.report_date <= date_to)

        return query.scalar() or Decimal("0")

    def _calculate_project_revenue(
        self,
        project_id: int,
        date_from: Optional[date],
        date_to: Optional[date]
    ) -> Decimal:
        """
        计算单个项目的预计收入

        使用 DailyReport.unit_price (从项目继承)
        """
        query = self.db.query(
            func.coalesce(
                func.sum(DailyReport.conversions * DailyReport.unit_price),
                Decimal("0")
            )
        )
        query = query.join(AdAccount, DailyReport.ad_account_id == AdAccount.id)
        query = query.filter(AdAccount.project_id == project_id)
        query = query.filter(DailyReport.unit_price.isnot(None))

        if date_from:
            query = query.filter(DailyReport.report_date >= date_from)
        if date_to:
            query = query.filter(DailyReport.report_date <= date_to)

        return query.scalar() or Decimal("0")

    def _get_project_unit_price(self, project_id: int) -> Optional[Decimal]:
        """
        获取项目的单价

        从该项目的日报中获取最新的 unit_price
        """
        result = self.db.query(DailyReport.unit_price).join(
            AdAccount, DailyReport.ad_account_id == AdAccount.id
        ).filter(
            AdAccount.project_id == project_id,
            DailyReport.unit_price.isnot(None),
            DailyReport.unit_price > 0
        ).order_by(
            DailyReport.report_date.desc()
        ).first()

        return result[0] if result else None

    # ========== 资金分布 - 按渠道 ==========

    def get_fund_distribution_by_channels(
        self,
        current_user: User,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "topup",
        order: str = "desc",
        date_from: Optional[date] = None,
        date_to: Optional[date] = None
    ) -> FundDistributionChannelsResponse:
        """获取按渠道的资金分布"""
        # 权限检查
        self._check_overview_permission(current_user)

        # 获取可访问的项目
        project_ids = self._get_accessible_project_ids(current_user)

        # 按供应商分组统计
        query = self.db.query(
            Supplier.id,
            Supplier.name,
            func.coalesce(func.sum(TopupRequest.amount), Decimal("0")).label("total_topup"),
            func.count(func.distinct(AdAccount.id)).label("account_count")
        )
        query = query.outerjoin(AdAccount, AdAccount.supplier_id == Supplier.id)
        query = query.outerjoin(
            TopupRequest,
            and_(
                TopupRequest.ad_account_id == AdAccount.id,
                TopupRequest.status == TopupRequestStatus.COMPLETED.value
            )
        )

        if project_ids is not None:
            query = query.filter(AdAccount.project_id.in_(project_ids))

        query = query.group_by(Supplier.id, Supplier.name)

        # 获取总数
        total = query.count()

        # 分页
        offset = (page - 1) * page_size
        results = query.offset(offset).limit(page_size).all()

        # 构建结果
        items = []
        total_topup_sum = Decimal("0")
        total_spend_sum = Decimal("0")
        total_balance_sum = Decimal("0")

        for row in results:
            channel_id, channel_name, total_topup, account_count = row

            # 计算渠道消耗
            channel_spend = self._calculate_channel_spend(
                channel_id, project_ids, date_from, date_to
            )
            channel_balance = total_topup - channel_spend

            items.append(ChannelFundItem(
                channel_id=str(channel_id) if channel_id else None,
                channel_name=channel_name or "未知渠道",
                total_topup=total_topup,
                total_spend=channel_spend,
                balance=channel_balance,
                account_count=account_count or 0,
            ))

            total_topup_sum += total_topup
            total_spend_sum += channel_spend
            total_balance_sum += channel_balance

        # 排序
        reverse = order == "desc"
        if sort_by == "topup":
            items.sort(key=lambda x: x.total_topup, reverse=reverse)
        elif sort_by == "spend":
            items.sort(key=lambda x: x.total_spend, reverse=reverse)
        elif sort_by == "balance":
            items.sort(key=lambda x: x.balance, reverse=reverse)

        return FundDistributionChannelsResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            summary={
                "total_topup": total_topup_sum,
                "total_spend": total_spend_sum,
                "total_balance": total_balance_sum,
            }
        )

    def _calculate_channel_spend(
        self,
        supplier_id: int,
        project_ids: Optional[List[int]],
        date_from: Optional[date],
        date_to: Optional[date]
    ) -> Decimal:
        """
        计算渠道消耗

        使用 DailyReport.raw_spend 作为消耗数据源
        """
        query = self.db.query(func.coalesce(func.sum(DailyReport.raw_spend), Decimal("0")))
        query = query.join(AdAccount, DailyReport.ad_account_id == AdAccount.id)
        query = query.filter(AdAccount.supplier_id == supplier_id)

        if project_ids is not None:
            query = query.filter(AdAccount.project_id.in_(project_ids))

        if date_from:
            query = query.filter(DailyReport.report_date >= date_from)
        if date_to:
            query = query.filter(DailyReport.report_date <= date_to)

        return query.scalar() or Decimal("0")

    # ========== 应收明细 ==========

    def get_receivables(
        self,
        current_user: User,
        page: int = 1,
        page_size: int = 20,
        project_id: Optional[int] = None,
        status: Optional[str] = None
    ) -> ReceivableListResponse:
        """
        获取应收明细

        TODO: 待 receivable 表实现后完善
        目前基于 daily_reports 计算模拟数据
        """
        # 权限检查
        self._check_overview_permission(current_user)

        # 暂时返回空列表，待 receivable 表实现
        return ReceivableListResponse(
            items=[],
            total=0,
            page=page,
            page_size=page_size,
            total_amount=Decimal("0"),
            total_pending=Decimal("0"),
        )

    # ========== 回款记录 ==========

    def get_payments(
        self,
        current_user: User,
        page: int = 1,
        page_size: int = 20,
        project_id: Optional[int] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None
    ) -> PaymentListResponse:
        """
        获取回款记录

        TODO: 待 receivable 表实现后完善
        """
        # 权限检查
        self._check_overview_permission(current_user)

        # 暂时返回空列表，待实现
        return PaymentListResponse(
            items=[],
            total=0,
            page=page,
            page_size=page_size,
            total_amount=Decimal("0"),
        )

    # ========== 资金预警 ==========

    def get_fund_alerts(self, current_user: User) -> FundAlertsResponse:
        """获取资金预警列表"""
        # 权限检查
        self._check_overview_permission(current_user)

        alerts = []

        # 获取资金概览
        overview = self.get_fund_overview(current_user)

        # 检查资金占用率预警
        if overview.occupy_rate and overview.occupy_rate >= float(self.OCCUPY_RATE_CRITICAL * 100):
            alerts.append(FundAlertItem(
                alert_type="high_occupy_rate",
                severity="critical",
                message=f"资金占用率过高: {overview.occupy_rate:.1f}%，超过 90% 警戒线",
                value=Decimal(str(overview.occupy_rate)),
                threshold=self.OCCUPY_RATE_CRITICAL * 100,
                created_at=datetime.now(),
            ))
        elif overview.occupy_rate and overview.occupy_rate >= float(self.OCCUPY_RATE_WARNING * 100):
            alerts.append(FundAlertItem(
                alert_type="high_occupy_rate",
                severity="high",
                message=f"资金占用率较高: {overview.occupy_rate:.1f}%，超过 80% 预警线",
                value=Decimal(str(overview.occupy_rate)),
                threshold=self.OCCUPY_RATE_WARNING * 100,
                created_at=datetime.now(),
            ))

        # 检查余额为负
        if overview.current_balance < 0:
            alerts.append(FundAlertItem(
                alert_type="negative_balance",
                severity="critical",
                message=f"账户余额为负: ¥{overview.current_balance:,.2f}",
                value=overview.current_balance,
                created_at=datetime.now(),
            ))

        critical_count = sum(1 for a in alerts if a.severity == "critical")
        high_count = sum(1 for a in alerts if a.severity == "high")

        return FundAlertsResponse(
            alerts=alerts,
            total=len(alerts),
            critical_count=critical_count,
            high_count=high_count,
        )

    # ========== 权限辅助方法 ==========

    def _check_overview_permission(self, current_user: User) -> None:
        """
        检查资金概览访问权限

        允许角色 (MASTER.md v4.4 §2.4):
        - ceo, finance, admin: 全部数据
        - project_owner: 自己项目
        - account_manager: 账户余额
        - supervisor: 团队数据
        """
        allowed_roles = ["ceo", "finance", "project_owner", "account_manager", "admin", "supervisor"]
        if current_user.role not in allowed_roles:
            raise PermissionDeniedError("无权访问资金总览")

    def _get_accessible_project_ids(self, current_user: User) -> Optional[List[int]]:
        """
        获取用户可访问的项目ID列表

        返回 (MASTER.md v4.4 §2.4):
        - None: 可访问全部项目 (ceo, finance, admin)
        - List[int]: 限定的项目ID列表 (project_owner, account_manager, supervisor)
        """
        if current_user.role in ["ceo", "finance", "admin"]:
            return None  # 全部项目

        if current_user.role == "project_owner":
            # 查询用户负责的项目 (使用 created_by 字段)
            project_ids = self.db.query(Project.id).filter(
                Project.created_by == current_user.id
            ).all()
            return [p[0] for p in project_ids]

        if current_user.role == "supervisor":
            # 主管: 查询团队成员负责的项目
            # TODO: 待 team 表实现后完善，目前返回全部项目
            # 暂时使用与 project_owner 相同逻辑
            project_ids = self.db.query(Project.id).filter(
                Project.created_by == current_user.id
            ).all()
            return [p[0] for p in project_ids]

        if current_user.role == "account_manager":
            # 查询用户管理的账户所属项目
            project_ids = self.db.query(func.distinct(AdAccount.project_id)).filter(
                AdAccount.assigned_to == current_user.id
            ).all()
            return [p[0] for p in project_ids if p[0] is not None]

        return []  # 其他角色无权访问 (pitcher)


def get_fund_service(db: Session) -> FundService:
    """依赖注入工厂函数"""
    return FundService(db)
