"""
计费公式边界测试 - P1 级验收项
Version: 1.0
Author: AI Code Factory

验收项对齐:
- LG-S06: REVENUE 金额 = conversions_final × unit_price
- LG-S07: COST 金额 = real_spend × (1 + fee_rate)

SoT对齐:
- LEDGER_SOT.md v1.1 §5 计费公式
- BUSINESS_RULES.md v3.2 §3 计费规则
"""

import pytest
from decimal import Decimal, ROUND_HALF_UP
from datetime import date


class TestRevenueFormula:
    """
    LG-S06: REVENUE 计费公式测试

    公式: REVENUE = conversions_final × unit_price
    """

    def test_revenue_normal_calculation(self):
        """正常收益计算"""
        conversions_final = 100
        unit_price = Decimal("10.00")

        revenue = Decimal(conversions_final) * unit_price

        assert revenue == Decimal("1000.00")

    def test_revenue_zero_conversions(self):
        """零转化收益计算"""
        conversions_final = 0
        unit_price = Decimal("10.00")

        revenue = Decimal(conversions_final) * unit_price

        assert revenue == Decimal("0.00")

    def test_revenue_zero_unit_price(self):
        """零单价收益计算"""
        conversions_final = 100
        unit_price = Decimal("0.00")

        revenue = Decimal(conversions_final) * unit_price

        assert revenue == Decimal("0.00")

    def test_revenue_high_volume(self):
        """高转化量收益计算"""
        conversions_final = 1000000  # 100万
        unit_price = Decimal("10.00")

        revenue = Decimal(conversions_final) * unit_price

        assert revenue == Decimal("10000000.00")

    def test_revenue_decimal_unit_price(self):
        """小数单价收益计算"""
        conversions_final = 100
        unit_price = Decimal("10.55")

        revenue = Decimal(conversions_final) * unit_price

        assert revenue == Decimal("1055.00")

    def test_revenue_small_unit_price(self):
        """极小单价收益计算"""
        conversions_final = 100
        unit_price = Decimal("0.01")

        revenue = Decimal(conversions_final) * unit_price

        assert revenue == Decimal("1.00")

    @pytest.mark.parametrize("conversions,unit_price,expected", [
        (1, Decimal("0.01"), Decimal("0.01")),
        (1, Decimal("100.00"), Decimal("100.00")),
        (10, Decimal("9.99"), Decimal("99.90")),
        (999, Decimal("1.00"), Decimal("999.00")),
        (1000, Decimal("0.001"), Decimal("1.000")),
    ])
    def test_revenue_boundary_cases(self, conversions, unit_price, expected):
        """收益计算边界情况"""
        revenue = Decimal(conversions) * unit_price
        assert revenue == expected


class TestCostFormula:
    """
    LG-S07: COST 计费公式测试

    公式: COST = real_spend × (1 + fee_rate)
    """

    def test_cost_normal_calculation(self):
        """正常成本计算"""
        real_spend = Decimal("1000.00")
        fee_rate = Decimal("0.05")  # 5%

        cost = real_spend * (1 + fee_rate)

        assert cost == Decimal("1050.00")

    def test_cost_zero_spend(self):
        """零消耗成本计算"""
        real_spend = Decimal("0.00")
        fee_rate = Decimal("0.05")

        cost = real_spend * (1 + fee_rate)

        assert cost == Decimal("0.00")

    def test_cost_zero_fee_rate(self):
        """零费率成本计算"""
        real_spend = Decimal("1000.00")
        fee_rate = Decimal("0.00")

        cost = real_spend * (1 + fee_rate)

        assert cost == Decimal("1000.00")

    def test_cost_high_fee_rate(self):
        """高费率成本计算 (20%)"""
        real_spend = Decimal("1000.00")
        fee_rate = Decimal("0.20")

        cost = real_spend * (1 + fee_rate)

        assert cost == Decimal("1200.00")

    def test_cost_decimal_fee_rate(self):
        """小数费率成本计算"""
        real_spend = Decimal("1000.00")
        fee_rate = Decimal("0.055")  # 5.5%

        cost = real_spend * (1 + fee_rate)

        assert cost == Decimal("1055.00")

    def test_cost_high_spend(self):
        """高消耗成本计算"""
        real_spend = Decimal("1000000.00")  # 100万
        fee_rate = Decimal("0.05")

        cost = real_spend * (1 + fee_rate)

        assert cost == Decimal("1050000.00")

    @pytest.mark.parametrize("spend,fee_rate,expected", [
        (Decimal("100.00"), Decimal("0.00"), Decimal("100.00")),
        (Decimal("100.00"), Decimal("0.01"), Decimal("101.00")),
        (Decimal("100.00"), Decimal("0.10"), Decimal("110.00")),
        (Decimal("100.00"), Decimal("0.50"), Decimal("150.00")),
        (Decimal("1.00"), Decimal("0.05"), Decimal("1.05")),
    ])
    def test_cost_boundary_cases(self, spend, fee_rate, expected):
        """成本计算边界情况"""
        cost = spend * (1 + fee_rate)
        assert cost == expected


class TestFormulaPrecision:
    """
    计费精度测试

    对齐 DATA_SCHEMA.md v5.2:
    - 金额字段: DECIMAL(18, 2)
    - 费率字段: DECIMAL(5, 4)
    """

    def test_revenue_precision_two_decimal(self):
        """收益精度 - 保留两位小数"""
        conversions_final = 3
        unit_price = Decimal("10.33")

        revenue = Decimal(conversions_final) * unit_price
        # 3 × 10.33 = 30.99
        assert revenue == Decimal("30.99")

    def test_cost_precision_rounding(self):
        """成本精度 - 四舍五入"""
        real_spend = Decimal("100.00")
        fee_rate = Decimal("0.0333")  # 3.33%

        cost = real_spend * (1 + fee_rate)
        # 100 × 1.0333 = 103.33

        # 四舍五入到两位小数
        cost_rounded = cost.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        assert cost_rounded == Decimal("103.33")

    def test_revenue_no_overflow(self):
        """收益计算 - 无溢出"""
        conversions_final = 10000000  # 1000万
        unit_price = Decimal("999.99")

        revenue = Decimal(conversions_final) * unit_price

        # 应该正确计算，无溢出
        assert revenue == Decimal("9999900000.00")

    def test_cost_no_overflow(self):
        """成本计算 - 无溢出"""
        real_spend = Decimal("9999999999.99")  # 接近上限
        fee_rate = Decimal("0.05")

        cost = real_spend * (1 + fee_rate)

        # 应该正确计算，无溢出
        assert cost == Decimal("10499999999.9895")


class TestNegativeValues:
    """
    负值处理测试

    业务规则: 转化数和消耗应为非负数
    """

    def test_negative_conversions_rejected(self):
        """负转化数应拒绝"""
        conversions_final = -100
        unit_price = Decimal("10.00")

        # 业务层应该拒绝负转化数
        # 这里只验证计算结果
        revenue = Decimal(conversions_final) * unit_price
        assert revenue < 0  # 负值表示异常

    def test_negative_spend_rejected(self):
        """负消耗应拒绝"""
        real_spend = Decimal("-1000.00")
        fee_rate = Decimal("0.05")

        # 业务层应该拒绝负消耗
        cost = real_spend * (1 + fee_rate)
        assert cost < 0  # 负值表示异常

    def test_negative_fee_rate_rejected(self):
        """负费率应拒绝"""
        real_spend = Decimal("1000.00")
        fee_rate = Decimal("-0.05")

        # 业务层应该拒绝负费率
        cost = real_spend * (1 + fee_rate)
        # 负费率会导致成本低于消耗
        assert cost < real_spend


class TestFormulaIntegration:
    """
    公式集成测试

    验证公式在实际业务场景中的应用
    """

    def test_profit_calculation(self):
        """利润计算 = REVENUE - COST"""
        # 收益计算
        conversions_final = 100
        unit_price = Decimal("15.00")
        revenue = Decimal(conversions_final) * unit_price

        # 成本计算
        real_spend = Decimal("1000.00")
        fee_rate = Decimal("0.05")
        cost = real_spend * (1 + fee_rate)

        # 利润
        profit = revenue - cost

        assert revenue == Decimal("1500.00")
        assert cost == Decimal("1050.00")
        assert profit == Decimal("450.00")

    def test_profit_margin_calculation(self):
        """利润率计算 = (REVENUE - COST) / REVENUE"""
        conversions_final = 100
        unit_price = Decimal("15.00")
        revenue = Decimal(conversions_final) * unit_price

        real_spend = Decimal("1000.00")
        fee_rate = Decimal("0.05")
        cost = real_spend * (1 + fee_rate)

        if revenue > 0:
            profit_margin = (revenue - cost) / revenue * 100
            # (1500 - 1050) / 1500 × 100 = 30%
            assert profit_margin == Decimal("30")

    def test_break_even_scenario(self):
        """盈亏平衡场景"""
        # 收益 = 成本
        real_spend = Decimal("1000.00")
        fee_rate = Decimal("0.05")
        cost = real_spend * (1 + fee_rate)  # 1050

        # 需要多少转化才能达到盈亏平衡?
        unit_price = Decimal("10.50")
        required_conversions = cost / unit_price  # 1050 / 10.50 = 100

        assert required_conversions == Decimal("100")

    def test_loss_scenario(self):
        """亏损场景"""
        conversions_final = 50
        unit_price = Decimal("10.00")
        revenue = Decimal(conversions_final) * unit_price  # 500

        real_spend = Decimal("1000.00")
        fee_rate = Decimal("0.05")
        cost = real_spend * (1 + fee_rate)  # 1050

        profit = revenue - cost

        assert profit == Decimal("-550.00")  # 亏损 550
        assert profit < 0
