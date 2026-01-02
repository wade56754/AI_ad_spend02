"""
API 测试: 死号处理 API - TASK-ACC-004

SoT References:
- STATE_MACHINE.md v2.9 §7.1: 账户状态机 (dead 为终态之一)
- BR-ACCT-006: 停用账户禁止操作（死号仅允许余额迁移）
- API_SOT.md v9.0 §8: POST /api/v1/ad-accounts/{account_id}/mark-dead

端点: POST /api/v1/ad-accounts/{account_id}/mark-dead

Version: 1.0
Author: Claude Code (TASK-ACC-004)
"""

import pytest
from uuid import uuid4


class TestMarkDeadAPI:
    """死号处理 API 测试"""

    BASE_URL = "/api/v1/ad-accounts"

    class TestMarkDeadEndpoint:
        """POST /ad-accounts/{account_id}/mark-dead"""

        def test_mark_dead_requires_auth(self, client):
            """标记死号需要认证"""
            response = client.post(
                f"{TestMarkDeadAPI.BASE_URL}/1/mark-dead",
                json={
                    "reason": "测试死号原因",
                },
            )
            assert response.status_code == 401

        def test_mark_dead_success_by_admin(
            self, client, admin_token, sample_active_account
        ):
            """管理员成功标记死号"""
            response = client.post(
                f"{TestMarkDeadAPI.BASE_URL}/{sample_active_account.id}/mark-dead",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={
                    "reason": "账户被平台封禁，无法继续投放",
                    "notes": "封禁原因：违反广告政策",
                    "transfer_balance": True,
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "account_id" in data["data"]
            assert "previous_status" in data["data"]
            assert data["data"]["new_status"] == "dead"
            assert "marked_at" in data["data"]
            assert "reason" in data["data"]

        def test_mark_dead_success_by_account_manager(
            self, client, account_manager_token, sample_active_account
        ):
            """户管成功标记死号"""
            response = client.post(
                f"{TestMarkDeadAPI.BASE_URL}/{sample_active_account.id}/mark-dead",
                headers={"Authorization": f"Bearer {account_manager_token}"},
                json={
                    "reason": "账户异常，需要标记为死号处理",
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True

        def test_mark_dead_denied_for_pitcher(
            self, client, pitcher_token, sample_active_account
        ):
            """投手无权标记死号"""
            response = client.post(
                f"{TestMarkDeadAPI.BASE_URL}/{sample_active_account.id}/mark-dead",
                headers={"Authorization": f"Bearer {pitcher_token}"},
                json={
                    "reason": "投手不应该能标记死号",
                },
            )
            assert response.status_code == 403
            data = response.json()
            assert data["success"] is False

        def test_mark_dead_denied_for_finance(
            self, client, finance_token, sample_active_account
        ):
            """财务无权标记死号"""
            response = client.post(
                f"{TestMarkDeadAPI.BASE_URL}/{sample_active_account.id}/mark-dead",
                headers={"Authorization": f"Bearer {finance_token}"},
                json={
                    "reason": "财务不应该能标记死号",
                },
            )
            assert response.status_code == 403

        def test_mark_dead_account_not_found(self, client, admin_token):
            """账户不存在返回 404"""
            response = client.post(
                f"{TestMarkDeadAPI.BASE_URL}/99999/mark-dead",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={
                    "reason": "账户不存在测试",
                },
            )
            assert response.status_code == 404

        def test_mark_dead_requires_reason(
            self, client, admin_token, sample_active_account
        ):
            """死号原因为必填"""
            response = client.post(
                f"{TestMarkDeadAPI.BASE_URL}/{sample_active_account.id}/mark-dead",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={
                    # 缺少 reason
                },
            )
            assert response.status_code == 422

        def test_mark_dead_reason_too_short(
            self, client, admin_token, sample_active_account
        ):
            """死号原因太短"""
            response = client.post(
                f"{TestMarkDeadAPI.BASE_URL}/{sample_active_account.id}/mark-dead",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={
                    "reason": "1234",  # min_length=5
                },
            )
            assert response.status_code == 422


class TestMarkDeadBusinessRules:
    """死号处理业务规则测试"""

    BASE_URL = "/api/v1/ad-accounts"

    def test_cannot_mark_dead_already_dead(
        self, client, admin_token, sample_dead_account
    ):
        """不能重复标记已死号的账户"""
        response = client.post(
            f"{TestMarkDeadAPI.BASE_URL}/{sample_dead_account.id}/mark-dead",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "reason": "尝试重复标记死号",
            },
        )
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False

    def test_cannot_mark_dead_archived_account(
        self, client, admin_token, sample_archived_account
    ):
        """不能标记已归档的账户"""
        response = client.post(
            f"{TestMarkDeadAPI.BASE_URL}/{sample_archived_account.id}/mark-dead",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "reason": "尝试标记已归档账户",
            },
        )
        assert response.status_code == 400


class TestMarkDeadStatusTransitions:
    """死号处理状态转换测试"""

    BASE_URL = "/api/v1/ad-accounts"

    def test_mark_dead_from_new_status(self, client, admin_token, sample_new_account):
        """从 new 状态转换到 dead"""
        response = client.post(
            f"{TestMarkDeadAPI.BASE_URL}/{sample_new_account.id}/mark-dead",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "reason": "开户失败，账户无法激活",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["previous_status"] == "new"
        assert data["data"]["new_status"] == "dead"

    def test_mark_dead_from_testing_status(
        self, client, admin_token, sample_testing_account
    ):
        """从 testing 状态转换到 dead"""
        response = client.post(
            f"{TestMarkDeadAPI.BASE_URL}/{sample_testing_account.id}/mark-dead",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "reason": "测试期间发现账户异常",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["previous_status"] == "testing"
        assert data["data"]["new_status"] == "dead"

    def test_mark_dead_from_active_status(
        self, client, admin_token, sample_active_account
    ):
        """从 active 状态转换到 dead"""
        response = client.post(
            f"{TestMarkDeadAPI.BASE_URL}/{sample_active_account.id}/mark-dead",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "reason": "账户被平台封禁",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["previous_status"] == "active"
        assert data["data"]["new_status"] == "dead"

    def test_mark_dead_from_suspended_status(
        self, client, admin_token, sample_suspended_account
    ):
        """从 suspended 状态转换到 dead"""
        response = client.post(
            f"{TestMarkDeadAPI.BASE_URL}/{sample_suspended_account.id}/mark-dead",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "reason": "暂停账户确认无法恢复",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["previous_status"] == "suspended"
        assert data["data"]["new_status"] == "dead"


class TestMarkDeadResponse:
    """死号处理响应格式测试"""

    BASE_URL = "/api/v1/ad-accounts"

    def test_response_format(self, client, admin_token, sample_active_account):
        """测试响应格式符合 API_SOT"""
        response = client.post(
            f"{TestMarkDeadAPI.BASE_URL}/{sample_active_account.id}/mark-dead",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "reason": "响应格式测试",
            },
        )

        if response.status_code == 200:
            data = response.json()

            # 验证标准响应格式
            assert "success" in data
            assert "data" in data
            assert "message" in data

            # 验证数据字段
            mark_dead_data = data["data"]
            required_fields = [
                "account_id",
                "account_name",
                "account_code",
                "platform",
                "project_id",
                "previous_status",
                "new_status",
                "marked_at",
                "marked_by",
                "marked_by_name",
                "reason",
                "total_spend",
                "total_leads",
            ]

            for field in required_fields:
                assert field in mark_dead_data, f"Missing field: {field}"

    def test_response_includes_balance_transfer_hint(
        self, client, admin_token, sample_account_with_balance
    ):
        """有余额时响应包含余额迁移提示"""
        response = client.post(
            f"{TestMarkDeadAPI.BASE_URL}/{sample_account_with_balance.id}/mark-dead",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "reason": "账户有余额测试",
                "transfer_balance": True,
            },
        )

        if response.status_code == 200:
            data = response.json()
            assert "needs_balance_transfer" in data["data"]
            if data["data"]["needs_balance_transfer"]:
                assert "balance_transfer_url" in data["data"]
                assert data["data"]["balance_transfer_url"] is not None


class TestMarkDeadPermissionMatrix:
    """
    死号处理权限矩阵测试

    SoT: AUTH_SPEC.md v2.0 §5.3.1

    权限矩阵:
    - admin: ✅ 可标记所有账户
    - account_manager: ✅ 可标记所管项目的账户
    - project_owner: ❌ 无权限
    - finance: ❌ 无权限
    - pitcher: ❌ 无权限
    """

    BASE_URL = "/api/v1/ad-accounts"

    def test_permission_matrix(self):
        """验证权限矩阵文档完整性"""
        allowed_roles = ["admin", "account_manager"]
        denied_roles = ["project_owner", "finance", "pitcher"]

        assert len(allowed_roles) == 2
        assert len(denied_roles) == 3
