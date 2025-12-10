"""
财务利润服务测试模块
测试 backend/services/finance_service.py 的利润计算和分析功能
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import Mock, MagicMock
from sqlalchemy.orm import Session

from backend.services.finance_service import FinanceService, get_finance_service
from backend.exceptions import ResourceNotFoundException, BusinessRuleException
from backend.models import Project, DailyReport, AdAccount, Channel
from backend.schemas.finance import (
    ProfitSummaryResponse,
    ProfitByProjectResponse,
    ProfitByAccountResponse,
    ProfitByChannelResponse,
    ProfitTrendResponse,
    ProfitCompareResponse,
    ProfitOverviewResponse,
)


# ==================== Fixtures ====================

@pytest.fixture
def mock_db():
    """模拟数据库会话"""
    return Mock(spec=Session)


@pytest.fixture
def finance_service(mock_db):
    """财务服务 fixture"""
    return FinanceService(mock_db)


@pytest.fixture
def sample_project():
    """示例项目"""
    project = Mock(spec=Project)
    project.id = 1
    project.name = "Test Project"
    return project


@pytest.fixture
def sample_ad_account():
    """示例广告账户"""
    account = Mock(spec=AdAccount)
    account.id = 101
    account.account_name = "Test Account"
    account.project_id = 1
    account.channel_id = 1
    return account


@pytest.fixture
def sample_channel():
    """示例渠道"""
    channel = Mock(spec=Channel)
    channel.id = 1
    channel.name = "Test Channel"
    return channel


# ==================== 初始化测试 ====================

@pytest.mark.unit
@pytest.mark.finance
class TestFinanceServiceInitialization:
    """测试财务服务初始化"""

    def test_finance_service_initialization(self, mock_db):
        """测试财务服务初始化"""
        service = FinanceService(mock_db)
        assert service.db == mock_db

    def test_get_finance_service_factory(self, mock_db):
        """测试工厂函数"""
        service = get_finance_service(mock_db)
        assert isinstance(service, FinanceService)
        assert service.db == mock_db


# ==================== 利润汇总测试 ====================

@pytest.mark.unit
@pytest.mark.finance
class TestProfitSummary:
    """测试利润汇总功能"""

    def test_get_profit_summary_invalid_date_range(self, finance_service):
        """测试无效的日期范围"""
        start = date(2024, 12, 31)
        end = date(2024, 1, 1)

        with pytest.raises(BusinessRuleException) as exc_info:
            finance_service.get_profit_summary(start_date=start, end_date=end)

        assert "开始日期不能晚于结束日期" in str(exc_info.value.message)

    def test_get_profit_summary_project_not_found(self, finance_service, mock_db):
        """测试项目不存在"""
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query

        with pytest.raises(ResourceNotFoundException) as exc_info:
            finance_service.get_profit_summary(project_id=999)

        assert "项目 999 不存在" in str(exc_info.value.message)

    def test_get_profit_summary_success_no_filters(self, finance_service, mock_db):
        """测试成功获取利润汇总（无过滤）"""
        # 模拟查询结果
        mock_result = Mock()
        mock_result.report_date = date(2024, 1, 1)
        mock_result.project_id = 1
        mock_result.project_name = "Test Project"
        mock_result.project_unit_price = Decimal("100.00")
        mock_result.conversions_final = 50
        mock_result.real_spend = Decimal("3000.00")

        mock_query = Mock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [mock_result]
        mock_db.query.return_value = mock_query

        result = finance_service.get_profit_summary()

        assert isinstance(result, ProfitSummaryResponse)
        assert len(result.items) == 1
        assert result.total_conversions == 50
        assert result.total_revenue == Decimal("5000.00")
        assert result.total_cost == Decimal("3000.00")
        assert result.total_profit == Decimal("2000.00")
        assert result.overall_profit_margin == 40.0

    def test_get_profit_summary_with_project_filter(self, finance_service, mock_db, sample_project):
        """测试带项目过滤的利润汇总"""
        # 模拟项目存在
        mock_project_query = Mock()
        mock_project_query.filter.return_value.first.return_value = sample_project

        # 模拟数据查询
        mock_result = Mock()
        mock_result.report_date = date(2024, 1, 1)
        mock_result.project_id = 1
        mock_result.project_name = "Test Project"
        mock_result.project_unit_price = Decimal("50.00")
        mock_result.conversions_final = 100
        mock_result.real_spend = Decimal("4000.00")

        mock_data_query = Mock()
        mock_data_query.join.return_value = mock_data_query
        mock_data_query.filter.return_value = mock_data_query
        mock_data_query.group_by.return_value = mock_data_query
        mock_data_query.order_by.return_value = mock_data_query
        mock_data_query.all.return_value = [mock_result]

        # 第一次调用返回项目查询，第二次返回数据查询
        mock_db.query.side_effect = [mock_project_query, mock_data_query]

        result = finance_service.get_profit_summary(project_id=1)

        assert isinstance(result, ProfitSummaryResponse)
        assert result.items[0].project_id == 1


# ==================== 按项目利润测试 ====================

@pytest.mark.unit
@pytest.mark.finance
class TestProfitByProject:
    """测试按项目利润统计"""

    def test_get_profit_by_project_invalid_date(self, finance_service):
        """测试无效日期范围"""
        with pytest.raises(BusinessRuleException):
            finance_service.get_profit_by_project(
                start_date=date(2024, 12, 31),
                end_date=date(2024, 1, 1)
            )

    def test_get_profit_by_project_success(self, finance_service, mock_db):
        """测试成功获取按项目利润"""
        mock_result = Mock()
        mock_result.project_id = 1
        mock_result.project_name = "Project A"
        mock_result.conversions_final = 200
        mock_result.avg_unit_price = 75.0
        mock_result.real_spend = Decimal("10000.00")
        mock_result.report_count = 30

        mock_query = Mock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [mock_result]
        mock_db.query.return_value = mock_query

        result = finance_service.get_profit_by_project(limit=20)

        assert isinstance(result, ProfitByProjectResponse)
        assert result.total_projects == 1
        assert len(result.items) == 1
        assert result.items[0].project_id == 1
        assert result.items[0].project_name == "Project A"


# ==================== 按账户利润测试 ====================

@pytest.mark.unit
@pytest.mark.finance
class TestProfitByAccount:
    """测试按账户利润统计"""

    def test_get_profit_by_account_project_not_found(self, finance_service, mock_db):
        """测试项目不存在"""
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query

        with pytest.raises(ResourceNotFoundException):
            finance_service.get_profit_by_account(project_id=999)

    def test_get_profit_by_account_success(self, finance_service, mock_db, sample_project):
        """测试成功获取按账户利润"""
        # 模拟项目查询
        mock_project_query = Mock()
        mock_project_query.filter.return_value.first.return_value = sample_project

        # 模拟数据查询
        mock_result = Mock()
        mock_result.ad_account_id = 101
        mock_result.account_name = "Account A"
        mock_result.project_id = 1
        mock_result.project_name = "Test Project"
        mock_result.conversions_final = 50
        mock_result.avg_unit_price = 100.0
        mock_result.real_spend = Decimal("4000.00")

        mock_data_query = Mock()
        mock_data_query.join.return_value = mock_data_query
        mock_data_query.filter.return_value = mock_data_query
        mock_data_query.group_by.return_value = mock_data_query
        mock_data_query.order_by.return_value = mock_data_query
        mock_data_query.limit.return_value = mock_data_query
        mock_data_query.all.return_value = [mock_result]

        mock_db.query.side_effect = [mock_project_query, mock_data_query]

        result = finance_service.get_profit_by_account(project_id=1)

        assert isinstance(result, ProfitByAccountResponse)
        assert result.total_accounts == 1
        assert result.items[0].ad_account_id == 101


# ==================== 按渠道利润测试 ====================

@pytest.mark.unit
@pytest.mark.finance
class TestProfitByChannel:
    """测试按渠道利润统计"""

    def test_get_profit_by_channel_success(self, finance_service, mock_db):
        """测试成功获取按渠道利润"""
        mock_result = Mock()
        mock_result.channel_id = 1
        mock_result.channel_name = "Channel A"
        mock_result.account_count = 5
        mock_result.conversions_final = 300
        mock_result.avg_unit_price = 80.0
        mock_result.real_spend = Decimal("20000.00")

        mock_query = Mock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [mock_result]
        mock_db.query.return_value = mock_query

        result = finance_service.get_profit_by_channel()

        assert isinstance(result, ProfitByChannelResponse)
        assert result.total_channels == 1
        assert result.items[0].channel_id == 1
        assert result.items[0].total_accounts == 5


# ==================== 利润趋势测试 ====================

@pytest.mark.unit
@pytest.mark.finance
class TestProfitTrend:
    """测试利润趋势分析"""

    def test_get_profit_trend_invalid_date_range(self, finance_service):
        """测试无效日期范围"""
        with pytest.raises(BusinessRuleException):
            finance_service.get_profit_trend(
                start_date=date(2024, 12, 31),
                end_date=date(2024, 1, 1)
            )

    def test_get_profit_trend_daily_granularity(self, finance_service, mock_db):
        """测试日粒度趋势"""
        mock_result = Mock()
        mock_result.period = date(2024, 1, 1)
        mock_result.conversions_final = 100
        mock_result.avg_unit_price = 50.0
        mock_result.real_spend = Decimal("4000.00")

        mock_query = Mock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [mock_result]
        mock_db.query.return_value = mock_query

        result = finance_service.get_profit_trend(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            granularity="daily"
        )

        assert isinstance(result, ProfitTrendResponse)
        assert result.granularity == "daily"
        assert result.period_count == 1

    def test_get_profit_trend_default_date_range(self, finance_service, mock_db):
        """测试默认日期范围（最近30天）"""
        mock_query = Mock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []
        mock_db.query.return_value = mock_query

        result = finance_service.get_profit_trend()

        assert isinstance(result, ProfitTrendResponse)


# ==================== 利润对比测试 ====================

@pytest.mark.unit
@pytest.mark.finance
class TestProfitCompare:
    """测试项目利润对比"""

    def test_compare_profit_empty_project_list(self, finance_service):
        """测试空项目列表"""
        with pytest.raises(BusinessRuleException) as exc_info:
            finance_service.compare_profit(project_ids=[])

        assert "至少需要指定一个项目进行对比" in str(exc_info.value.message)

    def test_compare_profit_projects_not_found(self, finance_service, mock_db):
        """测试项目不存在"""
        mock_query = Mock()
        mock_query.filter.return_value.all.return_value = []
        mock_db.query.return_value = mock_query

        with pytest.raises(ResourceNotFoundException):
            finance_service.compare_profit(project_ids=[1, 2, 3])

    def test_compare_profit_success(self, finance_service, mock_db):
        """测试成功对比项目利润"""
        # 模拟项目存在
        project1 = Mock(spec=Project)
        project1.id = 1
        project1.name = "Project 1"

        project2 = Mock(spec=Project)
        project2.id = 2
        project2.name = "Project 2"

        mock_project_query = Mock()
        mock_project_query.filter.return_value.all.return_value = [project1, project2]

        # 模拟数据查询
        result1 = Mock()
        result1.project_id = 1
        result1.project_name = "Project 1"
        result1.conversions_final = 100
        result1.avg_unit_price = 60.0
        result1.real_spend = Decimal("5000.00")

        result2 = Mock()
        result2.project_id = 2
        result2.project_name = "Project 2"
        result2.conversions_final = 80
        result2.avg_unit_price = 70.0
        result2.real_spend = Decimal("4500.00")

        mock_data_query = Mock()
        mock_data_query.join.return_value = mock_data_query
        mock_data_query.filter.return_value = mock_data_query
        mock_data_query.group_by.return_value = mock_data_query
        mock_data_query.all.return_value = [result1, result2]

        mock_db.query.side_effect = [mock_project_query, mock_data_query]

        result = finance_service.compare_profit(project_ids=[1, 2])

        assert isinstance(result, ProfitCompareResponse)
        assert result.compare_count == 2
        assert result.best_profit_project is not None


# ==================== 利润概览测试 ====================

@pytest.mark.unit
@pytest.mark.finance
class TestProfitOverview:
    """测试利润概览"""

    def test_get_profit_overview_success(self, finance_service, mock_db):
        """测试成功获取利润概览"""
        # 模拟每日数据查询结果（用于今天、本周、本月）
        mock_period_result = Mock()
        mock_period_result.conversions = 50
        mock_period_result.avg_unit_price = Decimal("100.00")  # 使用Decimal类型
        mock_period_result.real_spend = Decimal("4000.00")

        # 模拟top_projects查询结果
        mock_top_project = Mock()
        mock_top_project.project_id = 1
        mock_top_project.project_name = "Test Project"
        mock_top_project.conversions = 50
        mock_top_project.real_spend = Decimal("4000.00")

        # 创建查询Mock：需要支持多次调用（今天、本周、本月、top_projects）
        def create_query_mock():
            query = Mock()
            query.join.return_value = query
            query.filter.return_value = query
            query.group_by.return_value = query
            query.order_by.return_value = query
            query.limit.return_value = query
            query.first.return_value = mock_period_result
            query.all.return_value = [mock_top_project]
            return query

        # 模拟多次查询调用：今天、昨天、本周、上周、本月、上月、top_projects（共7次）
        mock_db.query.side_effect = [create_query_mock() for _ in range(7)]

        result = finance_service.get_profit_overview()

        assert isinstance(result, ProfitOverviewResponse)
        assert result.today_revenue >= Decimal("0.00")
        assert result.week_revenue >= Decimal("0.00")
        assert result.month_revenue >= Decimal("0.00")


# ==================== 辅助方法测试 ====================

@pytest.mark.unit
@pytest.mark.finance
class TestHelperMethods:
    """测试辅助方法"""

    def test_calculate_profit_margin_positive_revenue(self, finance_service):
        """测试正常利润率计算"""
        revenue = Decimal("10000.00")
        profit = Decimal("2000.00")

        margin = finance_service._calculate_profit_margin(revenue, profit)

        assert margin == 20.0

    def test_calculate_profit_margin_zero_revenue(self, finance_service):
        """测试零收入利润率"""
        revenue = Decimal("0.00")
        profit = Decimal("0.00")

        margin = finance_service._calculate_profit_margin(revenue, profit)

        assert margin == 0.0

    def test_calculate_profit_margin_negative_profit(self, finance_service):
        """测试负利润率"""
        revenue = Decimal("10000.00")
        profit = Decimal("-1000.00")

        margin = finance_service._calculate_profit_margin(revenue, profit)

        assert margin == -10.0


# ==================== 边界情况测试 ====================

@pytest.mark.unit
@pytest.mark.finance
class TestFinanceServiceEdgeCases:
    """测试财务服务边界情况"""

    def test_profit_summary_empty_results(self, finance_service, mock_db):
        """测试空结果集"""
        mock_query = Mock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []
        mock_db.query.return_value = mock_query

        result = finance_service.get_profit_summary()

        assert isinstance(result, ProfitSummaryResponse)
        assert len(result.items) == 0
        assert result.total_conversions == 0
        assert result.total_revenue == Decimal("0.00")

    def test_profit_with_zero_unit_price(self, finance_service, mock_db):
        """测试单价为零的情况"""
        mock_result = Mock()
        mock_result.report_date = date(2024, 1, 1)
        mock_result.project_id = 1
        mock_result.project_name = "Test Project"
        mock_result.project_unit_price = Decimal("0.00")
        mock_result.conversions_final = 100
        mock_result.real_spend = Decimal("5000.00")

        mock_query = Mock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [mock_result]
        mock_db.query.return_value = mock_query

        result = finance_service.get_profit_summary()

        assert result.items[0].revenue == Decimal("0.00")
        assert result.items[0].profit == Decimal("-5000.00")

    def test_profit_with_null_conversions(self, finance_service, mock_db):
        """测试转化数为 NULL 的情况"""
        mock_result = Mock()
        mock_result.report_date = date(2024, 1, 1)
        mock_result.project_id = 1
        mock_result.project_name = "Test Project"
        mock_result.project_unit_price = Decimal("100.00")
        mock_result.conversions_final = None
        mock_result.real_spend = Decimal("1000.00")

        mock_query = Mock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [mock_result]
        mock_db.query.return_value = mock_query

        result = finance_service.get_profit_summary()

        assert result.items[0].conversions_final == 0
        assert result.items[0].revenue == Decimal("0.00")


# ==================== 集成测试 ====================

@pytest.mark.integration
@pytest.mark.finance
class TestFinanceServiceIntegration:
    """财务服务集成测试"""

    def test_full_profit_analysis_workflow(self, finance_service, mock_db):
        """测试完整的利润分析工作流"""
        # 模拟多个方法调用
        mock_query = Mock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        mock_query.first.return_value = None
        mock_db.query.return_value = mock_query

        # 获取概览
        overview = finance_service.get_profit_overview()
        assert isinstance(overview, ProfitOverviewResponse)

        # 获取汇总
        summary = finance_service.get_profit_summary()
        assert isinstance(summary, ProfitSummaryResponse)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
