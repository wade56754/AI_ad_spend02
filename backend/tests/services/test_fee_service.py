"""
FeeService 单元测试
Version: 1.0 (Financial SoT Phase 4)
Author: Claude协作开发

测试覆盖:
1. 手续费计算 (PERCENTAGE/FIXED)
2. 含费金额计算
3. 费率配置管理
4. 边界条件和异常处理
"""

import pytest
from datetime import date, datetime, timezone
from decimal import Decimal
from unittest.mock import Mock, MagicMock, patch
from sqlalchemy.orm import Session

from backend.services.fee_service import (
    FeeService,
    FeeType,
    get_fee_service,
    calculate_fee,
    calculate_cost
)
from backend.models.finance.supplier import Supplier
from backend.exceptions.custom_exceptions import (
    BusinessLogicError,
    ResourceNotFoundError,
    ValidationError
)


# ========== Fixtures ==========

@pytest.fixture
def mock_db():
    """创建 Mock 数据库会话"""
    db = MagicMock(spec=Session)
    return db


@pytest.fixture
def mock_supplier():
    """创建 Mock 供应商"""
    supplier = MagicMock(spec=Supplier)
    supplier.id = 1
    supplier.name = "Test Supplier"
    supplier.fee_rate = Decimal("0.10")  # 10%
    supplier.fee_type = FeeType.PERCENTAGE
    supplier.platform = "FB"
    return supplier


@pytest.fixture
def service(mock_db):
    """创建 FeeService 实例"""
    return FeeService(mock_db)


# ========== 基础测试 ==========

class TestFeeServiceInit:
    """测试 FeeService 初始化"""

    def test_init_with_db(self, mock_db):
        """测试正常初始化"""
        service = FeeService(mock_db)
        assert service.db == mock_db

    def test_default_values(self, service):
        """测试默认值"""
        assert service.DECIMAL_PLACES == 2
        assert service.RATE_DECIMAL_PLACES == 4
        assert service.DEFAULT_FEE_RATE == Decimal("0.10")
        assert service.DEFAULT_FEE_TYPE == FeeType.PERCENTAGE
        assert service.MIN_FEE_RATE == Decimal("0")
        assert service.MAX_FEE_RATE == Decimal("1")


# ========== 手续费计算测试 ==========

class TestCalculateFee:
    """测试手续费计算"""

    def test_calculate_fee_percentage(self, service, mock_db, mock_supplier):
        """测试百分比计算"""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_supplier

        spend = Decimal("1000.00")
        fee = service.calculate_fee(spend, supplier_id=1)

        # 10% of 1000 = 100
        assert fee == Decimal("100.00")

    def test_calculate_fee_fixed(self, service, mock_db, mock_supplier):
        """测试固定金额计算"""
        mock_supplier.fee_type = FeeType.FIXED
        mock_supplier.fee_rate = Decimal("50.00")
        mock_db.query.return_value.filter.return_value.first.return_value = mock_supplier

        spend = Decimal("1000.00")
        fee = service.calculate_fee(spend, supplier_id=1)

        # Fixed fee = 50
        assert fee == Decimal("50.00")

    def test_calculate_fee_zero_rate(self, service, mock_db, mock_supplier):
        """测试零费率"""
        mock_supplier.fee_rate = Decimal("0")
        mock_db.query.return_value.filter.return_value.first.return_value = mock_supplier

        spend = Decimal("1000.00")
        fee = service.calculate_fee(spend, supplier_id=1)

        assert fee == Decimal("0.00")

    def test_calculate_fee_supplier_not_found(self, service, mock_db):
        """测试供应商不存在"""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ResourceNotFoundError) as exc_info:
            service.calculate_fee(Decimal("1000.00"), supplier_id=999)

        assert exc_info.value.error_code == "FEE_001"

    def test_calculate_fee_negative_spend(self, service, mock_db, mock_supplier):
        """测试负数消耗金额"""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_supplier

        with pytest.raises(ValidationError) as exc_info:
            service.calculate_fee(Decimal("-100.00"), supplier_id=1)

        assert exc_info.value.error_code == "FEE_011"

    def test_calculate_fee_default_rate(self, service, mock_db, mock_supplier):
        """测试使用默认费率"""
        mock_supplier.fee_rate = None
        mock_db.query.return_value.filter.return_value.first.return_value = mock_supplier

        spend = Decimal("1000.00")
        fee = service.calculate_fee(spend, supplier_id=1)

        # Default 10% of 1000 = 100
        assert fee == Decimal("100.00")


class TestCalculateFeeByRate:
    """测试按费率计算"""

    def test_calculate_fee_by_rate_percentage(self, service):
        """测试百分比计算"""
        fee = service.calculate_fee_by_rate(
            spend_amount=Decimal("1000.00"),
            fee_rate=Decimal("0.05"),
            fee_type=FeeType.PERCENTAGE
        )
        assert fee == Decimal("50.00")

    def test_calculate_fee_by_rate_fixed(self, service):
        """测试固定金额计算"""
        fee = service.calculate_fee_by_rate(
            spend_amount=Decimal("1000.00"),
            fee_rate=Decimal("25.00"),
            fee_type=FeeType.FIXED
        )
        assert fee == Decimal("25.00")

    def test_calculate_fee_by_rate_invalid_rate(self, service):
        """测试无效费率"""
        with pytest.raises(ValidationError) as exc_info:
            service.calculate_fee_by_rate(
                spend_amount=Decimal("1000.00"),
                fee_rate=Decimal("1.5"),  # > 1
                fee_type=FeeType.PERCENTAGE
            )
        assert exc_info.value.error_code == "FEE_002"

    def test_calculate_fee_by_rate_negative_rate(self, service):
        """测试负费率"""
        with pytest.raises(ValidationError) as exc_info:
            service.calculate_fee_by_rate(
                spend_amount=Decimal("1000.00"),
                fee_rate=Decimal("-0.05"),
                fee_type=FeeType.PERCENTAGE
            )
        assert exc_info.value.error_code == "FEE_002"

    def test_calculate_fee_by_rate_invalid_type(self, service):
        """测试无效费率类型"""
        with pytest.raises(ValidationError) as exc_info:
            service.calculate_fee_by_rate(
                spend_amount=Decimal("1000.00"),
                fee_rate=Decimal("0.05"),
                fee_type="INVALID"
            )
        assert exc_info.value.error_code == "FEE_003"


# ========== 含费金额计算测试 ==========

class TestCalculateGrossAmount:
    """测试含费金额计算"""

    def test_calculate_gross_amount(self, service):
        """测试正常计算"""
        gross = service.calculate_gross_amount(
            spend_amount=Decimal("1000.00"),
            fee_amount=Decimal("100.00")
        )
        assert gross == Decimal("1100.00")

    def test_calculate_gross_amount_zero_fee(self, service):
        """测试零手续费"""
        gross = service.calculate_gross_amount(
            spend_amount=Decimal("1000.00"),
            fee_amount=Decimal("0.00")
        )
        assert gross == Decimal("1000.00")

    def test_calculate_gross_amount_rounding(self, service):
        """测试四舍五入"""
        gross = service.calculate_gross_amount(
            spend_amount=Decimal("100.005"),
            fee_amount=Decimal("10.003")
        )
        # 100.005 + 10.003 = 110.008 -> 110.01
        assert gross == Decimal("110.01")


# ========== 成本计算测试 ==========

class TestCalculateCost:
    """测试成本计算"""

    def test_calculate_cost(self, service, mock_db, mock_supplier):
        """测试成本计算"""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_supplier

        fee, cost, fee_rate = service.calculate_cost(
            real_spend=Decimal("1000.00"),
            supplier_id=1
        )

        assert fee == Decimal("100.00")  # 10%
        assert cost == Decimal("1100.00")  # 1000 + 100
        assert fee_rate == Decimal("0.10")

    def test_calculate_cost_supplier_not_found(self, service, mock_db):
        """测试供应商不存在"""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ResourceNotFoundError):
            service.calculate_cost(Decimal("1000.00"), supplier_id=999)


# ========== 费率管理测试 ==========

class TestFeeRateManagement:
    """测试费率管理"""

    def test_get_effective_fee_rate(self, service, mock_db, mock_supplier):
        """测试获取生效费率"""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_supplier

        result = service.get_effective_fee_rate(supplier_id=1)

        assert result["supplier_id"] == 1
        assert result["supplier_name"] == "Test Supplier"
        assert result["fee_rate"] == "0.10"
        assert result["fee_type"] == FeeType.PERCENTAGE
        assert result["is_default"] is False

    def test_get_effective_fee_rate_default(self, service, mock_db, mock_supplier):
        """测试获取默认费率"""
        mock_supplier.fee_rate = None
        mock_db.query.return_value.filter.return_value.first.return_value = mock_supplier

        result = service.get_effective_fee_rate(supplier_id=1)

        assert result["fee_rate"] == "0.10"  # Default
        assert result["is_default"] is True

    def test_update_fee_rate(self, service, mock_db, mock_supplier):
        """测试更新费率"""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_supplier

        result = service.update_fee_rate(
            supplier_id=1,
            new_rate=Decimal("0.15"),
            fee_type=FeeType.PERCENTAGE
        )

        assert result["supplier_id"] == 1
        assert result["new_fee_rate"] == "0.15"
        mock_db.commit.assert_called_once()

    def test_update_fee_rate_invalid(self, service, mock_db, mock_supplier):
        """测试更新无效费率"""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_supplier

        with pytest.raises(ValidationError) as exc_info:
            service.update_fee_rate(
                supplier_id=1,
                new_rate=Decimal("1.5"),  # > 1
                fee_type=FeeType.PERCENTAGE
            )
        assert exc_info.value.error_code == "FEE_002"

    def test_update_fee_rate_supplier_not_found(self, service, mock_db):
        """测试更新不存在的供应商"""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ResourceNotFoundError):
            service.update_fee_rate(
                supplier_id=999,
                new_rate=Decimal("0.15")
            )


# ========== 批量计算测试 ==========

class TestBatchCalculateFees:
    """测试批量计算"""

    def test_batch_calculate_fees(self, service, mock_db, mock_supplier):
        """测试批量计算"""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_supplier

        items = [
            {"spend_amount": "1000.00", "supplier_id": 1},
            {"spend_amount": "2000.00", "supplier_id": 1},
        ]

        results = service.batch_calculate_fees(items)

        assert len(results) == 2
        assert results[0]["success"] is True
        assert results[0]["fee_amount"] == "100.00"
        assert results[1]["success"] is True
        assert results[1]["fee_amount"] == "200.00"

    def test_batch_calculate_fees_with_error(self, service, mock_db):
        """测试批量计算包含错误"""
        # 第一个成功，第二个失败
        mock_supplier = MagicMock(spec=Supplier)
        mock_supplier.id = 1
        mock_supplier.name = "Test"
        mock_supplier.fee_rate = Decimal("0.10")
        mock_supplier.fee_type = FeeType.PERCENTAGE

        def side_effect(*args, **kwargs):
            query = MagicMock()
            filter_result = MagicMock()
            filter_result.first.return_value = mock_supplier
            query.filter.return_value = filter_result
            return query

        mock_db.query.side_effect = side_effect

        items = [
            {"spend_amount": "1000.00", "supplier_id": 1},
            {"spend_amount": "-100.00", "supplier_id": 1},  # 负数，会失败
        ]

        results = service.batch_calculate_fees(items)

        assert len(results) == 2
        assert results[0]["success"] is True
        assert results[1]["success"] is False
        assert results[1]["error"] is not None


# ========== 便捷函数测试 ==========

class TestConvenienceFunctions:
    """测试便捷函数"""

    def test_get_fee_service(self, mock_db):
        """测试 get_fee_service"""
        service = get_fee_service(mock_db)
        assert isinstance(service, FeeService)

    def test_calculate_fee_function(self, mock_db):
        """测试 calculate_fee 函数"""
        mock_supplier = MagicMock(spec=Supplier)
        mock_supplier.id = 1
        mock_supplier.fee_rate = Decimal("0.10")
        mock_supplier.fee_type = FeeType.PERCENTAGE
        mock_db.query.return_value.filter.return_value.first.return_value = mock_supplier

        fee = calculate_fee(mock_db, Decimal("1000.00"), 1)
        assert fee == Decimal("100.00")

    def test_calculate_cost_function(self, mock_db):
        """测试 calculate_cost 函数"""
        mock_supplier = MagicMock(spec=Supplier)
        mock_supplier.id = 1
        mock_supplier.fee_rate = Decimal("0.10")
        mock_supplier.fee_type = FeeType.PERCENTAGE
        mock_db.query.return_value.filter.return_value.first.return_value = mock_supplier

        fee, cost, rate = calculate_cost(mock_db, Decimal("1000.00"), 1)
        assert fee == Decimal("100.00")
        assert cost == Decimal("1100.00")
        assert rate == Decimal("0.10")


# ========== 边界条件测试 ==========

class TestBoundaryConditions:
    """测试边界条件"""

    def test_zero_spend_amount(self, service, mock_db, mock_supplier):
        """测试零消耗"""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_supplier

        fee = service.calculate_fee(Decimal("0.00"), supplier_id=1)
        assert fee == Decimal("0.00")

    def test_very_small_spend(self, service, mock_db, mock_supplier):
        """测试极小消耗"""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_supplier

        fee = service.calculate_fee(Decimal("0.01"), supplier_id=1)
        # 0.01 * 0.10 = 0.001 -> 0.00 (四舍五入)
        assert fee == Decimal("0.00")

    def test_very_large_spend(self, service, mock_db, mock_supplier):
        """测试大额消耗"""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_supplier

        fee = service.calculate_fee(Decimal("1000000.00"), supplier_id=1)
        # 1000000 * 0.10 = 100000
        assert fee == Decimal("100000.00")

    def test_max_fee_rate(self, service):
        """测试最大费率 (100%)"""
        fee = service.calculate_fee_by_rate(
            spend_amount=Decimal("1000.00"),
            fee_rate=Decimal("1.00"),
            fee_type=FeeType.PERCENTAGE
        )
        assert fee == Decimal("1000.00")

    def test_min_fee_rate(self, service):
        """测试最小费率 (0%)"""
        fee = service.calculate_fee_by_rate(
            spend_amount=Decimal("1000.00"),
            fee_rate=Decimal("0.00"),
            fee_type=FeeType.PERCENTAGE
        )
        assert fee == Decimal("0.00")


# ========== 精度测试 ==========

class TestPrecision:
    """测试精度"""

    def test_rounding_half_up(self, service):
        """测试四舍五入"""
        # 0.055 * 1000 = 55.5 -> 55.50 (but we test the 2 decimal result)
        fee = service.calculate_fee_by_rate(
            spend_amount=Decimal("1000.00"),
            fee_rate=Decimal("0.055"),
            fee_type=FeeType.PERCENTAGE
        )
        assert fee == Decimal("55.00")

    def test_decimal_precision(self, service):
        """测试小数精度"""
        fee = service.calculate_fee_by_rate(
            spend_amount=Decimal("123.45"),
            fee_rate=Decimal("0.0333"),
            fee_type=FeeType.PERCENTAGE
        )
        # 123.45 * 0.0333 = 4.110885 -> 4.11
        assert fee == Decimal("4.11")

    @pytest.mark.parametrize("spend,rate,expected", [
        (Decimal("100.00"), Decimal("0.10"), Decimal("10.00")),
        (Decimal("100.00"), Decimal("0.05"), Decimal("5.00")),
        (Decimal("100.00"), Decimal("0.01"), Decimal("1.00")),
        (Decimal("100.00"), Decimal("0.001"), Decimal("0.10")),
        (Decimal("100.00"), Decimal("0.0001"), Decimal("0.01")),
        (Decimal("999.99"), Decimal("0.10"), Decimal("100.00")),
    ])
    def test_various_rates(self, service, spend, rate, expected):
        """测试各种费率"""
        fee = service.calculate_fee_by_rate(
            spend_amount=spend,
            fee_rate=rate,
            fee_type=FeeType.PERCENTAGE
        )
        assert fee == expected


# ========== FeeType 测试 ==========

class TestFeeType:
    """测试 FeeType 常量"""

    def test_fee_type_values(self):
        """测试 FeeType 值"""
        assert FeeType.PERCENTAGE == "PERCENTAGE"
        assert FeeType.FIXED == "FIXED"
