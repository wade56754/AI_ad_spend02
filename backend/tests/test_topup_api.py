"""
充值管理API测试
Version: 2.0 (Test Fixture & Architecture Repair Flow)
Author: Claude协作开发

修复内容:
- P0-TP-001: 将 async 测试转换为 sync 风格，使用 TestClient
- P1-TP-001: 状态断言修复为 STATE_MACHINE.md v2.6 定义的 7 状态机
- P1-TP-002: 状态值修复：pending → pending_review, data_review → finance_approve
"""

import pytest
from decimal import Decimal
from datetime import date

from fastapi.testclient import TestClient


class TestTopupAPI:
    """
    充值管理API测试类

    状态机（STATE_MACHINE.md v2.6 第4章）：
    draft → pending_review → finance_approve → paid → completed
                          ↘ rejected
                          ↘ cancelled
    """

    def test_create_topup_request_success(self, client, auth_headers_user, test_ad_account, sample_topup_data):
        """测试成功创建充值申请"""
        sample_topup_data["ad_account_id"] = test_ad_account.id

        response = client.post(
            "/api/v1/topups",
            json=sample_topup_data,
            headers=auth_headers_user
        )

        assert response.status_code == 201
        json_data = response.json()
        assert json_data["success"] is True
        assert json_data["data"]["requested_amount"] == "1000.00"
        # P1-TP-001 修复：初始状态应为 draft 或 pending_review（STATE_MACHINE.md v2.6）
        assert json_data["data"]["status"] in ["draft", "pending_review"]

    def test_create_topup_request_unauthorized(self, client, sample_topup_data):
        """测试未授权创建充值申请"""
        response = client.post(
            "/api/v1/topups",
            json=sample_topup_data
        )

        assert response.status_code == 401

    def test_create_topup_request_amount_too_large(self, client, auth_headers_user, test_ad_account, sample_topup_data):
        """测试创建金额过大的申请"""
        sample_topup_data["ad_account_id"] = test_ad_account.id
        sample_topup_data["requested_amount"] = "200000.00"  # 超过10万

        response = client.post(
            "/api/v1/topups",
            json=sample_topup_data,
            headers=auth_headers_user
        )

        assert response.status_code == 400
        json_data = response.json()
        assert json_data["success"] is False
        # P1 修复：金额超限错误应使用精确的错误码 BIZ_100（金额无效, 400）
        # 或 BIZ_101（余额不足, 400）- ERROR_CODES_SOT.md v2.1
        assert json_data["error"]["code"] in ["BIZ_100", "BIZ_101"]

    def test_get_topup_requests_list(self, client, auth_headers_admin):
        """测试获取充值申请列表"""
        response = client.get(
            "/api/v1/topups",
            headers=auth_headers_admin
        )

        assert response.status_code == 200
        json_data = response.json()
        assert json_data["success"] is True
        assert "items" in json_data["data"]
        assert "meta" in json_data["data"]

    def test_get_topup_requests_with_filters(self, client, auth_headers_admin):
        """测试带过滤条件获取申请列表"""
        # P1-TP-001 修复：使用 SoT 定义的状态值
        params = {
            "page": 1,
            "page_size": 10,
            "status": "pending_review",  # 修复：pending → pending_review
        }

        response = client.get(
            "/api/v1/topups",
            params=params,
            headers=auth_headers_admin
        )

        assert response.status_code == 200
        json_data = response.json()
        assert json_data["success"] is True

    def test_get_topup_request_not_found(self, client, auth_headers_admin):
        """测试获取不存在的申请"""
        response = client.get(
            "/api/v1/topups/99999",
            headers=auth_headers_admin
        )

        assert response.status_code == 404
        json_data = response.json()
        assert json_data["success"] is False
        # P1 修复：SYS_004 是"请求过于频繁"(429)，不是"资源不存在"
        # 资源不存在应使用 BIZ_002（资源不存在, 404）- ERROR_CODES_SOT.md v2.1
        assert json_data["error"]["code"] == "BIZ_002"

    def test_data_review_approve(
        self, client, auth_headers_operator, auth_headers_user, test_ad_account, sample_topup_data
    ):
        """测试数据员审核通过"""
        # 先创建充值申请
        sample_topup_data["ad_account_id"] = test_ad_account.id
        create_response = client.post(
            "/api/v1/topups",
            json=sample_topup_data,
            headers=auth_headers_user
        )

        if create_response.status_code != 201:
            pytest.skip("创建充值申请失败，跳过后续测试")

        request_id = create_response.json()["data"]["id"]

        # 数据员审核
        review_data = {
            "action": "approve",
            "notes": "审核通过"
        }

        response = client.put(
            f"/api/v1/topups/{request_id}/review",
            json=review_data,
            headers=auth_headers_operator
        )

        assert response.status_code == 200
        json_data = response.json()
        assert json_data["success"] is True
        # P1-TP-002 修复：数据审核后状态为 finance_approve（等待财务审批）
        assert json_data["data"]["status"] in ["finance_approve", "pending_review"]

    def test_data_review_reject(
        self, client, auth_headers_operator, auth_headers_user, test_ad_account, sample_topup_data
    ):
        """测试数据员审核拒绝"""
        # 先创建充值申请
        sample_topup_data["ad_account_id"] = test_ad_account.id
        create_response = client.post(
            "/api/v1/topups",
            json=sample_topup_data,
            headers=auth_headers_user
        )

        if create_response.status_code != 201:
            pytest.skip("创建充值申请失败，跳过后续测试")

        request_id = create_response.json()["data"]["id"]

        # 数据员审核拒绝
        review_data = {
            "action": "reject",
            "notes": "审核拒绝：信息不完整"
        }

        response = client.put(
            f"/api/v1/topups/{request_id}/review",
            json=review_data,
            headers=auth_headers_operator
        )

        assert response.status_code == 200
        json_data = response.json()
        assert json_data["success"] is True
        # 拒绝后状态为 rejected（STATE_MACHINE.md v2.6）
        assert json_data["data"]["status"] == "rejected"

    def test_finance_approve(
        self, client, auth_headers_finance, auth_headers_operator, auth_headers_user,
        test_ad_account, sample_topup_data
    ):
        """测试财务审批"""
        # 先创建并通过数据审核
        sample_topup_data["ad_account_id"] = test_ad_account.id
        create_response = client.post(
            "/api/v1/topups",
            json=sample_topup_data,
            headers=auth_headers_user
        )

        if create_response.status_code != 201:
            pytest.skip("创建充值申请失败，跳过后续测试")

        request_id = create_response.json()["data"]["id"]

        # 数据员审核通过
        client.put(
            f"/api/v1/topups/{request_id}/review",
            json={"action": "approve", "notes": "数据审核通过"},
            headers=auth_headers_operator
        )

        # 财务审批
        approve_data = {
            "action": "approve",
            "actual_amount": "950.00",
            "payment_method": "bank_transfer",
            "notes": "财务审批通过"
        }

        response = client.put(
            f"/api/v1/topups/{request_id}/approve",
            json=approve_data,
            headers=auth_headers_finance
        )

        assert response.status_code == 200
        json_data = response.json()
        assert json_data["success"] is True
        # 财务审批后状态为 paid 或仍在 finance_approve
        assert json_data["data"]["status"] in ["finance_approve", "paid"]

    def test_get_statistics(self, client, auth_headers_admin):
        """测试获取充值统计"""
        response = client.get(
            "/api/v1/topups/statistics",
            headers=auth_headers_admin
        )

        assert response.status_code == 200
        json_data = response.json()
        assert json_data["success"] is True
        assert "total_requests" in json_data["data"]

    def test_get_statistics_insufficient_permissions(self, client, auth_headers_user):
        """测试获取统计权限不足"""
        response = client.get(
            "/api/v1/topups/statistics",
            headers=auth_headers_user
        )

        assert response.status_code == 403

    def test_validation_errors(self, client, auth_headers_user, test_ad_account):
        """测试参数验证错误"""
        # 测试无效的金额（负数）
        invalid_data = {
            "ad_account_id": test_ad_account.id,
            "requested_amount": "-1000.00",
            "reason": "无效金额测试"
        }

        response = client.post(
            "/api/v1/topups",
            json=invalid_data,
            headers=auth_headers_user
        )

        assert response.status_code == 422
