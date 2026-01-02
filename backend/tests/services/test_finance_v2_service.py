"""
财务管理 V2 服务层测试 - TASK-FIN-004 财务仪表盘

SoT References:
- MASTER.md v4.8 §4.5.5 资金口径定义
- LEDGER_SOT.md v1.1 §2-3 双账本
- BUSINESS_RULES.md v3.2 利润计算公式

测试范围:
- FundServiceV2: 资金概览、应收账款、资金分布
- ProfitServiceV2: 盈亏概览、项目利润、渠道成本、趋势

Version: 1.0
Author: Claude Code (TASK-FIN-004)
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch
from calendar import monthrange

from backend.services.fund_service_v2 import FundServiceV2
from backend.services.profit_service_v2 import ProfitServiceV2


class TestFundServiceV2:
    """资金总览服务测试"""

    @pytest.fixture
    def service(self, db_session):
        """创建资金服务实例"""
        return FundServiceV2(db_session)

    class TestGetOverview:
        """获取资金概览测试"""

        def test_get_overview_default_period(self, service):
            """测试默认时间范围（本月）"""
            result = service.get_overview()
            assert result.period is not None
            assert result.currency == "USD"
            assert result.summary is not None
            assert result.changes is not None

        def test_get_overview_with_month_period(self, service):
            """测试月份时间范围"""
            result = service.get_overview(period="month")
            assert result.period is not None

        def test_get_overview_with_quarter_period(self, service):
            """测试季度时间范围"""
            result = service.get_overview(period="quarter")
            assert "-Q" in result.period

        def test_get_overview_with_year_period(self, service):
            """测试年度时间范围"""
            result = service.get_overview(period="year")
            assert len(result.period) == 4  # YYYY format

        def test_get_overview_with_specific_date(self, service):
            """测试指定月份"""
            result = service.get_overview(date_str="2025-12")
            assert result.period == "2025-12"

        def test_summary_fields_present(self, service):
            """验证摘要字段完整"""
            result = service.get_overview()
            summary = result.summary
            assert hasattr(summary, "total_income")
            assert hasattr(summary, "total_expense")
            assert hasattr(summary, "available_balance")
            assert hasattr(summary, "total_receivable")
            assert hasattr(summary, "outstanding")

    class TestGetReceivables:
        """获取应收账款测试"""

        def test_get_receivables_default(self, service):
            """测试默认查询"""
            result = service.get_receivables()
            assert result.items is not None
            assert result.totals is not None

        def test_get_receivables_outstanding_only(self, service):
            """测试只显示未收"""
            result = service.get_receivables(status="outstanding")
            assert isinstance(result.items, list)

        def test_get_receivables_settled_only(self, service):
            """测试只显示已收"""
            result = service.get_receivables(status="settled")
            assert isinstance(result.items, list)

        def test_get_receivables_sort_by_outstanding(self, service):
            """测试按未收金额排序"""
            result = service.get_receivables(sort_by="outstanding")
            assert isinstance(result.items, list)

        def test_get_receivables_sort_by_client(self, service):
            """测试按客户名称排序"""
            result = service.get_receivables(sort_by="client")
            assert isinstance(result.items, list)

        def test_totals_calculation(self, service):
            """验证汇总计算"""
            result = service.get_receivables()
            totals = result.totals
            assert hasattr(totals, "total_topup")
            assert hasattr(totals, "total_receivable")
            assert hasattr(totals, "total_outstanding")

    class TestGetDistribution:
        """获取资金分布测试"""

        def test_get_distribution_by_project(self, service):
            """测试按项目分组"""
            result = service.get_distribution(group_by="project")
            assert result.group_by == "project"
            assert result.items is not None

        def test_get_distribution_by_supplier(self, service):
            """测试按供应商分组"""
            result = service.get_distribution(group_by="supplier")
            assert result.group_by == "supplier"

        def test_distribution_percentage_sum(self, service):
            """验证分布百分比总和"""
            result = service.get_distribution()
            if result.items and result.total > 0:
                total_pct = sum(item.percentage for item in result.items)
                # 百分比总和应接近 100（允许舍入误差）
                assert 99.0 <= total_pct <= 101.0 or total_pct == 0


class TestProfitServiceV2:
    """项目盈亏服务测试"""

    @pytest.fixture
    def service(self, db_session):
        """创建盈亏服务实例"""
        return ProfitServiceV2(db_session)

    class TestGetOverview:
        """获取盈亏概览测试"""

        def test_get_overview_default(self, service):
            """测试默认查询"""
            result = service.get_overview()
            assert result.period is not None
            assert result.currency == "USD"
            assert result.summary is not None
            assert result.changes is not None
            assert result.benchmarks is not None

        def test_get_overview_with_period(self, service):
            """测试指定月份"""
            result = service.get_overview(period="2025-12")
            assert result.period == "2025-12"

        def test_summary_profit_calculation(self, service):
            """验证利润计算公式"""
            result = service.get_overview()
            summary = result.summary
            # profit = revenue - cost
            expected_profit = summary.total_revenue - summary.total_cost
            assert summary.total_profit == expected_profit

        def test_benchmarks_present(self, service):
            """验证基准值存在"""
            result = service.get_overview()
            benchmarks = result.benchmarks
            assert hasattr(benchmarks, "industry_avg_profit_rate")
            assert hasattr(benchmarks, "company_target_profit_rate")
            assert benchmarks.industry_avg_profit_rate == 0.15
            assert benchmarks.company_target_profit_rate == 0.20

    class TestGetProjectProfits:
        """获取项目利润明细测试"""

        def test_get_project_profits_default(self, service):
            """测试默认查询"""
            result = service.get_project_profits()
            assert result.items is not None
            assert result.totals is not None

        def test_get_project_profits_sort_by_profit(self, service):
            """测试按利润排序"""
            result = service.get_project_profits(sort_by="profit")
            items = result.items
            if len(items) >= 2:
                # 验证降序排列
                for i in range(len(items) - 1):
                    assert items[i].profit >= items[i + 1].profit

        def test_get_project_profits_sort_by_profit_rate(self, service):
            """测试按利润率排序"""
            result = service.get_project_profits(sort_by="profit_rate")
            assert isinstance(result.items, list)

        def test_get_project_profits_active_only(self, service):
            """测试只显示活跃项目"""
            result = service.get_project_profits(status="active")
            for item in result.items:
                assert item.status in ["active", "completed"]

        def test_get_project_profits_inactive_only(self, service):
            """测试只显示非活跃项目"""
            result = service.get_project_profits(status="inactive")
            for item in result.items:
                assert item.status in ["refunded", "closed", "cancelled"]

        def test_profit_status_mapping(self, service):
            """验证利润状态映射"""
            result = service.get_project_profits()
            valid_statuses = {"healthy", "warning", "danger", "inactive"}
            for item in result.items:
                assert item.profit_status in valid_statuses

    class TestGetSupplierCosts:
        """获取渠道成本分析测试"""

        def test_get_supplier_costs_default(self, service):
            """测试默认查询"""
            result = service.get_supplier_costs()
            assert result.items is not None
            assert result.summary is not None

        def test_supplier_cost_fields(self, service):
            """验证成本字段完整"""
            result = service.get_supplier_costs()
            summary = result.summary
            assert hasattr(summary, "avg_fee_rate")
            assert hasattr(summary, "total_spend")
            assert hasattr(summary, "total_fee")

    class TestGetTrend:
        """获取利润趋势测试"""

        def test_get_trend_by_day(self, service):
            """测试按日趋势"""
            result = service.get_trend(granularity="day")
            assert result.granularity == "day"
            assert result.series is not None

        def test_get_trend_by_week(self, service):
            """测试按周趋势"""
            result = service.get_trend(granularity="week")
            assert result.granularity == "week"
            for item in result.series:
                assert "-W" in item.period

        def test_get_trend_by_month(self, service):
            """测试按月趋势"""
            result = service.get_trend(granularity="month")
            assert result.granularity == "month"

        def test_trend_series_fields(self, service):
            """验证趋势数据字段"""
            result = service.get_trend()
            for item in result.series:
                assert hasattr(item, "period")
                assert hasattr(item, "revenue")
                assert hasattr(item, "cost")
                assert hasattr(item, "profit")


class TestProfitCalculationFormulas:
    """
    利润计算公式验证

    SoT: BUSINESS_RULES.md v3.2
    - revenue = conversions_final × unit_price
    - cost = real_spend + fee (fee = spend × fee_rate)
    - profit = revenue - cost
    - profit_rate = profit / revenue
    """

    @pytest.fixture
    def service(self, db_session):
        return ProfitServiceV2(db_session)

    def test_profit_formula(self):
        """验证利润公式"""
        # 模拟数据
        conversions = 100
        unit_price = Decimal("50.00")
        real_spend = Decimal("3000.00")
        fee_rate = Decimal("0.08")

        # 计算
        revenue = conversions * unit_price  # 5000
        fee = real_spend * fee_rate  # 240
        cost = real_spend + fee  # 3240
        profit = revenue - cost  # 1760
        profit_rate = float(profit / revenue)  # 0.352

        assert revenue == Decimal("5000.00")
        assert cost == Decimal("3240.00")
        assert profit == Decimal("1760.00")
        assert 0.35 < profit_rate < 0.36

    def test_profit_status_thresholds(self, service):
        """验证利润状态阈值"""
        # healthy: >= 15%
        assert service._get_profit_status(0.20, "active") == "healthy"
        assert service._get_profit_status(0.15, "active") == "healthy"

        # warning: 5% - 15%
        assert service._get_profit_status(0.10, "active") == "warning"
        assert service._get_profit_status(0.05, "active") == "warning"

        # danger: < 5%
        assert service._get_profit_status(0.04, "active") == "danger"
        assert service._get_profit_status(0.00, "active") == "danger"
        assert service._get_profit_status(-0.10, "active") == "danger"

        # inactive: refunded/closed
        assert service._get_profit_status(0.20, "refunded") == "inactive"
        assert service._get_profit_status(0.20, "closed") == "inactive"
        assert service._get_profit_status(0.20, "cancelled") == "inactive"


class TestFundCalculationFormulas:
    """
    资金计算公式验证

    SoT: MASTER.md v4.4 §4.5.5
    - 可用余额 = 期初余额 + 本期收款 - 本期支出
    - 应收未收 = 总应收 - 总已收
    """

    @pytest.fixture
    def service(self, db_session):
        return FundServiceV2(db_session)

    def test_available_balance_formula(self, service):
        """验证可用余额公式"""
        result = service.get_overview()
        summary = result.summary

        # available_balance = opening_balance + total_income - total_expense
        expected = (
            summary.opening_balance + summary.total_income - summary.total_expense
        )
        assert summary.available_balance == expected

    def test_outstanding_formula(self, service):
        """验证应收未收公式"""
        result = service.get_overview()
        summary = result.summary

        # outstanding = total_receivable - total_received
        expected = summary.total_receivable - summary.total_received
        assert summary.outstanding == expected
