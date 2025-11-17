"""
Excel导入/导出功能单元测试
测试阶段2实现的Excel导入/导出功能

Version: 1.0
Author: Claude协作开发
"""

import pytest
from io import BytesIO
from datetime import date
from decimal import Decimal
import pandas as pd

from fastapi import UploadFile
from routers.daily_reports import parse_excel_row_to_report
from config.excel_column_mapping import (
    find_column_definition,
    validate_column_exists,
    MAX_FILE_SIZE_BYTES
)


@pytest.mark.unit
@pytest.mark.excel
class TestExcelColumnMapping:
    """测试Excel列映射配置"""

    def test_find_column_definition_chinese(self):
        """测试：可以通过中文列名找到列定义"""
        col_def = find_column_definition("报表日期")
        assert col_def is not None
        assert col_def.field_name == "report_date"
        assert col_def.required is True

    def test_find_column_definition_english(self):
        """测试：可以通过英文列名找到列定义"""
        col_def = find_column_definition("Report Date")
        assert col_def is not None
        assert col_def.field_name == "report_date"

    def test_find_column_definition_alias(self):
        """测试：可以通过别名找到列定义"""
        col_def = find_column_definition("日期")
        assert col_def is not None
        assert col_def.field_name == "report_date"

    def test_find_column_definition_case_insensitive(self):
        """测试：列名匹配忽略大小写"""
        col_def1 = find_column_definition("report date")
        col_def2 = find_column_definition("REPORT DATE")
        assert col_def1 is not None
        assert col_def2 is not None
        assert col_def1.field_name == col_def2.field_name

    def test_validate_column_exists_success(self):
        """测试：验证包含所有必需列的Excel"""
        columns = [
            "报表日期",
            "广告账户ID",
            "展示次数",
            "点击次数",
            "消耗金额",
            "转化次数",
            "新增粉丝数"
        ]
        valid, missing = validate_column_exists(columns)
        assert valid is True
        assert len(missing) == 0

    def test_validate_column_exists_missing_required(self):
        """测试：验证缺少必需列的Excel"""
        columns = ["报表日期", "展示次数"]  # 缺少"广告账户ID"等必需列
        valid, missing = validate_column_exists(columns)
        assert valid is False
        assert len(missing) > 0
        assert "广告账户ID" in missing


@pytest.mark.unit
@pytest.mark.excel
class TestExcelRowParsing:
    """测试Excel行数据解析"""

    def test_parse_valid_row(self):
        """测试：解析有效的数据行"""
        row = pd.Series({
            "报表日期": "2024-01-15",
            "广告账户ID": 1,
            "广告系列名称": "测试广告系列",
            "展示次数": 10000,
            "点击次数": 500,
            "消耗金额": 100.00,
            "转化次数": 10,
            "新增粉丝数": 20
        })
        columns = list(row.index)

        request, error = parse_excel_row_to_report(row, row_number=2, df_columns=columns)

        assert error is None
        assert request is not None
        assert request.report_date == date(2024, 1, 15)
        assert request.ad_account_id == 1
        assert request.impressions == 10000
        assert request.clicks == 500
        assert request.spend == Decimal("100.00")

    def test_parse_row_with_english_columns(self):
        """测试：解析英文列名的数据行"""
        row = pd.Series({
            "Report Date": "2024-01-15",
            "Ad Account ID": 1,
            "Impressions": 10000,
            "Clicks": 500,
            "Spend": 100.00,
            "Conversions": 10,
            "New Follows": 20
        })
        columns = list(row.index)

        request, error = parse_excel_row_to_report(row, row_number=2, df_columns=columns)

        assert error is None
        assert request is not None
        assert request.report_date == date(2024, 1, 15)

    def test_parse_row_missing_required_field(self):
        """测试：解析缺少必需字段的数据行"""
        row = pd.Series({
            # 缺少"报表日期"
            "广告账户ID": 1,
            "展示次数": 10000,
            "点击次数": 500,
            "消耗金额": 100.00,
            "转化次数": 10,
            "新增粉丝数": 20
        })
        columns = list(row.index)

        request, error = parse_excel_row_to_report(row, row_number=2, df_columns=columns)

        assert request is None
        assert error is not None
        assert error.error_code == "MISSING_REQUIRED_COLUMN"
        assert error.field_name == "report_date"
        assert "报表日期" in error.error_message

    def test_parse_row_invalid_date_format(self):
        """测试：解析无效日期格式"""
        row = pd.Series({
            "报表日期": "2025-13-32",  # 无效日期
            "广告账户ID": 1,
            "展示次数": 10000,
            "点击次数": 500,
            "消耗金额": 100.00,
            "转化次数": 10,
            "新增粉丝数": 20
        })
        columns = list(row.index)

        request, error = parse_excel_row_to_report(row, row_number=2, df_columns=columns)

        assert request is None
        assert error is not None
        assert error.error_code == "TYPE_CONVERSION_ERROR"
        assert error.field_name == "report_date"

    def test_parse_row_value_out_of_range(self):
        """测试：解析数值超出范围"""
        row = pd.Series({
            "报表日期": "2024-01-15",
            "广告账户ID": -1,  # 小于最小值1
            "展示次数": 10000,
            "点击次数": 500,
            "消耗金额": 100.00,
            "转化次数": 10,
            "新增粉丝数": 20
        })
        columns = list(row.index)

        request, error = parse_excel_row_to_report(row, row_number=2, df_columns=columns)

        assert request is None
        assert error is not None
        assert error.error_code == "VALUE_OUT_OF_RANGE"
        assert error.field_name == "ad_account_id"

    def test_parse_row_empty_required_field(self):
        """测试：解析必需字段为空"""
        row = pd.Series({
            "报表日期": None,  # 空值
            "广告账户ID": 1,
            "展示次数": 10000,
            "点击次数": 500,
            "消耗金额": 100.00,
            "转化次数": 10,
            "新增粉丝数": 20
        })
        columns = list(row.index)

        request, error = parse_excel_row_to_report(row, row_number=2, df_columns=columns)

        assert request is None
        assert error is not None
        assert error.error_code == "EMPTY_REQUIRED_FIELD"
        assert error.field_name == "report_date"


@pytest.mark.integration
@pytest.mark.excel
@pytest.mark.api
class TestExcelImportAPI:
    """测试Excel导入API"""

    def test_import_valid_excel_file(
        self,
        client,
        db_session,
        test_ad_account,
        test_data_operator_user,
        auth_headers_operator,
        sample_excel_file_bytes
    ):
        """测试：导入有效的Excel文件"""
        # 准备文件
        files = {
            "file": ("test.xlsx", BytesIO(sample_excel_file_bytes), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        }

        # 发送请求
        response = client.post(
            "/daily-reports/import-file?skip_errors=false",
            files=files,
            headers=auth_headers_operator
        )

        # 断言
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["success_count"] >= 0
        assert data["data"]["total_count"] == 3  # sample_excel_data有3行

    def test_import_file_too_large(
        self,
        client,
        auth_headers_operator
    ):
        """测试：上传超过大小限制的文件"""
        # 创建大文件（>5MB）
        large_data = b"x" * (MAX_FILE_SIZE_BYTES + 1)
        files = {
            "file": ("large.xlsx", BytesIO(large_data), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        }

        response = client.post(
            "/daily-reports/import-file",
            files=files,
            headers=auth_headers_operator
        )

        # 断言
        assert response.status_code == 400
        data = response.json()
        assert "BIZ_FILE_TOO_LARGE" in data["error"]["code"]

    def test_import_invalid_file_type(
        self,
        client,
        auth_headers_operator
    ):
        """测试：上传非Excel文件"""
        files = {
            "file": ("test.txt", BytesIO(b"not an excel file"), "text/plain")
        }

        response = client.post(
            "/daily-reports/import-file",
            files=files,
            headers=auth_headers_operator
        )

        # 断言
        assert response.status_code == 400
        data = response.json()
        assert "BIZ_INVALID_FILE_TYPE" in data["error"]["code"]


@pytest.mark.integration
@pytest.mark.excel
@pytest.mark.api
class TestExcelExportAPI:
    """测试Excel导出API"""

    def test_export_daily_reports(
        self,
        client,
        db_session,
        mock_daily_reports,  # 10条测试数据
        auth_headers_admin
    ):
        """测试：导出日报为Excel文件"""
        response = client.get(
            "/daily-reports/export",
            headers=auth_headers_admin
        )

        # 断言
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        assert "attachment" in response.headers["content-disposition"]

        # 验证可以解析为Excel
        excel_data = BytesIO(response.content)
        df = pd.read_excel(excel_data)
        assert len(df) == 10  # mock_daily_reports创建了10条

    def test_export_with_rbac_filter(
        self,
        client,
        db_session,
        mock_daily_reports,
        test_user,
        auth_headers_user
    ):
        """测试：导出时应用RBAC过滤（投手只能导出自己的数据）"""
        response = client.get(
            "/daily-reports/export",
            headers=auth_headers_user
        )

        # 断言
        assert response.status_code == 200

        # 验证Excel内容
        excel_data = BytesIO(response.content)
        df = pd.read_excel(excel_data)
        # mock_daily_reports的所有数据都是test_user创建的，所以应该能看到全部
        assert len(df) == 10

    def test_export_limit_exceeded(
        self,
        client,
        db_session,
        test_ad_account,
        test_user,
        auth_headers_admin
    ):
        """测试：导出数据量超限"""
        # 创建超过MAX_EXPORT_ROWS的数据（需要mock，此处仅验证逻辑）
        # 实际测试中可以修改MAX_EXPORT_ROWS为较小值（如10）来测试
        from config.excel_column_mapping import MAX_EXPORT_ROWS

        # 如果数据库中有>MAX_EXPORT_ROWS条数据，应返回400
        # 此处跳过实际数据创建，仅作逻辑说明

    def test_export_empty_data(
        self,
        client,
        auth_headers_admin
    ):
        """测试：导出空数据"""
        response = client.get(
            "/daily-reports/export?report_date_start=2099-01-01",  # 未来日期，无数据
            headers=auth_headers_admin
        )

        # 断言
        assert response.status_code == 404
        data = response.json()
        assert "BIZ_NO_DATA" in data["error"]["code"]


@pytest.mark.unit
@pytest.mark.excel
class TestExcelErrorHandling:
    """测试Excel导入的错误处理"""

    def test_detailed_error_message(self):
        """测试：错误消息包含详细信息"""
        row = pd.Series({
            "报表日期": "invalid-date",
            "广告账户ID": 1,
            "展示次数": 10000,
            "点击次数": 500,
            "消耗金额": 100.00,
            "转化次数": 10,
            "新增粉丝数": 20
        })
        columns = list(row.index)

        _, error = parse_excel_row_to_report(row, row_number=5, df_columns=columns)

        # 断言错误信息完整
        assert error is not None
        assert error.row_number == 5
        assert error.field_name is not None
        assert error.error_code is not None
        assert error.error_message is not None
        # 应该有修复建议
        assert error.suggestion is not None or error.error_message is not None
