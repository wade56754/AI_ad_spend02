"""
CEO Dashboard 汇总服务

汇总所有 CEO 仪表盘数据。

SoT Reference:
- LEDGER_SOT.md v1.1
- CLAUDE_CLI_TASK_CEO_DASHBOARD_REFACTOR_V3.md

Version: 3.0
Author: Claude Code
"""

from decimal import Decimal
from datetime import date, datetime
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from .profit_service import ProfitService
from .project_balance_service import ProjectBalanceService
from .cash_status_service import CashStatusService
from backend.models import Project, DailyReport


class CEODashboardService:
    """CEO Dashboard 汇总服务"""

    def __init__(self, db: Session):
        self.db = db
        self.profit_service = ProfitService(db)
        self.balance_service = ProjectBalanceService(db)
        self.cash_service = CashStatusService(db)

    def get_overview(self, period: str = None) -> Dict[str, Any]:
        """
        获取 CEO 仪表盘概览

        Args:
            period: 月份，格式 YYYY-MM

        Returns:
            完整仪表盘数据
        """
        # 现金状况
        cash_status = self.cash_service.get_cash_status(period)

        # 利润概览
        profit_summary = self.profit_service.get_profit_summary(period)

        # 项目余额
        project_balance = self.balance_service.get_all_balances(period)

        # 待办事项
        action_items = self.get_action_items(period)

        # 项目排行 Top 5
        ranking = self.profit_service.get_project_ranking(period, limit=5)

        return {
            "period": period or self._current_period(),
            "currency": "USD",
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "formula_version": "v3",
            "formula_note": "毛利=收款-消耗，不含手续费",

            "cash_status": {
                "opening_balance": cash_status["balance"]["opening"],
                "closing_balance": cash_status["balance"]["closing"],
                "total_income": cash_status["income"]["total"],
                "total_expense": cash_status["expense"]["total"],
                "balance_change_pct": cash_status["balance"]["change_pct"],
                "runway_days": cash_status["runway"]["days"]
            },

            "profit_summary": {
                "total_revenue": profit_summary["revenue"]["total"],
                "total_cost": profit_summary["cost"]["total"],
                "total_profit": profit_summary["profit"]["total"],
                "profit_rate": profit_summary["profit"]["rate"],
                "profit_rate_pct": profit_summary["profit"]["rate_pct"],
                "total_conversions": profit_summary["revenue"]["conversions"],
                "avg_cpl": profit_summary["cpl"]["overall"],
                "target_profit_rate": profit_summary["profit"]["target_rate"],
                "profit_status": profit_summary["profit"]["status"]
            },

            "project_balance_summary": {
                "total_projects": project_balance["summary"]["total_count"],
                "prepaid_count": project_balance["summary"]["prepaid_count"],
                "pending_refund_count": project_balance["summary"]["pending_refund_count"],
                "refunded_count": project_balance["summary"]["refunded_count"],
                "total_prepaid_balance": project_balance["totals"]["total_balance"]
            },

            "action_items": action_items,

            "top_projects": [
                {
                    "project_name": p["project_name"],
                    "profit": p["metrics"]["profit"],
                    "profit_rate": p["metrics"]["profit_rate"],
                    "profit_rate_pct": p["metrics"]["profit_rate_pct"],
                    "status": p["profit_status"]
                }
                for p in ranking["items"][:5]
            ]
        }

    def get_action_items(self, period: str = None) -> Dict[str, Any]:
        """
        获取待办事项

        Args:
            period: 月份

        Returns:
            待办事项数据
        """
        # 异常项目（毛利率 < 10%）
        ranking = self.profit_service.get_project_ranking(period)
        abnormal_projects = [
            p for p in ranking["items"]
            if p["profit_status"] in ["danger", "loss"]
        ]

        abnormal_items = []
        for project in abnormal_projects:
            profit_rate_pct = project["metrics"]["profit_rate_pct"]
            profit = project["metrics"]["profit"]

            abnormal_items.append({
                "project_id": project["project_id"],
                "project_name": project["project_name"],
                "issue_type": "negative_profit" if profit < 0 else "low_profit",
                "severity": "high" if profit < 0 else "medium",
                "metrics": {
                    "revenue": project["metrics"]["revenue"],
                    "cost": project["metrics"]["cost"],
                    "profit": profit,
                    "profit_rate": project["metrics"]["profit_rate"]
                },
                "message": f"毛利率{profit_rate_pct:.1f}%，本月{'亏损' if profit < 0 else '利润较低'} ${abs(profit):,.0f}",
                "suggested_action": "pause" if profit < 0 else "review",
                "actions": [
                    {"key": "pause", "label": "暂停项目", "variant": "destructive"},
                    {"key": "view", "label": "查看详情", "variant": "outline"}
                ]
            })

        # 待处理日报
        pending_reports = self._get_pending_reports()

        # 待退款项目
        balance_data = self.balance_service.get_all_balances(period)
        pending_refunds = [
            {
                "project_name": item["project_name"],
                "amount": item["balance"]
            }
            for item in balance_data["items"]
            if item["status"] == "pending_refund"
        ]

        return {
            "abnormal_projects": {
                "count": len(abnormal_items),
                "items": abnormal_items
            },
            "pending_reports": {
                "count": pending_reports["total_count"],
                "items": pending_reports["items"]
            },
            "pending_refunds": {
                "count": len(pending_refunds),
                "total_amount": sum(p["amount"] for p in pending_refunds),
                "items": pending_refunds
            }
        }

    def get_trend_data(
        self,
        period: str = None,
        granularity: str = "daily"
    ) -> Dict[str, Any]:
        """
        获取趋势数据

        Args:
            period: 月份
            granularity: 粒度 (daily/weekly/monthly)

        Returns:
            趋势数据
        """
        from datetime import timedelta
        from sqlalchemy import func

        start_date, end_date = self.profit_service._parse_period(period)

        # 按天聚合数据
        daily_data = self.db.query(
            DailyReport.report_date,
            func.sum(DailyReport.real_spend).label("spend"),
            func.sum(DailyReport.conversions_final).label("conversions")
        ).filter(
            DailyReport.report_date >= start_date,
            DailyReport.report_date <= end_date
        ).group_by(
            DailyReport.report_date
        ).order_by(
            DailyReport.report_date
        ).all()

        # 获取所有项目的平均单价
        projects = self.db.query(Project).filter(
            Project.status.in_(["active", "completed", "planning"])
        ).all()

        # 计算平均单价
        total_unit_price = sum(float(p.unit_price or 0) for p in projects)
        avg_unit_price = Decimal(str(total_unit_price / len(projects))) if projects else Decimal("0")

        # 构建趋势数据
        trend_items = []
        for row in daily_data:
            conversions = int(row.conversions or 0)
            spend = Decimal(str(row.spend or 0))
            revenue = Decimal(str(conversions)) * avg_unit_price
            profit = revenue - spend

            trend_items.append({
                "date": row.report_date.strftime("%Y-%m-%d"),
                "revenue": float(revenue.quantize(Decimal("0.01"))),
                "spend": float(spend.quantize(Decimal("0.01"))),
                "profit": float(profit.quantize(Decimal("0.01"))),
                "conversions": conversions
            })

        return {
            "period": period or self._current_period(),
            "granularity": granularity,
            "items": trend_items
        }

    def _get_pending_reports(self) -> Dict[str, Any]:
        """获取待处理日报统计"""
        from sqlalchemy import func

        # 统计各状态的日报数量
        pending_statuses = ["raw_submitted", "trend_pending", "trend_flagged", "final_pending"]

        results = self.db.query(
            DailyReport.report_date,
            DailyReport.status,
            func.count(DailyReport.id).label("count")
        ).filter(
            DailyReport.status.in_(pending_statuses)
        ).group_by(
            DailyReport.report_date,
            DailyReport.status
        ).order_by(
            DailyReport.report_date.desc()
        ).limit(10).all()

        items = []
        date_counts = {}

        for row in results:
            date_str = row.report_date.strftime("%Y-%m-%d")
            if date_str not in date_counts:
                date_counts[date_str] = {"date": date_str, "count": 0, "statuses": []}
            date_counts[date_str]["count"] += row.count
            date_counts[date_str]["statuses"].append({
                "status": row.status,
                "count": row.count
            })

        items = list(date_counts.values())
        total_count = sum(item["count"] for item in items)

        return {
            "total_count": total_count,
            "items": items[:5]  # 只返回最近5天
        }

    def _current_period(self) -> str:
        """获取当前月份"""
        return date.today().strftime("%Y-%m")
