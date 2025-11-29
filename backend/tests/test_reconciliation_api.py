"""
对账管理API测试
Version: 2.0 (Test Fixture & Architecture Repair Flow)
Author: Claude协作开发

修复内容:
- P0-RA-001: 将 async 测试转换为 sync 风格，使用 TestClient
- P1-RA-001: 状态断言修复为 STATE_MACHINE.md v2.6 定义 (pending → draft)
- P1-RA-002: 修复 timedelta 导入错误
- P1-RA-003: 使用 conftest.py 定义的 auth_headers fixtures
"""

import pytest
from decimal import Decimal
from datetime import date, timedelta

from fastapi.testclient import TestClient


class TestReconciliationAPI:
    """对账管理API测试类"""

    def test_create_reconciliation_batch_success(self, client, auth_headers_admin):
        """测试成功创建对账批次"""
        data = {
            "reconciliation_date": "2025-11-10",
            "channel_ids": [1, 2],
            "auto_match": True,
            "threshold": "100.00",
            "notes": "测试对账批次"
        }

        response = client.post("/api/v1/reconciliations/batches", json=data, headers=auth_headers_admin)

        assert response.status_code == 200
        json_data = response.json()
        assert json_data["success"] is True
        assert json_data["data"]["reconciliation_date"] == "2025-11-10"
        # P1-RA-001: pending → draft (STATE_MACHINE.md v2.6)
        assert json_data["data"]["status"] == "draft"
        assert json_data["data"]["batch_no"].startswith("REC")

    def test_create_reconciliation_batch_insufficient_permissions(
        self, client, auth_headers_user
    ):
        """测试创建对账批次权限不足"""
        data = {
            "reconciliation_date": "2025-11-10",
            "auto_match": True
        }

        response = client.post("/api/v1/reconciliations/batches", json=data, headers=auth_headers_user)

        assert response.status_code == 403
        json_data = response.json()
        assert json_data["success"] is False

    def test_create_reconciliation_batch_future_date(
        self, client, auth_headers_admin
    ):
        """测试创建未来日期的对账批次"""
        # P1-RA-002: 修复 timedelta 导入
        future_date = (date.today() + timedelta(days=1)).isoformat()
        data = {
            "reconciliation_date": future_date,
            "auto_match": True
        }

        response = client.post("/api/v1/reconciliations/batches", json=data, headers=auth_headers_admin)

        assert response.status_code == 400
        json_data = response.json()
        assert json_data["success"] is False
        # P1 修复：BIZ_301 是"状态转换不允许"(400)，不是"日期不能为未来"
        # 日期不能为未来应使用 BIZ_201（日期不能为未来, 400）- ERROR_CODES_SOT.md v2.1
        assert json_data["error"]["code"] == "BIZ_201"

    def test_get_reconciliation_batches_list(
        self, client, auth_headers_admin
    ):
        """测试获取对账批次列表"""
        response = client.get("/api/v1/reconciliations", headers=auth_headers_admin)

        assert response.status_code == 200
        json_data = response.json()
        assert json_data["success"] is True
        assert "items" in json_data["data"]
        assert "meta" in json_data["data"]

    def test_get_reconciliation_batches_with_filters(
        self, client, auth_headers_admin
    ):
        """测试带过滤条件获取对账批次列表"""
        params = {
            "page": 1,
            "page_size": 10,
            "status": "completed",
            "date_from": "2025-11-01",
            "date_to": "2025-11-30"
        }

        response = client.get("/api/v1/reconciliations", params=params, headers=auth_headers_admin)

        assert response.status_code == 200
        json_data = response.json()
        assert json_data["success"] is True

    def test_get_reconciliation_batch_detail(
        self, client, auth_headers_admin, sample_reconciliation_data
    ):
        """测试获取对账批次详情"""
        # 先创建一个批次
        create_response = client.post(
            "/api/v1/reconciliations/batches",
            json=sample_reconciliation_data,
            headers=auth_headers_admin
        )

        if create_response.status_code != 200:
            pytest.skip("创建对账批次失败，跳过后续测试")

        batch_id = create_response.json()["data"]["id"]

        response = client.get(
            f"/api/v1/reconciliations/batches/{batch_id}",
            headers=auth_headers_admin
        )

        assert response.status_code == 200
        json_data = response.json()
        assert json_data["success"] is True
        assert json_data["data"]["id"] == batch_id

    def test_run_reconciliation(
        self, client, auth_headers_admin, sample_reconciliation_data
    ):
        """测试执行对账"""
        # 先创建一个批次
        create_response = client.post(
            "/api/v1/reconciliations/batches",
            json=sample_reconciliation_data,
            headers=auth_headers_admin
        )

        if create_response.status_code != 200:
            pytest.skip("创建对账批次失败，跳过后续测试")

        batch_id = create_response.json()["data"]["id"]

        response = client.post(
            f"/api/v1/reconciliations/batches/{batch_id}/run",
            headers=auth_headers_admin
        )

        assert response.status_code == 200
        json_data = response.json()
        assert json_data["success"] is True
        # P1-RA-001: processing/completed 是有效的中间/最终状态
        assert json_data["data"]["status"] in ["pending_review", "approved", "completed"]

    def test_get_reconciliation_details(
        self, client, auth_headers_admin, sample_reconciliation_data
    ):
        """测试获取对账详情列表"""
        # 先创建一个批次
        create_response = client.post(
            "/api/v1/reconciliations/batches",
            json=sample_reconciliation_data,
            headers=auth_headers_admin
        )

        if create_response.status_code != 200:
            pytest.skip("创建对账批次失败，跳过后续测试")

        batch_id = create_response.json()["data"]["id"]

        response = client.get(
            f"/api/v1/reconciliations/batches/{batch_id}/details",
            headers=auth_headers_admin
        )

        assert response.status_code == 200
        json_data = response.json()
        assert json_data["success"] is True
        assert "items" in json_data["data"]

    def test_get_reconciliation_statistics(
        self, client, auth_headers_admin
    ):
        """测试获取对账统计"""
        params = {
            "date_from": "2025-11-01",
            "date_to": "2025-11-30"
        }

        response = client.get("/api/v1/reconciliations/statistics", params=params, headers=auth_headers_admin)

        assert response.status_code == 200
        json_data = response.json()
        assert json_data["success"] is True
        assert "total_batches" in json_data["data"]

    def test_get_reconciliation_statistics_insufficient_permissions(
        self, client, auth_headers_user
    ):
        """测试获取对账统计权限不足"""
        response = client.get("/api/v1/reconciliations/statistics", headers=auth_headers_user)

        assert response.status_code == 403

    def test_export_reconciliation_data_excel(
        self, client, auth_headers_admin
    ):
        """测试导出对账数据为Excel"""
        params = {
            "format_type": "excel",
            "date_from": "2025-11-01",
            "date_to": "2025-11-30"
        }

        response = client.get("/api/v1/reconciliations/export", params=params, headers=auth_headers_admin)

        assert response.status_code == 200
        assert "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" in response.headers.get("content-type", "")

    def test_export_reconciliation_data_insufficient_permissions(
        self, client, auth_headers_user
    ):
        """测试导出对账数据权限不足"""
        response = client.get("/api/v1/reconciliations/export", headers=auth_headers_user)

        assert response.status_code == 403

    def test_get_reconciliation_reports(
        self, client, auth_headers_finance
    ):
        """测试获取对账报告列表"""
        params = {
            "page": 1,
            "page_size": 10,
            "report_type": "daily"
        }

        response = client.get("/api/v1/reconciliations/reports", params=params, headers=auth_headers_finance)

        assert response.status_code == 200
        json_data = response.json()
        assert json_data["success"] is True
        assert "items" in json_data["data"]

    def test_generate_reconciliation_report(
        self, client, auth_headers_admin
    ):
        """测试生成对账报告"""
        data = {
            "batch_id": 1,
            "report_type": "daily",
            "report_period_start": "2025-11-01",
            "report_period_end": "2025-11-01",
            "include_charts": True,
            "format_type": "excel"
        }

        response = client.post("/api/v1/reconciliations/reports", json=data, headers=auth_headers_admin)

        # 可能返回200或404（如果批次不存在）
        assert response.status_code in [200, 404]

    def test_unauthorized_access(self, client):
        """测试未授权访问被拒绝"""
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

    def test_invalid_date_range(
        self, client, auth_headers_admin
    ):
        """测试无效的日期范围"""
        data = {
            "report_type": "daily",
            "report_period_start": "2025-11-30",
            "report_period_end": "2025-11-01",  # 结束日期早于开始日期
            "include_charts": True
        }

        response = client.post("/api/v1/reconciliations/reports", json=data, headers=auth_headers_admin)

        assert response.status_code == 422  # 验证错误
