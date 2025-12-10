"""
渠道管理 API 测试
Version: 1.0
Author: Claude Code (AI 代码工厂)

SoT References:
- API_SOT.md v9.0 第5章 Channels API
- AUTH_SPEC.md v2.0 (角色权限)
"""

import pytest
from uuid import uuid4
from decimal import Decimal


class TestChannelsList:
    """渠道列表 API 测试"""

    def test_list_channels_success(self, client, auth_headers, test_channel):
        """测试获取渠道列表 - 成功"""
        response = client.get("/api/v1/channels/", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert isinstance(data["data"], list)
        assert len(data["data"]) >= 1

        # 验证分页元数据
        assert "meta" in data
        assert "pagination" in data["meta"]
        pagination = data["meta"]["pagination"]
        assert "page" in pagination
        assert "page_size" in pagination
        assert "total" in pagination

    def test_list_channels_with_pagination(self, client, auth_headers, test_channel):
        """测试获取渠道列表 - 分页"""
        response = client.get(
            "/api/v1/channels/",
            params={"page": 1, "page_size": 10},
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        pagination = data["meta"]["pagination"]
        assert pagination["page"] == 1
        assert pagination["page_size"] == 10

    def test_list_channels_filter_by_active(self, client, auth_headers, test_channel):
        """测试获取渠道列表 - 按激活状态过滤"""
        response = client.get(
            "/api/v1/channels/",
            params={"is_active": True},
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        # 所有返回的渠道应该都是激活状态
        for channel in data["data"]:
            assert channel.get("is_active", True) is True

    def test_list_channels_search(self, client, auth_headers, test_channel):
        """测试获取渠道列表 - 搜索"""
        response = client.get(
            "/api/v1/channels/",
            params={"search": "Facebook"},
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        # 搜索结果应该包含匹配的渠道
        assert data["success"] is True

    def test_list_channels_unauthorized(self, client):
        """测试获取渠道列表 - 未授权"""
        response = client.get("/api/v1/channels/")

        assert response.status_code == 401


class TestChannelGet:
    """渠道详情 API 测试"""

    def test_get_channel_success(self, client, auth_headers, test_channel):
        """测试获取渠道详情 - 成功"""
        response = client.get(
            f"/api/v1/channels/{test_channel.id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data

        channel_data = data["data"]
        assert channel_data["id"] == str(test_channel.id)
        assert channel_data["name"] == test_channel.name

    def test_get_channel_not_found(self, client, auth_headers):
        """测试获取渠道详情 - 不存在"""
        fake_id = uuid4()
        response = client.get(
            f"/api/v1/channels/{fake_id}",
            headers=auth_headers
        )

        assert response.status_code == 404

    def test_get_channel_unauthorized(self, client, test_channel):
        """测试获取渠道详情 - 未授权"""
        response = client.get(f"/api/v1/channels/{test_channel.id}")

        assert response.status_code == 401


class TestChannelCreate:
    """渠道创建 API 测试"""

    def test_create_channel_success(self, client, admin_headers, admin_user):
        """测试创建渠道 - 成功"""
        channel_data = {
            "name": "TikTok Ads",
            "service_fee_type": "percent",
            "service_fee_value": "5.00",
            "is_active": True,
            "created_by": str(admin_user.id)
        }

        response = client.post(
            "/api/v1/channels/",
            json=channel_data,
            headers=admin_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "TikTok Ads"

    def test_create_channel_missing_name(self, client, admin_headers, admin_user):
        """测试创建渠道 - 缺少名称"""
        channel_data = {
            "service_fee_type": "percent",
            "created_by": str(admin_user.id)
        }

        response = client.post(
            "/api/v1/channels/",
            json=channel_data,
            headers=admin_headers
        )

        assert response.status_code == 422  # Validation error

    def test_create_channel_unauthorized(self, client):
        """测试创建渠道 - 未授权"""
        channel_data = {
            "name": "Test Channel"
        }

        response = client.post("/api/v1/channels/", json=channel_data)

        assert response.status_code == 401


class TestChannelUpdate:
    """渠道更新 API 测试"""

    def test_update_channel_success(self, client, admin_headers, test_channel, admin_user):
        """测试更新渠道 - 成功"""
        update_data = {
            "name": "Facebook Ads Updated",
            "updated_by": str(admin_user.id)
        }

        response = client.put(
            f"/api/v1/channels/{test_channel.id}",
            json=update_data,
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "Facebook Ads Updated"

    def test_update_channel_partial(self, client, admin_headers, test_channel, admin_user):
        """测试更新渠道 - 部分更新"""
        update_data = {
            "is_active": False,
            "updated_by": str(admin_user.id)
        }

        response = client.put(
            f"/api/v1/channels/{test_channel.id}",
            json=update_data,
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["is_active"] is False

    def test_update_channel_not_found(self, client, admin_headers, admin_user):
        """测试更新渠道 - 不存在"""
        fake_id = uuid4()
        update_data = {
            "name": "Updated Name",
            "updated_by": str(admin_user.id)
        }

        response = client.put(
            f"/api/v1/channels/{fake_id}",
            json=update_data,
            headers=admin_headers
        )

        assert response.status_code == 404

    def test_update_channel_unauthorized(self, client, test_channel):
        """测试更新渠道 - 未授权"""
        update_data = {"name": "Updated Name"}

        response = client.put(
            f"/api/v1/channels/{test_channel.id}",
            json=update_data
        )

        assert response.status_code == 401
