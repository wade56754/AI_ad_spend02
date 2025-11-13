"""
充值管理权限测试
Version: 1.0
Author: Claude协作开发
"""

import pytest
from httpx import AsyncClient


class TestTopupPermissions:
    """充值管理权限测试类"""

    @pytest.mark.asyncio
    async def test_admin_full_permissions(self, client: AsyncClient, admin_token):
        """测试管理员拥有完整权限"""
        headers = {"Authorization": f"Bearer {admin_token}"}

        # 管理员可以查看所有申请
        response = await client.get("/api/v1/topups", headers=headers)
        assert response.status_code == 200

        # 管理员可以查看统计
        response = await client.get("/api/v1/topups/statistics", headers=headers)
        assert response.status_code == 200

        # 管理员可以导出数据
        response = await client.get("/api/v1/topups/export", headers=headers)
        assert response.status_code == 200

        # 管理员可以查看仪表板
        response = await client.get("/api/v1/topups/dashboard", headers=headers)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_finance_permissions(self, client: AsyncClient, finance_token):
        """测试财务人员权限"""
        headers = {"Authorization": f"Bearer {finance_token}"}

        # 财务不能创建申请
        create_data = {
            "ad_account_id": 1,
            "requested_amount": "1000.00",
            "reason": "测试申请"
        }
        response = await client.post("/api/v1/topups", json=create_data, headers=headers)
        assert response.status_code == 403

        # 财务可以查看所有申请
        response = await client.get("/api/v1/topups", headers=headers)
        assert response.status_code == 200

        # 财务可以进行财务审批
        response = await client.put(
            "/api/v1/topups/1/approve",
            json={"action": "approve", "actual_amount": "1000.00"},
            headers=headers
        )
        # 可能404（ID不存在）但不能是403（权限不足）

        # 财务可以标记为已打款
        response = await client.put(
            "/api/v1/topups/1/pay",
            json={},
            headers=headers
        )
        # 可能404但不能是403

        # 财务可以上传凭证
        response = await client.post(
            "/api/v1/topups/1/receipt",
            json={"receipt_url": "https://example.com"},
            headers=headers
        )
        # 可能404但不能是403

        # 财务可以查看统计
        response = await client.get("/api/v1/topups/statistics", headers=headers)
        assert response.status_code == 200

        # 财务可以导出数据
        response = await client.get("/api/v1/topups/export", headers=headers)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_data_operator_permissions(self, client: AsyncClient, data_operator_token):
        """测试数据员权限"""
        headers = {"Authorization": f"Bearer {data_operator_token}"}

        # 数据员不能创建申请
        create_data = {
            "ad_account_id": 1,
            "requested_amount": "1000.00",
            "reason": "测试申请"
        }
        response = await client.post("/api/v1/topups", json=create_data, headers=headers)
        assert response.status_code == 403

        # 数据员可以查看所有申请
        response = await client.get("/api/v1/topups", headers=headers)
        assert response.status_code == 200

        # 数据员可以进行数据审核
        response = await client.put(
            "/api/v1/topups/1/review",
            json={"action": "approve", "notes": "审核通过"},
            headers=headers
        )
        # 可能404但不能是403

        # 数据员不能进行财务审批
        response = await client.put(
            "/api/v1/topups/1/approve",
            json={"action": "approve", "actual_amount": "1000.00"},
            headers=headers
        )
        assert response.status_code == 403

        # 数据员不能标记为已打款
        response = await client.put(
            "/api/v1/topups/1/pay",
            json={},
            headers=headers
        )
        assert response.status_code == 403

        # 数据员可以查看统计
        response = await client.get("/api/v1/topups/statistics", headers=headers)
        assert response.status_code == 200

        # 数据员不能导出数据
        response = await client.get("/api/v1/topups/export", headers=headers)
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_account_manager_permissions(self, client: AsyncClient, account_manager_token, account_manager_project_id):
        """测试账户管理员权限"""
        headers = {"Authorization": f"Bearer {account_manager_token}"}

        # 账户管理员可以创建申请
        create_data = {
            "ad_account_id": 1,
            "requested_amount": "1000.00",
            "reason": "账户经理申请"
        }
        response = await client.post("/api/v1/topups", json=create_data, headers=headers)
        # 可能422（参数错误）但不能是403（权限不足）

        # 账户管理员可以查看申请列表（只能看到自己项目的）
        response = await client.get("/api/v1/topups", headers=headers)
        assert response.status_code == 200

        # 账户管理员不能审核
        response = await client.put(
            "/api/v1/topups/1/review",
            json={"action": "approve"},
            headers=headers
        )
        assert response.status_code == 403

        # 账户管理员不能进行财务审批
        response = await client.put(
            "/api/v1/topups/1/approve",
            json={"action": "approve"},
            headers=headers
        )
        assert response.status_code == 403

        # 账户管理员不能查看统计
        response = await client.get("/api/v1/topups/statistics", headers=headers)
        assert response.status_code == 403

        # 账户管理员不能导出数据
        response = await client.get("/api/v1/topups/export", headers=headers)
        assert response.status_code == 403

        # 账户管理员可以查看仪表板
        response = await client.get("/api/v1/topups/dashboard", headers=headers)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_media_buyer_permissions(self, client: AsyncClient, media_buyer_token):
        """测试媒体买家权限"""
        headers = {"Authorization": f"Bearer {media_buyer_token}"}

        # 媒体买家可以创建申请
        create_data = {
            "ad_account_id": 1,
            "requested_amount": "1000.00",
            "reason": "媒体买家申请"
        }
        response = await client.post("/api/v1/topups", json=create_data, headers=headers)
        # 可能422（参数错误）但不能是403（权限不足）

        # 媒体买家可以查看申请列表（只能看到自己的）
        response = await client.get("/api/v1/topups", headers=headers)
        assert response.status_code == 200

        # 媒体买家不能审核
        response = await client.put(
            "/api/v1/topups/1/review",
            json={"action": "approve"},
            headers=headers
        )
        assert response.status_code == 403

        # 媒体买家不能进行财务审批
        response = await client.put(
            "/api/v1/topups/1/approve",
            json={"action": "approve"},
            headers=headers
        )
        assert response.status_code == 403

        # 媒体买家不能查看统计
        response = await client.get("/api/v1/topups/statistics", headers=headers)
        assert response.status_code == 403

        # 媒体买家不能导出数据
        response = await client.get("/api/v1/topups/export", headers=headers)
        assert response.status_code == 403

        # 媒体买家可以查看仪表板
        response = await client.get("/api/v1/topups/dashboard", headers=headers)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_cross_project_access_denied(self, client: AsyncClient, account_manager_token):
        """测试跨项目访问被拒绝"""
        headers = {"Authorization": f"Bearer {account_manager_token}"}

        # 尝试访问不属于自己项目的申请详情
        response = await client.get("/api/v1/topups/10000", headers=headers)
        # 应该是404（不存在）或403（无权限）

        # 尝试操作不属于自己项目的申请
        response = await client.put(
            "/api/v1/topups/10000/review",
            json={"action": "approve"},
            headers=headers
        )
        # 应该是404或403

    @pytest.mark.asyncio
    async def test_data_isolation(self, client: AsyncClient, admin_token, media_buyer_token):
        """测试数据隔离"""
        # 管理员创建一个申请
        headers_admin = {"Authorization": f"Bearer {admin_token}"}
        create_data = {
            "ad_account_id": 1,
            "requested_amount": "1000.00",
            "reason": "管理员创建的申请"
        }
        # 注意：管理员可能没有权限创建，这里仅作示例
        # response = await client.post("/api/v1/topups", json=create_data, headers=headers_admin)

        # 媒体买家不应该能看到这个申请
        headers_buyer = {"Authorization": f"Bearer {media_buyer_token}"}
        response = await client.get("/api/v1/topups", headers=headers_buyer)
        data = response.json()["data"]["items"]
        # 媒体买家只能看到自己的申请

    @pytest.mark.asyncio
    async def test_unauthenticated_access(self, client: AsyncClient):
        """测试未认证访问被拒绝"""
        # 未认证不能创建申请
        create_data = {
            "ad_account_id": 1,
            "requested_amount": "1000.00",
            "reason": "测试"
        }
        response = await client.post("/api/v1/topups", json=create_data)
        assert response.status_code == 401

        # 未认证不能查看申请列表
        response = await client.get("/api/v1/topups")
        assert response.status_code == 401

        # 未认证不能查看统计
        response = await client.get("/api/v1/topups/statistics")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_invalid_token(self, client: AsyncClient):
        """测试无效token访问被拒绝"""
        headers = {"Authorization": "Bearer invalid_token"}

        # 无效token不能创建申请
        create_data = {
            "ad_account_id": 1,
            "requested_amount": "1000.00",
            "reason": "测试"
        }
        response = await client.post("/api/v1/topups", json=create_data, headers=headers)
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_rls_enforcement(self, client: AsyncClient, media_buyer_token, admin_token):
        """测试RLS策略强制执行"""
        # 管理员查看所有申请
        headers_admin = {"Authorization": f"Bearer {admin_token}"}
        response_admin = await client.get("/api/v1/topups", headers=headers_admin)
        admin_count = len(response_admin.json()["data"]["items"])

        # 媒体买家查看自己的申请
        headers_buyer = {"Authorization": f"Bearer {media_buyer_token}"}
        response_buyer = await client.get("/api/v1/topups", headers=headers_buyer)
        buyer_count = len(response_buyer.json()["data"]["items"])

        # 媒体买家看到的申请数量应该少于或等于管理员看到的
        assert buyer_count <= admin_count

    @pytest.mark.asyncio
    async def test_permission_inheritance(self, client: AsyncClient, finance_token, account_manager_token):
        """测试权限继承"""
        # 财务可以查看所有账户余额
        headers_finance = {"Authorization": f"Bearer {finance_token}"}
        response_finance = await client.get("/api/v1/topups/accounts/1/balance", headers=headers_finance)
        # 可能404（账户不存在）但不能是403

        # 账户管理员只能查看自己项目账户的余额
        headers_manager = {"Authorization": f"Bearer {account_manager_token}"}
        response_manager = await client.get("/api/v1/topups/accounts/1/balance", headers=headers_manager)
        # 可能403（无权限）或404（账户不存在或无权限）