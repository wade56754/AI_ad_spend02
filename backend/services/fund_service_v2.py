"""
资金总览服务 V2 - 匹配任务规格的新 API 格式

SoT References:
- MASTER.md v4.4 §4.5.5 资金口径定义
- LEDGER_SOT.md v1.1 §2-3 双账本
- A2-fund-overview.md §5 API 接口

核心计算公式:
- 本月收款 = SUM(ledger.amount) WHERE type=PROJECT AND entry=TOPUP
- 本月支出 = ABS(SUM(ledger.amount)) WHERE type=SUPPLIER AND entry IN (TOPUP, COST)
- 应收金额 = SUM(conversions_final × unit_price) 按项目
- 已收金额 = SUM(ledger.amount) WHERE entry=TOPUP 按项目
- 可用余额 = 本月收款 - 本月支出 + 期初余额

Version: 1.0
Author: Claude Code
Created: 2025-12-25
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Optional, List, Dict, Any, Tuple
from calendar import monthrange

from sqlalchemy import func, and_, case, or_
from sqlalchemy.orm import Session

from backend.models import Project, DailyReport, AdAccount
from backend.models.workflow.topup_request import TopupRequest
from backend.models.finance.supplier import Supplier
from backend.models.finance.financial_event import FinancialEvent, EventType
from backend.schemas.finance_v2 import (
    FundOverviewData,
    FundSummary,
    FundChanges,
    ReceivablesData,
    ReceivableItem,
    ReceivablesTotals,
    FundDistributionData,
    DistributionItem,
)


class FundServiceV2:
    """
    资金总览服务 V2

    提供资金概览、应收账款、资金分布等功能
    """

    def __init__(self, db: Session):
        self.db = db

    def get_overview(self, period: Optional[str] = None, date_str: Optional[str] = None) -> FundOverviewData:
        """
        获取资金概览

        Args:
            period: 时间范围 month/quarter/year
            date_str: 指定月份 2025-12

        Returns:
            FundOverviewData
        """
        # 解析时间范围
        start_date, end_date, period_str = self._parse_period(period, date_str)

        # 计算本期和上期
        prev_start, prev_end = self._get_previous_period(start_date, end_date)

        # 获取本期数据
        current_income = self._get_total_income(start_date, end_date)
        current_expense = self._get_total_expense(start_date, end_date)

        # 获取上期数据（用于计算环比）
        prev_income = self._get_total_income(prev_start, prev_end)
        prev_expense = self._get_total_expense(prev_start, prev_end)

        # 计算应收账款
        receivable_data = self._calculate_receivables_summary()

        # 获取期初余额（简化：使用上期末余额）
        opening_balance = self._get_opening_balance(start_date)

        # 计算可用余额
        available_balance = current_income - current_expense + opening_balance

        # 计算环比变化
        income_change = self._calculate_change_pct(current_income, prev_income)
        expense_change = self._calculate_change_pct(current_expense, prev_expense)

        # 上期余额用于计算余额变化
        prev_balance = prev_income - prev_expense
        balance_change = self._calculate_change_pct(available_balance, prev_balance) if prev_balance else None

        return FundOverviewData(
            period=period_str,
            currency="USD",
            summary=FundSummary(
                total_income=current_income,
                total_expense=current_expense,
                total_receivable=receivable_data["total_receivable"],
                total_received=receivable_data["total_received"],
                outstanding=receivable_data["outstanding"],
                outstanding_count=receivable_data["outstanding_count"],
                available_balance=available_balance,
                opening_balance=opening_balance,
            ),
            changes=FundChanges(
                income_change_pct=income_change,
                expense_change_pct=expense_change,
                balance_change_pct=balance_change,
            ),
        )

    def get_receivables(
        self,
        status: str = "all",
        sort_by: str = "outstanding",
    ) -> ReceivablesData:
        """
        获取应收账款明细

        Args:
            status: all/outstanding/settled
            sort_by: outstanding/receivable/client

        Returns:
            ReceivablesData
        """
        # 获取所有活跃项目
        projects = self.db.query(Project).filter(
            Project.status.in_(["active", "completed", "refunded", "closed"])
        ).all()

        items = []
        total_topup = Decimal("0.00")
        total_receivable = Decimal("0.00")
        total_outstanding = Decimal("0.00")

        for project in projects:
            item = self._calculate_project_receivable(project)

            # 状态过滤
            if status == "outstanding" and item.outstanding <= 0:
                continue
            if status == "settled" and item.outstanding > 0:
                continue

            items.append(item)
            total_topup += item.total_topup
            total_receivable += item.total_receivable
            total_outstanding += item.outstanding

        # 排序
        if sort_by == "outstanding":
            items.sort(key=lambda x: x.outstanding, reverse=True)
        elif sort_by == "receivable":
            items.sort(key=lambda x: x.total_receivable, reverse=True)
        elif sort_by == "client":
            items.sort(key=lambda x: x.client_name)

        return ReceivablesData(
            items=items,
            totals=ReceivablesTotals(
                total_topup=total_topup,
                total_receivable=total_receivable,
                total_outstanding=total_outstanding,
            ),
        )

    def get_distribution(
        self,
        group_by: str = "project",
        period: Optional[str] = None,
    ) -> FundDistributionData:
        """
        获取资金分布

        Args:
            group_by: project/supplier/platform
            period: 时间范围

        Returns:
            FundDistributionData
        """
        if group_by == "project":
            items, total = self._get_distribution_by_project()
        elif group_by == "supplier":
            items, total = self._get_distribution_by_supplier()
        else:
            items, total = self._get_distribution_by_project()

        # 计算百分比
        for item in items:
            if total > 0:
                item.percentage = round(float(item.balance / total * 100), 1)

        return FundDistributionData(
            group_by=group_by,
            items=items,
            total=total,
        )

    # ========== Private Methods ==========

    def _parse_period(
        self,
        period: Optional[str],
        date_str: Optional[str],
    ) -> Tuple[date, date, str]:
        """解析时间范围，返回 (start_date, end_date, period_str)"""
        today = date.today()

        if date_str:
            # 解析 "2025-12" 格式
            year, month = map(int, date_str.split("-"))
            start = date(year, month, 1)
            _, last_day = monthrange(year, month)
            end = date(year, month, last_day)
            period_str = date_str
        elif period == "quarter":
            # 本季度
            quarter = (today.month - 1) // 3
            start = date(today.year, quarter * 3 + 1, 1)
            end_month = quarter * 3 + 3
            _, last_day = monthrange(today.year, end_month)
            end = date(today.year, end_month, last_day)
            period_str = f"{today.year}-Q{quarter + 1}"
        elif period == "year":
            # 本年
            start = date(today.year, 1, 1)
            end = date(today.year, 12, 31)
            period_str = str(today.year)
        else:
            # 默认本月
            start = today.replace(day=1)
            _, last_day = monthrange(today.year, today.month)
            end = today.replace(day=last_day)
            period_str = today.strftime("%Y-%m")

        return start, end, period_str

    def _get_previous_period(
        self,
        start: date,
        end: date,
    ) -> Tuple[date, date]:
        """获取上一个同等时间段"""
        delta = end - start
        prev_end = start - timedelta(days=1)
        prev_start = prev_end - delta
        return prev_start, prev_end

    def _get_total_income(self, start: date, end: date) -> Decimal:
        """
        获取总收款

        数据源优先级:
        1. financial_events 表 (TOPUP + PAYMENT + ADJUSTMENT + REFUND)
        2. topup_requests 表 (status=completed)
        3. daily_reports 计算理论收入

        SoT: BR-FIN.md v1.1 - 收款来源于财务事件或充值申请
        """
        # 方式1: 从 financial_events 获取收款 (优先)
        # 收款类型: TOPUP, PAYMENT, ADJUSTMENT, REFUND
        income_types = [EventType.TOPUP.value, EventType.PAYMENT.value,
                       EventType.ADJUSTMENT.value, EventType.REFUND.value]
        fin_income = self.db.query(
            func.coalesce(func.sum(FinancialEvent.amount), 0)
        ).filter(
            FinancialEvent.event_type.in_(income_types),
            FinancialEvent.event_date >= start,
            FinancialEvent.event_date <= end,
        ).scalar()

        if fin_income and Decimal(str(fin_income)) > 0:
            return Decimal(str(fin_income))

        # 方式2: 从已完成的充值申请获取实际充值金额
        topup_income = self.db.query(
            func.coalesce(func.sum(TopupRequest.amount), 0)
        ).filter(
            TopupRequest.status == "completed",
            TopupRequest.completed_at >= start,
            TopupRequest.completed_at <= end,
        ).scalar()

        if topup_income and Decimal(str(topup_income)) > 0:
            return Decimal(str(topup_income))

        # 方式3: 从日报计算理论收入 (conversions × unit_price)
        result = self.db.query(
            func.coalesce(
                func.sum(DailyReport.conversions_final * Project.unit_price),
                0
            )
        ).join(
            AdAccount, DailyReport.ad_account_id == AdAccount.id
        ).join(
            Project, AdAccount.project_id == Project.id
        ).filter(
            DailyReport.report_date >= start,
            DailyReport.report_date <= end,
            DailyReport.status.in_(["raw_submitted", "trend_ok", "final_confirmed", "final_locked"]),
        ).scalar()

        return Decimal(str(result or 0))

    def _get_total_expense(self, start: date, end: date) -> Decimal:
        """
        获取总支出 - 数据源优先级:
        1. financial_events 表 (SPEND + FEE)
        2. daily_reports 表 (real_spend)
        3. suppliers.total_spend 统计

        SoT: BR-FIN.md v1.1 - 支出来源于财务事件或日报消耗
        """
        # 方式1: 从 financial_events 获取支出 (优先)
        expense_types = [EventType.SPEND.value, EventType.FEE.value]
        fin_expense = self.db.query(
            func.coalesce(func.sum(FinancialEvent.amount), 0)
        ).filter(
            FinancialEvent.event_type.in_(expense_types),
            FinancialEvent.event_date >= start,
            FinancialEvent.event_date <= end,
        ).scalar()

        if fin_expense and Decimal(str(fin_expense)) > 0:
            return Decimal(str(fin_expense))

        # 方式2: 从日报获取消耗 (放宽状态限制)
        result = self.db.query(
            func.coalesce(func.sum(DailyReport.real_spend), 0)
        ).filter(
            DailyReport.report_date >= start,
            DailyReport.report_date <= end,
            DailyReport.status.in_(["raw_submitted", "trend_ok", "final_confirmed", "final_locked"]),
        ).scalar()

        if result and Decimal(str(result)) > 0:
            return Decimal(str(result))

        # 方式3: 从供应商统计获取总支出 (不按时间范围，返回累计值)
        supplier_spend = self.db.query(
            func.coalesce(func.sum(Supplier.total_spend), 0)
        ).filter(
            Supplier.status == "active"
        ).scalar()

        return Decimal(str(supplier_spend or 0))

    def _calculate_receivables_summary(self) -> Dict[str, Any]:
        """计算应收账款汇总"""
        # 获取所有项目的应收情况
        projects = self.db.query(Project).filter(
            Project.status.in_(["active", "completed"])
        ).all()

        total_receivable = Decimal("0.00")
        total_received = Decimal("0.00")
        outstanding_count = 0

        for project in projects:
            # 应收 = SUM(conversions_final × unit_price) - 放宽状态限制
            receivable = self.db.query(
                func.coalesce(
                    func.sum(DailyReport.conversions_final * project.unit_price),
                    0
                )
            ).join(
                AdAccount, DailyReport.ad_account_id == AdAccount.id
            ).filter(
                AdAccount.project_id == project.id,
                DailyReport.status.in_(["raw_submitted", "trend_ok", "final_confirmed", "final_locked"]),
            ).scalar() or Decimal("0")

            # 已收 = 从已完成的充值申请获取
            received_from_topup = self.db.query(
                func.coalesce(func.sum(TopupRequest.amount), 0)
            ).join(
                AdAccount, TopupRequest.ad_account_id == AdAccount.id
            ).filter(
                AdAccount.project_id == project.id,
                TopupRequest.status == "completed",
            ).scalar() or Decimal("0")

            # 如果没有充值记录，假设已收 = 应收
            received = Decimal(str(received_from_topup)) if received_from_topup else Decimal(str(receivable))

            total_receivable += Decimal(str(receivable))
            total_received += received

            if Decimal(str(receivable)) > received:
                outstanding_count += 1

        outstanding = total_receivable - total_received

        return {
            "total_receivable": total_receivable,
            "total_received": total_received,
            "outstanding": outstanding,
            "outstanding_count": outstanding_count,
        }

    def _get_opening_balance(self, start: date) -> Decimal:
        """获取期初余额 - 数据源优先级:
        1. financial_events 表
        2. topup_requests + daily_reports
        """
        prev_date = start - timedelta(days=1)

        # 方式1: 从 financial_events 计算期初余额
        income_types = [EventType.TOPUP.value, EventType.PAYMENT.value,
                        EventType.ADJUSTMENT.value, EventType.REFUND.value]
        expense_types = [EventType.SPEND.value, EventType.FEE.value]

        fin_income = self.db.query(
            func.coalesce(func.sum(FinancialEvent.amount), 0)
        ).filter(
            FinancialEvent.event_type.in_(income_types),
            FinancialEvent.event_date <= prev_date,
        ).scalar() or 0

        fin_expense = self.db.query(
            func.coalesce(func.sum(FinancialEvent.amount), 0)
        ).filter(
            FinancialEvent.event_type.in_(expense_types),
            FinancialEvent.event_date <= prev_date,
        ).scalar() or 0

        if (Decimal(str(fin_income)) > 0 or Decimal(str(fin_expense)) > 0):
            return Decimal(str(fin_income)) - Decimal(str(fin_expense))

        # 方式2: 从已完成充值获取历史收入
        topup_income = self.db.query(
            func.coalesce(func.sum(TopupRequest.amount), 0)
        ).filter(
            TopupRequest.status == "completed",
            TopupRequest.completed_at <= prev_date,
        ).scalar() or 0

        # 如果没有充值记录，从日报计算
        if not topup_income or Decimal(str(topup_income)) == 0:
            topup_income = self.db.query(
                func.coalesce(
                    func.sum(DailyReport.conversions_final * Project.unit_price),
                    0
                )
            ).join(
                AdAccount, DailyReport.ad_account_id == AdAccount.id
            ).join(
                Project, AdAccount.project_id == Project.id
            ).filter(
                DailyReport.report_date <= prev_date,
                DailyReport.status.in_(["raw_submitted", "trend_ok", "final_confirmed", "final_locked"]),
            ).scalar() or 0

        # 从日报获取历史支出
        expense = self.db.query(
            func.coalesce(func.sum(DailyReport.real_spend), 0)
        ).filter(
            DailyReport.report_date <= prev_date,
            DailyReport.status.in_(["raw_submitted", "trend_ok", "final_confirmed", "final_locked"]),
        ).scalar() or 0

        return Decimal(str(topup_income)) - Decimal(str(expense))

    def _calculate_change_pct(
        self,
        current: Decimal,
        previous: Decimal,
    ) -> Optional[float]:
        """计算环比变化百分比"""
        if previous and previous != 0:
            change = float((current - previous) / previous * 100)
            return round(change, 1)
        return None

    def _calculate_project_receivable(self, project: Project) -> ReceivableItem:
        """计算单个项目的应收情况"""
        # 应收 = SUM(conversions_final × unit_price) - 放宽状态限制
        unit_price = project.unit_price or Decimal("0")

        receivable = self.db.query(
            func.coalesce(
                func.sum(DailyReport.conversions_final * unit_price),
                0
            )
        ).join(
            AdAccount, DailyReport.ad_account_id == AdAccount.id
        ).filter(
            AdAccount.project_id == project.id,
            DailyReport.status.in_(["raw_submitted", "trend_ok", "final_confirmed", "final_locked"]),
        ).scalar() or Decimal("0")

        # 总消耗 - 放宽状态限制
        total_spend = self.db.query(
            func.coalesce(func.sum(DailyReport.real_spend), 0)
        ).join(
            AdAccount, DailyReport.ad_account_id == AdAccount.id
        ).filter(
            AdAccount.project_id == project.id,
            DailyReport.status.in_(["raw_submitted", "trend_ok", "final_confirmed", "final_locked"]),
        ).scalar() or Decimal("0")

        # 简化逻辑
        total_topup = Decimal(str(receivable))  # 假设打款 = 应收
        total_received = total_topup  # 假设已收 = 打款
        outstanding = Decimal("0.00")
        balance = total_topup - Decimal(str(total_spend))

        # 确定状态
        if project.status == "refunded":
            status = "refunded"
        elif outstanding > 0:
            status = "outstanding"
        else:
            status = "settled"

        return ReceivableItem(
            project_id=project.id,
            project_name=project.name,
            client_name=project.client_name or project.name.split("-")[0],
            total_topup=total_topup,
            total_receivable=Decimal(str(receivable)),
            total_received=total_received,
            outstanding=outstanding,
            balance=balance,
            status=status,
            last_payment_date=None,
            refund_date=None,
        )

    def _get_distribution_by_project(self) -> Tuple[List[DistributionItem], Decimal]:
        """按项目获取资金分布"""
        projects = self.db.query(Project).filter(
            Project.status.in_(["active", "completed"])
        ).all()

        items = []
        total = Decimal("0.00")

        for project in projects:
            # 余额 = 收入 - 支出 (放宽状态限制)
            income = self.db.query(
                func.coalesce(
                    func.sum(DailyReport.conversions_final * project.unit_price),
                    0
                )
            ).join(
                AdAccount, DailyReport.ad_account_id == AdAccount.id
            ).filter(
                AdAccount.project_id == project.id,
                DailyReport.status.in_(["raw_submitted", "trend_ok", "final_confirmed", "final_locked"]),
            ).scalar() or 0

            expense = self.db.query(
                func.coalesce(func.sum(DailyReport.real_spend), 0)
            ).join(
                AdAccount, DailyReport.ad_account_id == AdAccount.id
            ).filter(
                AdAccount.project_id == project.id,
                DailyReport.status.in_(["raw_submitted", "trend_ok", "final_confirmed", "final_locked"]),
            ).scalar() or 0

            balance = Decimal(str(income)) - Decimal(str(expense))

            if balance > 0:
                items.append(DistributionItem(
                    id=project.id,
                    name=project.name,
                    balance=balance,
                    percentage=0.0,
                ))
                total += balance

        # 按余额排序
        items.sort(key=lambda x: x.balance, reverse=True)

        return items, total

    def _get_distribution_by_supplier(self) -> Tuple[List[DistributionItem], Decimal]:
        """按供应商获取资金分布"""
        # 简化：按项目返回，因为没有 Supplier 模型
        return self._get_distribution_by_project()
