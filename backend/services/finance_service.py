"""
财务利润服务
处理利润汇总查询等业务逻辑

SoT 对齐:
- DATA_SCHEMA.md v5.2: daily_reports, projects, ad_accounts 表结构
- BUSINESS_RULES.md v3.1: 利润计算公式
  - revenue = conversions_final × unit_price
  - cost = real_spend + fee
  - profit = revenue - cost
- ERROR_CODES_SOT.md v2.1: 错误码规范
"""

from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from backend.exceptions import ResourceNotFoundException, BusinessRuleException
from backend.models import Project, DailyReport, AdAccount
from backend.schemas.finance import (
    ProfitSummaryItem,
    ProfitSummaryResponse,
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


def get_finance_service(db: Session) -> FinanceService:
    """
    获取财务服务实例（依赖注入工厂函数）

    Args:
        db: 数据库会话

    Returns:
        FinanceService: 财务服务实例
    """
    return FinanceService(db)
