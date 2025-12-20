"""
项目管理API测试
Version: 2.0 - Fixed fixture compatibility
Author: Claude协作开发

变更说明：
- v2.0: 修复 fixture 兼容性问题
  - 将 async_client 改为 async_client (来自 conftest.py)
  - 使用 conftest 提供的 token fixtures
  - 移除 pytestmark skip
- v1.1: Skip all tests due to fixture mismatch
"""

import pytest
from decimal import Decimal
from datetime import date

from backend.models import User


class TestProjectAPI:
    """项目管理API测试类"""

    @pytest.mark.asyncio
    async def test_create_project_success(self, async_client, admin_token):
        """测试成功创建项目"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        data = {
            "name": "新项目",
            "client_name": "客户A",
            "client_company": "客户公司A",
            "description": "项目描述",
            "budget": "10000.00",
            "currency": "USD",
            "start_date": "2025-01-01",
            "end_date": "2025-12-31"
        }

        response = await async_client.post("/api/v1/projects", json=data, headers=headers)

        assert response.status_code == 201
        json_data = response.json()
        assert json_data["success"] is True
        assert json_data["data"]["name"] == "新项目"
        assert json_data["data"]["client_name"] == "客户A"
        assert json_data["data"]["budget"] == "10000.00"

    @pytest.mark.asyncio
    async def test_create_project_unauthorized(self, async_client):
        """测试未授权创建项目"""
        data = {
            "name": "项目",
            "client_name": "客户",
            "client_company": "公司"
        }

        response = await async_client.post("/api/v1/projects", json=data)

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_project_insufficient_permissions(self, async_client, media_buyer_token):
        """测试权限不足创建项目"""
        headers = {"Authorization": f"Bearer {media_buyer_token}"}
        data = {
            "name": "项目",
            "client_name": "客户",
            "client_company": "公司"
        }

        response = await async_client.post("/api/v1/projects", json=data, headers=headers)

        assert response.status_code == 403
        json_data = response.json()
        assert json_data["success"] is False
        assert "权限不足" in json_data["error"]["message"]

    @pytest.mark.asyncio
    async def test_get_projects_list(self, async_client, admin_token):
        """测试获取项目列表"""
        headers = {"Authorization": f"Bearer {admin_token}"}

        response = await async_client.get("/api/v1/projects", headers=headers)

        assert response.status_code == 200
        json_data = response.json()
        assert json_data["success"] is True
        assert "items" in json_data["data"]
        assert "meta" in json_data["data"]
        assert "pagination" in json_data["data"]["meta"]

    @pytest.mark.asyncio
    async def test_get_projects_with_filters(self, async_client, admin_token):
        """测试带过滤条件获取项目列表"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        params = {
            "page": 1,
            "page_size": 10,
            "status": "active",
            "client_name": "测试客户"
        }

        response = await async_client.get("/api/v1/projects", params=params, headers=headers)

        assert response.status_code == 200
        json_data = response.json()
        assert json_data["success"] is True

    @pytest.mark.asyncio
    async def test_get_project_detail(self, async_client, admin_token, sample_project_id):
        """测试获取项目详情"""
        headers = {"Authorization": f"Bearer {admin_token}"}

        response = await async_client.get(f"/api/v1/projects/{sample_project_id}", headers=headers)

        assert response.status_code == 200
        json_data = response.json()
        assert json_data["success"] is True
        assert json_data["data"]["id"] == sample_project_id

    @pytest.mark.asyncio
    async def test_get_project_not_found(self, async_client, admin_token):
        """测试获取不存在的项目"""
        headers = {"Authorization": f"Bearer {admin_token}"}

        response = await async_client.get("/api/v1/projects/99999", headers=headers)

        assert response.status_code == 404
        json_data = response.json()
        assert json_data["success"] is False
        # Error code format can be SYS_004 or SYS-004
        assert json_data["error"]["code"] in ["SYS_004", "SYS-004"]

    @pytest.mark.asyncio
    async def test_update_project_success(self, async_client, admin_token, sample_project_id):
        """测试成功更新项目"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        data = {
            "name": "更新后的项目",
            "status": "active",
            "budget": "15000.00"
        }

        response = await async_client.put(f"/api/v1/projects/{sample_project_id}", json=data, headers=headers)

        assert response.status_code == 200
        json_data = response.json()
        assert json_data["success"] is True
        assert json_data["data"]["name"] == "更新后的项目"
        assert json_data["data"]["status"] == "active"
        assert json_data["data"]["budget"] == "15000.00"

    @pytest.mark.asyncio
    async def test_delete_project_success(self, async_client, admin_token, sample_project_id):
        """测试成功删除项目"""
        headers = {"Authorization": f"Bearer {admin_token}"}

        response = await async_client.delete(f"/api/v1/projects/{sample_project_id}", headers=headers)

        assert response.status_code == 204

        # 验证项目已删除
        response = await async_client.get(f"/api/v1/projects/{sample_project_id}", headers=headers)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_assign_project_member(self, async_client, admin_token, sample_project_id, media_buyer_user_id):
        """测试分配项目成员"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        data = {
            "user_id": str(media_buyer_user_id),  # UUID 转换为字符串以支持 JSON 序列化
            "role": "media_buyer"
        }

        response = await async_client.post(
            f"/api/v1/projects/{sample_project_id}/members",
            json=data,
            headers=headers
        )

        assert response.status_code == 200
        json_data = response.json()
        assert json_data["success"] is True
        # user_id 在响应中可能是字符串格式（如果 schema 接受 UUID/str）
        assert str(json_data["data"]["user_id"]) == str(media_buyer_user_id)
        assert json_data["data"]["project_role"] == "media_buyer"

    @pytest.mark.asyncio
    async def test_get_project_members(self, async_client, admin_token, sample_project_id):
        """测试获取项目成员列表"""
        headers = {"Authorization": f"Bearer {admin_token}"}

        response = await async_client.get(f"/api/v1/projects/{sample_project_id}/members", headers=headers)

        assert response.status_code == 200
        json_data = response.json()
        assert json_data["success"] is True
        assert isinstance(json_data["data"], list)

    @pytest.mark.asyncio
    async def test_remove_project_member(self, async_client, admin_token, sample_project_id, media_buyer_user_id):
        """测试移除项目成员"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # 先创建成员，确保成员存在
        member_data = {
            "user_id": str(media_buyer_user_id),
            "role": "media_buyer"
        }
        create_response = await async_client.post(
            f"/api/v1/projects/{sample_project_id}/members",
            json=member_data,
            headers=headers
        )
        # 如果成员已存在，忽略 400 错误
        assert create_response.status_code in [200, 400]

        # 然后删除成员
        response = await async_client.delete(
            f"/api/v1/projects/{sample_project_id}/members/{str(media_buyer_user_id)}",  # UUID 转换为字符串
            headers=headers
        )

        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_add_project_expense(self, async_client, admin_token, sample_project_id):
        """测试添加项目费用"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        data = {
            "expense_type": "media_spend",
            "amount": "500.00",
            "description": "Facebook广告费",
            "expense_date": date.today().isoformat()
        }

        response = await async_client.post(
            f"/api/v1/projects/{sample_project_id}/expenses",
            json=data,
            headers=headers
        )

        assert response.status_code == 200
        json_data = response.json()
        assert json_data["success"] is True
        assert json_data["data"]["expense_type"] == "media_spend"
        assert json_data["data"]["amount"] == "500.00"

    @pytest.mark.asyncio
    async def test_get_project_expenses(self, async_client, admin_token, sample_project_id):
        """测试获取项目费用列表"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        params = {"page": 1, "page_size": 10}

        response = await async_client.get(
            f"/api/v1/projects/{sample_project_id}/expenses",
            params=params,
            headers=headers
        )

        assert response.status_code == 200
        json_data = response.json()
        assert json_data["success"] is True
        assert "items" in json_data["data"]
        assert "meta" in json_data["data"]

    @pytest.mark.asyncio
    async def test_get_project_statistics(self, async_client, admin_token):
        """测试获取项目统计信息"""
        headers = {"Authorization": f"Bearer {admin_token}"}

        response = await async_client.get("/api/v1/projects/statistics", headers=headers)

        assert response.status_code == 200
        json_data = response.json()
        assert json_data["success"] is True
        assert "total_projects" in json_data["data"]
        assert "active_projects" in json_data["data"]
        assert "total_budget" in json_data["data"]
        assert "total_clients" in json_data["data"]

    @pytest.mark.asyncio
    async def test_get_project_statistics_insufficient_permissions(
        self, async_client, media_buyer_token
    ):
        """测试获取项目统计信息权限不足"""
        headers = {"Authorization": f"Bearer {media_buyer_token}"}

        response = await async_client.get("/api/v1/projects/statistics", headers=headers)

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_validation_errors(self, async_client, admin_token):
        """测试参数验证错误"""
        headers = {"Authorization": f"Bearer {admin_token}"}

        # 测试创建项目时的验证错误
        invalid_data = {
            "name": "",  # 空名称
            "client_name": "客户",
            "client_company": "公司",
            "budget": "-1000.00"  # 负数预算
        }

        response = await async_client.post("/api/v1/projects", json=invalid_data, headers=headers)

        assert response.status_code == 422
        json_data = response.json()
        assert json_data["success"] is False

    @pytest.mark.asyncio
    async def test_date_range_validation(self, async_client, admin_token):
        """测试日期范围验证"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        data = {
            "name": "项目",
            "client_name": "客户",
            "client_company": "公司",
            "start_date": "2025-12-31",
            "end_date": "2025-01-01"  # 结束日期早于开始日期
        }

        response = await async_client.post("/api/v1/projects", json=data, headers=headers)

        assert response.status_code == 400
        json_data = response.json()
        assert json_data["success"] is False
        # 检查错误消息（处理编码问题）
        error_message = json_data["error"]["message"]
        assert "日期" in error_message or "date" in error_message.lower()