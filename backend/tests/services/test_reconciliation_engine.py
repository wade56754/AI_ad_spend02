"""
ReconciliationEngine 单元测试
Version: 1.0 (Financial SoT Phase 5)
Author: Claude协作开发

测试覆盖:
1. Invariants 校验 (5 条)
2. Excel 余额对比
3. 余额一致性校验
4. 批次完成条件检查
"""

import pytest
from datetime import date, datetime, timezone, timedelta
from decimal import Decimal
from unittest.mock import Mock, MagicMock, patch
from sqlalchemy.orm import Session

from backend.services.reconciliation_engine import (
    ReconciliationEngine,
    InvariantType,
    InvariantResult,
    ExcelComparisonResult,
    get_reconciliation_engine,
    run_invariants_check,
    compare_excel_balance
)
from backend.models.enums import ReconciliationBatchStatus, ReconciliationDetailStatus
from backend.exceptions.custom_exceptions import BusinessLogicError, ValidationError


# ========== Fixtures ==========

@pytest.fixture
def mock_db():
    """创建 Mock 数据库会话"""
    db = MagicMock(spec=Session)
    return db


@pytest.fixture
def engine(mock_db):
    """创建 ReconciliationEngine 实例"""
    return ReconciliationEngine(mock_db)


# ========== 基础测试 ==========

class TestReconciliationEngineInit:
    """测试 ReconciliationEngine 初始化"""

    def test_init_with_db(self, mock_db):
        """测试正常初始化"""
        engine = ReconciliationEngine(mock_db)
        assert engine.db == mock_db

    def test_invariants_defined(self, engine):
        """测试 Invariants 配置已定义"""
        assert len(engine.INVARIANTS) == 5
        for inv_type in InvariantType:
            assert inv_type in engine.INVARIANTS
            assert "name" in engine.INVARIANTS[inv_type]
            assert "sql" in engine.INVARIANTS[inv_type]

    def test_tolerance_values(self, engine):
        """测试容差值"""
        assert engine.TOLERANCE == Decimal("0.01")
        assert engine.RATE_TOLERANCE == Decimal("0.01")


# ========== Invariants 校验测试 ==========

class TestInvariantChecks:
    """测试 Invariants 校验"""

    def test_check_single_invariant_pass(self, engine, mock_db):
        """测试单个 Invariant 校验通过"""
        # Mock: 返回空结果（无违规）
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_db.execute.return_value = mock_result

        result = engine.check_invariant(InvariantType.DEBIT_CREDIT_BALANCE)

        assert isinstance(result, InvariantResult)
        assert result.invariant_id == "INV-001"
        assert result.name == "借贷平衡"
        assert result.passed is True
        assert len(result.violations) == 0

    def test_check_single_invariant_fail(self, engine, mock_db):
        """测试单个 Invariant 校验失败"""
        # Mock: 返回违规记录
        mock_row = MagicMock()
        mock_row._mapping = {
            "event_id": "evt-001",
            "total_debit": Decimal("100.00"),
            "total_credit": Decimal("90.00"),
            "imbalance": Decimal("10.00")
        }
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [mock_row]
        mock_db.execute.return_value = mock_result

        result = engine.check_invariant(InvariantType.DEBIT_CREDIT_BALANCE)

        assert result.passed is False
        assert len(result.violations) == 1

    def test_check_all_invariants(self, engine, mock_db):
        """测试运行所有 Invariants"""
        # Mock: 所有查询返回空结果
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_db.execute.return_value = mock_result

        results = engine.run_all_checks()

        assert len(results) == 5
        for inv_type in InvariantType:
            assert inv_type.value in results
            assert isinstance(results[inv_type.value], InvariantResult)

    def test_check_summary(self, engine, mock_db):
        """测试获取校验摘要"""
        # Mock: 所有查询返回空结果
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_db.execute.return_value = mock_result

        summary = engine.get_check_summary()

        assert "total_checks" in summary
        assert summary["total_checks"] == 5
        assert "passed" in summary
        assert "failed" in summary
        assert "all_passed" in summary
        assert "details" in summary

    def test_invariant_type_enum(self):
        """测试 InvariantType 枚举"""
        assert InvariantType.DEBIT_CREDIT_BALANCE.value == "INV-001"
        assert InvariantType.SUPPLIER_NON_NEGATIVE.value == "INV-002"
        assert InvariantType.NO_ORPHAN_ENTRIES.value == "INV-003"
        assert InvariantType.CONFIRMED_EVENTS_POSTED.value == "INV-004"
        assert InvariantType.BALANCE_FIELD_CONSISTENCY.value == "INV-005"

    def test_invariant_handles_missing_table(self, engine, mock_db):
        """测试处理表不存在的情况"""
        # Mock: 抛出表不存在异常
        mock_db.execute.side_effect = Exception("relation 'financial_events' does not exist")

        result = engine.check_invariant(InvariantType.NO_ORPHAN_ENTRIES)

        # 应该返回通过，因为表不存在时跳过校验
        assert result.passed is True
        assert len(result.violations) == 1
        assert "表不存在" in result.violations[0].get("note", "")


# ========== Excel 对比测试 ==========

class TestExcelComparison:
    """测试 Excel 余额对比"""

    def test_compare_with_excel_matched(self, engine, mock_db):
        """测试 Excel 对比匹配"""
        # Mock: 供应商查询
        mock_supplier = MagicMock()
        mock_supplier.name = "Test Supplier"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_supplier

        # Mock: Ledger 余额查询
        mock_db.query.return_value.filter.return_value.scalar.return_value = Decimal("1000.00")

        result = engine.compare_with_excel(
            entity_type="SUPPLIER",
            entity_id="1",
            excel_balance=Decimal("1000.00"),
            as_of_date=date.today()
        )

        assert isinstance(result, ExcelComparisonResult)
        assert result.matched is True
        assert result.difference == Decimal("0.00")

    def test_compare_with_excel_mismatched(self, engine, mock_db):
        """测试 Excel 对比不匹配"""
        # Mock
        mock_supplier = MagicMock()
        mock_supplier.name = "Test Supplier"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_supplier
        mock_db.query.return_value.filter.return_value.scalar.return_value = Decimal("1000.00")

        result = engine.compare_with_excel(
            entity_type="SUPPLIER",
            entity_id="1",
            excel_balance=Decimal("950.00"),
            as_of_date=date.today()
        )

        assert result.matched is False
        assert result.difference == Decimal("50.00")

    def test_batch_compare_with_excel(self, engine, mock_db):
        """测试批量 Excel 对比"""
        # Mock
        mock_supplier = MagicMock()
        mock_supplier.name = "Test Supplier"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_supplier
        mock_db.query.return_value.filter.return_value.scalar.return_value = Decimal("1000.00")

        comparisons = [
            {
                "entity_type": "SUPPLIER",
                "entity_id": "1",
                "excel_balance": Decimal("1000.00"),
                "as_of_date": date.today()
            },
            {
                "entity_type": "SUPPLIER",
                "entity_id": "2",
                "excel_balance": Decimal("2000.00"),
                "as_of_date": date.today()
            }
        ]

        results = engine.batch_compare_with_excel(comparisons)

        assert len(results) == 2
        assert all(isinstance(r, ExcelComparisonResult) for r in results)

    def test_comparison_result_to_dict(self):
        """测试 ExcelComparisonResult.to_dict()"""
        result = ExcelComparisonResult(
            entity_type="SUPPLIER",
            entity_id="1",
            entity_name="Test Supplier",
            system_balance=Decimal("1000.00"),
            excel_balance=Decimal("1000.00"),
            difference=Decimal("0"),
            difference_rate=Decimal("0"),
            matched=True,
            as_of_date=date.today()
        )

        d = result.to_dict()

        assert d["entity_type"] == "SUPPLIER"
        assert d["matched"] is True
        assert "system_balance" in d
        assert "excel_balance" in d


# ========== 余额一致性校验测试 ==========

class TestBalanceConsistency:
    """测试余额一致性校验"""

    def test_validate_balance_consistency_consistent(self, engine, mock_db):
        """测试余额一致"""
        # Mock: 实体查询
        mock_supplier = MagicMock()
        mock_supplier.balance = Decimal("1000.00")
        mock_db.query.return_value.filter.return_value.first.return_value = mock_supplier

        # Mock: Ledger 余额
        mock_db.query.return_value.filter.return_value.scalar.return_value = Decimal("1000.00")

        result = engine.validate_balance_consistency(
            entity_type="SUPPLIER",
            entity_id="1"
        )

        assert result["is_consistent"] is True
        assert Decimal(result["difference"]) == Decimal("0")

    def test_validate_balance_consistency_inconsistent(self, engine, mock_db):
        """测试余额不一致"""
        # Mock: 实体查询
        mock_supplier = MagicMock()
        mock_supplier.balance = Decimal("1000.00")
        mock_db.query.return_value.filter.return_value.first.return_value = mock_supplier

        # Mock: Ledger 余额不一致
        mock_db.query.return_value.filter.return_value.scalar.return_value = Decimal("900.00")

        result = engine.validate_balance_consistency(
            entity_type="SUPPLIER",
            entity_id="1"
        )

        assert result["is_consistent"] is False
        assert Decimal(result["difference"]) == Decimal("100.00")


# ========== 快照集成测试 ==========

class TestSnapshotIntegration:
    """测试与 BalanceSnapshotService 集成"""

    def test_get_historical_balance_from_snapshot(self, engine, mock_db):
        """测试从快照获取历史余额"""
        mock_snapshot = MagicMock()
        mock_snapshot.balance = Decimal("1000.00")
        mock_db.query.return_value.filter.return_value.first.return_value = mock_snapshot

        balance = engine.get_historical_balance_from_snapshot(
            entity_type="SUPPLIER",
            entity_id="1",
            as_of_date=date.today()
        )

        assert balance == Decimal("1000.00")

    def test_get_historical_balance_no_snapshot(self, engine, mock_db):
        """测试快照不存在的情况"""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        balance = engine.get_historical_balance_from_snapshot(
            entity_type="SUPPLIER",
            entity_id="1",
            as_of_date=date.today()
        )

        assert balance is None

    def test_compare_snapshot_with_ledger(self, engine, mock_db):
        """测试对比快照与 Ledger"""
        # Mock: 快照存在
        mock_snapshot = MagicMock()
        mock_snapshot.balance = Decimal("1000.00")

        # 第一次查询返回快照，第二次返回 Ledger 余额
        mock_db.query.return_value.filter.return_value.first.return_value = mock_snapshot
        mock_db.query.return_value.filter.return_value.scalar.return_value = Decimal("1000.00")

        result = engine.compare_snapshot_with_ledger(
            entity_type="SUPPLIER",
            entity_id="1",
            as_of_date=date.today()
        )

        assert result["has_snapshot"] is True
        assert result["is_consistent"] is True


# ========== 批次完成条件测试 ==========

class TestBatchCompletion:
    """测试批次完成条件检查"""

    def test_calculate_batch_difference(self, engine, mock_db):
        """测试计算批次差异"""
        # Mock: 批次
        mock_batch = MagicMock()
        mock_batch.id = 1
        mock_batch.batch_code = "REC-001"
        mock_batch.period_start = date.today()
        mock_batch.period_end = date.today()
        mock_batch.status = ReconciliationBatchStatus.PENDING_REVIEW.value
        mock_db.query.return_value.filter.return_value.first.return_value = mock_batch

        # Mock: 明细
        mock_detail = MagicMock()
        mock_detail.system_spend = Decimal("100.00")
        mock_detail.actual_spend = Decimal("90.00")
        mock_detail.discrepancy = Decimal("10.00")
        mock_detail.status = ReconciliationDetailStatus.PENDING.value
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_detail]

        result = engine.calculate_batch_difference(1)

        assert result["batch_id"] == 1
        assert "total_discrepancy" in result
        assert "can_complete" in result

    def test_check_batch_completion_conditions_all_pass(self, engine, mock_db):
        """测试批次完成条件全部通过"""
        # Mock: 批次
        mock_batch = MagicMock()
        mock_batch.id = 1
        mock_batch.status = ReconciliationBatchStatus.APPROVED.value
        mock_db.query.return_value.filter.return_value.first.return_value = mock_batch

        # Mock: 无 pending 明细
        mock_db.query.return_value.filter.return_value.count.return_value = 0

        # Mock: 无 adjusted 明细
        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = engine.check_batch_completion_conditions(1)

        assert result["all_passed"] is True
        assert result["can_complete"] is True

    def test_check_batch_completion_conditions_pending_exists(self, engine, mock_db):
        """测试存在 pending 明细时无法完成"""
        # Mock: 批次
        mock_batch = MagicMock()
        mock_batch.id = 1
        mock_batch.status = ReconciliationBatchStatus.APPROVED.value
        mock_db.query.return_value.filter.return_value.first.return_value = mock_batch

        # Mock: 有 pending 明细
        mock_db.query.return_value.filter.return_value.count.return_value = 5

        # Mock: 无 adjusted 明细
        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = engine.check_batch_completion_conditions(1)

        assert result["all_passed"] is False
        assert result["can_complete"] is False

    def test_batch_not_found(self, engine, mock_db):
        """测试批次不存在时抛出异常"""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(BusinessLogicError) as exc_info:
            engine.calculate_batch_difference(999)

        assert exc_info.value.error_code == "RECON_020"


# ========== 便捷函数测试 ==========

class TestConvenienceFunctions:
    """测试便捷函数"""

    def test_get_reconciliation_engine(self, mock_db):
        """测试 get_reconciliation_engine"""
        engine = get_reconciliation_engine(mock_db)
        assert isinstance(engine, ReconciliationEngine)

    def test_run_invariants_check(self, mock_db):
        """测试 run_invariants_check"""
        # Mock: 所有查询返回空结果
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_db.execute.return_value = mock_result

        summary = run_invariants_check(mock_db)

        assert "total_checks" in summary
        assert "all_passed" in summary


# ========== InvariantResult 测试 ==========

class TestInvariantResult:
    """测试 InvariantResult 数据类"""

    def test_invariant_result_to_dict(self):
        """测试 to_dict 方法"""
        result = InvariantResult(
            invariant_id="INV-001",
            name="借贷平衡",
            passed=True,
            violations=[],
            checked_at=datetime.now(timezone.utc)
        )

        d = result.to_dict()

        assert d["invariant_id"] == "INV-001"
        assert d["name"] == "借贷平衡"
        assert d["passed"] is True
        assert d["violation_count"] == 0

    def test_invariant_result_with_violations(self):
        """测试有违规记录的结果"""
        violations = [{"id": i} for i in range(15)]  # 15 条违规

        result = InvariantResult(
            invariant_id="INV-001",
            name="借贷平衡",
            passed=False,
            violations=violations,
            checked_at=datetime.now(timezone.utc)
        )

        d = result.to_dict()

        assert d["passed"] is False
        assert d["violation_count"] == 15
        assert len(d["violations"]) == 10  # 最多返回 10 条


# ========== 私有方法测试 ==========

class TestPrivateMethods:
    """测试私有辅助方法"""

    def test_get_entity_name_supplier(self, engine, mock_db):
        """测试获取供应商名称"""
        mock_supplier = MagicMock()
        mock_supplier.name = "Test Supplier"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_supplier

        name = engine._get_entity_name("SUPPLIER", "1")
        assert name == "Test Supplier"

    def test_get_entity_name_not_found(self, engine, mock_db):
        """测试实体不存在时返回默认名称"""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        name = engine._get_entity_name("SUPPLIER", "999")
        assert name == "Supplier#999"

    def test_get_entity_field_balance(self, engine, mock_db):
        """测试获取实体 balance 字段"""
        mock_supplier = MagicMock()
        mock_supplier.balance = Decimal("1000.00")
        mock_db.query.return_value.filter.return_value.first.return_value = mock_supplier

        balance = engine._get_entity_field_balance("SUPPLIER", "1")
        assert balance == Decimal("1000.00")

    def test_calculate_ledger_balance(self, engine, mock_db):
        """测试从 Ledger 计算余额"""
        mock_db.query.return_value.filter.return_value.scalar.return_value = Decimal("1500.00")

        balance = engine._calculate_ledger_balance(
            entity_type="SUPPLIER",
            entity_id="1",
            as_of_date=date.today()
        )

        assert balance == Decimal("1500.00")

    def test_calculate_ledger_balance_no_entries(self, engine, mock_db):
        """测试无分录时返回 0"""
        mock_db.query.return_value.filter.return_value.scalar.return_value = None

        balance = engine._calculate_ledger_balance(
            entity_type="SUPPLIER",
            entity_id="1",
            as_of_date=date.today()
        )

        assert balance == Decimal("0")
