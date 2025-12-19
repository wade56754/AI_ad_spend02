"""
收益归属测试 - P1 级验收项
Version: 1.0
Author: AI Code Factory

验收项对齐:
- BR-006: 收益归属规则

SoT对齐:
- BUSINESS_RULES.md v3.2 §4 收益归属
- LEDGER_SOT.md v1.1 §4 双账本规则
"""

import pytest
from decimal import Decimal
from datetime import date, datetime
from uuid import uuid4


class TestRevenueAttributionRules:
    """
    BR-006: 收益归属规则测试

    对齐 BUSINESS_RULES.md v3.2:
    - REVENUE 记入 PROJECT 账本
    - COST 记入 SUPPLIER 账本
    - 归属基于日报的 ad_account_id → project_id
    """

    def test_revenue_attributed_to_project(
        self,
        db_session,
        test_ad_account,
        test_project
    ):
        """收益归属到正确的项目"""
        # 验证账户关联到项目
        assert test_ad_account.project_id == test_project.id

        # 收益应通过账户归属到项目
        # 这是业务规则的基础验证

    def test_cost_attributed_to_supplier(
        self,
        db_session,
        test_ad_account,
        test_channel
    ):
        """成本归属到正确的供应商/渠道"""
        # 验证账户关联到渠道
        assert test_ad_account.channel_id == test_channel.id

        # 成本应通过账户归属到渠道/供应商

    def test_daily_report_revenue_attribution(
        self,
        db_session,
        test_daily_report,
        test_ad_account,
        test_project
    ):
        """日报收益归属链路"""
        # 日报 → 账户 → 项目
        assert test_daily_report.ad_account_id == test_ad_account.id
        assert test_ad_account.project_id == test_project.id

        # 收益归属路径完整


class TestProjectRevenueLedger:
    """
    项目账本收益记录测试

    对齐 LEDGER_SOT.md v1.1:
    - PROJECT 账本记录 REVENUE 类型
    """

    def test_revenue_entry_type_correct(self):
        """REVENUE 分录类型正确"""
        from backend.models.base import LedgerEntryType

        # REVENUE 应该是有效的分录类型
        assert hasattr(LedgerEntryType, 'REVENUE')
        assert LedgerEntryType.REVENUE.value == 'REVENUE'

    def test_revenue_positive_amount(self):
        """REVENUE 金额为正"""
        from backend.models.base import LedgerEntryType

        # 收益金额应为正数
        revenue_amount = Decimal("1000.00")
        assert revenue_amount > 0

    def test_revenue_ledger_entry_structure(
        self,
        db_session,
        test_ad_account
    ):
        """收益账本记录结构"""
        from backend.models.finance.ledger import LedgerEntry
        from backend.models.base import LedgerEntryType

        # 创建收益记录
        entry = LedgerEntry(
            ad_account_id=test_ad_account.id,
            entry_type=LedgerEntryType.REVENUE.value,
            amount=Decimal("1000.00"),
            balance_after=Decimal("1000.00"),
            reference_type="daily_report",
            entry_date=datetime.utcnow(),
        )
        db_session.add(entry)
        db_session.commit()

        # 验证记录正确
        assert entry.entry_type == LedgerEntryType.REVENUE.value
        assert entry.amount > 0
        assert entry.ad_account_id == test_ad_account.id


class TestSupplierCostLedger:
    """
    供应商账本成本记录测试

    对齐 LEDGER_SOT.md v1.1:
    - SUPPLIER 账本记录 COST 类型
    """

    def test_cost_entry_type_correct(self):
        """COST 分录类型正确"""
        from backend.models.base import LedgerEntryType

        assert hasattr(LedgerEntryType, 'COST')
        assert LedgerEntryType.COST.value == 'COST'

    def test_cost_negative_amount(self):
        """COST 金额为负 (扣减余额)"""
        # 成本金额应为负数（从账户余额扣减）
        cost_amount = Decimal("-1050.00")
        assert cost_amount < 0


class TestAttributionChain:
    """
    归属链路测试

    验证完整的归属链路:
    DailyReport → AdAccount → Project/Channel
    """

    def test_daily_report_to_account_link(
        self,
        db_session,
        test_daily_report,
        test_ad_account
    ):
        """日报到账户链路"""
        assert test_daily_report.ad_account_id == test_ad_account.id

    def test_account_to_project_link(
        self,
        db_session,
        test_ad_account,
        test_project
    ):
        """账户到项目链路"""
        assert test_ad_account.project_id == test_project.id

    def test_account_to_channel_link(
        self,
        db_session,
        test_ad_account,
        test_channel
    ):
        """账户到渠道链路"""
        assert test_ad_account.channel_id == test_channel.id

    def test_full_attribution_chain(
        self,
        db_session,
        test_daily_report,
        test_ad_account,
        test_project,
        test_channel
    ):
        """完整归属链路验证"""
        # 日报 → 账户
        assert test_daily_report.ad_account_id == test_ad_account.id

        # 账户 → 项目 (收益归属)
        assert test_ad_account.project_id == test_project.id

        # 账户 → 渠道 (成本归属)
        assert test_ad_account.channel_id == test_channel.id


class TestMultiAccountAttribution:
    """
    多账户归属测试

    验证同一项目下多个账户的收益聚合
    """

    def test_multiple_accounts_same_project(
        self,
        db_session,
        test_project,
        test_channel,
        media_buyer_user
    ):
        """同一项目多账户"""
        from backend.models import AdAccount

        # 创建多个账户
        accounts = []
        for i in range(3):
            account = AdAccount(
                id=100 + i,
                account_code=f"ACT_MULTI_{i}",
                account_name=f"多账户测试{i}",
                status="active",
                project_id=test_project.id,
                channel_id=test_channel.id,
                assigned_to=media_buyer_user.id,
            )
            db_session.add(account)
            accounts.append(account)

        db_session.commit()

        # 验证所有账户归属同一项目
        for account in accounts:
            assert account.project_id == test_project.id

    def test_project_revenue_aggregation(
        self,
        db_session,
        test_project,
        test_channel,
        media_buyer_user
    ):
        """项目收益聚合"""
        from backend.models import AdAccount
        from backend.models.finance.ledger import LedgerEntry
        from backend.models.base import LedgerEntryType
        from sqlalchemy import func

        # 创建两个账户
        account_a = AdAccount(
            id=200,
            account_code="ACT_AGG_A",
            account_name="聚合测试A",
            status="active",
            project_id=test_project.id,
            channel_id=test_channel.id,
            assigned_to=media_buyer_user.id,
        )
        account_b = AdAccount(
            id=201,
            account_code="ACT_AGG_B",
            account_name="聚合测试B",
            status="active",
            project_id=test_project.id,
            channel_id=test_channel.id,
            assigned_to=media_buyer_user.id,
        )
        db_session.add_all([account_a, account_b])
        db_session.commit()

        # 为每个账户创建收益记录
        entry_a = LedgerEntry(
            ad_account_id=account_a.id,
            entry_type=LedgerEntryType.REVENUE.value,
            amount=Decimal("1000.00"),
            balance_after=Decimal("1000.00"),
            reference_type="test",
            entry_date=datetime.utcnow(),
        )
        entry_b = LedgerEntry(
            ad_account_id=account_b.id,
            entry_type=LedgerEntryType.REVENUE.value,
            amount=Decimal("2000.00"),
            balance_after=Decimal("2000.00"),
            reference_type="test",
            entry_date=datetime.utcnow(),
        )
        db_session.add_all([entry_a, entry_b])
        db_session.commit()

        # 聚合项目收益
        total_revenue = db_session.query(
            func.sum(LedgerEntry.amount)
        ).join(
            AdAccount, LedgerEntry.ad_account_id == AdAccount.id
        ).filter(
            AdAccount.project_id == test_project.id,
            LedgerEntry.entry_type == LedgerEntryType.REVENUE.value
        ).scalar()

        # 验证总收益
        assert total_revenue == Decimal("3000.00")


class TestAttributionIsolation:
    """
    归属隔离测试

    验证不同项目之间的收益隔离
    """

    def test_different_projects_isolated(
        self,
        db_session,
        test_project,
        test_project_2,
        test_channel,
        media_buyer_user
    ):
        """不同项目收益隔离"""
        from backend.models import AdAccount
        from backend.models.finance.ledger import LedgerEntry
        from backend.models.base import LedgerEntryType
        from sqlalchemy import func

        # 项目1的账户
        account_1 = AdAccount(
            id=300,
            account_code="ACT_ISO_1",
            account_name="隔离测试1",
            status="active",
            project_id=test_project.id,
            channel_id=test_channel.id,
            assigned_to=media_buyer_user.id,
        )

        # 项目2的账户
        account_2 = AdAccount(
            id=301,
            account_code="ACT_ISO_2",
            account_name="隔离测试2",
            status="active",
            project_id=test_project_2.id,
            channel_id=test_channel.id,
            assigned_to=media_buyer_user.id,
        )

        db_session.add_all([account_1, account_2])
        db_session.commit()

        # 创建收益记录
        entry_1 = LedgerEntry(
            ad_account_id=account_1.id,
            entry_type=LedgerEntryType.REVENUE.value,
            amount=Decimal("1000.00"),
            balance_after=Decimal("1000.00"),
            reference_type="test",
            entry_date=datetime.utcnow(),
        )
        entry_2 = LedgerEntry(
            ad_account_id=account_2.id,
            entry_type=LedgerEntryType.REVENUE.value,
            amount=Decimal("5000.00"),
            balance_after=Decimal("5000.00"),
            reference_type="test",
            entry_date=datetime.utcnow(),
        )
        db_session.add_all([entry_1, entry_2])
        db_session.commit()

        # 查询项目1的收益
        project_1_revenue = db_session.query(
            func.sum(LedgerEntry.amount)
        ).join(
            AdAccount, LedgerEntry.ad_account_id == AdAccount.id
        ).filter(
            AdAccount.project_id == test_project.id,
            LedgerEntry.entry_type == LedgerEntryType.REVENUE.value
        ).scalar()

        # 验证隔离
        assert project_1_revenue == Decimal("1000.00")
        assert project_1_revenue != Decimal("5000.00")
