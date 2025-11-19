"""
健康检查 API 测试
Version: 1.0
Author: Claude Code
"""

import pytest
from fastapi.testclient import TestClient


def test_health_check(client):
    """测试健康检查端点"""
    response = client.get("/api/v1/health")

    assert response.status_code == 200

    # 验证响应结构
    data = response.json()
    assert "success" in data
    assert data["success"] is True

    assert "data" in data
    assert "status" in data["data"]
    assert data["data"]["status"] == "ok"

    assert "service" in data["data"]
    assert data["data"]["service"] == "ai-ad-spend-backend"

    assert "version" in data["data"]
    assert "timestamp" in data["data"]

    assert "message" in data
    assert data["message"] == "Health check passed"


def test_healthz_endpoint(client):
    """测试 Kubernetes 兼容的 healthz 端点"""
    response = client.get("/healthz")

    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert data["data"]["status"] == "ok"
    assert "timestamp" in data["data"]


def test_readyz_endpoint(client):
    """测试 Kubernetes 兼容的 readyz 端点"""
    response = client.get("/readyz")

    # readyz 端点在测试环境可能返回 503（数据库未连接）
    # 我们只验证它返回了有效的响应
    assert response.status_code in [200, 503]

    data = response.json()
    # 503 时 success 为 False
    if response.status_code == 200:
        assert data["success"] is True
        assert data["data"]["status"] == "ok"
        assert data["data"]["checks"]["database"] == "ok"
    else:
        assert data["success"] is False
