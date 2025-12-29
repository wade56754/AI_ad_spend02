"""
阶梯定价计算服务测试

测试覆盖:
- 固定价格计算
- 阶梯价格计算（加拿大TK规则、新加坡规则）
- 成本计算（含手续费）
- 边界条件（零进粉、无规则等）

Version: 1.0
"""
import pytest
from decimal import Decimal
from backend.services.pricing_service import (
    calculate_revenue,
    calculate_cost,
    calculate_profit,
    calculate_profit_margin,
    calculate_daily_report_financials,
)


class TestCalculateRevenue:
    """阶梯定价计算测试"""

    def test_fixed_price(self):
        """固定价格"""
        result = calculate_revenue(
            conversions=100,
            price_rules={"type": "fixed", "price": 50},
            unit_price=Decimal("0")
        )
        assert result == Decimal("5000.00")

    def test_fixed_price_with_decimal(self):
        """固定价格 - 小数"""
        result = calculate_revenue(
            conversions=33,
            price_rules={"type": "fixed", "price": 150.50},
            unit_price=Decimal("0")
        )
        assert result == Decimal("4966.50")

    def test_tiered_price_canada_tk(self):
        """加拿大TK阶梯: 0-15为$100, 16-30为$120, 31+为$130"""
        rules = {
            "type": "tiered",
            "tiers": [
                {"min": 0, "max": 15, "price": 100},
                {"min": 16, "max": 30, "price": 120},
                {"min": 31, "max": None, "price": 130}
            ]
        }
        # 34个 = 16*100 + 15*120 + 3*130 = 1600 + 1800 + 390 = 3790
        # 修正：0-15 是16个，16-30 是15个，31-33 是3个
        # 0-15 (含0和15): 16个 * 100 = 1600
        # 16-30 (含16和30): 15个 * 120 = 1800
        # 31-33: 3个 * 130 = 390
        # 总计: 3790
        result = calculate_revenue(34, rules, Decimal("0"))
        assert result == Decimal("3790.00")

    def test_tiered_price_exact_boundary(self):
        """阶梯边界 - 刚好15个"""
        rules = {
            "type": "tiered",
            "tiers": [
                {"min": 0, "max": 15, "price": 100},
                {"min": 16, "max": 30, "price": 120},
                {"min": 31, "max": None, "price": 130}
            ]
        }
        # 15个 = 15*100 = 1500 (注意：0-15 包含0)
        # 实际上 min=0, max=15 表示 16 个位置 (0,1,2,...,15)
        result = calculate_revenue(15, rules, Decimal("0"))
        assert result == Decimal("1500.00")

    def test_tiered_price_singapore(self):
        """新加坡阶梯: 0-10为$100, 11-20为$110, 21+为$120"""
        rules = {
            "type": "tiered",
            "tiers": [
                {"min": 0, "max": 10, "price": 100},
                {"min": 11, "max": 20, "price": 110},
                {"min": 21, "max": None, "price": 120}
            ]
        }
        # 18个: 0-10 (11个) * 100 = 1100, 11-17 (7个) * 110 = 770
        # 总计: 1870
        result = calculate_revenue(18, rules, Decimal("0"))
        assert result == Decimal("1870.00")

    def test_no_rules_fallback(self):
        """无规则时使用 unit_price"""
        result = calculate_revenue(
            conversions=50,
            price_rules=None,
            unit_price=Decimal("40.00")
        )
        assert result == Decimal("2000.00")

    def test_zero_conversions(self):
        """零进粉"""
        result = calculate_revenue(0, None, Decimal("100"))
        assert result == Decimal("0.00")

    def test_negative_conversions(self):
        """负数进粉（应返回0）"""
        result = calculate_revenue(-5, None, Decimal("100"))
        assert result == Decimal("0.00")

    def test_empty_tiers(self):
        """空阶梯列表"""
        rules = {"type": "tiered", "tiers": []}
        result = calculate_revenue(10, rules, Decimal("50"))
        assert result == Decimal("0.00")

    def test_unknown_type_fallback(self):
        """未知定价类型回退到 unit_price"""
        rules = {"type": "unknown_type"}
        result = calculate_revenue(10, rules, Decimal("25"))
        assert result == Decimal("250.00")


class TestCalculateCost:
    """成本计算测试"""

    def test_cost_with_standard_fee(self):
        """标准手续费 8%"""
        # 1000 * (1 + 0.08) = 1080
        result = calculate_cost(Decimal("1000.00"), Decimal("0.08"))
        assert result == Decimal("1080.00")

    def test_cost_with_low_fee(self):
        """低费率（VCC 1%）"""
        # 500 * 1.01 = 505
        result = calculate_cost(Decimal("500.00"), Decimal("0.01"))
        assert result == Decimal("505.00")

    def test_cost_with_high_fee(self):
        """高费率（15%）"""
        # 1000 * 1.15 = 1150
        result = calculate_cost(Decimal("1000.00"), Decimal("0.15"))
        assert result == Decimal("1150.00")

    def test_zero_spend(self):
        """零消耗"""
        result = calculate_cost(Decimal("0"), Decimal("0.08"))
        assert result == Decimal("0.00")

    def test_negative_spend(self):
        """负数消耗（应返回0）"""
        result = calculate_cost(Decimal("-100"), Decimal("0.08"))
        assert result == Decimal("0.00")

    def test_zero_fee_rate(self):
        """零费率"""
        result = calculate_cost(Decimal("1000.00"), Decimal("0"))
        assert result == Decimal("1000.00")


class TestCalculateProfit:
    """利润计算测试"""

    def test_positive_profit(self):
        """正利润"""
        result = calculate_profit(Decimal("5000.00"), Decimal("3000.00"))
        assert result == Decimal("2000.00")

    def test_negative_profit(self):
        """负利润（亏损）"""
        result = calculate_profit(Decimal("3000.00"), Decimal("5000.00"))
        assert result == Decimal("-2000.00")

    def test_zero_profit(self):
        """零利润"""
        result = calculate_profit(Decimal("3000.00"), Decimal("3000.00"))
        assert result == Decimal("0.00")


class TestCalculateProfitMargin:
    """利润率计算测试"""

    def test_positive_margin(self):
        """正利润率"""
        # (5000 - 3000) / 5000 * 100 = 40%
        result = calculate_profit_margin(Decimal("5000.00"), Decimal("3000.00"))
        assert result == Decimal("40.00")

    def test_negative_margin(self):
        """负利润率"""
        # (3000 - 5000) / 3000 * 100 = -66.67%
        result = calculate_profit_margin(Decimal("3000.00"), Decimal("5000.00"))
        assert result == Decimal("-66.67")

    def test_zero_revenue(self):
        """零收入时返回0"""
        result = calculate_profit_margin(Decimal("0"), Decimal("1000.00"))
        assert result == Decimal("0.00")


class TestCalculateDailyReportFinancials:
    """日报财务指标综合计算测试"""

    def test_full_calculation(self):
        """完整计算流程"""
        result = calculate_daily_report_financials(
            conversions=20,
            real_spend=Decimal("1000.00"),
            price_rules={"type": "fixed", "price": 100},
            unit_price=Decimal("0"),
            fee_rate=Decimal("0.08")
        )

        assert result["revenue"] == Decimal("2000.00")
        assert result["cost"] == Decimal("1080.00")
        assert result["profit"] == Decimal("920.00")
        assert result["profit_margin"] == Decimal("46.00")

    def test_tiered_calculation(self):
        """阶梯定价计算"""
        rules = {
            "type": "tiered",
            "tiers": [
                {"min": 0, "max": 10, "price": 100},
                {"min": 11, "max": None, "price": 120}
            ]
        }
        result = calculate_daily_report_financials(
            conversions=15,
            real_spend=Decimal("800.00"),
            price_rules=rules,
            unit_price=Decimal("0"),
            fee_rate=Decimal("0.08")
        )

        # 收入: 11*100 + 4*120 = 1100 + 480 = 1580
        # 成本: 800 * 1.08 = 864
        # 利润: 1580 - 864 = 716
        # 利润率: 716 / 1580 * 100 = 45.32%
        assert result["revenue"] == Decimal("1580.00")
        assert result["cost"] == Decimal("864.00")
        assert result["profit"] == Decimal("716.00")
        assert result["profit_margin"] == Decimal("45.32")
