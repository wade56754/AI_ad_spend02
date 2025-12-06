# -*- coding: utf-8 -*-
"""
Import Jobs API Smoke Tests

测试 import_jobs 模块的基本 API 端点：
- 列表获取
- 单条查询
- 文件上传

SoT References:
- docs/2.sot/ERROR_CODES_SOT.md v2.2 (错误码定义)
- docs/2.sot/API_SOT.md v9.0 (API 规范)

Generated for: backend/tests/api/test_import_jobs_smoke.py
"""

import io
import pytest
from uuid import uuid4


# ============================================================================
# API 端点常量
# ============================================================================

API_BASE = "/api/v1"
IMPORT_JOBS_URL = f"{API_BASE}/import_jobs"


def import_job_url(job_id: str) -> str:
    """生成导入任务详情 URL"""
    return f"{IMPORT_JOBS_URL}/{job_id}"


# ============================================================================
# Smoke Tests - 基本功能测试
# ============================================================================

@pytest.mark.api
class TestImportJobsSmoke:
    """
    Smoke Tests: 导入任务模块基本功能验证

    覆盖场景:
    1. 获取任务列表 (GET /)
    2. 获取任务详情 (GET /{job_id})
    3. 上传文件创建任务 (POST /upload)
    4. 参数校验 (status/type 枚举值)
    5. 404 资源不存在
    """

    def test_list_import_jobs__returns_200_with_pagination(
        self, client, auth_headers
    ):
        """
        获取导入任务列表 - 返回 200 和分页信息

        验证:
        - HTTP 200
        - success: true
        - meta.pagination 存在
        """
        # Act
        response = client.get(IMPORT_JOBS_URL, headers=auth_headers)

        # Assert
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("success") is True
        assert "data" in data
        assert "meta" in data
        assert "pagination" in data["meta"]

    def test_list_import_jobs__filter_by_status(
        self, client, auth_headers
    ):
        """
        按状态过滤任务列表

        验证:
        - HTTP 200
        - 支持 status 参数
        """
        # Act
        response = client.get(
            IMPORT_JOBS_URL,
            params={"status": "pending"},
            headers=auth_headers,
        )

        # Assert
        assert response.status_code == 200

    def test_list_import_jobs__filter_by_type(
        self, client, auth_headers
    ):
        """
        按类型过滤任务列表

        验证:
        - HTTP 200
        - 支持 type 参数
        """
        # Act
        response = client.get(
            IMPORT_JOBS_URL,
            params={"type": "finance"},
            headers=auth_headers,
        )

        # Assert
        assert response.status_code == 200

    def test_list_import_jobs__invalid_status_returns_400(
        self, client, auth_headers
    ):
        """
        无效 status 参数 - 返回 400

        验证:
        - HTTP 400
        - 错误码为 VALIDATION_006
        """
        # Act
        response = client.get(
            IMPORT_JOBS_URL,
            params={"status": "invalid_status"},
            headers=auth_headers,
        )

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert data.get("success") is False
        # 验证错误码
        assert data.get("code") == "VALIDATION_006"

    def test_list_import_jobs__invalid_type_returns_400(
        self, client, auth_headers
    ):
        """
        无效 type 参数 - 返回 400

        验证:
        - HTTP 400
        - 错误码为 VALIDATION_006
        """
        # Act
        response = client.get(
            IMPORT_JOBS_URL,
            params={"type": "invalid_type"},
            headers=auth_headers,
        )

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert data.get("success") is False
        assert data.get("code") == "VALIDATION_006"

    def test_get_import_job__not_found_returns_404(
        self, client, auth_headers
    ):
        """
        获取不存在的任务 - 返回 404

        验证:
        - HTTP 404
        - 错误码为 BIZ_002
        """
        # Arrange
        fake_job_id = str(uuid4())

        # Act
        response = client.get(
            import_job_url(fake_job_id),
            headers=auth_headers,
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert data.get("success") is False
        assert data.get("code") == "BIZ_002"

    def test_upload_csv__returns_201_on_success(
        self, client, auth_headers
    ):
        """
        上传 CSV 文件成功 - 返回 201

        验证:
        - HTTP 201
        - success: true
        - 返回 job_id
        """
        # Arrange
        csv_content = "name,value\ntest1,100\ntest2,200\n"
        csv_file = io.BytesIO(csv_content.encode("utf-8"))

        # Act
        response = client.post(
            f"{IMPORT_JOBS_URL}/upload",
            files={"file": ("test.csv", csv_file, "text/csv")},
            params={"type": "finance"},
            headers=auth_headers,
        )

        # Assert
        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("success") is True
        assert "job_id" in data.get("data", {})

    def test_upload_csv__empty_file_returns_400(
        self, client, auth_headers
    ):
        """
        上传空文件 - 返回 400

        验证:
        - HTTP 400
        - 错误码为 BIZ_503
        """
        # Arrange
        empty_file = io.BytesIO(b"")

        # Act
        response = client.post(
            f"{IMPORT_JOBS_URL}/upload",
            files={"file": ("empty.csv", empty_file, "text/csv")},
            headers=auth_headers,
        )

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert data.get("success") is False
        assert data.get("code") == "BIZ_503"

    def test_upload_csv__invalid_file_type_returns_400(
        self, client, auth_headers
    ):
        """
        上传非 CSV 文件 - 返回 400

        验证:
        - HTTP 400
        - 错误码为 BIZ_500
        """
        # Arrange
        txt_content = b"This is not a CSV file"
        txt_file = io.BytesIO(txt_content)

        # Act
        response = client.post(
            f"{IMPORT_JOBS_URL}/upload",
            files={"file": ("test.txt", txt_file, "text/plain")},
            headers=auth_headers,
        )

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert data.get("success") is False
        assert data.get("code") == "BIZ_500"

    def test_upload_csv__invalid_type_param_returns_400(
        self, client, auth_headers
    ):
        """
        上传时指定无效 type 参数 - 返回 400

        验证:
        - HTTP 400
        - 错误码为 VALIDATION_006
        """
        # Arrange
        csv_content = "name,value\ntest1,100\n"
        csv_file = io.BytesIO(csv_content.encode("utf-8"))

        # Act
        response = client.post(
            f"{IMPORT_JOBS_URL}/upload",
            files={"file": ("test.csv", csv_file, "text/csv")},
            params={"type": "invalid_type"},
            headers=auth_headers,
        )

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert data.get("success") is False
        assert data.get("code") == "VALIDATION_006"


@pytest.mark.api
class TestImportJobsAuth:
    """
    认证测试: 未授权请求

    验证无 token 时返回 401
    """

    def test_list_import_jobs__no_auth_returns_401(self, client):
        """
        无认证获取列表 - 返回 401
        """
        # Act
        response = client.get(IMPORT_JOBS_URL)

        # Assert
        assert response.status_code == 401

    def test_get_import_job__no_auth_returns_401(self, client):
        """
        无认证获取详情 - 返回 401
        """
        # Act
        response = client.get(import_job_url(str(uuid4())))

        # Assert
        assert response.status_code == 401

    def test_upload__no_auth_returns_401(self, client):
        """
        无认证上传 - 返回 401
        """
        # Arrange
        csv_file = io.BytesIO(b"name,value\ntest,100\n")

        # Act
        response = client.post(
            f"{IMPORT_JOBS_URL}/upload",
            files={"file": ("test.csv", csv_file, "text/csv")},
        )

        # Assert
        assert response.status_code == 401
