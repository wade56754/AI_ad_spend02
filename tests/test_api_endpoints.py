#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
API端点测试
测试所有API接口的功能、权限和数据验证
"""

import pytest
import json
from decimal import Decimal
from datetime import date, datetime
from fastapi import status

from tests.conftest import pytest_marks, assert_decimal_equal


@pytest.mark.integration
@pytest.mark.api
class TestUserEndpoints:
    """用户相关API端点测试"""

    def test_register_user_success(self, client):
        """测试用户注册成功"""
        user_data = {
            "email": "newuser@test.com",
            "username": "newuser",
            "password": "Test123456!",
            "name": "新用户",
            "role": "client"
        }

        response = client.post("/api/auth/register", json=user_data)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["email"] == user_data["email"]
        assert data["username"] == user_data["username"]
        assert "password" not in data  # 密码不应返回

    def test_register_user_duplicate_email(self, client, test_user):
        """测试重复邮箱注册失败"""
        user_data = {
            "email": test_user.email,
            "username": "different",
            "password": "Test123456!",
            "name": "测试"
        }

        response = client.post("/api/auth/register", json=user_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already exists" in response.json()["detail"]

    def test_login_success(self, client, test_user):
        """测试登录成功"""
        login_data = {
            "email": test_user.email,
            "password": "Test123456!"
        }

        response = client.post("/api/auth/login", data=login_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_invalid_credentials(self, client):
        """测试登录失败（错误密码）"""
        login_data = {
            "email": "nonexistent@test.com",
            "password": "wrongpassword"
        }

        response = client.post("/api/auth/login", data=login_data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_current_user(self, client, auth_headers_user):
        """测试获取当前用户信息"""
        response = client.get("/api/users/me", headers=auth_headers_user)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "email" in data
        assert "role" in data

    def test_get_current_user_unauthorized(self, client):
        """测试未授权访问用户信息"""
        response = client.get("/api/users/me")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.parametrize("role,expected_status", [
        ("admin", status.HTTP_200_OK),
        ("manager", status.HTTP_200_OK),
        ("client", status.HTTP_403_FORBIDDEN),
    ])
    def test_list_users_by_role(self, client, role, expected_status):
        """测试根据角色获取用户列表"""
        # 创建不同角色的测试用户
        headers = {
            "Authorization": f"Bearer {self._create_token_for_role(role)}"
        }

        response = client.get("/api/users", headers=headers)

        assert response.status_code == expected_status

    def _create_token_for_role(self, role: str) -> str:
        """辅助函数：为特定角色创建token"""
        # 这里应该实现真实的token创建逻辑
        return "mock_token"


@pytest.mark.integration
@pytest.mark.api
class TestProjectEndpoints:
    """项目相关API端点测试"""

    def test_create_project_success(self, client, auth_headers_user, test_channel):
        """测试创建项目成功"""
        project_data = {
            "name": "新测试项目",
            "description": "项目描述",
            "channel_id": test_channel.id,
            "total_budget": 10000.00,
            "daily_budget": 500.00,
            "cpl_target": 50.00,
            "cpl_tolerance": 5.00
        }

        response = client.post(
            "/api/projects",
            json=project_data,
            headers=auth_headers_user
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == project_data["name"]
        assert data["total_budget"] == project_data["total_budget"]

    def test_create_project_invalid_budget(self, client, auth_headers_user):
        """测试创建项目（无效预算）"""
        project_data = {
            "name": "无效预算项目",
            "total_budget": -1000,  # 负预算
            "daily_budget": 0
        }

        response = client.post(
            "/api/projects",
            json=project_data,
            headers=auth_headers_user
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_get_projects(self, client, auth_headers_user, test_project):
        """测试获取项目列表"""
        response = client.get("/api/projects", headers=auth_headers_user)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) > 0
        assert any(p["id"] == str(test_project.id) for p in data)

    def test_get_project_detail(self, client, auth_headers_user, test_project):
        """测试获取项目详情"""
        response = client.get(
            f"/api/projects/{test_project.id}",
            headers=auth_headers_user
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(test_project.id)
        assert data["name"] == test_project.name

    def test_update_project(self, client, auth_headers_user, test_project):
        """测试更新项目"""
        update_data = {
            "name": "更新后的项目名",
            "total_budget": 15000.00
        }

        response = client.patch(
            f"/api/projects/{test_project.id}",
            json=update_data,
            headers=auth_headers_user
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["total_budget"] == update_data["total_budget"]

    def test_delete_project(self, client, auth_headers_admin, test_project):
        """测试删除项目（仅管理员）"""
        response = client.delete(
            f"/api/projects/{test_project.id}",
            headers=auth_headers_admin
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_delete_project_unauthorized(self, client, auth_headers_user, test_project):
        """测试普通用户删除项目失败"""
        response = client.delete(
            f"/api/projects/{test_project.id}",
            headers=auth_headers_user
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.integration
@pytest.mark.api
class TestTopUpEndpoints:
    """充值相关API端点测试"""

    def test_create_topup_success(self, client, auth_headers_user, test_project, test_channel):
        """测试创建充值申请成功"""
        topup_data = {
            "project_id": str(test_project.id),
            "channel_id": str(test_channel.id),
            "amount": 1000.00,
            "receipt_image": "receipt.jpg",
            "notes": "测试充值"
        }

        response = client.post(
            "/api/topups",
            json=topup_data,
            headers=auth_headers_user
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["amount"] == topup_data["amount"]
        assert data["status"] == "draft"

    def test_submit_topup_for_approval(self, client, auth_headers_user, test_topup):
        """测试提交充值申请审批"""
        response = client.post(
            f"/api/topups/{test_topup.id}/submit",
            headers=auth_headers_user
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "pending"
        assert data["submitted_at"] is not None

    def test_approve_topup(self, client, auth_headers_admin, test_topup):
        """测试审批充值申请"""
        # 先提交审批
        client.post(f"/api/topups/{test_topup.id}/submit")

        approve_data = {
            "notes": "审批通过",
            "actual_amount": 1000.00
        }

        response = client.post(
            f"/api/topups/{test_topup.id}/approve",
            json=approve_data,
            headers=auth_headers_admin
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "approved"
        assert data["approved_by"] is not None

    def test_approve_topup_unauthorized(self, client, auth_headers_user, test_topup):
        """测试普通用户审批失败"""
        response = client.post(
            f"/api/topups/{test_topup.id}/approve",
            headers=auth_headers_user
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_list_topups_by_status(self, client, auth_headers_admin):
        """测试按状态筛选充值申请"""
        response = client.get(
            "/api/topups?status=pending",
            headers=auth_headers_admin
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        for topup in data:
            assert topup["status"] == "pending"

    def test_get_topup_statistics(self, client, auth_headers_admin):
        """测试获取充值统计"""
        response = client.get(
            "/api/topups/statistics",
            headers=auth_headers_admin
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "total_amount" in data
        assert "pending_count" in data
        assert "approved_count" in data


@pytest.mark.integration
@pytest.mark.api
class TestReportEndpoints:
    """报表相关API端点测试"""

    def test_upload_daily_report(self, client, auth_headers_user, test_ad_account):
        """测试上传日报数据"""
        report_data = {
            "account_id": str(test_ad_account.id),
            "report_date": str(date.today()),
            "impressions": 10000,
            "clicks": 500,
            "conversions": 10,
            "spend": 250.00,
            "revenue": 500.00
        }

        response = client.post(
            "/api/reports/daily",
            json=report_data,
            headers=auth_headers_user
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["impressions"] == report_data["impressions"]
        assert data["spend"] == report_data["spend"]

    def test_batch_upload_reports(self, client, auth_headers_user, test_ad_account):
        """测试批量上传日报"""
        reports = [
            {
                "account_id": str(test_ad_account.id),
                "report_date": str(date.today()),
                "impressions": 10000,
                "clicks": 500,
                "spend": 250.00
            },
            {
                "account_id": str(test_ad_account.id),
                "report_date": str(date(2025, 1, 1)),
                "impressions": 15000,
                "clicks": 750,
                "spend": 350.00
            }
        ]

        response = client.post(
            "/api/reports/batch",
            json={"reports": reports},
            headers=auth_headers_user
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["success_count"] == 2

    def test_get_reports_by_date_range(self, client, auth_headers_user):
        """测试按日期范围获取报表"""
        start_date = "2025-01-01"
        end_date = "2025-01-31"

        response = client.get(
            f"/api/reports?start_date={start_date}&end_date={end_date}",
            headers=auth_headers_user
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # 验证日期范围
        for report in data:
            assert start_date <= report["report_date"] <= end_date

    def test_get_project_performance(self, client, auth_headers_user, test_project):
        """测试获取项目绩效报表"""
        response = client.get(
            f"/api/projects/{test_project.id}/performance",
            headers=auth_headers_user
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "total_spend" in data
        assert "total_conversions" in data
        assert "actual_cpl" in data
        assert "cpl_variance" in data

    def test_export_reports_to_excel(self, client, auth_headers_user):
        """测试导出报表到Excel"""
        response = client.get(
            "/api/reports/export?format=excel",
            headers=auth_headers_user
        )

        assert response.status_code == status.HTTP_200_OK
        assert "application/vnd.openxmlformats-officedocument" in response.headers["content-type"]


@pytest.mark.integration
@pytest.mark.api
class TestFinancialEndpoints:
    """财务相关API端点测试"""

    def test_get_ledger_entries(self, client, auth_headers_admin):
        """测试获取财务流水"""
        response = client.get(
            "/api/financial/ledger",
            headers=auth_headers_admin
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    def test_reconcile_transactions(self, client, auth_headers_admin):
        """测试自动对账"""
        response = client.post(
            "/api/financial/reconcile",
            json={"date_range": {"start": "2025-01-01", "end": "2025-01-31"}},
            headers=auth_headers_admin
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "matched_count" in data
        assert "discrepancies" in data

    def test_get_budget_utilization(self, client, auth_headers_user, test_project):
        """测试获取预算使用率"""
        response = client.get(
            f"/api/projects/{test_project.id}/budget-utilization",
            headers=auth_headers_user
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "total_budget" in data
        assert "used_budget" in data
        assert "utilization_rate" in data
        assert "remaining_days" in data


@pytest.mark.integration
@pytest.mark.api
class TestAuditEndpoints:
    """审计相关API端点测试"""

    def test_get_audit_logs(self, client, auth_headers_admin):
        """测试获取审计日志"""
        response = client.get(
            "/api/audit/logs",
            headers=auth_headers_admin
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    def test_get_audit_logs_by_resource(self, client, auth_headers_admin, test_project):
        """测试获取特定资源的审计日志"""
        response = client.get(
            f"/api/audit/logs?resource_type=project&resource_id={test_project.id}",
            headers=auth_headers_admin
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        for log in data:
            assert log["resource_type"] == "project"
            assert log["resource_id"] == str(test_project.id)

    def test_get_user_activity_log(self, client, auth_headers_user):
        """测试获取用户活动日志"""
        response = client.get(
            "/api/audit/my-activities",
            headers=auth_headers_user
        )

        assert response.status_code == status.HTTP_200_OK


@pytest.mark.integration
@pytest.mark.api
class TestSystemEndpoints:
    """系统相关API端点测试"""

    def test_health_check(self, client):
        """测试健康检查"""
        response = client.get("/api/health")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data

    def test_get_system_info(self, client, auth_headers_admin):
        """测试获取系统信息"""
        response = client.get(
            "/api/system/info",
            headers=auth_headers_admin
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "database" in data
        assert "redis" in data
        assert "version" in data

    def test_get_system_stats(self, client, auth_headers_admin):
        """测试获取系统统计"""
        response = client.get(
            "/api/system/stats",
            headers=auth_headers_admin
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "total_users" in data
        assert "total_projects" in data
        assert "total_topups" in data


@pytest.mark.integration
@pytest.mark.api
class TestErrorHandling:
    """错误处理测试"""

    def test_404_not_found(self, client):
        """测试404错误"""
        response = client.get("/api/nonexistent-endpoint")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "detail" in data

    def test_validation_error(self, client):
        """测试验证错误"""
        response = client.post(
            "/api/projects",
            json={"invalid": "data"}
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        assert "detail" in data

    def test_rate_limit(self, client):
        """测试速率限制（如果实现）"""
        # 快速发送多个请求
        for _ in range(100):
            response = client.get("/api/health")

        # 检查是否被限制
        response = client.get("/api/health")
        # 这里取决于具体的限流实现
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_429_TOO_MANY_REQUESTS]

    def test_cors_headers(self, client):
        """测试CORS头"""
        response = client.options("/api/health")

        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers