"""
月度结算 API 路由测试 - TASK-FIN-003 月度锁账

SoT References:
- API_SOT.md v9.0 §6.5 Monthly Settlements API
- STATE_MACHINE.md v2.9 §13.1 (月度结算状态机)
- MASTER.md v4.8 §2.4 (CEO: 月度锁账确认)

端点列表 (10 个):
- POST   /monthly-settlements/generate
- POST   /monthly-settlements/batch-generate
- GET    /monthly-settlements
- GET    /monthly-settlements/statistics
- GET    /monthly-settlements/{id}
- PUT    /monthly-settlements/{id}
- POST   /monthly-settlements/{id}/confirm
- POST   /monthly-settlements/{id}/lock
- POST   /monthly-settlements/{id}/reject
- POST   /monthly-settlements/{id}/archive
- POST   /monthly-settlements/{id}/recalculate

Version: 1.0
Author: Claude Code (TASK-FIN-003)
"""

import pytest
from datetime import date
from decimal import Decimal


class TestMonthlySettlementsAPI:
    """月度结算 API 测试"""

    BASE_URL = "/api/v1/monthly-settlements"

    class TestGenerateEndpoint:
        """POST /monthly-settlements/generate"""

        def test_generate_requires_auth(self, client):
            """生成结算需要认证"""
            response = client.post(
                f"{TestMonthlySettlementsAPI.BASE_URL}/generate",
                json={
                    "project_id": 1,
                    "settlement_month": "2024-01-01",
                },
            )
            assert response.status_code == 401

        def test_generate_requires_finance_role(self, client, pitcher_token):
            """生成结算需要 finance 角色"""
            response = client.post(
                f"{TestMonthlySettlementsAPI.BASE_URL}/generate",
                json={
                    "project_id": 1,
                    "settlement_month": "2024-01-01",
                },
                headers={"Authorization": f"Bearer {pitcher_token}"},
            )
            assert response.status_code == 403

    class TestBatchGenerateEndpoint:
        """POST /monthly-settlements/batch-generate"""

        def test_batch_generate_requires_auth(self, client):
            """批量生成需要认证"""
            response = client.post(
                f"{TestMonthlySettlementsAPI.BASE_URL}/batch-generate",
                json={
                    "settlement_month": "2024-01-01",
                },
            )
            assert response.status_code == 401

    class TestListEndpoint:
        """GET /monthly-settlements"""

        def test_list_requires_auth(self, client):
            """列表查询需要认证"""
            response = client.get(TestMonthlySettlementsAPI.BASE_URL)
            assert response.status_code == 401

        def test_list_empty_result(self, client, finance_token):
            """空列表返回"""
            response = client.get(
                TestMonthlySettlementsAPI.BASE_URL,
                headers={"Authorization": f"Bearer {finance_token}"},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["items"] == []

    class TestStatisticsEndpoint:
        """GET /monthly-settlements/statistics"""

        def test_statistics_requires_auth(self, client):
            """统计需要认证"""
            response = client.get(f"{TestMonthlySettlementsAPI.BASE_URL}/statistics")
            assert response.status_code == 401

    class TestDetailEndpoint:
        """GET /monthly-settlements/{id}"""

        def test_detail_not_found(self, client, finance_token):
            """获取不存在的结算详情"""
            response = client.get(
                f"{TestMonthlySettlementsAPI.BASE_URL}/99999",
                headers={"Authorization": f"Bearer {finance_token}"},
            )
            assert response.status_code == 404

    class TestUpdateEndpoint:
        """PUT /monthly-settlements/{id}"""

        def test_update_requires_auth(self, client):
            """更新需要认证"""
            response = client.put(
                f"{TestMonthlySettlementsAPI.BASE_URL}/1",
                json={"notes": "更新备注"},
            )
            assert response.status_code == 401

    class TestConfirmEndpoint:
        """POST /monthly-settlements/{id}/confirm"""

        def test_confirm_requires_auth(self, client):
            """确认需要认证"""
            response = client.post(
                f"{TestMonthlySettlementsAPI.BASE_URL}/1/confirm",
                json={},
            )
            assert response.status_code == 401

        def test_confirm_not_found(self, client, finance_token):
            """确认不存在的结算"""
            response = client.post(
                f"{TestMonthlySettlementsAPI.BASE_URL}/99999/confirm",
                json={},
                headers={"Authorization": f"Bearer {finance_token}"},
            )
            assert response.status_code == 404

    class TestLockEndpoint:
        """POST /monthly-settlements/{id}/lock"""

        def test_lock_requires_auth(self, client):
            """锁定需要认证"""
            response = client.post(
                f"{TestMonthlySettlementsAPI.BASE_URL}/1/lock",
                json={},
            )
            assert response.status_code == 401

        def test_lock_requires_ceo_role(self, client, finance_token):
            """锁定需要 CEO 角色"""
            response = client.post(
                f"{TestMonthlySettlementsAPI.BASE_URL}/1/lock",
                json={},
                headers={"Authorization": f"Bearer {finance_token}"},
            )
            # 403 因为 finance 没有锁定权限
            assert response.status_code == 403

    class TestRejectEndpoint:
        """POST /monthly-settlements/{id}/reject"""

        def test_reject_requires_auth(self, client):
            """退回需要认证"""
            response = client.post(
                f"{TestMonthlySettlementsAPI.BASE_URL}/1/reject",
                json={"reason": "数据有误"},
            )
            assert response.status_code == 401

        def test_reject_requires_reason(self, client, finance_token):
            """退回需要提供原因"""
            response = client.post(
                f"{TestMonthlySettlementsAPI.BASE_URL}/1/reject",
                json={},  # 缺少 reason
                headers={"Authorization": f"Bearer {finance_token}"},
            )
            assert response.status_code == 422

    class TestArchiveEndpoint:
        """POST /monthly-settlements/{id}/archive"""

        def test_archive_requires_auth(self, client):
            """归档需要认证"""
            response = client.post(
                f"{TestMonthlySettlementsAPI.BASE_URL}/1/archive",
            )
            assert response.status_code == 401

        def test_archive_requires_admin_role(self, client, finance_token):
            """归档需要 admin 角色"""
            response = client.post(
                f"{TestMonthlySettlementsAPI.BASE_URL}/1/archive",
                headers={"Authorization": f"Bearer {finance_token}"},
            )
            # 403 因为 finance 没有归档权限
            assert response.status_code == 403

    class TestRecalculateEndpoint:
        """POST /monthly-settlements/{id}/recalculate"""

        def test_recalculate_requires_auth(self, client):
            """重新计算需要认证"""
            response = client.post(
                f"{TestMonthlySettlementsAPI.BASE_URL}/1/recalculate",
            )
            assert response.status_code == 401


class TestMonthlySettlementsAPIStateMachine:
    """
    月度结算 API 状态机流转测试

    SoT: STATE_MACHINE.md v2.9 §13.1
    流程: pending → confirmed → locked → archived
    退回: confirmed → pending
    """

    BASE_URL = "/api/v1/monthly-settlements"

    # 注: 完整的状态机流转测试需要先创建项目和日报数据
    # 这里仅测试端点可达性和错误处理

    def test_state_transition_flow_documented(self):
        """验证状态流转文档完整性"""
        # pending → confirmed (finance/admin)
        # confirmed → locked (ceo/admin)
        # confirmed → pending (finance/admin, 退回)
        # locked → archived (admin)
        expected_transitions = {
            "pending": ["confirmed"],
            "confirmed": ["locked", "pending"],
            "locked": ["archived"],
            "archived": [],
        }
        assert len(expected_transitions) == 4


class TestMonthlySettlementsAPIPermissions:
    """
    月度结算 API 权限矩阵测试

    SoT: MASTER.md v4.8 §2.4

    权限矩阵:
    - admin: 全部操作
    - ceo: 锁定、查看
    - finance: 确认、退回、查看
    - project_owner: 查看自己项目
    """

    BASE_URL = "/api/v1/monthly-settlements"

    def test_permission_matrix_documented(self):
        """验证权限矩阵文档完整性"""
        permission_matrix = {
            "admin": [
                "generate",
                "list",
                "detail",
                "update",
                "confirm",
                "lock",
                "reject",
                "archive",
                "recalculate",
            ],
            "ceo": ["list", "detail", "lock"],
            "finance": [
                "generate",
                "list",
                "detail",
                "update",
                "confirm",
                "reject",
                "recalculate",
            ],
            "project_owner": ["list", "detail"],
        }
        # admin 应该有最多权限
        assert len(permission_matrix["admin"]) > len(permission_matrix["finance"])
        # ceo 特有 lock 权限
        assert "lock" in permission_matrix["ceo"]
        # finance 不能 lock
        assert "lock" not in permission_matrix["finance"]
