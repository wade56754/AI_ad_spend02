"""
BalanceSnapshotService 单元测试
Version: 1.0
Author: Claude Code

Phase 4 Financial SoT - 余额快照服务测试

测试覆盖:
1. 实体类型验证
2. 日期验证
3. 快照创建 (单个/批量)
4. 余额计算
5. 历史余额查询
6. 一致性验证
7. 缺失快照填充
"""

import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, MagicMock, patch
from uuid import uuid4

from backend.services.balance_snapshot_service import (
    BalanceSnapshotService,
    create_daily_snapshot,
    get_balance_at_date
)
from backend.models.finance.balance_snapshot import BalanceSnapshot, EntityType
from backend.models.finance.ledger import LedgerEntry
from backend.exceptions.custom_exceptions import ValidationError, BusinessLogicError


class TestEntityTypeValidation:
    """实体类型验证测试"""

    def test_valid_entity_types(self):
        """测试有效的实体类型"""
        valid_types = ["SUPPLIER", "PROJECT", "ACCOUNT", "TEAM"]
        for entity_type in valid_types:
            # Should not raise
            BalanceSnapshotService._validate_entity_type(entity_type)

    def test_invalid_entity_type_raises_error(self):
        """测试无效实体类型抛出错误"""
        with pytest.raises(ValidationError) as exc_info:
            BalanceSnapshotService._validate_entity_type("INVALID")
        assert "无效的实体类型" in str(exc_info.value.message)

    def test_empty_entity_type_raises_error(self):
        """测试空实体类型抛出错误"""
        with pytest.raises(ValidationError):
            BalanceSnapshotService._validate_entity_type("")

    def test_lowercase_entity_type_raises_error(self):
        """测试小写实体类型抛出错误 (必须大写)"""
        with pytest.raises(ValidationError):
            BalanceSnapshotService._validate_entity_type("supplier")


class TestDateValidation:
    """日期验证测试"""

    def test_future_date_raises_error(self):
        """测试未来日期抛出错误"""
        db = Mock()
        future_date = date.today() + timedelta(days=1)

        with pytest.raises(ValidationError) as exc_info:
            BalanceSnapshotService.create_daily_snapshot(
                entity_type="SUPPLIER",
                entity_id="test-123",
                snapshot_date=future_date,
                db=db
            )
        assert "不能是未来" in str(exc_info.value.message)

    def test_today_date_is_valid(self):
        """测试今天日期有效"""
        db = Mock()
        today = date.today()

        # Mock the ledger calculation
        with patch.object(
            BalanceSnapshotService,
            'calculate_balance_from_ledger',
            return_value={
                "balance": Decimal("1000.00"),
                "total_debit": Decimal("500.00"),
                "total_credit": Decimal("1500.00")
            }
        ):
            with patch.object(BalanceSnapshot, 'upsert_snapshot') as mock_upsert:
                mock_snapshot = Mock()
                mock_snapshot.balance = Decimal("1000.00")
                mock_upsert.return_value = mock_snapshot

                result = BalanceSnapshotService.create_daily_snapshot(
                    entity_type="SUPPLIER",
                    entity_id="test-123",
                    snapshot_date=today,
                    db=db
                )

                assert result is not None
                mock_upsert.assert_called_once()

    def test_past_date_is_valid(self):
        """测试过去日期有效"""
        db = Mock()
        past_date = date.today() - timedelta(days=30)

        with patch.object(
            BalanceSnapshotService,
            'calculate_balance_from_ledger',
            return_value={
                "balance": Decimal("500.00"),
                "total_debit": Decimal("200.00"),
                "total_credit": Decimal("700.00")
            }
        ):
            with patch.object(BalanceSnapshot, 'upsert_snapshot') as mock_upsert:
                mock_snapshot = Mock()
                mock_snapshot.balance = Decimal("500.00")
                mock_upsert.return_value = mock_snapshot

                result = BalanceSnapshotService.create_daily_snapshot(
                    entity_type="SUPPLIER",
                    entity_id="test-123",
                    snapshot_date=past_date,
                    db=db
                )

                assert result is not None

    def test_invalid_date_range_raises_error(self):
        """测试无效日期范围抛出错误"""
        db = Mock()
        start_date = date(2025, 1, 15)
        end_date = date(2025, 1, 10)  # end < start

        with pytest.raises(ValidationError) as exc_info:
            BalanceSnapshotService.get_entity_balance_history(
                entity_type="SUPPLIER",
                entity_id="test-123",
                start_date=start_date,
                end_date=end_date,
                db=db
            )
        assert "开始日期不能晚于结束日期" in str(exc_info.value.message)


class TestCalculateBalanceFromLedger:
    """从账本计算余额测试"""

    def test_calculate_with_entries(self):
        """测试有分录时的余额计算"""
        db = Mock()

        # Mock query result
        mock_result = Mock()
        mock_result.total_debit = Decimal("500.00")
        mock_result.total_credit = Decimal("1500.00")

        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_result
        db.query.return_value = mock_query

        result = BalanceSnapshotService.calculate_balance_from_ledger(
            entity_type="SUPPLIER",
            entity_id="supplier-123",
            as_of_date=date.today(),
            db=db
        )

        assert result["balance"] == Decimal("1000.00")  # 1500 - 500
        assert result["total_debit"] == Decimal("500.00")
        assert result["total_credit"] == Decimal("1500.00")

    def test_calculate_with_no_entries(self):
        """测试无分录时返回零余额"""
        db = Mock()

        # Mock empty result
        mock_result = Mock()
        mock_result.total_debit = None
        mock_result.total_credit = None

        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_result
        db.query.return_value = mock_query

        result = BalanceSnapshotService.calculate_balance_from_ledger(
            entity_type="SUPPLIER",
            entity_id="supplier-new",
            as_of_date=date.today(),
            db=db
        )

        assert result["balance"] == Decimal("0")
        assert result["total_debit"] == Decimal("0")
        assert result["total_credit"] == Decimal("0")

    def test_calculate_negative_balance(self):
        """测试负余额计算"""
        db = Mock()

        mock_result = Mock()
        mock_result.total_debit = Decimal("2000.00")
        mock_result.total_credit = Decimal("500.00")

        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_result
        db.query.return_value = mock_query

        result = BalanceSnapshotService.calculate_balance_from_ledger(
            entity_type="ACCOUNT",
            entity_id="account-123",
            as_of_date=date.today(),
            db=db
        )

        assert result["balance"] == Decimal("-1500.00")  # 500 - 2000


class TestCreateDailySnapshot:
    """创建每日快照测试"""

    def test_create_snapshot_success(self):
        """测试成功创建快照"""
        db = Mock()

        with patch.object(
            BalanceSnapshotService,
            'calculate_balance_from_ledger',
            return_value={
                "balance": Decimal("1000.00"),
                "total_debit": Decimal("500.00"),
                "total_credit": Decimal("1500.00")
            }
        ):
            with patch.object(BalanceSnapshot, 'upsert_snapshot') as mock_upsert:
                mock_snapshot = Mock()
                mock_snapshot.balance = Decimal("1000.00")
                mock_snapshot.entity_type = "SUPPLIER"
                mock_snapshot.entity_id = "supplier-123"
                mock_upsert.return_value = mock_snapshot

                result = BalanceSnapshotService.create_daily_snapshot(
                    entity_type="SUPPLIER",
                    entity_id="supplier-123",
                    snapshot_date=date.today(),
                    db=db
                )

                assert result.balance == Decimal("1000.00")
                mock_upsert.assert_called_once_with(
                    session=db,
                    entity_type="SUPPLIER",
                    entity_id="supplier-123",
                    snapshot_date=date.today(),
                    balance=Decimal("1000.00"),
                    total_debit=Decimal("500.00"),
                    total_credit=Decimal("1500.00"),
                    currency="USD"
                )

    def test_create_snapshot_with_custom_currency(self):
        """测试使用自定义币种创建快照"""
        db = Mock()

        with patch.object(
            BalanceSnapshotService,
            'calculate_balance_from_ledger',
            return_value={
                "balance": Decimal("8000.00"),
                "total_debit": Decimal("2000.00"),
                "total_credit": Decimal("10000.00")
            }
        ):
            with patch.object(BalanceSnapshot, 'upsert_snapshot') as mock_upsert:
                mock_snapshot = Mock()
                mock_upsert.return_value = mock_snapshot

                BalanceSnapshotService.create_daily_snapshot(
                    entity_type="PROJECT",
                    entity_id="project-123",
                    snapshot_date=date.today(),
                    db=db,
                    currency="CNY"
                )

                call_args = mock_upsert.call_args
                assert call_args.kwargs["currency"] == "CNY"

    def test_create_snapshot_exception_handling(self):
        """测试快照创建异常处理"""
        db = Mock()

        with patch.object(
            BalanceSnapshotService,
            'calculate_balance_from_ledger',
            side_effect=Exception("Database error")
        ):
            with pytest.raises(BusinessLogicError) as exc_info:
                BalanceSnapshotService.create_daily_snapshot(
                    entity_type="SUPPLIER",
                    entity_id="supplier-123",
                    snapshot_date=date.today(),
                    db=db
                )
            assert "快照创建失败" in str(exc_info.value.message)


class TestCreateAllSnapshots:
    """批量创建快照测试"""

    def test_create_all_snapshots_success(self):
        """测试批量创建快照成功"""
        db = Mock()

        # Mock get_entities_with_ledger
        with patch.object(
            BalanceSnapshotService,
            '_get_entities_with_ledger',
            return_value=[
                ("SUPPLIER", "supplier-1"),
                ("SUPPLIER", "supplier-2"),
                ("PROJECT", "project-1")
            ]
        ):
            with patch.object(
                BalanceSnapshotService,
                'create_daily_snapshot'
            ) as mock_create:
                mock_snapshot = Mock()
                mock_snapshot.balance = Decimal("1000.00")
                mock_create.return_value = mock_snapshot

                result = BalanceSnapshotService.create_all_snapshots(
                    snapshot_date=date.today(),
                    db=db
                )

                assert result["success"] == 3
                assert result["failed"] == 0
                assert len(result["details"]) == 3
                assert mock_create.call_count == 3

    def test_create_all_snapshots_with_filter(self):
        """测试按实体类型过滤批量创建"""
        db = Mock()

        with patch.object(
            BalanceSnapshotService,
            '_get_entities_with_ledger',
            return_value=[
                ("SUPPLIER", "supplier-1"),
                ("SUPPLIER", "supplier-2")
            ]
        ):
            with patch.object(
                BalanceSnapshotService,
                'create_daily_snapshot'
            ) as mock_create:
                mock_snapshot = Mock()
                mock_snapshot.balance = Decimal("1000.00")
                mock_create.return_value = mock_snapshot

                result = BalanceSnapshotService.create_all_snapshots(
                    snapshot_date=date.today(),
                    db=db,
                    entity_types=["SUPPLIER"]
                )

                assert result["success"] == 2

    def test_create_all_snapshots_partial_failure(self):
        """测试部分失败的批量创建"""
        db = Mock()

        with patch.object(
            BalanceSnapshotService,
            '_get_entities_with_ledger',
            return_value=[
                ("SUPPLIER", "supplier-1"),
                ("SUPPLIER", "supplier-2"),
                ("SUPPLIER", "supplier-3")
            ]
        ):
            # First succeeds, second fails, third succeeds
            mock_snapshot = Mock()
            mock_snapshot.balance = Decimal("1000.00")

            with patch.object(
                BalanceSnapshotService,
                'create_daily_snapshot',
                side_effect=[
                    mock_snapshot,
                    Exception("Failed"),
                    mock_snapshot
                ]
            ):
                result = BalanceSnapshotService.create_all_snapshots(
                    snapshot_date=date.today(),
                    db=db
                )

                assert result["success"] == 2
                assert result["failed"] == 1


class TestGetBalanceAtDate:
    """获取历史余额测试"""

    def test_get_balance_from_snapshot(self):
        """测试从快照获取余额"""
        db = Mock()

        mock_snapshot = Mock()
        mock_snapshot.balance = Decimal("1500.00")

        with patch.object(BalanceSnapshot, 'get_snapshot', return_value=mock_snapshot):
            result = BalanceSnapshotService.get_balance_at_date(
                entity_type="SUPPLIER",
                entity_id="supplier-123",
                as_of_date=date(2025, 1, 15),
                db=db,
                use_snapshot=True
            )

            assert result == Decimal("1500.00")

    def test_get_balance_from_ledger_when_no_snapshot(self):
        """测试无快照时从账本计算余额"""
        db = Mock()

        with patch.object(BalanceSnapshot, 'get_snapshot', return_value=None):
            with patch.object(BalanceSnapshot, 'get_latest_snapshot', return_value=None):
                with patch.object(
                    BalanceSnapshotService,
                    'calculate_balance_from_ledger',
                    return_value={
                        "balance": Decimal("2000.00"),
                        "total_debit": Decimal("500.00"),
                        "total_credit": Decimal("2500.00")
                    }
                ):
                    result = BalanceSnapshotService.get_balance_at_date(
                        entity_type="SUPPLIER",
                        entity_id="supplier-123",
                        as_of_date=date(2025, 1, 15),
                        db=db
                    )

                    assert result == Decimal("2000.00")

    def test_get_balance_bypass_snapshot(self):
        """测试绕过快照直接从账本计算"""
        db = Mock()

        with patch.object(
            BalanceSnapshotService,
            'calculate_balance_from_ledger',
            return_value={
                "balance": Decimal("3000.00"),
                "total_debit": Decimal("1000.00"),
                "total_credit": Decimal("4000.00")
            }
        ):
            result = BalanceSnapshotService.get_balance_at_date(
                entity_type="PROJECT",
                entity_id="project-123",
                as_of_date=date(2025, 1, 15),
                db=db,
                use_snapshot=False
            )

            assert result == Decimal("3000.00")


class TestGetEntityBalanceHistory:
    """获取余额历史测试"""

    def test_get_history_success(self):
        """测试成功获取余额历史"""
        db = Mock()

        mock_snapshots = [
            Mock(
                snapshot_date=date(2025, 1, 10),
                balance=Decimal("1000.00"),
                total_debit=Decimal("500.00"),
                total_credit=Decimal("1500.00"),
                currency="USD",
                calculated_at=datetime(2025, 1, 10, 23, 59, 59)
            ),
            Mock(
                snapshot_date=date(2025, 1, 11),
                balance=Decimal("1200.00"),
                total_debit=Decimal("600.00"),
                total_credit=Decimal("1800.00"),
                currency="USD",
                calculated_at=datetime(2025, 1, 11, 23, 59, 59)
            )
        ]

        with patch.object(BalanceSnapshot, 'get_entity_history', return_value=mock_snapshots):
            result = BalanceSnapshotService.get_entity_balance_history(
                entity_type="SUPPLIER",
                entity_id="supplier-123",
                start_date=date(2025, 1, 10),
                end_date=date(2025, 1, 15),
                db=db
            )

            assert len(result) == 2
            assert result[0]["balance"] == 1000.00
            assert result[1]["balance"] == 1200.00

    def test_get_history_empty(self):
        """测试空历史记录"""
        db = Mock()

        with patch.object(BalanceSnapshot, 'get_entity_history', return_value=[]):
            result = BalanceSnapshotService.get_entity_balance_history(
                entity_type="SUPPLIER",
                entity_id="supplier-new",
                start_date=date(2025, 1, 1),
                end_date=date(2025, 1, 31),
                db=db
            )

            assert result == []


class TestValidateBalanceConsistency:
    """余额一致性验证测试"""

    def test_consistent_balance(self):
        """测试余额一致"""
        db = Mock()

        with patch.object(
            BalanceSnapshotService,
            'calculate_balance_from_ledger',
            return_value={
                "balance": Decimal("1000.00"),
                "total_debit": Decimal("500.00"),
                "total_credit": Decimal("1500.00")
            }
        ):
            result = BalanceSnapshotService.validate_balance_consistency(
                entity_type="SUPPLIER",
                entity_id="supplier-123",
                expected_balance=Decimal("1000.00"),
                db=db
            )

            assert result["consistent"] is True
            assert result["difference"] == 0.0

    def test_inconsistent_balance(self):
        """测试余额不一致"""
        db = Mock()

        with patch.object(
            BalanceSnapshotService,
            'calculate_balance_from_ledger',
            return_value={
                "balance": Decimal("1000.00"),
                "total_debit": Decimal("500.00"),
                "total_credit": Decimal("1500.00")
            }
        ):
            result = BalanceSnapshotService.validate_balance_consistency(
                entity_type="SUPPLIER",
                entity_id="supplier-123",
                expected_balance=Decimal("1100.00"),
                db=db
            )

            assert result["consistent"] is False
            assert result["difference"] == 100.0

    def test_within_tolerance(self):
        """测试在容差范围内"""
        db = Mock()

        with patch.object(
            BalanceSnapshotService,
            'calculate_balance_from_ledger',
            return_value={
                "balance": Decimal("1000.005"),
                "total_debit": Decimal("500.00"),
                "total_credit": Decimal("1500.005")
            }
        ):
            result = BalanceSnapshotService.validate_balance_consistency(
                entity_type="SUPPLIER",
                entity_id="supplier-123",
                expected_balance=Decimal("1000.00"),
                db=db,
                tolerance=Decimal("0.01")
            )

            assert result["consistent"] is True
            assert result["within_tolerance"] is True


class TestBatchValidateConsistency:
    """批量一致性验证测试"""

    def test_batch_validate_success(self):
        """测试批量验证成功"""
        db = Mock()

        entities = [
            ("SUPPLIER", "supplier-1", Decimal("1000.00")),
            ("SUPPLIER", "supplier-2", Decimal("2000.00")),
            ("PROJECT", "project-1", Decimal("5000.00"))
        ]

        with patch.object(
            BalanceSnapshotService,
            'validate_balance_consistency'
        ) as mock_validate:
            mock_validate.return_value = {
                "consistent": True,
                "expected_balance": 1000.0,
                "calculated_balance": 1000.0,
                "difference": 0.0,
                "within_tolerance": True
            }

            result = BalanceSnapshotService.batch_validate_consistency(
                entities=entities,
                db=db
            )

            assert result["total"] == 3
            assert result["consistent"] == 3
            assert result["inconsistent"] == 0


class TestFillMissingSnapshots:
    """填充缺失快照测试"""

    def test_fill_missing_snapshots(self):
        """测试填充缺失快照"""
        db = Mock()

        # Mock existing snapshots
        mock_existing = [
            Mock(snapshot_date=date(2025, 1, 10)),
            Mock(snapshot_date=date(2025, 1, 12))
        ]

        with patch.object(BalanceSnapshot, 'get_entity_history', return_value=mock_existing):
            with patch.object(
                BalanceSnapshotService,
                'create_daily_snapshot'
            ) as mock_create:
                mock_snapshot = Mock()
                mock_create.return_value = mock_snapshot

                result = BalanceSnapshotService.fill_missing_snapshots(
                    entity_type="SUPPLIER",
                    entity_id="supplier-123",
                    start_date=date(2025, 1, 10),
                    end_date=date(2025, 1, 13),
                    db=db
                )

                # 4 days total, 2 existing, 2 to create
                assert result["total_days"] == 4
                assert result["existing"] == 2
                assert result["created"] == 2

    def test_fill_no_missing_snapshots(self):
        """测试无缺失快照"""
        db = Mock()

        # All dates have snapshots
        mock_existing = [
            Mock(snapshot_date=date(2025, 1, 10)),
            Mock(snapshot_date=date(2025, 1, 11)),
            Mock(snapshot_date=date(2025, 1, 12))
        ]

        with patch.object(BalanceSnapshot, 'get_entity_history', return_value=mock_existing):
            with patch.object(
                BalanceSnapshotService,
                'create_daily_snapshot'
            ) as mock_create:
                result = BalanceSnapshotService.fill_missing_snapshots(
                    entity_type="SUPPLIER",
                    entity_id="supplier-123",
                    start_date=date(2025, 1, 10),
                    end_date=date(2025, 1, 12),
                    db=db
                )

                assert result["created"] == 0
                mock_create.assert_not_called()


class TestConvenienceFunctions:
    """便捷函数测试"""

    def test_create_daily_snapshot_function(self):
        """测试 create_daily_snapshot 便捷函数"""
        db = Mock()

        with patch.object(
            BalanceSnapshotService,
            'create_daily_snapshot'
        ) as mock_method:
            mock_snapshot = Mock()
            mock_method.return_value = mock_snapshot

            result = create_daily_snapshot(
                entity_type="SUPPLIER",
                entity_id="supplier-123",
                snapshot_date=date.today(),
                db=db
            )

            assert result == mock_snapshot
            mock_method.assert_called_once()

    def test_get_balance_at_date_function(self):
        """测试 get_balance_at_date 便捷函数"""
        db = Mock()

        with patch.object(
            BalanceSnapshotService,
            'get_balance_at_date',
            return_value=Decimal("1500.00")
        ) as mock_method:
            result = get_balance_at_date(
                entity_type="SUPPLIER",
                entity_id="supplier-123",
                as_of_date=date.today(),
                db=db
            )

            assert result == Decimal("1500.00")
            mock_method.assert_called_once()
