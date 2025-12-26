"""
Dashboard 模块单元测试

测试 schemas, service, router 的基本功能
"""

import pytest
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

# ============ Schema Tests ============

class TestDashboardSchemas:
    """Dashboard Schema 测试"""

    def test_kpi_data_defaults(self):
        """测试 KpiData 默认值"""
        from backend.schemas.dashboard import KpiData

        kpi = KpiData()
        assert kpi.total_spend == Decimal("0.00")
        assert kpi.total_conversions == 0
        assert kpi.total_follows == 0
        assert kpi.avg_cpl is None
        assert kpi.roi is None

    def test_kpi_data_with_values(self):
        """测试 KpiData 赋值"""
        from backend.schemas.dashboard import KpiData

        kpi = KpiData(
            total_spend=Decimal("1000.50"),
            total_conversions=100,
            total_follows=50,
            avg_cpl=Decimal("20.01"),
            roi=1.5,
            spend_change=10.5
        )
        assert kpi.total_spend == Decimal("1000.50")
        assert kpi.total_conversions == 100
        assert kpi.avg_cpl == Decimal("20.01")
        assert kpi.spend_change == 10.5

    def test_trend_item(self):
        """测试 TrendItem"""
        from backend.schemas.dashboard import TrendItem

        item = TrendItem(
            report_date=date(2024, 1, 15),
            spend=Decimal("500.00"),
            conversions=25,
            follows=10,
            cpl=Decimal("50.00")
        )
        assert item.report_date == date(2024, 1, 15)
        assert item.spend == Decimal("500.00")
        assert item.follows == 10

    def test_project_ranking_item(self):
        """测试 ProjectRankingItem"""
        from backend.schemas.dashboard import ProjectRankingItem

        item = ProjectRankingItem(
            project_id=1,
            project_name="Test Project",
            total_spend=Decimal("10000.00"),
            total_follows=500,
            cost_per_follow=Decimal("20.00"),
            roas=1.5,
            rank=1
        )
        assert item.project_id == 1
        assert item.project_name == "Test Project"
        assert item.rank == 1

    def test_todo_item(self):
        """测试 TodoItem"""
        from backend.schemas.dashboard import TodoItem

        item = TodoItem(
            type="pending_report",
            label="待审核日报",
            count=5,
            priority="high"
        )
        assert item.type == "pending_report"
        assert item.count == 5
        assert item.priority == "high"

    def test_dashboard_summary(self):
        """测试 DashboardSummary"""
        from backend.schemas.dashboard import DashboardSummary, KpiData

        kpi = KpiData(total_spend=Decimal("5000.00"))
        summary = DashboardSummary(
            period="2024-01",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            total_projects=10,
            active_projects=8,
            suspended_projects=2,
            kpi=kpi,
            pending_reports=3,
            pending_topups=1
        )
        assert summary.total_projects == 10
        assert summary.active_projects == 8
        assert summary.kpi.total_spend == Decimal("5000.00")


# ============ Service Tests ============

class TestDashboardService:
    """Dashboard Service 测试"""

    def test_parse_period_default(self):
        """测试 parse_period 默认周期"""
        from backend.services.dashboard_service import DashboardService

        # Mock db session
        mock_db = MagicMock()
        service = DashboardService(mock_db)

        start, end, period_str = service.parse_period(None)

        # 应该返回当前月份
        today = date.today()
        assert start.year == today.year
        assert start.month == today.month
        assert start.day == 1

    def test_parse_period_with_value(self):
        """测试 parse_period 指定周期"""
        from backend.services.dashboard_service import DashboardService

        mock_db = MagicMock()
        service = DashboardService(mock_db)

        start, end, period_str = service.parse_period("2024-06")

        assert start == date(2024, 6, 1)
        assert end == date(2024, 6, 30)
        assert period_str == "2024-06"

    def test_parse_period_december(self):
        """测试 parse_period 12月份边界"""
        from backend.services.dashboard_service import DashboardService

        mock_db = MagicMock()
        service = DashboardService(mock_db)

        start, end, period_str = service.parse_period("2024-12")

        assert start == date(2024, 12, 1)
        assert end == date(2024, 12, 31)


# ============ Router Tests ============

class TestDashboardRouter:
    """Dashboard Router 测试"""

    def test_router_exists(self):
        """测试 Router 存在"""
        from backend.routers.dashboard import router

        assert router is not None
        assert router.prefix == "/dashboards"

    def test_router_has_kpi_endpoint(self):
        """测试 /kpi 端点存在"""
        from backend.routers.dashboard import router

        routes = [r.path for r in router.routes]
        assert any("/kpi" in r for r in routes)

    def test_router_has_trend_endpoint(self):
        """测试 /trend 端点存在"""
        from backend.routers.dashboard import router

        routes = [r.path for r in router.routes]
        assert any("/trend" in r for r in routes)

    def test_router_has_ranking_endpoint(self):
        """测试 /ranking 端点存在"""
        from backend.routers.dashboard import router

        routes = [r.path for r in router.routes]
        assert any("/ranking" in r for r in routes)

    def test_router_has_todos_endpoint(self):
        """测试 /todos 端点存在"""
        from backend.routers.dashboard import router

        routes = [r.path for r in router.routes]
        assert any("/todos" in r for r in routes)

    def test_router_has_ceo_endpoints(self):
        """测试 CEO 端点存在 (向后兼容)"""
        from backend.routers.dashboard import router

        routes = [r.path for r in router.routes]
        assert any("/ceo/summary" in r for r in routes)
        assert any("/ceo/detail" in r for r in routes)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
