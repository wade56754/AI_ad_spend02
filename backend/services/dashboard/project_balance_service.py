"""
项目余额服务

核心公式（对齐原始收支表"剩余预付款"）:
- 余额 = 累计收款 - 累计消耗
- 如果 > 0：客户预付款
- 如果 = 0：已结清
- 如果 < 0：需补款（罕见）

SoT Reference:
- LEDGER_SOT.md v1.1
- CLAUDE_CLI_TASK_CEO_DASHBOARD_REFACTOR_V3.md §2.2

Version: 3.0
Author: Claude Code
"""

from decimal import Decimal, ROUND_HALF_UP
from datetime import date
from typing import Dict, List, Any, Optional
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.models import Project, LedgerEntry, DailyReport


class ProjectBalanceService:
    """项目余额服务"""

    def __init__(self, db: Session):
        self.db = db

    def get_all_balances(self, period: str = None) -> Dict[str, Any]:
        """
        获取所有项目余额

        Args:
            period: 月份（可选，用于过滤）

        Returns:
            项目余额列表
        """
        # 获取有余额相关的项目
        projects = self.db.query(Project).filter(
            Project.status.in_(["active", "completed", "refunded", "planning"])
        ).all()

        items = []
        totals = {
            "cumulative_revenue": Decimal("0"),
            "cumulative_cost": Decimal("0"),
            "total_balance": Decimal("0")
        }

        for project in projects:
            balance_info = self._get_project_balance(project)

            # 跳过没有任何金额的项目
            if balance_info["cumulative_revenue"] == 0 and balance_info["cumulative_cost"] == 0:
                continue

            items.append(balance_info)

            totals["cumulative_revenue"] += Decimal(str(balance_info["cumulative_revenue"]))
            totals["cumulative_cost"] += Decimal(str(balance_info["cumulative_cost"]))
            totals["total_balance"] += Decimal(str(balance_info["balance"]))

        # 按余额排序
        items.sort(key=lambda x: x["balance"], reverse=True)

        return {
            "period": period or self._current_period(),
            "currency": "USD",
            "formula": "余额 = 累计收款 - 累计消耗",
            "items": items,
            "totals": {k: float(v.quantize(Decimal("0.01"))) for k, v in totals.items()},
            "summary": self._get_summary(items)
        }

    def get_project_balance(self, project_id: int) -> Optional[Dict[str, Any]]:
        """
        获取单个项目余额

        Args:
            project_id: 项目ID

        Returns:
            项目余额详情
        """
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return None

        return self._get_project_balance(project)

    def _get_project_balance(self, project: Project) -> Dict[str, Any]:
        """
        计算单个项目余额

        余额 = 累计收款(TOPUP) - 累计消耗
        """
        # 获取项目下所有账户
        account_ids = [acc.id for acc in project.ad_accounts]

        # 方案1: 从 LedgerEntry 获取累计收款（甲方打款）
        # 通过 ad_account_id 关联到项目
        if account_ids:
            topup_amount = self.db.query(
                func.coalesce(func.sum(LedgerEntry.amount), 0)
            ).filter(
                LedgerEntry.ad_account_id.in_(account_ids),
                LedgerEntry.entry_type == "TOPUP"
            ).scalar()
            cumulative_topup = Decimal(str(topup_amount))
        else:
            cumulative_topup = Decimal("0")

        if account_ids:
            spend_amount = self.db.query(
                func.coalesce(func.sum(DailyReport.real_spend), 0)
            ).filter(
                DailyReport.ad_account_id.in_(account_ids)
            ).scalar()
            cumulative_spend = Decimal(str(spend_amount))
        else:
            cumulative_spend = Decimal("0")

        # 计算余额
        balance = cumulative_topup - cumulative_spend

        # 检查退款
        refund = self._get_refund_info(account_ids)

        # 确定状态
        status = self._determine_status(balance, refund, project.status)

        # 如果已退款，余额显示为0
        final_balance = Decimal("0") if refund else balance

        return {
            "project_id": project.id,
            "project_name": project.name,
            "client_name": project.client_name or project.name,
            "cumulative_revenue": float(cumulative_topup.quantize(Decimal("0.01"))),
            "cumulative_cost": float(cumulative_spend.quantize(Decimal("0.01"))),
            "balance": float(final_balance.quantize(Decimal("0.01"))),
            "status": status["code"],
            "status_label": status["label"],
            "refund_amount": refund.get("amount") if refund else None,
            "refund_date": refund.get("date") if refund else None,
            "note": self._generate_note(status, final_balance, refund)
        }

    def _get_refund_info(self, account_ids: List[int]) -> Optional[Dict[str, Any]]:
        """获取退款信息"""
        if not account_ids:
            return None
        # 只查询需要的字段，避免 balance_after 不存在的问题
        refund = self.db.query(
            LedgerEntry.amount,
            LedgerEntry.entry_date
        ).filter(
            LedgerEntry.ad_account_id.in_(account_ids),
            LedgerEntry.entry_type == "REVERSAL"
        ).first()

        if refund:
            return {
                "amount": abs(float(refund.amount)),
                "date": refund.entry_date.strftime("%Y-%m-%d") if refund.entry_date else None
            }
        return None

    def _determine_status(
        self,
        balance: Decimal,
        refund: Optional[Dict],
        project_status: str
    ) -> Dict[str, str]:
        """确定项目余额状态"""
        if refund:
            return {"code": "refunded", "label": "已退款"}
        if project_status == "completed" and balance > 0:
            return {"code": "pending_refund", "label": "待退款"}
        if balance > 0:
            return {"code": "prepaid", "label": "客户预付"}
        if balance == 0:
            return {"code": "settled", "label": "已结清"}
        return {"code": "need_topup", "label": "需补款"}

    def _generate_note(
        self,
        status: Dict[str, str],
        balance: Decimal,
        refund: Optional[Dict]
    ) -> str:
        """生成备注说明"""
        code = status["code"]
        if code == "refunded" and refund:
            return f"已退款 ${refund['amount']:,.2f}"
        if code == "pending_refund":
            return f"项目结束，待退 ${balance:,.2f}"
        if code == "prepaid":
            return f"预付款剩余 ${balance:,.2f}"
        if code == "settled":
            return "已结清"
        if code == "need_topup":
            return f"需补款 ${abs(balance):,.2f}"
        return ""

    def _get_summary(self, items: List[Dict]) -> Dict[str, int]:
        """生成统计摘要"""
        return {
            "total_count": len(items),
            "prepaid_count": len([i for i in items if i["status"] == "prepaid"]),
            "pending_refund_count": len([i for i in items if i["status"] == "pending_refund"]),
            "refunded_count": len([i for i in items if i["status"] == "refunded"]),
            "settled_count": len([i for i in items if i["status"] == "settled"]),
            "need_topup_count": len([i for i in items if i["status"] == "need_topup"])
        }

    def _current_period(self) -> str:
        """获取当前月份"""
        return date.today().strftime("%Y-%m")
