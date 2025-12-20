"""
消耗导入服务测试
Version: 1.0 (Financial SoT Phase 2)
Author: Claude Code

测试范围:
- 状态机测试 (raw → pending → confirmed → posted → reversed)
- Excel 导入测试
- 验证/确认/入账/冲正流程测试
- 边界条件测试

SoT 对齐:
- STATE_MACHINE.md v2.6: 事件状态机
- ERROR_CODES_SOT.md v2.1: 错误码

注意: 这些测试依赖 financial_events 表，需要先运行数据库迁移
"""

import pytest

# financial_events 表已迁移完成，测试已启用
from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import uuid4
from unittest.mock import Mock, patch, MagicMock
import io

from backend.models.finance import (
    FinancialEvent,
    EventType,
    EventStatus,
    SourceType,
    Team,
    Buyer,
    generate_spend_idempotency_key,
)
from backend.schemas.spend import (
    SpendImportRequest,
    SpendEventCreate,
    TeamCodeEnum,
)
from backend.services.spend_import_service import SpendImportService
from backend.exceptions.custom_exceptions import (
    BusinessLogicError,
    ResourceNotFoundError,
    ResourceConflictError,
)


class TestSpendEventStateMachine:
    """
    消耗事件状态机测试

    状态流转图:
    raw → pending → confirmed → posted → reversed
          ↑___________↓
         (可回退到 raw)
    """

    def test_event_initial_status_is_raw(self, db_session):
        """测试事件初始状态为 raw"""
        event = FinancialEvent(
            id=uuid4(),  # SQLite 不支持 gen_random_uuid()
            event_type=EventType.SPEND.value,
            idempotency_key=f"TEST:{uuid4()}",
            amount=Decimal("100.00"),
            event_date=date.today(),
        )
        db_session.add(event)
        db_session.flush()

        assert event.event_status == EventStatus.RAW.value

    def test_transition_raw_to_pending(self, db_session):
        """测试 raw → pending 转换"""
        event = FinancialEvent(
            id=uuid4(),  # SQLite 不支持 gen_random_uuid()
            event_type=EventType.SPEND.value,
            event_status=EventStatus.RAW.value,
            idempotency_key=f"TEST:{uuid4()}",
            amount=Decimal("100.00"),
            event_date=date.today(),
        )
        db_session.add(event)
        db_session.flush()

        # 执行转换
        result = event.transition_to(EventStatus.PENDING.value)

        assert result is True
        assert event.event_status == EventStatus.PENDING.value

    def test_transition_pending_to_confirmed(self, db_session):
        """测试 pending → confirmed 转换"""
        user_id = uuid4()
        event = FinancialEvent(
            id=uuid4(),  # SQLite 不支持 gen_random_uuid()
            event_type=EventType.SPEND.value,
            event_status=EventStatus.PENDING.value,
            idempotency_key=f"TEST:{uuid4()}",
            amount=Decimal("100.00"),
            event_date=date.today(),
        )
        db_session.add(event)
        db_session.flush()

        # 执行转换
        result = event.transition_to(EventStatus.CONFIRMED.value, user_id)

        assert result is True
        assert event.event_status == EventStatus.CONFIRMED.value
        assert event.confirmed_by == user_id
        assert event.confirmed_at is not None

    def test_transition_confirmed_to_posted(self, db_session):
        """测试 confirmed → posted 转换"""
        event = FinancialEvent(
            id=uuid4(),  # SQLite 不支持 gen_random_uuid()
            event_type=EventType.SPEND.value,
            event_status=EventStatus.CONFIRMED.value,
            idempotency_key=f"TEST:{uuid4()}",
            amount=Decimal("100.00"),
            event_date=date.today(),
        )
        db_session.add(event)
        db_session.flush()

        # 执行转换
        result = event.transition_to(EventStatus.POSTED.value)

        assert result is True
        assert event.event_status == EventStatus.POSTED.value
        assert event.posted_at is not None

    def test_transition_posted_to_reversed(self, db_session):
        """测试 posted → reversed 转换"""
        event = FinancialEvent(
            id=uuid4(),  # SQLite 不支持 gen_random_uuid()
            event_type=EventType.SPEND.value,
            event_status=EventStatus.POSTED.value,
            idempotency_key=f"TEST:{uuid4()}",
            amount=Decimal("100.00"),
            event_date=date.today(),
        )
        db_session.add(event)
        db_session.flush()

        # 执行转换
        result = event.transition_to(EventStatus.REVERSED.value)

        assert result is True
        assert event.event_status == EventStatus.REVERSED.value

    def test_transition_pending_back_to_raw(self, db_session):
        """测试 pending → raw 回退"""
        event = FinancialEvent(
            id=uuid4(),  # SQLite 不支持 gen_random_uuid()
            event_type=EventType.SPEND.value,
            event_status=EventStatus.PENDING.value,
            idempotency_key=f"TEST:{uuid4()}",
            amount=Decimal("100.00"),
            event_date=date.today(),
        )
        db_session.add(event)
        db_session.flush()

        # 执行回退
        result = event.transition_to(EventStatus.RAW.value)

        assert result is True
        assert event.event_status == EventStatus.RAW.value

    def test_invalid_transition_raw_to_confirmed(self, db_session):
        """测试非法转换 raw → confirmed"""
        event = FinancialEvent(
            id=uuid4(),  # SQLite 不支持 gen_random_uuid()
            event_type=EventType.SPEND.value,
            event_status=EventStatus.RAW.value,
            idempotency_key=f"TEST:{uuid4()}",
            amount=Decimal("100.00"),
            event_date=date.today(),
        )
        db_session.add(event)
        db_session.flush()

        # 尝试非法转换
        with pytest.raises(ValueError) as exc_info:
            event.transition_to(EventStatus.CONFIRMED.value)

        assert "不允许从 raw 转换到 confirmed" in str(exc_info.value)

    def test_invalid_transition_raw_to_posted(self, db_session):
        """测试非法转换 raw → posted"""
        event = FinancialEvent(
            id=uuid4(),  # SQLite 不支持 gen_random_uuid()
            event_type=EventType.SPEND.value,
            event_status=EventStatus.RAW.value,
            idempotency_key=f"TEST:{uuid4()}",
            amount=Decimal("100.00"),
            event_date=date.today(),
        )
        db_session.add(event)
        db_session.flush()

        with pytest.raises(ValueError):
            event.transition_to(EventStatus.POSTED.value)

    def test_invalid_transition_confirmed_to_raw(self, db_session):
        """测试非法转换 confirmed → raw"""
        event = FinancialEvent(
            id=uuid4(),  # SQLite 不支持 gen_random_uuid()
            event_type=EventType.SPEND.value,
            event_status=EventStatus.CONFIRMED.value,
            idempotency_key=f"TEST:{uuid4()}",
            amount=Decimal("100.00"),
            event_date=date.today(),
        )
        db_session.add(event)
        db_session.flush()

        with pytest.raises(ValueError):
            event.transition_to(EventStatus.RAW.value)

    def test_reversed_is_terminal_state(self, db_session):
        """测试 reversed 是终态，不能转换到其他状态"""
        event = FinancialEvent(
            id=uuid4(),  # SQLite 不支持 gen_random_uuid()
            event_type=EventType.SPEND.value,
            event_status=EventStatus.REVERSED.value,
            idempotency_key=f"TEST:{uuid4()}",
            amount=Decimal("100.00"),
            event_date=date.today(),
        )
        db_session.add(event)
        db_session.flush()

        # 尝试转换到任何其他状态都应该失败
        for target_status in [EventStatus.RAW, EventStatus.PENDING, EventStatus.CONFIRMED, EventStatus.POSTED]:
            with pytest.raises(ValueError):
                event.transition_to(target_status.value)


class TestSpendImportService:
    """消耗导入服务测试"""

    @pytest.fixture
    def service(self, db_session):
        """创建服务实例"""
        return SpendImportService(db_session)

    @pytest.fixture
    def sample_team(self, db_session):
        """创建测试团队"""
        team = Team(
            id=uuid4(),  # SQLite 不支持 gen_random_uuid()
            code="SZ",
            name="深圳团队",
            status="active"
        )
        db_session.add(team)
        db_session.commit()
        return team

    @pytest.fixture
    def sample_ad_account(self, db_session, sample_supplier):
        """创建测试广告账户"""
        from backend.models import AdAccount
        account = AdAccount(
            account_code="TEST001",
            account_name="测试账户",
            supplier_id=sample_supplier.id if sample_supplier else None,
            status="active"
        )
        db_session.add(account)
        db_session.commit()
        return account

    @pytest.fixture
    def sample_supplier(self, db_session):
        """创建测试供应商"""
        from backend.models import Supplier
        supplier = Supplier(
            name="测试供应商",
            status="active",
            fee_rate=Decimal("0.10"),  # 10% 手续费
        )
        db_session.add(supplier)
        db_session.commit()
        return supplier


class TestIdempotencyKey:
    """幂等键测试"""

    def test_generate_spend_idempotency_key(self):
        """测试 SPEND 幂等键生成"""
        account_id = "12345"
        event_date = date(2024, 12, 19)

        key = generate_spend_idempotency_key(account_id, event_date)

        assert key == "SPEND:12345:2024-12-19"

    def test_idempotency_key_uniqueness(self):
        """测试幂等键唯一性"""
        key1 = generate_spend_idempotency_key("123", date(2024, 12, 19))
        key2 = generate_spend_idempotency_key("123", date(2024, 12, 20))
        key3 = generate_spend_idempotency_key("456", date(2024, 12, 19))

        assert key1 != key2  # 不同日期
        assert key1 != key3  # 不同账户
        assert key2 != key3  # 两者都不同

    def test_duplicate_event_prevention(self, db_session):
        """测试重复事件防止"""
        idempotency_key = f"SPEND:123:{date.today().isoformat()}"

        # 创建第一个事件
        event1 = FinancialEvent(
            id=uuid4(),  # SQLite 不支持 gen_random_uuid()
            event_type=EventType.SPEND.value,
            idempotency_key=idempotency_key,
            amount=Decimal("100.00"),
            event_date=date.today(),
        )
        db_session.add(event1)
        db_session.commit()

        # 尝试创建重复事件
        event2 = FinancialEvent(
            id=uuid4(),  # SQLite 不支持 gen_random_uuid()
            event_type=EventType.SPEND.value,
            idempotency_key=idempotency_key,
            amount=Decimal("200.00"),
            event_date=date.today(),
        )
        db_session.add(event2)

        # 应该抛出完整性错误
        with pytest.raises(Exception):  # IntegrityError
            db_session.commit()


class TestEventBusinessProperties:
    """事件业务属性测试"""

    def test_is_posted_property(self, db_session):
        """测试 is_posted 属性"""
        event = FinancialEvent(
            event_type=EventType.SPEND.value,
            event_status=EventStatus.RAW.value,
            idempotency_key=f"TEST:{uuid4()}",
            amount=Decimal("100.00"),
            event_date=date.today(),
        )

        assert event.is_posted is False

        event.event_status = EventStatus.POSTED.value
        assert event.is_posted is True

    def test_can_post_property(self, db_session):
        """测试 can_post 属性"""
        event = FinancialEvent(
            event_type=EventType.SPEND.value,
            event_status=EventStatus.RAW.value,
            idempotency_key=f"TEST:{uuid4()}",
            amount=Decimal("100.00"),
            event_date=date.today(),
        )

        assert event.can_post is False  # raw 不能入账

        event.event_status = EventStatus.PENDING.value
        assert event.can_post is False  # pending 不能入账

        event.event_status = EventStatus.CONFIRMED.value
        assert event.can_post is True  # confirmed 可以入账

    def test_can_reverse_property(self, db_session):
        """测试 can_reverse 属性"""
        event = FinancialEvent(
            event_type=EventType.SPEND.value,
            event_status=EventStatus.CONFIRMED.value,
            idempotency_key=f"TEST:{uuid4()}",
            amount=Decimal("100.00"),
            event_date=date.today(),
        )

        assert event.can_reverse is False  # confirmed 不能冲正

        event.event_status = EventStatus.POSTED.value
        assert event.can_reverse is True  # posted 可以冲正

    def test_calculate_gross_amount(self, db_session):
        """测试含费金额计算"""
        event = FinancialEvent(
            event_type=EventType.SPEND.value,
            idempotency_key=f"TEST:{uuid4()}",
            amount=Decimal("100.00"),
            fee_amount=Decimal("10.00"),
            event_date=date.today(),
        )

        assert event.calculate_gross_amount() == Decimal("110.00")

    def test_payload_operations(self, db_session):
        """测试扩展数据操作"""
        event = FinancialEvent(
            event_type=EventType.SPEND.value,
            idempotency_key=f"TEST:{uuid4()}",
            amount=Decimal("100.00"),
            event_date=date.today(),
            payload={}
        )

        # 设置字段
        event.set_payload_field("today_max", 150.0)
        event.set_payload_field("yesterday_max", 50.0)

        # 获取字段
        assert event.get_payload_field("today_max") == 150.0
        assert event.get_payload_field("yesterday_max") == 50.0
        assert event.get_payload_field("nonexistent", "default") == "default"


class TestEventTypeEnum:
    """事件类型枚举测试"""

    def test_all_event_types_defined(self):
        """测试所有事件类型已定义"""
        expected_types = ["TOPUP", "SPEND", "PAYMENT", "TRANSFER", "ADJUSTMENT", "FEE", "REFUND"]

        for event_type in expected_types:
            assert hasattr(EventType, event_type)
            assert EventType[event_type].value == event_type

    def test_event_type_values(self):
        """测试事件类型值"""
        assert EventType.TOPUP.value == "TOPUP"
        assert EventType.SPEND.value == "SPEND"
        assert EventType.PAYMENT.value == "PAYMENT"


class TestEventStatusEnum:
    """事件状态枚举测试"""

    def test_all_event_statuses_defined(self):
        """测试所有事件状态已定义"""
        expected_statuses = ["RAW", "PENDING", "CONFIRMED", "POSTED", "REVERSED"]

        for status in expected_statuses:
            assert hasattr(EventStatus, status)

    def test_event_status_values(self):
        """测试事件状态值"""
        assert EventStatus.RAW.value == "raw"
        assert EventStatus.PENDING.value == "pending"
        assert EventStatus.CONFIRMED.value == "confirmed"
        assert EventStatus.POSTED.value == "posted"
        assert EventStatus.REVERSED.value == "reversed"


class TestSourceTypeEnum:
    """来源类型枚举测试"""

    def test_all_source_types_defined(self):
        """测试所有来源类型已定义"""
        expected_types = ["EXCEL_IMPORT", "API", "MANUAL", "SYSTEM"]

        for source_type in expected_types:
            assert hasattr(SourceType, source_type)

    def test_source_type_values(self):
        """测试来源类型值"""
        assert SourceType.EXCEL_IMPORT.value == "excel_import"
        assert SourceType.API.value == "api"
        assert SourceType.MANUAL.value == "manual"
        assert SourceType.SYSTEM.value == "system"


class TestSchemaValidation:
    """Schema 验证测试"""

    def test_spend_event_create_valid(self):
        """测试有效的创建请求"""
        request = SpendEventCreate(
            ad_account_id=1,
            supplier_id=1,
            event_date=date.today(),
            amount=Decimal("100.00"),
        )

        assert request.ad_account_id == 1
        assert request.amount == Decimal("100.00")

    def test_spend_event_create_future_date_rejected(self):
        """测试未来日期被拒绝"""
        with pytest.raises(ValueError) as exc_info:
            SpendEventCreate(
                ad_account_id=1,
                supplier_id=1,
                event_date=date.today() + timedelta(days=1),
                amount=Decimal("100.00"),
            )

        assert "未来日期" in str(exc_info.value)

    def test_spend_event_create_invalid_amount_precision(self):
        """测试无效的金额精度"""
        with pytest.raises(ValueError) as exc_info:
            SpendEventCreate(
                ad_account_id=1,
                supplier_id=1,
                event_date=date.today(),
                amount=Decimal("100.00001"),  # 5位小数，超过4位限制
            )

        assert "小数" in str(exc_info.value)

    def test_spend_import_request_valid(self):
        """测试有效的导入请求"""
        request = SpendImportRequest(
            team_code=TeamCodeEnum.SZ,
            dry_run=True,
        )

        assert request.team_code == TeamCodeEnum.SZ
        assert request.dry_run is True


class TestTransitionValidation:
    """状态转换验证测试"""

    def test_can_transition_to_valid(self, db_session):
        """测试 can_transition_to 方法 - 有效转换"""
        event = FinancialEvent(
            event_type=EventType.SPEND.value,
            event_status=EventStatus.RAW.value,
            idempotency_key=f"TEST:{uuid4()}",
            amount=Decimal("100.00"),
            event_date=date.today(),
        )

        assert event.can_transition_to(EventStatus.PENDING.value) is True
        assert event.can_transition_to(EventStatus.CONFIRMED.value) is False

    def test_can_transition_to_invalid(self, db_session):
        """测试 can_transition_to 方法 - 无效转换"""
        event = FinancialEvent(
            event_type=EventType.SPEND.value,
            event_status=EventStatus.POSTED.value,
            idempotency_key=f"TEST:{uuid4()}",
            amount=Decimal("100.00"),
            event_date=date.today(),
        )

        assert event.can_transition_to(EventStatus.RAW.value) is False
        assert event.can_transition_to(EventStatus.PENDING.value) is False
        assert event.can_transition_to(EventStatus.CONFIRMED.value) is False
        assert event.can_transition_to(EventStatus.REVERSED.value) is True


class TestEventTransitions:
    """事件转换定义测试"""

    def test_transitions_constant_defined(self):
        """测试状态转换规则已定义"""
        expected_transitions = {
            "raw": ["pending"],
            "pending": ["confirmed", "raw"],
            "confirmed": ["posted"],
            "posted": ["reversed"],
            "reversed": [],
        }

        assert FinancialEvent.TRANSITIONS == expected_transitions

    def test_transitions_are_complete(self):
        """测试转换规则完整覆盖所有状态"""
        all_statuses = [s.value for s in EventStatus]

        for status in all_statuses:
            assert status in FinancialEvent.TRANSITIONS


# ==================== 新增功能测试 (Phase 2) ====================


class TestBatchReversal:
    """批量冲正功能测试"""

    @pytest.fixture
    def service(self, db_session):
        """创建服务实例"""
        return SpendImportService(db_session)

    @pytest.fixture
    def posted_events(self, db_session):
        """创建已入账的事件"""
        events = []
        for i in range(3):
            event = FinancialEvent(
                id=uuid4(),  # SQLite 不支持 gen_random_uuid()
                event_type=EventType.SPEND.value,
                event_status=EventStatus.POSTED.value,
                idempotency_key=f"SPEND:batch-test-{i}:{date.today().isoformat()}",
                amount=Decimal("100.00"),
                fee_amount=Decimal("10.00"),
                event_date=date.today(),
            )
            event.gross_amount = event.amount + event.fee_amount
            db_session.add(event)
            events.append(event)
        db_session.flush()
        return events

    def test_batch_reverse_all_success(self, service, posted_events):
        """测试批量冲正全部成功"""
        event_ids = [e.id for e in posted_events]
        user_id = uuid4()

        result = service.reverse_events(
            event_ids=event_ids,
            reason="批量测试冲正",
            user_id=user_id,
        )

        assert result.success is True
        assert result.total_events == 3
        assert result.success_events == 3
        assert result.failed_events == 0
        assert result.total_reversed_amount == Decimal("330.00")  # 3 * 110

    def test_batch_reverse_partial_failure(self, service, posted_events, db_session):
        """测试批量冲正部分失败"""
        # 将一个事件改为 raw 状态
        posted_events[0].event_status = EventStatus.RAW.value
        db_session.flush()

        event_ids = [e.id for e in posted_events]
        user_id = uuid4()

        result = service.reverse_events(
            event_ids=event_ids,
            reason="部分失败测试",
            user_id=user_id,
        )

        assert result.success is False
        assert result.total_events == 3
        assert result.success_events == 2
        assert result.failed_events == 1
        assert len(result.failed_details) == 1
        assert result.failed_details[0]["error_code"] == "STATE-405"

    def test_batch_reverse_nonexistent_event(self, service):
        """测试批量冲正不存在的事件"""
        fake_ids = [uuid4(), uuid4()]
        user_id = uuid4()

        result = service.reverse_events(
            event_ids=fake_ids,
            reason="不存在的事件测试",
            user_id=user_id,
        )

        assert result.success is False
        assert result.failed_events == 2
        assert all(d["error_code"] == "NOT-001" for d in result.failed_details)


class TestExportEvents:
    """导出功能测试"""

    @pytest.fixture
    def service(self, db_session):
        """创建服务实例"""
        return SpendImportService(db_session)

    @pytest.fixture
    def sample_events(self, db_session):
        """创建测试事件"""
        from backend.models.finance import Team

        # 创建团队 (Team 也需要显式 id)
        team = Team(id=uuid4(), code="SZ", name="深圳团队", status="active")
        db_session.add(team)
        db_session.flush()

        # 创建事件
        events = []
        for i in range(5):
            event = FinancialEvent(
                id=uuid4(),  # SQLite 不支持 gen_random_uuid()
                event_type=EventType.SPEND.value,
                event_status=EventStatus.POSTED.value,
                idempotency_key=f"SPEND:export-test-{i}:{date.today().isoformat()}",
                amount=Decimal(f"{(i+1)*100}.00"),
                fee_amount=Decimal("10.00"),
                currency="USD",
                event_date=date.today(),
                team_id=team.id,
            )
            event.gross_amount = event.amount + event.fee_amount
            db_session.add(event)
            events.append(event)

        db_session.flush()
        return events

    def test_export_xlsx(self, service, sample_events):
        """测试导出 Excel 格式"""
        file_content, file_name = service.export_events(
            export_format="xlsx"
        )

        assert file_content is not None
        assert len(file_content) > 0
        assert file_name.endswith(".xlsx")
        assert "spend_export_" in file_name

    def test_export_csv(self, service, sample_events):
        """测试导出 CSV 格式"""
        file_content, file_name = service.export_events(
            export_format="csv"
        )

        assert file_content is not None
        assert len(file_content) > 0
        assert file_name.endswith(".csv")
        assert "spend_export_" in file_name

    def test_export_with_filters(self, service, sample_events):
        """测试带筛选条件的导出"""
        file_content, file_name = service.export_events(
            event_status=EventStatus.POSTED.value,
            start_date=date.today(),
            end_date=date.today(),
            export_format="xlsx",
        )

        assert file_content is not None
        assert len(file_content) > 0

    def test_export_empty_result(self, service):
        """测试导出空结果"""
        file_content, file_name = service.export_events(
            start_date=date(2000, 1, 1),
            end_date=date(2000, 1, 2),  # 远古日期，应该没有数据
            export_format="xlsx",
        )

        assert file_content is not None  # 即使没有数据也会生成空文件


class TestTemplateGeneration:
    """模板生成功能测试"""

    @pytest.fixture
    def service(self, db_session):
        """创建服务实例"""
        return SpendImportService(db_session)

    def test_generate_template(self, service):
        """测试生成导入模板"""
        file_content, file_name, columns = service.generate_template()

        assert file_content is not None
        assert len(file_content) > 0
        assert file_name.endswith(".xlsx")
        assert "spend_import_template_" in file_name

        # 验证列名
        expected_columns = ["账户ID", "账户名称", "消耗金额", "今日最大消耗", "昨日最大消耗", "日期"]
        assert columns == expected_columns

    def test_template_is_valid_excel(self, service):
        """测试模板是有效的 Excel 文件"""
        import pandas as pd

        file_content, _, _ = service.generate_template()

        # 尝试用 pandas 读取
        df = pd.read_excel(io.BytesIO(file_content), sheet_name="消耗数据")

        assert df is not None
        assert len(df) == 2  # 两行示例数据
        assert "账户ID" in df.columns
        assert "消耗金额" in df.columns

    def test_template_has_instructions(self, service):
        """测试模板包含填写说明"""
        import pandas as pd

        file_content, _, _ = service.generate_template()

        # 读取说明 sheet
        df = pd.read_excel(io.BytesIO(file_content), sheet_name="填写说明")

        assert df is not None
        assert len(df) > 0  # 有说明内容


class TestBatchReverseSchemas:
    """批量冲正 Schema 测试"""

    def test_batch_reverse_request_valid(self):
        """测试有效的批量冲正请求"""
        from backend.schemas.spend import SpendEventBatchReverseRequest

        request = SpendEventBatchReverseRequest(
            event_ids=[uuid4(), uuid4()],
            reason="这是一个有效的冲正原因说明"
        )

        assert len(request.event_ids) == 2
        assert request.reason == "这是一个有效的冲正原因说明"

    def test_batch_reverse_request_empty_ids_rejected(self):
        """测试空ID列表被拒绝"""
        from backend.schemas.spend import SpendEventBatchReverseRequest

        with pytest.raises(ValueError):
            SpendEventBatchReverseRequest(
                event_ids=[],
                reason="冲正原因"
            )

    def test_batch_reverse_request_short_reason_rejected(self):
        """测试过短的原因被拒绝"""
        from backend.schemas.spend import SpendEventBatchReverseRequest

        with pytest.raises(ValueError):
            SpendEventBatchReverseRequest(
                event_ids=[uuid4()],
                reason="短"  # 少于5个字符
            )

    def test_batch_reverse_request_too_many_ids_rejected(self):
        """测试超过100条被拒绝"""
        from backend.schemas.spend import SpendEventBatchReverseRequest

        with pytest.raises(ValueError):
            SpendEventBatchReverseRequest(
                event_ids=[uuid4() for _ in range(101)],
                reason="超过限制的冲正请求"
            )
