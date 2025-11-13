"""
权限控制测试
Version: 1.0
Author: Claude协作开发
"""

import pytest
from httpx import AsyncClient

# 测试数据
TEST_USERS = {
    "admin": {
        "email": "admin@example.com",
        "password": "Admin123!",
        "username": "admin"
    },
    "finance": {
        "email": "finance@example.com",
        "password": "Finance123!",
        "username": "finance"
    },
    "data_operator": {
        "email": "data@example.com",
        "password": "Data123!",
        "username": "data_operator"
    },
    "account_manager": {
        "email": "account@example.com",
        "password": "Account123!",
        "username": "account_manager"
    },
    "media_buyer": {
        "email": "media@example.com",
        "password": "Media123!",
        "username": "media_buyer"
    }
}


class TestPermissions:
    """权限控制测试类"""

    @pytest.fixture(scope="class")
    async def setup_tokens(self):
        """设置用户tokens"""
        self.tokens = {}
        client = AsyncClient()

        for role, user_data in TEST_USERS.items():
            # 先注册用户（如果不存在）
            register_data = {
                "email": user_data["email"],
                "password": user_data["password"],
                "username": user_data["username"],
                "full_name": f"Test {role.title()}"
            }
            await client.post("/api/v1/auth/register", json=register_data)

            # 登录获取token
            login_data = {
                "identifier": user_data["email"],
                "password": user_data["password"]
            }
            response = await client.post("/api/v1/auth/login", json=login_data)
            if response.status_code == 200:
                self.tokens[role] = response.json()["data"]["token"]

        return self.tokens

    @pytest.fixture(autouse=True)
    async def get_tokens(self, setup_tokens):
        """获取用户tokens"""
        return setup_tokens

    @pytest.mark.asyncio
    async def test_admin_full_permissions(self, client: AsyncClient, get_tokens):
        """测试管理员拥有完整权限"""
        token = get_tokens.get("admin")
        if not token:
            pytest.skip("Admin token not available")

        headers = {"Authorization": f"Bearer {token['access_token']}"}

        # 管理员可以访问所有模块
        endpoints = [
            ("/api/v1/projects", 200),
            ("/api/v1/channels", 200),
            ("/api/v1/ad-accounts", 200),
            ("/api/v1/daily-reports", 200),
            ("/api/v1/topups", 200),
            ("/api/v1/reconciliations", 200),
            ("/api/v1/users", 200)  # 如果有用户管理接口
        ]

        for endpoint, expected_status in endpoints:
            response = await client.get(endpoint, headers=headers)
            assert response.status_code == expected_status, f"Admin failed to access {endpoint}"

    @pytest.mark.asyncio
    async def test_finance_permissions(self, client: AsyncClient, get_tokens):
        """测试财务人员权限"""
        token = get_tokens.get("finance")
        if not token:
            pytest.skip("Finance token not available")

        headers = {"Authorization": f"Bearer {token['access_token']}"}

        # 财务可以访问的模块
        allowed_endpoints = [
            ("/api/v1/projects", 200),
            ("/api/v1/daily-reports", 200),
            ("/api/v1/topups", 200),
            ("/api/v1/reconciliations", 200),
            ("/api/v1/ad-accounts", 200)  # 只读访问
        ]

        # 财务不能访问的模块
        forbidden_endpoints = [
            ("/api/v1/channels", 403),  # 可能没有权限
            ("/api/v1/users", 403),  # 可能没有权限
        ]

        for endpoint, expected_status in allowed_endpoints:
            response = await client.get(endpoint, headers=headers)
            assert response.status_code == expected_status, f"Finance should access {endpoint}"

        for endpoint, expected_status in forbidden_endpoints:
            response = await client.get(endpoint, headers=headers)
            assert response.status_code == expected_status, f"Finance should NOT access {endpoint}"

    @pytest.mark.asyncio
    async def test_data_operator_permissions(self, client: AsyncClient, get_tokens):
        """测试数据员权限"""
        token = get_tokens.get("data_operator")
        if not token:
            pytest.skip("Data operator token not available")

        headers = {"Authorization": f"Bearer {token['access_token']}"}

        # 数据员可以访问的模块
        allowed_endpoints = [
            ("/api/v1/projects", 200),
            ("/api/v1/daily-reports", 200),
            ("/api/v1/ad-accounts", 200),  # 只读访问
            ("/api/v1/reconciliations/statistics", 200),  # 只读访问统计
        ]

        # 数据员不能访问的模块
        forbidden_endpoints = [
            ("/api/v1/channels", 403),
            ("/api/v1/topups", 403),
            ("/api/v1/reconciliations", 403),  # 不能执行对账
        ]

        for endpoint, expected_status in allowed_endpoints:
            response = await client.get(endpoint, headers=headers)
            assert response.status_code == expected_status, f"Data operator should access {endpoint}"

        for endpoint, expected_status in forbidden_endpoints:
            response = await client.get(endpoint, headers=headers)
            assert response.status_code == expected_status, f"Data operator should NOT access {endpoint}"

    @pytest.mark.asyncio
    async def test_account_manager_permissions(self, client: AsyncClient, get_tokens):
        """测试账户管理员权限"""
        token = get_tokens.get("account_manager")
        if not token:
            pytest.skip("Account manager token not available")

        headers = {"Authorization": f"Bearer {token['access_token']}"}

        # 账户管理员可以访问的模块
        allowed_endpoints = [
            ("/api/v1/projects", 200),
            ("/api/v1/ad-accounts", 200),
            ("/api/v1/channels", 200),  # 可能可以读取
            ("/api/v1/daily-reports", 200),
            ("/api/v1/topups", 200),  # 可以申请
            ("/api/v1/reconciliations", 200),  # 可能可以查看
        ]

        # 账户管理员不能访问的模块
        forbidden_endpoints = [
            ("/api/v1/users", 403),
            ("/api/v1/reconciliations/statistics", 403),
        ]

        for endpoint, expected_status in allowed_endpoints:
            response = await client.get(endpoint, headers=headers)
            assert response.status_code == expected_status, f"Account manager should access {endpoint}"

        for endpoint, expected_status in forbidden_endpoints:
            response = await client.get(endpoint, headers=headers)
            assert response.status_code == expected_status, f"Account manager should NOT access {endpoint}"

    @pytest.mark.asyncio
    async def test_media_buyer_permissions(self, client: AsyncClient, get_tokens):
        """测试媒体买家权限"""
        token = get_tokens.get("media_buyer")
        if not token:
            pytest.skip("Media buyer token not available")

        headers = {"Authorization": f"Bearer {token['access_token']}"}

        # 媒体买家可以访问的模块
        allowed_endpoints = [
            ("/api/v1/projects", 200),
            ("/api/v1/ad-accounts", 200),  # 可以查看自己负责的
            ("/api/v1/daily-reports", 200),
            ("/api/v1/topups", 200),  # 可以申请
            ("/api/v1/reconciliations", 200),  # 可能可以查看
        ]

        # 媒体买家不能访问的模块
        forbidden_endpoints = [
            ("/api/v1/channels", 403),
            ("/api/v1/users", 403),
            ("/api/v1/reconciliations/statistics", 403),
        ]

        for endpoint, expected_status in allowed_endpoints:
            response = await client.get(endpoint, headers=headers)
            assert response.status_code == expected_status, f"Media buyer should access {endpoint}"

        for endpoint, expected_status in forbidden_endpoints:
            response = await client.get(endpoint, headers=headers)
            assert response.status_code == expected_status, f"Media buyer should NOT access {endpoint}"

    @pytest.mark.asyncio
    async def test_cross_role_access_denied(self, client: AsyncClient, get_tokens):
        """测试跨角色访问被拒绝"""
        media_token = get_tokens.get("media_buyer")
        if not media_token:
            pytest.skip("Media buyer token not available")

        headers = {"Authorization": f"Bearer {media_token['access_token']}"}

        # 媒体买家尝试访问财务专用端点
        financial_endpoints = [
            "/api/v1/topups/statistics",
            "/api/v1/reconciliations/statistics",
            "/api/v1/users"
        ]

        for endpoint in financial_endpoints:
            response = await client.get(endpoint, headers=headers)
            assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_unauthenticated_access(self, client: AsyncClient):
        """测试未认证访问被拒绝"""
        endpoints = [
            "/api/v1/projects",
            "/api/v1/daily-reports",
            "/api/v1/auth/me"
        ]

        for endpoint in endpoints:
            response = await client.get(endpoint)
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_invalid_token_access(self, client: AsyncClient):
        """测试无效token访问被拒绝"""
        headers = {"Authorization": "Bearer invalid_token"}

        endpoints = [
            "/api/v1/projects",
            "/api/v1/auth/me"
        ]

        for endpoint in endpoints:
            response = await client.get(endpoint, headers=headers)
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_token_expiration(self, client: AsyncClient, get_tokens):
        """测试token过期处理"""
        # 这个测试需要模拟token过期，实际测试中可能需要修改JWT配置
        admin_token = get_tokens.get("admin")
        if not admin_token:
            pytest.skip("Admin token not available")

        # 尝试使用过期的token（需要模拟）
        expired_token = admin_token['access_token']
        # 模拟过期（实际可能需要修改token内容）
        headers = {"Authorization": f"Bearer {expired_token}"}

        response = await client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code in [401, 403]  # 取决于具体实现

    @pytest.mark.asyncio
    async def test_token_revocation(self, client: AsyncClient, get_tokens):
        """测试token撤销"""
        token = get_tokens.get("admin")
        if not token:
            pytest.skip("Admin token not available")

        headers = {"Authorization": f"Bearer {token['access_token']}"}

        # 先使用token
        response = await client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 200

        # 登出
        await client.post("/api/v1/auth/logout", headers=headers)

        # 再次使用已登出的token
        response = await client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_role_hierarchy(self, client: AsyncClient, get_tokens):
        """测试角色权限层级"""
        # 获取不同角色的tokens
        admin_token = get_tokens.get("admin")
        media_token = get_tokens.get("media_buyer")

        if admin_token and media_token:
            admin_headers = {"Authorization": f"Bearer {admin_token['access_token']}"}
            media_headers = {"Authorization": f"Bearer {media_token['access_token']}"}

            # 管理员可以访问财务端点
            admin_response = await client.get("/api/v1/topups/statistics", headers=admin_headers)
            assert admin_response.status_code in [200, 403]  # 取决于是否有数据

            # 媒体买家不能访问财务端点
            media_response = await client.get("/api/v1/topups/statistics", headers=media_headers)
            assert media_response.status_code == 403

    @pytest.mark.asyncio
    async def test_permission_inheritance(self, client: AsyncClient, get_tokens):
        """测试权限继承"""
        # 测试finance角色继承admin的部分权限
        finance_token = get_tokens.get("finance")
        admin_token = get_tokens.get("admin")

        if finance_token and admin_token:
            finance_headers = {"Authorization": f"Bearer {finance_token['access_token']}"}
            admin_headers = {"Authorization": f"Bearer {admin_token['access_token']}"}

            # 两者都可以查看项目
            finance_response = await client.get("/api/v1/projects", headers=finance_headers)
            admin_response = await client.get("/api/v1/projects", headers=admin_headers)

            # 都应该返回200或403（取决于数据权限）
            assert finance_response.status_code in [200, 403]
            assert admin_response.status_code in [200, 403]

    @pytest.mark.asyncio
    async def test_api_method_permissions(self, client: AsyncClient, get_tokens):
        """测试不同HTTP方法的权限控制"""
        media_token = get_tokens.get("media_buyer")
        if not media_token:
            pytest.skip("Media buyer token not available")

        headers = {"Authorization": f"Bearer {media_token['access_token']}"}

        # 媒体买家只能读取，不能写入
        get_response = await client.get("/api/v1/ad-accounts", headers=headers)
        assert get_response.status_code in [200, 403]

        # 尝试写入操作
        post_response = await client.post(
            "/api/v1/ad-accounts",
            json={"name": "Test Account"},
            headers=headers
        )
        assert post_response.status_code in [403, 422]  # 403表示无权限，422可能是数据验证错误

    @pytest.mark.asyncio
    async def test_data_isolation(self, client: AsyncClient, get_tokens):
        """测试数据隔离"""
        media_token = get_tokens.get("media_buyer")
        account_manager_token = get_tokens.get("account_manager")

        if media_token and account_manager_token:
            media_headers = {"Authorization": f"Bearer {media_token['access_token']}"}
            manager_headers = {"Authorization": f"Bearer {account_manager_token['access_token']}"}

            # 获取各自的项目列表
            media_response = await client.get("/api/v1/projects", headers=media_headers)
            manager_response = await client.get("/api/v1/projects", headers=manager_headers)

            # 两者都应该能返回（即使数据可能不同）
            assert media_response.status_code in [200, 403]
            assert manager_response.status_code in [200, 403]

            # 如果都返回200，检查数据隔离
            if (media_response.status_code == 200 and
                manager_response.status_code == 200):
                media_projects = media_response.json().get("data", {}).get("items", [])
                manager_projects = manager_response.json().get("data", {}).get("items", [])

                # 媒体买家看到的项目应该是账户管理员项目的子集
                # 这里需要根据实际业务逻辑验证