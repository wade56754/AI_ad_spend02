"""
SQLAlchemy 模型 Mock 构建工具
提供统一的 Mock 对象构建方法，确保 Mock 配置与实际模型一致
"""

from unittest.mock import Mock, MagicMock
from typing import Dict, Any, Optional
from decimal import Decimal
from datetime import date, datetime
from uuid import uuid4


class SQLAlchemyMockBuilder:
    """SQLAlchemy 模型 Mock 构建器"""

    @staticmethod
    def build_ad_account(
        account_code: str = "acc_test_001",
        account_name: str = "测试账户",
        status: str = "active",
        project_id: int = 1,
        channel_id: Any = None,
        assigned_to: int = 50,
        balance: Decimal = None,
        daily_budget: Decimal = None,
        total_budget: Decimal = None,
        **kwargs
    ) -> Mock:
        """
        构建 AdAccount Mock 对象

        Args:
            account_code: 账户代码
            account_name: 账户名称
            status: 账户状态
            project_id: 项目ID
            channel_id: 渠道ID
            assigned_to: 负责人ID
            balance: 账户余额
            daily_budget: 日预算 (测试用，实际模型暂无此字段)
            total_budget: 总预算 (测试用，实际模型暂无此字段)
            **kwargs: 其他字段

        Returns:
            Mock 对象，包含所有必要字段
        """
        from backend.models import AdAccount

        # 使用 MagicMock 以便支持尚未在模型中定义的字段
        mock = MagicMock(spec=AdAccount)
        mock.id = kwargs.get('id', 1)
        mock.account_code = account_code
        mock.account_name = account_name
        mock.status = status
        mock.project_id = project_id
        mock.channel_id = channel_id or uuid4()
        mock.assigned_to = assigned_to
        mock.assigned_user_id = assigned_to  # 向后兼容属性
        mock.balance = balance or Decimal("25000.00")
        mock.opened_at = kwargs.get('opened_at', None)
        mock.died_at = kwargs.get('died_at', None)
        mock.death_reason = kwargs.get('death_reason', None)
        mock.death_loss = kwargs.get('death_loss', None)
        mock.notes = kwargs.get('notes', None)
        mock.version = kwargs.get('version', 1)
        mock.created_at = kwargs.get('created_at', datetime.utcnow())
        mock.updated_at = kwargs.get('updated_at', None)

        # 预算字段 (测试用，未来可能加入模型)
        mock.daily_budget = daily_budget or Decimal("1000.00")
        mock.total_budget = total_budget or Decimal("30000.00")

        # 状态相关时间字段
        mock.activated_date = kwargs.get('activated_date', None)
        mock.suspended_date = kwargs.get('suspended_date', None)

        # 设置其他字段
        for key, value in kwargs.items():
            if not hasattr(mock, key):
                setattr(mock, key, value)

        return mock

    @staticmethod
    def build_account_performance(
        ad_account_id: int = 1,
        report_date: date = None,
        spend: Decimal = None,
        conversions: int = 0,
        impressions: int = 0,
        clicks: int = 0,
        revenue: Decimal = None,
        **kwargs
    ) -> Mock:
        """
        构建 AccountPerformance Mock 对象

        Args:
            ad_account_id: 广告账户ID
            report_date: 报告日期
            spend: 消耗金额
            conversions: 转化数
            impressions: 展示数
            clicks: 点击数
            revenue: 收入
            **kwargs: 其他字段

        Returns:
            Mock 对象
        """
        from backend.models import AccountPerformance

        mock = Mock(spec=AccountPerformance)
        mock.id = kwargs.get('id', 1)
        mock.ad_account_id = ad_account_id
        mock.date = report_date or date.today()
        mock.spend = spend or Decimal("1000.00")
        mock.conversions = conversions
        mock.impressions = impressions
        mock.clicks = clicks
        mock.revenue = revenue or Decimal("0.00")
        mock.ctr = kwargs.get('ctr', None)
        mock.cpc = kwargs.get('cpc', None)
        mock.cpa = kwargs.get('cpa', None)
        mock.roas = kwargs.get('roas', None)
        mock.created_at = kwargs.get('created_at', datetime.utcnow())
        mock.updated_at = kwargs.get('updated_at', None)

        # 设置其他字段
        for key, value in kwargs.items():
            if not hasattr(mock, key):
                setattr(mock, key, value)

        return mock

    @staticmethod
    def build_ledger_entry(
        entry_type: str = "REVENUE",
        amount: Decimal = None,
        ad_account_id: int = 1,
        **kwargs
    ) -> Mock:
        """
        构建 LedgerEntry Mock 对象

        Args:
            entry_type: 条目类型 (使用 LedgerEntryType 枚举值)
            amount: 金额
            ad_account_id: 广告账户ID
            **kwargs: 其他字段 (reference_id, notes, entity_type, entity_id, etc.)

        Returns:
            Mock 对象

        Note:
            数据库实际字段 (DATA_SCHEMA.md v5.10):
            - id, ledger_type, project_id, supplier_id, ad_account_id
            - entry_type, amount, currency, reference_id
            - occurred_at, created_by, notes, created_at
            - entity_type, entity_id, event_id, idempotency_key, direction, entry_date

            已移除不存在的字段: balance_after, reference_type
        """
        from backend.models import LedgerEntry

        mock = Mock(spec=LedgerEntry)
        mock.id = kwargs.get('id', 1)
        mock.entry_type = entry_type
        mock.amount = amount or Decimal("1000.00")
        mock.ad_account_id = ad_account_id
        mock.reference_id = kwargs.get('reference_id', None)
        mock.notes = kwargs.get('notes', None)
        mock.entry_date = kwargs.get('entry_date', datetime.utcnow())
        mock.created_at = kwargs.get('created_at', datetime.utcnow())

        # 实际数据库字段
        mock.ledger_type = kwargs.get('ledger_type', None)
        mock.project_id = kwargs.get('project_id', None)
        mock.supplier_id = kwargs.get('supplier_id', None)
        mock.currency = kwargs.get('currency', 'CNY')
        mock.occurred_at = kwargs.get('occurred_at', None)
        mock.created_by = kwargs.get('created_by', None)
        mock.entity_type = kwargs.get('entity_type', None)
        mock.entity_id = kwargs.get('entity_id', None)
        mock.event_id = kwargs.get('event_id', None)
        mock.idempotency_key = kwargs.get('idempotency_key', None)
        mock.direction = kwargs.get('direction', None)

        # 设置其他字段
        for key, value in kwargs.items():
            if not hasattr(mock, key):
                setattr(mock, key, value)

        return mock

    @staticmethod
    def build_daily_report(
        ad_account_id: int = 1,
        report_date: date = None,
        status: str = "final_confirmed",
        conversions_raw: int = 0,
        conversions_final: int = 0,
        raw_spend: Decimal = None,
        real_spend: Decimal = None,
        **kwargs
    ) -> Mock:
        """
        构建 DailyReport Mock 对象

        Args:
            ad_account_id: 广告账户ID
            report_date: 报告日期
            status: 状态
            conversions_raw: 原始粉数
            conversions_final: 最终粉数
            raw_spend: 原始消耗
            real_spend: 真实消耗
            **kwargs: 其他字段

        Returns:
            Mock 对象
        """
        from backend.models import DailyReport

        mock = Mock(spec=DailyReport)
        mock.id = kwargs.get('id', 1)
        mock.ad_account_id = ad_account_id
        mock.report_date = report_date or date.today()
        mock.status = status
        mock.conversions_raw = conversions_raw
        mock.conversions_final = conversions_final
        mock.raw_spend = raw_spend or Decimal("1000.00")
        mock.real_spend = real_spend or Decimal("1000.00")
        mock.fee = kwargs.get('fee', Decimal("0.00"))
        mock.unit_price = kwargs.get('unit_price', Decimal("10.00"))
        mock.impressions = kwargs.get('impressions', 0)
        mock.clicks = kwargs.get('clicks', 0)
        mock.submitted_by = kwargs.get('submitted_by', None)
        mock.reviewed_by = kwargs.get('reviewed_by', None)
        mock.notes = kwargs.get('notes', None)
        mock.created_at = kwargs.get('created_at', datetime.utcnow())
        mock.updated_at = kwargs.get('updated_at', None)

        # 设置其他字段
        for key, value in kwargs.items():
            if not hasattr(mock, key):
                setattr(mock, key, value)

        return mock

    @staticmethod
    def build_project(
        project_id: int = 1,
        name: str = "测试项目",
        status: str = "active",
        **kwargs
    ) -> Mock:
        """
        构建 Project Mock 对象

        Args:
            project_id: 项目ID
            name: 项目名称
            status: 项目状态
            **kwargs: 其他字段

        Returns:
            Mock 对象
        """
        from backend.models import Project

        mock = Mock(spec=Project)
        mock.id = project_id
        mock.name = name
        mock.status = status
        mock.account_manager_id = kwargs.get('account_manager_id', None)
        mock.created_at = kwargs.get('created_at', datetime.utcnow())
        mock.updated_at = kwargs.get('updated_at', None)

        # 设置其他字段
        for key, value in kwargs.items():
            if not hasattr(mock, key):
                setattr(mock, key, value)

        return mock

    @staticmethod
    def build_channel(
        channel_id: Any = None,
        name: str = "测试渠道",
        status: str = "active",
        **kwargs
    ) -> Mock:
        """
        构建 Channel Mock 对象

        Args:
            channel_id: 渠道ID (UUID)
            name: 渠道名称
            status: 渠道状态
            **kwargs: 其他字段

        Returns:
            Mock 对象
        """
        from backend.models import Channel

        mock = Mock(spec=Channel)
        mock.id = channel_id or uuid4()
        mock.name = name
        mock.status = status
        mock.created_at = kwargs.get('created_at', datetime.utcnow())
        mock.updated_at = kwargs.get('updated_at', None)

        # 设置其他字段
        for key, value in kwargs.items():
            if not hasattr(mock, key):
                setattr(mock, key, value)

        return mock


# 使用示例
if __name__ == "__main__":
    # 示例：创建 AdAccount Mock
    account = SQLAlchemyMockBuilder.build_ad_account(
        account_code="acc_123",
        account_name="测试账户",
        status="active"
    )
    print(f"Account: {account.account_code}, {account.account_name}")

    # 示例：创建 AccountPerformance Mock
    performance = SQLAlchemyMockBuilder.build_account_performance(
        ad_account_id=1,
        spend=Decimal("5000.00"),
        conversions=100
    )
    print(f"Performance: spend={performance.spend}, conversions={performance.conversions}")

    # 示例：创建 LedgerEntry Mock
    from backend.models.enums import LedgerEntryType
    ledger = SQLAlchemyMockBuilder.build_ledger_entry(
        entry_type=LedgerEntryType.REVENUE.value,
        amount=Decimal("10000.00")
    )
    print(f"Ledger: type={ledger.entry_type}, amount={ledger.amount}")

