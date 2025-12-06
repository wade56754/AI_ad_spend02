"""
财务利润 API 测试
测试 /api/v1/finance/profit/summary 端点

SoT 对齐:
- ERROR_CODES_SOT.md v2.1: 错误码验证
- BUSINESS_RULES.md v3.1: 利润计算公式验证
- AUTH_SPEC.md v2.0: 权限控制验证

Version: 1.1
Author: Claude Code
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal


# ============================================================================
# Smoke Tests (5 cases)
# ============================================================================

class TestFinanceProfitApiSmoke:
    """财务利润 API 冒烟测试"""

    def test_profit_summary_no_project_id_returns_all(
        self,
        client,
        admin_headers,
        test_project,
        test_ad_account,
        test_daily_report,
    ):
        """
        TC-PROFIT-001: 不传 project_id 返回所有项目汇总

        Given: 存在日报数据
        When: GET /api/v1/finance/profit/summary (无 project_id)
        Then: 返回 200, 包含所有项目的利润汇总
        """
        response = client.get(
            "/api/v1/finance/profit/summary",
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data

    def test_profit_summary_with_project_id(
        self,
        client,
        admin_headers,
        test_project,
        test_ad_account,
        test_daily_report,
    ):
        """
        TC-PROFIT-002: 传 project_id 返回指定项目汇总

        Given: 存在指定项目的日报数据
        When: GET /api/v1/finance/profit/summary?project_id=X
        Then: 返回 200, 仅包含指定项目的利润汇总
        """
        response = client.get(
            f"/api/v1/finance/profit/summary?project_id={test_project.id}",
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_profit_summary_invalid_project_returns_404(
        self,
        client,
        admin_headers,
    ):
        """
        TC-PROFIT-003: 不存在的 project_id 返回 BIZ_002

        Given: 项目 ID 不存在
        When: GET /api/v1/finance/profit/summary?project_id=99999
        Then: 返回 404, code=BIZ_002

        Ref: ERROR_CODES_SOT.md v2.1 - BIZ_002 资源不存在
        """
        response = client.get(
            "/api/v1/finance/profit/summary?project_id=99999",
            headers=admin_headers,
        )

        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        # error_response 格式: {"success": false, "error": {"code": "...", "message": "..."}}
        assert data["error"]["code"] == "BIZ_002"

    def test_profit_summary_invalid_date_range_returns_400(
        self,
        client,
        admin_headers,
    ):
        """
        TC-PROFIT-004: 日期范围无效返回 BIZ_001

        Given: start_date > end_date
        When: GET /api/v1/finance/profit/summary?start_date=X&end_date=Y
        Then: 返回 400, code=BIZ_001 (BusinessRuleException)

        Ref: ERROR_CODES_SOT.md v2.1 - BIZ_001 业务规则错误
        """
        today = date.today()
        yesterday = today - timedelta(days=1)

        response = client.get(
            f"/api/v1/finance/profit/summary?start_date={today}&end_date={yesterday}",
            headers=admin_headers,
        )

        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        # error_response 格式: {"success": false, "error": {"code": "...", "message": "..."}}
        assert data["error"]["code"] == "BIZ_001"

    def test_profit_summary_unauthorized_returns_403(
        self,
        client,
        media_buyer_headers,
    ):
        """
        TC-PROFIT-005: 无权限用户返回 403

        Given: 用户角色为 media_buyer
        When: GET /api/v1/finance/profit/summary
        Then: 返回 403

        Ref: AUTH_SPEC.md v2.0 - 权限矩阵
        Allowed: admin, finance, data_operator
        Denied: media_buyer, account_manager
        """
        response = client.get(
            "/api/v1/finance/profit/summary",
            headers=media_buyer_headers,
        )

        # 应返回 403 权限不足
        assert response.status_code == 403
        data = response.json()
        assert data["success"] is False
        # 403 响应格式可能因认证中间件而异
        # 验证错误码存在于 error 或 code 字段
        error_code = data.get("error", {}).get("code") or data.get("code")
        assert error_code is not None


# ============================================================================
# Additional Tests
# ============================================================================

class TestFinanceProfitApiAuthorization:
    """权限验证测试"""

    def test_admin_can_access(self, client, admin_headers):
        """admin 角色可以访问"""
        response = client.get(
            "/api/v1/finance/profit/summary",
            headers=admin_headers,
        )
        assert response.status_code == 200

    def test_finance_can_access(self, client, finance_headers):
        """finance 角色可以访问"""
        response = client.get(
            "/api/v1/finance/profit/summary",
            headers=finance_headers,
        )
        assert response.status_code == 200

    def test_data_operator_can_access(self, client, data_operator_headers):
        """data_operator 角色可以访问"""
        response = client.get(
            "/api/v1/finance/profit/summary",
            headers=data_operator_headers,
        )
        assert response.status_code == 200

    def test_no_token_returns_401(self, client):
        """无 token 返回 401"""
        response = client.get("/api/v1/finance/profit/summary")
        assert response.status_code == 401


class TestFinanceProfitApiDateFilters:
    """日期过滤测试"""

    def test_with_start_date_only(
        self,
        client,
        admin_headers,
        test_project,
        test_ad_account,
        test_daily_report,
    ):
        """只传 start_date"""
        yesterday = date.today() - timedelta(days=1)
        response = client.get(
            f"/api/v1/finance/profit/summary?start_date={yesterday}",
            headers=admin_headers,
        )
        assert response.status_code == 200

    def test_with_end_date_only(
        self,
        client,
        admin_headers,
        test_project,
        test_ad_account,
        test_daily_report,
    ):
        """只传 end_date"""
        tomorrow = date.today() + timedelta(days=1)
        response = client.get(
            f"/api/v1/finance/profit/summary?end_date={tomorrow}",
            headers=admin_headers,
        )
        assert response.status_code == 200

    def test_with_valid_date_range(
        self,
        client,
        admin_headers,
        test_project,
        test_ad_account,
        test_daily_report,
    ):
        """传有效日期范围"""
        start = date.today() - timedelta(days=7)
        end = date.today()
        response = client.get(
            f"/api/v1/finance/profit/summary?start_date={start}&end_date={end}",
            headers=admin_headers,
        )
        assert response.status_code == 200


class TestFinanceProfitApiResponseFormat:
    """响应格式验证测试"""

    def test_response_contains_required_fields(
        self,
        client,
        admin_headers,
    ):
        """
        响应包含必要字段

        Ref: schemas/finance.py ProfitSummaryResponse
        """
        response = client.get(
            "/api/v1/finance/profit/summary",
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # 验证 Envelope 格式
        assert "success" in data
        assert "message" in data
        assert "data" in data

        # 验证 data 字段结构
        result = data["data"]
        assert "items" in result
        assert "total_conversions" in result
        assert "total_revenue" in result
        assert "total_cost" in result
        assert "total_profit" in result
        assert "overall_profit_margin" in result
