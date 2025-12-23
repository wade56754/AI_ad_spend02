"""
Phase 1 财务模块单元测试
测试 Team, Buyer, FinancialEvent 模型

SoT 对齐:
- FINANCIAL_SOT_DESIGN.md v1.0
- DATA_SCHEMA.md v5.3
- STATE_MACHINE.md v2.6 (FinancialEvent 5状态机)

测试覆盖:
1. Team 模型测试 (active/inactive 状态)
2. Buyer 模型测试 (active/inactive 状态)
3. FinancialEvent 模型测试 (5状态机)
4. 关联关系测试
5. 业务规则测试
"""

import pytest
from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4
from unittest.mock import Mock, MagicMock, patch

from backend.models.finance.team import Team, TeamStatus
from backend.models.finance.buyer import Buyer, BuyerStatus
from backend.models.finance.financial_event import (
    FinancialEvent,
    EventType,
    EventStatus,
    SourceType,
    generate_spend_idempotency_key,
    generate_topup_idempotency_key,
    generate_payment_idempotency_key,
)


# ==================== Team 模型测试 ====================

@pytest.mark.unit
@pytest.mark.finance
class TestTeamModel:
    """Team 模型单元测试"""

    def test_team_creation_with_defaults(self):
        """测试 Team 创建默认值

        注意: SQLAlchemy Column defaults 只在数据库插入时生效
        Python 对象初始化时需显式传值或检查 Column 定义的 default
        """
        team = Team(code="SZ", name="深圳团队", status=TeamStatus.ACTIVE)

        assert team.code == "SZ"
        assert team.name == "深圳团队"
        assert team.status == TeamStatus.ACTIVE
        assert team.description is None

    def test_team_status_constants(self):
        """测试 TeamStatus 常量"""
        assert TeamStatus.ACTIVE == "active"
        assert TeamStatus.INACTIVE == "inactive"

    def test_team_is_active_property(self):
        """测试 is_active 属性"""
        active_team = Team(code="T1", status=TeamStatus.ACTIVE)
        inactive_team = Team(code="T2", status=TeamStatus.INACTIVE)

        assert active_team.is_active is True
        assert inactive_team.is_active is False

    def test_team_repr(self):
        """测试 Team __repr__"""
        team = Team(code="ZZ", name="郑州团队")
        team.id = uuid4()

        repr_str = repr(team)
        assert "Team" in repr_str
        assert "ZZ" in repr_str
        assert "郑州团队" in repr_str

    def test_team_get_by_code(self):
        """测试根据代码获取团队"""
        mock_session = Mock()
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query

        expected_team = Team(code="SZ")
        mock_query.first.return_value = expected_team

        result = Team.get_by_code(mock_session, "SZ")

        assert result == expected_team
        mock_session.query.assert_called_once_with(Team)

    def test_team_get_active_teams(self):
        """测试获取活跃团队"""
        mock_session = Mock()
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query

        expected_teams = [Team(code="SZ"), Team(code="ZZ")]
        mock_query.all.return_value = expected_teams

        result = Team.get_active_teams(mock_session)

        assert len(result) == 2


# ==================== Buyer 模型测试 ====================

@pytest.mark.unit
@pytest.mark.finance
class TestBuyerModel:
    """Buyer 模型单元测试"""

    def test_buyer_creation_with_defaults(self):
        """测试 Buyer 创建默认值

        注意: SQLAlchemy Column defaults 只在数据库插入时生效
        """
        buyer = Buyer(code="B001", name="张三", status=BuyerStatus.ACTIVE)

        assert buyer.code == "B001"
        assert buyer.name == "张三"
        assert buyer.status == BuyerStatus.ACTIVE
        assert buyer.team_id is None
        assert buyer.user_id is None

    def test_buyer_status_constants(self):
        """测试 BuyerStatus 常量"""
        assert BuyerStatus.ACTIVE == "active"
        assert BuyerStatus.INACTIVE == "inactive"

    def test_buyer_is_active_property(self):
        """测试 is_active 属性"""
        active_buyer = Buyer(code="B1", status=BuyerStatus.ACTIVE)
        inactive_buyer = Buyer(code="B2", status=BuyerStatus.INACTIVE)

        assert active_buyer.is_active is True
        assert inactive_buyer.is_active is False

    def test_buyer_team_code_property_with_team(self):
        """测试 team_code 属性 (有团队)"""
        team = Team(code="SZ")
        buyer = Buyer(code="B001")
        buyer.team = team

        assert buyer.team_code == "SZ"

    def test_buyer_team_code_property_without_team(self):
        """测试 team_code 属性 (无团队)"""
        buyer = Buyer(code="B001")
        buyer.team = None

        assert buyer.team_code is None

    def test_buyer_repr(self):
        """测试 Buyer __repr__"""
        buyer = Buyer(code="B001", name="投手1")
        buyer.id = uuid4()

        repr_str = repr(buyer)
        assert "Buyer" in repr_str
        assert "B001" in repr_str
        assert "投手1" in repr_str

    def test_buyer_get_by_code(self):
        """测试根据代码获取投手"""
        mock_session = Mock()
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query

        expected_buyer = Buyer(code="B001")
        mock_query.first.return_value = expected_buyer

        result = Buyer.get_by_code(mock_session, "B001")

        assert result == expected_buyer

    def test_buyer_get_active_buyers(self):
        """测试获取活跃投手"""
        mock_session = Mock()
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query

        expected_buyers = [Buyer(code="B1"), Buyer(code="B2")]
        mock_query.all.return_value = expected_buyers

        result = Buyer.get_active_buyers(mock_session)

        assert len(result) == 2

    def test_buyer_get_by_team(self):
        """测试获取团队投手"""
        mock_session = Mock()
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query

        team_id = uuid4()
        expected_buyers = [Buyer(code="B1"), Buyer(code="B2")]
        mock_query.all.return_value = expected_buyers

        result = Buyer.get_by_team(mock_session, team_id)

        assert len(result) == 2


# ==================== FinancialEvent 状态机测试 ====================

@pytest.mark.unit
@pytest.mark.finance
@pytest.mark.state_machine
class TestFinancialEventStateMachine:
    """FinancialEvent 5状态机测试"""

    def test_event_type_enum_values(self):
        """测试 EventType 枚举值"""
        assert EventType.TOPUP.value == "TOPUP"
        assert EventType.SPEND.value == "SPEND"
        assert EventType.PAYMENT.value == "PAYMENT"
        assert EventType.TRANSFER.value == "TRANSFER"
        assert EventType.ADJUSTMENT.value == "ADJUSTMENT"
        assert EventType.FEE.value == "FEE"
        assert EventType.REFUND.value == "REFUND"

    def test_event_status_enum_values(self):
        """测试 EventStatus 枚举值 (5状态机)"""
        assert EventStatus.RAW.value == "raw"
        assert EventStatus.PENDING.value == "pending"
        assert EventStatus.CONFIRMED.value == "confirmed"
        assert EventStatus.POSTED.value == "posted"
        assert EventStatus.REVERSED.value == "reversed"

    def test_source_type_enum_values(self):
        """测试 SourceType 枚举值"""
        assert SourceType.EXCEL_IMPORT.value == "excel_import"
        assert SourceType.API.value == "api"
        assert SourceType.MANUAL.value == "manual"
        assert SourceType.SYSTEM.value == "system"

    # ===== 状态转换: RAW → PENDING =====

    def test_transition_raw_to_pending_allowed(self):
        """测试 RAW → PENDING 转换 (允许)"""
        event = FinancialEvent(
            event_type=EventType.SPEND.value,
            event_status=EventStatus.RAW.value,
            idempotency_key="test-key-1",
            amount=Decimal("100.00"),
            event_date=date.today()
        )

        assert event.can_transition_to(EventStatus.PENDING.value) is True

        result = event.transition_to(EventStatus.PENDING.value)

        assert result is True
        assert event.event_status == EventStatus.PENDING.value

    def test_transition_raw_to_confirmed_not_allowed(self):
        """测试 RAW → CONFIRMED 转换 (禁止)"""
        event = FinancialEvent(
            event_type=EventType.SPEND.value,
            event_status=EventStatus.RAW.value,
            idempotency_key="test-key-2",
            amount=Decimal("100.00"),
            event_date=date.today()
        )

        assert event.can_transition_to(EventStatus.CONFIRMED.value) is False

        with pytest.raises(ValueError) as exc_info:
            event.transition_to(EventStatus.CONFIRMED.value)

        assert "不允许从 raw 转换到 confirmed" in str(exc_info.value)

    # ===== 状态转换: PENDING → CONFIRMED =====

    def test_transition_pending_to_confirmed_allowed(self):
        """测试 PENDING → CONFIRMED 转换 (允许)"""
        user_id = uuid4()
        event = FinancialEvent(
            event_type=EventType.TOPUP.value,
            event_status=EventStatus.PENDING.value,
            idempotency_key="test-key-3",
            amount=Decimal("500.00"),
            event_date=date.today()
        )

        assert event.can_transition_to(EventStatus.CONFIRMED.value) is True

        result = event.transition_to(EventStatus.CONFIRMED.value, user_id=user_id)

        assert result is True
        assert event.event_status == EventStatus.CONFIRMED.value
        assert event.confirmed_by == user_id
        assert event.confirmed_at is not None

    def test_transition_pending_to_raw_allowed(self):
        """测试 PENDING → RAW 转换 (允许, 回退)"""
        event = FinancialEvent(
            event_type=EventType.TOPUP.value,
            event_status=EventStatus.PENDING.value,
            idempotency_key="test-key-4",
            amount=Decimal("500.00"),
            event_date=date.today()
        )

        assert event.can_transition_to(EventStatus.RAW.value) is True

        result = event.transition_to(EventStatus.RAW.value)

        assert result is True
        assert event.event_status == EventStatus.RAW.value

    def test_transition_pending_to_posted_not_allowed(self):
        """测试 PENDING → POSTED 转换 (禁止, 必须先 CONFIRMED)"""
        event = FinancialEvent(
            event_type=EventType.TOPUP.value,
            event_status=EventStatus.PENDING.value,
            idempotency_key="test-key-5",
            amount=Decimal("500.00"),
            event_date=date.today()
        )

        assert event.can_transition_to(EventStatus.POSTED.value) is False

        with pytest.raises(ValueError) as exc_info:
            event.transition_to(EventStatus.POSTED.value)

        assert "不允许从 pending 转换到 posted" in str(exc_info.value)

    # ===== 状态转换: CONFIRMED → POSTED =====

    def test_transition_confirmed_to_posted_allowed(self):
        """测试 CONFIRMED → POSTED 转换 (允许)"""
        event = FinancialEvent(
            event_type=EventType.SPEND.value,
            event_status=EventStatus.CONFIRMED.value,
            idempotency_key="test-key-6",
            amount=Decimal("200.00"),
            event_date=date.today()
        )

        assert event.can_transition_to(EventStatus.POSTED.value) is True
        assert event.can_post is True

        result = event.transition_to(EventStatus.POSTED.value)

        assert result is True
        assert event.event_status == EventStatus.POSTED.value
        assert event.posted_at is not None

    def test_transition_confirmed_to_reversed_not_allowed(self):
        """测试 CONFIRMED → REVERSED 转换 (禁止, 必须先 POSTED)"""
        event = FinancialEvent(
            event_type=EventType.SPEND.value,
            event_status=EventStatus.CONFIRMED.value,
            idempotency_key="test-key-7",
            amount=Decimal("200.00"),
            event_date=date.today()
        )

        assert event.can_transition_to(EventStatus.REVERSED.value) is False

        with pytest.raises(ValueError):
            event.transition_to(EventStatus.REVERSED.value)

    # ===== 状态转换: POSTED → REVERSED =====

    def test_transition_posted_to_reversed_allowed(self):
        """测试 POSTED → REVERSED 转换 (允许)"""
        event = FinancialEvent(
            event_type=EventType.SPEND.value,
            event_status=EventStatus.POSTED.value,
            idempotency_key="test-key-8",
            amount=Decimal("200.00"),
            event_date=date.today()
        )

        assert event.can_transition_to(EventStatus.REVERSED.value) is True
        assert event.is_posted is True
        assert event.can_reverse is True

        result = event.transition_to(EventStatus.REVERSED.value)

        assert result is True
        assert event.event_status == EventStatus.REVERSED.value

    def test_transition_posted_to_confirmed_not_allowed(self):
        """测试 POSTED → CONFIRMED 转换 (禁止)"""
        event = FinancialEvent(
            event_type=EventType.SPEND.value,
            event_status=EventStatus.POSTED.value,
            idempotency_key="test-key-9",
            amount=Decimal("200.00"),
            event_date=date.today()
        )

        assert event.can_transition_to(EventStatus.CONFIRMED.value) is False

    # ===== REVERSED 终态测试 =====

    def test_reversed_is_terminal_state(self):
        """测试 REVERSED 是终态 (无法转换)"""
        event = FinancialEvent(
            event_type=EventType.SPEND.value,
            event_status=EventStatus.REVERSED.value,
            idempotency_key="test-key-10",
            amount=Decimal("200.00"),
            event_date=date.today()
        )

        # 终态无法转换到任何状态
        for status in [EventStatus.RAW, EventStatus.PENDING, EventStatus.CONFIRMED, EventStatus.POSTED]:
            assert event.can_transition_to(status.value) is False

    # ===== 完整流程测试 =====

    def test_full_lifecycle_raw_to_reversed(self):
        """测试完整生命周期: RAW → PENDING → CONFIRMED → POSTED → REVERSED"""
        user_id = uuid4()
        event = FinancialEvent(
            event_type=EventType.SPEND.value,
            event_status=EventStatus.RAW.value,
            idempotency_key="test-lifecycle",
            amount=Decimal("1000.00"),
            event_date=date.today()
        )

        # RAW → PENDING
        event.transition_to(EventStatus.PENDING.value)
        assert event.event_status == EventStatus.PENDING.value

        # PENDING → CONFIRMED
        event.transition_to(EventStatus.CONFIRMED.value, user_id=user_id)
        assert event.event_status == EventStatus.CONFIRMED.value
        assert event.confirmed_by == user_id

        # CONFIRMED → POSTED
        event.transition_to(EventStatus.POSTED.value)
        assert event.event_status == EventStatus.POSTED.value
        assert event.is_posted is True

        # POSTED → REVERSED
        event.transition_to(EventStatus.REVERSED.value)
        assert event.event_status == EventStatus.REVERSED.value

        # 验证终态
        assert event.can_transition_to(EventStatus.RAW.value) is False


# ==================== FinancialEvent 模型测试 ====================

@pytest.mark.unit
@pytest.mark.finance
class TestFinancialEventModel:
    """FinancialEvent 模型单元测试"""

    def test_event_creation_with_defaults(self):
        """测试 FinancialEvent 创建默认值

        注意: SQLAlchemy Column defaults 只在数据库插入时生效
        """
        event = FinancialEvent(
            event_type=EventType.SPEND.value,
            event_status=EventStatus.RAW.value,
            idempotency_key="test-key",
            amount=Decimal("100.00"),
            fee_amount=Decimal("0"),
            currency="USD",
            event_date=date.today()
        )

        assert event.event_type == "SPEND"
        assert event.event_status == EventStatus.RAW.value
        assert event.amount == Decimal("100.00")
        assert event.fee_amount == Decimal("0")
        assert event.currency == "USD"

    def test_event_type_enum_property(self):
        """测试 event_type_enum 属性"""
        event = FinancialEvent(
            event_type=EventType.TOPUP.value,
            idempotency_key="test-key-enum",
            amount=Decimal("100.00"),
            event_date=date.today()
        )

        assert event.event_type_enum == EventType.TOPUP

    def test_event_status_enum_property(self):
        """测试 event_status_enum 属性"""
        event = FinancialEvent(
            event_type=EventType.SPEND.value,
            event_status=EventStatus.CONFIRMED.value,
            idempotency_key="test-key-status",
            amount=Decimal("100.00"),
            event_date=date.today()
        )

        assert event.event_status_enum == EventStatus.CONFIRMED

    def test_calculate_gross_amount(self):
        """测试 calculate_gross_amount 计算"""
        event = FinancialEvent(
            event_type=EventType.TOPUP.value,
            idempotency_key="test-gross",
            amount=Decimal("100.00"),
            fee_amount=Decimal("3.50"),
            event_date=date.today()
        )

        gross = event.calculate_gross_amount()

        assert gross == Decimal("103.50")

    def test_calculate_gross_amount_no_fee(self):
        """测试 calculate_gross_amount (无手续费)"""
        event = FinancialEvent(
            event_type=EventType.SPEND.value,
            idempotency_key="test-no-fee",
            amount=Decimal("200.00"),
            event_date=date.today()
        )

        gross = event.calculate_gross_amount()

        assert gross == Decimal("200.00")

    def test_payload_operations(self):
        """测试 payload 操作"""
        event = FinancialEvent(
            event_type=EventType.SPEND.value,
            idempotency_key="test-payload",
            amount=Decimal("100.00"),
            event_date=date.today()
        )

        # 设置 payload 字段
        event.set_payload_field("source_file", "spend_2024.xlsx")
        event.set_payload_field("row_number", 42)

        # 获取 payload 字段
        assert event.get_payload_field("source_file") == "spend_2024.xlsx"
        assert event.get_payload_field("row_number") == 42
        assert event.get_payload_field("nonexistent", "default") == "default"

    def test_payload_operations_with_none_payload(self):
        """测试 payload 操作 (初始为 None)"""
        event = FinancialEvent(
            event_type=EventType.SPEND.value,
            idempotency_key="test-none-payload",
            amount=Decimal("100.00"),
            event_date=date.today()
        )
        event.payload = None

        # 设置应自动初始化 payload
        event.set_payload_field("key", "value")
        assert event.payload == {"key": "value"}

        # 获取时 payload 为 None 应返回默认值
        event.payload = None
        assert event.get_payload_field("key", "default") == "default"

    def test_event_repr(self):
        """测试 FinancialEvent __repr__"""
        event = FinancialEvent(
            event_type=EventType.TOPUP.value,
            event_status=EventStatus.PENDING.value,
            idempotency_key="test-repr",
            amount=Decimal("500.00"),
            event_date=date.today()
        )
        event.id = uuid4()

        repr_str = repr(event)
        assert "FinancialEvent" in repr_str
        assert "TOPUP" in repr_str
        assert "pending" in repr_str
        assert "500" in repr_str

    def test_get_by_idempotency_key(self):
        """测试根据幂等键获取事件"""
        mock_session = Mock()
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query

        expected_event = FinancialEvent(idempotency_key="unique-key")
        mock_query.first.return_value = expected_event

        result = FinancialEvent.get_by_idempotency_key(mock_session, "unique-key")

        assert result == expected_event

    def test_get_pending_events(self):
        """测试获取待确认事件"""
        mock_session = Mock()
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query

        expected_events = [
            FinancialEvent(event_status=EventStatus.PENDING.value),
            FinancialEvent(event_status=EventStatus.PENDING.value)
        ]
        mock_query.all.return_value = expected_events

        result = FinancialEvent.get_pending_events(mock_session)

        assert len(result) == 2

    def test_get_pending_events_by_type(self):
        """测试获取指定类型的待确认事件"""
        mock_session = Mock()
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query

        expected_events = [FinancialEvent(event_type=EventType.SPEND.value)]
        mock_query.all.return_value = expected_events

        result = FinancialEvent.get_pending_events(mock_session, event_type="SPEND")

        assert len(result) == 1

    def test_get_confirmed_events(self):
        """测试获取已确认待入账事件"""
        mock_session = Mock()
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query

        expected_events = [FinancialEvent(event_status=EventStatus.CONFIRMED.value)]
        mock_query.all.return_value = expected_events

        result = FinancialEvent.get_confirmed_events(mock_session)

        assert len(result) == 1

    def test_get_events_by_date_range(self):
        """测试获取日期范围内的事件"""
        mock_session = Mock()
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query

        start = date(2024, 1, 1)
        end = date(2024, 12, 31)
        expected_events = [FinancialEvent(), FinancialEvent()]
        mock_query.all.return_value = expected_events

        result = FinancialEvent.get_events_by_date_range(mock_session, start, end)

        assert len(result) == 2


# ==================== 幂等键生成测试 ====================

@pytest.mark.unit
@pytest.mark.finance
class TestIdempotencyKeyGeneration:
    """幂等键生成函数测试"""

    def test_generate_spend_idempotency_key(self):
        """测试 SPEND 幂等键生成"""
        account_id = "ACC123"
        event_date = date(2024, 12, 20)

        key = generate_spend_idempotency_key(account_id, event_date)

        assert key == "SPEND:ACC123:2024-12-20"

    def test_generate_topup_idempotency_key(self):
        """测试 TOPUP 幂等键生成"""
        supplier_id = 1
        amount = Decimal("1000.00")
        payment_date = date(2024, 12, 20)
        buyer_code = "B001"

        key = generate_topup_idempotency_key(supplier_id, amount, payment_date, buyer_code)

        assert key == "TOPUP:1:1000.00:2024-12-20:B001"

    def test_generate_payment_idempotency_key(self):
        """测试 PAYMENT 幂等键生成"""
        project_id = 5
        amount = Decimal("5000.00")
        payment_date = date(2024, 12, 20)
        reference_no = "PAY-2024-001"

        key = generate_payment_idempotency_key(project_id, amount, payment_date, reference_no)

        assert key == "PAYMENT:5:5000.00:2024-12-20:PAY-2024-001"

    def test_idempotency_key_uniqueness(self):
        """测试幂等键唯一性"""
        key1 = generate_spend_idempotency_key("ACC1", date(2024, 12, 20))
        key2 = generate_spend_idempotency_key("ACC1", date(2024, 12, 21))
        key3 = generate_spend_idempotency_key("ACC2", date(2024, 12, 20))

        # 所有键应该不同
        assert key1 != key2
        assert key1 != key3
        assert key2 != key3


# ==================== 业务属性测试 ====================

@pytest.mark.unit
@pytest.mark.finance
class TestFinancialEventBusinessProperties:
    """FinancialEvent 业务属性测试"""

    def test_is_posted_property(self):
        """测试 is_posted 属性"""
        posted_event = FinancialEvent(
            event_status=EventStatus.POSTED.value,
            event_type=EventType.SPEND.value,
            idempotency_key="posted-1",
            amount=Decimal("100"),
            event_date=date.today()
        )
        pending_event = FinancialEvent(
            event_status=EventStatus.PENDING.value,
            event_type=EventType.SPEND.value,
            idempotency_key="pending-1",
            amount=Decimal("100"),
            event_date=date.today()
        )

        assert posted_event.is_posted is True
        assert pending_event.is_posted is False

    def test_can_post_property(self):
        """测试 can_post 属性"""
        confirmed_event = FinancialEvent(
            event_status=EventStatus.CONFIRMED.value,
            event_type=EventType.SPEND.value,
            idempotency_key="confirmed-1",
            amount=Decimal("100"),
            event_date=date.today()
        )
        pending_event = FinancialEvent(
            event_status=EventStatus.PENDING.value,
            event_type=EventType.SPEND.value,
            idempotency_key="pending-2",
            amount=Decimal("100"),
            event_date=date.today()
        )

        assert confirmed_event.can_post is True
        assert pending_event.can_post is False

    def test_can_reverse_property(self):
        """测试 can_reverse 属性"""
        posted_event = FinancialEvent(
            event_status=EventStatus.POSTED.value,
            event_type=EventType.SPEND.value,
            idempotency_key="posted-2",
            amount=Decimal("100"),
            event_date=date.today()
        )
        confirmed_event = FinancialEvent(
            event_status=EventStatus.CONFIRMED.value,
            event_type=EventType.SPEND.value,
            idempotency_key="confirmed-2",
            amount=Decimal("100"),
            event_date=date.today()
        )

        assert posted_event.can_reverse is True
        assert confirmed_event.can_reverse is False


# ==================== 边界条件测试 ====================

@pytest.mark.unit
@pytest.mark.finance
@pytest.mark.boundary
class TestFinancialEventBoundaryConditions:
    """FinancialEvent 边界条件测试"""

    def test_zero_amount(self):
        """测试零金额"""
        event = FinancialEvent(
            event_type=EventType.ADJUSTMENT.value,
            idempotency_key="zero-amount",
            amount=Decimal("0.00"),
            event_date=date.today()
        )

        assert event.amount == Decimal("0.00")
        assert event.calculate_gross_amount() == Decimal("0.00")

    def test_negative_amount(self):
        """测试负金额 (用于调整)"""
        event = FinancialEvent(
            event_type=EventType.ADJUSTMENT.value,
            idempotency_key="negative-amount",
            amount=Decimal("-50.00"),
            event_date=date.today()
        )

        assert event.amount == Decimal("-50.00")

    def test_large_amount(self):
        """测试大金额"""
        event = FinancialEvent(
            event_type=EventType.TOPUP.value,
            idempotency_key="large-amount",
            amount=Decimal("99999999999999.9999"),
            event_date=date.today()
        )

        assert event.amount == Decimal("99999999999999.9999")

    def test_high_precision_fee(self):
        """测试高精度手续费"""
        event = FinancialEvent(
            event_type=EventType.TOPUP.value,
            idempotency_key="precision-fee",
            amount=Decimal("100.0000"),
            fee_amount=Decimal("3.5123"),
            event_date=date.today()
        )

        gross = event.calculate_gross_amount()
        assert gross == Decimal("103.5123")

    def test_empty_payload(self):
        """测试空 payload"""
        event = FinancialEvent(
            event_type=EventType.SPEND.value,
            idempotency_key="empty-payload",
            amount=Decimal("100.00"),
            event_date=date.today(),
            payload={}
        )

        assert event.payload == {}
        assert event.get_payload_field("any_key") is None

    def test_complex_payload(self):
        """测试复杂 payload"""
        complex_payload = {
            "source_file": "data.xlsx",
            "row_numbers": [1, 2, 3],
            "metadata": {
                "imported_at": "2024-12-20T10:00:00Z",
                "imported_by": "admin"
            }
        }
        event = FinancialEvent(
            event_type=EventType.SPEND.value,
            idempotency_key="complex-payload",
            amount=Decimal("100.00"),
            event_date=date.today(),
            payload=complex_payload
        )

        assert event.payload["row_numbers"] == [1, 2, 3]
        assert event.payload["metadata"]["imported_by"] == "admin"

    def test_all_event_types(self):
        """测试所有事件类型"""
        for event_type in EventType:
            event = FinancialEvent(
                event_type=event_type.value,
                idempotency_key=f"type-{event_type.value}",
                amount=Decimal("100.00"),
                event_date=date.today()
            )
            assert event.event_type == event_type.value
            assert event.event_type_enum == event_type

    def test_all_currencies(self):
        """测试不同币种"""
        currencies = ["USD", "CNY", "EUR", "GBP"]
        for currency in currencies:
            event = FinancialEvent(
                event_type=EventType.TOPUP.value,
                idempotency_key=f"currency-{currency}",
                amount=Decimal("100.00"),
                currency=currency,
                event_date=date.today()
            )
            assert event.currency == currency
