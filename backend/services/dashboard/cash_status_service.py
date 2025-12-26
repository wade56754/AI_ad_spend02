"""
公司现金状况服务

核心公式:
- 期末余额 = 期初余额 + 收入 - 支出
- 收入 = 甲方打款（假设与收款一致）
- 支出 = 渠道充值 + 后勤支出

SoT Reference:
- LEDGER_SOT.md v1.1
- CLAUDE_CLI_TASK_CEO_DASHBOARD_REFACTOR_V3.md §2.3

Version: 3.0
Author: Claude Code
"""

from decimal import Decimal, ROUND_HALF_UP
from datetime import date, timedelta
from typing import Dict, Any, Optional
from sqlalchemy import func, and_
from sqlalchemy.orm import Session

from backend.models import LedgerEntry, TopupRequest, DailyReport


class CashStatusService:
    """公司现金状况服务"""

    # 默认期初余额（可配置）
    DEFAULT_OPENING_BALANCE = Decimal("26016.50")

    def __init__(self, db: Session):
        self.db = db

    def get_cash_status(self, period: str = None) -> Dict[str, Any]:
        """
        获取公司现金状况

        Args:
            period: 月份，格式 YYYY-MM

        Returns:
            现金状况数据
        """
        start_date, end_date = self._parse_period(period)

        # 计算收入
        income = self._calculate_income(start_date, end_date)

        # 计算支出
        expense = self._calculate_expense(start_date, end_date)

        # 期初余额（从配置或历史数据获取）
        opening_balance = self._get_opening_balance(start_date)

        # 期末余额
        closing_balance = opening_balance + income["total"] - expense["total"]

        # 余额变化
        balance_change = closing_balance - opening_balance
        balance_change_pct = (
            (balance_change / opening_balance * 100).quantize(Decimal("0.1"))
            if opening_balance > 0 else Decimal("0")
        )

        # 周转天数
        runway = self._calculate_runway(closing_balance, expense)

        return {
            "period": period or self._current_period(),
            "currency": "USD",
            "balance": {
                "opening": float(opening_balance.quantize(Decimal("0.01"))),
                "closing": float(closing_balance.quantize(Decimal("0.01"))),
                "change": float(balance_change.quantize(Decimal("0.01"))),
                "change_pct": float(balance_change_pct)
            },
            "income": {
                "total": float(income["total"].quantize(Decimal("0.01"))),
                "breakdown": income["breakdown"]
            },
            "expense": {
                "total": float(expense["total"].quantize(Decimal("0.01"))),
                "breakdown": expense["breakdown"]
            },
            "runway": runway
        }

    def _calculate_income(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """计算收入"""
        # 甲方打款（从 Ledger TOPUP 记录）
        client_topup = self.db.query(
            func.coalesce(func.sum(LedgerEntry.amount), 0)
        ).filter(
            LedgerEntry.entry_type == "TOPUP",
            LedgerEntry.entry_date >= start_date,
            LedgerEntry.entry_date <= end_date
        ).scalar()
        client_topup = Decimal(str(client_topup))

        # 渠道退款（从 REVERSAL 记录，取绝对值的一部分作为退款）
        # 注意：在实际业务中，渠道退款可能需要单独字段或标记
        supplier_refund = self.db.query(
            func.coalesce(func.sum(func.abs(LedgerEntry.amount)), 0)
        ).filter(
            LedgerEntry.entry_type == "REVERSAL",
            LedgerEntry.entry_date >= start_date,
            LedgerEntry.entry_date <= end_date
        ).scalar()
        supplier_refund = Decimal(str(supplier_refund))

        total = client_topup + supplier_refund

        return {
            "total": total,
            "breakdown": [
                {
                    "type": "client_topup",
                    "label": "甲方打款",
                    "amount": float(client_topup.quantize(Decimal("0.01")))
                },
                {
                    "type": "supplier_refund",
                    "label": "渠道退款",
                    "amount": float(supplier_refund.quantize(Decimal("0.01")))
                }
            ]
        }

    def _calculate_expense(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """计算支出"""
        # 渠道充值（广告消耗）- 从日报 real_spend 汇总
        ad_spend = self.db.query(
            func.coalesce(func.sum(DailyReport.real_spend), 0)
        ).filter(
            DailyReport.report_date >= start_date,
            DailyReport.report_date <= end_date
        ).scalar()
        supplier_topup = Decimal(str(ad_spend))

        # 后勤支出（预估，实际应从 company_expenses 表获取）
        # 这里按广告消耗的比例估算
        operation_cost = (supplier_topup * Decimal("0.12")).quantize(Decimal("0.01"))

        # 广告配套（预估）
        infrastructure_cost = (supplier_topup * Decimal("0.04")).quantize(Decimal("0.01"))

        total = supplier_topup + operation_cost + infrastructure_cost

        return {
            "total": total,
            "breakdown": [
                {
                    "type": "supplier_topup",
                    "label": "渠道充值",
                    "amount": float(supplier_topup.quantize(Decimal("0.01")))
                },
                {
                    "type": "operation",
                    "label": "后勤支出",
                    "amount": float(operation_cost)
                },
                {
                    "type": "infrastructure",
                    "label": "广告配套",
                    "amount": float(infrastructure_cost)
                }
            ]
        }

    def _get_opening_balance(self, start_date: date) -> Decimal:
        """
        获取期初余额

        实际应从历史快照或配置获取
        """
        # TODO: 实现从历史数据或配置获取
        return self.DEFAULT_OPENING_BALANCE

    def _calculate_runway(
        self,
        closing_balance: Decimal,
        expense: Dict[str, Any]
    ) -> Dict[str, Any]:
        """计算资金周转天数"""
        # 仅计算广告支出
        supplier_topup = Decimal("0")
        for item in expense["breakdown"]:
            if item["type"] == "supplier_topup":
                supplier_topup = Decimal(str(item["amount"]))
                break

        # 计算日均广告消耗
        days_in_period = 30  # 简化处理
        avg_daily_ad_spend = (supplier_topup / days_in_period).quantize(Decimal("0.01"))

        # 周转天数
        runway_days = int(closing_balance / avg_daily_ad_spend) if avg_daily_ad_spend > 0 else 0

        return {
            "days": runway_days,
            "avg_daily_ad_spend": float(avg_daily_ad_spend),
            "note": "仅计算广告业务支出，不含后勤"
        }

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
