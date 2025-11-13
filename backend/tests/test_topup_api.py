"""
充值管理API测试
Version: 1.0
Author: Claude协作开发
"""

import pytest
from decimal import Decimal
from datetime import date
from httpx import AsyncClient

from models.user import User


class TestTopupAPI:
    """充值管理API测试类"""

    @pytest.mark.asyncio
    async def test_create_topup_request_success(self, client: AsyncClient, media_buyer_token, managed_ad_account_id):
        """测试成功创建充值申请"""
        headers = {"Authorization": f"Bearer {media_buyer_token}"}
        data = {
            "ad_account_id": managed_ad_account_id,
            "requested_amount": "1000.00",
            "reason": "广告投放充值",
            "urgency_level": "normal"
        }

        response = await client.post("/api/v1/topups", json=data, headers=headers)

        assert response.status_code == 201
        json_data = response.json()
        assert json_data["success"] is True
        assert json_data["data"]["requested_amount"] == "1000.00"
        assert json_data["data"]["status"] == "pending"

    @pytest.mark.asyncio
    async def test_create_topup_request_insufficient_permissions(self, client: AsyncClient, admin_token, sample_ad_account_id):
        """测试创建申请权限不足"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        data = {
            "ad_account_id": sample_ad_account_id,
            "requested_amount": "1000.00",
            "reason": "测试申请"
        }

        response = await client.post("/api/v1/topups", json=data, headers=headers)

        assert response.status_code == 403
        json_data = response.json()
        assert json_data["success"] is False

    @pytest.mark.asyncio
    async def test_create_topup_request_amount_too_large(self, client: AsyncClient, media_buyer_token, managed_ad_account_id):
        """测试创建金额过大的申请"""
        headers = {"Authorization": f"Bearer {media_buyer_token}"}
        data = {
            "ad_account_id": managed_ad_account_id,
            "requested_amount": "200000.00",  # 超过10万
            "reason": "超大金额测试"
        }

        response = await client.post("/api/v1/topups", json=data, headers=headers)

        assert response.status_code == 400
        json_data = response.json()
        assert json_data["success"] is False
        assert "BIZ_201" in json_data["error"]["code"]

    @pytest.mark.asyncio
    async def test_get_topup_requests_list(self, client: AsyncClient, admin_token):
        """测试获取充值申请列表"""
        headers = {"Authorization": f"Bearer {admin_token}"}

        response = await client.get("/api/v1/topups", headers=headers)

        assert response.status_code == 200
        json_data = response.json()
        assert json_data["success"] is True
        assert "items" in json_data["data"]
        assert "meta" in json_data["data"]

    @pytest.mark.asyncio
    async def test_get_topup_requests_with_filters(self, client: AsyncClient, admin_token):
        """测试带过滤条件获取申请列表"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        params = {
            "page": 1,
            "page_size": 10,
            "status": "pending",
            "urgency": "high"
        }

        response = await client.get("/api/v1/topups", params=params, headers=headers)

        assert response.status_code == 200
        json_data = response.json()
        assert json_data["success"] is True

    @pytest.mark.asyncio
    async def test_get_topup_request_detail(self, client: AsyncClient, admin_token, sample_topup_request_id):
        """测试获取充值申请详情"""
        headers = {"Authorization": f"Bearer {admin_token}"}

        response = await client.get(f"/api/v1/topups/{sample_topup_request_id}", headers=headers)

        assert response.status_code == 200
        json_data = response.json()
        assert json_data["success"] is True
        assert json_data["data"]["id"] == sample_topup_request_id

    @pytest.mark.asyncio
    async def test_get_topup_request_not_found(self, client: AsyncClient, admin_token):
        """测试获取不存在的申请"""
        headers = {"Authorization": f"Bearer {admin_token}"}

        response = await client.get("/api/v1/topups/99999", headers=headers)

        assert response.status_code == 404
        json_data = response.json()
        assert json_data["success"] is False
        assert json_data["error"]["code"] == "SYS_004"

    @pytest.mark.asyncio
    async def test_data_review_approve(self, client: AsyncClient, data_operator_token, sample_topup_request_id):
        """测试数据员审核通过"""
        headers = {"Authorization": f"Bearer {data_operator_token}"}
        data = {
            "action": "approve",
            "notes": "审核通过"
        }

        response = await client.put(
            f"/api/v1/topups/{sample_topup_request_id}/review",
            json=data,
            headers=headers
        )

        assert response.status_code == 200
        json_data = response.json()
        assert json_data["success"] is True
        assert json_data["data"]["status"] == "data_review"

    @pytest.mark.asyncio
    async def test_data_review_reject(self, client: AsyncClient, data_operator_token, sample_topup_request_id):
        """测试数据员审核拒绝"""
        headers = {"Authorization": f"Bearer {data_operator_token}"}
        data = {
            "action": "reject",
            "notes": "审核拒绝：信息不完整"
        }

        response = await client.put(
            f"/api/v1/topups/{sample_topup_request_id}/review",
            json=data,
            headers=headers
        )

        assert response.status_code == 200
        json_data = response.json()
        assert json_data["success"] is True
        assert json_data["data"]["status"] == "rejected"

    @pytest.mark.asyncio
    async def test_finance_approve(self, client: AsyncClient, finance_token, sample_topup_request_id):
        """测试财务审批"""
        # 先通过数据审核
        headers = {"Authorization": f"Bearer {data_operator_token}"}
        data = {"action": "approve", "notes": "数据审核通过"}
        await client.put(f"/api/v1/topups/{sample_topup_request_id}/review", json=data, headers=headers)

        # 然后财务审批
        headers = {"Authorization": f"Bearer {finance_token}"}
        data = {
            "action": "approve",
            "actual_amount": "950.00",
            "payment_method": "bank_transfer",
            "notes": "财务审批通过"
        }

        response = await client.put(
            f"/api/v1/topups/{sample_topup_request_id}/approve",
            json=data,
            headers=headers
        )

        assert response.status_code == 200
        json_data = response.json()
        assert json_data["success"] is True
        assert json_data["data"]["status"] == "finance_approve"
        assert json_data["data"]["actual_amount"] == "950.00"

    @pytest.mark.asyncio
    async def test_mark_as_paid(self, client: AsyncClient, finance_token, sample_topup_request_id):
        """测试标记为已打款"""
        # 先完成财务审批
        await self._setup_paid_scenario(client, finance_token, sample_topup_request_id)

        headers = {"Authorization": f"Bearer {finance_token}"}
        data = {
            "transaction_id": "TXN20251112143045",
            "notes": "已通过银行转账"
        }

        response = await client.put(
            f"/api/v1/topups/{sample_topup_request_id}/pay",
            json=data,
            headers=headers
        )

        assert response.status_code == 200
        json_data = response.json()
        assert json_data["success"] is True
        assert json_data["data"]["status"] == "paid"

    @pytest.mark.asyncio
    async def test_upload_receipt(self, client: AsyncClient, finance_token, sample_topup_request_id):
        """测试上传打款凭证"""
        # 先标记为已打款
        await self._setup_paid_scenario(client, finance_token, sample_topup_request_id)
        await client.put(
            f"/api/v1/topups/{sample_topup_request_id}/pay",
            json={"transaction_id": "TXN123"},
            headers={"Authorization": f"Bearer {finance_token}"}
        )

        headers = {"Authorization": f"Bearer {finance_token}"}
        data = {
            "receipt_url": "https://example.com/receipt.jpg",
            "transaction_id": "TXN20251112143046",
            "notes": "凭证已上传"
        }

        response = await client.post(
            f"/api/v1/topups/{sample_topup_request_id}/receipt",
            json=data,
            headers=headers
        )

        assert response.status_code == 200
        json_data = response.json()
        assert json_data["success"] is True
        assert json_data["data"]["receipt_url"] == "https://example.com/receipt.jpg"

    @pytest.mark.asyncio
    async def test_get_approval_logs(self, client: AsyncClient, admin_token, sample_topup_request_id):
        """测试获取审批日志"""
        headers = {"Authorization": f"Bearer {admin_token}"}

        response = await client.get(
            f"/api/v1/topups/{sample_topup_request_id}/logs",
            headers=headers
        )

        assert response.status_code == 200
        json_data = response.json()
        assert json_data["success"] is True
        assert isinstance(json_data["data"], list)

    @pytest.mark.asyncio
    async def test_get_statistics(self, client: AsyncClient, admin_token):
        """测试获取充值统计"""
        headers = {"Authorization": f"Bearer {admin_token}"}

        response = await client.get("/api/v1/topups/statistics", headers=headers)

        assert response.status_code == 200
        json_data = response.json()
        assert json_data["success"] is True
        assert "total_requests" in json_data["data"]
        assert "total_amount_requested" in json_data["data"]

    @pytest.mark.asyncio
    async def test_get_statistics_insufficient_permissions(self, client: AsyncClient, media_buyer_token):
        """测试获取统计权限不足"""
        headers = {"Authorization": f"Bearer {media_buyer_token}"}

        response = await client.get("/api/v1/topups/statistics", headers=headers)

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_get_dashboard(self, client: AsyncClient, finance_token):
        """测试获取仪表板数据"""
        headers = {"Authorization": f"Bearer {finance_token}"}

        response = await client.get("/api/v1/topups/dashboard", headers=headers)

        assert response.status_code == 200
        json_data = response.json()
        assert json_data["success"] is True
        assert "pending_reviews" in json_data["data"]
        assert "today_requests" in json_data["data"]

    @pytest.mark.asyncio
    async def test_get_account_balance(self, client: AsyncClient, admin_token, sample_ad_account_id):
        """测试获取账户余额"""
        headers = {"Authorization": f"Bearer {admin_token}"}

        response = await client.get(
            f"/api/v1/topups/accounts/{sample_ad_account_id}/balance",
            headers=headers
        )

        assert response.status_code == 200
        json_data = response.json()
        assert json_data["success"] is True
        assert json_data["data"]["ad_account_id"] == sample_ad_account_id
        assert json_data["data"]["max_balance"] == "500000.00"

    @pytest.mark.asyncio
    async def test_export_requests(self, client: AsyncClient, admin_token):
        """测试导出充值记录"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        params = {
            "start_date": "2025-01-01",
            "end_date": "2025-12-31",
            "status": "completed"
        }

        response = await client.get("/api/v1/topups/export", params=params, headers=headers)

        assert response.status_code == 200
        json_data = response.json()
        assert json_data["success"] is True
        assert isinstance(json_data["data"], list)

    @pytest.mark.asyncio
    async def test_export_requests_insufficient_permissions(self, client: AsyncClient, media_buyer_token):
        """测试导出权限不足"""
        headers = {"Authorization": f"Bearer {media_buyer_token}"}

        response = await client.get("/api/v1/topups/export", headers=headers)

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_invalid_status_transition(self, client: AsyncClient, data_operator_token, sample_topup_request_id):
        """测试无效状态转换"""
        # 直接尝试财务审批（未通过数据审核）
        headers = {"Authorization": f"Bearer {data_operator_token}"}
        data = {
            "action": "approve",
            "actual_amount": "1000.00",
            "payment_method": "bank_transfer"
        }

        response = await client.put(
            f"/api/v1/topups/{sample_topup_request_id}/approve",
            json=data,
            headers=headers
        )

        assert response.status_code == 403  # Data operator cannot approve finance

    @pytest.mark.asyncio
    async def test_validation_errors(self, client: AsyncClient, media_buyer_token, managed_ad_account_id):
        """测试参数验证错误"""
        headers = {"Authorization": f"Bearer {media_buyer_token}"}

        # 测试无效的金额
        invalid_data = {
            "ad_account_id": managed_ad_account_id,
            "requested_amount": "-1000.00",  # 负数
            "reason": "无效金额测试"
        }

        response = await client.post("/api/v1/topups", json=invalid_data, headers=headers)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_unauthorized_access(self, client: AsyncClient):
        """测试未授权访问"""
        data = {
            "ad_account_id": 1,
            "requested_amount": "1000.00",
            "reason": "未授权测试"
        }

        response = await client.post("/api/v1/topups", json=data)

        assert response.status_code == 401

    # ===== 辅助方法 =====

    async def _setup_paid_scenario(self, client: AsyncClient, finance_token: str, request_id: int):
        """设置已打款场景的辅助方法"""
        # 通过数据审核
        headers = {"Authorization": f"Bearer {data_operator_token}"}
        data = {"action": "approve", "notes": "数据审核通过"}
        await client.put(f"/api/v1/topups/{request_id}/review", json=data, headers=headers)

        # 通过财务审批
        headers = {"Authorization": f"Bearer {finance_token}"}
        data = {
            "action": "approve",
            "actual_amount": "1000.00",
            "payment_method": "bank_transfer"
        }
        await client.put(f"/api/v1/topups/{request_id}/approve", json=data, headers=headers)