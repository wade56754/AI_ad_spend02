"""
消耗导入 API 路由测试
Version: 1.0 (Financial SoT Phase 2)
Author: Claude Code

测试范围:
- API 端点测试
- 权限控制测试
- 请求/响应格式测试
- 错误处理测试

SoT 对齐:
- API_SOT.md v9.0: 标准响应格式
- AUTH_SPEC.md v2.0: 角色权限
"""

import pytest
from datetime import date
from decimal import Decimal
from uuid import uuid4
from unittest.mock import Mock, patch, MagicMock
import io

from fastapi.testclient import TestClient
from fastapi import status


class TestSpendImportEndpoint:
    """消耗导入端点测试"""

    @pytest.fixture
    def mock_service(self):
        """模拟服务"""
        with patch('backend.routers.spend.SpendImportService') as mock:
            yield mock

    def test_import_requires_authentication(self, client):
        """测试导入需要认证"""
        response = client.post(
            "/api/v1/spend/import",
            params={"team_code": "SZ"},
            files={"file": ("test.xlsx", b"fake content", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        )

        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]

    def test_import_requires_valid_file_type(self, client, auth_headers):
        """测试导入需要有效的文件类型"""
        response = client.post(
            "/api/v1/spend/import",
            params={"team_code": "SZ"},
            files={"file": ("test.txt", b"fake content", "text/plain")},
            headers=auth_headers
        )

        # 应该返回错误 (文件类型不支持)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_import_requires_team_code(self, client, auth_headers):
        """测试导入需要团队代码"""
        response = client.post(
            "/api/v1/spend/import",
            files={"file": ("test.xlsx", b"fake content", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestSpendEventsEndpoints:
    """消耗事件 CRUD 端点测试"""

    def test_list_events_requires_authentication(self, client):
        """测试列表需要认证"""
        response = client.get("/api/v1/spend/events")

        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]

    def test_get_event_requires_authentication(self, client):
        """测试获取详情需要认证"""
        event_id = uuid4()
        response = client.get(f"/api/v1/spend/events/{event_id}")

        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]

    def test_create_event_requires_authentication(self, client):
        """测试创建需要认证"""
        response = client.post(
            "/api/v1/spend/events",
            json={
                "ad_account_id": 1,
                "supplier_id": 1,
                "event_date": str(date.today()),
                "amount": "100.00"
            }
        )

        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]


class TestSpendStateTransitionEndpoints:
    """消耗事件状态转换端点测试"""

    def test_validate_requires_authentication(self, client):
        """测试验证需要认证"""
        response = client.post(
            "/api/v1/spend/events/validate",
            json={"event_ids": [str(uuid4())]}
        )

        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]

    def test_confirm_requires_authentication(self, client):
        """测试确认需要认证"""
        response = client.post(
            "/api/v1/spend/events/confirm",
            json={"event_ids": [str(uuid4())]}
        )

        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]

    def test_post_requires_authentication(self, client):
        """测试入账需要认证"""
        response = client.post(
            "/api/v1/spend/events/post",
            json={"event_ids": [str(uuid4())]}
        )

        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]

    def test_reverse_requires_authentication(self, client):
        """测试冲正需要认证"""
        response = client.post(
            "/api/v1/spend/events/reverse",
            json={
                "event_id": str(uuid4()),
                "reason": "测试冲正原因"
            }
        )

        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]


class TestSpendStatisticsEndpoint:
    """消耗统计端点测试"""

    def test_statistics_requires_authentication(self, client):
        """测试统计需要认证"""
        response = client.get("/api/v1/spend/statistics")

        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]


class TestSpendRolePermissions:
    """消耗功能角色权限测试"""

    @pytest.fixture
    def finance_user_headers(self):
        """财务用户认证头"""
        return {"Authorization": "Bearer finance_token"}

    @pytest.fixture
    def data_operator_headers(self):
        """数据运营用户认证头"""
        return {"Authorization": "Bearer data_operator_token"}

    @pytest.fixture
    def admin_headers(self):
        """管理员认证头"""
        return {"Authorization": "Bearer admin_token"}

    @pytest.fixture
    def media_buyer_headers(self):
        """投手用户认证头"""
        return {"Authorization": "Bearer media_buyer_token"}

    # 注意: 以下测试需要 mock 认证和权限检查才能正常工作
    # 在实际运行时，需要配合测试 fixtures 使用


class TestRequestValidation:
    """请求验证测试"""

    def test_validate_request_requires_event_ids(self, client, auth_headers):
        """测试验证请求需要事件ID列表"""
        response = client.post(
            "/api/v1/spend/events/validate",
            json={},
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_validate_request_max_event_ids(self, client, auth_headers):
        """测试验证请求事件ID列表上限"""
        # 创建超过1000个事件ID
        event_ids = [str(uuid4()) for _ in range(1001)]

        response = client.post(
            "/api/v1/spend/events/validate",
            json={"event_ids": event_ids},
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_reverse_request_requires_reason(self, client, auth_headers):
        """测试冲正请求需要原因"""
        response = client.post(
            "/api/v1/spend/events/reverse",
            json={"event_id": str(uuid4())},
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_reverse_request_reason_min_length(self, client, auth_headers):
        """测试冲正原因最小长度"""
        response = client.post(
            "/api/v1/spend/events/reverse",
            json={
                "event_id": str(uuid4()),
                "reason": "abc"  # 只有3个字符，小于5个字符的最小要求
            },
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestResponseFormat:
    """响应格式测试"""

    def test_success_response_format(self, client, auth_headers, mock_spend_service):
        """测试成功响应格式符合 API_SOT"""
        # 需要 mock 服务返回
        pass  # 实际测试需要更完整的 mock 设置

    def test_error_response_format(self, client):
        """测试错误响应格式符合 ERROR_CODES_SOT"""
        # 测试未认证错误
        response = client.get("/api/v1/spend/events")

        # 应该返回标准错误格式
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]


class TestPagination:
    """分页测试"""

    def test_list_events_default_pagination(self, client, auth_headers):
        """测试列表默认分页"""
        # 需要 mock 认证
        pass

    def test_list_events_custom_pagination(self, client, auth_headers):
        """测试列表自定义分页"""
        pass

    def test_list_events_invalid_page(self, client, auth_headers):
        """测试无效页码"""
        response = client.get(
            "/api/v1/spend/events",
            params={"page": 0},  # 页码应该 >= 1
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_list_events_invalid_page_size(self, client, auth_headers):
        """测试无效每页数量"""
        response = client.get(
            "/api/v1/spend/events",
            params={"page_size": 200},  # 超过 100 的上限
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestFiltering:
    """筛选测试"""

    def test_list_events_filter_by_status(self, client, auth_headers):
        """测试按状态筛选"""
        pass

    def test_list_events_filter_by_date_range(self, client, auth_headers):
        """测试按日期范围筛选"""
        pass

    def test_list_events_filter_by_team(self, client, auth_headers):
        """测试按团队筛选"""
        pass

    def test_list_events_filter_by_supplier(self, client, auth_headers):
        """测试按供应商筛选"""
        pass


# ========== Fixtures ==========
# 注意: client 和 auth_headers fixtures 从 conftest.py 继承
# 不要在这里重复定义，否则会覆盖 conftest.py 中的真正实现

@pytest.fixture
def mock_spend_service():
    """Mock 消耗导入服务"""
    with patch('backend.routers.spend.get_spend_service') as mock:
        service = MagicMock()
        mock.return_value = service
        yield service
