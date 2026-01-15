"""
报表服务
Version: 1.0
Author: Claude协作开发

提供多维度报表查询和生成功能
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, case, desc

from backend.models import (
    Project,
    AdAccount,
    AccountPerformance,
    Channel,
    LedgerEntry,
    LedgerEntryType,
    ReconciliationBatch,
    ReconciliationBatchStatus,
    TopupRequest,
    TopupStatus,
    DailyReport,
    DailyReportStatus,
    User,
)
from backend.schemas.reports import (
    ReportQueryRequest,
    PerformanceReportItem,
    PerformanceReportResponse,
    ProfitReportItem,
    ProfitReportResponse,
    ReconciliationReportItem,
    ReconciliationReportResponse,
    FinancialSummaryItem,
    FinancialSummaryResponse,
    DashboardSummary,
    TrendDataPoint,
    TrendReportResponse,
    ReportPeriod,
    ReportGroupBy,
)


class ReportsService:
    """报表服务类"""

    def __init__(self, db: Session):
        self.db = db

    # ========== 效果报表 ==========

    async def get_performance_report(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        project_ids: Optional[List[int]] = None,
        channel_ids: Optional[List[int]] = None,
        group_by: Optional[List[str]] = None,
    ) -> PerformanceReportResponse:
        """获取效果报表"""

        # 默认日期范围：最近30天
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=30)

        # 构建查询 - 使用 AccountPerformance 替代 AdSpendDaily
        query = (
            self.db.query(
                Project.id.label("project_id"),
                Project.name.label("project_name"),
                Channel.id.label("channel_id"),
                Channel.name.label("channel_name"),
                func.coalesce(func.sum(AccountPerformance.spend), 0).label(
                    "total_spend"
                ),
                func.coalesce(func.sum(AccountPerformance.conversions), 0).label(
                    "total_leads"
                ),  # leads_count → conversions
            )
            .select_from(AccountPerformance)
            .join(AdAccount, AccountPerformance.ad_account_id == AdAccount.id)
            .join(Project, AdAccount.project_id == Project.id)
            .join(Channel, AdAccount.channel_id == Channel.id)
            .filter(
                AccountPerformance.date >= start_date,
                AccountPerformance.date <= end_date,
            )
        )

        # 应用过滤条件
        if project_ids:
            query = query.filter(Project.id.in_(project_ids))
        if channel_ids:
            query = query.filter(Channel.id.in_(channel_ids))

        # 分组
        query = query.group_by(Project.id, Project.name, Channel.id, Channel.name)

        results = query.all()

        # 转换为响应模型
        items = []
        total_spend = Decimal("0.00")
        total_leads = 0

        for row in results:
            spend = Decimal(str(row.total_spend or 0))
            leads = int(row.total_leads or 0)
            cpa = spend / leads if leads > 0 else None

            items.append(
                PerformanceReportItem(
                    project_id=row.project_id,
                    project_name=row.project_name,
                    channel_id=row.channel_id,
                    channel_name=row.channel_name,
                    total_spend=spend,
                    total_leads=leads,
                    cpa=cpa,
                )
            )

            total_spend += spend
            total_leads += leads

        # 计算汇总
        summary = {
            "total_spend": str(total_spend.quantize(Decimal("0.01"))),
            "total_leads": total_leads,
            "avg_cpa": str((total_spend / total_leads).quantize(Decimal("0.01")))
            if total_leads > 0
            else None,
            "project_count": len(
                set(item.project_id for item in items if item.project_id)
            ),
            "channel_count": len(
                set(item.channel_id for item in items if item.channel_id)
            ),
        }

        return PerformanceReportResponse(
            items=items,
            summary=summary,
            meta={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "generated_at": datetime.now().isoformat(),
            },
        )

    # ========== 利润报表 ==========

    async def get_profit_report(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        project_ids: Optional[List[int]] = None,
    ) -> ProfitReportResponse:
        """获取利润报表"""

        # 默认日期范围：最近30天
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=30)

        # 获取项目消耗 - 使用 AccountPerformance 替代 AdSpendDaily
        spend_query = (
            self.db.query(
                Project.id.label("project_id"),
                Project.name.label("project_name"),
                func.coalesce(func.sum(AccountPerformance.spend), 0).label("ad_spend"),
            )
            .select_from(AccountPerformance)
            .join(AdAccount, AccountPerformance.ad_account_id == AdAccount.id)
            .join(Project, AdAccount.project_id == Project.id)
            .filter(
                AccountPerformance.date >= start_date,
                AccountPerformance.date <= end_date,
            )
        )

        if project_ids:
            spend_query = spend_query.filter(Project.id.in_(project_ids))

        spend_query = spend_query.group_by(Project.id, Project.name)
        spend_results = {row.project_id: row for row in spend_query.all()}

        # 获取项目充值
        topup_query = (
            self.db.query(
                AdAccount.project_id.label("project_id"),
                func.coalesce(func.sum(LedgerEntry.amount), 0).label("topup_amount"),
            )
            .select_from(LedgerEntry)
            .join(AdAccount, LedgerEntry.ad_account_id == AdAccount.id)
            .filter(
                LedgerEntry.entry_type == LedgerEntryType.TOPUP.value,  # 使用枚举值
                func.date(LedgerEntry.entry_date) >= start_date,
                func.date(LedgerEntry.entry_date) <= end_date,
            )
        )

        if project_ids:
            topup_query = topup_query.filter(AdAccount.project_id.in_(project_ids))

        topup_query = topup_query.group_by(AdAccount.project_id)
        topup_results = {
            row.project_id: Decimal(str(row.topup_amount or 0))
            for row in topup_query.all()
        }

        # 合并结果
        items = []
        total_revenue = Decimal("0.00")
        total_cost = Decimal("0.00")
        total_profit = Decimal("0.00")

        for project_id, spend_row in spend_results.items():
            ad_spend = Decimal(str(spend_row.ad_spend or 0))
            topup_amount = topup_results.get(project_id, Decimal("0.00"))

            # 简化计算：收入 = 充值，成本 = 消耗
            revenue = topup_amount
            cost = ad_spend
            profit = revenue - cost
            profit_rate = float(profit / revenue * 100) if revenue > 0 else None

            items.append(
                ProfitReportItem(
                    project_id=project_id,
                    project_name=spend_row.project_name,
                    revenue=revenue,
                    cost=cost,
                    profit=profit,
                    profit_rate=profit_rate,
                    ad_spend=ad_spend,
                    topup_amount=topup_amount,
                )
            )

            total_revenue += revenue
            total_cost += cost
            total_profit += profit

        # 排序：按利润降序
        items.sort(key=lambda x: x.profit, reverse=True)

        summary = {
            "total_revenue": str(total_revenue.quantize(Decimal("0.01"))),
            "total_cost": str(total_cost.quantize(Decimal("0.01"))),
            "total_profit": str(total_profit.quantize(Decimal("0.01"))),
            "profit_rate": float(total_profit / total_revenue * 100)
            if total_revenue > 0
            else None,
            "project_count": len(items),
        }

        return ProfitReportResponse(
            items=items,
            summary=summary,
            meta={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "generated_at": datetime.now().isoformat(),
            },
        )

    # ========== 对账报表 ==========

    async def get_reconciliation_report(
        self, start_date: Optional[date] = None, end_date: Optional[date] = None
    ) -> ReconciliationReportResponse:
        """获取对账报表"""

        # 默认日期范围：最近30天
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=30)

        # 按状态统计批次
        status_query = (
            self.db.query(
                ReconciliationBatch.status,
                func.count(ReconciliationBatch.id).label("count"),
                func.coalesce(
                    func.sum(ReconciliationBatch.total_system_spend), 0
                ).label("system_spend"),
                func.coalesce(
                    func.sum(ReconciliationBatch.total_actual_spend), 0
                ).label("actual_spend"),
                func.coalesce(func.sum(ReconciliationBatch.discrepancy), 0).label(
                    "discrepancy"
                ),
            )
            .filter(
                ReconciliationBatch.period_end >= start_date,
                ReconciliationBatch.period_end <= end_date,
            )
            .group_by(ReconciliationBatch.status)
        )

        status_results = {row.status: row for row in status_query.all()}

        # 构建响应
        total_batches = sum(row.count for row in status_results.values())
        draft = status_results.get("draft")
        pending = status_results.get("pending_review")
        approved = status_results.get("approved")
        completed = status_results.get("completed")

        total_system_spend = sum(
            Decimal(str(row.system_spend or 0)) for row in status_results.values()
        )
        total_actual_spend = sum(
            Decimal(str(row.actual_spend or 0)) for row in status_results.values()
        )
        total_discrepancy = sum(
            Decimal(str(row.discrepancy or 0)) for row in status_results.values()
        )

        # 确保 total_discrepancy 是 Decimal 类型
        if not isinstance(total_discrepancy, Decimal):
            total_discrepancy = Decimal(str(total_discrepancy or 0))

        items = [
            ReconciliationReportItem(
                period=f"{start_date.isoformat()} ~ {end_date.isoformat()}",
                total_batches=total_batches,
                draft_batches=draft.count if draft else 0,
                pending_review_batches=pending.count if pending else 0,
                approved_batches=approved.count if approved else 0,
                completed_batches=completed.count if completed else 0,
                total_system_spend=total_system_spend,
                total_actual_spend=total_actual_spend,
                total_discrepancy=total_discrepancy,
                completion_rate=float(
                    (completed.count if completed else 0) / total_batches * 100
                )
                if total_batches > 0
                else 0,
                discrepancy_rate=float(
                    abs(total_discrepancy) / total_system_spend * 100
                )
                if total_system_spend > 0
                else 0,
            )
        ]

        summary = {
            "total_batches": total_batches,
            "completed_batches": completed.count if completed else 0,
            "completion_rate": items[0].completion_rate,
            "total_discrepancy": str(total_discrepancy.quantize(Decimal("0.01"))),
        }

        return ReconciliationReportResponse(
            items=items,
            summary=summary,
            meta={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "generated_at": datetime.now().isoformat(),
            },
        )

    # ========== 财务摘要 ==========

    async def get_financial_summary(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        project_ids: Optional[List[int]] = None,
    ) -> FinancialSummaryResponse:
        """获取财务摘要"""

        # 默认日期范围：最近30天
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=30)

        # 查询账户财务数据
        # 注意：AdAccount 没有 balance 字段，使用 deposit 作为替代
        # 实际余额应通过 ledger entries 或 balance_snapshots 计算
        query = (
            self.db.query(
                AdAccount.id.label("account_id"),
                AdAccount.name.label("account_name"),  # 使用实际列名 name
                AdAccount.deposit.label("current_balance"),  # 使用 deposit 作为 balance 的替代
                Project.id.label("project_id"),
                Project.name.label("project_name"),
                Channel.id.label("channel_id"),
                Channel.name.label("channel_name"),
            )
            .select_from(AdAccount)
            .join(Project, AdAccount.project_id == Project.id)
            .join(Channel, AdAccount.channel_id == Channel.id)
        )

        if project_ids:
            query = query.filter(Project.id.in_(project_ids))

        accounts = query.all()

        items = []
        for account in accounts:
            # 查询期间的账本分录
            ledger_query = (
                self.db.query(
                    LedgerEntry.entry_type,
                    func.coalesce(func.sum(LedgerEntry.amount), 0).label("total"),
                )
                .filter(
                    LedgerEntry.ad_account_id
                    == account.id,  # 使用 account.id 而不是 account.account_id
                    func.date(LedgerEntry.entry_date) >= start_date,
                    func.date(LedgerEntry.entry_date) <= end_date,
                )
                .group_by(LedgerEntry.entry_type)
            )

            ledger_data = {
                row.entry_type: Decimal(str(row.total or 0))
                for row in ledger_query.all()
            }

            topup = ledger_data.get("TOPUP", Decimal("0.00"))
            spend = abs(ledger_data.get("COST", Decimal("0.00")))
            transfer_in = ledger_data.get("TRANSFER_IN", Decimal("0.00"))
            transfer_out = abs(ledger_data.get("TRANSFER_OUT", Decimal("0.00")))
            net_change = topup - spend + transfer_in - transfer_out

            items.append(
                FinancialSummaryItem(
                    account_id=account.account_id,
                    account_name=account.account_name,
                    project_id=account.project_id,
                    project_name=account.project_name,
                    channel_id=account.channel_id,
                    channel_name=account.channel_name,
                    current_balance=Decimal(str(account.current_balance or 0)),
                    total_topup=topup,
                    total_spend=spend,
                    total_transfer_in=transfer_in,
                    total_transfer_out=transfer_out,
                    net_change=net_change,
                )
            )

        # 汇总
        total_balance = sum(item.current_balance for item in items)
        total_topup = sum(item.total_topup for item in items)
        total_spend = sum(item.total_spend for item in items)

        # 确保所有汇总值是 Decimal 类型
        if not isinstance(total_balance, Decimal):
            total_balance = Decimal(str(total_balance or 0))
        if not isinstance(total_topup, Decimal):
            total_topup = Decimal(str(total_topup or 0))
        if not isinstance(total_spend, Decimal):
            total_spend = Decimal(str(total_spend or 0))

        summary = {
            "total_accounts": len(items),
            "total_balance": str(total_balance.quantize(Decimal("0.01"))),
            "total_topup": str(total_topup.quantize(Decimal("0.01"))),
            "total_spend": str(total_spend.quantize(Decimal("0.01"))),
        }

        return FinancialSummaryResponse(
            items=items,
            summary=summary,
            meta={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "generated_at": datetime.now().isoformat(),
            },
        )

    # ========== 仪表盘摘要 ==========

    async def get_dashboard_summary(self) -> DashboardSummary:
        """获取仪表盘摘要"""

        today = date.today()
        month_start = today.replace(day=1)

        # 今日数据 - 使用 AccountPerformance 替代 AdSpendDaily
        today_spend_query = (
            self.db.query(func.coalesce(func.sum(AccountPerformance.spend), 0))
            .filter(AccountPerformance.date == today)
            .scalar()
        )

        today_leads_query = (
            self.db.query(
                func.coalesce(
                    func.sum(AccountPerformance.conversions), 0
                )  # leads_count → conversions
            )
            .filter(AccountPerformance.date == today)
            .scalar()
        )

        today_topup_query = (
            self.db.query(func.coalesce(func.sum(LedgerEntry.amount), 0))
            .filter(
                LedgerEntry.entry_type == LedgerEntryType.TOPUP.value,  # 使用枚举值
                func.date(LedgerEntry.entry_date) == today,
            )
            .scalar()
        )

        # 本月数据 - 使用 AccountPerformance 替代 AdSpendDaily
        month_spend_query = (
            self.db.query(func.coalesce(func.sum(AccountPerformance.spend), 0))
            .filter(
                AccountPerformance.date >= month_start, AccountPerformance.date <= today
            )
            .scalar()
        )

        month_leads_query = (
            self.db.query(
                func.coalesce(
                    func.sum(AccountPerformance.conversions), 0
                )  # leads_count → conversions
            )
            .filter(
                AccountPerformance.date >= month_start, AccountPerformance.date <= today
            )
            .scalar()
        )

        month_topup_query = (
            self.db.query(func.coalesce(func.sum(LedgerEntry.amount), 0))
            .filter(
                LedgerEntry.entry_type == LedgerEntryType.TOPUP.value,  # 使用枚举值
                func.date(LedgerEntry.entry_date) >= month_start,
                func.date(LedgerEntry.entry_date) <= today,
            )
            .scalar()
        )

        # 账户统计
        total_accounts = self.db.query(func.count(AdAccount.id)).scalar() or 0
        active_accounts = (
            self.db.query(func.count(AdAccount.id))
            .filter(AdAccount.status == "active")
            .scalar()
            or 0
        )
        # 低余额账户统计 - 暂时设为0，因为余额需从账本计算
        # 注意: 按 LEDGER_SOT.md v1.1，余额应从 ledger_entries 计算，而非直接存储
        low_balance_accounts = 0  # TODO: 从 ledger_entries 计算账户余额

        # 项目统计
        total_projects = self.db.query(func.count(Project.id)).scalar() or 0
        active_projects = (
            self.db.query(func.count(Project.id))
            .filter(Project.status == "active")
            .scalar()
            or 0
        )

        # 待办事项
        pending_topups = (
            self.db.query(func.count(TopupRequest.id))
            .filter(
                TopupRequest.status
                == TopupStatus.PENDING_REVIEW.value  # 修复：PENDING_DATA_REVIEW → PENDING_REVIEW
            )
            .scalar()
            or 0
        )

        pending_reconciliations = (
            self.db.query(func.count(ReconciliationBatch.id))
            .filter(ReconciliationBatch.status == "pending_review")
            .scalar()
            or 0
        )

        pending_reports = (
            self.db.query(func.count(DailyReport.id))
            .filter(DailyReport.status == DailyReportStatus.RAW_SUBMITTED.value)
            .scalar()
            or 0
        )

        # 消耗趋势（最近7天） - 使用 AccountPerformance 替代 AdSpendDaily
        spend_trend = []
        for i in range(6, -1, -1):
            trend_date = today - timedelta(days=i)
            daily_spend = (
                self.db.query(func.coalesce(func.sum(AccountPerformance.spend), 0))
                .filter(AccountPerformance.date == trend_date)
                .scalar()
            )
            spend_trend.append(
                {"date": trend_date.isoformat(), "value": float(daily_spend or 0)}
            )

        # 线索趋势（最近7天） - 使用 AccountPerformance 替代 AdSpendDaily
        leads_trend = []
        for i in range(6, -1, -1):
            trend_date = today - timedelta(days=i)
            daily_leads = (
                self.db.query(
                    func.coalesce(
                        func.sum(AccountPerformance.conversions), 0
                    )  # leads_count → conversions
                )
                .filter(AccountPerformance.date == trend_date)
                .scalar()
            )
            leads_trend.append(
                {"date": trend_date.isoformat(), "value": int(daily_leads or 0)}
            )

        month_spend = Decimal(str(month_spend_query or 0))
        month_topup = Decimal(str(month_topup_query or 0))
        month_profit = month_topup - month_spend

        return DashboardSummary(
            today_spend=Decimal(str(today_spend_query or 0)),
            today_leads=int(today_leads_query or 0),
            today_topup=Decimal(str(today_topup_query or 0)),
            month_spend=month_spend,
            month_leads=int(month_leads_query or 0),
            month_topup=month_topup,
            month_profit=month_profit,
            total_accounts=total_accounts,
            active_accounts=active_accounts,
            low_balance_accounts=low_balance_accounts,
            total_projects=total_projects,
            active_projects=active_projects,
            pending_topups=pending_topups,
            pending_reconciliations=pending_reconciliations,
            pending_reports=pending_reports,
            spend_trend=spend_trend,
            leads_trend=leads_trend,
        )

    # ========== 趋势报表 ==========

    async def get_trend_report(
        self,
        metric: str,  # spend, leads, topup, profit
        period: str = "daily",  # daily, weekly, monthly
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> TrendReportResponse:
        """获取趋势报表"""

        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=30)

        data_points = []

        if metric == "spend":
            # 使用 AccountPerformance 替代 AdSpendDaily
            query = (
                self.db.query(
                    AccountPerformance.date,
                    func.coalesce(func.sum(AccountPerformance.spend), 0).label("value"),
                )
                .filter(
                    AccountPerformance.date >= start_date,
                    AccountPerformance.date <= end_date,
                )
                .group_by(AccountPerformance.date)
                .order_by(AccountPerformance.date)
            )

            for row in query.all():
                data_points.append(
                    TrendDataPoint(date=row.date, value=Decimal(str(row.value or 0)))
                )

        elif metric == "leads":
            # 使用 AccountPerformance 替代 AdSpendDaily
            query = (
                self.db.query(
                    AccountPerformance.date,
                    func.coalesce(func.sum(AccountPerformance.conversions), 0).label(
                        "value"
                    ),  # leads_count → conversions
                )
                .filter(
                    AccountPerformance.date >= start_date,
                    AccountPerformance.date <= end_date,
                )
                .group_by(AccountPerformance.date)
                .order_by(AccountPerformance.date)
            )

            for row in query.all():
                data_points.append(
                    TrendDataPoint(date=row.date, value=Decimal(str(row.value or 0)))
                )

        elif metric == "topup":
            query = (
                self.db.query(
                    func.date(LedgerEntry.entry_date).label("date"),
                    func.coalesce(func.sum(LedgerEntry.amount), 0).label("value"),
                )
                .filter(
                    LedgerEntry.entry_type == LedgerEntryType.TOPUP.value,  # 使用枚举值
                    func.date(LedgerEntry.entry_date) >= start_date,
                    func.date(LedgerEntry.entry_date) <= end_date,
                )
                .group_by(func.date(LedgerEntry.entry_date))
                .order_by(func.date(LedgerEntry.entry_date))
            )

            for row in query.all():
                data_points.append(
                    TrendDataPoint(date=row.date, value=Decimal(str(row.value or 0)))
                )

        # 计算汇总
        total_value = sum(dp.value for dp in data_points)
        # 确保 total_value 是 Decimal 类型
        if not isinstance(total_value, Decimal):
            total_value = Decimal(str(total_value or 0))
        avg_value = total_value / len(data_points) if data_points else Decimal("0")
        max_value = max((dp.value for dp in data_points), default=Decimal("0"))
        min_value = min((dp.value for dp in data_points), default=Decimal("0"))

        return TrendReportResponse(
            period=f"{start_date.isoformat()} ~ {end_date.isoformat()}",
            data_points=data_points,
            summary={
                "total": str(total_value.quantize(Decimal("0.01"))),
                "average": str(avg_value.quantize(Decimal("0.01"))),
                "max": str(max_value.quantize(Decimal("0.01"))),
                "min": str(min_value.quantize(Decimal("0.01"))),
                "count": len(data_points),
            },
        )


def get_reports_service(db: Session) -> ReportsService:
    """获取报表服务实例"""
    return ReportsService(db)
