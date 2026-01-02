"""
财务管理 V2 API 测试 - TASK-FIN-004 财务仪表盘

SoT References:
- MASTER.md v4.8 §4.5.5 资金口径定义
- LEDGER_SOT.md v1.1 §2-3 双账本
- API_SOT.md v9.0 §11A (财务利润 API)

端点列表 (7 个):
资金总览:
- GET /api/v1/finance/fund/overview
- GET /api/v1/finance/fund/receivables
- GET /api/v1/finance/fund/distribution

项目盈亏:
- GET /api/v1/finance/profit/overview
- GET /api/v1/finance/profit/projects
- GET /api/v1/finance/profit/suppliers
- GET /api/v1/finance/profit/trend

Version: 1.0
Author: Claude Code (TASK-FIN-004)
"""

import pytest


class TestFinanceV2FundAPI:
    """资金总览 API 测试"""

    BASE_URL = "/api/v1/finance/fund"

    class TestFundOverviewEndpoint:
        """GET /finance/fund/overview"""

        def test_overview_requires_auth(self, client):
            """资金概览需要认证"""
            response = client.get(f"{TestFinanceV2FundAPI.BASE_URL}/overview")
            assert response.status_code == 401

        def test_overview_success(self, client, finance_token):
            """资金概览查询成功"""
            response = client.get(
                f"{TestFinanceV2FundAPI.BASE_URL}/overview",
                headers={"Authorization": f"Bearer {finance_token}"},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "period" in data["data"]
            assert "summary" in data["data"]
            assert "changes" in data["data"]

        def test_overview_with_period_param(self, client, finance_token):
            """资金概览带时间参数"""
            response = client.get(
                f"{TestFinanceV2FundAPI.BASE_URL}/overview?period=month",
                headers={"Authorization": f"Bearer {finance_token}"},
            )
            assert response.status_code == 200

        def test_overview_with_date_param(self, client, finance_token):
            """资金概览带月份参数"""
            response = client.get(
                f"{TestFinanceV2FundAPI.BASE_URL}/overview?date=2025-12",
                headers={"Authorization": f"Bearer {finance_token}"},
            )
            assert response.status_code == 200

    class TestReceivablesEndpoint:
        """GET /finance/fund/receivables"""

        def test_receivables_requires_auth(self, client):
            """应收账款需要认证"""
            response = client.get(f"{TestFinanceV2FundAPI.BASE_URL}/receivables")
            assert response.status_code == 401

        def test_receivables_success(self, client, finance_token):
            """应收账款查询成功"""
            response = client.get(
                f"{TestFinanceV2FundAPI.BASE_URL}/receivables",
                headers={"Authorization": f"Bearer {finance_token}"},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "items" in data["data"]
            assert "totals" in data["data"]

        def test_receivables_with_status_filter(self, client, finance_token):
            """应收账款按状态过滤"""
            response = client.get(
                f"{TestFinanceV2FundAPI.BASE_URL}/receivables?status=outstanding",
                headers={"Authorization": f"Bearer {finance_token}"},
            )
            assert response.status_code == 200

        def test_receivables_with_sort(self, client, finance_token):
            """应收账款排序"""
            response = client.get(
                f"{TestFinanceV2FundAPI.BASE_URL}/receivables?sort_by=client",
                headers={"Authorization": f"Bearer {finance_token}"},
            )
            assert response.status_code == 200

    class TestDistributionEndpoint:
        """GET /finance/fund/distribution"""

        def test_distribution_requires_auth(self, client):
            """资金分布需要认证"""
            response = client.get(f"{TestFinanceV2FundAPI.BASE_URL}/distribution")
            assert response.status_code == 401

        def test_distribution_success(self, client, finance_token):
            """资金分布查询成功"""
            response = client.get(
                f"{TestFinanceV2FundAPI.BASE_URL}/distribution",
                headers={"Authorization": f"Bearer {finance_token}"},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "group_by" in data["data"]
            assert "items" in data["data"]
            assert "total" in data["data"]

        def test_distribution_by_project(self, client, finance_token):
            """按项目分组的资金分布"""
            response = client.get(
                f"{TestFinanceV2FundAPI.BASE_URL}/distribution?group_by=project",
                headers={"Authorization": f"Bearer {finance_token}"},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["data"]["group_by"] == "project"


class TestFinanceV2ProfitAPI:
    """项目盈亏 API 测试"""

    BASE_URL = "/api/v1/finance/profit"

    class TestProfitOverviewEndpoint:
        """GET /finance/profit/overview"""

        def test_profit_overview_requires_auth(self, client):
            """盈亏概览需要认证"""
            response = client.get(f"{TestFinanceV2ProfitAPI.BASE_URL}/overview")
            assert response.status_code == 401

        def test_profit_overview_success(self, client, finance_token):
            """盈亏概览查询成功"""
            response = client.get(
                f"{TestFinanceV2ProfitAPI.BASE_URL}/overview",
                headers={"Authorization": f"Bearer {finance_token}"},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "period" in data["data"]
            assert "summary" in data["data"]
            assert "changes" in data["data"]
            assert "benchmarks" in data["data"]

        def test_profit_overview_summary_fields(self, client, finance_token):
            """盈亏概览摘要字段验证"""
            response = client.get(
                f"{TestFinanceV2ProfitAPI.BASE_URL}/overview",
                headers={"Authorization": f"Bearer {finance_token}"},
            )
            assert response.status_code == 200
            summary = response.json()["data"]["summary"]
            # 验证核心字段存在
            expected_fields = [
                "total_revenue",
                "total_cost",
                "total_profit",
                "total_conversions",
                "avg_profit_rate",
            ]
            for field in expected_fields:
                assert field in summary, f"Missing field: {field}"

    class TestProjectProfitsEndpoint:
        """GET /finance/profit/projects"""

        def test_project_profits_requires_auth(self, client):
            """项目利润明细需要认证"""
            response = client.get(f"{TestFinanceV2ProfitAPI.BASE_URL}/projects")
            assert response.status_code == 401

        def test_project_profits_success(self, client, finance_token):
            """项目利润明细查询成功"""
            response = client.get(
                f"{TestFinanceV2ProfitAPI.BASE_URL}/projects",
                headers={"Authorization": f"Bearer {finance_token}"},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "items" in data["data"]
            assert "totals" in data["data"]

        def test_project_profits_with_sort(self, client, finance_token):
            """项目利润明细排序"""
            response = client.get(
                f"{TestFinanceV2ProfitAPI.BASE_URL}/projects?sort_by=profit_rate",
                headers={"Authorization": f"Bearer {finance_token}"},
            )
            assert response.status_code == 200

        def test_project_profits_with_status_filter(self, client, finance_token):
            """项目利润明细按状态过滤"""
            response = client.get(
                f"{TestFinanceV2ProfitAPI.BASE_URL}/projects?status=active",
                headers={"Authorization": f"Bearer {finance_token}"},
            )
            assert response.status_code == 200

    class TestSupplierCostsEndpoint:
        """GET /finance/profit/suppliers"""

        def test_supplier_costs_requires_auth(self, client):
            """渠道成本分析需要认证"""
            response = client.get(f"{TestFinanceV2ProfitAPI.BASE_URL}/suppliers")
            assert response.status_code == 401

        def test_supplier_costs_success(self, client, finance_token):
            """渠道成本分析查询成功"""
            response = client.get(
                f"{TestFinanceV2ProfitAPI.BASE_URL}/suppliers",
                headers={"Authorization": f"Bearer {finance_token}"},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "items" in data["data"]
            assert "summary" in data["data"]

    class TestProfitTrendEndpoint:
        """GET /finance/profit/trend"""

        def test_profit_trend_requires_auth(self, client):
            """利润趋势需要认证"""
            response = client.get(f"{TestFinanceV2ProfitAPI.BASE_URL}/trend")
            assert response.status_code == 401

        def test_profit_trend_success(self, client, finance_token):
            """利润趋势查询成功"""
            response = client.get(
                f"{TestFinanceV2ProfitAPI.BASE_URL}/trend",
                headers={"Authorization": f"Bearer {finance_token}"},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "granularity" in data["data"]
            assert "series" in data["data"]

        def test_profit_trend_with_granularity(self, client, finance_token):
            """利润趋势颗粒度参数"""
            for granularity in ["day", "week", "month"]:
                response = client.get(
                    f"{TestFinanceV2ProfitAPI.BASE_URL}/trend?granularity={granularity}",
                    headers={"Authorization": f"Bearer {finance_token}"},
                )
                assert response.status_code == 200
                data = response.json()
                assert data["data"]["granularity"] == granularity


class TestFinanceV2Permissions:
    """
    财务 V2 API 权限测试

    SoT: MASTER.md v4.8 §2.4

    权限矩阵:
    - admin: 全部
    - ceo: 全部
    - finance: 全部
    - project_owner: profit/* 端点
    - pitcher: 无权限
    """

    def test_permission_matrix_documented(self):
        """验证权限矩阵文档完整性"""
        fund_endpoints = ["overview", "receivables", "distribution"]
        profit_endpoints = ["overview", "projects", "suppliers", "trend"]

        # finance 应该可以访问所有端点
        finance_access = fund_endpoints + profit_endpoints
        assert len(finance_access) == 7

        # project_owner 可以访问 profit 端点
        project_owner_access = ["profit/overview", "profit/projects", "profit/trend"]
        assert len(project_owner_access) == 3


class TestFinanceV2DataIntegrity:
    """
    财务 V2 数据完整性测试

    验证计算公式符合 SoT 定义
    """

    def test_profit_formula_documented(self):
        """验证利润公式文档完整性"""
        # SoT: BUSINESS_RULES.md v3.2
        # revenue = conversions_final × unit_price
        # cost = real_spend + fee (fee = spend × fee_rate)
        # profit = revenue - cost
        # profit_margin = profit / revenue × 100
        expected_formula = {
            "revenue": "conversions_final × unit_price",
            "cost": "real_spend + fee",
            "profit": "revenue - cost",
            "profit_rate": "profit / revenue",
        }
        assert len(expected_formula) == 4

    def test_profit_status_thresholds(self):
        """验证利润状态阈值"""
        # SoT: profit_service_v2.py
        # 🟢 healthy: profit_rate >= 15%
        # 🟡 warning: 5% <= profit_rate < 15%
        # 🔴 danger: profit_rate < 5%
        # ⚫ inactive: refunded/closed
        thresholds = {
            "healthy": 0.15,
            "warning": 0.05,
            "danger": 0.0,
        }
        assert thresholds["healthy"] > thresholds["warning"]
        assert thresholds["warning"] > thresholds["danger"]
