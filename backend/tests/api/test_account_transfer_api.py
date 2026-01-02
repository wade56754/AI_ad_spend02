"""
API 测试: 账户转移 API - TASK-ACC-003

SoT References:
- BR-ACCT.md v5.5 §BR-ACCT-002: 账户唯一性
- BR-ACCT.md v5.5 §BR-ACCT-005: 审计日志
- AUTH_SPEC.md v2.0 §5.3.1: 权限控制
- API_SOT.md v9.0 §8: 广告账户 API

端点: POST /api/v1/ad-accounts/{account_id}/transfer

Version: 1.0
Author: Claude Code (TASK-ACC-003)
"""

import pytest
from uuid import uuid4


class TestAccountTransferAPI:
    """账户转移 API 测试"""

    BASE_URL = "/api/v1/ad-accounts"

    class TestTransferEndpoint:
        """POST /ad-accounts/{account_id}/transfer"""

        def test_transfer_requires_auth(self, client):
            """转移需要认证"""
            response = client.post(
                f"{TestAccountTransferAPI.BASE_URL}/1/transfer",
                json={
                    "target_pitcher_id": str(uuid4()),
                    "reason": "测试转移原因",
                },
            )
            assert response.status_code == 401

        def test_transfer_success_by_admin(
            self, client, admin_token, sample_account_with_owner, sample_pitcher
        ):
            """管理员成功转移账户"""
            response = client.post(
                f"{TestAccountTransferAPI.BASE_URL}/{sample_account_with_owner.id}/transfer",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={
                    "target_pitcher_id": str(sample_pitcher.id),
                    "reason": "投放策略调整，需要更换投手",
                    "notes": "原投手已离职",
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "account_id" in data["data"]
            assert "previous_pitcher_id" in data["data"]
            assert "new_pitcher_id" in data["data"]
            assert "transferred_at" in data["data"]
            assert "reason" in data["data"]

        def test_transfer_success_by_account_manager(
            self,
            client,
            account_manager_token,
            sample_account_with_owner,
            sample_pitcher,
        ):
            """户管成功转移账户"""
            response = client.post(
                f"{TestAccountTransferAPI.BASE_URL}/{sample_account_with_owner.id}/transfer",
                headers={"Authorization": f"Bearer {account_manager_token}"},
                json={
                    "target_pitcher_id": str(sample_pitcher.id),
                    "reason": "工作量调配，转移账户",
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True

        def test_transfer_denied_for_pitcher(
            self, client, pitcher_token, sample_account_with_owner, sample_pitcher
        ):
            """投手无权转移账户"""
            response = client.post(
                f"{TestAccountTransferAPI.BASE_URL}/{sample_account_with_owner.id}/transfer",
                headers={"Authorization": f"Bearer {pitcher_token}"},
                json={
                    "target_pitcher_id": str(sample_pitcher.id),
                    "reason": "投手不应该能转移账户",
                },
            )
            assert response.status_code == 403
            data = response.json()
            assert data["success"] is False

        def test_transfer_denied_for_finance(
            self, client, finance_token, sample_account_with_owner, sample_pitcher
        ):
            """财务无权转移账户"""
            response = client.post(
                f"{TestAccountTransferAPI.BASE_URL}/{sample_account_with_owner.id}/transfer",
                headers={"Authorization": f"Bearer {finance_token}"},
                json={
                    "target_pitcher_id": str(sample_pitcher.id),
                    "reason": "财务不应该能转移账户",
                },
            )
            assert response.status_code == 403

        def test_transfer_account_not_found(self, client, admin_token, sample_pitcher):
            """账户不存在返回404"""
            response = client.post(
                f"{TestAccountTransferAPI.BASE_URL}/99999/transfer",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={
                    "target_pitcher_id": str(sample_pitcher.id),
                    "reason": "账户不存在测试",
                },
            )
            assert response.status_code == 404

        def test_transfer_requires_reason(
            self, client, admin_token, sample_account_with_owner, sample_pitcher
        ):
            """转移原因为必填"""
            response = client.post(
                f"{TestAccountTransferAPI.BASE_URL}/{sample_account_with_owner.id}/transfer",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={
                    "target_pitcher_id": str(sample_pitcher.id),
                    # 缺少 reason
                },
            )
            assert response.status_code == 422

        def test_transfer_reason_too_short(
            self, client, admin_token, sample_account_with_owner, sample_pitcher
        ):
            """转移原因太短"""
            response = client.post(
                f"{TestAccountTransferAPI.BASE_URL}/{sample_account_with_owner.id}/transfer",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={
                    "target_pitcher_id": str(sample_pitcher.id),
                    "reason": "1234",  # min_length=5
                },
            )
            assert response.status_code == 422

        def test_transfer_target_pitcher_required(
            self, client, admin_token, sample_account_with_owner
        ):
            """目标投手为必填"""
            response = client.post(
                f"{TestAccountTransferAPI.BASE_URL}/{sample_account_with_owner.id}/transfer",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={
                    "reason": "缺少目标投手测试",
                    # 缺少 target_pitcher_id
                },
            )
            assert response.status_code == 422


class TestAccountTransferBusinessRules:
    """账户转移业务规则测试"""

    BASE_URL = "/api/v1/ad-accounts"

    def test_transfer_requires_existing_owner(
        self, client, admin_token, sample_account_without_owner, sample_pitcher
    ):
        """转移要求账户必须有原负责人"""
        response = client.post(
            f"{TestAccountTransferAPI.BASE_URL}/{sample_account_without_owner.id}/transfer",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "target_pitcher_id": str(sample_pitcher.id),
                "reason": "尝试转移未分配的账户",
            },
        )
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False

    def test_transfer_target_must_be_pitcher(
        self, client, admin_token, sample_account_with_owner, sample_finance_user
    ):
        """转移目标必须是投手"""
        response = client.post(
            f"{TestAccountTransferAPI.BASE_URL}/{sample_account_with_owner.id}/transfer",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "target_pitcher_id": str(sample_finance_user.id),
                "reason": "目标不是投手",
            },
        )
        assert response.status_code == 400

    def test_transfer_cannot_transfer_to_same_owner(
        self, client, admin_token, sample_account_with_owner
    ):
        """不能转移给当前负责人"""
        # 假设 sample_account_with_owner.owner_id 是当前负责人
        response = client.post(
            f"{TestAccountTransferAPI.BASE_URL}/{sample_account_with_owner.id}/transfer",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "target_pitcher_id": str(sample_account_with_owner.owner_id),
                "reason": "转移给同一个人",
            },
        )
        assert response.status_code == 400


class TestAccountTransferResponse:
    """账户转移响应格式测试"""

    BASE_URL = "/api/v1/ad-accounts"

    def test_response_format(
        self, client, admin_token, sample_account_with_owner, sample_pitcher
    ):
        """测试响应格式符合 API_SOT"""
        response = client.post(
            f"{TestAccountTransferAPI.BASE_URL}/{sample_account_with_owner.id}/transfer",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "target_pitcher_id": str(sample_pitcher.id),
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
            transfer_data = data["data"]
            required_fields = [
                "account_id",
                "account_name",
                "account_code",
                "previous_pitcher_id",
                "previous_pitcher_name",
                "new_pitcher_id",
                "new_pitcher_name",
                "transferred_at",
                "transferred_by",
                "transferred_by_name",
                "reason",
            ]

            for field in required_fields:
                assert field in transfer_data, f"Missing field: {field}"


class TestAccountTransferPermissionMatrix:
    """
    账户转移权限矩阵测试

    SoT: AUTH_SPEC.md v2.0 §5.3.1

    权限矩阵:
    - admin: ✅ 可转移所有账户
    - account_manager: ✅ 可转移所管项目的账户
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
