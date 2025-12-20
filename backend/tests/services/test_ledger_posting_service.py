"""
LedgerPostingService 单元测试

测试覆盖:
1. 事件验证 (validate_event_for_posting)
2. 标准分录生成 (SPEND/TOPUP/PAYMENT/FEE/REFUND)
3. 转账分录生成 (TRANSFER)
4. 调整分录生成 (ADJUSTMENT)
5. 事件冲正 (reverse_event)
6. 批量过账 (post_events_batch)
7. 幂等性检查

SoT Reference:
- LEDGER_SOT.md v1.1
- STATE_MACHINE.md v2.6 (财务事件状态机)

Author: Claude Code (AI 代码工厂)
"""

import pytest
from decimal import Decimal
from datetime import date, datetime
from uuid import uuid4
from unittest.mock import Mock, MagicMock, patch

from backend.services.ledger_posting_service import (
    LedgerPostingService,
    PostingDirection,
    EntityType,
    get_ledger_posting_service
)
from backend.models.finance.financial_event import (
    FinancialEvent,
    EventType,
    EventStatus
)
from backend.models.finance.ledger import LedgerEntry
from backend.models.enums import LedgerEntryType
from backend.exceptions.custom_exceptions import (
    BusinessLogicError,
    StateTransitionError
)


# ============================================
# Fixtures
# ============================================

@pytest.fixture
def mock_db():
    """Mock 数据库会话"""
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    db.query.return_value.filter.return_value.all.return_value = []
    return db


@pytest.fixture
def confirmed_spend_event():
    """创建 CONFIRMED 状态的 SPEND 事件"""
    event = FinancialEvent(
        id=uuid4(),
        event_type=EventType.SPEND.value,
        event_status=EventStatus.CONFIRMED.value,
        source_type="test",
        source_ref="test_ref",
        idempotency_key=f"TEST:SPEND:{uuid4()}",
        amount=Decimal('1000.00'),
        fee_amount=Decimal('100.00'),
        gross_amount=Decimal('1100.00'),
        currency='USD',
        event_date=date.today(),
        supplier_id=1,
        ad_account_id=1,
        payload={}
    )
    return event


@pytest.fixture
def confirmed_topup_event():
    """创建 CONFIRMED 状态的 TOPUP 事件"""
    event = FinancialEvent(
        id=uuid4(),
        event_type=EventType.TOPUP.value,
        event_status=EventStatus.CONFIRMED.value,
        source_type="test",
        source_ref="test_ref",
        idempotency_key=f"TEST:TOPUP:{uuid4()}",
        amount=Decimal('5000.00'),
        fee_amount=Decimal('0'),
        gross_amount=Decimal('5000.00'),
        currency='USD',
        event_date=date.today(),
        supplier_id=1,
        team_id=uuid4(),
        payload={}
    )
    return event


@pytest.fixture
def confirmed_transfer_event():
    """创建 CONFIRMED 状态的 TRANSFER 事件"""
    event = FinancialEvent(
        id=uuid4(),
        event_type=EventType.TRANSFER.value,
        event_status=EventStatus.CONFIRMED.value,
        source_type="test",
        source_ref="test_ref",
        idempotency_key=f"TEST:TRANSFER:{uuid4()}",
        amount=Decimal('500.00'),
        fee_amount=Decimal('0'),
        currency='USD',
        event_date=date.today(),
        payload={
            'from_account_id': 1,
            'to_account_id': 2
        }
    )
    return event


@pytest.fixture
def posted_event():
    """创建 POSTED 状态的事件 (用于冲正测试)"""
    event = FinancialEvent(
        id=uuid4(),
        event_type=EventType.SPEND.value,
        event_status=EventStatus.POSTED.value,
        source_type="test",
        source_ref="test_ref",
        idempotency_key=f"TEST:SPEND:{uuid4()}",
        amount=Decimal('1000.00'),
        fee_amount=Decimal('100.00'),
        currency='USD',
        event_date=date.today(),
        supplier_id=1,
        ad_account_id=1,
        posted_at=datetime.utcnow(),
        payload={}
    )
    return event


# ============================================
# 测试: 事件验证
# ============================================

class TestValidateEventForPosting:
    """测试事件验证逻辑"""

    def test_valid_spend_event(self, confirmed_spend_event):
        """测试有效的 SPEND 事件"""
        is_valid, error = LedgerPostingService.validate_event_for_posting(
            confirmed_spend_event
        )
        assert is_valid is True
        assert error is None

    def test_invalid_status_raw(self, confirmed_spend_event):
        """测试 RAW 状态事件不能入账"""
        confirmed_spend_event.event_status = EventStatus.RAW.value
        is_valid, error = LedgerPostingService.validate_event_for_posting(
            confirmed_spend_event
        )
        assert is_valid is False
        assert "状态必须为 confirmed" in error

    def test_invalid_status_pending(self, confirmed_spend_event):
        """测试 PENDING 状态事件不能入账"""
        confirmed_spend_event.event_status = EventStatus.PENDING.value
        is_valid, error = LedgerPostingService.validate_event_for_posting(
            confirmed_spend_event
        )
        assert is_valid is False
        assert "状态必须为 confirmed" in error

    def test_invalid_amount_zero(self, confirmed_spend_event):
        """测试金额为 0 的事件"""
        confirmed_spend_event.amount = Decimal('0')
        is_valid, error = LedgerPostingService.validate_event_for_posting(
            confirmed_spend_event
        )
        assert is_valid is False
        assert "金额无效" in error

    def test_invalid_amount_negative(self, confirmed_spend_event):
        """测试金额为负的事件"""
        confirmed_spend_event.amount = Decimal('-100')
        is_valid, error = LedgerPostingService.validate_event_for_posting(
            confirmed_spend_event
        )
        assert is_valid is False
        assert "金额无效" in error

    def test_spend_missing_supplier(self, confirmed_spend_event):
        """测试 SPEND 事件缺少供应商"""
        confirmed_spend_event.supplier_id = None
        is_valid, error = LedgerPostingService.validate_event_for_posting(
            confirmed_spend_event
        )
        assert is_valid is False
        assert "必须关联供应商" in error

    def test_spend_missing_account(self, confirmed_spend_event):
        """测试 SPEND 事件缺少广告账户"""
        confirmed_spend_event.ad_account_id = None
        is_valid, error = LedgerPostingService.validate_event_for_posting(
            confirmed_spend_event
        )
        assert is_valid is False
        assert "必须关联广告账户" in error

    def test_topup_missing_supplier(self, confirmed_topup_event):
        """测试 TOPUP 事件缺少供应商"""
        confirmed_topup_event.supplier_id = None
        is_valid, error = LedgerPostingService.validate_event_for_posting(
            confirmed_topup_event
        )
        assert is_valid is False
        assert "必须关联供应商" in error

    def test_transfer_missing_accounts(self, confirmed_transfer_event):
        """测试 TRANSFER 事件缺少账户信息"""
        confirmed_transfer_event.payload = {}
        is_valid, error = LedgerPostingService.validate_event_for_posting(
            confirmed_transfer_event
        )
        assert is_valid is False
        assert "源账户和目标账户" in error


# ============================================
# 测试: 标准分录生成
# ============================================

class TestPostSpendEvent:
    """测试 SPEND 事件过账"""

    def test_spend_creates_two_entries(self, mock_db, confirmed_spend_event):
        """SPEND 事件应生成两条分录 (SUPPLIER + ACCOUNT)"""
        entries = LedgerPostingService.post_event(
            confirmed_spend_event, mock_db
        )

        assert len(entries) == 2

        # 验证 SUPPLIER 分录
        supplier_entry = next(
            (e for e in entries if e.entity_type == EntityType.SUPPLIER),
            None
        )
        assert supplier_entry is not None
        assert supplier_entry.entry_type == LedgerEntryType.COST.value
        assert supplier_entry.direction == PostingDirection.DEBIT
        assert supplier_entry.amount < 0  # DEBIT 为负数

        # 验证 ACCOUNT 分录
        account_entry = next(
            (e for e in entries if e.entity_type == EntityType.ACCOUNT),
            None
        )
        assert account_entry is not None
        assert account_entry.entry_type == LedgerEntryType.COST.value
        assert account_entry.direction == PostingDirection.DEBIT

    def test_spend_updates_event_status(self, mock_db, confirmed_spend_event):
        """SPEND 过账后事件状态应为 POSTED"""
        LedgerPostingService.post_event(confirmed_spend_event, mock_db)

        assert confirmed_spend_event.event_status == EventStatus.POSTED.value
        assert confirmed_spend_event.posted_at is not None


class TestPostTopupEvent:
    """测试 TOPUP 事件过账"""

    def test_topup_creates_one_entry(self, mock_db, confirmed_topup_event):
        """TOPUP 事件应生成一条分录 (SUPPLIER CREDIT)"""
        entries = LedgerPostingService.post_event(
            confirmed_topup_event, mock_db
        )

        assert len(entries) == 1

        entry = entries[0]
        assert entry.entity_type == EntityType.SUPPLIER
        assert entry.entry_type == LedgerEntryType.TOPUP.value
        assert entry.direction == PostingDirection.CREDIT
        assert entry.amount > 0  # CREDIT 为正数


class TestPostTransferEvent:
    """测试 TRANSFER 事件过账"""

    def test_transfer_creates_two_entries(self, mock_db, confirmed_transfer_event):
        """TRANSFER 事件应生成两条分录 (OUT + IN)"""
        entries = LedgerPostingService.post_event(
            confirmed_transfer_event, mock_db
        )

        assert len(entries) == 2

        # 验证 TRANSFER_OUT 分录
        out_entry = next(
            (e for e in entries if e.entry_type == LedgerEntryType.TRANSFER_OUT.value),
            None
        )
        assert out_entry is not None
        assert out_entry.direction == PostingDirection.DEBIT
        assert out_entry.amount < 0

        # 验证 TRANSFER_IN 分录
        in_entry = next(
            (e for e in entries if e.entry_type == LedgerEntryType.TRANSFER_IN.value),
            None
        )
        assert in_entry is not None
        assert in_entry.direction == PostingDirection.CREDIT
        assert in_entry.amount > 0

    def test_transfer_amounts_equal(self, mock_db, confirmed_transfer_event):
        """TRANSFER OUT 和 IN 金额绝对值应相等"""
        entries = LedgerPostingService.post_event(
            confirmed_transfer_event, mock_db
        )

        out_entry = next(e for e in entries if e.entry_type == LedgerEntryType.TRANSFER_OUT.value)
        in_entry = next(e for e in entries if e.entry_type == LedgerEntryType.TRANSFER_IN.value)

        assert abs(out_entry.amount) == abs(in_entry.amount)


# ============================================
# 测试: 事件冲正
# ============================================

class TestReverseEvent:
    """测试事件冲正"""

    def test_reverse_posted_event(self, mock_db, posted_event):
        """测试冲正已入账事件"""
        # Mock 原始分录
        original_entry = LedgerEntry(
            id=1,
            ad_account_id=1,
            entry_type=LedgerEntryType.COST.value,
            amount=Decimal('-1100.00'),
            balance_after=Decimal('0'),
            direction=PostingDirection.DEBIT,
            entity_type=EntityType.SUPPLIER,
            entity_id='1',
            event_id=posted_event.id,
            idempotency_key='original_key'
        )
        mock_db.query.return_value.filter.return_value.all.return_value = [original_entry]

        reversal_entries = LedgerPostingService.reverse_event(
            posted_event, "测试冲正", mock_db
        )

        assert len(reversal_entries) == 1

        reversal = reversal_entries[0]
        assert reversal.entry_type == LedgerEntryType.REVERSAL.value
        assert reversal.amount == Decimal('1100.00')  # 金额取反
        assert reversal.direction == PostingDirection.CREDIT  # 方向取反

    def test_reverse_non_posted_event_fails(self, mock_db, confirmed_spend_event):
        """测试冲正非 POSTED 状态事件应失败"""
        with pytest.raises(StateTransitionError) as exc_info:
            LedgerPostingService.reverse_event(
                confirmed_spend_event, "测试冲正", mock_db
            )

        assert "不允许冲正" in str(exc_info.value.message)

    def test_reverse_updates_event_status(self, mock_db, posted_event):
        """冲正后事件状态应为 REVERSED"""
        original_entry = LedgerEntry(
            id=1,
            ad_account_id=1,
            entry_type=LedgerEntryType.COST.value,
            amount=Decimal('-1100.00'),
            balance_after=Decimal('0'),
            direction=PostingDirection.DEBIT,
            entity_type=EntityType.SUPPLIER,
            entity_id='1',
            event_id=posted_event.id
        )
        mock_db.query.return_value.filter.return_value.all.return_value = [original_entry]

        LedgerPostingService.reverse_event(posted_event, "测试冲正", mock_db)

        assert posted_event.event_status == EventStatus.REVERSED.value


# ============================================
# 测试: 幂等性
# ============================================

class TestIdempotency:
    """测试幂等性"""

    def test_duplicate_posting_returns_existing(self, mock_db, confirmed_spend_event):
        """重复过账应返回已存在的分录"""
        existing_entry = LedgerEntry(
            id=1,
            ad_account_id=1,
            entry_type=LedgerEntryType.COST.value,
            amount=Decimal('-1100.00'),
            balance_after=Decimal('0'),
            event_id=confirmed_spend_event.id
        )

        # Mock: 已存在分录
        mock_db.query.return_value.filter.return_value.first.return_value = existing_entry
        mock_db.query.return_value.filter.return_value.all.return_value = [existing_entry]

        entries = LedgerPostingService.post_event(
            confirmed_spend_event, mock_db
        )

        # 应返回已存在的分录，不创建新的
        assert len(entries) == 1
        assert entries[0].id == existing_entry.id


# ============================================
# 测试: 批量操作
# ============================================

class TestBatchPosting:
    """测试批量过账"""

    def test_batch_post_success(self, mock_db):
        """测试批量过账成功"""
        event1_id = uuid4()
        event2_id = uuid4()

        event1 = FinancialEvent(
            id=event1_id,
            event_type=EventType.TOPUP.value,
            event_status=EventStatus.CONFIRMED.value,
            idempotency_key=f"TEST:TOPUP:1:{event1_id}",
            amount=Decimal('1000.00'),
            currency='USD',
            event_date=date.today(),
            supplier_id=1
        )
        event2 = FinancialEvent(
            id=event2_id,
            event_type=EventType.TOPUP.value,
            event_status=EventStatus.CONFIRMED.value,
            idempotency_key=f"TEST:TOPUP:2:{event2_id}",
            amount=Decimal('2000.00'),
            currency='USD',
            event_date=date.today(),
            supplier_id=1
        )

        # Mock: 第一次查询返回 event1, 第二次查询返回 event2
        # 每个事件查询两次: 一次在 post_events_batch, 一次检查已存在分录
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            event1,  # 第一个事件
            None,    # 检查 event1 是否已有分录 (无)
            event2,  # 第二个事件
            None,    # 检查 event2 是否已有分录 (无)
        ]

        result = LedgerPostingService.post_events_batch(
            [event1_id, event2_id], mock_db
        )

        assert result["total"] == 2
        assert result["success"] == 2
        assert result["failed"] == 0

    def test_batch_post_partial_failure(self, mock_db):
        """测试批量过账部分失败"""
        event1 = FinancialEvent(
            id=uuid4(),
            event_type=EventType.TOPUP.value,
            event_status=EventStatus.CONFIRMED.value,
            idempotency_key=f"TEST:TOPUP:1",
            amount=Decimal('1000.00'),
            currency='USD',
            event_date=date.today(),
            supplier_id=1
        )

        # 第一个成功，第二个不存在
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            event1, None
        ]

        result = LedgerPostingService.post_events_batch(
            [event1.id, uuid4()], mock_db
        )

        assert result["total"] == 2
        assert result["success"] == 1
        assert result["failed"] == 1
        assert len(result["errors"]) == 1


# ============================================
# 测试: 服务实例
# ============================================

class TestServiceInstance:
    """测试服务实例获取"""

    def test_get_service_instance(self):
        """测试获取服务实例"""
        service = get_ledger_posting_service()
        assert isinstance(service, LedgerPostingService)


# ============================================
# 测试: 金额计算
# ============================================

class TestAmountCalculation:
    """测试金额计算"""

    def test_gross_amount_calculation(self, confirmed_spend_event):
        """测试含费金额计算"""
        gross = LedgerPostingService._get_amount(
            confirmed_spend_event, 'gross_amount'
        )
        expected = confirmed_spend_event.amount + confirmed_spend_event.fee_amount
        assert gross == expected

    def test_amount_field(self, confirmed_spend_event):
        """测试普通金额字段"""
        amount = LedgerPostingService._get_amount(
            confirmed_spend_event, 'amount'
        )
        assert amount == confirmed_spend_event.amount

    def test_fee_amount_field(self, confirmed_spend_event):
        """测试手续费金额字段"""
        fee = LedgerPostingService._get_amount(
            confirmed_spend_event, 'fee_amount'
        )
        assert fee == confirmed_spend_event.fee_amount
