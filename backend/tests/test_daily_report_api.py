"""
日报管理API集成测试
Version: 1.0
Author: Claude协作开发
"""

import pytest
import json
from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient


class TestDailyReportAPI:
    """日报管理API测试类"""

    def test_create_daily_report_success(self, client, auth_headers_user, test_ad_account, sample_daily_report_data):
        """测试成功创建日报"""
        # 更新数据为正确的账户ID
        sample_daily_report_data["ad_account_id"] = test_ad_account.id

        response = client.post(
            "/api/v1/daily-reports",
            json=sample_daily_report_data,
            headers=auth_headers_user
        )

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["report_date"] == "2024-01-15"
        assert data["data"]["status"] == "pending"
        assert data["data"]["campaign_name"] == "测试广告系列"

    def test_create_daily_report_unauthorized(self, client, sample_daily_report_data):
        """测试未授权创建日报"""
        response = client.post(
            "/api/v1/daily-reports",
            json=sample_daily_report_data
        )

        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] in ["SYS_002", "NOT_AUTHENTICATED"]

    def test_create_daily_report_invalid_data(self, client, auth_headers_user, sample_daily_report_data):
        """测试创建无效数据的日报"""
        # 点击数大于展示数
        sample_daily_report_data["impressions"] = 100
        sample_daily_report_data["clicks"] = 200

        response = client.post(
            "/api/v1/daily-reports",
            json=sample_daily_report_data,
            headers=auth_headers_user
        )

        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False

    def test_list_daily_reports_success(self, client, auth_headers_user):
        """测试成功获取日报列表"""
        response = client.get(
            "/api/v1/daily-reports",
            headers=auth_headers_user
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "items" in data["data"]
        assert "meta" in data["data"]
        assert "pagination" in data["data"]["meta"]

    def test_list_daily_reports_with_filters(self, client, auth_headers_user):
        """测试带筛选条件获取日报列表"""
        response = client.get(
            "/api/v1/daily-reports?status=pending&page=1&page_size=10",
            headers=auth_headers_user
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["meta"]["pagination"]["page"] == 1
        assert data["data"]["meta"]["pagination"]["page_size"] == 10

    def test_get_daily_report_detail_success(self, client, auth_headers_user, test_ad_account, sample_daily_report_data):
        """测试成功获取日报详情"""
        # 先创建日报
        sample_daily_report_data["ad_account_id"] = test_ad_account.id
        create_response = client.post(
            "/api/v1/daily-reports",
            json=sample_daily_report_data,
            headers=auth_headers_user
        )
        report_id = create_response.json()["data"]["id"]

        # 获取详情
        response = client.get(
            f"/api/v1/daily-reports/{report_id}",
            headers=auth_headers_user
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == report_id
        assert "ctr" in data["data"]  # 计算字段应该存在

    def test_get_daily_report_not_found(self, client, auth_headers_user):
        """测试获取不存在的日报"""
        response = client.get(
            "/api/v1/daily-reports/999999",
            headers=auth_headers_user
        )

        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "SYS_004"

    def test_update_daily_report_success(self, client, auth_headers_user, test_ad_account, sample_daily_report_data):
        """测试成功更新日报"""
        # 先创建日报
        sample_daily_report_data["ad_account_id"] = test_ad_account.id
        create_response = client.post(
            "/api/v1/daily-reports",
            json=sample_daily_report_data,
            headers=auth_headers_user
        )
        report_id = create_response.json()["data"]["id"]

        # 更新日报
        update_data = {
            "campaign_name": "更新后的广告系列",
            "impressions": 20000,
            "spend": "200.00"
        }
        response = client.put(
            f"/api/v1/daily-reports/{report_id}",
            json=update_data,
            headers=auth_headers_user
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["campaign_name"] == "更新后的广告系列"
        assert data["data"]["impressions"] == 20000
        assert data["data"]["spend"] == "200.00"

    def test_delete_daily_report_success(self, client, auth_headers_admin, test_ad_account, sample_daily_report_data):
        """测试成功删除日报（仅管理员）"""
        # 先创建日报
        sample_daily_report_data["ad_account_id"] = test_ad_account.id
        create_response = client.post(
            "/api/v1/daily-reports",
            json=sample_daily_report_data,
            headers=auth_headers_admin
        )
        report_id = create_response.json()["data"]["id"]

        # 删除日报
        response = client.delete(
            f"/api/v1/daily-reports/{report_id}",
            headers=auth_headers_admin
        )

        assert response.status_code == 204

        # 验证已删除
        response = client.get(
            f"/api/v1/daily-reports/{report_id}",
            headers=auth_headers_admin
        )
        assert response.status_code == 404

    def test_delete_daily_report_permission_denied(self, client, auth_headers_user, test_ad_account, sample_daily_report_data):
        """测试非管理员删除日报被拒绝"""
        # 先创建日报
        sample_daily_report_data["ad_account_id"] = test_ad_account.id
        create_response = client.post(
            "/api/v1/daily-reports",
            json=sample_daily_report_data,
            headers=auth_headers_user
        )
        report_id = create_response.json()["data"]["id"]

        # 尝试删除（普通用户）
        response = client.delete(
            f"/api/v1/daily-reports/{report_id}",
            headers=auth_headers_user
        )

        assert response.status_code == 403
        data = response.json()
        assert data["success"] is False
        assert "PERMISSION" in data["error"]["code"]

    def test_approve_daily_report_success(self, client, auth_headers_operator, test_ad_account, sample_daily_report_data):
        """测试成功审核日报"""
        # 先创建日报
        sample_daily_report_data["ad_account_id"] = test_ad_account.id
        create_response = client.post(
            "/api/v1/daily-reports",
            json=sample_daily_report_data,
            headers=auth_headers_operator
        )
        report_id = create_response.json()["data"]["id"]

        # 审核日报
        audit_data = {
            "audit_notes": "数据准确，审核通过"
        }
        response = client.post(
            f"/api/v1/daily-reports/{report_id}/approve",
            json=audit_data,
            headers=auth_headers_operator
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["status"] == "approved"
        assert data["data"]["audit_notes"] == "数据准确，审核通过"

    def test_approve_daily_report_permission_denied(self, client, auth_headers_user, test_ad_account, sample_daily_report_data):
        """测试非数据员审核日报被拒绝"""
        # 先创建日报
        sample_daily_report_data["ad_account_id"] = test_ad_account.id
        create_response = client.post(
            "/api/v1/daily-reports",
            json=sample_daily_report_data,
            headers=auth_headers_user
        )
        report_id = create_response.json()["data"]["id"]

        # 尝试审核（普通投手）
        audit_data = {
            "audit_notes": "审核通过"
        }
        response = client.post(
            f"/api/v1/daily-reports/{report_id}/approve",
            json=audit_data,
            headers=auth_headers_user
        )

        assert response.status_code == 403
        data = response.json()
        assert data["success"] is False

    def test_reject_daily_report_success(self, client, auth_headers_operator, test_ad_account, sample_daily_report_data):
        """测试成功驳回报日"""
        # 先创建日报
        sample_daily_report_data["ad_account_id"] = test_ad_account.id
        create_response = client.post(
            "/api/v1/daily-reports",
            json=sample_daily_report_data,
            headers=auth_headers_operator
        )
        report_id = create_response.json()["data"]["id"]

        # 驳回报日
        audit_data = {
            "audit_notes": "数据有误，请重新提交"
        }
        response = client.post(
            f"/api/v1/daily-reports/{report_id}/reject",
            json=audit_data,
            headers=auth_headers_operator
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["status"] == "rejected"
        assert data["data"]["audit_notes"] == "数据有误，请重新提交"

    def test_batch_import_success(self, client, auth_headers_operator, sample_batch_import_data):
        """测试批量导入成功"""
        response = client.post(
            "/api/v1/daily-reports/batch-import",
            json=sample_batch_import_data,
            headers=auth_headers_operator
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["total_count"] == 2
        assert data["data"]["success_count"] == 2
        assert data["data"]["error_count"] == 0

    def test_batch_import_with_errors(self, client, auth_headers_operator):
        """测试批量导入部分失败"""
        import_data = {
            "reports": [
                {
                    "report_date": "2024-01-15",
                    "ad_account_id": 1,
                    "impressions": 10000
                },
                {
                    "report_date": "2030-01-01",  # 无效日期
                    "ad_account_id": 1
                }
            ],
            "skip_errors": True
        }

        response = client.post(
            "/api/v1/daily-reports/batch-import",
            json=import_data,
            headers=auth_headers_operator
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["success_count"] == 1
        assert data["data"]["error_count"] == 1
        assert len(data["data"]["errors"]) == 1

    def test_import_file_success(self, client, auth_headers_operator, excel_file_content):
        """测试文件导入成功"""
        files = {
            "file": ("test_reports.xlsx", excel_file_content, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        }

        response = client.post(
            "/api/v1/daily-reports/import-file",
            files=files,
            headers=auth_headers_operator
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "total_count" in data["data"]
        assert "success_count" in data["data"]

    def test_import_file_invalid_format(self, client, auth_headers_operator):
        """测试导入无效格式文件"""
        files = {
            "file": ("test.txt", b"invalid file content", "text/plain")
        }

        response = client.post(
            "/api/v1/daily-reports/import-file",
            files=files,
            headers=auth_headers_operator
        )

        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "只支持Excel文件" in data["error"]["message"]

    def test_export_daily_reports_success(self, client, auth_headers_operator):
        """测试导出日报成功"""
        response = client.get(
            "/api/v1/daily-reports/export",
            headers=auth_headers_operator
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        assert "attachment" in response.headers["content-disposition"]

    def test_get_statistics_success(self, client, auth_headers_operator):
        """测试获取统计数据成功"""
        response = client.get(
            "/api/v1/daily-reports/statistics",
            headers=auth_headers_operator
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "total_reports" in data["data"]
        assert "approved_reports" in data["data"]
        assert "rejected_reports" in data["data"]
        assert "pending_reports" in data["data"]
        assert "total_spend" in data["data"]
        assert "ctr" in data["data"]
        assert "conversion_rate" in data["data"]

    def test_get_audit_logs_success(self, client, auth_headers_operator, test_ad_account, sample_daily_report_data):
        """测试获取审核日志成功"""
        # 先创建并操作日报
        sample_daily_report_data["ad_account_id"] = test_ad_account.id
        create_response = client.post(
            "/api/v1/daily-reports",
            json=sample_daily_report_data,
            headers=auth_headers_operator
        )
        report_id = create_response.json()["data"]["id"]

        # 审核日报
        client.post(
            f"/api/v1/daily-reports/{report_id}/approve",
            json={"audit_notes": "审核通过"},
            headers=auth_headers_operator
        )

        # 获取审计日志
        response = client.get(
            f"/api/v1/daily-reports/{report_id}/audit-logs",
            headers=auth_headers_operator
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
        assert len(data["data"]) >= 2  # 创建日志 + 审核日志

    def test_pagination_works_correctly(self, client, auth_headers_user):
        """测试分页功能正常工作"""
        # 测试第一页
        response = client.get(
            "/api/v1/daily-reports?page=1&page_size=5",
            headers=auth_headers_user
        )
        data = response.json()
        assert data["success"] is True
        assert data["data"]["meta"]["pagination"]["page"] == 1
        assert data["data"]["meta"]["pagination"]["page_size"] == 5

        # 测试第二页
        response = client.get(
            "/api/v1/daily-reports?page=2&page_size=5",
            headers=auth_headers_user
        )
        data = response.json()
        assert data["success"] is True
        assert data["data"]["meta"]["pagination"]["page"] == 2

    def test_search_functionality(self, client, auth_headers_user):
        """测试搜索功能"""
        # 按日期范围搜索
        response = client.get(
            "/api/v1/daily-reports?report_date_start=2024-01-01&report_date_end=2024-01-31",
            headers=auth_headers_user
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # 按状态搜索
        response = client.get(
            "/api/v1/daily-reports?status=pending",
            headers=auth_headers_user
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_response_format_consistency(self, client, auth_headers_user):
        """测试响应格式一致性"""
        # 测试列表响应格式
        response = client.get(
            "/api/v1/daily-reports",
            headers=auth_headers_user
        )
        data = response.json()
        assert "success" in data
        assert "data" in data
        assert "message" in data
        assert "code" in data
        assert "request_id" in data
        assert "timestamp" in data

    def test_error_handling_format(self, client, auth_headers_user):
        """测试错误处理格式"""
        # 测试404错误格式
        response = client.get(
            "/api/v1/daily-reports/999999",
            headers=auth_headers_user
        )
        data = response.json()
        assert data["success"] is False
        assert "error" in data
        assert "code" in data["error"]
        assert "message" in data["error"]