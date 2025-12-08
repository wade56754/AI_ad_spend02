"""
财务利润服务
处理利润汇总查询等业务逻辑

SoT 对齐:
- DATA_SCHEMA.md v5.2: daily_reports, projects, ad_accounts, channels 表结构
- BUSINESS_RULES.md v3.1: 利润计算公式
  - revenue = conversions_final × unit_price
  - cost = real_spend + fee
  - profit = revenue - cost
  - profit_margin = profit / revenue × 100
- ERROR_CODES_SOT.md v2.1: 错误码规范

Version: 2.0
Author: Claude Code
"""

from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, List, Dict, Any
import statistics

from sqlalchemy import and_, func, extract, case
from sqlalchemy.orm import Session

from backend.exceptions import ResourceNotFoundException, BusinessRuleException
from backend.models import Project, DailyReport, AdAccount, Channel
from backend.schemas.finance import (
    ProfitSummaryItem,
    ProfitSummaryResponse,
    ProfitByProjectItem,
    ProfitByProjectResponse,
    ProfitByAccountItem,
    ProfitByAccountResponse,
    ProfitByChannelItem,
    ProfitByChannelResponse,
    ProfitTrendItem,
    ProfitTrendResponse,
    ProfitCompareItem,
    ProfitCompareResponse,
    ProfitOverviewResponse,
    TrendGranularityEnum,
)


class FinanceService:
    """财务利润服务类"""

    def __init__(self, db: Session):
        """
        初始化财务服务

        Args:
            db: 数据库会话（通过 FastAPI 依赖注入）
        """
        self.db = db

    def get_profit_summary(
        self,
        project_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> ProfitSummaryResponse:
        """
        获取利润汇总

        Args:
            project_id: 项目ID (可选，不传则返回全部项目汇总)
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            ProfitSummaryResponse: 利润汇总响应

        Raises:
            ResourceNotFoundException: 项目不存在时抛出 BIZ_002
            BusinessRuleException: 日期范围无效时抛出 BIZ_001
        """
        # 日期范围验证
        if start_date and end_date and start_date > end_date:
            raise BusinessRuleException(
                message="开始日期不能晚于结束日期"
            )

        # 如果指定了 project_id，先验证项目存在
        if project_id is not None:
            project = self.db.query(Project).filter(Project.id == project_id).first()
            if not project:
                raise ResourceNotFoundException(
                    message=f"项目 {project_id} 不存在"
                )

        # 构建查询 - 通过 ad_accounts 关联 project
        # daily_reports.ad_account_id → ad_accounts.project_id → projects.id
        # 使用 DailyReport.unit_price 而非 Project.unit_price（模型未实现）
        query = self.db.query(
            DailyReport.report_date,
            AdAccount.project_id,
            Project.name.label('project_name'),
            func.avg(DailyReport.unit_price).label('project_unit_price'),  # 使用日报中的单价
            func.sum(DailyReport.conversions_final).label('conversions_final'),
            func.sum(DailyReport.real_spend).label('real_spend'),
        ).join(
            AdAccount, DailyReport.ad_account_id == AdAccount.id
        ).join(
            Project, AdAccount.project_id == Project.id
        )

        # 应用过滤条件
        filters = []
        if project_id is not None:
            filters.append(AdAccount.project_id == project_id)
        if start_date:
            filters.append(DailyReport.report_date >= start_date)
        if end_date:
            filters.append(DailyReport.report_date <= end_date)

        if filters:
            query = query.filter(and_(*filters))

        # 按日期和项目分组
        query = query.group_by(
            DailyReport.report_date,
            AdAccount.project_id,
            Project.name
        ).order_by(DailyReport.report_date.desc())

        results = query.all()

        # 构建响应
        items = []
        total_conversions = 0
        total_revenue = Decimal("0.00")
        total_cost = Decimal("0.00")

        for row in results:
            conversions = row.conversions_final or 0
            unit_price = row.project_unit_price or Decimal("0.00")
            real_spend = row.real_spend or Decimal("0.00")
            fee = Decimal("0.00")  # TODO: 从渠道服务费配置获取

            # 计算利润
            revenue = Decimal(conversions) * unit_price
            cost = real_spend + fee
            profit = revenue - cost

            # 计算利润率
            if revenue > 0:
                profit_margin = float((profit / revenue * 100).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                ))
            else:
                profit_margin = 0.0

            item = ProfitSummaryItem(
                report_date=row.report_date,
                project_id=row.project_id,
                project_name=row.project_name,
                conversions_final=conversions,
                unit_price=unit_price,
                revenue=revenue.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
                real_spend=real_spend,
                fee=fee,
                cost=cost.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
                profit=profit.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
                profit_margin=profit_margin,
            )
            items.append(item)

            # 累计总计
            total_conversions += conversions
            total_revenue += revenue
            total_cost += cost

        # 计算总体利润
        total_profit = total_revenue - total_cost
        if total_revenue > 0:
            overall_profit_margin = float((total_profit / total_revenue * 100).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            ))
        else:
            overall_profit_margin = 0.0

        return ProfitSummaryResponse(
            items=items,
            total_conversions=total_conversions,
            total_revenue=total_revenue.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            total_cost=total_cost.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            total_profit=total_profit.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            overall_profit_margin=overall_profit_margin,
        )

    def _calculate_profit_margin(self, revenue: Decimal, profit: Decimal) -> float:
        """计算利润率"""
        if revenue > 0:
            return float((profit / revenue * 100).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            ))
        return 0.0

    def get_profit_by_project(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 20,
    ) -> ProfitByProjectResponse:
        """
        按项目维度统计利润

        Args:
            start_date: 开始日期
            end_date: 结束日期
            limit: 返回数量限制

        Returns:
            ProfitByProjectResponse: 按项目汇总的利润数据
        """
        if start_date and end_date and start_date > end_date:
            raise BusinessRuleException(message="开始日期不能晚于结束日期")

        query = self.db.query(
            AdAccount.project_id,
            Project.name.label('project_name'),
            func.sum(DailyReport.conversions_final).label('conversions_final'),
            func.avg(DailyReport.unit_price).label('avg_unit_price'),
            func.sum(DailyReport.real_spend).label('real_spend'),
            func.count(DailyReport.id).label('report_count'),
        ).join(
            AdAccount, DailyReport.ad_account_id == AdAccount.id
        ).join(
            Project, AdAccount.project_id == Project.id
        )

        filters = []
        if start_date:
            filters.append(DailyReport.report_date >= start_date)
        if end_date:
            filters.append(DailyReport.report_date <= end_date)

        if filters:
            query = query.filter(and_(*filters))

        query = query.group_by(
            AdAccount.project_id,
            Project.name
        ).order_by(func.sum(DailyReport.real_spend).desc()).limit(limit)

        results = query.all()

        items = []
        total_conversions = 0
        total_revenue = Decimal("0.00")
        total_cost = Decimal("0.00")

        for row in results:
            conversions = row.conversions_final or 0
            avg_unit_price = Decimal(str(row.avg_unit_price or 0))
            real_spend = row.real_spend or Decimal("0.00")
            fee = Decimal("0.00")

            revenue = Decimal(conversions) * avg_unit_price
            cost = real_spend + fee
            profit = revenue - cost

            item = ProfitByProjectItem(
                project_id=row.project_id,
                project_name=row.project_name,
                total_conversions=conversions,
                avg_unit_price=avg_unit_price.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
                total_revenue=revenue.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
                total_spend=real_spend.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
                total_fee=fee,
                total_cost=cost.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
                total_profit=profit.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
                profit_margin=self._calculate_profit_margin(revenue, profit),
                report_count=row.report_count or 0,
            )
            items.append(item)

            total_conversions += conversions
            total_revenue += revenue
            total_cost += cost

        total_profit = total_revenue - total_cost

        return ProfitByProjectResponse(
            items=items,
            total_projects=len(items),
            total_conversions=total_conversions,
            total_revenue=total_revenue.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            total_cost=total_cost.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            total_profit=total_profit.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            overall_profit_margin=self._calculate_profit_margin(total_revenue, total_profit),
        )

    def get_profit_by_account(
        self,
        project_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 20,
    ) -> ProfitByAccountResponse:
        """
        按账户维度统计利润

        Args:
            project_id: 项目ID过滤
            start_date: 开始日期
            end_date: 结束日期
            limit: 返回数量限制

        Returns:
            ProfitByAccountResponse: 按账户汇总的利润数据
        """
        if start_date and end_date and start_date > end_date:
            raise BusinessRuleException(message="开始日期不能晚于结束日期")

        if project_id is not None:
            project = self.db.query(Project).filter(Project.id == project_id).first()
            if not project:
                raise ResourceNotFoundException(message=f"项目 {project_id} 不存在")

        query = self.db.query(
            DailyReport.ad_account_id,
            AdAccount.name.label('account_name'),
            AdAccount.project_id,
            Project.name.label('project_name'),
            func.sum(DailyReport.conversions_final).label('conversions_final'),
            func.avg(DailyReport.unit_price).label('avg_unit_price'),
            func.sum(DailyReport.real_spend).label('real_spend'),
        ).join(
            AdAccount, DailyReport.ad_account_id == AdAccount.id
        ).join(
            Project, AdAccount.project_id == Project.id
        )

        filters = []
        if project_id is not None:
            filters.append(AdAccount.project_id == project_id)
        if start_date:
            filters.append(DailyReport.report_date >= start_date)
        if end_date:
            filters.append(DailyReport.report_date <= end_date)

        if filters:
            query = query.filter(and_(*filters))

        query = query.group_by(
            DailyReport.ad_account_id,
            AdAccount.name,
            AdAccount.project_id,
            Project.name
        ).order_by(func.sum(DailyReport.real_spend).desc()).limit(limit)

        results = query.all()

        items = []
        total_conversions = 0
        total_revenue = Decimal("0.00")
        total_cost = Decimal("0.00")

        for row in results:
            conversions = row.conversions_final or 0
            avg_unit_price = Decimal(str(row.avg_unit_price or 0))
            real_spend = row.real_spend or Decimal("0.00")

            revenue = Decimal(conversions) * avg_unit_price
            cost = real_spend
            profit = revenue - cost

            item = ProfitByAccountItem(
                ad_account_id=row.ad_account_id,
                account_name=row.account_name or f"Account-{row.ad_account_id}",
                project_id=row.project_id,
                project_name=row.project_name,
                total_conversions=conversions,
                total_revenue=revenue.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
                total_spend=real_spend.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
                total_cost=cost.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
                total_profit=profit.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
                profit_margin=self._calculate_profit_margin(revenue, profit),
            )
            items.append(item)

            total_conversions += conversions
            total_revenue += revenue
            total_cost += cost

        total_profit = total_revenue - total_cost

        return ProfitByAccountResponse(
            items=items,
            total_accounts=len(items),
            total_conversions=total_conversions,
            total_revenue=total_revenue.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            total_cost=total_cost.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            total_profit=total_profit.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            overall_profit_margin=self._calculate_profit_margin(total_revenue, total_profit),
        )

    def get_profit_by_channel(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 20,
    ) -> ProfitByChannelResponse:
        """
        按渠道维度统计利润

        Args:
            start_date: 开始日期
            end_date: 结束日期
            limit: 返回数量限制

        Returns:
            ProfitByChannelResponse: 按渠道汇总的利润数据
        """
        if start_date and end_date and start_date > end_date:
            raise BusinessRuleException(message="开始日期不能晚于结束日期")

        query = self.db.query(
            AdAccount.channel_id,
            Channel.name.label('channel_name'),
            func.count(func.distinct(AdAccount.id)).label('account_count'),
            func.sum(DailyReport.conversions_final).label('conversions_final'),
            func.avg(DailyReport.unit_price).label('avg_unit_price'),
            func.sum(DailyReport.real_spend).label('real_spend'),
        ).join(
            AdAccount, DailyReport.ad_account_id == AdAccount.id
        ).join(
            Channel, AdAccount.channel_id == Channel.id
        )

        filters = []
        if start_date:
            filters.append(DailyReport.report_date >= start_date)
        if end_date:
            filters.append(DailyReport.report_date <= end_date)

        if filters:
            query = query.filter(and_(*filters))

        query = query.group_by(
            AdAccount.channel_id,
            Channel.name
        ).order_by(func.sum(DailyReport.real_spend).desc()).limit(limit)

        results = query.all()

        items = []
        total_conversions = 0
        total_revenue = Decimal("0.00")
        total_cost = Decimal("0.00")

        for row in results:
            conversions = row.conversions_final or 0
            avg_unit_price = Decimal(str(row.avg_unit_price or 0))
            real_spend = row.real_spend or Decimal("0.00")

            revenue = Decimal(conversions) * avg_unit_price
            cost = real_spend
            profit = revenue - cost

            item = ProfitByChannelItem(
                channel_id=row.channel_id,
                channel_name=row.channel_name or f"Channel-{row.channel_id}",
                total_accounts=row.account_count or 0,
                total_conversions=conversions,
                total_revenue=revenue.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
                total_spend=real_spend.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
                total_cost=cost.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
                total_profit=profit.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
                profit_margin=self._calculate_profit_margin(revenue, profit),
            )
            items.append(item)

            total_conversions += conversions
            total_revenue += revenue
            total_cost += cost

        total_profit = total_revenue - total_cost

        return ProfitByChannelResponse(
            items=items,
            total_channels=len(items),
            total_conversions=total_conversions,
            total_revenue=total_revenue.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            total_cost=total_cost.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            total_profit=total_profit.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            overall_profit_margin=self._calculate_profit_margin(total_revenue, total_profit),
        )

    def get_profit_trend(
        self,
        project_id: Optional[int] = None,
        channel_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        granularity: TrendGranularityEnum = TrendGranularityEnum.DAILY,
    ) -> ProfitTrendResponse:
        """
        获取利润趋势分析

        Args:
            project_id: 项目ID过滤
            channel_id: 渠道ID过滤
            start_date: 开始日期
            end_date: 结束日期
            granularity: 趋势粒度（daily/weekly/monthly）

        Returns:
            ProfitTrendResponse: 利润趋势数据
        """
        if start_date and end_date and start_date > end_date:
            raise BusinessRuleException(message="开始日期不能晚于结束日期")

        # 默认时间范围：最近30天
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=30)

        # 根据粒度选择分组字段
        if granularity == TrendGranularityEnum.DAILY:
            period_field = DailyReport.report_date
            group_by = [DailyReport.report_date]
        elif granularity == TrendGranularityEnum.WEEKLY:
            period_field = func.date_trunc('week', DailyReport.report_date)
            group_by = [period_field]
        else:  # MONTHLY
            period_field = func.date_trunc('month', DailyReport.report_date)
            group_by = [period_field]

        query = self.db.query(
            period_field.label('period'),
            func.sum(DailyReport.conversions_final).label('conversions_final'),
            func.avg(DailyReport.unit_price).label('avg_unit_price'),
            func.sum(DailyReport.real_spend).label('real_spend'),
        ).join(
            AdAccount, DailyReport.ad_account_id == AdAccount.id
        )

        filters = [
            DailyReport.report_date >= start_date,
            DailyReport.report_date <= end_date,
        ]

        if project_id is not None:
            filters.append(AdAccount.project_id == project_id)
        if channel_id is not None:
            filters.append(AdAccount.channel_id == channel_id)

        query = query.filter(and_(*filters))
        query = query.group_by(*group_by).order_by(period_field)

        results = query.all()

        items = []
        profits = []

        for i, row in enumerate(results):
            conversions = row.conversions_final or 0
            avg_unit_price = Decimal(str(row.avg_unit_price or 0))
            real_spend = row.real_spend or Decimal("0.00")

            revenue = Decimal(conversions) * avg_unit_price
            cost = real_spend
            profit = revenue - cost

            # 计算环比变化
            profit_change = None
            profit_change_rate = None
            if i > 0 and items:
                prev_profit = items[i - 1].total_profit
                profit_change = profit - prev_profit
                if prev_profit != 0:
                    profit_change_rate = float((profit_change / abs(prev_profit) * 100).quantize(
                        Decimal("0.01"), rounding=ROUND_HALF_UP
                    ))

            # 确定时间段
            period_date = row.period if isinstance(row.period, date) else row.period.date() if row.period else start_date
            if granularity == TrendGranularityEnum.DAILY:
                period_str = period_date.isoformat()
                period_start = period_date
                period_end = period_date
            elif granularity == TrendGranularityEnum.WEEKLY:
                period_str = f"Week {period_date.isocalendar()[1]}"
                period_start = period_date
                period_end = period_date + timedelta(days=6)
            else:
                period_str = period_date.strftime("%Y-%m")
                period_start = period_date.replace(day=1)
                next_month = period_date.replace(day=28) + timedelta(days=4)
                period_end = next_month - timedelta(days=next_month.day)

            item = ProfitTrendItem(
                period=period_str,
                period_start=period_start,
                period_end=period_end,
                total_conversions=conversions,
                total_revenue=revenue.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
                total_cost=cost.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
                total_profit=profit.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
                profit_margin=self._calculate_profit_margin(revenue, profit),
                profit_change=profit_change.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) if profit_change else None,
                profit_change_rate=profit_change_rate,
            )
            items.append(item)
            profits.append(float(profit))

        # 计算统计指标
        if profits:
            avg_profit = Decimal(str(sum(profits) / len(profits)))
            max_profit = Decimal(str(max(profits)))
            min_profit = Decimal(str(min(profits)))
            volatility = statistics.stdev(profits) / abs(sum(profits) / len(profits)) * 100 if len(profits) > 1 and sum(profits) != 0 else 0.0
        else:
            avg_profit = Decimal("0.00")
            max_profit = Decimal("0.00")
            min_profit = Decimal("0.00")
            volatility = 0.0

        return ProfitTrendResponse(
            items=items,
            granularity=granularity.value,
            period_count=len(items),
            avg_profit=avg_profit.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            max_profit=max_profit.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            min_profit=min_profit.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            profit_volatility=round(volatility, 2),
        )

    def compare_profit(
        self,
        project_ids: List[int],
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> ProfitCompareResponse:
        """
        项目利润对比分析

        Args:
            project_ids: 对比项目ID列表
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            ProfitCompareResponse: 利润对比数据
        """
        if not project_ids:
            raise BusinessRuleException(message="至少需要指定一个项目进行对比")

        if start_date and end_date and start_date > end_date:
            raise BusinessRuleException(message="开始日期不能晚于结束日期")

        # 验证项目存在
        projects = self.db.query(Project).filter(Project.id.in_(project_ids)).all()
        if len(projects) != len(project_ids):
            existing_ids = {p.id for p in projects}
            missing_ids = set(project_ids) - existing_ids
            raise ResourceNotFoundException(message=f"项目不存在: {missing_ids}")

        query = self.db.query(
            AdAccount.project_id,
            Project.name.label('project_name'),
            func.sum(DailyReport.conversions_final).label('conversions_final'),
            func.avg(DailyReport.unit_price).label('avg_unit_price'),
            func.sum(DailyReport.real_spend).label('real_spend'),
        ).join(
            AdAccount, DailyReport.ad_account_id == AdAccount.id
        ).join(
            Project, AdAccount.project_id == Project.id
        ).filter(
            AdAccount.project_id.in_(project_ids)
        )

        filters = []
        if start_date:
            filters.append(DailyReport.report_date >= start_date)
        if end_date:
            filters.append(DailyReport.report_date <= end_date)

        if filters:
            query = query.filter(and_(*filters))

        query = query.group_by(
            AdAccount.project_id,
            Project.name
        )

        results = query.all()

        # 构建项目利润数据
        profit_data = []
        for row in results:
            conversions = row.conversions_final or 0
            avg_unit_price = Decimal(str(row.avg_unit_price or 0))
            real_spend = row.real_spend or Decimal("0.00")

            revenue = Decimal(conversions) * avg_unit_price
            cost = real_spend
            profit = revenue - cost
            margin = self._calculate_profit_margin(revenue, profit)

            profit_data.append({
                'project_id': row.project_id,
                'project_name': row.project_name,
                'conversions': conversions,
                'revenue': revenue,
                'cost': cost,
                'profit': profit,
                'margin': margin,
            })

        # 排序计算排名
        sorted_by_profit = sorted(profit_data, key=lambda x: x['profit'], reverse=True)
        sorted_by_margin = sorted(profit_data, key=lambda x: x['margin'], reverse=True)

        profit_ranks = {d['project_id']: i + 1 for i, d in enumerate(sorted_by_profit)}
        margin_ranks = {d['project_id']: i + 1 for i, d in enumerate(sorted_by_margin)}

        items = []
        total_profit = Decimal("0.00")
        total_margins = []

        for d in profit_data:
            item = ProfitCompareItem(
                project_id=d['project_id'],
                project_name=d['project_name'],
                total_conversions=d['conversions'],
                total_revenue=d['revenue'].quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
                total_cost=d['cost'].quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
                total_profit=d['profit'].quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
                profit_margin=d['margin'],
                rank_by_profit=profit_ranks[d['project_id']],
                rank_by_margin=margin_ranks[d['project_id']],
            )
            items.append(item)
            total_profit += d['profit']
            total_margins.append(d['margin'])

        # 找出最佳项目
        best_profit_project = sorted_by_profit[0]['project_name'] if sorted_by_profit else None
        best_margin_project = sorted_by_margin[0]['project_name'] if sorted_by_margin else None
        avg_margin = sum(total_margins) / len(total_margins) if total_margins else 0.0

        return ProfitCompareResponse(
            items=items,
            compare_count=len(items),
            best_profit_project=best_profit_project,
            best_margin_project=best_margin_project,
            total_profit=total_profit.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            avg_profit_margin=round(avg_margin, 2),
        )

    def get_profit_overview(self) -> ProfitOverviewResponse:
        """
        获取利润概览

        Returns:
            ProfitOverviewResponse: 利润概览数据（今日/本周/本月）
        """
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        month_start = today.replace(day=1)

        yesterday = today - timedelta(days=1)
        last_week_start = week_start - timedelta(days=7)
        last_week_end = week_start - timedelta(days=1)
        last_month_start = (month_start - timedelta(days=1)).replace(day=1)
        last_month_end = month_start - timedelta(days=1)

        def get_period_data(start: date, end: date) -> Dict[str, Decimal]:
            """获取指定时间段的数据"""
            result = self.db.query(
                func.sum(DailyReport.conversions_final).label('conversions'),
                func.avg(DailyReport.unit_price).label('avg_unit_price'),
                func.sum(DailyReport.real_spend).label('real_spend'),
            ).filter(
                and_(
                    DailyReport.report_date >= start,
                    DailyReport.report_date <= end,
                )
            ).first()

            if result and result.conversions:
                conversions = result.conversions or 0
                avg_unit_price = Decimal(str(result.avg_unit_price or 0))
                real_spend = result.real_spend or Decimal("0.00")

                revenue = Decimal(conversions) * avg_unit_price
                cost = real_spend
                profit = revenue - cost
            else:
                revenue = Decimal("0.00")
                cost = Decimal("0.00")
                profit = Decimal("0.00")

            return {
                'revenue': revenue.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
                'cost': cost.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
                'profit': profit.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
                'margin': self._calculate_profit_margin(revenue, profit),
            }

        def calculate_change(current: Decimal, previous: Decimal) -> Optional[float]:
            """计算变化率"""
            if previous and previous != 0:
                change = (current - previous) / abs(previous) * 100
                return float(change.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
            return None

        # 获取各时间段数据
        today_data = get_period_data(today, today)
        week_data = get_period_data(week_start, today)
        month_data = get_period_data(month_start, today)

        yesterday_data = get_period_data(yesterday, yesterday)
        last_week_data = get_period_data(last_week_start, last_week_end)
        last_month_data = get_period_data(last_month_start, last_month_end)

        # 获取TOP项目
        top_projects = self.db.query(
            AdAccount.project_id,
            Project.name.label('project_name'),
            func.sum(DailyReport.conversions_final).label('conversions'),
            func.sum(DailyReport.real_spend).label('real_spend'),
        ).join(
            AdAccount, DailyReport.ad_account_id == AdAccount.id
        ).join(
            Project, AdAccount.project_id == Project.id
        ).filter(
            DailyReport.report_date >= month_start
        ).group_by(
            AdAccount.project_id,
            Project.name
        ).order_by(func.sum(DailyReport.real_spend).desc()).limit(5).all()

        top_profit_projects = []
        for p in top_projects:
            conversions = p.conversions or 0
            real_spend = p.real_spend or Decimal("0.00")
            # 简化计算：假设平均单价
            profit = Decimal(conversions) * Decimal("10") - real_spend  # 假设单价10
            top_profit_projects.append({
                'project_id': p.project_id,
                'project_name': p.project_name,
                'profit': float(profit.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
            })

        return ProfitOverviewResponse(
            today_revenue=today_data['revenue'],
            today_cost=today_data['cost'],
            today_profit=today_data['profit'],
            today_profit_margin=today_data['margin'],
            week_revenue=week_data['revenue'],
            week_cost=week_data['cost'],
            week_profit=week_data['profit'],
            week_profit_margin=week_data['margin'],
            month_revenue=month_data['revenue'],
            month_cost=month_data['cost'],
            month_profit=month_data['profit'],
            month_profit_margin=month_data['margin'],
            profit_change_from_yesterday=calculate_change(today_data['profit'], yesterday_data['profit']),
            profit_change_from_last_week=calculate_change(week_data['profit'], last_week_data['profit']),
            profit_change_from_last_month=calculate_change(month_data['profit'], last_month_data['profit']),
            top_profit_projects=top_profit_projects,
        )


def get_finance_service(db: Session) -> FinanceService:
    """
    获取财务服务实例（依赖注入工厂函数）

    Args:
        db: 数据库会话

    Returns:
        FinanceService: 财务服务实例
    """
    return FinanceService(db)
