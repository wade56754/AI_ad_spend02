#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据导入功能测试
测试各种数据格式的导入、验证和处理
"""

import pytest
import pandas as pd
import json
from decimal import Decimal, InvalidOperation
from datetime import date, datetime
from io import BytesIO, StringIO
from typing import Dict, List, Any
import tempfile
import os

from tests.conftest import assert_decimal_equal, pytest_marks


@pytest.mark.integration
@pytest.mark.functional
class TestExcelDataImport:
    """Excel数据导入测试"""

    def create_test_excel_file(self, data: List[Dict]) -> BytesIO:
        """创建测试用的Excel文件"""
        df = pd.DataFrame(data)
        excel_buffer = BytesIO()
        df.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)
        return excel_buffer

    def test_valid_daily_report_import(self, db_session, test_ad_account):
        """测试有效的日报数据导入"""
        test_data = [
            {
                "account_id": str(test_ad_account.id),
                "report_date": "2025-01-01",
                "impressions": 10000,
                "clicks": 500,
                "conversions": 10,
                "spend": 250.00,
                "revenue": 500.00
            },
            {
                "account_id": str(test_ad_account.id),
                "report_date": "2025-01-02",
                "impressions": 12000,
                "clicks": 600,
                "conversions": 12,
                "spend": 300.00,
                "revenue": 600.00
            }
        ]

        excel_file = self.create_test_excel_file(test_data)

        # 模拟文件上传
        result = import_daily_reports_from_excel(excel_file, db_session)

        assert result["success_count"] == 2
        assert result["error_count"] == 0
        assert result["duplicates"] == 0

    def test_invalid_excel_format(self, db_session):
        """测试无效的Excel格式"""
        # 创建缺少必要列的Excel
        invalid_data = [
            {
                "date": "2025-01-01",
                "impressions": 10000
                # 缺少account_id等其他必要字段
            }
        ]

        excel_file = self.create_test_excel_file(invalid_data)
        result = import_daily_reports_from_excel(excel_file, db_session)

        assert result["success_count"] == 0
        assert result["error_count"] > 0
        assert "missing_fields" in result["errors"][0]["type"]

    def test_duplicate_data_handling(self, db_session, test_ad_account, test_daily_report):
        """测试重复数据处理"""
        # 创建与已存在的数据相同的数据
        duplicate_data = [
            {
                "account_id": str(test_ad_account.id),
                "report_date": str(test_daily_report.report_date),
                "impressions": 10000,
                "clicks": 500,
                "spend": 250.00
            }
        ]

        excel_file = self.create_test_excel_file(duplicate_data)
        result = import_daily_reports_from_excel(excel_file, db_session, skip_duplicates=True)

        assert result["duplicates"] == 1
        assert result["success_count"] == 0

    @pytest.mark.parametrize("invalid_value,field_name", [
        ("invalid_number", "impressions"),
        (-1, "impressions"),  # 负数
        (None, "clicks"),
        ("", "conversions"),
        ("not_a_date", "report_date")
    ])
    def test_field_validation(self, db_session, test_ad_account, invalid_value, field_name):
        """测试字段验证"""
        data = {
            "account_id": str(test_ad_account.id),
            "report_date": "2025-01-01",
            "impressions": 10000,
            "clicks": 500,
            "conversions": 10,
            "spend": 250.00,
            "revenue": 500.00
        }
        data[field_name] = invalid_value

        excel_file = self.create_test_excel_file([data])
        result = import_daily_reports_from_excel(excel_file, db_session)

        assert result["error_count"] == 1

    def test_large_file_import(self, db_session, test_ad_account):
        """测试大文件导入"""
        # 创建1000行测试数据
        large_data = []
        for i in range(1000):
            large_data.append({
                "account_id": str(test_ad_account.id),
                "report_date": f"2025-01-{(i % 30) + 1:02d}",
                "impressions": 10000 + i,
                "clicks": 500 + i,
                "conversions": 10 + (i % 5),
                "spend": 250.00 + (i * 0.1),
                "revenue": 500.00 + (i * 0.2)
            })

        excel_file = self.create_test_excel_file(large_data)
        result = import_daily_reports_from_excel(excel_file, db_session)

        assert result["success_count"] == 1000
        assert result["processing_time"] < 30  # 应该在30秒内完成


@pytest.mark.integration
@pytest.mark.functional
class TestCSVDataImport:
    """CSV数据导入测试"""

    def create_test_csv_file(self, data: List[Dict]) -> StringIO:
        """创建测试用的CSV文件"""
        df = pd.DataFrame(data)
        csv_buffer = StringIO()
        df.to_csv(csv_buffer, index=False)
        csv_buffer.seek(0)
        return csv_buffer

    def test_csv_import_with_custom_delimiter(self, db_session, test_ad_account):
        """测试使用自定义分隔符的CSV导入"""
        # 使用分号分隔符
        test_data = [
            {
                "account_id": str(test_ad_account.id),
                "report_date": "2025-01-01",
                "impressions": 10000,
                "clicks": 500,
                "spend": 250.00
            }
        ]

        # 创建分号分隔的CSV
        df = pd.DataFrame(test_data)
        csv_buffer = StringIO()
        df.to_csv(csv_buffer, index=False, sep=';')
        csv_buffer.seek(0)

        result = import_daily_reports_from_csv(
            csv_buffer,
            db_session,
            delimiter=';'
        )

        assert result["success_count"] == 1

    def test_csv_with_headers(self, db_session, test_ad_account):
        """测试带表头的CSV导入"""
        csv_content = f"""Account ID,Report Date,Impressions,Clicks,Conversions,Spend,Revenue
{test_ad_account.id},2025-01-01,10000,500,10,250.00,500.00
{test_ad_account.id},2025-01-02,12000,600,12,300.00,600.00"""

        csv_buffer = StringIO(csv_content)
        result = import_daily_reports_from_csv(
            csv_buffer,
            db_session,
            has_headers=True,
            field_mapping={
                "Account ID": "account_id",
                "Report Date": "report_date",
                "Impressions": "impressions",
                "Clicks": "clicks",
                "Conversions": "conversions",
                "Spend": "spend",
                "Revenue": "revenue"
            }
        )

        assert result["success_count"] == 2

    def test_csv_encoding_handling(self, db_session, test_ad_account):
        """测试CSV编码处理"""
        # 创建包含中文字符的UTF-8编码CSV
        test_data = [{
            "account_id": str(test_ad_account.id),
            "report_date": "2025-01-01",
            "impressions": 10000,
            "clicks": 500,
            "spend": 250.00,
            "notes": "测试数据"
        }]

        df = pd.DataFrame(test_data)

        # 创建临时文件以测试不同编码
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.csv', delete=False) as tmp:
            df.to_csv(tmp.name, index=False, encoding='utf-8-sig')

            with open(tmp.name, 'r', encoding='utf-8-sig') as f:
                result = import_daily_reports_from_csv(f, db_session)

            os.unlink(tmp.name)

        assert result["success_count"] == 1


@pytest.mark.integration
@pytest.mark.functional
class TestJSONDataImport:
    """JSON数据导入测试"""

    def test_single_record_import(self, db_session, test_ad_account):
        """测试单条记录导入"""
        json_data = {
            "account_id": str(test_ad_account.id),
            "report_date": "2025-01-01",
            "metrics": {
                "impressions": 10000,
                "clicks": 500,
                "conversions": 10
            },
            "financial": {
                "spend": 250.00,
                "revenue": 500.00
            }
        }

        result = import_daily_report_from_json(json_data, db_session)
        assert result["success"] is True

    def test_batch_json_import(self, db_session, test_ad_account):
        """测试批量JSON导入"""
        batch_data = [
            {
                "account_id": str(test_ad_account.id),
                "report_date": "2025-01-01",
                "impressions": 10000,
                "clicks": 500,
                "spend": 250.00
            },
            {
                "account_id": str(test_ad_account.id),
                "report_date": "2025-01-02",
                "impressions": 12000,
                "clicks": 600,
                "spend": 300.00
            }
        ]

        result = import_daily_reports_batch_json(batch_data, db_session)
        assert result["success_count"] == 2

    def test_nested_json_structure(self, db_session, test_ad_account):
        """测试嵌套JSON结构"""
        json_data = {
            "metadata": {
                "import_date": "2025-01-01T00:00:00Z",
                "source": "facebook_ads"
            },
            "data": {
                "account_id": str(test_ad_account.id),
                "report_date": "2025-01-01",
                "results": {
                    "impressions": 10000,
                    "clicks": 500,
                    "conversions": {
                        "total": 10,
                        "by_type": {
                            "lead": 8,
                            "purchase": 2
                        }
                    }
                },
                "cost": {
                    "amount": 250.00,
                    "currency": "CNY"
                }
            }
        }

        result = import_nested_json_report(json_data, db_session)
        assert result["success"] is True
        assert result["extracted_data"]["conversions"] == 10

    def test_invalid_json_handling(self, db_session):
        """测试无效JSON处理"""
        invalid_json = '{"invalid": json structure'  # 缺少闭合括号

        with pytest.raises(json.JSONDecodeError):
            import_daily_report_from_json(invalid_json, db_session)


@pytest.mark.integration
@pytest.mark.functional
class TestDataValidation:
    """数据验证测试"""

    def test_numeric_range_validation(self):
        """测试数值范围验证"""
        # 测试有效值
        assert validate_numeric_field("impressions", 10000) is True
        assert validate_numeric_field("clicks", 500) is True

        # 测试无效值
        assert validate_numeric_field("impressions", -1) is False
        assert validate_numeric_field("clicks", None) is False

    def test_date_format_validation(self):
        """测试日期格式验证"""
        # 有效日期格式
        assert validate_date_format("2025-01-01") is True
        assert validate_date_format("2025/01/01") is True
        assert validate_date_format("01-01-2025") is True

        # 无效日期格式
        assert validate_date_format("2025-13-01") is False  # 无效月份
        assert validate_date_format("not-a-date") is False
        assert validate_date_format("2025-02-30") is False  # 无效日期

    def test_decimal_precision_validation(self):
        """测试小数精度验证"""
        # 有效精度
        assert validate_decimal_precision("250.00") is True
        assert validate_decimal_precision("250.123456") is False  # 超过精度

    def test_account_id_validation(self, db_session, test_ad_account):
        """测试账户ID验证"""
        # 有效ID
        assert validate_account_id(str(test_ad_account.id), db_session) is True

        # 无效ID
        assert validate_account_id("invalid-uuid", db_session) is False
        assert validate_account_id("00000000-0000-0000-0000-000000000000", db_session) is False

    def test_business_rule_validation(self):
        """测试业务规则验证"""
        # 点击不能大于展示
        assert validate_business_rule("clicks <= impressions", 600, 10000) is True
        assert validate_business_rule("clicks <= impressions", 15000, 10000) is False

        # 转化不能大于点击
        assert validate_business_rule("conversions <= clicks", 10, 500) is True
        assert validate_business_rule("conversions <= clicks", 600, 500) is False


@pytest.mark.integration
@pytest.mark.functional
class TestImportPerformance:
    """导入性能测试"""

    @pytest.mark.slow
    def test_import_speed_benchmark(self, db_session, test_ad_account):
        """测试导入速度基准"""
        # 创建10000条测试数据
        large_dataset = []
        for i in range(10000):
            large_dataset.append({
                "account_id": str(test_ad_account.id),
                "report_date": f"2025-01-{(i % 30) + 1:02d}",
                "impressions": 10000 + i,
                "clicks": 500 + (i % 100),
                "conversions": 10 + (i % 5),
                "spend": round(250.00 + (i * 0.01), 2)
            })

        # 测量导入时间
        start_time = datetime.now()

        df = pd.DataFrame(large_dataset)
        excel_buffer = BytesIO()
        df.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)

        result = import_daily_reports_from_excel(excel_buffer, db_session)

        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()

        # 验证性能指标
        assert result["success_count"] == 10000
        assert processing_time < 60  # 应该在60秒内完成
        assert processing_time < 0.01 * 10000  # 每条记录处理时间小于0.01秒

    @pytest.mark.slow
    def test_concurrent_imports(self, db_session, test_ad_account):
        """测试并发导入"""
        import threading
        import queue

        results = queue.Queue()

        def import_worker(data_chunk):
            df = pd.DataFrame(data_chunk)
            excel_buffer = BytesIO()
            df.to_excel(excel_buffer, index=False)
            excel_buffer.seek(0)

            result = import_daily_reports_from_excel(excel_buffer, db_session)
            results.put(result)

        # 创建5个并发导入任务
        threads = []
        for i in range(5):
            chunk_data = []
            for j in range(100):
                chunk_data.append({
                    "account_id": str(test_ad_account.id),
                    "report_date": f"2025-01-{j + 1:02d}",
                    "impressions": 10000 + (i * 100) + j,
                    "clicks": 500 + j,
                    "spend": 250.00 + j
                })

            thread = threading.Thread(target=import_worker, args=(chunk_data,))
            threads.append(thread)
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join()

        # 汇总结果
        total_success = 0
        while not results.empty():
            result = results.get()
            total_success += result["success_count"]

        assert total_success == 500  # 5个线程 × 100条记录


@pytest.mark.integration
@pytest.mark.functional
class TestErrorHandling:
    """错误处理测试"""

    def test_partial_import_recovery(self, db_session, test_ad_account):
        """测试部分导入恢复"""
        # 创建包含一些无效记录的数据
        mixed_data = [
            {
                "account_id": str(test_ad_account.id),
                "report_date": "2025-01-01",
                "impressions": 10000,
                "clicks": 500,
                "spend": 250.00
            },
            {
                "account_id": str(test_ad_account.id),
                "report_date": "invalid-date",
                "impressions": 10000,
                "clicks": 500,
                "spend": 250.00
            },
            {
                "account_id": str(test_ad_account.id),
                "report_date": "2025-01-02",
                "impressions": 12000,
                "clicks": 600,
                "spend": 300.00
            }
        ]

        df = pd.DataFrame(mixed_data)
        excel_buffer = BytesIO()
        df.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)

        result = import_daily_reports_from_excel(
            excel_buffer,
            db_session,
            continue_on_error=True
        )

        assert result["success_count"] == 2
        assert result["error_count"] == 1
        assert len(result["errors"]) == 1
        assert result["errors"][0]["row_index"] == 2  # 第二行（从1开始）

    def test_transaction_rollback(self, db_session, test_ad_account):
        """测试事务回滚"""
        # 创建会触发错误的批量数据
        problematic_data = []
        for i in range(1000):
            data = {
                "account_id": str(test_ad_account.id),
                "report_date": f"2025-01-{(i % 30) + 1:02d}",
                "impressions": 10000 + i,
                "clicks": 500 + i,
                "spend": 250.00 + i
            }

            # 在中间插入一条会导致数据库约束违反的记录
            if i == 500:
                data["account_id"] = None  # 这会导致错误

            problematic_data.append(data)

        df = pd.DataFrame(problematic_data)
        excel_buffer = BytesIO()
        df.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)

        result = import_daily_reports_from_excel(
            excel_buffer,
            db_session,
            transactional=True
        )

        # 事务应该回滚，没有数据被导入
        assert result["success_count"] == 0
        assert result["error_count"] == 1

    def test_memory_usage(self, db_session):
        """测试内存使用"""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # 创建大数据集
        large_dataset = []
        for i in range(50000):  # 5万条记录
            large_dataset.append({
                "account_id": str(test_ad_account.id),
                "report_date": f"2025-01-{(i % 30) + 1:02d}",
                "impressions": 10000 + i,
                "clicks": 500 + i,
                "spend": 250.00 + i
            })

        df = pd.DataFrame(large_dataset)
        excel_buffer = BytesIO()
        df.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)

        result = import_daily_reports_from_excel(
            excel_buffer,
            db_session,
            chunk_size=1000  # 分块处理
        )

        final_memory = process.memory_info().rss
        memory_increase = (final_memory - initial_memory) / 1024 / 1024  # MB

        assert result["success_count"] == 50000
        assert memory_increase < 500  # 内存增长不应超过500MB


# 辅助函数（这些应该在实际的导入服务中实现）
def import_daily_reports_from_excel(file_buffer, db_session, **kwargs):
    """从Excel导入日报数据"""
    return {
        "success_count": 0,
        "error_count": 0,
        "duplicates": 0,
        "processing_time": 0,
        "errors": []
    }

def import_daily_reports_from_csv(csv_buffer, db_session, **kwargs):
    """从CSV导入日报数据"""
    return {
        "success_count": 0,
        "error_count": 0,
        "errors": []
    }

def import_daily_report_from_json(json_data, db_session):
    """从JSON导入单条日报"""
    return {"success": False}

def import_daily_reports_batch_json(batch_data, db_session):
    """批量导入JSON日报"""
    return {"success_count": 0}

def import_nested_json_report(json_data, db_session):
    """导入嵌套结构的JSON报表"""
    return {
        "success": False,
        "extracted_data": {}
    }

def validate_numeric_field(field_name, value):
    """验证数值字段"""
    if value is None or value < 0:
        return False
    return True

def validate_date_format(date_str):
    """验证日期格式"""
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except:
        try:
            datetime.strptime(date_str, "%Y/%m/%d")
            return True
        except:
            try:
                datetime.strptime(date_str, "%m-%d-%Y")
                return True
            except:
                return False

def validate_decimal_precision(value):
    """验证小数精度"""
    try:
        decimal = Decimal(str(value))
        return abs(decimal.as_tuple().exponent) <= 2
    except:
        return False

def validate_account_id(account_id, db_session):
    """验证账户ID"""
    # 这里应该查询数据库验证
    return True

def validate_business_rule(rule, value1, value2):
    """验证业务规则"""
    if rule == "clicks <= impressions":
        return value1 <= value2
    elif rule == "conversions <= clicks":
        return value1 <= value2
    return False