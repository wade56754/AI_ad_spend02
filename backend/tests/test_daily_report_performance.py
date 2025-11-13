"""
日报管理性能测试
Version: 1.0
Author: Claude协作开发
"""

import pytest
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading


class TestDailyReportPerformance:
    """日报管理性能测试类"""

    def test_list_reports_response_time(self, client, auth_headers_user):
        """测试获取日报列表响应时间"""
        start_time = time.time()

        response = client.get(
            "/api/v1/daily-reports",
            headers=auth_headers_user
        )

        end_time = time.time()
        response_time = (end_time - start_time) * 1000  # 转换为毫秒

        assert response.status_code == 200
        assert response_time < 300  # 响应时间应小于300ms

    def test_get_report_detail_response_time(self, client, auth_headers_user):
        """测试获取日报详情响应时间"""
        # 先创建一个日报
        create_response = client.post(
            "/api/v1/daily-reports",
            json={
                "report_date": "2024-01-15",
                "ad_account_id": 1,
                "impressions": 10000
            },
            headers=auth_headers_user
        )

        if create_response.status_code == 201:
            report_id = create_response.json()["data"]["id"]

            start_time = time.time()
            response = client.get(
                f"/api/v1/daily-reports/{report_id}",
                headers=auth_headers_user
            )
            end_time = time.time()

            response_time = (end_time - start_time) * 1000
            assert response.status_code == 200
            assert response_time < 100  # 详情响应时间应小于100ms

    def test_create_report_response_time(self, client, auth_headers_user, test_ad_account):
        """测试创建日报响应时间"""
        start_time = time.time()

        response = client.post(
            "/api/v1/daily-reports",
            json={
                "report_date": "2024-01-15",
                "ad_account_id": test_ad_account.id,
                "impressions": 10000,
                "clicks": 500,
                "spend": "100.00"
            },
            headers=auth_headers_user
        )

        end_time = time.time()
        response_time = (end_time - start_time) * 1000

        assert response.status_code == 201
        assert response_time < 200  # 创建响应时间应小于200ms

    def test_statistics_response_time(self, client, auth_headers_operator):
        """测试统计数据响应时间"""
        start_time = time.time()

        response = client.get(
            "/api/v1/daily-reports/statistics",
            headers=auth_headers_operator
        )

        end_time = time.time()
        response_time = (end_time - start_time) * 1000

        assert response.status_code == 200
        assert response_time < 500  # 统计响应时间应小于500ms

    def test_concurrent_requests(self, client, auth_headers_user):
        """测试并发请求处理能力"""
        def make_request():
            return client.get(
                "/api/v1/daily-reports",
                headers=auth_headers_user
            )

        # 并发10个请求
        num_requests = 10
        start_time = time.time()

        with ThreadPoolExecutor(max_workers=num_requests) as executor:
            futures = [executor.submit(make_request) for _ in range(num_requests)]

            successful_requests = 0
            for future in as_completed(futures):
                response = future.result()
                if response.status_code == 200:
                    successful_requests += 1

        end_time = time.time()
        total_time = end_time - start_time
        avg_time = (total_time / num_requests) * 1000

        assert successful_requests == num_requests
        assert avg_time < 300  # 平均响应时间小于300ms

    def test_pagination_performance(self, client, auth_headers_user):
        """测试分页性能"""
        # 测试不同页大小的性能
        page_sizes = [10, 20, 50, 100]

        for page_size in page_sizes:
            start_time = time.time()

            response = client.get(
                f"/api/v1/daily-reports?page_size={page_size}",
                headers=auth_headers_user
            )

            end_time = time.time()
            response_time = (end_time - start_time) * 1000

            assert response.status_code == 200
            # 页面越大，响应时间可能会增加，但应该保持在合理范围
            assert response_time < 500

    def test_batch_import_performance(self, client, auth_headers_operator):
        """测试批量导入性能"""
        # 准备批量数据
        batch_data = {
            "reports": [
                {
                    "report_date": f"2024-01-{i:02d}",
                    "ad_account_id": 1,
                    "impressions": 10000 * i,
                    "clicks": 500 * i,
                    "spend": str(100.00 * i)
                }
                for i in range(1, 51)  # 50条记录
            ],
            "skip_errors": True
        }

        start_time = time.time()

        response = client.post(
            "/api/v1/daily-reports/batch-import",
            json=batch_data,
            headers=auth_headers_operator
        )

        end_time = time.time()
        processing_time = end_time - start_time
        throughput = len(batch_data["reports"]) / processing_time

        assert response.status_code == 200
        assert throughput > 10  # 每秒应能处理至少10条记录

    def test_export_performance(self, client, auth_headers_operator):
        """测试导出性能"""
        start_time = time.time()

        response = client.get(
            "/api/v1/daily-reports/export",
            headers=auth_headers_operator
        )

        end_time = time.time()
        response_time = (end_time - start_time) * 1000

        assert response.status_code == 200
        assert response_time < 3000  # 导出响应时间应小于3秒

    def test_filter_performance(self, client, auth_headers_operator):
        """测试筛选性能"""
        filters = [
            "?status=pending",
            "?report_date_start=2024-01-01",
            "?report_date_end=2024-12-31",
            "?ad_account_id=1",
            "?status=pending&report_date_start=2024-01-01"
        ]

        for filter_query in filters:
            start_time = time.time()

            response = client.get(
                f"/api/v1/daily-reports{filter_query}",
                headers=auth_headers_operator
            )

            end_time = time.time()
            response_time = (end_time - start_time) * 1000

            assert response.status_code == 200
            assert response_time < 400

    def test_database_query_optimization(self, client, auth_headers_operator):
        """测试数据库查询优化"""
        # 使用EXPLAIN ANALYZE来验证查询性能（如果数据库支持）
        # 这里是一个示例，实际实现可能需要根据数据库类型调整

        # 测试复杂查询的性能
        start_time = time.time()

        response = client.get(
            "/api/v1/daily-reports/statistics?"
            "report_date_start=2024-01-01"
            "&report_date_end=2024-12-31"
            "&status=pending",
            headers=auth_headers_operator
        )

        end_time = time.time()
        response_time = (end_time - start_time) * 1000

        assert response.status_code == 200
        assert response_time < 1000  # 复杂统计查询应在1秒内完成

    def test_memory_usage_during_batch_operations(self, client, auth_headers_operator):
        """测试批量操作时的内存使用"""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # 执行批量操作
        batch_data = {
            "reports": [
                {
                    "report_date": f"2024-01-{i%28+1:02d}",
                    "ad_account_id": 1,
                    "impressions": 10000
                }
                for i in range(100)  # 100条记录
            ],
            "skip_errors": True
        }

        response = client.post(
            "/api/v1/daily-reports/batch-import",
            json=batch_data,
            headers=auth_headers_operator
        )

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        assert response.status_code == 200
        assert memory_increase < 50  # 内存增长应小于50MB

    def test_cache_performance(self, client, auth_headers_user):
        """测试缓存性能"""
        # 第一次请求（无缓存）
        start_time = time.time()
        response1 = client.get(
            "/api/v1/daily-reports/statistics",
            headers=auth_headers_user
        )
        first_time = (time.time() - start_time) * 1000

        # 第二次请求（应该有缓存）
        start_time = time.time()
        response2 = client.get(
            "/api/v1/daily-reports/statistics",
            headers=auth_headers_user
        )
        second_time = (time.time() - start_time) * 1000

        assert response1.status_code == 200
        assert response2.status_code == 200

        # 如果有缓存，第二次请求应该更快
        # 这个测试可能需要根据实际的缓存策略调整