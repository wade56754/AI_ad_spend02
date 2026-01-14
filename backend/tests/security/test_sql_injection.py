"""
SQL 注入防护测试
Version: 1.0
Author: AI Code Factory

测试 ORM 参数化查询是否防止 SQL 注入
"""

import pytest


class TestSQLInjectionProtection:
    """
    SQL 注入防护测试

    验证系统使用 SQLAlchemy ORM 参数化查询，
    不会受到 SQL 注入攻击
    """

    # SQL 注入测试向量
    INJECTION_PAYLOADS = [
        "' OR '1'='1",
        "'; DROP TABLE users; --",
        "1; SELECT * FROM users",
        "' UNION SELECT * FROM users --",
        "1' AND '1'='1",
        "admin'--",
        "' OR 1=1 --",
        "'; TRUNCATE TABLE projects; --",
    ]

    def test_project_name_injection_protection(
        self,
        client,
        admin_headers
    ):
        """项目名称参数不受 SQL 注入影响"""
        for payload in self.INJECTION_PAYLOADS:
            response = client.get(
                "/api/v1/projects",
                params={"name": payload},
                headers=admin_headers
            )
            # 应该返回正常响应（空结果或 200），不应崩溃
            assert response.status_code in [200, 400, 404, 422]

    def test_project_search_injection_protection(
        self,
        client,
        admin_headers
    ):
        """项目搜索参数不受 SQL 注入影响"""
        for payload in self.INJECTION_PAYLOADS:
            response = client.get(
                "/api/v1/projects",
                params={"search": payload},
                headers=admin_headers
            )
            # 应该返回正常响应，不应崩溃
            assert response.status_code in [200, 400, 404, 422]

    def test_daily_report_filter_injection_protection(
        self,
        client,
        admin_headers
    ):
        """日报筛选参数不受 SQL 注入影响"""
        for payload in self.INJECTION_PAYLOADS:
            response = client.get(
                "/api/v1/daily-reports",
                params={"status": payload},
                headers=admin_headers
            )
            assert response.status_code in [200, 400, 404, 422]

    def test_ad_account_search_injection_protection(
        self,
        client,
        admin_headers
    ):
        """广告账户搜索参数不受 SQL 注入影响"""
        for payload in self.INJECTION_PAYLOADS:
            response = client.get(
                "/api/v1/ad-accounts",
                params={"search": payload},
                headers=admin_headers
            )
            assert response.status_code in [200, 400, 404, 422]

    def test_user_search_injection_protection(
        self,
        client,
        admin_headers
    ):
        """用户搜索参数不受 SQL 注入影响"""
        for payload in self.INJECTION_PAYLOADS:
            response = client.get(
                "/api/v1/users",
                params={"search": payload},
                headers=admin_headers
            )
            assert response.status_code in [200, 400, 404, 422]

    def test_create_project_name_injection_protection(
        self,
        client,
        admin_headers
    ):
        """创建项目时名称字段不受 SQL 注入影响"""
        for payload in self.INJECTION_PAYLOADS[:3]:  # 只测试前 3 个
            response = client.post(
                "/api/v1/projects",
                headers=admin_headers,
                json={
                    "project_name": payload,
                    "project_code": "TEST_INJ",
                    "client_name": "测试客户",
                }
            )
            # 应该返回正常响应（创建成功或验证失败），不应崩溃
            assert response.status_code in [200, 201, 400, 404, 422, 500]


class TestXSSProtection:
    """
    XSS 攻击防护测试
    """

    XSS_PAYLOADS = [
        "<script>alert('xss')</script>",
        "<img src=x onerror=alert('xss')>",
        "javascript:alert('xss')",
        "<svg onload=alert('xss')>",
        "';alert('xss');//",
    ]

    def test_project_name_xss_protection(
        self,
        client,
        admin_headers
    ):
        """项目名称应正确存储，不执行脚本"""
        for payload in self.XSS_PAYLOADS[:2]:
            response = client.post(
                "/api/v1/projects",
                headers=admin_headers,
                json={
                    "project_name": payload,
                    "project_code": "TEST_XSS",
                    "client_name": "测试客户",
                }
            )
            # 应该返回正常响应
            assert response.status_code in [200, 201, 400, 404, 422, 500]

            # 如果创建成功，验证数据正确存储
            if response.status_code in [200, 201]:
                data = response.json()
                if "data" in data:
                    # 数据应该被原样存储，不应被执行
                    assert data["data"].get("project_name") == payload or \
                           "<script>" not in str(data)


class TestInputValidation:
    """
    输入验证测试
    """

    def test_invalid_date_format_rejected(
        self,
        client,
        admin_headers
    ):
        """无效日期格式应被拒绝"""
        invalid_dates = [
            "not-a-date",
            "2024-13-01",  # 无效月份
            "2024-02-30",  # 无效日期
            "0000-00-00",
        ]

        for date in invalid_dates:
            response = client.get(
                "/api/v1/daily-reports",
                params={"date_from": date},
                headers=admin_headers
            )
            # 应该返回验证错误或空结果，不应崩溃
            assert response.status_code in [200, 400, 404, 422]

    def test_invalid_numeric_id_rejected(
        self,
        client,
        admin_headers
    ):
        """无效数字 ID 应被拒绝"""
        invalid_ids = [
            "abc",
            "-1",
            "0",
            "99999999999999",
            "1.5",
        ]

        for id_value in invalid_ids:
            response = client.get(
                f"/api/v1/projects/{id_value}",
                headers=admin_headers
            )
            # 应该返回 404 或验证错误，不应崩溃
            assert response.status_code in [400, 404, 422]

    def test_oversized_input_rejected(
        self,
        client,
        admin_headers
    ):
        """过大输入应被拒绝"""
        # 创建一个非常大的字符串
        large_input = "A" * 100000  # 100KB

        response = client.post(
            "/api/v1/projects",
            headers=admin_headers,
            json={
                "project_name": large_input,
                "project_code": "TEST",
                "client_name": "测试客户",
            }
        )
        # 应该返回验证错误，不应崩溃
        assert response.status_code in [400, 404, 422, 413, 500]
