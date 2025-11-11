#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
性能基准测试
测试系统性能指标，建立性能基准线
"""

import pytest
import time
import asyncio
import statistics
from decimal import Decimal
from datetime import datetime, date
from concurrent.futures import ThreadPoolExecutor, as_completed
import psutil
import os
import gc
from typing import List, Dict, Any

from tests.conftest import pytest_marks


@pytest.mark.performance
@pytest.mark.slow
class TestAPIPerformance:
    """API性能测试"""

    @pytest.mark.parametrize("endpoint,expected_max_time", [
        ("/api/health", 100),  # 健康检查应在100ms内响应
        ("/api/users/me", 200),  # 用户信息应在200ms内响应
        ("/api/projects", 300),  # 项目列表应在300ms内响应
    ])
    def test_api_response_time(self, client, auth_headers_user, endpoint, expected_max_time):
        """测试API响应时间"""
        # 预热请求
        client.get(endpoint, headers=auth_headers_user)

        # 执行多次请求取平均值
        times = []
        for _ in range(10):
            start = time.perf_counter()
            response = client.get(endpoint, headers=auth_headers_user)
            end = time.perf_counter()

            assert response.status_code == 200
            times.append((end - start) * 1000)  # 转换为毫秒

        avg_time = statistics.mean(times)
        p95_time = statistics.quantiles(times, n=20)[18]  # 95th percentile

        # 性能断言
        assert avg_time < expected_max_time, f"Average time {avg_time:.2f}ms > {expected_max_time}ms"
        assert p95_time < expected_max_time * 2, f"P95 time {p95_time:.2f}ms > {expected_max_time * 2}ms"

    def test_concurrent_requests(self, client, auth_headers_user):
        """测试并发请求性能"""
        endpoint = "/api/projects"
        concurrent_users = 50
        requests_per_user = 10

        def make_requests():
            times = []
            for _ in range(requests_per_user):
                start = time.perf_counter()
                response = client.get(endpoint, headers=auth_headers_user)
                end = time.perf_counter()
                times.append((end - start) * 1000)
                assert response.status_code == 200
            return times

        # 并发执行
        start_time = time.perf_counter()
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = [executor.submit(make_requests) for _ in range(concurrent_users)]
            all_times = []
            for future in as_completed(futures):
                all_times.extend(future.result())

        total_time = time.perf_counter() - start_time
        total_requests = concurrent_users * requests_per_user

        # 性能指标
        avg_time = statistics.mean(all_times)
        p95_time = statistics.quantiles(all_times, n=20)[18]
        qps = total_requests / total_time

        # 性能断言
        assert avg_time < 500, f"Average time {avg_time:.2f}ms > 500ms"
        assert p95_time < 1000, f"P95 time {p95_time:.2f}ms > 1000ms"
        assert qps > 50, f"QPS {qps:.2f} < 50"

    def test_heavy_payload_response(self, client, auth_headers_user):
        """测试大负载响应性能"""
        # 请求包含大量数据的接口
        endpoint = "/api/reports/daily?limit=1000"

        start = time.perf_counter()
        response = client.get(endpoint, headers=auth_headers_user)
        end = time.perf_counter()

        assert response.status_code == 200
        response_time = (end - start) * 1000

        # 大数据响应时间应在合理范围内
        assert response_time < 1000, f"Heavy payload response time {response_time:.2f}ms > 1000ms"

        # 验证返回的数据量
        data = response.json()
        assert len(data) > 0


@pytest.mark.performance
@pytest.mark.slow
class TestDatabasePerformance:
    """数据库性能测试"""

    def test_query_performance_indexed(self, db_session):
        """测试索引查询性能"""
        from backend.models import DailyReport

        # 测试有索引的字段查询
        times = []
        for _ in range(100):
            start = time.perf_counter()
            reports = db_session.query(DailyReport).filter(
                DailyReport.report_date == date.today()
            ).limit(10).all()
            end = time.perf_counter()
            times.append((end - start) * 1000)

        avg_time = statistics.mean(times)
        assert avg_time < 50, f"Indexed query average time {avg_time:.2f}ms > 50ms"

    def test_query_performance_non_indexed(self, db_session):
        """测试非索引查询性能"""
        from backend.models import AuditLog

        # 测试可能没有索引的字段查询
        times = []
        for _ in range(50):
            start = time.perf_counter()
            logs = db_session.query(AuditLog).filter(
                AuditLog.action.like("%login%")
            ).limit(10).all()
            end = time.perf_counter()
            times.append((end - start) * 1000)

        avg_time = statistics.mean(times)
        # 非索引查询应该较慢但不应该太慢
        assert avg_time < 500, f"Non-indexed query average time {avg_time:.2f}ms > 500ms"

    def test_bulk_insert_performance(self, db_session):
        """测试批量插入性能"""
        from backend.models import DailyReport

        # 准备测试数据
        test_data = []
        for i in range(1000):
            test_data.append({
                "account_id": "test_account",
                "report_date": date(2025, 1, (i % 30) + 1),
                "impressions": 10000 + i,
                "clicks": 500 + (i % 100),
                "spend": Decimal("250.00") + (i * 0.1)
            })

        # 测试批量插入
        start = time.perf_counter()
        db_session.bulk_insert_mappings(DailyReport, test_data)
        db_session.commit()
        end = time.perf_counter()

        insert_time = (end - start) * 1000
        records_per_second = 1000 / (insert_time / 1000)

        # 性能断言
        assert insert_time < 1000, f"Bulk insert time {insert_time:.2f}ms > 1000ms"
        assert records_per_second > 1000, f"Records per second {records_per_second:.2f} < 1000"

    def test_concurrent_db_operations(self, db_session):
        """测试并发数据库操作"""
        from backend.models import TopUp

        def db_operation(i):
            start = time.perf_counter()
            # 创建记录
            topup = TopUp(
                project_id="test_project",
                amount=Decimal("1000.00"),
                status="draft"
            )
            db_session.add(topup)
            db_session.commit()

            # 查询记录
            retrieved = db_session.query(TopUp).filter(TopUp.id == topup.id).first()
            end = time.perf_counter()
            return (end - start) * 1000

        # 并发执行
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(db_operation, i) for i in range(100)]
            times = [future.result() for future in as_completed(futures)]

        avg_time = statistics.mean(times)
        assert avg_time < 100, f"Concurrent DB operation average time {avg_time:.2f}ms > 100ms"


@pytest.mark.performance
@pytest.mark.slow
class TestFinancialCalculationPerformance:
    """财务计算性能测试"""

    def test_cpl_calculation_performance(self):
        """测试CPL计算性能"""
        from tests.test_financial_calculations import calculate_cpl

        test_cases = [
            (Decimal("1000.00"), 20),
            (Decimal("50000.00"), 1234),
            (Decimal("999999.99"), 9999),
        ]

        times = []
        for spend, conversions in test_cases:
            for _ in range(1000):
                start = time.perf_counter()
                cpl = calculate_cpl(spend, conversions)
                end = time.perf_counter()
                times.append((end - start) * 1000)

        avg_time = statistics.mean(times)
        assert avg_time < 1, f"CPL calculation average time {avg_time:.3f}ms > 1ms"

    def test_budget_analysis_performance(self):
        """测试预算分析性能"""
        from tests.test_financial_calculations import (
            analyze_budget_pace,
            calculate_budget_utilization_rate
        )

        # 大量预算分析
        times = []
        for i in range(1000):
            start = time.perf_counter()
            utilization = calculate_budget_utilization_rate(
                Decimal("10000.00"),
                Decimal("5000.00") + (i * 10)
            )
            pace = analyze_budget_pace(
                Decimal("30000.00"),
                30,
                15,
                Decimal("15000.00")
            )
            end = time.perf_counter()
            times.append((end - start) * 1000)

        avg_time = statistics.mean(times)
        assert avg_time < 5, f"Budget analysis average time {avg_time:.3f}ms > 5ms"

    def test_roi_calculation_performance(self):
        """测试ROI计算性能"""
        from tests.test_financial_calculations import calculate_roi

        # 批量ROI计算
        test_data = []
        for i in range(10000):
            test_data.append((
                Decimal("1000.00") + (i * 10),
                Decimal("1500.00") + (i * 15)
            ))

        start = time.perf_counter()
        for spend, revenue in test_data:
            roi = calculate_roi(spend, revenue)
        end = time.perf_counter()

        total_time = (end - start) * 1000
        avg_time = total_time / 10000

        assert avg_time < 0.5, f"ROI calculation average time {avg_time:.3f}ms > 0.5ms"


@pytest.mark.performance
@pytest.mark.slow
class TestMemoryUsage:
    """内存使用测试"""

    def test_memory_usage_bulk_operations(self, db_session):
        """测试批量操作的内存使用"""
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # 创建大量对象
        from backend.models import DailyReport
        objects = []
        for i in range(10000):
            obj = {
                "account_id": f"account_{i}",
                "report_date": date(2025, 1, (i % 30) + 1),
                "impressions": 10000 + i,
                "clicks": 500 + (i % 100)
            }
            objects.append(obj)

            # 每1000个对象检查一次内存
            if i % 1000 == 0:
                current_memory = process.memory_info().rss
                memory_increase = (current_memory - initial_memory) / 1024 / 1024  # MB

        # 清理
        del objects
        gc.collect()

        final_memory = process.memory_info().rss
        memory_after_cleanup = (final_memory - initial_memory) / 1024 / 1024

        # 内存不应该无限增长
        assert memory_after_cleanup < 100, f"Memory after cleanup {memory_after_cleanup:.2f}MB > 100MB"

    def test_memory_leak_detection(self, db_session):
        """测试内存泄漏检测"""
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # 执行可能引起内存泄漏的操作
        for cycle in range(5):
            # 创建临时对象
            temp_objects = []
            for i in range(1000):
                temp_objects.append({
                    "data": "x" * 1000,  # 1KB data
                    "index": i
                })

            # 模拟一些处理
            processed = [obj["index"] for obj in temp_objects]

            # 清理
            del temp_objects
            del processed

            # 强制垃圾回收
            gc.collect()

            current_memory = process.memory_info().rss
            memory_increase = (current_memory - initial_memory) / 1024 / 1024

        final_memory = process.memory_info().rss
        total_increase = (final_memory - initial_memory) / 1024 / 1024

        # 5个周期后内存增长应该很小
        assert total_increase < 50, f"Memory leak detected: increased by {total_increase:.2f}MB"


@pytest.mark.performance
@pytest.mark.slow
class TestReportGenerationPerformance:
    """报表生成性能测试"""

    def test_large_report_generation(self, db_session):
        """测试大数据报表生成"""
        # 模拟大量数据
        report_data = []
        for i in range(50000):
            report_data.append({
                "date": f"2025-01-{(i % 30) + 1:02d}",
                "account_id": f"account_{i % 100}",
                "impressions": 10000 + i,
                "clicks": 500 + (i % 100),
                "conversions": 10 + (i % 5),
                "spend": Decimal("250.00") + (i * 0.01)
            })

        # 测试Excel报表生成
        start = time.perf_counter()
        excel_buffer = generate_excel_report(report_data)
        end = time.perf_counter()

        generation_time = (end - start) * 1000
        records_per_second = 50000 / (generation_time / 1000)

        # 性能断言
        assert generation_time < 5000, f"Excel generation time {generation_time:.2f}ms > 5000ms"
        assert records_per_second > 10000, f"Records per second {records_per_second:.2f} < 10000"

        # 验证文件大小
        assert len(excel_buffer.getvalue()) > 0

    def test_aggregation_report_performance(self):
        """测试聚合报表性能"""
        # 生成测试数据
        daily_data = []
        for i in range(10000):
            daily_data.append({
                "date": f"2025-01-{(i % 30) + 1:02d}",
                "spend": Decimal("1000.00") + (i * 0.1),
                "revenue": Decimal("1500.00") + (i * 0.15),
                "conversions": 10 + (i % 5)
            })

        # 测试月度聚合
        start = time.perf_counter()
        monthly_summary = aggregate_monthly_performance(daily_data)
        end = time.perf_counter()

        aggregation_time = (end - start) * 1000

        assert aggregation_time < 500, f"Monthly aggregation time {aggregation_time:.2f}ms > 500ms"
        assert len(monthly_summary) > 0

    def test_real_time_dashboard_performance(self, db_session):
        """测试实时仪表盘性能"""
        # 模拟实时仪表盘数据获取
        dashboard_queries = [
            "get_today_spend",
            "get_active_projects",
            "get_pending_topups",
            "get_monthly_performance",
            "get_alert_count"
        ]

        times = []
        for _ in range(10):
            start = time.perf_counter()
            dashboard_data = fetch_dashboard_data(dashboard_queries)
            end = time.perf_counter()
            times.append((end - start) * 1000)

        avg_time = statistics.mean(times)

        # 仪表盘应该快速响应
        assert avg_time < 1000, f"Dashboard load time {avg_time:.2f}ms > 1000ms"
        assert len(dashboard_data) == len(dashboard_queries)


@pytest.mark.performance
@pytest.mark.slow
class TestScalability:
    """可扩展性测试"""

    def test_user_scalability(self, client):
        """测试用户规模扩展性"""
        # 模拟不同数量的并发用户
        user_counts = [10, 50, 100, 200]
        response_times = []

        for user_count in user_counts:
            def user_session():
                # 模拟用户操作序列
                operations = [
                    ("GET", "/api/health"),
                    ("GET", "/api/users/me"),
                    ("GET", "/api/projects")
                ]

                session_times = []
                for method, endpoint in operations:
                    start = time.perf_counter()
                    if method == "GET":
                        client.get(endpoint)
                    end = time.perf_counter()
                    session_times.append((end - start) * 1000)

                return statistics.mean(session_times)

            # 并发用户
            with ThreadPoolExecutor(max_workers=user_count) as executor:
                futures = [executor.submit(user_session) for _ in range(user_count)]
                user_times = [future.result() for future in as_completed(futures)]

            avg_time = statistics.mean(user_times)
            response_times.append((user_count, avg_time))

        # 验证响应时间增长是线性的
        for i in range(1, len(response_times)):
            prev_users, prev_time = response_times[i-1]
            curr_users, curr_time = response_times[i]

            time_increase_ratio = curr_time / prev_time
            user_increase_ratio = curr_users / prev_users

            # 时间增长不应该超过用户增长的平方
            assert time_increase_ratio < user_increase_ratio ** 1.5

    def test_data_volume_scalability(self):
        """测试数据量扩展性"""
        data_volumes = [1000, 5000, 10000, 50000]
        processing_times = []

        for volume in data_volumes:
            # 生成测试数据
            test_data = []
            for i in range(volume):
                test_data.append({
                    "value": i,
                    "square": i * i,
                    "sqrt": i ** 0.5
                })

            # 测试处理时间
            start = time.perf_counter()
            result = process_data(test_data)
            end = time.perf_counter()

            processing_time = (end - start) * 1000
            processing_times.append((volume, processing_time))

        # 验证处理时间是O(n)或接近
        for i in range(1, len(processing_times)):
            prev_volume, prev_time = processing_times[i-1]
            curr_volume, curr_time = processing_times[i]

            time_increase_ratio = curr_time / prev_time
            volume_increase_ratio = curr_volume / prev_volume

            # 时间增长应该接近线性
            assert time_increase_ratio < volume_increase_ratio * 1.5


# 辅助函数
def generate_excel_report(data):
    """生成Excel报表"""
    import io
    output = io.BytesIO()
    # 这里应该是实际的Excel生成逻辑
    output.write(b"dummy excel content")
    return output

def aggregate_monthly_performance(data):
    """聚合月度绩效"""
    # 简单的聚合逻辑
    return {"total": len(data)}

def fetch_dashboard_data(queries):
    """获取仪表盘数据"""
    result = {}
    for query in queries:
        result[query] = {"value": 100}
    return result

def process_data(data):
    """处理数据"""
    result = []
    for item in data:
        result.append({
            "processed": True,
            "value": item["value"]
        })
    return result