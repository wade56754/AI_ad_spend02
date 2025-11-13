"""
日报管理Service层单元测试
Version: 1.0
Author: Claude协作开发
"""

import pytest
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import Mock, patch

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from services.daily_report_service import DailyReportService
from schemas.daily_report import (
    DailyReportCreateRequest,
    DailyReportUpdateRequest,
    DailyReportAuditRequest,
    DailyReportBatchImportRequest,
    DailyReportQueryParams
)
from exceptions.custom_exceptions import (
    BusinessLogicError,
    ResourceNotFoundError,
    PermissionDeniedError,
    ResourceConflictError
)
from models.user import User
from models.daily_report import DailyReport


class TestDailyReportService:
    """日报管理服务测试类"""

    def test_create_daily_report_success(self, db_session, test_ad_account, test_user):
        """测试成功创建日报"""
        # 准备测试数据
        service = DailyReportService(db_session)
        request = DailyReportCreateRequest(
            report_date=date(2024, 1, 15),
            ad_account_id=test_ad_account.id,
            campaign_name="测试广告系列",
            impressions=10000,
            clicks=500,
            spend=Decimal("100.00"),
            conversions=10,
            new_follows=20
        )

        # 执行操作
        report = service.create_daily_report(request, test_user)

        # 验证结果
        assert report.report_date == date(2024, 1, 15)
        assert report.ad_account_id == test_ad_account.id
        assert report.created_by == test_user.id
        assert report.status == "pending"
        assert report.impressions == 10000

        # 验证审计日志已创建
        assert len(report.audit_logs) == 1
        assert report.audit_logs[0].action == "created"

    def test_create_daily_report_duplicate(self, db_session, test_ad_account, test_user):
        """测试创建重复日报"""
        service = DailyReportService(db_session)
        request = DailyReportCreateRequest(
            report_date=date(2024, 1, 15),
            ad_account_id=test_ad_account.id
        )

        # 第一次创建成功
        service.create_daily_report(request, test_user)

        # 第二次创建应该失败
        with pytest.raises(ResourceConflictError) as exc_info:
            service.create_daily_report(request, test_user)

        assert "日报已存在" in str(exc_info.value)

    def test_create_daily_report_future_date(self, db_session, test_ad_account, test_user):
        """测试创建未来日期的日报"""
        service = DailyReportService(db_session)
        request = DailyReportCreateRequest(
            report_date=date(2030, 1, 1),  # 未来日期
            ad_account_id=test_ad_account.id
        )

        with pytest.raises(ValueError) as exc_info:
            service.create_daily_report(request, test_user)

        assert "报表日期不能是未来日期" in str(exc_info.value)

    def test_create_daily_report_invalid_data(self, db_session, test_ad_account, test_user):
        """测试创建无效数据的日报（点击数大于展示数）"""
        service = DailyReportService(db_session)
        request = DailyReportCreateRequest(
            report_date=date(2024, 1, 15),
            ad_account_id=test_ad_account.id,
            impressions=100,
            clicks=200  # 点击数大于展示数
        )

        with pytest.raises(ValueError) as exc_info:
            service.create_daily_report(request, test_user)

        assert "点击次数不能大于展示次数" in str(exc_info.value)

    def test_get_daily_reports_success(self, db_session, test_ad_account, test_user):
        """测试成功获取日报列表"""
        service = DailyReportService(db_session)

        # 创建测试数据
        request1 = DailyReportCreateRequest(
            report_date=date(2024, 1, 15),
            ad_account_id=test_ad_account.id
        )
        request2 = DailyReportCreateRequest(
            report_date=date(2024, 1, 16),
            ad_account_id=test_ad_account.id
        )

        service.create_daily_report(request1, test_user)
        service.create_daily_report(request2, test_user)

        # 执行查询
        params = DailyReportQueryParams()
        reports, total = service.get_daily_reports(params, test_user)

        # 验证结果
        assert total == 2
        assert len(reports) == 2

    def test_get_daily_reports_with_filters(self, db_session, test_ad_account, test_user):
        """测试带筛选条件的日报列表查询"""
        service = DailyReportService(db_session)

        # 创建不同状态的日报
        request1 = DailyReportCreateRequest(
            report_date=date(2024, 1, 15),
            ad_account_id=test_ad_account.id
        )
        report = service.create_daily_report(request1, test_user)

        # 审核其中一个
        service.approve_daily_report(
            report.id,
            DailyReportAuditRequest(audit_notes="审核通过"),
            test_user
        )

        # 按状态筛选
        params = DailyReportQueryParams(status="approved")
        reports, total = service.get_daily_reports(params, test_user)

        assert total == 1
        assert reports[0].status == "approved"

    def test_get_daily_report_detail_success(self, db_session, test_ad_account, test_user):
        """测试成功获取日报详情"""
        service = DailyReportService(db_session)

        # 创建日报
        request = DailyReportCreateRequest(
            report_date=date(2024, 1, 15),
            ad_account_id=test_ad_account.id,
            campaign_name="测试广告系列"
        )
        created_report = service.create_daily_report(request, test_user)

        # 获取详情
        report = service.get_daily_report(created_report.id, test_user)

        assert report.id == created_report.id
        assert report.campaign_name == "测试广告系列"

    def test_get_daily_report_not_found(self, db_session, test_user):
        """测试获取不存在的日报"""
        service = DailyReportService(db_session)

        with pytest.raises(ResourceNotFoundError):
            service.get_daily_report(999999, test_user)

    def test_update_daily_report_success(self, db_session, test_ad_account, test_user):
        """测试成功更新日报"""
        service = DailyReportService(db_session)

        # 创建日报
        request = DailyReportCreateRequest(
            report_date=date(2024, 1, 15),
            ad_account_id=test_ad_account.id,
            impressions=10000
        )
        report = service.create_daily_report(request, test_user)

        # 更新日报
        update_request = DailyReportUpdateRequest(
            impressions=20000,
            clicks=1000,
            spend=Decimal("200.00")
        )
        updated_report = service.update_daily_report(
            report.id,
            update_request,
            test_user
        )

        assert updated_report.impressions == 20000
        assert updated_report.clicks == 1000
        assert updated_report.spend == Decimal("200.00")

    def test_update_approved_report_should_fail(self, db_session, test_ad_account, test_user):
        """测试更新已审核的日报应该失败"""
        service = DailyReportService(db_session)

        # 创建并审核日报
        request = DailyReportCreateRequest(
            report_date=date(2024, 1, 15),
            ad_account_id=test_ad_account.id
        )
        report = service.create_daily_report(request, test_user)

        service.approve_daily_report(
            report.id,
            DailyReportAuditRequest(audit_notes="审核通过"),
            test_user
        )

        # 尝试更新已审核的日报
        with pytest.raises(BusinessLogicError) as exc_info:
            service.update_daily_report(
                report.id,
                DailyReportUpdateRequest(impressions=20000),
                test_user
            )

        assert "已审核的日报不能修改" in str(exc_info.value)

    def test_approve_daily_report_success(self, db_session, test_ad_account, test_user):
        """测试成功审核日报"""
        service = DailyReportService(db_session)

        # 创建日报
        request = DailyReportCreateRequest(
            report_date=date(2024, 1, 15),
            ad_account_id=test_ad_account.id
        )
        report = service.create_daily_report(request, test_user)

        # 审核日报
        audit_request = DailyReportAuditRequest(audit_notes="数据准确")
        approved_report = service.approve_daily_report(
            report.id,
            audit_request,
            test_user
        )

        assert approved_report.status == "approved"
        assert approved_report.audit_notes == "数据准确"
        assert approved_report.audit_user_id == test_user.id

    def test_reject_daily_report_success(self, db_session, test_ad_account, test_user):
        """测试成功驳回报日"""
        service = DailyReportService(db_session)

        # 创建日报
        request = DailyReportCreateRequest(
            report_date=date(2024, 1, 15),
            ad_account_id=test_ad_account.id
        )
        report = service.create_daily_report(request, test_user)

        # 驳回报日
        audit_request = DailyReportAuditRequest(audit_notes="数据有误")
        rejected_report = service.reject_daily_report(
            report.id,
            audit_request,
            test_user
        )

        assert rejected_report.status == "rejected"
        assert rejected_report.audit_notes == "数据有误"

    def test_batch_import_success(self, db_session, test_ad_account, test_user):
        """测试批量导入成功"""
        service = DailyReportService(db_session)

        # 准备批量导入数据
        reports_data = [
            DailyReportCreateRequest(
                report_date=date(2024, 1, 15),
                ad_account_id=test_ad_account.id,
                impressions=10000
            ),
            DailyReportCreateRequest(
                report_date=date(2024, 1, 16),
                ad_account_id=test_ad_account.id,
                impressions=15000
            )
        ]

        batch_request = DailyReportBatchImportRequest(
            reports=reports_data,
            skip_errors=False
        )

        # 执行批量导入
        success_count, error_count, errors, imported_ids = service.batch_import_daily_reports(
            batch_request,
            test_user
        )

        assert success_count == 2
        assert error_count == 0
        assert len(errors) == 0
        assert len(imported_ids) == 2

    def test_batch_import_with_errors(self, db_session, test_ad_account, test_user):
        """测试批量导入部分失败"""
        service = DailyReportService(db_session)

        # 准备包含错误数据的批量导入
        reports_data = [
            DailyReportCreateRequest(
                report_date=date(2024, 1, 15),
                ad_account_id=test_ad_account.id,
                impressions=10000
            ),
            DailyReportCreateRequest(
                report_date=date(2030, 1, 1),  # 无效日期
                ad_account_id=test_ad_account.id
            )
        ]

        batch_request = DailyReportBatchImportRequest(
            reports=reports_data,
            skip_errors=True
        )

        # 执行批量导入
        success_count, error_count, errors, imported_ids = service.batch_import_daily_reports(
            batch_request,
            test_user
        )

        assert success_count == 1
        assert error_count == 1
        assert len(errors) == 1
        assert len(imported_ids) == 1

    def test_get_statistics_success(self, db_session, test_ad_account, test_user):
        """测试获取统计数据成功"""
        service = DailyReportService(db_session)

        # 创建多个日报
        reports_data = [
            DailyReportCreateRequest(
                report_date=date(2024, 1, 15),
                ad_account_id=test_ad_account.id,
                spend=Decimal("100.00"),
                impressions=10000,
                clicks=500,
                conversions=10
            ),
            DailyReportCreateRequest(
                report_date=date(2024, 1, 16),
                ad_account_id=test_ad_account.id,
                spend=Decimal("200.00"),
                impressions=20000,
                clicks=1000,
                conversions=20
            )
        ]

        for request in reports_data:
            service.create_daily_report(request, test_user)

        # 获取统计
        params = DailyReportQueryParams()
        stats = service.get_daily_report_statistics(params, test_user)

        assert stats['total_reports'] == 2
        assert stats['total_spend'] == Decimal("300.00")
        assert stats['total_impressions'] == 30000
        assert stats['total_clicks'] == 1500
        assert stats['total_conversions'] == 30

    def test_get_audit_logs_success(self, db_session, test_ad_account, test_user):
        """测试获取审核日志成功"""
        service = DailyReportService(db_session)

        # 创建并操作日报
        request = DailyReportCreateRequest(
            report_date=date(2024, 1, 15),
            ad_account_id=test_ad_account.id
        )
        report = service.create_daily_report(request, test_user)

        service.approve_daily_report(
            report.id,
            DailyReportAuditRequest(audit_notes="审核通过"),
            test_user
        )

        # 获取审计日志
        logs = service.get_daily_report_audit_logs(report.id, test_user)

        assert len(logs) >= 2  # 创建日志 + 审核日志
        assert logs[0].action == "created"
        assert any(log.action == "approved" for log in logs)

    @patch('services.daily_report_service.DailyReportService.get_current_user_id')
    def test_transaction_rollback_on_error(self, mock_get_user_id, db_session, test_ad_account):
        """测试错误时事务回滚"""
        mock_get_user_id.return_value = 1
        service = DailyReportService(db_session)

        initial_count = db_session.query(DailyReport).count()

        # 创建会成功的日报
        valid_request = DailyReportCreateRequest(
            report_date=date(2024, 1, 15),
            ad_account_id=test_ad_account.id
        )

        # 创建会失败的日报
        invalid_request = DailyReportCreateRequest(
            report_date=date(2030, 1, 1),  # 无效日期
            ad_account_id=test_ad_account.id
        )

        # 在事务中混合操作
        try:
            with service.transaction():
                report1 = service.create_daily_report(valid_request, test_user)
                report2 = service.create_daily_report(invalid_request, test_user)
        except:
            pass  # 预期会失败

        # 验证事务已回滚
        final_count = db_session.query(DailyReport).count()
        assert final_count == initial_count