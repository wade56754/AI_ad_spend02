"""
利润计算服务 (v3 修正版)

核心公式（对齐原始收支表）:
- 收款 = 进粉 × 单粉价格
- 消耗 = SUM(real_spend)
- 毛利 = 收款 - 消耗 （⚠️ 不含手续费！）
- CPL = 消耗 / 进粉

验证基准:
- 印度K4: 毛利率 33.8% (不是 26.6%)
- 德国Summer: 毛利率 44.4% (不是 37.4%)

SoT Reference:
- LEDGER_SOT.md v1.1 §1 Phase声明
- CLAUDE_CLI_TASK_CEO_DASHBOARD_REFACTOR_V3.md §2.1

Version: 3.0
Author: Claude Code
"""

from decimal import Decimal, ROUND_HALF_UP
from datetime import date, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy import func, and_
from sqlalchemy.orm import Session

from backend.models import Project, DailyReport, AdAccount


class ProfitService:
    """
    利润计算服务

    ⚠️ v3 核心修正:
    - cost = real_spend（不含手续费）
    - profit = revenue - cost
    - 手续费仅作参考，不计入成本
    """

    # 利润率阈值
    PROFIT_RATE_HEALTHY = Decimal("0.20")   # >= 20% 健康
    PROFIT_RATE_WARNING = Decimal("0.10")   # >= 10% 警告
    PROFIT_RATE_DANGER = Decimal("0.00")    # >= 0% 危险
    # < 0% 亏损

    # 目标毛利率
    TARGET_PROFIT_RATE = Decimal("0.20")

    def __init__(self, db: Session):
        self.db = db

    def get_profit_summary(self, period: str = None) -> Dict[str, Any]:
        """
        获取利润概览

        公式: 毛利 = 收款 - 消耗（不含手续费）

        Args:
            period: 月份，格式 YYYY-MM，默认当月

        Returns:
            利润概览数据
        """
        start_date, end_date = self._parse_period(period)

        # 获取活跃项目
        projects = self.db.query(Project).filter(
            Project.status.in_(["active", "completed", "planning"])
        ).all()

        total_revenue = Decimal("0")
        total_cost = Decimal("0")
        total_conversions = 0

        for project in projects:
            metrics = self.calculate_project_metrics(project, start_date, end_date)
            total_revenue += metrics["revenue"]
            total_cost += metrics["cost"]
            total_conversions += metrics["conversions"] or 0

        # 计算毛利（不含手续费）
        total_profit = total_revenue - total_cost

        # 边界处理：收款=0 时，利润率返回 null (前端显示 "--")
        if total_revenue > 0:
            profit_rate = (total_profit / total_revenue).quantize(
                Decimal("0.0001"), rounding=ROUND_HALF_UP
            )
            profit_rate_pct = float((profit_rate * 100).quantize(Decimal("0.1")))
            profit_status = self._get_profit_status(profit_rate)
            profit_status_label = self._get_profit_status_label(profit_rate)
            gap = profit_rate - self.TARGET_PROFIT_RATE
        else:
            # 收款=0，无法计算利润率
            profit_rate = None
            profit_rate_pct = None
            profit_status = "no_revenue"
            profit_status_label = "无收款"
            gap = None

        avg_cpl = (total_cost / total_conversions).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        ) if total_conversions > 0 else Decimal("0")

        return {
            "period": period or self._current_period(),
            "currency": "USD",
            "formula": "毛利 = 收款 - 消耗（不含手续费）",
            "revenue": {
                "total": float(total_revenue.quantize(Decimal("0.01"))),
                "label": "收款",
                "conversions": total_conversions,
                "avg_unit_price": float((total_revenue / total_conversions).quantize(Decimal("0.01"))) if total_conversions > 0 else 0,
                "note": "收款 = 进粉 × 单粉价格"
            },
            "cost": {
                "total": float(total_cost.quantize(Decimal("0.01"))),
                "label": "消耗",
                "note": "不含手续费"
            },
            "profit": {
                "total": float(total_profit.quantize(Decimal("0.01"))),
                "label": "毛利",
                "rate": float(profit_rate) if profit_rate is not None else None,
                "rate_pct": profit_rate_pct,
                "target_rate": float(self.TARGET_PROFIT_RATE),
                "gap": float(gap.quantize(Decimal("0.0001"))) if gap is not None else None,
                "status": profit_status,
                "status_label": profit_status_label
            },
            "cpl": {
                "overall": float(avg_cpl),
                "formula": "CPL = 消耗 / 进粉"
            },
            "fee_reference": {
                "estimated_rate": 0.08,
                "estimated_amount": float((total_cost * Decimal("0.08")).quantize(Decimal("0.01"))),
                "note": "仅供参考，不计入成本"
            }
        }

    def get_project_ranking(self, period: str = None, limit: int = 10) -> Dict[str, Any]:
        """
        获取项目毛利排行

        Args:
            period: 月份
            limit: 返回数量

        Returns:
            项目排行数据
        """
        start_date, end_date = self._parse_period(period)

        projects = self.db.query(Project).filter(
            Project.status.in_(["active", "completed", "planning"])
        ).all()

        project_metrics = []
        for project in projects:
            metrics = self.calculate_project_metrics(project, start_date, end_date)

            # 跳过没有数据的项目
            if metrics["revenue"] == 0 and metrics["cost"] == 0:
                continue

            # 边界处理：profit_rate 可能为 None (revenue=0)
            profit_rate = metrics["profit_rate"]
            if profit_rate is not None:
                profit_rate_float = float(profit_rate.quantize(Decimal("0.001")))
                profit_rate_pct = float((profit_rate * 100).quantize(Decimal("0.1")))
                profit_status = self._get_profit_status(profit_rate)
            else:
                profit_rate_float = None
                profit_rate_pct = None
                profit_status = "no_revenue"

            project_metrics.append({
                "project_id": project.id,
                "project_name": project.name,
                "client_name": project.client_name,
                "profit_status": profit_status,
                "pricing": self._get_pricing_info(project),
                "metrics": {
                    "conversions": metrics["conversions"],
                    "revenue": float(metrics["revenue"].quantize(Decimal("0.01"))),
                    "cost": float(metrics["cost"].quantize(Decimal("0.01"))),
                    "profit": float(metrics["profit"].quantize(Decimal("0.01"))),
                    "profit_rate": profit_rate_float,
                    "profit_rate_pct": profit_rate_pct,
                    "cpl": float(metrics["cpl"].quantize(Decimal("0.01"))) if metrics["cpl"] else None
                }
            })

        # 按毛利金额排序
        project_metrics.sort(key=lambda x: x["metrics"]["profit"], reverse=True)

        # 添加排名
        for i, item in enumerate(project_metrics):
            item["rank"] = i + 1

        # 统计
        healthy_count = len([p for p in project_metrics if p["profit_status"] == "healthy"])
        warning_count = len([p for p in project_metrics if p["profit_status"] == "warning"])
        danger_count = len([p for p in project_metrics if p["profit_status"] in ["danger", "loss"]])
        no_revenue_count = len([p for p in project_metrics if p["profit_status"] == "no_revenue"])

        total_profit = sum(p["metrics"]["profit"] for p in project_metrics)
        # 只计算有 profit_rate 的项目
        valid_rates = [p["metrics"]["profit_rate"] for p in project_metrics if p["metrics"]["profit_rate"] is not None]
        avg_profit_rate = (sum(valid_rates) / len(valid_rates)) if valid_rates else None

        return {
            "period": period or self._current_period(),
            "currency": "USD",
            "formula": "毛利 = 收款 - 消耗（不含手续费）",
            "items": project_metrics[:limit],
            "summary": {
                "total_projects": len(project_metrics),
                "healthy_count": healthy_count,
                "warning_count": warning_count,
                "danger_count": danger_count,
                "no_revenue_count": no_revenue_count,
                "total_profit": float(total_profit),
                "avg_profit_rate": float(avg_profit_rate) if avg_profit_rate is not None else None
            }
        }

    def calculate_project_metrics(
        self,
        project: Project,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """
        计算单个项目的指标

        ⚠️ v3 核心修正:
        - cost = real_spend（不含手续费）
        - profit = revenue - cost
        """
        # 获取项目下所有账户的 ID
        account_ids = [acc.id for acc in project.ad_accounts]

        if not account_ids:
            return {
                "conversions": 0,
                "revenue": Decimal("0"),
                "cost": Decimal("0"),
                "profit": Decimal("0"),
                "profit_rate": Decimal("0"),
                "cpl": None
            }

        # 获取进粉数（使用 conversions_final）
        conversions_result = self.db.query(
            func.coalesce(func.sum(DailyReport.conversions_final), 0)
        ).filter(
            DailyReport.ad_account_id.in_(account_ids),
            DailyReport.report_date >= start_date,
            DailyReport.report_date <= end_date
        ).scalar()
        conversions = int(conversions_result)

        # 获取消耗（使用 real_spend）
        spend_result = self.db.query(
            func.coalesce(func.sum(DailyReport.real_spend), 0)
        ).filter(
            DailyReport.ad_account_id.in_(account_ids),
            DailyReport.report_date >= start_date,
            DailyReport.report_date <= end_date
        ).scalar()
        real_spend = Decimal(str(spend_result))

        # 计算收款（按定价规则）
        revenue = self._calculate_revenue(project, conversions, real_spend)

        # ⚠️ v3 修正：消耗就是成本，不含手续费
        cost = real_spend

        # 计算毛利
        profit = revenue - cost
        # 边界处理：revenue=0 时返回 None (前端显示 "--")
        profit_rate = (profit / revenue) if revenue > 0 else None

        # CPL
        cpl = (real_spend / conversions) if conversions > 0 else None

        return {
            "conversions": conversions if conversions > 0 else None,
            "revenue": revenue,
            "cost": cost,  # 不含手续费
            "profit": profit,
            "profit_rate": profit_rate,  # None when revenue=0
            "cpl": cpl
        }

    def _calculate_revenue(
        self,
        project: Project,
        conversions: int,
        real_spend: Decimal
    ) -> Decimal:
        """
        计算收款（支持三种定价模式）

        1. fixed: 固定单价 (revenue = conversions × unit_price)
        2. tiered: 阶梯定价
        3. markup: 加价模式 (revenue = real_spend × markup_rate)
        """
        price_rules = project.price_rules or {}
        pricing_type = price_rules.get("type", "fixed")

        if pricing_type == "markup":
            # 华侨粉模式：按消耗加价
            markup_rate = Decimal(str(price_rules.get("markup_rate", 1.2)))
            return (real_spend * markup_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        elif pricing_type == "tiered":
            # 阶梯定价
            return self._calculate_tiered_revenue(conversions, price_rules)

        else:  # fixed
            # 固定单价
            unit_price = project.unit_price or Decimal("0")
            return (Decimal(str(conversions)) * unit_price).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def _calculate_tiered_revenue(
        self,
        conversions: int,
        price_rules: dict
    ) -> Decimal:
        """计算阶梯定价收入"""
        tiers = price_rules.get("tiers", [])
        if not tiers or conversions <= 0:
            return Decimal("0")

        total_revenue = Decimal("0")
        remaining = conversions

        sorted_tiers = sorted(tiers, key=lambda x: x.get("min", 0))

        for tier in sorted_tiers:
            if remaining <= 0:
                break

            tier_min = tier.get("min", 0)
            tier_max = tier.get("max")
            tier_price = Decimal(str(tier.get("price", 0)))

            if tier_max is None:
                # 无上限阶梯
                tier_count = remaining
            else:
                tier_range = tier_max - tier_min + 1
                tier_count = min(remaining, tier_range)

            total_revenue += Decimal(tier_count) * tier_price
            remaining -= tier_count

        return total_revenue.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def _get_pricing_info(self, project: Project) -> Dict[str, Any]:
        """获取项目定价信息"""
        price_rules = project.price_rules or {}
        pricing_type = price_rules.get("type", "fixed")

        if pricing_type == "markup":
            return {
                "type": "markup",
                "markup_rate": price_rules.get("markup_rate", 1.2),
                "note": f"按消耗×{price_rules.get('markup_rate', 1.2)}结算"
            }
        elif pricing_type == "tiered":
            return {
                "type": "tiered",
                "tiers": price_rules.get("tiers", []),
                "note": "阶梯定价"
            }
        else:
            return {
                "type": "fixed",
                "unit_price": float(project.unit_price or 0),
                "note": f"固定单价 ${project.unit_price or 0}"
            }

    def _get_profit_status(self, profit_rate: Decimal) -> str:
        """获取利润状态"""
        if profit_rate >= self.PROFIT_RATE_HEALTHY:
            return "healthy"
        if profit_rate >= self.PROFIT_RATE_WARNING:
            return "warning"
        if profit_rate >= self.PROFIT_RATE_DANGER:
            return "danger"
        return "loss"

    def _get_profit_status_label(self, profit_rate: Decimal) -> str:
        """获取利润状态标签"""
        status = self._get_profit_status(profit_rate)
        labels = {
            "healthy": "健康",
            "warning": "低于目标",
            "danger": "较低",
            "loss": "亏损"
        }
        return labels.get(status, "未知")

    def _parse_period(self, period: str = None) -> tuple:
        """解析月份参数"""
        if not period:
            today = date.today()
            start = today.replace(day=1)
            end = today
        else:
            year, month = map(int, period.split("-"))
            start = date(year, month, 1)
            if month == 12:
                end = date(year + 1, 1, 1) - timedelta(days=1)
            else:
                end = date(year, month + 1, 1) - timedelta(days=1)
        return start, end

    def _current_period(self) -> str:
        """获取当前月份"""
        return date.today().strftime("%Y-%m")
