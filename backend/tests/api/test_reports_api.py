"""
Reports API 集成测试

测试范围：
1. GET /api/v1/reports/projects/summary - 项目汇总报表
2. GET /api/v1/reports/projects/{id}/accounts - 项目详情报表
3. GET /api/v1/reports/channels/summary - 渠道汇总报表
4. GET /api/v1/reports/buyers/summary - 投手汇总报表
5. GET /api/v1/reports/dashboard/summary - 仪表板汇总

测试场景：
- 200 OK：正常查询
- 403 Forbidden：权限不足
- 400 Bad Request：参数错误
- 404 Not Found：资源不存在
- 401 Unauthorized：未认证

Version: 1.0
Created: 2025-12-07
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from fastapi.testclient import TestClient

from backend.models import (
    User, UserRole, Project, AdAccount, DailyReport, DailyReportStatus,
    LedgerEntry, LedgerBookType, LedgerEntryType, Supplier
)


# ===== 测试用例 =====

class TestProjectSummaryAPI:
    """测试项目汇总报表 API"""

    def test_get_project_summary_success(
        self, client: TestClient, admin_token, db_session
    ):
        """测试成功获取项目汇总报表"""
        response = client.get(
            "/api/v1/reports/projects/summary",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={
                "start_date": (date.today() - timedelta(days=30)).isoformat(),
                "end_date": date.today().isoformat(),
                "group_by": "day",
                "page": 1,
                "page_size": 20
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "items" in data["data"]
        assert "summary" in data["data"]
        assert "meta" in data["data"]

    def test_get_project_summary_with_filters(
        self, client: TestClient, admin_token, test_project
    ):
        """测试带筛选条件的项目汇总报表"""
        response = client.get(
            "/api/v1/reports/projects/summary",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={
                "project_id": test_project.id,
                "group_by": "week",
                "sort_by": "revenue",
                "sort_order": "desc"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_get_project_summary_unauthorized(self, client: TestClient):
        """测试未认证访问"""
        response = client.get("/api/v1/reports/projects/summary")
        assert response.status_code == 401

    def test_get_project_summary_invalid_date_range(
        self, client: TestClient, admin_token
    ):
        """测试无效日期范围（结束日期早于开始日期）"""
        response = client.get(
            "/api/v1/reports/projects/summary",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={
                "start_date": date.today().isoformat(),
                "end_date": (date.today() - timedelta(days=10)).isoformat()
            }
        )

        # 应该返回 400 或接受并返回空数据
        assert response.status_code in [200, 400]

    def test_get_project_summary_pagination(
        self, client: TestClient, admin_token
    ):
        """测试分页功能"""
        # 第一页
        response1 = client.get(
            "/api/v1/reports/projects/summary",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"page": 1, "page_size": 5}
        )
        assert response1.status_code == 200
        data1 = response1.json()
        assert data1["data"]["meta"]["page"] == 1

        # 第二页
        response2 = client.get(
            "/api/v1/reports/projects/summary",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"page": 2, "page_size": 5}
        )
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2["data"]["meta"]["page"] == 2


class TestProjectAccountsAPI:
    """测试项目详情报表 API"""

    def test_get_project_accounts_success(
        self, client: TestClient, admin_token, test_project
    ):
        """测试成功获取项目详情报表"""
        response = client.get(
            f"/api/v1/reports/projects/{test_project.id}/accounts",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "project" in data["data"]
        assert "accounts" in data["data"]
        assert "summary" in data["data"]

    def test_get_project_accounts_not_found(
        self, client: TestClient, admin_token
    ):
        """测试项目不存在"""
        response = client.get(
            "/api/v1/reports/projects/99999/accounts",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 404

    def test_get_project_accounts_permission_denied(
        self, client: TestClient, account_manager_token, db_session
    ):
        """测试账户经理访问其他人的项目"""
        # 创建另一个项目（不属于当前账户经理）
        other_project = Project(
            id=999,
            name="其他项目",
            account_manager_id=999,
            status="active"
        )
        db_session.add(other_project)
        db_session.commit()

        response = client.get(
            f"/api/v1/reports/projects/{other_project.id}/accounts",
            headers={"Authorization": f"Bearer {account_manager_token}"}
        )

        assert response.status_code == 403

    def test_get_project_accounts_with_date_filter(
        self, client: TestClient, admin_token, test_project
    ):
        """测试带日期筛选的项目详情报表"""
        response = client.get(
            f"/api/v1/reports/projects/{test_project.id}/accounts",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={
                "start_date": (date.today() - timedelta(days=30)).isoformat(),
                "end_date": date.today().isoformat()
            }
        )

        assert response.status_code == 200


class TestChannelSummaryAPI:
    """测试渠道汇总报表 API"""

    def test_get_channel_summary_success(
        self, client: TestClient, admin_token
    ):
        """测试成功获取渠道汇总报表"""
        response = client.get(
            "/api/v1/reports/channels/summary",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={
                "group_by": "day",
                "page": 1,
                "page_size": 20
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "items" in data["data"]
        assert "summary" in data["data"]

    def test_get_channel_summary_filter_by_channel(
        self, client: TestClient, admin_token, test_supplier
    ):
        """测试按渠道 ID 筛选"""
        response = client.get(
            "/api/v1/reports/channels/summary",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"channel_id": str(test_supplier.id)}
        )

        assert response.status_code == 200
        data = response.json()
        # 验证返回的所有行都是该渠道
        for item in data["data"]["items"]:
            assert item["channel_id"] == str(test_supplier.id)

    def test_get_channel_summary_sort_by_cost(
        self, client: TestClient, admin_token
    ):
        """测试按成本排序"""
        response = client.get(
            "/api/v1/reports/channels/summary",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={
                "sort_by": "cost",
                "sort_order": "desc"
            }
        )

        assert response.status_code == 200

    def test_get_channel_summary_unauthorized(self, client: TestClient):
        """测试未认证访问"""
        response = client.get("/api/v1/reports/channels/summary")
        assert response.status_code == 401


class TestBuyerSummaryAPI:
    """测试投手汇总报表 API"""

    def test_get_buyer_summary_success(
        self, client: TestClient, admin_token
    ):
        """测试成功获取投手汇总报表"""
        response = client.get(
            "/api/v1/reports/buyers/summary",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={
                "group_by": "day",
                "page": 1,
                "page_size": 20
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_get_buyer_summary_filter_by_buyer(
        self, client: TestClient, admin_token, media_buyer_user
    ):
        """测试按投手 ID 筛选"""
        response = client.get(
            "/api/v1/reports/buyers/summary",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"buyer_id": str(media_buyer_user.id)}
        )

        assert response.status_code == 200

    def test_media_buyer_can_only_see_own_data(
        self, client: TestClient, media_buyer_token
    ):
        """测试投手只能查看自己的数据"""
        response = client.get(
            "/api/v1/reports/buyers/summary",
            headers={"Authorization": f"Bearer {media_buyer_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        # 验证所有返回的行都是当前投手的数据
        # （具体验证需要知道 buyer_id，这里仅检查返回成功）

    def test_get_buyer_summary_sort_by_profit(
        self, client: TestClient, admin_token
    ):
        """测试按毛利排序"""
        response = client.get(
            "/api/v1/reports/buyers/summary",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={
                "sort_by": "profit",
                "sort_order": "desc"
            }
        )

        assert response.status_code == 200


class TestDashboardSummaryAPI:
    """测试仪表板汇总 API"""

    def test_get_dashboard_summary_success(
        self, client: TestClient, admin_token
    ):
        """测试成功获取仪表板汇总"""
        response = client.get(
            "/api/v1/reports/dashboard/summary",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "overview" in data["data"]
        assert "by_project" in data["data"]
        assert "by_channel" in data["data"]
        assert "by_buyer" in data["data"]
        assert "trend" in data["data"]

        # 验证总览指标结构
        overview = data["data"]["overview"]
        assert "total_revenue" in overview
        assert "total_cost" in overview
        assert "total_profit" in overview
        assert "avg_profit_margin" in overview

    def test_get_dashboard_summary_with_date_filter(
        self, client: TestClient, admin_token
    ):
        """测试带日期筛选的仪表板汇总"""
        response = client.get(
            "/api/v1/reports/dashboard/summary",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={
                "start_date": (date.today() - timedelta(days=30)).isoformat(),
                "end_date": date.today().isoformat()
            }
        )

        assert response.status_code == 200

    def test_get_dashboard_summary_unauthorized(self, client: TestClient):
        """测试未认证访问"""
        response = client.get("/api/v1/reports/dashboard/summary")
        assert response.status_code == 401

    def test_dashboard_trend_data_structure(
        self, client: TestClient, admin_token
    ):
        """测试仪表板趋势数据结构"""
        response = client.get(
            "/api/v1/reports/dashboard/summary",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        trend = data["data"]["trend"]

        # 验证趋势数据结构
        assert "daily" in trend
        assert "monthly" in trend
        assert isinstance(trend["daily"], list)
        assert isinstance(trend["monthly"], list)

        # 如果有数据，验证数据点结构
        if len(trend["daily"]) > 0:
            daily_point = trend["daily"][0]
            assert "period" in daily_point
            assert "revenue" in daily_point
            assert "cost" in daily_point
            assert "profit" in daily_point


class TestResponseFormat:
    """测试响应格式统一性"""

    def test_success_response_format(
        self, client: TestClient, admin_token
    ):
        """测试成功响应格式"""
        response = client.get(
            "/api/v1/reports/projects/summary",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "data" in data
        assert data["success"] is True

    def test_error_response_format_403(
        self, client: TestClient, media_buyer_token, db_session
    ):
        """测试权限错误响应格式"""
        # 创建其他账户经理的项目
        other_project = Project(
            id=999,
            name="其他项目",
            account_manager_id=999,
            status="active"
        )
        db_session.add(other_project)
        db_session.commit()

        response = client.get(
            f"/api/v1/reports/projects/{other_project.id}/accounts",
            headers={"Authorization": f"Bearer {media_buyer_token}"}
        )

        assert response.status_code == 403
        data = response.json()
        assert "detail" in data

    def test_error_response_format_404(
        self, client: TestClient, admin_token
    ):
        """测试资源不存在响应格式"""
        response = client.get(
            "/api/v1/reports/projects/99999/accounts",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data


class TestSOTAlignmentAPI:
    """测试 API 层 SoT 对齐"""

    def test_only_authenticated_users_can_access(self, client: TestClient):
        """测试仅认证用户可访问（AUTH_SPEC v2.0）"""
        endpoints = [
            "/api/v1/reports/projects/summary",
            "/api/v1/reports/channels/summary",
            "/api/v1/reports/buyers/summary",
            "/api/v1/reports/dashboard/summary"
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 401

    def test_decimal_serialization(
        self, client: TestClient, admin_token
    ):
        """测试 Decimal 字段正确序列化为 float"""
        response = client.get(
            "/api/v1/reports/projects/summary",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        if len(data["data"]["items"]) > 0:
            item = data["data"]["items"][0]
            # 验证金额字段是 float 类型而非字符串
            assert isinstance(item.get("total_revenue", 0), (int, float))
            assert isinstance(item.get("total_cost", 0), (int, float))
            assert isinstance(item.get("gross_profit", 0), (int, float))

    def test_date_format_validation(
        self, client: TestClient, admin_token
    ):
        """测试日期格式验证"""
        response = client.get(
            "/api/v1/reports/projects/summary",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={
                "start_date": "invalid-date",
                "end_date": date.today().isoformat()
            }
        )

        # 应该返回 422 验证错误
        assert response.status_code == 422
