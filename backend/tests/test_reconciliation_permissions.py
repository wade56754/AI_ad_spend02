"""
对账管理权限测试
Version: 2.0 (Test Fixture & Architecture Repair Flow)
Author: Claude协作开发

修复内容:
- P0-RP-001: 将 async 测试转换为 sync 风格，使用 TestClient
- P1-RP-001: 使用 conftest.py 定义的 auth_headers fixtures
"""

import pytest
from fastapi.testclient import TestClient


class TestReconciliationPermissions:
    """对账管理权限测试类"""

    def test_admin_full_permissions(self, client, auth_headers_admin):
        """测试管理员拥有完整权限"""
        # 管理员可以查看所有对账批次
        response = client.get("/api/v1/reconciliations", headers=auth_headers_admin)
        assert response.status_code == 200

        # 管理员可以创建对账批次
        data = {
            "reconciliation_date": "2025-11-10",
            "auto_match": True,
            "notes": "管理员创建的测试批次"
        }
        response = client.post("/api/v1/reconciliations/batches", json=data, headers=auth_headers_admin)
        assert response.status_code == 200

        # 管理员可以查看统计
        response = client.get("/api/v1/reconciliations/statistics", headers=auth_headers_admin)
        assert response.status_code == 200

        # 管理员可以导出数据
        response = client.get("/api/v1/reconciliations/export", headers=auth_headers_admin)
        assert response.status_code == 200

    def test_finance_permissions(self, client, auth_headers_finance):
        """测试财务人员权限"""
        # 财务可以查看所有对账批次
        response = client.get("/api/v1/reconciliations", headers=auth_headers_finance)
        assert response.status_code == 200

        # 财务可以创建对账批次
        data = {
            "reconciliation_date": "2025-11-11",
            "auto_match": True,
            "notes": "财务创建的测试批次"
        }
        response = client.post("/api/v1/reconciliations/batches", json=data, headers=auth_headers_finance)
        assert response.status_code == 200

        # 财务可以查看统计
        response = client.get("/api/v1/reconciliations/statistics", headers=auth_headers_finance)
        assert response.status_code == 200

        # 财务可以导出数据
        response = client.get("/api/v1/reconciliations/export", headers=auth_headers_finance)
        assert response.status_code == 200

    def test_data_operator_permissions(self, client, auth_headers_operator):
        """测试数据员权限"""
        # 数据员不能创建对账批次
        data = {
            "reconciliation_date": "2025-11-10",
            "auto_match": True
        }
        response = client.post("/api/v1/reconciliations/batches", json=data, headers=auth_headers_operator)
        assert response.status_code == 403

        # 数据员可以查看对账批次
        response = client.get("/api/v1/reconciliations", headers=auth_headers_operator)
        assert response.status_code == 200

        # 数据员可以查看统计
        response = client.get("/api/v1/reconciliations/statistics", headers=auth_headers_operator)
        assert response.status_code == 200

        # 数据员不能导出数据
        response = client.get("/api/v1/reconciliations/export", headers=auth_headers_operator)
        assert response.status_code == 403

    def test_media_buyer_permissions(self, client, auth_headers_user):
        """测试媒体买家权限"""
        # 媒体买家不能创建对账批次
        data = {
            "reconciliation_date": "2025-11-10",
            "auto_match": True
        }
        response = client.post("/api/v1/reconciliations/batches", json=data, headers=auth_headers_user)
        assert response.status_code == 403

        # 媒体买家可以查看对账批次（只能看到自己的）
        response = client.get("/api/v1/reconciliations", headers=auth_headers_user)
        assert response.status_code == 200

        # 媒体买家不能查看统计
        response = client.get("/api/v1/reconciliations/statistics", headers=auth_headers_user)
        assert response.status_code == 403

        # 媒体买家不能导出数据
        response = client.get("/api/v1/reconciliations/export", headers=auth_headers_user)
        assert response.status_code == 403

    def test_unauthenticated_access(self, client):
        """测试未认证访问被拒绝"""
        # 未认证不能创建对账批次
        data = {
            "reconciliation_date": "2025-11-10",
            "auto_match": True
        }
        response = client.post("/api/v1/reconciliations/batches", json=data)
        assert response.status_code == 401

        # 未认证不能查看对账列表
        response = client.get("/api/v1/reconciliations")
        assert response.status_code == 401

        # 未认证不能查看统计
        response = client.get("/api/v1/reconciliations/statistics")
        assert response.status_code == 401

    def test_invalid_token(self, client):
        """测试无效token访问被拒绝"""
        headers = {"Authorization": "Bearer invalid_token"}

        # 无效token不能创建对账批次
        data = {
            "reconciliation_date": "2025-11-10",
            "auto_match": True
        }
        response = client.post("/api/v1/reconciliations/batches", json=data, headers=headers)
        assert response.status_code == 401
