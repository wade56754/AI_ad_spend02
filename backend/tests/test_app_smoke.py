"""
应用启动冒烟测试
Version: 1.0
Author: Claude Code

验证应用能够成功启动并响应基本请求
"""

import pytest


def test_app_can_start(client):
    """测试应用能够成功启动"""
    # client fixture 会创建 TestClient，如果应用启动失败会抛出异常
    assert client is not None


def test_health_endpoint_200(client):
    """测试健康检查端点返回 200"""
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    data = response.json()

    # 验证基本结构
    assert "success" in data
    assert data["success"] is True
    assert "data" in data
    assert data["data"]["status"] == "ok"


def test_healthz_endpoint_200(client):
    """测试 K8s 健康探针返回 200"""
    response = client.get("/healthz")

    assert response.status_code == 200
    data = response.json()
    assert data["data"]["status"] == "ok"


def test_api_health_fallback(client):
    """测试兼容性健康检查端点"""
    response = client.get("/api/health")

    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "healthy"


def test_404_for_nonexistent_route(client):
    """测试不存在的路由返回 404"""
    response = client.get("/nonexistent/route/12345")

    assert response.status_code == 404
