"""
项目盈亏服务 V2 测试 (Profit Service V2 Tests)

测试范围:
- 盈亏概览 (get_overview)
- 项目利润明细 (get_project_profits)
- 渠道成本分析 (get_supplier_costs)
- 利润趋势 (get_trend)
- 阶梯定价计算
- 利润状态判断

SoT References:
- MASTER.md v4.4 §6.5 (项目盈亏字段集)
- BUSINESS_RULES.md v3.2 BR-PROFIT-001~006
- CORE_MODULES.md v1.0 §4.5 (阶梯价格规则)

Version: 1.0
Author: Claude Code
"""

import pytest
from decimal import Decimal
from datetime import date, timedelta
from unittest.mock import patch, MagicMock

from backend.services.profit_service_v2 import ProfitServiceV2
from backend.schemas.finance_v2 import (
    ProfitOverviewData,
    ProjectProfitsData,
    SupplierCostsData,
    ProfitTrendData,
    ProfitStatus,
)
from backend.models import Project, DailyReport


class TestProfitServiceOverview:
    """盈亏概览测试"""

    def test_get_overview_current_month(self, db_session):
        """测试获取当月概览"""
        service = ProfitServiceV2(db_session)
        overview = service.get_overview()

        assert isinstance(overview, ProfitOverviewData)
        assert overview.currency == "USD"
        assert overview.summary is not None
        assert overview.changes is not None
        assert overview.benchmarks is not None
        # 验证基准值
        assert overview.benchmarks.industry_avg_profit_rate == 0.15
        assert overview.benchmarks.company_target_profit_rate == 0.20

    def test_get_overview_specific_period(self, db_session):
        """测试获取指定月份概览"""
        service = ProfitServiceV2(db_session)
        overview = service.get_overview(period="2025-12")

        assert overview.period == "2025-12"

    def test_get_overview_with_data(
        self, db_session, test_project, test_ad_account, admin_user
    ):
        """测试有数据时的概览"""
        # 创建测试日报数据
        # 注意：DailyReport 通过 ad_account_id 关联，项目关系通过 AdAccount 获取
        report = DailyReport(
            ad_account_id=test_ad_account.id,
            report_date=date.today(),
            conversions_final=100,
            real_spend=Decimal("1000.00"),
            status="final_locked",
            created_by=admin_user.id,
        )
        db_session.add(report)
        db_session.commit()

        service = ProfitServiceV2(db_session)
        overview = service.get_overview()

        # 验证汇总数据
        assert overview.summary.total_conversions >= 100
        # 消耗应该大于等于测试数据
        # 注意：可能有其他测试数据影响结果


class TestProfitServiceProjectProfits:
    """项目利润明细测试"""

    def test_get_project_profits_all(self, db_session):
        """测试获取所有项目利润"""
        service = ProfitServiceV2(db_session)
        result = service.get_project_profits()

        assert isinstance(result, ProjectProfitsData)
        assert result.totals is not None
        assert isinstance(result.items, list)

    def test_get_project_profits_active_only(self, db_session, test_project):
        """测试只获取活跃项目"""
        service = ProfitServiceV2(db_session)
        result = service.get_project_profits(status="active")

        assert isinstance(result, ProjectProfitsData)
        # 所有返回的项目应该是活跃状态
        for item in result.items:
            assert item.status in ("active", "completed")

    def test_get_project_profits_inactive_only(self, db_session):
        """测试只获取非活跃项目"""
        service = ProfitServiceV2(db_session)
        result = service.get_project_profits(status="inactive")

        # 所有返回的项目应该是非活跃状态
        for item in result.items:
            assert item.status in ("refunded", "closed", "cancelled")

    def test_get_project_profits_sort_by_profit(self, db_session):
        """测试按利润排序"""
        service = ProfitServiceV2(db_session)
        result = service.get_project_profits(sort_by="profit")

        # 验证降序排序
        for i in range(len(result.items) - 1):
            assert result.items[i].profit >= result.items[i + 1].profit

    def test_get_project_profits_sort_by_profit_rate(self, db_session):
        """测试按利润率排序"""
        service = ProfitServiceV2(db_session)
        result = service.get_project_profits(sort_by="profit_rate")

        # 验证降序排序
        for i in range(len(result.items) - 1):
            assert result.items[i].profit_rate >= result.items[i + 1].profit_rate

    def test_get_project_profits_sort_by_revenue(self, db_session):
        """测试按收入排序"""
        service = ProfitServiceV2(db_session)
        result = service.get_project_profits(sort_by="revenue")

        # 验证降序排序
        for i in range(len(result.items) - 1):
            assert result.items[i].revenue >= result.items[i + 1].revenue

    def test_get_project_profits_with_data(
        self, db_session, test_project, test_ad_account, admin_user
    ):
        """测试有日报数据时的项目利润"""
        # 设置项目单价
        test_project.unit_price = Decimal("50.00")
        db_session.commit()

        # 创建测试日报 (通过 ad_account_id 关联项目)
        report = DailyReport(
            ad_account_id=test_ad_account.id,
            report_date=date.today(),
            conversions_final=20,
            real_spend=Decimal("800.00"),
            status="final_locked",
            created_by=admin_user.id,
        )
        db_session.add(report)
        db_session.commit()

        service = ProfitServiceV2(db_session)
        result = service.get_project_profits()

        # 查找测试项目
        project_item = next(
            (item for item in result.items if item.project_id == test_project.id),
            None,
        )

        if project_item:
            # 收入 = 20 * 50 = 1000
            # 成本 = 800 + 800*0.08 = 864
            # 利润 = 1000 - 864 = 136
            assert project_item.conversions == 20
            assert project_item.revenue == Decimal("1000.00")


class TestProfitServiceSupplierCosts:
    """渠道成本分析测试"""

    def test_get_supplier_costs(self, db_session):
        """测试获取渠道成本"""
        service = ProfitServiceV2(db_session)
        result = service.get_supplier_costs()

        assert isinstance(result, SupplierCostsData)
        assert result.summary is not None
        assert isinstance(result.items, list)

    def test_get_supplier_costs_specific_period(self, db_session):
        """测试指定期间的渠道成本"""
        service = ProfitServiceV2(db_session)
        result = service.get_supplier_costs(period="2025-12")

        assert isinstance(result, SupplierCostsData)

    def test_get_supplier_costs_summary(self, db_session):
        """测试渠道成本汇总"""
        service = ProfitServiceV2(db_session)
        result = service.get_supplier_costs()

        # 验证汇总数据结构
        assert hasattr(result.summary, "avg_fee_rate")
        assert hasattr(result.summary, "total_spend")
        assert hasattr(result.summary, "total_fee")


class TestProfitServiceTrend:
    """利润趋势测试"""

    def test_get_trend_daily(self, db_session):
        """测试日趋势"""
        service = ProfitServiceV2(db_session)
        result = service.get_trend(granularity="day")

        assert isinstance(result, ProfitTrendData)
        assert result.granularity == "day"
        assert isinstance(result.series, list)

    def test_get_trend_weekly(self, db_session):
        """测试周趋势"""
        service = ProfitServiceV2(db_session)
        result = service.get_trend(granularity="week")

        assert result.granularity == "week"
        # 周标签格式应该是 YYYY-Wxx
        for item in result.series:
            assert "-W" in item.period

    def test_get_trend_monthly(self, db_session):
        """测试月趋势"""
        service = ProfitServiceV2(db_session)
        result = service.get_trend(granularity="month")

        assert result.granularity == "month"
        # 月标签格式应该是 YYYY-MM
        for item in result.series:
            assert len(item.period) == 7  # "2025-12"

    def test_get_trend_series_structure(self, db_session):
        """测试趋势序列数据结构"""
        service = ProfitServiceV2(db_session)
        result = service.get_trend(granularity="week")

        for item in result.series:
            assert hasattr(item, "period")
            assert hasattr(item, "revenue")
            assert hasattr(item, "cost")
            assert hasattr(item, "profit")


class TestProfitServiceRevenueCalculation:
    """收入计算测试"""

    def test_calculate_revenue_fixed_price(self, db_session, test_project):
        """测试固定单价收入计算"""
        test_project.unit_price = Decimal("100.00")
        test_project.price_rules = None
        db_session.commit()

        service = ProfitServiceV2(db_session)
        revenue = service._calculate_revenue(test_project, 50)

        assert revenue == Decimal("5000.00")  # 50 * 100

    def test_calculate_revenue_tiered_price(self, db_session, test_project):
        """测试阶梯定价收入计算"""
        test_project.unit_price = Decimal("100.00")
        test_project.price_rules = {
            "type": "tiered",
            "tiers": [
                {"min": 0, "max": 10, "price": 120},
                {"min": 11, "max": 50, "price": 100},
                {"min": 51, "max": None, "price": 80},
            ],
        }
        db_session.commit()

        service = ProfitServiceV2(db_session)

        # 测试 5 个转化（全部在第一档）
        revenue_5 = service._calculate_revenue(test_project, 5)
        assert revenue_5 == Decimal("600.00")  # 5 * 120

        # 测试 15 个转化（跨两档）
        revenue_15 = service._calculate_revenue(test_project, 15)
        # 前 11 个 @ 120 = 1320
        # 后 4 个 @ 100 = 400
        # 总计 = 1720
        expected = Decimal("120") * 11 + Decimal("100") * 4
        assert revenue_15 == expected

    def test_calculate_revenue_spend_ratio(self, db_session, test_project):
        """测试按消耗比例定价"""
        test_project.unit_price = Decimal("50.00")
        test_project.price_rules = {
            "type": "spend_ratio",
            "ratio": 1.2,
        }
        db_session.commit()

        service = ProfitServiceV2(db_session)
        # 当前实现简化为基础收入
        revenue = service._calculate_revenue(test_project, 20)
        assert revenue == Decimal("1000.00")  # 20 * 50


class TestProfitServiceProfitStatus:
    """利润状态判断测试"""

    def test_profit_status_healthy(self, db_session):
        """测试健康状态 (>=15%)"""
        service = ProfitServiceV2(db_session)

        status = service._get_profit_status(0.20, "active")
        assert status == "healthy"

        status = service._get_profit_status(0.15, "active")
        assert status == "healthy"

    def test_profit_status_warning(self, db_session):
        """测试警告状态 (5%-15%)"""
        service = ProfitServiceV2(db_session)

        status = service._get_profit_status(0.10, "active")
        assert status == "warning"

        status = service._get_profit_status(0.05, "active")
        assert status == "warning"

    def test_profit_status_danger(self, db_session):
        """测试危险状态 (<5%)"""
        service = ProfitServiceV2(db_session)

        status = service._get_profit_status(0.04, "active")
        assert status == "danger"

        status = service._get_profit_status(0.0, "active")
        assert status == "danger"

        status = service._get_profit_status(-0.1, "active")
        assert status == "danger"

    def test_profit_status_inactive(self, db_session):
        """测试非活跃状态"""
        service = ProfitServiceV2(db_session)

        # 即使利润率很高，非活跃项目也应该是 inactive
        status = service._get_profit_status(0.30, "refunded")
        assert status == "inactive"

        status = service._get_profit_status(0.20, "closed")
        assert status == "inactive"

        status = service._get_profit_status(0.15, "cancelled")
        assert status == "inactive"


class TestProfitServicePeriodParsing:
    """时间段解析测试"""

    def test_parse_period_specific_month(self, db_session):
        """测试解析指定月份"""
        service = ProfitServiceV2(db_session)
        start, end, period_str = service._parse_period("2025-12")

        assert start == date(2025, 12, 1)
        assert end == date(2025, 12, 31)
        assert period_str == "2025-12"

    def test_parse_period_february(self, db_session):
        """测试解析二月（考虑闰年）"""
        service = ProfitServiceV2(db_session)

        # 非闰年
        start, end, period_str = service._parse_period("2025-02")
        assert end == date(2025, 2, 28)

        # 闰年
        start, end, period_str = service._parse_period("2024-02")
        assert end == date(2024, 2, 29)

    def test_parse_period_default_current_month(self, db_session):
        """测试默认为当月"""
        service = ProfitServiceV2(db_session)
        start, end, period_str = service._parse_period(None)

        today = date.today()
        assert start.year == today.year
        assert start.month == today.month
        assert start.day == 1

    def test_get_previous_period(self, db_session):
        """测试获取上一期"""
        service = ProfitServiceV2(db_session)

        start = date(2025, 12, 1)
        end = date(2025, 12, 31)

        prev_start, prev_end = service._get_previous_period(start, end)

        # 上一期应该是相同长度的时间段
        assert (prev_end - prev_start).days == (end - start).days


class TestProfitServiceChangeCalculation:
    """环比变化计算测试"""

    def test_calculate_change_pct_increase(self, db_session):
        """测试增长百分比"""
        service = ProfitServiceV2(db_session)

        change = service._calculate_change_pct(Decimal("120"), Decimal("100"))
        assert change == 20.0  # 20% 增长

    def test_calculate_change_pct_decrease(self, db_session):
        """测试下降百分比"""
        service = ProfitServiceV2(db_session)

        change = service._calculate_change_pct(Decimal("80"), Decimal("100"))
        assert change == -20.0  # 20% 下降

    def test_calculate_change_pct_zero_previous(self, db_session):
        """测试上期为零"""
        service = ProfitServiceV2(db_session)

        change = service._calculate_change_pct(Decimal("100"), Decimal("0"))
        assert change is None  # 无法计算

    def test_calculate_change_pct_none_previous(self, db_session):
        """测试上期为 None"""
        service = ProfitServiceV2(db_session)

        change = service._calculate_change_pct(Decimal("100"), None)
        assert change is None


class TestProfitServicePriceRules:
    """价格规则测试"""

    def test_get_price_rules_none(self, db_session, test_project):
        """测试无价格规则"""
        test_project.price_rules = None
        db_session.commit()

        service = ProfitServiceV2(db_session)
        rules = service._get_price_rules(test_project)

        assert rules is None

    def test_get_price_rules_fixed(self, db_session, test_project):
        """测试固定价格规则"""
        test_project.price_rules = {"type": "fixed"}
        db_session.commit()

        service = ProfitServiceV2(db_session)
        rules = service._get_price_rules(test_project)

        assert rules is not None
        assert rules.type == "fixed"

    def test_get_price_rules_tiered(self, db_session, test_project):
        """测试阶梯价格规则"""
        test_project.price_rules = {
            "type": "tiered",
            "tiers": [
                {"min": 0, "max": 100, "price": 50},
                {"min": 101, "max": None, "price": 40},
            ],
        }
        db_session.commit()

        service = ProfitServiceV2(db_session)
        rules = service._get_price_rules(test_project)

        assert rules is not None
        assert rules.type == "tiered"
        assert len(rules.tiers) == 2
        assert rules.tiers[0].price == Decimal("50")

    def test_get_price_rules_spend_ratio(self, db_session, test_project):
        """测试消耗比例规则"""
        test_project.price_rules = {
            "type": "spend_ratio",
            "ratio": 1.15,
        }
        db_session.commit()

        service = ProfitServiceV2(db_session)
        rules = service._get_price_rules(test_project)

        assert rules is not None
        assert rules.type == "spend_ratio"
        assert rules.ratio == 1.15


class TestProfitServicePeriodGeneration:
    """时间段生成测试"""

    def test_generate_periods_daily(self, db_session):
        """测试生成日时间段"""
        service = ProfitServiceV2(db_session)
        start = date(2025, 12, 1)
        end = date(2025, 12, 5)

        periods = service._generate_periods(start, end, "day")

        assert len(periods) == 5
        assert periods[0][2] == "2025-12-01"
        assert periods[4][2] == "2025-12-05"

    def test_generate_periods_weekly(self, db_session):
        """测试生成周时间段"""
        service = ProfitServiceV2(db_session)
        start = date(2025, 12, 1)
        end = date(2025, 12, 31)

        periods = service._generate_periods(start, end, "week")

        # 12月有约5周
        assert len(periods) >= 4
        # 验证周标签格式
        for period_start, period_end, label in periods:
            assert "-W" in label

    def test_generate_periods_monthly(self, db_session):
        """测试生成月时间段"""
        service = ProfitServiceV2(db_session)
        start = date(2025, 1, 1)
        end = date(2025, 3, 31)

        periods = service._generate_periods(start, end, "month")

        assert len(periods) == 3
        assert periods[0][2] == "2025-01"
        assert periods[1][2] == "2025-02"
        assert periods[2][2] == "2025-03"


class TestProfitServiceN1Optimization:
    """N+1 查询优化测试"""

    def test_project_profits_uses_batch_query(
        self, db_session, test_project, test_ad_account, admin_user
    ):
        """测试项目利润使用批量查询"""
        # 创建多个日报 (通过 ad_account_id 关联项目)
        for i in range(5):
            report = DailyReport(
                ad_account_id=test_ad_account.id,
                report_date=date.today() - timedelta(days=i),
                conversions_final=10 + i,
                real_spend=Decimal("100.00") + Decimal(str(i * 10)),
                status="final_locked",
                created_by=admin_user.id,
            )
            db_session.add(report)
        db_session.commit()

        service = ProfitServiceV2(db_session)

        # 这个测试主要验证不会抛出 N+1 相关的性能问题
        # 实际的性能测试需要更复杂的基础设施
        result = service.get_project_profits()

        # 验证结果正确返回
        assert isinstance(result, ProjectProfitsData)
        assert result.totals is not None
