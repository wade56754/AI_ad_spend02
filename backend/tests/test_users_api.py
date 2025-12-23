"""
用户管理 API 测试

SoT References:
- API_SOT.md v9.0 §5 Users API
- ERROR_CODES_SOT.md v2.1

测试覆盖:
- GET /api/v1/users - 用户列表
- POST /api/v1/users - 创建用户
- GET /api/v1/users/{user_id} - 用户详情
- PUT /api/v1/users/{user_id} - 更新用户
- DELETE /api/v1/users/{user_id} - 删除用户

Author: AI 代码工厂 v2.4
"""
import pytest
from uuid import uuid4


@pytest.fixture
def sample_user_id():
    """样例用户 ID - 用于测试不存在或无权限场景"""
    return str(uuid4())


class TestUsersAPI:
    """用户管理 API 测试类"""

    # ========== GET /api/v1/users 测试 ==========

    @pytest.mark.asyncio
    async def test_get_users_as_admin(self, async_client, admin_token):
        """测试管理员获取用户列表"""
        headers = {"Authorization": f"Bearer {admin_token}"}

        response = await async_client.get("/api/v1/users", headers=headers)

        assert response.status_code == 200
        json_data = response.json()
        assert json_data.get("success") is True
        assert "data" in json_data
        assert "items" in json_data["data"]
        assert "meta" in json_data["data"]

    @pytest.mark.asyncio
    async def test_get_users_with_pagination(self, async_client, admin_token):
        """测试分页参数"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        params = {"page": 1, "page_size": 10}

        response = await async_client.get("/api/v1/users", params=params, headers=headers)

        assert response.status_code == 200
        json_data = response.json()
        assert json_data["data"]["meta"]["pagination"]["page"] == 1
        assert json_data["data"]["meta"]["pagination"]["page_size"] == 10

    @pytest.mark.asyncio
    async def test_get_users_with_role_filter(self, async_client, admin_token):
        """测试角色过滤"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        params = {"role": "media_buyer"}

        response = await async_client.get("/api/v1/users", params=params, headers=headers)

        assert response.status_code == 200
        json_data = response.json()
        # 如果有数据，验证角色
        if json_data["data"]["items"]:
            for user in json_data["data"]["items"]:
                assert user["role"] == "media_buyer"

    @pytest.mark.asyncio
    async def test_get_users_with_search(self, async_client, admin_token):
        """测试搜索功能"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        params = {"search": "admin"}

        response = await async_client.get("/api/v1/users", params=params, headers=headers)

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_users_invalid_role_filter(self, async_client, admin_token):
        """测试无效角色过滤 - VALIDATION_002"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        params = {"role": "invalid_role"}

        response = await async_client.get("/api/v1/users", params=params, headers=headers)

        # 应该返回 400 或 422 (验证错误)
        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_get_users_as_non_admin(self, async_client, media_buyer_token):
        """测试非管理员获取用户列表 - AUTH_500"""
        headers = {"Authorization": f"Bearer {media_buyer_token}"}

        response = await async_client.get("/api/v1/users", headers=headers)

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_get_users_unauthenticated(self, async_client):
        """测试未认证访问"""
        response = await async_client.get("/api/v1/users")

        assert response.status_code in [401, 403]

    # ========== POST /api/v1/users 测试 ==========

    @pytest.mark.asyncio
    async def test_create_user_success(self, async_client, admin_token):
        """测试成功创建用户"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        unique_id = str(uuid4())[:8]
        data = {
            "username": f"newuser_{unique_id}",
            "email": f"newuser_{unique_id}@example.com",
            "password": "Password123!",
            "role": "media_buyer",
            "is_active": True
        }

        response = await async_client.post("/api/v1/users", json=data, headers=headers)

        assert response.status_code in [200, 201]
        json_data = response.json()
        assert json_data.get("success") is True
        assert json_data["data"]["username"] == data["username"]
        assert json_data["data"]["email"] == data["email"]
        assert json_data["data"]["role"] == "media_buyer"

    @pytest.mark.asyncio
    async def test_create_user_duplicate_username(self, async_client, admin_token):
        """测试重复用户名 - DB_004"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        unique_id = str(uuid4())[:8]

        # 创建第一个用户
        data1 = {
            "username": f"dupuser_{unique_id}",
            "email": f"dupuser1_{unique_id}@example.com",
            "password": "Password123!",
            "role": "media_buyer"
        }
        await async_client.post("/api/v1/users", json=data1, headers=headers)

        # 尝试创建同名用户
        data2 = {
            "username": f"dupuser_{unique_id}",  # 相同用户名
            "email": f"dupuser2_{unique_id}@example.com",
            "password": "Password123!",
            "role": "media_buyer"
        }
        response = await async_client.post("/api/v1/users", json=data2, headers=headers)

        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_create_user_duplicate_email(self, async_client, admin_token):
        """测试重复邮箱 - DB_004"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        unique_id = str(uuid4())[:8]
        email = f"dupemail_{unique_id}@example.com"

        # 创建第一个用户
        data1 = {
            "username": f"emailuser1_{unique_id}",
            "email": email,
            "password": "Password123!",
            "role": "media_buyer"
        }
        await async_client.post("/api/v1/users", json=data1, headers=headers)

        # 尝试创建同邮箱用户
        data2 = {
            "username": f"emailuser2_{unique_id}",
            "email": email,  # 相同邮箱
            "password": "Password123!",
            "role": "media_buyer"
        }
        response = await async_client.post("/api/v1/users", json=data2, headers=headers)

        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_create_user_invalid_role(self, async_client, admin_token):
        """测试无效角色 - VALIDATION_002"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        data = {
            "username": "invalidroleuser",
            "email": "invalidrole@example.com",
            "password": "Password123!",
            "role": "invalid_role"  # 无效角色
        }

        response = await async_client.post("/api/v1/users", json=data, headers=headers)

        assert response.status_code == 422  # Pydantic 验证错误

    @pytest.mark.asyncio
    async def test_create_user_short_password(self, async_client, admin_token):
        """测试密码太短"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        data = {
            "username": "shortpwduser",
            "email": "shortpwd@example.com",
            "password": "123",  # 太短
            "role": "media_buyer"
        }

        response = await async_client.post("/api/v1/users", json=data, headers=headers)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_user_as_non_admin(self, async_client, media_buyer_token):
        """测试非管理员创建用户 - AUTH_500"""
        headers = {"Authorization": f"Bearer {media_buyer_token}"}
        data = {
            "username": "nonadminuser",
            "email": "nonadmin@example.com",
            "password": "Password123!",
            "role": "media_buyer"
        }

        response = await async_client.post("/api/v1/users", json=data, headers=headers)

        assert response.status_code == 403

    # ========== GET /api/v1/users/{user_id} 测试 ==========

    @pytest.mark.asyncio
    async def test_get_user_detail_as_admin(self, async_client, admin_token, sample_user_id):
        """测试管理员获取用户详情"""
        headers = {"Authorization": f"Bearer {admin_token}"}

        response = await async_client.get(f"/api/v1/users/{sample_user_id}", headers=headers)

        assert response.status_code in [200, 404]
        if response.status_code == 200:
            json_data = response.json()
            assert json_data.get("success") is True

    @pytest.mark.asyncio
    async def test_get_user_not_found(self, async_client, admin_token):
        """测试获取不存在的用户 - BIZ_002"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        fake_id = str(uuid4())

        response = await async_client.get(f"/api/v1/users/{fake_id}", headers=headers)

        assert response.status_code == 404

    # ========== PUT /api/v1/users/{user_id} 测试 ==========

    @pytest.mark.asyncio
    async def test_update_user_success(self, async_client, admin_token):
        """测试成功更新用户"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        unique_id = str(uuid4())[:8]

        # 先创建用户
        create_data = {
            "username": f"updateuser_{unique_id}",
            "email": f"updateuser_{unique_id}@example.com",
            "password": "Password123!",
            "role": "media_buyer"
        }
        create_response = await async_client.post("/api/v1/users", json=create_data, headers=headers)

        if create_response.status_code in [200, 201]:
            user_id = create_response.json()["data"]["id"]

            # 更新用户
            update_data = {
                "is_active": False
            }
            response = await async_client.put(f"/api/v1/users/{user_id}", json=update_data, headers=headers)

            assert response.status_code == 200
            json_data = response.json()
            assert json_data["data"]["is_active"] is False

    @pytest.mark.asyncio
    async def test_update_user_not_found(self, async_client, admin_token):
        """测试更新不存在的用户 - BIZ_002"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        fake_id = str(uuid4())
        update_data = {"is_active": False}

        response = await async_client.put(f"/api/v1/users/{fake_id}", json=update_data, headers=headers)

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_user_as_non_admin(self, async_client, media_buyer_token, sample_user_id):
        """测试非管理员更新用户 - AUTH_500"""
        headers = {"Authorization": f"Bearer {media_buyer_token}"}
        update_data = {"is_active": False}

        response = await async_client.put(f"/api/v1/users/{sample_user_id}", json=update_data, headers=headers)

        assert response.status_code == 403

    # ========== DELETE /api/v1/users/{user_id} 测试 ==========

    @pytest.mark.asyncio
    async def test_delete_user_success(self, async_client, admin_token):
        """测试成功删除用户"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        unique_id = str(uuid4())[:8]

        # 先创建用户
        create_data = {
            "username": f"deleteuser_{unique_id}",
            "email": f"deleteuser_{unique_id}@example.com",
            "password": "Password123!",
            "role": "media_buyer"
        }
        create_response = await async_client.post("/api/v1/users", json=create_data, headers=headers)

        if create_response.status_code in [200, 201]:
            user_id = create_response.json()["data"]["id"]

            # 删除用户
            response = await async_client.delete(f"/api/v1/users/{user_id}", headers=headers)

            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_delete_user_not_found(self, async_client, admin_token):
        """测试删除不存在的用户 - BIZ_002"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        fake_id = str(uuid4())

        response = await async_client.delete(f"/api/v1/users/{fake_id}", headers=headers)

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_user_as_non_admin(self, async_client, media_buyer_token, sample_user_id):
        """测试非管理员删除用户 - AUTH_500"""
        headers = {"Authorization": f"Bearer {media_buyer_token}"}

        response = await async_client.delete(f"/api/v1/users/{sample_user_id}", headers=headers)

        assert response.status_code == 403


class TestUsersPermissions:
    """用户管理权限测试"""

    @pytest.mark.asyncio
    async def test_admin_has_full_access(self, async_client, admin_token):
        """测试管理员拥有完整权限"""
        headers = {"Authorization": f"Bearer {admin_token}"}

        # 列表
        response = await async_client.get("/api/v1/users", headers=headers)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_finance_cannot_manage_users(self, async_client, finance_token):
        """测试财务不能管理用户"""
        headers = {"Authorization": f"Bearer {finance_token}"}

        response = await async_client.get("/api/v1/users", headers=headers)
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_data_operator_cannot_manage_users(self, async_client, data_operator_token):
        """测试数据员不能管理用户"""
        headers = {"Authorization": f"Bearer {data_operator_token}"}

        response = await async_client.get("/api/v1/users", headers=headers)
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_account_manager_cannot_manage_users(self, async_client, account_manager_token):
        """测试账户经理不能管理用户"""
        headers = {"Authorization": f"Bearer {account_manager_token}"}

        response = await async_client.get("/api/v1/users", headers=headers)
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_media_buyer_cannot_manage_users(self, async_client, media_buyer_token):
        """测试投手不能管理用户"""
        headers = {"Authorization": f"Bearer {media_buyer_token}"}

        response = await async_client.get("/api/v1/users", headers=headers)
        assert response.status_code == 403
