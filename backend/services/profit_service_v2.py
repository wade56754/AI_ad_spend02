"""
项目盈亏服务 V2 - 匹配任务规格的新 API 格式

SoT References:
- MASTER.md v4.4 §6.5 页面 3 项目盈亏字段集
- BUSINESS_RULES.md v3.2: 利润计算公式
- CORE_MODULES.md v1.0 §4.5 阶梯价格规则

核心计算公式:
- revenue = conversions_final × unit_price
- cost = real_spend + fee (fee = spend × fee_rate)
- profit = revenue - cost
- profit_margin = profit / revenue × 100

利润状态规则:
- 🟢 healthy: profit_rate >= 15%
- 🟡 warning: 5% <= profit_rate < 15%
- 🔴 danger: profit_rate < 5%
- ⚫ inactive: refunded/closed

Version: 1.1
Author: Claude Code
Created: 2025-12-25
Updated: 2026-01-12 - Fixed Supplier.name query in get_supplier_costs
"""

from datetime import date, timedelta
from decimal import Decimal
from typing import Optional, List, Dict, Any, Tuple, Literal
from calendar import monthrange

from sqlalchemy import func, and_
from sqlalchemy.orm import Session

from backend.models import Project, DailyReport, AdAccount
from backend.models.finance.supplier import Supplier
from backend.schemas.finance_v2 import (
    ProfitOverviewData,
    ProfitSummary,
    ProfitChanges,
    ProfitBenchmarks,
    ProjectProfitsData,
    ProjectProfitItem,
    ProjectProfitTotals,
    PriceRules,
    PriceTier,
    SupplierCostsData,
    SupplierCostItem,
    SupplierCostSummary,
    ProfitTrendData,
    TrendSeriesItem,
    ProfitStatus,
)


class ProfitServiceV2:
    """
    项目盈亏服务 V2

    提供盈亏概览、项目利润明细、渠道成本分析、利润趋势等功能
    """

    # 行业基准值
    INDUSTRY_AVG_PROFIT_RATE = 0.15
    COMPANY_TARGET_PROFIT_RATE = 0.20

    def __init__(self, db: Session):
        self.db = db

    def get_overview(self, period: Optional[str] = None) -> ProfitOverviewData:
        """
        获取盈亏概览

        Args:
            period: 指定月份 2025-12

        Returns:
            ProfitOverviewData
        """
        # 解析时间范围
        start_date, end_date, period_str = self._parse_period(period)

        # 计算本期和上期
        prev_start, prev_end = self._get_previous_period(start_date, end_date)

        # 获取本期汇总
        current = self._calculate_period_summary(start_date, end_date)

        # 获取上期汇总（用于计算环比）
        previous = self._calculate_period_summary(prev_start, prev_end)

        # 计算环比变化
        revenue_change = self._calculate_change_pct(
            current["revenue"], previous["revenue"]
        )
        profit_change = self._calculate_change_pct(
            current["profit"], previous["profit"]
        )

        return ProfitOverviewData(
            period=period_str,
            currency="USD",
            summary=ProfitSummary(
                total_revenue=current["revenue"],
                total_cost=current["cost"],
                total_profit=current["profit"],
                total_conversions=current["conversions"],
                avg_profit_rate=current["profit_rate"],
                total_fee=current["fee"],
            ),
            changes=ProfitChanges(
                revenue_change_pct=revenue_change,
                profit_change_pct=profit_change,
            ),
            benchmarks=ProfitBenchmarks(
                industry_avg_profit_rate=self.INDUSTRY_AVG_PROFIT_RATE,
                company_target_profit_rate=self.COMPANY_TARGET_PROFIT_RATE,
            ),
        )

    def get_project_profits(
        self,
        period: Optional[str] = None,
        sort_by: str = "profit",
        status: str = "all",
    ) -> ProjectProfitsData:
        """
        获取项目利润明细

        Args:
            period: 时间范围
            sort_by: profit/profit_rate/revenue
            status: all/active/inactive

        Returns:
            ProjectProfitsData

        优化说明 (Phase 3 N+1 修复):
        - 使用批量查询预取所有项目的日报聚合数据
        - 避免在循环中对每个项目单独查询
        """
        start_date, end_date, _ = self._parse_period(period)

        # 获取项目列表
        query = self.db.query(Project)

        if status == "active":
            query = query.filter(Project.status.in_(["active", "completed"]))
        elif status == "inactive":
            query = query.filter(Project.status.in_(["refunded", "closed", "cancelled"]))

        projects = query.all()
        project_ids = [p.id for p in projects]

        # ===== N+1 优化: 批量预取所有项目的日报聚合数据 =====
        # DailyReport 通过 AdAccount 关联到 Project
        daily_report_aggs = {}
        if project_ids:
            agg_results = self.db.query(
                AdAccount.project_id,
                func.coalesce(func.sum(DailyReport.conversions_final), 0).label("conversions"),
                func.coalesce(func.sum(DailyReport.real_spend), 0).label("spend"),
            ).join(
                AdAccount, DailyReport.ad_account_id == AdAccount.id
            ).filter(
                AdAccount.project_id.in_(project_ids),
                DailyReport.report_date >= start_date,
                DailyReport.report_date <= end_date,
                DailyReport.status == "final_locked",
            ).group_by(AdAccount.project_id).all()

            for row in agg_results:
                daily_report_aggs[row.project_id] = {
                    "conversions": int(row.conversions or 0),
                    "spend": Decimal(str(row.spend or 0)),
                }

        items = []
        total_conversions = 0
        total_revenue = Decimal("0.00")
        total_cost = Decimal("0.00")
        total_profit = Decimal("0.00")

        for project in projects:
            # 使用预取的数据代替单独查询
            agg_data = daily_report_aggs.get(project.id, {"conversions": 0, "spend": Decimal("0")})
            item = self._calculate_project_profit_from_agg(project, agg_data)
            items.append(item)

            total_conversions += item.conversions or 0
            total_revenue += item.revenue
            total_cost += item.cost
            total_profit += item.profit

        # 计算平均利润率
        avg_profit_rate = float(total_profit / total_revenue) if total_revenue > 0 else 0.0

        # 排序
        sort_key = {
            "profit": lambda x: x.profit,
            "profit_rate": lambda x: x.profit_rate,
            "revenue": lambda x: x.revenue,
        }.get(sort_by, lambda x: x.profit)

        items.sort(key=sort_key, reverse=True)

        return ProjectProfitsData(
            items=items,
            totals=ProjectProfitTotals(
                total_conversions=total_conversions,
                total_revenue=total_revenue,
                total_cost=total_cost,
                total_profit=total_profit,
                avg_profit_rate=avg_profit_rate,
            ),
        )

    def get_supplier_costs(self, period: Optional[str] = None) -> SupplierCostsData:  # v1.2 - Supplier.name JOIN
        """
        获取渠道成本分析 (Updated 2026-01-12)

        Args:
            period: 时间范围

        Returns:
            SupplierCostsData
        """
        start_date, end_date, _ = self._parse_period(period)

        # 按渠道/供应商聚合
        # 通过 AdAccount.supplier_id 关联 Supplier 表获取供应商名称和平台
        # 注意: platform 在 Supplier 表上，不在 AdAccount 表上
        results = self.db.query(
            AdAccount.supplier_id,
            Supplier.name.label("supplier_name"),
            Supplier.platform.label("platform"),  # 从 Supplier 获取 platform
            func.sum(DailyReport.real_spend).label("total_spend"),
            func.count(func.distinct(AdAccount.id)).label("account_count"),
        ).join(
            DailyReport, DailyReport.ad_account_id == AdAccount.id
        ).outerjoin(
            Supplier, AdAccount.supplier_id == Supplier.id
        ).filter(
            DailyReport.report_date >= start_date,
            DailyReport.report_date <= end_date,
            DailyReport.status == "final_locked",
        ).group_by(
            AdAccount.supplier_id,
            Supplier.name,
            Supplier.platform,  # 从 Supplier 获取 platform
        ).all()

        items = []
        total_spend = Decimal("0.00")
        total_fee = Decimal("0.00")
        weighted_fee_rate = Decimal("0.00")

        for r in results:
            spend = Decimal(str(r.total_spend or 0))
            # 假设费率 8%（实际应从 supplier 或 ad_account 获取）
            fee_rate = 0.08
            fee = spend * Decimal(str(fee_rate))
            cost = spend + fee

            items.append(SupplierCostItem(
                supplier_id=str(r.supplier_id) if r.supplier_id else "unknown",
                supplier_name=r.supplier_name or "未知渠道",
                platform=r.platform,
                fee_rate=fee_rate,
                total_spend=spend,
                total_fee=fee,
                total_cost=cost,
                account_count=r.account_count or 0,
            ))

            total_spend += spend
            total_fee += fee
            weighted_fee_rate += spend * Decimal(str(fee_rate))

        # 计算平均费率
        avg_fee_rate = float(weighted_fee_rate / total_spend) if total_spend > 0 else 0.0

        # 按消耗排序
        items.sort(key=lambda x: x.total_spend, reverse=True)

        return SupplierCostsData(
            items=items,
            summary=SupplierCostSummary(
                avg_fee_rate=avg_fee_rate,
                total_spend=total_spend,
                total_fee=total_fee,
            ),
        )

    def get_trend(
        self,
        granularity: str = "week",
        period: Optional[str] = None,
    ) -> ProfitTrendData:
        """
        获取利润趋势

        Args:
            granularity: day/week/month
            period: 时间范围

        Returns:
            ProfitTrendData
        """
        start_date, end_date, _ = self._parse_period(period)

        # 根据颗粒度生成时间段
        periods = self._generate_periods(start_date, end_date, granularity)

        series = []
        for period_start, period_end, period_label in periods:
            summary = self._calculate_period_summary(period_start, period_end)

            series.append(TrendSeriesItem(
                period=period_label,
                revenue=summary["revenue"],
                cost=summary["cost"],
                profit=summary["profit"],
            ))

        return ProfitTrendData(
            granularity=granularity,
            series=series,
        )

    # ========== Private Methods ==========

    def _parse_period(self, period: Optional[str]) -> Tuple[date, date, str]:
        """解析时间范围"""
        today = date.today()

        if period:
            # 解析 "2025-12" 格式
            year, month = map(int, period.split("-"))
            start = date(year, month, 1)
            _, last_day = monthrange(year, month)
            end = date(year, month, last_day)
            period_str = period
        else:
            # 默认本月
            start = today.replace(day=1)
            _, last_day = monthrange(today.year, today.month)
            end = today.replace(day=last_day)
            period_str = today.strftime("%Y-%m")

        return start, end, period_str

    def _get_previous_period(self, start: date, end: date) -> Tuple[date, date]:
        """获取上一个同等时间段"""
        delta = end - start
        prev_end = start - timedelta(days=1)
        prev_start = prev_end - delta
        return prev_start, prev_end

    def _calculate_period_summary(
        self,
        start: date,
        end: date,
    ) -> Dict[str, Any]:
        """计算时间段内的汇总数据"""
        # 聚合日报数据
        result = self.db.query(
            func.coalesce(func.sum(DailyReport.conversions_final), 0).label("conversions"),
            func.coalesce(func.sum(DailyReport.real_spend), 0).label("spend"),
        ).filter(
            DailyReport.report_date >= start,
            DailyReport.report_date <= end,
            DailyReport.status == "final_locked",
        ).first()

        conversions = int(result.conversions or 0)
        spend = Decimal(str(result.spend or 0))

        # 计算收入：需要按项目的 unit_price 计算
        # DailyReport -> AdAccount -> Project
        revenue_result = self.db.query(
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
            DailyReport.status == "final_locked",
        ).scalar()

        revenue = Decimal(str(revenue_result or 0))

        # 费用（假设平均费率 8%）
        fee = spend * Decimal("0.08")

        # 成本 = 消耗 + 费用
        cost = spend + fee

        # 利润 = 收入 - 成本
        profit = revenue - cost

        # 利润率
        profit_rate = float(profit / revenue) if revenue > 0 else 0.0

        return {
            "conversions": conversions,
            "revenue": revenue,
            "spend": spend,
            "fee": fee,
            "cost": cost,
            "profit": profit,
            "profit_rate": profit_rate,
        }

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

    def _calculate_project_profit(
        self,
        project: Project,
        start: date,
        end: date,
    ) -> ProjectProfitItem:
        """计算单个项目的利润"""
        unit_price = project.unit_price or Decimal("0")

        # 聚合日报数据 - DailyReport 通过 AdAccount 关联到 Project
        result = self.db.query(
            func.coalesce(func.sum(DailyReport.conversions_final), 0).label("conversions"),
            func.coalesce(func.sum(DailyReport.real_spend), 0).label("spend"),
        ).join(
            AdAccount, DailyReport.ad_account_id == AdAccount.id
        ).filter(
            AdAccount.project_id == project.id,
            DailyReport.report_date >= start,
            DailyReport.report_date <= end,
            DailyReport.status == "final_locked",
        ).first()

        conversions = int(result.conversions or 0)
        spend = Decimal(str(result.spend or 0))

        # 收入计算（支持阶梯定价）
        revenue = self._calculate_revenue(project, conversions)

        # 平均单价
        avg_unit_price = revenue / conversions if conversions > 0 else unit_price

        # 费用（假设 8%）
        fee_rate = 0.08
        fee = spend * Decimal(str(fee_rate))

        # 成本
        cost = spend + fee

        # 利润
        profit = revenue - cost

        # 利润率
        profit_rate = float(profit / revenue) if revenue > 0 else 0.0

        # 利润状态
        profit_status = self._get_profit_status(profit_rate, project.status)

        # 价格规则
        price_rules = self._get_price_rules(project)

        return ProjectProfitItem(
            project_id=project.id,
            project_name=project.name,
            status=project.status or "active",
            profit_status=profit_status,
            conversions=conversions if conversions > 0 else None,
            revenue=revenue,
            avg_unit_price=avg_unit_price,
            cost=cost,
            fee_rate=fee_rate,
            profit=profit,
            profit_rate=profit_rate,
            price_rules=price_rules,
        )

    def _calculate_project_profit_from_agg(
        self,
        project: Project,
        agg_data: dict,
    ) -> ProjectProfitItem:
        """
        使用预取的聚合数据计算单个项目的利润

        Phase 3 N+1 优化: 避免在循环中对每个项目单独查询

        Args:
            project: 项目对象
            agg_data: 预取的聚合数据 {"conversions": int, "spend": Decimal}

        Returns:
            ProjectProfitItem
        """
        unit_price = project.unit_price or Decimal("0")

        conversions = agg_data.get("conversions", 0)
        spend = agg_data.get("spend", Decimal("0"))

        # 收入计算（支持阶梯定价）
        revenue = self._calculate_revenue(project, conversions)

        # 平均单价
        avg_unit_price = revenue / conversions if conversions > 0 else unit_price

        # 费用（假设 8%）
        fee_rate = 0.08
        fee = spend * Decimal(str(fee_rate))

        # 成本
        cost = spend + fee

        # 利润
        profit = revenue - cost

        # 利润率
        profit_rate = float(profit / revenue) if revenue > 0 else 0.0

        # 利润状态
        profit_status = self._get_profit_status(profit_rate, project.status)

        # 价格规则
        price_rules = self._get_price_rules(project)

        return ProjectProfitItem(
            project_id=project.id,
            project_name=project.name,
            status=project.status or "active",
            profit_status=profit_status,
            conversions=conversions if conversions > 0 else None,
            revenue=revenue,
            avg_unit_price=avg_unit_price,
            cost=cost,
            fee_rate=fee_rate,
            profit=profit,
            profit_rate=profit_rate,
            price_rules=price_rules,
        )

    def _calculate_revenue(self, project: Project, conversions: int) -> Decimal:
        """
        计算收入（支持阶梯定价）

        SoT: CORE_MODULES.md §4.5 阶梯价格规则
        """
        unit_price = project.unit_price or Decimal("0")
        price_rules = project.price_rules

        if not price_rules or not isinstance(price_rules, dict):
            # 固定单价
            return unit_price * conversions

        pricing_type = price_rules.get("type", "fixed")

        if pricing_type == "tiered" and "tiers" in price_rules:
            # 阶梯定价
            tiers = price_rules["tiers"]
            remaining = conversions
            total_revenue = Decimal("0")

            for tier in sorted(tiers, key=lambda x: x.get("min", 0)):
                tier_min = tier.get("min", 0)
                tier_max = tier.get("max")
                tier_price = Decimal(str(tier.get("price", 0)))

                if remaining <= 0:
                    break

                if tier_max is None:
                    # 无上限
                    tier_count = remaining
                else:
                    tier_count = min(remaining, tier_max - tier_min + 1)

                total_revenue += tier_price * tier_count
                remaining -= tier_count

            return total_revenue

        elif pricing_type == "spend_ratio":
            # 按消耗比例
            ratio = Decimal(str(price_rules.get("ratio", 1.0)))
            # 需要额外查询消耗，这里简化返回基础收入
            return unit_price * conversions

        else:
            # 固定单价
            return unit_price * conversions

    def _get_profit_status(self, profit_rate: float, status: str) -> ProfitStatus:
        """
        获取利润状态

        🟢 healthy: profit_rate >= 15%
        🟡 warning: 5% <= profit_rate < 15%
        🔴 danger: profit_rate < 5%
        ⚫ inactive: refunded/closed
        """
        if status in ("refunded", "closed", "cancelled"):
            return "inactive"
        if profit_rate >= 0.15:
            return "healthy"
        if profit_rate >= 0.05:
            return "warning"
        return "danger"

    def _get_price_rules(self, project: Project) -> Optional[PriceRules]:
        """获取价格规则"""
        if not project.price_rules:
            return None

        rules = project.price_rules
        pricing_type = rules.get("type", "fixed")

        if pricing_type == "tiered" and "tiers" in rules:
            tiers = [
                PriceTier(
                    min=t.get("min", 0),
                    max=t.get("max"),
                    price=Decimal(str(t.get("price", 0))),
                )
                for t in rules["tiers"]
            ]
            return PriceRules(type="tiered", tiers=tiers)

        elif pricing_type == "spend_ratio":
            return PriceRules(
                type="spend_ratio",
                ratio=rules.get("ratio", 1.0),
            )

        return PriceRules(type="fixed")

    def _generate_periods(
        self,
        start: date,
        end: date,
        granularity: str,
    ) -> List[Tuple[date, date, str]]:
        """生成时间段列表"""
        periods = []

        if granularity == "day":
            current = start
            while current <= end:
                periods.append((
                    current,
                    current,
                    current.strftime("%Y-%m-%d"),
                ))
                current += timedelta(days=1)

        elif granularity == "week":
            # 按 ISO 周计算
            current = start
            while current <= end:
                # 获取周的开始（周一）
                week_start = current - timedelta(days=current.weekday())
                week_end = week_start + timedelta(days=6)

                # 确保不超出范围
                actual_start = max(week_start, start)
                actual_end = min(week_end, end)

                iso_year, iso_week, _ = current.isocalendar()
                periods.append((
                    actual_start,
                    actual_end,
                    f"{iso_year}-W{iso_week:02d}",
                ))

                current = week_end + timedelta(days=1)

        elif granularity == "month":
            current = start.replace(day=1)
            while current <= end:
                _, last_day = monthrange(current.year, current.month)
                month_end = current.replace(day=last_day)

                actual_start = max(current, start)
                actual_end = min(month_end, end)

                periods.append((
                    actual_start,
                    actual_end,
                    current.strftime("%Y-%m"),
                ))

                # 下个月
                if current.month == 12:
                    current = date(current.year + 1, 1, 1)
                else:
                    current = date(current.year, current.month + 1, 1)

        return periods
