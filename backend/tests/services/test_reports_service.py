"""
报表服务测试模块
测试 backend/services/reports_service.py 的报表生成和查询功能
"""

import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, MagicMock, AsyncMock, patch
from sqlalchemy.orm import Session

from backend.services.reports_service import ReportsService, get_reports_service
from backend.models import (
    Project, AdAccount, AccountPerformance, Channel,
    LedgerEntry, ReconciliationBatch, TopupRequest,
    DailyReport
)
# 注意：AdSpendDaily 是占位符，实际应使用 AccountPerformance
from backend.schemas.reports import (
    PerformanceReportResponse,
    ProfitReportResponse,
    ReconciliationReportResponse,
    FinancialSummaryResponse,
    DashboardSummary,
    TrendReportResponse,
)


# ==================== Fixtures ====================

@pytest.fixture
def mock_db():
    """模拟数据库会话"""
    return Mock(spec=Session)


@pytest.fixture
def reports_service(mock_db):
    """报表服务 fixture"""
    return ReportsService(mock_db)


@pytest.fixture
def sample_date_range():
    """示例日期范围"""
    return {
        'start_date': date(2024, 1, 1),
        'end_date': date(2024, 1, 31)
    }


@pytest.fixture
def mock_query_result():
    """模拟查询结果"""
    result = Mock()
    result.project_id = 1
    result.project_name = "Test Project"
    result.channel_id = 1
    result.channel_name = "Test Channel"
    result.total_spend = 10000.00
    result.total_leads = 500
    return result


# ==================== 初始化测试 ====================

@pytest.mark.unit
@pytest.mark.reports
class TestReportsServiceInitialization:
    """测试报表服务初始化"""

    def test_reports_service_initialization(self, mock_db):
        """测试报表服务初始化"""
        service = ReportsService(mock_db)
        assert service.db == mock_db

    def test_get_reports_service_factory(self, mock_db):
        """测试工厂函数"""
        service = get_reports_service(mock_db)
        assert isinstance(service, ReportsService)
        assert service.db == mock_db


# ==================== 效果报表测试 ====================

@pytest.mark.unit
@pytest.mark.reports
class TestPerformanceReport:
    """测试效果报表功能"""

    @pytest.mark.asyncio
    async def test_get_performance_report_default_date_range(self, reports_service, mock_db):
        """测试默认日期范围（最近30天）"""
        mock_query = Mock()
        mock_query.select_from.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = []
        mock_db.query.return_value = mock_query

        result = await reports_service.get_performance_report()

        assert isinstance(result, PerformanceReportResponse)
        assert result.meta is not None
        # 验证日期范围是最近30天
        end_date = date.fromisoformat(result.meta['end_date'])
        start_date = date.fromisoformat(result.meta['start_date'])
        assert (end_date - start_date).days == 30

    @pytest.mark.asyncio
    async def test_get_performance_report_with_data(self, reports_service, mock_db, mock_query_result):
        """测试带数据的效果报表"""
        mock_query = Mock()
        mock_query.select_from.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = [mock_query_result]
        mock_db.query.return_value = mock_query

        result = await reports_service.get_performance_report(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31)
        )

        assert isinstance(result, PerformanceReportResponse)
        assert len(result.items) == 1
        assert result.items[0].project_name == "Test Project"
        assert result.summary['total_leads'] == 500
        assert result.summary['project_count'] == 1

    @pytest.mark.asyncio
    async def test_get_performance_report_with_filters(self, reports_service, mock_db):
        """测试带过滤条件的效果报表"""
        mock_query = Mock()
        mock_query.select_from.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = []
        mock_db.query.return_value = mock_query

        result = await reports_service.get_performance_report(
            project_ids=[1, 2],
            channel_ids=[1]
        )

        assert isinstance(result, PerformanceReportResponse)
        # 验证 filter 被调用了两次（project_ids 和 channel_ids）
        assert mock_query.filter.call_count >= 2

    @pytest.mark.asyncio
    async def test_get_performance_report_cpa_calculation(self, reports_service, mock_db):
        """测试 CPA 计算"""
        result = Mock()
        result.project_id = 1
        result.project_name = "Test"
        result.channel_id = 1
        result.channel_name = "Channel"
        result.total_spend = 5000.00
        result.total_leads = 100

        mock_query = Mock()
        mock_query.select_from.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = [result]
        mock_db.query.return_value = mock_query

        response = await reports_service.get_performance_report()

        assert response.items[0].cpa == Decimal("5000.00") / 100

    @pytest.mark.asyncio
    async def test_get_performance_report_zero_leads(self, reports_service, mock_db):
        """测试零线索时 CPA 为 None"""
        result = Mock()
        result.project_id = 1
        result.project_name = "Test"
        result.channel_id = 1
        result.channel_name = "Channel"
        result.total_spend = 5000.00
        result.total_leads = 0

        mock_query = Mock()
        mock_query.select_from.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = [result]
        mock_db.query.return_value = mock_query

        response = await reports_service.get_performance_report()

        assert response.items[0].cpa is None


# ==================== 利润报表测试 ====================

@pytest.mark.unit
@pytest.mark.reports
class TestProfitReport:
    """测试利润报表功能"""

    @pytest.mark.asyncio
    async def test_get_profit_report_success(self, reports_service, mock_db):
        """测试成功获取利润报表"""
        # 模拟消耗查询
        spend_result = Mock()
        spend_result.project_id = 1
        spend_result.project_name = "Project A"
        spend_result.ad_spend = 8000.00

        spend_query = Mock()
        spend_query.select_from.return_value = spend_query
        spend_query.join.return_value = spend_query
        spend_query.filter.return_value = spend_query
        spend_query.group_by.return_value = spend_query
        spend_query.all.return_value = [spend_result]

        # 模拟充值查询
        topup_result = Mock()
        topup_result.project_id = 1
        topup_result.topup_amount = 10000.00

        topup_query = Mock()
        topup_query.select_from.return_value = topup_query
        topup_query.join.return_value = topup_query
        topup_query.filter.return_value = topup_query
        topup_query.group_by.return_value = topup_query
        topup_query.all.return_value = [topup_result]

        # 交替返回 spend 和 topup 查询
        mock_db.query.side_effect = [spend_query, topup_query]

        result = await reports_service.get_profit_report(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31)
        )

        assert isinstance(result, ProfitReportResponse)
        assert len(result.items) == 1
        assert result.items[0].project_name == "Project A"
        assert result.items[0].profit == Decimal("2000.00")
        assert result.summary['project_count'] == 1

    @pytest.mark.asyncio
    async def test_get_profit_report_with_project_filter(self, reports_service, mock_db):
        """测试带项目过滤的利润报表"""
        spend_query = Mock()
        spend_query.select_from.return_value = spend_query
        spend_query.join.return_value = spend_query
        spend_query.filter.return_value = spend_query
        spend_query.group_by.return_value = spend_query
        spend_query.all.return_value = []

        topup_query = Mock()
        topup_query.select_from.return_value = topup_query
        topup_query.join.return_value = topup_query
        topup_query.filter.return_value = topup_query
        topup_query.group_by.return_value = topup_query
        topup_query.all.return_value = []

        mock_db.query.side_effect = [spend_query, topup_query]

        result = await reports_service.get_profit_report(
            project_ids=[1, 2]
        )

        assert isinstance(result, ProfitReportResponse)
        # 验证 filter 被调用（包含 project_ids 过滤）
        assert spend_query.filter.call_count >= 1

    @pytest.mark.asyncio
    async def test_get_profit_report_sorting(self, reports_service, mock_db):
        """测试利润报表按利润降序排序"""
        spend_result1 = Mock()
        spend_result1.project_id = 1
        spend_result1.project_name = "Low Profit"
        spend_result1.ad_spend = 9000.00

        spend_result2 = Mock()
        spend_result2.project_id = 2
        spend_result2.project_name = "High Profit"
        spend_result2.ad_spend = 5000.00

        spend_query = Mock()
        spend_query.select_from.return_value = spend_query
        spend_query.join.return_value = spend_query
        spend_query.filter.return_value = spend_query
        spend_query.group_by.return_value = spend_query
        spend_query.all.return_value = [spend_result1, spend_result2]

        topup_result1 = Mock()
        topup_result1.project_id = 1
        topup_result1.topup_amount = 10000.00

        topup_result2 = Mock()
        topup_result2.project_id = 2
        topup_result2.topup_amount = 10000.00

        topup_query = Mock()
        topup_query.select_from.return_value = topup_query
        topup_query.join.return_value = topup_query
        topup_query.filter.return_value = topup_query
        topup_query.group_by.return_value = topup_query
        topup_query.all.return_value = [topup_result1, topup_result2]

        mock_db.query.side_effect = [spend_query, topup_query]

        result = await reports_service.get_profit_report()

        # 验证按利润降序排序（High Profit 应在前）
        assert result.items[0].project_name == "High Profit"
        assert result.items[1].project_name == "Low Profit"


# ==================== 对账报表测试 ====================

@pytest.mark.unit
@pytest.mark.reports
class TestReconciliationReport:
    """测试对账报表功能"""

    @pytest.mark.asyncio
    async def test_get_reconciliation_report_success(self, reports_service, mock_db):
        """测试成功获取对账报表"""
        # 模拟各状态批次
        draft = Mock()
        draft.status = 'draft'
        draft.count = 2
        draft.system_spend = 5000.00
        draft.actual_spend = 5100.00
        draft.discrepancy = 100.00

        completed = Mock()
        completed.status = 'completed'
        completed.count = 8
        completed.system_spend = 40000.00
        completed.actual_spend = 39900.00
        completed.discrepancy = -100.00

        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = [draft, completed]
        mock_db.query.return_value = mock_query

        result = await reports_service.get_reconciliation_report(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31)
        )

        assert isinstance(result, ReconciliationReportResponse)
        assert len(result.items) == 1
        assert result.items[0].total_batches == 10
        assert result.items[0].completed_batches == 8
        assert result.items[0].completion_rate == 80.0

    @pytest.mark.asyncio
    async def test_get_reconciliation_report_empty(self, reports_service, mock_db):
        """测试空对账报表"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = []
        mock_db.query.return_value = mock_query

        result = await reports_service.get_reconciliation_report()

        assert isinstance(result, ReconciliationReportResponse)
        assert result.items[0].total_batches == 0
        assert result.items[0].completion_rate == 0


# ==================== 财务摘要测试 ====================

@pytest.mark.unit
@pytest.mark.reports
class TestFinancialSummary:
    """测试财务摘要功能"""

    @pytest.mark.asyncio
    async def test_get_financial_summary_success(self, reports_service, mock_db):
        """测试成功获取财务摘要"""
        # 模拟账户查询
        account = Mock()
        account.account_id = 101
        account.account_name = "Account A"
        account.current_balance = 5000.00
        account.project_id = 1
        account.project_name = "Project A"
        account.channel_id = 1
        account.channel_name = "Channel A"

        account_query = Mock()
        account_query.select_from.return_value = account_query
        account_query.join.return_value = account_query
        account_query.filter.return_value = account_query
        account_query.all.return_value = [account]

        # 模拟账本查询
        from backend.models.enums import LedgerEntryType
        ledger_topup = Mock()
        ledger_topup.entry_type = LedgerEntryType.TOPUP.value  # 使用枚举值
        ledger_topup.total = 10000.00

        ledger_cost = Mock()
        ledger_cost.entry_type = LedgerEntryType.COST.value  # 使用枚举值
        ledger_cost.total = -4000.00

        ledger_query = Mock()
        ledger_query.filter.return_value = ledger_query
        ledger_query.group_by.return_value = ledger_query
        ledger_query.all.return_value = [ledger_topup, ledger_cost]

        mock_db.query.side_effect = [account_query, ledger_query]

        result = await reports_service.get_financial_summary(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31)
        )

        assert isinstance(result, FinancialSummaryResponse)
        assert len(result.items) == 1
        assert result.items[0].account_name == "Account A"
        assert result.items[0].total_topup == Decimal("10000.00")
        assert result.summary['total_accounts'] == 1

    @pytest.mark.asyncio
    async def test_get_financial_summary_with_project_filter(self, reports_service, mock_db):
        """测试带项目过滤的财务摘要"""
        account_query = Mock()
        account_query.select_from.return_value = account_query
        account_query.join.return_value = account_query
        account_query.filter.return_value = account_query
        account_query.all.return_value = []

        mock_db.query.return_value = account_query

        result = await reports_service.get_financial_summary(
            project_ids=[1]
        )

        assert isinstance(result, FinancialSummaryResponse)
        # 验证 filter 被调用
        assert account_query.filter.call_count >= 1


# ==================== 仪表盘摘要测试 ====================

@pytest.mark.unit
@pytest.mark.reports
class TestDashboardSummary:
    """测试仪表盘摘要功能"""

    @pytest.mark.asyncio
    async def test_get_dashboard_summary_success(self, reports_service, mock_db):
        """测试成功获取仪表盘摘要"""
        # 模拟各种查询结果
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = 1000.00
        mock_query.all.return_value = []
        mock_db.query.return_value = mock_query

        result = await reports_service.get_dashboard_summary()

        assert isinstance(result, DashboardSummary)
        assert result.today_spend >= Decimal("0.00")
        assert result.month_spend >= Decimal("0.00")
        assert result.total_accounts >= 0
        assert result.total_projects >= 0
        assert len(result.spend_trend) == 7
        assert len(result.leads_trend) == 7

    @pytest.mark.asyncio
    async def test_get_dashboard_summary_profit_calculation(self, reports_service, mock_db):
        """测试仪表盘利润计算"""
        # 创建多个查询Mock，因为 get_dashboard_summary 有多个查询
        def create_query_mock(scalar_value=0):
            query = Mock()
            query.filter.return_value = query
            query.scalar.return_value = scalar_value
            query.all.return_value = []
            return query

        # 计算需要的查询次数：
        # 今日: spend, leads, topup (3个)
        # 本月: spend, leads, topup (3个)
        # 账户统计: total, active, low_balance (3个)
        # 项目统计: total, active (2个)
        # 待办: topups, reconciliations, reports (3个)
        # 趋势: 7天 spend + 7天 leads (14个)
        # 总计: 3 + 3 + 3 + 2 + 3 + 14 = 28个查询
        
        # 创建查询Mock序列
        query_mocks = []
        # 今日数据
        query_mocks.append(create_query_mock(5000.00))  # today_spend
        query_mocks.append(create_query_mock(100))       # today_leads
        query_mocks.append(create_query_mock(6000.00))   # today_topup
        # 本月数据
        query_mocks.append(create_query_mock(20000.00))  # month_spend
        query_mocks.append(create_query_mock(500))       # month_leads
        query_mocks.append(create_query_mock(25000.00))  # month_topup
        # 账户统计
        query_mocks.append(create_query_mock(10))        # total_accounts
        query_mocks.append(create_query_mock(8))         # active_accounts
        query_mocks.append(create_query_mock(2))         # low_balance_accounts
        # 项目统计
        query_mocks.append(create_query_mock(5))         # total_projects
        query_mocks.append(create_query_mock(4))         # active_projects
        # 待办事项
        query_mocks.append(create_query_mock(3))         # pending_topups
        query_mocks.append(create_query_mock(2))         # pending_reconciliations
        query_mocks.append(create_query_mock(5))         # pending_reports
        # 趋势数据（14个查询：7天spend + 7天leads）
        for _ in range(14):
            query_mocks.append(create_query_mock(0))
        
        mock_db.query.side_effect = query_mocks

        result = await reports_service.get_dashboard_summary()

        # 验证利润计算：topup - spend
        assert result.month_profit == Decimal("25000.00") - Decimal("20000.00")

    @pytest.mark.asyncio
    async def test_get_dashboard_summary_trend_data(self, reports_service, mock_db):
        """测试仪表盘趋势数据"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = 100.00
        mock_query.all.return_value = []
        mock_db.query.return_value = mock_query

        result = await reports_service.get_dashboard_summary()

        # 验证趋势数据格式
        assert len(result.spend_trend) == 7
        assert all('date' in item and 'value' in item for item in result.spend_trend)
        assert len(result.leads_trend) == 7
        assert all('date' in item and 'value' in item for item in result.leads_trend)


# ==================== 趋势报表测试 ====================

@pytest.mark.unit
@pytest.mark.reports
class TestTrendReport:
    """测试趋势报表功能"""

    @pytest.mark.asyncio
    async def test_get_trend_report_spend(self, reports_service, mock_db):
        """测试消耗趋势报表"""
        result1 = Mock()
        result1.date = date(2024, 1, 1)
        result1.value = 1000.00

        result2 = Mock()
        result2.date = date(2024, 1, 2)
        result2.value = 1500.00

        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [result1, result2]
        mock_db.query.return_value = mock_query

        result = await reports_service.get_trend_report(
            metric="spend",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31)
        )

        assert isinstance(result, TrendReportResponse)
        assert len(result.data_points) == 2
        assert result.summary['count'] == 2
        assert Decimal(result.summary['total']) == Decimal("2500.00")

    @pytest.mark.asyncio
    async def test_get_trend_report_leads(self, reports_service, mock_db):
        """测试线索趋势报表"""
        result1 = Mock()
        result1.date = date(2024, 1, 1)
        result1.value = 50

        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [result1]
        mock_db.query.return_value = mock_query

        result = await reports_service.get_trend_report(
            metric="leads",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31)
        )

        assert isinstance(result, TrendReportResponse)
        assert len(result.data_points) == 1

    @pytest.mark.asyncio
    async def test_get_trend_report_topup(self, reports_service, mock_db):
        """测试充值趋势报表"""
        result1 = Mock()
        result1.date = date(2024, 1, 1)
        result1.value = 5000.00

        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [result1]
        mock_db.query.return_value = mock_query

        result = await reports_service.get_trend_report(
            metric="topup",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31)
        )

        assert isinstance(result, TrendReportResponse)
        assert len(result.data_points) == 1

    @pytest.mark.asyncio
    async def test_get_trend_report_empty_data(self, reports_service, mock_db):
        """测试空数据趋势报表"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []
        mock_db.query.return_value = mock_query

        result = await reports_service.get_trend_report(
            metric="spend"
        )

        assert isinstance(result, TrendReportResponse)
        assert len(result.data_points) == 0
        assert Decimal(result.summary['total']) == Decimal("0.00")
        assert Decimal(result.summary['average']) == Decimal("0.00")

    @pytest.mark.asyncio
    async def test_get_trend_report_summary_calculations(self, reports_service, mock_db):
        """测试趋势报表汇总计算"""
        result1 = Mock()
        result1.date = date(2024, 1, 1)
        result1.value = 1000.00

        result2 = Mock()
        result2.date = date(2024, 1, 2)
        result2.value = 2000.00

        result3 = Mock()
        result3.date = date(2024, 1, 3)
        result3.value = 1500.00

        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [result1, result2, result3]
        mock_db.query.return_value = mock_query

        result = await reports_service.get_trend_report(metric="spend")

        # 验证汇总计算
        assert Decimal(result.summary['total']) == Decimal("4500.00")
        assert Decimal(result.summary['average']) == Decimal("1500.00")
        assert Decimal(result.summary['max']) == Decimal("2000.00")
        assert Decimal(result.summary['min']) == Decimal("1000.00")


# ==================== 边界情况测试 ====================

@pytest.mark.unit
@pytest.mark.reports
class TestReportsServiceEdgeCases:
    """测试报表服务边界情况"""

    @pytest.mark.asyncio
    async def test_performance_report_null_values(self, reports_service, mock_db):
        """测试效果报表空值处理"""
        result = Mock()
        result.project_id = 1
        result.project_name = "Test"
        result.channel_id = 1
        result.channel_name = "Channel"
        result.total_spend = None
        result.total_leads = None

        mock_query = Mock()
        mock_query.select_from.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = [result]
        mock_db.query.return_value = mock_query

        response = await reports_service.get_performance_report()

        assert response.items[0].total_spend == Decimal("0.00")
        assert response.items[0].total_leads == 0

    @pytest.mark.asyncio
    async def test_financial_summary_zero_balance(self, reports_service, mock_db):
        """测试财务摘要零余额处理"""
        account = Mock()
        account.account_id = 101
        account.account_name = "Account A"
        account.current_balance = None
        account.project_id = 1
        account.project_name = "Project A"
        account.channel_id = 1
        account.channel_name = "Channel A"

        account_query = Mock()
        account_query.select_from.return_value = account_query
        account_query.join.return_value = account_query
        account_query.filter.return_value = account_query
        account_query.all.return_value = [account]

        ledger_query = Mock()
        ledger_query.filter.return_value = ledger_query
        ledger_query.group_by.return_value = ledger_query
        ledger_query.all.return_value = []

        mock_db.query.side_effect = [account_query, ledger_query]

        result = await reports_service.get_financial_summary()

        assert result.items[0].current_balance == Decimal("0.00")


# ==================== 集成测试 ====================

@pytest.mark.integration
@pytest.mark.reports
class TestReportsServiceIntegration:
    """报表服务集成测试"""

    @pytest.mark.asyncio
    async def test_full_reporting_workflow(self, reports_service, mock_db):
        """测试完整报表生成工作流"""
        mock_query = Mock()
        mock_query.select_from.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []
        mock_query.scalar.return_value = 0
        mock_db.query.return_value = mock_query

        # 获取多种报表
        performance = await reports_service.get_performance_report()
        profit = await reports_service.get_profit_report()
        dashboard = await reports_service.get_dashboard_summary()

        assert isinstance(performance, PerformanceReportResponse)
        assert isinstance(profit, ProfitReportResponse)
        assert isinstance(dashboard, DashboardSummary)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
