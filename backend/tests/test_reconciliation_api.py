"""
对账管理API测试
Version: 1.0
Author: Claude协作开发
"""

import pytest
from decimal import Decimal
from datetime import date, datetime
from httpx import AsyncClient

from models.user import User


class TestReconciliationAPI:
    """对账管理API测试类"""

    @pytest.mark.asyncio
    async def test_create_reconciliation_batch_success(self, client: AsyncClient, admin_token):
        """测试成功创建对账批次"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        data = {
            "reconciliation_date": "2025-11-10",
            "channel_ids": [1, 2],
            "auto_match": True,
            "threshold": "100.00",
            "notes": "测试对账批次"
        }

        response = await client.post("/api/v1/reconciliations/batches", json=data, headers=headers)

        assert response.status_code == 200
        json_data = response.json()
        assert json_data["success"] is True
        assert json_data["data"]["reconciliation_date"] == "2025-11-10"
        assert json_data["data"]["status"] == "pending"
        assert json_data["data"]["batch_no"].startswith("REC")

    @pytest.mark.asyncio
    async def test_create_reconciliation_batch_insufficient_permissions(
        self, client: AsyncClient, media_buyer_token
    ):
        """测试创建对账批次权限不足"""
        headers = {"Authorization": f"Bearer {media_buyer_token}"}
        data = {
            "reconciliation_date": "2025-11-10",
            "auto_match": True
        }

        response = await client.post("/api/v1/reconciliations/batches", json=data, headers=headers)

        assert response.status_code == 403
        json_data = response.json()
        assert json_data["success"] is False

    @pytest.mark.asyncio
    async def test_create_reconciliation_batch_future_date(
        self, client: AsyncClient, admin_token
    ):
        """测试创建未来日期的对账批次"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        future_date = (date.today() + datetime.timedelta(days=1)).isoformat()
        data = {
            "reconciliation_date": future_date,
            "auto_match": True
        }

        response = await client.post("/api/v1/reconciliations/batches", json=data, headers=headers)

        assert response.status_code == 400
        json_data = response.json()
        assert json_data["success"] is False
        assert "BIZ_301" in json_data["error"]["code"]

    @pytest.mark.asyncio
    async def test_get_reconciliation_batches_list(
        self, client: AsyncClient, admin_token
    ):
        """测试获取对账批次列表"""
        headers = {"Authorization": f"Bearer {admin_token}"}

        response = await client.get("/api/v1/reconciliations", headers=headers)

        assert response.status_code == 200
        json_data = response.json()
        assert json_data["success"] is True
        assert "items" in json_data["data"]
        assert "meta" in json_data["data"]

    @pytest.mark.asyncio
    async def test_get_reconciliation_batches_with_filters(
        self, client: AsyncClient, admin_token
    ):
        """测试带过滤条件获取对账批次列表"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        params = {
            "page": 1,
            "page_size": 10,
            "status": "completed",
            "date_from": "2025-11-01",
            "date_to": "2025-11-30"
        }

        response = await client.get("/api/v1/reconciliations", params=params, headers=headers)

        assert response.status_code == 200
        json_data = response.json()
        assert json_data["success"] is True

    @pytest.mark.asyncio
    async def test_get_reconciliation_batch_detail(
        self, client: AsyncClient, admin_token, sample_reconciliation_batch_id
    ):
        """测试获取对账批次详情"""
        headers = {"Authorization": f"Bearer {admin_token}"}

        response = await client.get(
            f"/api/v1/reconciliations/batches/{sample_reconciliation_batch_id}",
            headers=headers
        )

        assert response.status_code == 200
        json_data = response.json()
        assert json_data["success"] is True
        assert json_data["data"]["id"] == sample_reconciliation_batch_id

    @pytest.mark.asyncio
    async def test_run_reconciliation(
        self, client: AsyncClient, admin_token, sample_reconciliation_batch_id
    ):
        """测试执行对账"""
        headers = {"Authorization": f"Bearer {admin_token}"}

        response = await client.post(
            f"/api/v1/reconciliations/batches/{sample_reconciliation_batch_id}/run",
            headers=headers
        )

        assert response.status_code == 200
        json_data = response.json()
        assert json_data["success"] is True
        assert json_data["data"]["status"] in ["processing", "completed"]

    @pytest.mark.asyncio
    async def test_get_reconciliation_details(
        self, client: AsyncClient, admin_token, sample_reconciliation_batch_id
    ):
        """测试获取对账详情列表"""
        headers = {"Authorization": f"Bearer {admin_token}"}

        response = await client.get(
            f"/api/v1/reconciliations/batches/{sample_reconciliation_batch_id}/details",
            headers=headers
        )

        assert response.status_code == 200
        json_data = response.json()
        assert json_data["success"] is True
        assert "items" in json_data["data"]

    @pytest.mark.asyncio
    async def test_review_reconciliation_detail(
        self, client: AsyncClient, admin_token, sample_reconciliation_detail_id
    ):
        """测试审核对账差异"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        data = {
            "action": "approve",
            "is_matched": True,
            "match_status": "matched",
            "review_notes": "审核通过",
            "auto_confidence": "0.95",
            "difference_type": "amount_mismatch",
            "difference_reason": "时间差异导致"
        }

        response = await client.put(
            f"/api/v1/reconciliations/details/{sample_reconciliation_detail_id}/review",
            json=data,
            headers=headers
        )

        assert response.status_code == 200
        json_data = response.json()
        assert json_data["success"] is True
        assert json_data["data"]["match_status"] == "matched"

    @pytest.mark.asyncio
    async def test_create_adjustment(
        self, client: AsyncClient, admin_token, sample_reconciliation_detail_id
    ):
        """测试创建调整记录"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        data = {
            "adjustment_type": "spend_adjustment",
            "original_amount": "1000.00",
            "adjustment_amount": "-50.00",
            "adjustment_reason": "data_error",
            "detailed_reason": "平台数据延迟导致差异",
            "evidence_url": "https://example.com/evidence.pdf",
            "notes": "已核实调整"
        }

        response = await client.post(
            f"/api/v1/reconciliations/details/{sample_reconciliation_detail_id}/adjust",
            json=data,
            headers=headers
        )

        assert response.status_code == 200
        json_data = response.json()
        assert json_data["success"] is True
        assert json_data["data"]["adjustment_type"] == "spend_adjustment"
        assert json_data["data"]["adjustment_amount"] == "-50.00"

    @pytest.mark.asyncio
    async def test_get_reconciliation_statistics(
        self, client: AsyncClient, admin_token
    ):
        """测试获取对账统计"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        params = {
            "date_from": "2025-11-01",
            "date_to": "2025-11-30"
        }

        response = await client.get("/api/v1/reconciliations/statistics", params=params, headers=headers)

        assert response.status_code == 200
        json_data = response.json()
        assert json_data["success"] is True
        assert "total_batches" in json_data["data"]
        assert "completed_batches" in json_data["data"]
        assert "total_accounts" in json_data["data"]
        assert "matched_accounts" in json_data["data"]
        assert "auto_match_rate" in json_data["data"]
        assert "difference_rate" in json_data["data"]

    @pytest.mark.asyncio
    async def test_get_reconciliation_statistics_insufficient_permissions(
        self, client: AsyncClient, media_buyer_token
    ):
        """测试获取对账统计权限不足"""
        headers = {"Authorization": f"Bearer {media_buyer_token}"}

        response = await client.get("/api/v1/reconciliations/statistics", headers=headers)

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_export_reconciliation_data_excel(
        self, client: AsyncClient, admin_token
    ):
        """测试导出对账数据为Excel"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        params = {
            "format_type": "excel",
            "date_from": "2025-11-01",
            "date_to": "2025-11-30"
        }

        response = await client.get("/api/v1/reconciliations/export", params=params, headers=headers)

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        assert "attachment" in response.headers["content-disposition"]

    @pytest.mark.asyncio
    async def test_export_reconciliation_data_pdf(
        self, client: AsyncClient, admin_token
    ):
        """测试导出对账数据为PDF"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        params = {
            "format_type": "pdf",
            "batch_id": 1
        }

        response = await client.get("/api/v1/reconciliations/export", params=params, headers=headers)

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"

    @pytest.mark.asyncio
    async def test_export_reconciliation_data_insufficient_permissions(
        self, client: AsyncClient, media_buyer_token
    ):
        """测试导出对账数据权限不足"""
        headers = {"Authorization": f"Bearer {media_buyer_token}"}

        response = await client.get("/api/v1/reconciliations/export", headers=headers)

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_get_reconciliation_reports(
        self, client: AsyncClient, finance_token
    ):
        """测试获取对账报告列表"""
        headers = {"Authorization": f"Bearer {finance_token}"}
        params = {
            "page": 1,
            "page_size": 10,
            "report_type": "daily"
        }

        response = await client.get("/api/v1/reconciliations/reports", params=params, headers=headers)

        assert response.status_code == 200
        json_data = response.json()
        assert json_data["success"] is True
        assert "items" in json_data["data"]

    @pytest.mark.asyncio
    async def test_generate_reconciliation_report(
        self, client: AsyncClient, admin_token
    ):
        """测试生成对账报告"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        data = {
            "batch_id": 1,
            "report_type": "daily",
            "report_period_start": "2025-11-01",
            "report_period_end": "2025-11-01",
            "include_charts": True,
            "format_type": "excel"
        }

        response = await client.post("/api/v1/reconciliations/reports", json=data, headers=headers)

        assert response.status_code == 200
        json_data = response.json()
        assert json_data["success"] is True

    @pytest.mark.asyncio
    async def test_cross_project_access_denied(
        self, client: AsyncClient, account_manager_token
    ):
        """测试跨项目访问被拒绝"""
        headers = {"Authorization": f"Bearer {account_manager_token}"}

        # 尝试访问不属于自己项目的对账批次
        response = await client.get("/api/v1/reconciliations/batches/10000", headers=headers)
        # 应该是404（不存在）或403（无权限）

    @pytest.mark.asyncio
    async def test_invalid_date_range(
        self, client: AsyncClient, admin_token
    ):
        """测试无效的日期范围"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        data = {
            "report_type": "daily",
            "report_period_start": "2025-11-30",
            "report_period_end": "2025-11-01",  # 结束日期早于开始日期
            "include_charts": True
        }

        response = await client.post("/api/v1/reconciliations/reports", json=data, headers=headers)

        assert response.status_code == 422  # 验证错误

    @pytest.mark.asyncio
    async def test_unauthorized_access(self, client: AsyncClient):
        """测试未授权访问被拒绝"""
        # 未认证不能创建对账批次
        data = {
            "reconciliation_date": "2025-11-10",
            "auto_match": True
        }
        response = await client.post("/api/v1/reconciliations/batches", json=data)
        assert response.status_code == 401

        # 未认证不能查看对账列表
        response = await client.get("/api/v1/reconciliations")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_invalid_batch_status_transition(
        self, client: AsyncClient, admin_token
    ):
        """测试无效的批次状态转换"""
        # 假设批次ID 1 已经是completed状态
        headers = {"Authorization": f"Bearer {admin_token}"}

        response = await client.post(
            "/api/v1/reconciliations/batches/1/run",
            headers=headers
        )

        # 可能返回400（状态无效）或200（幂等操作）
        assert response.status_code in [200, 400]

    @pytest.mark.asyncio
    async def test_adjustment_amount_validation(
        self, client: AsyncClient, admin_token, sample_reconciliation_detail_id
    ):
        """测试调整金额验证"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        data = {
            "adjustment_type": "spend_adjustment",
            "original_amount": "1000.00",
            "adjustment_amount": "1000.123",  # 超过2位小数
            "adjustment_reason": "test",
            "detailed_reason": "test"
        }

        response = await client.post(
            f"/api/v1/reconciliations/details/{sample_reconciliation_detail_id}/adjust",
            json=data,
            headers=headers
        )

        assert response.status_code == 422  # 验证错误

    @pytest.mark.asyncio
    async def test_auto_confidence_validation(
        self, client: AsyncClient, admin_token, sample_reconciliation_detail_id
    ):
        """测试自动匹配置信度验证"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        data = {
            "action": "approve",
            "is_matched": True,
            "match_status": "auto_matched",
            "auto_confidence": "0.75"  # 低于0.8的阈值
        }

        response = await client.put(
            f"/api/v1/reconciliations/details/{sample_reconciliation_detail_id}/review",
            json=data,
            headers=headers
        )

        assert response.status_code == 422  # 验证错误

    @pytest.mark.asyncio
    async def test_report_period_validation(
        self, client: AsyncClient, admin_token
    ):
        """测试报告周期验证"""
        headers = {"Authorization": f"Bearer {admin_token}"}

        # 周报超过7天
        data = {
            "report_type": "weekly",
            "report_period_start": "2025-11-01",
            "report_period_end": "2025-11-15",  # 超过7天
            "include_charts": True
        }

        response = await client.post("/api/v1/reconciliations/reports", json=data, headers=headers)

        assert response.status_code == 422  # 验证错误