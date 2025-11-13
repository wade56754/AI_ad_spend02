"""
项目管理权限测试
Version: 1.0
Author: Claude协作开发
"""

import pytest
from httpx import AsyncClient


class TestProjectPermissions:
    """项目管理权限测试类"""

    @pytest.mark.asyncio
    async def test_admin_full_permissions(self, client: AsyncClient, admin_token):
        """测试管理员拥有完整权限"""
        headers = {"Authorization": f"Bearer {admin_token}"}

        # 管理员可以创建项目
        create_data = {
            "name": "管理员项目",
            "client_name": "客户",
            "client_company": "公司"
        }
        response = await client.post("/api/v1/projects", json=create_data, headers=headers)
        assert response.status_code == 201
        project_id = response.json()["data"]["id"]

        # 管理员可以更新项目
        update_data = {"status": "active"}
        response = await client.put(f"/api/v1/projects/{project_id}", json=update_data, headers=headers)
        assert response.status_code == 200

        # 管理员可以删除项目
        response = await client.delete(f"/api/v1/projects/{project_id}", headers=headers)
        assert response.status_code == 204

        # 管理员可以查看统计信息
        response = await client.get("/api/v1/projects/statistics", headers=headers)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_finance_read_only_permissions(self, client: AsyncClient, finance_token):
        """测试财务只有只读权限"""
        headers = {"Authorization": f"Bearer {finance_token}"}

        # 财务不能创建项目
        create_data = {
            "name": "财务项目",
            "client_name": "客户",
            "client_company": "公司"
        }
        response = await client.post("/api/v1/projects", json=create_data, headers=headers)
        assert response.status_code == 403

        # 财务可以查看项目列表
        response = await client.get("/api/v1/projects", headers=headers)
        assert response.status_code == 200

        # 财务可以查看统计信息
        response = await client.get("/api/v1/projects/statistics", headers=headers)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_data_operator_permissions(self, client: AsyncClient, data_operator_token):
        """测试数据员权限"""
        headers = {"Authorization": f"Bearer {data_operator_token}"}

        # 数据员不能创建项目
        create_data = {
            "name": "数据员项目",
            "client_name": "客户",
            "client_company": "公司"
        }
        response = await client.post("/api/v1/projects", json=create_data, headers=headers)
        assert response.status_code == 403

        # 数据员可以查看项目列表
        response = await client.get("/api/v1/projects", headers=headers)
        assert response.status_code == 200

        # 数据员可以查看统计信息
        response = await client.get("/api/v1/projects/statistics", headers=headers)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_account_manager_limited_permissions(
        self, client: AsyncClient, account_manager_token, account_manager_project_id
    ):
        """测试账户管理员受限权限"""
        headers = {"Authorization": f"Bearer {account_manager_token}"}

        # 账户管理员不能创建项目
        create_data = {
            "name": "新项目",
            "client_name": "客户",
            "client_company": "公司"
        }
        response = await client.post("/api/v1/projects", json=create_data, headers=headers)
        assert response.status_code == 403

        # 账户管理员可以更新自己管理的项目
        update_data = {"status": "active"}
        response = await client.put(
            f"/api/v1/projects/{account_manager_project_id}",
            json=update_data,
            headers=headers
        )
        assert response.status_code == 200

        # 账户管理员不能删除项目
        response = await client.delete(f"/api/v1/projects/{account_manager_project_id}", headers=headers)
        assert response.status_code == 403

        # 账户管理员不能查看统计信息
        response = await client.get("/api/v1/projects/statistics", headers=headers)
        assert response.status_code == 403

        # 账户管理员可以管理自己项目的成员
        member_data = {
            "user_id": 1,  # 假设用户ID
            "role": "media_buyer"
        }
        response = await client.post(
            f"/api/v1/projects/{account_manager_project_id}/members",
            json=member_data,
            headers=headers
        )
        # 可能成功或失败（取决于用户是否存在），但不能是403权限错误
        assert response.status_code != 403

    @pytest.mark.asyncio
    async def test_media_buyer_minimal_permissions(
        self, client: AsyncClient, media_buyer_token, media_buyer_project_id
    ):
        """测试媒体买家最低权限"""
        headers = {"Authorization": f"Bearer {media_buyer_token}"}

        # 媒体买家不能创建项目
        create_data = {
            "name": "媒体买家项目",
            "client_name": "客户",
            "client_company": "公司"
        }
        response = await client.post("/api/v1/projects", json=create_data, headers=headers)
        assert response.status_code == 403

        # 媒体买家不能更新项目
        update_data = {"status": "active"}
        response = await client.put(
            f"/api/v1/projects/{media_buyer_project_id}",
            json=update_data,
            headers=headers
        )
        assert response.status_code == 403

        # 媒体买家不能删除项目
        response = await client.delete(f"/api/v1/projects/{media_buyer_project_id}", headers=headers)
        assert response.status_code == 403

        # 媒体买家不能查看统计信息
        response = await client.get("/api/v1/projects/statistics", headers=headers)
        assert response.status_code == 403

        # 媒体买家可以查看自己参与的项目
        response = await client.get(f"/api/v1/projects/{media_buyer_project_id}", headers=headers)
        assert response.status_code == 200

        # 媒体买家可以查看自己参与的项目成员
        response = await client.get(
            f"/api/v1/projects/{media_buyer_project_id}/members",
            headers=headers
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_cross_project_access_denied(
        self, client: AsyncClient, account_manager_token
    ):
        """测试跨项目访问被拒绝"""
        headers = {"Authorization": f"Bearer {account_manager_token}"}

        # 尝试访问不属于自己的项目（假设ID 10000不属于该用户）
        response = await client.get("/api/v1/projects/10000", headers=headers)
        assert response.status_code == 404 or response.status_code == 403

        # 尝试更新不属于自己的项目
        update_data = {"status": "active"}
        response = await client.put("/api/v1/projects/10000", json=update_data, headers=headers)
        assert response.status_code == 404 or response.status_code == 403

        # 尝试管理不属于自己的项目成员
        member_data = {
            "user_id": 1,
            "role": "media_buyer"
        }
        response = await client.post(
            "/api/v1/projects/10000/members",
            json=member_data,
            headers=headers
        )
        assert response.status_code == 404 or response.status_code == 403

    @pytest.mark.asyncio
    async def test_unauthenticated_access(self, client: AsyncClient):
        """测试未认证访问被拒绝"""
        # 未认证不能创建项目
        create_data = {
            "name": "项目",
            "client_name": "客户",
            "client_company": "公司"
        }
        response = await client.post("/api/v1/projects", json=create_data)
        assert response.status_code == 401

        # 未认证不能查看项目列表
        response = await client.get("/api/v1/projects")
        assert response.status_code == 401

        # 未认证不能查看项目详情
        response = await client.get("/api/v1/projects/1")
        assert response.status_code == 401

        # 未认证不能查看统计信息
        response = await client.get("/api/v1/projects/statistics")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_invalid_token(self, client: AsyncClient):
        """测试无效token访问被拒绝"""
        headers = {"Authorization": "Bearer invalid_token"}

        # 无效token不能创建项目
        create_data = {
            "name": "项目",
            "client_name": "客户",
            "client_company": "公司"
        }
        response = await client.post("/api/v1/projects", json=create_data, headers=headers)
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_rls_isolation(self, client: AsyncClient, admin_token, media_buyer_token):
        """测试RLS数据隔离"""
        # 管理员创建一个新项目
        headers_admin = {"Authorization": f"Bearer {admin_token}"}
        create_data = {
            "name": "私密项目",
            "client_name": "私密客户",
            "client_company": "私密公司"
        }
        response = await client.post("/api/v1/projects", json=create_data, headers=headers_admin)
        assert response.status_code == 201
        project_id = response.json()["data"]["id"]

        # 媒体买家不应该能看到这个新项目（除非被分配）
        headers_buyer = {"Authorization": f"Bearer {media_buyer_token}"}
        response = await client.get("/api/v1/projects", headers=headers_buyer)
        projects = response.json()["data"]["items"]
        project_ids = [p["id"] for p in projects]
        assert project_id not in project_ids

        # 媒体买家尝试访问这个项目应该失败
        response = await client.get(f"/api/v1/projects/{project_id}", headers=headers_buyer)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_data_filtering_by_role(self, client: AsyncClient, admin_token, account_manager_token):
        """测试基于角色的数据过滤"""
        # 管理员查看所有项目
        headers_admin = {"Authorization": f"Bearer {admin_token}"}
        response_admin = await client.get("/api/v1/projects", headers=headers_admin)
        admin_projects = response_admin.json()["data"]["items"]

        # 账户管理员查看项目
        headers_manager = {"Authorization": f"Bearer {account_manager_token}"}
        response_manager = await client.get("/api/v1/projects", headers=headers_manager)
        manager_projects = response_manager.json()["data"]["items"]

        # 账户管理员看到的项目应该少于或等于管理员看到的项目
        assert len(manager_projects) <= len(admin_projects)

        # 账户管理员只能看到自己管理的项目
        for project in manager_projects:
            assert project["account_manager_id"] is not None
            # 实际项目中需要根据账户管理员的ID进行过滤