"""
Ledger Service 测试套件

测试财务总账服务的核心功能，包括：
- LedgerService 方法（create_transaction, get_transactions, get_account_balance）
- LedgerEntry 模型 CRUD（Model-Level Sanity Check）
- 余额计算与序列一致性

对齐：
- LEDGER_SOT.md v1.1
- DATA_SCHEMA.md v5.2

NOTE: 本文件聚焦 Service 层和 Model 层基础功能测试。
      不可变量（金额方向、账本隔离）测试见 test_ledger_invariants.py
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta

from backend.models.finance.ledger import LedgerEntry
from backend.models.base import LedgerEntryType


# =============================================================================
# 固定时间基准（避免 datetime.now() 脆弱性）
# =============================================================================
BASE_TIME = datetime(2025, 1, 15, 12, 0, 0)


# =============================================================================
# 本地 Fixtures（补充 conftest.py 中缺失的）
# =============================================================================

@pytest.fixture
def test_ledger_entry(db_session, test_ad_account):
    """创建单条 TOPUP 类型的测试分录"""
    entry = LedgerEntry(
        ad_account_id=test_ad_account.id,
        entry_type=LedgerEntryType.TOPUP.value,
        amount=Decimal("5000.00"),
        balance_after=Decimal("5000.00"),
        reference_type="topup",
        notes="测试充值分录",
        entry_date=BASE_TIME,
    )
    db_session.add(entry)
    db_session.commit()
    db_session.refresh(entry)
    return entry


@pytest.fixture
def test_project_ledger_entry(db_session, test_ad_account):
    """创建 PROJECT 账本收入分录（REVENUE）"""
    entry = LedgerEntry(
        ad_account_id=test_ad_account.id,
        entry_type=LedgerEntryType.REVENUE.value,
        amount=Decimal("10000.00"),
        balance_after=Decimal("10000.00"),
        reference_type="daily_report",
        notes="测试收入分录 - PROJECT 账本",
        entry_date=BASE_TIME,
    )
    db_session.add(entry)
    db_session.commit()
    db_session.refresh(entry)
    return entry


@pytest.fixture
def test_supplier_ledger_entry(db_session, test_ad_account):
    """创建 SUPPLIER 账本成本分录（COST）"""
    entry = LedgerEntry(
        ad_account_id=test_ad_account.id,
        entry_type=LedgerEntryType.COST.value,
        amount=Decimal("-8000.00"),  # COST 必须为负数
        balance_after=Decimal("-8000.00"),
        reference_type="supplier_cost",
        notes="测试成本分录 - SUPPLIER 账本",
        entry_date=BASE_TIME,
    )
    db_session.add(entry)
    db_session.commit()
    db_session.refresh(entry)
    return entry


@pytest.fixture
def test_ledger_entries_batch(db_session, test_ad_account):
    """
    创建一批测试分录用于余额计算测试

    交易序列：
    1. TOPUP   +10000.00  (balance: 10000)
    2. REVENUE  +5000.00  (balance: 15000)
    3. COST     -2000.00  (balance: 13000)
    4. COST     -1000.00  (balance: 12000)

    最终余额：12000.00
    """
    entries = []
    balance = Decimal("0.00")

    transactions = [
        (LedgerEntryType.TOPUP, Decimal("10000.00"), BASE_TIME),
        (LedgerEntryType.REVENUE, Decimal("5000.00"), BASE_TIME + timedelta(hours=1)),
        (LedgerEntryType.COST, Decimal("-2000.00"), BASE_TIME + timedelta(hours=2)),
        (LedgerEntryType.COST, Decimal("-1000.00"), BASE_TIME + timedelta(hours=3)),
    ]

    for entry_type, amount, entry_date in transactions:
        balance += amount
        entry = LedgerEntry(
            ad_account_id=test_ad_account.id,
            entry_type=entry_type.value,
            amount=amount,
            balance_after=balance,
            entry_date=entry_date,
        )
        db_session.add(entry)
        entries.append(entry)

    db_session.commit()
    for e in entries:
        db_session.refresh(e)

    return entries


# =============================================================================
# Model-Level Sanity Check（LedgerEntry 模型基础 CRUD）
# =============================================================================

class TestLedgerEntryModelCRUD:
    """LedgerEntry 模型基础 CRUD 测试（Model-Level Sanity Check）"""

    def test_create_revenue_entry(self, db_session, test_ad_account, test_project):
        """
        测试创建收入分录（PROJECT 账本）
        对齐: LEDGER_SOT.md v1.1 §2.2.1 - REVENUE 必须为正数
        """
        entry = LedgerEntry(
            ad_account_id=test_ad_account.id,
            entry_type=LedgerEntryType.REVENUE.value,
            amount=Decimal("10000.00"),
            balance_after=Decimal("10000.00"),
            reference_id=test_project.id,
            reference_type="project",
            notes="测试收入分录",
            entry_date=BASE_TIME,
        )
        db_session.add(entry)
        db_session.commit()
        db_session.refresh(entry)

        # 验证持久化成功
        assert entry.id is not None
        assert entry.entry_type == LedgerEntryType.REVENUE.value
        assert entry.amount == Decimal("10000.00")
        assert entry.balance_after == Decimal("10000.00")
        assert entry.ad_account_id == test_ad_account.id
        # 验证 helper property
        assert entry.is_revenue is True
        assert entry.is_cost is False

    def test_create_cost_entry(self, db_session, test_ad_account):
        """
        测试创建成本分录（SUPPLIER 账本）
        对齐: LEDGER_SOT.md v1.1 §4.1 - COST 必须为负数
        """
        entry = LedgerEntry(
            ad_account_id=test_ad_account.id,
            entry_type=LedgerEntryType.COST.value,
            amount=Decimal("-5000.00"),  # COST 必须为负数
            balance_after=Decimal("-5000.00"),
            reference_type="supplier_cost",
            notes="测试成本分录",
            entry_date=BASE_TIME,
        )
        db_session.add(entry)
        db_session.commit()
        db_session.refresh(entry)

        assert entry.id is not None
        assert entry.entry_type == LedgerEntryType.COST.value
        assert entry.amount == Decimal("-5000.00")
        assert entry.is_cost is True
        assert entry.is_revenue is False

    def test_create_topup_entry(self, db_session, test_ad_account):
        """
        测试创建充值分录（两账本通用）
        对齐: LEDGER_SOT.md v1.1 §4.1 - TOPUP 必须为正数
        """
        entry = LedgerEntry(
            ad_account_id=test_ad_account.id,
            entry_type=LedgerEntryType.TOPUP.value,
            amount=Decimal("20000.00"),
            balance_after=Decimal("20000.00"),
            reference_type="topup",
            notes="测试充值分录",
            entry_date=BASE_TIME,
        )
        db_session.add(entry)
        db_session.commit()
        db_session.refresh(entry)

        assert entry.id is not None
        assert entry.entry_type == LedgerEntryType.TOPUP.value
        assert entry.amount == Decimal("20000.00")
        assert entry.is_topup is True

    def test_create_transfer_out_entry(self, db_session, test_ad_account):
        """
        测试创建转出分录（SUPPLIER 账本专用）
        对齐: LEDGER_SOT.md v1.1 §4.1 - TRANSFER_OUT 必须为负数
        """
        entry = LedgerEntry(
            ad_account_id=test_ad_account.id,
            entry_type=LedgerEntryType.TRANSFER_OUT.value,
            amount=Decimal("-1500.00"),  # TRANSFER_OUT 必须为负数
            balance_after=Decimal("-1500.00"),
            reference_type="transfer",
            notes="死号余额迁出",
            entry_date=BASE_TIME,
        )
        db_session.add(entry)
        db_session.commit()
        db_session.refresh(entry)

        assert entry.id is not None
        assert entry.entry_type == LedgerEntryType.TRANSFER_OUT.value
        assert entry.amount == Decimal("-1500.00")

    def test_create_transfer_in_entry(self, db_session, test_ad_account):
        """
        测试创建转入分录（SUPPLIER 账本专用）
        对齐: LEDGER_SOT.md v1.1 §4.1 - TRANSFER_IN 必须为正数
        """
        entry = LedgerEntry(
            ad_account_id=test_ad_account.id,
            entry_type=LedgerEntryType.TRANSFER_IN.value,
            amount=Decimal("1500.00"),  # TRANSFER_IN 必须为正数
            balance_after=Decimal("1500.00"),
            reference_type="transfer",
            notes="死号余额迁入",
            entry_date=BASE_TIME,
        )
        db_session.add(entry)
        db_session.commit()
        db_session.refresh(entry)

        assert entry.id is not None
        assert entry.entry_type == LedgerEntryType.TRANSFER_IN.value
        assert entry.amount == Decimal("1500.00")

    def test_create_reversal_entry(self, db_session, test_ad_account):
        """
        测试创建红冲分录（两账本通用）
        对齐: LEDGER_SOT.md v1.1 §4.1 - REVERSAL 方向取决于原记录
        """
        entry = LedgerEntry(
            ad_account_id=test_ad_account.id,
            entry_type=LedgerEntryType.REVERSAL.value,
            amount=Decimal("-500.00"),  # 红冲原 TOPUP +500 的记录
            balance_after=Decimal("-500.00"),
            reference_type="reversal",
            notes="红冲原充值记录",
            entry_date=BASE_TIME,
        )
        db_session.add(entry)
        db_session.commit()
        db_session.refresh(entry)

        assert entry.id is not None
        assert entry.entry_type == LedgerEntryType.REVERSAL.value
        assert entry.amount == Decimal("-500.00")


# =============================================================================
# LedgerEntry 查询方法测试
# =============================================================================

class TestLedgerEntryQueryMethods:
    """LedgerEntry 模型查询方法测试"""

    def test_get_account_balance(self, db_session, test_ad_account, test_ledger_entries_batch):
        """
        测试获取账户余额
        对齐: LEDGER_SOT.md v1.1 §2.4 - 余额通过 SUM 聚合计算
        """
        balance = LedgerEntry.get_account_balance(db_session, test_ad_account.id)

        # 验证：10000 + 5000 - 2000 - 1000 = 12000
        assert balance == Decimal("12000.00")

    def test_get_account_ledger(self, db_session, test_ad_account, test_ledger_entries_batch):
        """测试获取账户流水记录"""
        entries = LedgerEntry.get_account_ledger(db_session, test_ad_account.id, limit=10)

        # 验证返回数量
        assert len(entries) == 4
        # 验证排序（按 entry_date 降序）
        for i in range(len(entries) - 1):
            assert entries[i].entry_date >= entries[i + 1].entry_date

    def test_get_account_ledger_with_limit(self, db_session, test_ad_account, test_ledger_entries_batch):
        """测试获取账户流水记录（带 limit）"""
        entries = LedgerEntry.get_account_ledger(db_session, test_ad_account.id, limit=2)

        # 验证限制生效
        assert len(entries) == 2

    def test_get_date_range_entries(self, db_session, test_ad_account, test_ledger_entries_batch):
        """
        测试获取日期范围流水
        使用固定时间范围避免脆弱性
        """
        start_date = BASE_TIME
        end_date = BASE_TIME + timedelta(hours=4)

        entries = LedgerEntry.get_date_range_entries(
            db_session, test_ad_account.id, start_date, end_date
        )

        # 验证
        assert len(entries) == 4
        for entry in entries:
            assert start_date <= entry.entry_date <= end_date


# =============================================================================
# 余额计算与序列一致性测试
# =============================================================================

class TestBalanceCalculation:
    """余额计算序列一致性测试"""

    def test_balance_calculation_sequence(self, db_session, test_ad_account):
        """
        测试余额计算序列（多笔交易）
        对齐: LEDGER_SOT.md v1.1 §2.4 - 余额必须与分录序列一致
        """
        entries = []
        current_balance = Decimal("0.00")

        # 第一笔：充值 10000
        entry1 = LedgerEntry(
            ad_account_id=test_ad_account.id,
            entry_type=LedgerEntryType.TOPUP.value,
            amount=Decimal("10000.00"),
            balance_after=current_balance + Decimal("10000.00"),
            entry_date=BASE_TIME,
        )
        db_session.add(entry1)
        current_balance += Decimal("10000.00")
        entries.append(entry1)

        # 第二笔：收入 5000
        entry2 = LedgerEntry(
            ad_account_id=test_ad_account.id,
            entry_type=LedgerEntryType.REVENUE.value,
            amount=Decimal("5000.00"),
            balance_after=current_balance + Decimal("5000.00"),
            entry_date=BASE_TIME + timedelta(hours=1),
        )
        db_session.add(entry2)
        current_balance += Decimal("5000.00")
        entries.append(entry2)

        # 第三笔：成本 -2000
        entry3 = LedgerEntry(
            ad_account_id=test_ad_account.id,
            entry_type=LedgerEntryType.COST.value,
            amount=Decimal("-2000.00"),
            balance_after=current_balance + Decimal("-2000.00"),
            entry_date=BASE_TIME + timedelta(hours=2),
        )
        db_session.add(entry3)
        current_balance += Decimal("-2000.00")
        entries.append(entry3)

        db_session.commit()

        # 验证最终余额
        final_balance = LedgerEntry.get_account_balance(db_session, test_ad_account.id)
        assert final_balance == Decimal("13000.00")  # 10000 + 5000 - 2000

    def test_balance_after_matches_cumulative_sum(self, db_session, test_ad_account, test_ledger_entries_batch):
        """
        测试 balance_after 与累计金额一致
        对齐: LEDGER_SOT.md v1.1 - 余额快照验证
        """
        entries = LedgerEntry.get_account_ledger(db_session, test_ad_account.id, limit=100)

        # 从最早开始计算累计余额
        sorted_entries = sorted(entries, key=lambda e: e.entry_date)
        calculated_balance = Decimal("0.00")

        for entry in sorted_entries:
            calculated_balance += entry.amount
            assert entry.balance_after == calculated_balance, \
                f"Entry {entry.id}: balance_after={entry.balance_after}, expected={calculated_balance}"


# =============================================================================
# LedgerEntry 属性测试
# =============================================================================

class TestLedgerEntryProperties:
    """LedgerEntry 模型属性测试"""

    def test_entry_type_enum_property(self, db_session, test_ledger_entry):
        """测试分录类型枚举属性"""
        assert test_ledger_entry.entry_type_enum == LedgerEntryType.TOPUP
        assert isinstance(test_ledger_entry.entry_type_enum, LedgerEntryType)

    def test_entry_type_boolean_properties_project(self, db_session, test_project_ledger_entry):
        """
        测试分录类型布尔属性（PROJECT 账本分录）
        对齐: LEDGER_SOT.md v1.1 §2.2.1 - PROJECT 账本只允许 REVENUE/TOPUP/REVERSAL
        """
        assert test_project_ledger_entry.is_revenue is True
        assert test_project_ledger_entry.is_cost is False
        assert test_project_ledger_entry.is_topup is False

    def test_entry_type_boolean_properties_supplier(self, db_session, test_supplier_ledger_entry):
        """
        测试分录类型布尔属性（SUPPLIER 账本分录）
        对齐: LEDGER_SOT.md v1.1 §2.2.2 - SUPPLIER 账本只允许 COST/TOPUP/TRANSFER_*/REVERSAL
        """
        assert test_supplier_ledger_entry.is_cost is True
        assert test_supplier_ledger_entry.is_revenue is False
        assert test_supplier_ledger_entry.is_topup is False


# =============================================================================
# LedgerService 方法测试（Service-Level）
# NOTE: 由于 LedgerService 使用 get_db_session() 内部管理会话，
#       这些测试需要 mock 或配置测试数据库环境才能运行
#       以下为测试框架，实际执行需要相应的测试基础设施
# =============================================================================

class TestLedgerServiceMethods:
    """
    LedgerService 方法测试

    NOTE: LedgerService 内部使用 get_db_session() context manager，
          需要配置测试环境或 mock 才能正确测试。
          以下测试标记为 skip，待集成测试环境就绪后启用。
    """

    @pytest.mark.skip(reason="需要配置 LedgerService 测试环境（mock get_db_session 或使用测试数据库）")
    def test_create_transaction_topup(self, db_session, test_project, test_ad_account):
        """
        测试 LedgerService.create_transaction (TOPUP 类型)
        对齐: LEDGER_SOT.md v1.1 §8 - 项目充值流程
        """
        from backend.services.ledger_service import LedgerService
        from backend.models.ledger import TransactionType

        transaction = LedgerService.create_transaction(
            transaction_type=TransactionType.TOPUP,
            amount=Decimal("10000.00"),
            currency="CNY",
            project_id=test_project.id,
            account_id=test_ad_account.id,
            description="测试充值"
        )

        assert transaction is not None
        assert transaction.transaction_type == TransactionType.TOPUP
        assert transaction.amount == Decimal("10000.00")
        assert transaction.currency == "CNY"

    @pytest.mark.skip(reason="需要配置 LedgerService 测试环境")
    def test_get_account_balance_service(self, db_session, test_ad_account):
        """
        测试 LedgerService.get_account_balance
        对齐: LEDGER_SOT.md v1.1 §2.4 - 余额唯一真相源
        """
        from backend.services.ledger_service import LedgerService

        balance_info = LedgerService.get_account_balance(account_id=test_ad_account.id)

        if balance_info:
            assert "current_balance" in balance_info
            assert "available_balance" in balance_info
            assert "frozen_balance" in balance_info

    @pytest.mark.skip(reason="需要配置 LedgerService 测试环境")
    def test_get_transactions_with_filters(self, db_session, test_project):
        """
        测试 LedgerService.get_transactions（带过滤条件）
        """
        from backend.services.ledger_service import LedgerService
        from backend.models.ledger import TransactionType, TransactionStatus

        response = LedgerService.get_transactions(
            project_id=test_project.id,
            transaction_type=TransactionType.TOPUP,
            status=TransactionStatus.COMPLETED,
            page=1,
            size=10
        )

        assert response is not None
        assert hasattr(response, 'items')
        assert hasattr(response, 'total')
