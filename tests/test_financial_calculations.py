#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
财务计算专项测试
验证所有财务相关计算的准确性和精度
"""

import pytest
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from datetime import date, datetime, timedelta
from typing import List, Dict, Tuple

from tests.conftest import assert_decimal_equal, pytest_marks


@pytest.mark.unit
@pytest.mark.functional
class TestCPLCalculations:
    """CPL（Cost Per Lead）计算测试"""

    def test_cpl_basic_calculation(self):
        """测试基础CPL计算"""
        spend = Decimal("1000.00")
        conversions = 20
        expected_cpl = spend / Decimal(conversions)

        calculated_cpl = calculate_cpl(spend, conversions)

        assert_decimal_equal(calculated_cpl, expected_cpl)
        assert calculated_cpl == Decimal("50.00")

    def test_cpl_with_zero_conversions(self):
        """测试零转化时的CPL计算"""
        spend = Decimal("1000.00")
        conversions = 0

        cpl = calculate_cpl(spend, conversions)
        assert cpl is None  # 零转化时CPL应为None

    def test_cpl_rounding(self):
        """测试CPL计算的四舍五入"""
        # 测试需要四舍五入的情况
        spend = Decimal("1000.00")
        conversions = 3
        raw_cpl = spend / Decimal(conversions)  # 333.333...

        # 四舍五入到2位小数
        rounded_cpl = raw_cpl.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        assert_decimal_equal(rounded_cpl, Decimal("333.33"))

    @pytest.mark.parametrize("spend,conversions,expected", [
        ("500.00", 10, "50.00"),
        ("1234.56", 7, "176.37"),
        ("9999.99", 1, "9999.99"),
        ("0.01", 1, "0.01"),
        ("1000.00", 0, None),
    ])
    def test_cpl_parametrized(self, spend, conversions, expected):
        """参数化CPL计算测试"""
        cpl = calculate_cpl(Decimal(spend), conversions)

        if expected is None:
            assert cpl is None
        else:
            assert_decimal_equal(cpl, Decimal(expected))

    def test_cpl_tolerance_check(self):
        """测试CPL容差检查"""
        target_cpl = Decimal("50.00")
        tolerance = Decimal("5.00")  # 10%容差

        # 在容差范围内
        assert check_cpl_tolerance(target_cpl, Decimal("52.00"), tolerance) is True
        assert check_cpl_tolerance(target_cpl, Decimal("48.00"), tolerance) is True

        # 超出容差
        assert check_cpl_tolerance(target_cpl, Decimal("56.00"), tolerance) is False
        assert check_cpl_tolerance(target_cpl, Decimal("44.00"), tolerance) is False

    def test_cpl_variance_percentage(self):
        """测试CPL偏差百分比计算"""
        target_cpl = Decimal("50.00")
        actual_cpl = Decimal("55.00")

        variance = calculate_cpl_variance_percentage(target_cpl, actual_cpl)
        expected_variance = ((actual_cpl - target_cpl) / target_cpl) * 100

        assert_decimal_equal(variance, expected_variance, Decimal("0.01"))
        assert variance == Decimal("10.00")


@pytest.mark.unit
@pytest.mark.functional
class TestBudgetCalculations:
    """预算计算测试"""

    def test_daily_budget_calculation(self):
        """测试日预算计算"""
        monthly_budget = Decimal("30000.00")
        days_in_month = 30
        expected_daily = monthly_budget / Decimal(days_in_month)

        daily_budget = calculate_daily_budget(monthly_budget, days_in_month)
        assert_decimal_equal(daily_budget, expected_daily)

    def test_remaining_budget_calculation(self):
        """测试剩余预算计算"""
        total_budget = Decimal("10000.00")
        spent = Decimal("3500.00")
        expected_remaining = total_budget - spent

        remaining = calculate_remaining_budget(total_budget, spent)
        assert_decimal_equal(remaining, expected_remaining)

    def test_budget_utilization_rate(self):
        """测试预算使用率"""
        total_budget = Decimal("10000.00")
        spent = Decimal("7500.00")
        expected_rate = (spent / total_budget) * 100

        utilization = calculate_budget_utilization_rate(total_budget, spent)
        assert_decimal_equal(utilization, expected_rate, Decimal("0.01"))
        assert utilization == Decimal("75.00")

    def test_days_remaining_calculation(self):
        """测试剩余天数计算"""
        end_date = date(2025, 12, 31)
        today = date(2025, 12, 1)

        days_remaining = calculate_days_remaining(end_date, today)
        assert days_remaining == 30

    def test_recommended_daily_spend(self):
        """测试推荐日消费计算"""
        remaining_budget = Decimal("5000.00")
        remaining_days = 20
        expected_daily = remaining_budget / Decimal(remaining_days)

        recommended = calculate_recommended_daily_spend(remaining_budget, remaining_days)
        assert_decimal_equal(recommended, expected_daily)

    def test_budget_pace_analysis(self):
        """测试预算执行节奏分析"""
        total_budget = Decimal("10000.00")
        total_days = 30
        days_passed = 15
        spent_so_far = Decimal("4000.00")

        pace = analyze_budget_pace(
            total_budget,
            total_days,
            days_passed,
            spent_so_far
        )

        # 预期：已过15天，应该花费5000，实际花费4000
        expected_spend = (total_budget / Decimal(total_days)) * Decimal(days_passed)
        variance = spent_so_far - expected_spend

        assert pace["expected_spend"] == expected_spend
        assert pace["actual_spend"] == spent_so_far
        assert pace["variance"] == variance
        assert pace["is_on_track"] is False  # 消费不足

    @pytest.mark.parametrize("total,spent,expected_status", [
        ("10000.00", "8000.00", "warning"),     # 80% - 警告
        ("10000.00", "9500.00", "critical"),    # 95% - 严重
        ("10000.00", "10500.00", "overspend"),  # 超支
        ("10000.00", "5000.00", "normal"),      # 50% - 正常
    ])
    def test_budget_status(self, total, spent, expected_status):
        """测试预算状态"""
        status = get_budget_status(Decimal(total), Decimal(spent))
        assert status == expected_status


@pytest.mark.unit
@pytest.mark.functional
class TestROICalculations:
    """ROI（Return on Investment）计算测试"""

    def test_roi_positive(self):
        """测试正ROI计算"""
        spend = Decimal("1000.00")
        revenue = Decimal("1500.00")
        expected_roi = ((revenue - spend) / spend) * 100

        roi = calculate_roi(spend, revenue)
        assert_decimal_equal(roi, expected_roi, Decimal("0.01"))
        assert roi == Decimal("50.00")  # 50% ROI

    def test_roi_negative(self):
        """测试负ROI计算"""
        spend = Decimal("1000.00")
        revenue = Decimal("800.00")
        expected_roi = ((revenue - spend) / spend) * 100

        roi = calculate_roi(spend, revenue)
        assert_decimal_equal(roi, expected_roi, Decimal("0.01"))
        assert roi == Decimal("-20.00")  # -20% ROI

    def test_roi_zero_spend(self):
        """测试零消费的ROI"""
        spend = Decimal("0.00")
        revenue = Decimal("500.00")

        roi = calculate_roi(spend, revenue)
        assert roi is None  # 无限ROI，返回None

    def test_profit_margin_calculation(self):
        """测试利润率计算"""
        revenue = Decimal("1000.00")
        cost = Decimal("700.00")
        expected_margin = ((revenue - cost) / revenue) * 100

        margin = calculate_profit_margin(revenue, cost)
        assert_decimal_equal(margin, expected_margin, Decimal("0.01"))
        assert margin == Decimal("30.00")

    def test_break_even_point(self):
        """测试盈亏平衡点计算"""
        cpl = Decimal("50.00")
        conversion_value = Decimal("100.00")
        expected_break_even = conversion_value

        break_even = calculate_break_even_cpl(cpl, conversion_value)
        assert_decimal_equal(break_even, expected_break_even)

    def test_roas_calculation(self):
        """测试ROAS（Return on Ad Spend）计算"""
        spend = Decimal("1000.00")
        revenue = Decimal("5000.00")
        expected_roas = revenue / spend

        roas = calculate_roas(spend, revenue)
        assert_decimal_equal(roas, expected_roas, Decimal("0.01"))
        assert roas == Decimal("5.00")  # 5:1 ROAS


@pytest.mark.unit
@pytest.mark.functional
class TestMetricsCalculations:
    """广告指标计算测试"""

    def test_ctr_calculation(self):
        """测试CTR（Click-Through Rate）计算"""
        impressions = 10000
        clicks = 500
        expected_ctr = Decimal(clicks) / Decimal(impressions)

        ctr = calculate_ctr(impressions, clicks)
        assert_decimal_equal(ctr, expected_ctr, Decimal("0.0001"))
        assert ctr == Decimal("0.05")  # 5%

    def test_conversion_rate_calculation(self):
        """测试转化率计算"""
        clicks = 500
        conversions = 50
        expected_rate = Decimal(conversions) / Decimal(clicks)

        rate = calculate_conversion_rate(clicks, conversions)
        assert_decimal_equal(rate, expected_rate, Decimal("0.001"))
        assert rate == Decimal("0.10")  # 10%

    def test_cpa_calculation(self):
        """测试CPA（Cost Per Action）计算"""
        spend = Decimal("1000.00")
        actions = 25
        expected_cpa = spend / Decimal(actions)

        cpa = calculate_cpa(spend, actions)
        assert_decimal_equal(cpa, expected_cpa)
        assert cpa == Decimal("40.00")

    def test_cpm_calculation(self):
        """测试CPM（Cost Per Mille）计算"""
        spend = Decimal("500.00")
        impressions = 100000  # 100k
        expected_cpm = (spend / Decimal(impressions)) * 1000

        cpm = calculate_cpm(spend, impressions)
        assert_decimal_equal(cpm, expected_cpm, Decimal("0.01"))
        assert cpm == Decimal("5.00")

    def test_engagement_rate(self):
        """测试参与度计算"""
        clicks = 500
        likes = 100
        shares = 50
        comments = 25
        engagements = likes + shares + comments

        rate = calculate_engagement_rate(engagements, clicks)
        expected_rate = Decimal(engagements) / Decimal(clicks)

        assert_decimal_equal(rate, expected_rate, Decimal("0.001"))
        assert rate == Decimal("0.35")  # 35%

    @pytest.mark.parametrize("impressions,clicks,conversions", [
        (0, 0, 0),  # 全零
        (1000, 0, 0),  # 零点击
        (1000, 100, 0),  # 零转化
        (1000000, 50000, 2500),  # 大数值
    ])
    def test_metrics_edge_cases(self, impressions, clicks, conversions):
        """测试指标计算的边界情况"""
        # 这些应该都能正常处理而不出错
        ctr = calculate_ctr(impressions, clicks) if impressions > 0 else None
        conv_rate = calculate_conversion_rate(clicks, conversions) if clicks > 0 else None
        cpl = calculate_cpl(Decimal("1000.00"), conversions) if conversions > 0 else None

        # 验证结果合理性
        if ctr is not None:
            assert 0 <= ctr <= 1
        if conv_rate is not None:
            assert 0 <= conv_rate <= 1
        if cpl is not None:
            assert cpl > 0


@pytest.mark.functional
class TestFinancialAggregations:
    """财务聚合计算测试"""

    def test_monthly_aggregation(self):
        """测试月度数据聚合"""
        daily_data = [
            {"date": "2025-01-01", "spend": 100.00, "conversions": 2},
            {"date": "2025-01-02", "spend": 150.00, "conversions": 3},
            {"date": "2025-01-03", "spend": 120.00, "conversions": 2},
        ]

        monthly = aggregate_monthly_data(daily_data)

        assert monthly["total_spend"] == Decimal("370.00")
        assert monthly["total_conversions"] == 7
        assert monthly["avg_daily_spend"] == Decimal("123.33")
        assert_decimal_equal(monthly["avg_cpl"], Decimal("52.86"), Decimal("0.01"))

    def test_project_performance_summary(self):
        """测试项目绩效汇总"""
        accounts_data = [
            {
                "account_name": "Account A",
                "total_spend": Decimal("5000.00"),
                "total_conversions": 100,
                "total_revenue": Decimal("10000.00")
            },
            {
                "account_name": "Account B",
                "total_spend": Decimal("3000.00"),
                "total_conversions": 60,
                "total_revenue": Decimal("6000.00")
            }
        ]

        summary = summarize_project_performance(accounts_data)

        assert summary["total_spend"] == Decimal("8000.00")
        assert summary["total_conversions"] == 160
        assert summary["total_revenue"] == Decimal("16000.00")
        assert_decimal_equal(summary["avg_cpl"], Decimal("50.00"))
        assert_decimal_equal(summary["total_roi"], Decimal("100.00"))

    def test_trend_analysis(self):
        """测试趋势分析"""
        weekly_data = [
            {"week": "W1", "spend": 1000, "conversions": 20},
            {"week": "W2", "spend": 1200, "conversions": 25},
            {"week": "W3", "spend": 1100, "conversions": 22},
            {"week": "W4", "spend": 1300, "conversions": 28},
        ]

        trends = analyze_performance_trend(weekly_data)

        # 验证趋势计算
        assert trends["spend_trend"] == "increasing"  # 1000->1300
        assert trends["conversion_trend"] == "increasing"  # 20->28
        assert trends["cpl_trend"] in ["stable", "decreasing"]  # CPL应该稳定或下降

    def test_forecasting(self):
        """测试预测计算"""
        historical_data = [
            {"month": "2024-10", "spend": 10000, "conversions": 200},
            {"month": "2024-11", "spend": 11000, "conversions": 220},
            {"month": "2024-12", "spend": 12000, "conversions": 240},
        ]

        forecast = forecast_next_month_metrics(historical_data)

        # 基于线性增长的简单预测
        assert forecast["predicted_spend"] > 12000
        assert forecast["predicted_conversions"] > 240
        assert "confidence_interval" in forecast


# 辅助函数定义（这些应该在实际的services模块中实现）
def calculate_cpl(spend: Decimal, conversions: int) -> Decimal:
    """计算CPL"""
    if conversions == 0:
        return None
    return spend / Decimal(conversions)

def check_cpl_tolerance(target: Decimal, actual: Decimal, tolerance: Decimal) -> bool:
    """检查CPL是否在容差范围内"""
    difference = abs(actual - target)
    return difference <= tolerance

def calculate_cpl_variance_percentage(target: Decimal, actual: Decimal) -> Decimal:
    """计算CPL偏差百分比"""
    if target == 0:
        return Decimal("0")
    return ((actual - target) / target) * 100

def calculate_daily_budget(monthly_budget: Decimal, days: int) -> Decimal:
    """计算日预算"""
    return monthly_budget / Decimal(days)

def calculate_remaining_budget(total: Decimal, spent: Decimal) -> Decimal:
    """计算剩余预算"""
    return total - spent

def calculate_budget_utilization_rate(total: Decimal, spent: Decimal) -> Decimal:
    """计算预算使用率"""
    if total == 0:
        return Decimal("0")
    return (spent / total) * 100

def calculate_days_remaining(end_date: date, current_date: date = None) -> int:
    """计算剩余天数"""
    if current_date is None:
        current_date = date.today()
    delta = end_date - current_date
    return max(0, delta.days)

def calculate_recommended_daily_spend(remaining_budget: Decimal, remaining_days: int) -> Decimal:
    """计算推荐日消费"""
    if remaining_days == 0:
        return Decimal("0")
    return remaining_budget / Decimal(remaining_days)

def analyze_budget_pace(total: Decimal, days: int, passed: int, spent: Decimal) -> Dict:
    """分析预算执行节奏"""
    daily_budget = total / Decimal(days)
    expected_spend = daily_budget * Decimal(passed)
    variance = spent - expected_spend

    return {
        "expected_spend": expected_spend,
        "actual_spend": spent,
        "variance": variance,
        "is_on_track": abs(variance) <= (daily_budget * Decimal("0.1"))  # 10%容差
    }

def get_budget_status(total: Decimal, spent: Decimal) -> str:
    """获取预算状态"""
    rate = spent / total if total > 0 else 0

    if rate >= 1.05:
        return "overspend"
    elif rate >= 0.95:
        return "critical"
    elif rate >= 0.80:
        return "warning"
    else:
        return "normal"

def calculate_roi(spend: Decimal, revenue: Decimal) -> Decimal:
    """计算ROI"""
    if spend == 0:
        return None
    return ((revenue - spend) / spend) * 100

def calculate_profit_margin(revenue: Decimal, cost: Decimal) -> Decimal:
    """计算利润率"""
    if revenue == 0:
        return Decimal("0")
    return ((revenue - cost) / revenue) * 100

def calculate_break_even_cpl(cpl: Decimal, conversion_value: Decimal) -> Decimal:
    """计算盈亏平衡CPL"""
    return conversion_value

def calculate_roas(spend: Decimal, revenue: Decimal) -> Decimal:
    """计算ROAS"""
    if spend == 0:
        return None
    return revenue / spend

def calculate_ctr(impressions: int, clicks: int) -> Decimal:
    """计算CTR"""
    if impressions == 0:
        return Decimal("0")
    return Decimal(clicks) / Decimal(impressions)

def calculate_conversion_rate(clicks: int, conversions: int) -> Decimal:
    """计算转化率"""
    if clicks == 0:
        return Decimal("0")
    return Decimal(conversions) / Decimal(clicks)

def calculate_cpa(spend: Decimal, actions: int) -> Decimal:
    """计算CPA"""
    if actions == 0:
        return None
    return spend / Decimal(actions)

def calculate_cpm(spend: Decimal, impressions: int) -> Decimal:
    """计算CPM"""
    if impressions == 0:
        return Decimal("0")
    return (spend / Decimal(impressions)) * 1000

def calculate_engagement_rate(engagements: int, clicks: int) -> Decimal:
    """计算参与度"""
    if clicks == 0:
        return Decimal("0")
    return Decimal(engagements) / Decimal(clicks)

def aggregate_monthly_data(daily_data: List[Dict]) -> Dict:
    """聚合月度数据"""
    total_spend = sum(Decimal(str(d["spend"])) for d in daily_data)
    total_conversions = sum(d["conversions"] for d in daily_data)

    return {
        "total_spend": total_spend,
        "total_conversions": total_conversions,
        "avg_daily_spend": total_spend / Decimal(len(daily_data)),
        "avg_cpl": total_spend / Decimal(total_conversions) if total_conversions > 0 else Decimal("0")
    }

def summarize_project_performance(accounts_data: List[Dict]) -> Dict:
    """汇总项目绩效"""
    total_spend = sum(acc["total_spend"] for acc in accounts_data)
    total_conversions = sum(acc["total_conversions"] for acc in accounts_data)
    total_revenue = sum(acc["total_revenue"] for acc in accounts_data)

    return {
        "total_spend": total_spend,
        "total_conversions": total_conversions,
        "total_revenue": total_revenue,
        "avg_cpl": total_spend / Decimal(total_conversions) if total_conversions > 0 else Decimal("0"),
        "total_roi": calculate_roi(total_spend, total_revenue)
    }

def analyze_performance_trend(weekly_data: List[Dict]) -> Dict:
    """分析绩效趋势"""
    if len(weekly_data) < 2:
        return {"spend_trend": "insufficient_data"}

    first_week = weekly_data[0]
    last_week = weekly_data[-1]

    spend_change = last_week["spend"] - first_week["spend"]
    conv_change = last_week["conversions"] - first_week["conversions"]

    first_cpl = Decimal(str(first_week["spend"])) / Decimal(first_week["conversions"])
    last_cpl = Decimal(str(last_week["spend"])) / Decimal(last_week["conversions"])
    cpl_change = last_cpl - first_cpl

    return {
        "spend_trend": "increasing" if spend_change > 0 else "decreasing" if spend_change < 0 else "stable",
        "conversion_trend": "increasing" if conv_change > 0 else "decreasing" if conv_change < 0 else "stable",
        "cpl_trend": "increasing" if cpl_change > 0 else "decreasing" if cpl_change < 0 else "stable"
    }

def forecast_next_month_metrics(historical_data: List[Dict]) -> Dict:
    """预测下月指标"""
    if len(historical_data) < 2:
        return {"error": "insufficient_data"}

    # 简单的线性增长预测
    last_month = historical_data[-1]
    prev_month = historical_data[-2]

    spend_growth = last_month["spend"] - prev_month["spend"]
    conv_growth = last_month["conversions"] - prev_month["conversions"]

    predicted_spend = last_month["spend"] + spend_growth
    predicted_conversions = last_month["conversions"] + conv_growth

    # 计算置信区间（简单估算）
    spend_std = Decimal("0.1") * Decimal(str(predicted_spend))  # 10%标准差

    return {
        "predicted_spend": Decimal(str(predicted_spend)),
        "predicted_conversions": predicted_conversions,
        "confidence_interval": {
            "lower": Decimal(str(predicted_spend)) - spend_std,
            "upper": Decimal(str(predicted_spend)) + spend_std
        }
    }