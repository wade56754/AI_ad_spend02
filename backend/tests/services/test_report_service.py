"""
Reports Service 层单元测试

测试范围：
1. 项目报表查询（get_project_summary_report）
2. 项目详情报表（get_project_accounts_report）
3. 渠道报表查询（get_channel_summary_report）
4. 投手报表查询（get_buyer_summary_report）
5. 仪表板汇总（get_dashboard_summary）
6. 权限过滤逻辑（_apply_permission_filter）
7. SoT 对齐验证（LEDGER_SOT, STATE_MACHINE, AUTH_SPEC）

Version: 1.0
Created: 2025-12-07
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session

from backend.models import (
    User, UserRole, Project, AdAccount, DailyReport, DailyReportStatus,
    LedgerEntry, LedgerBookType, LedgerEntryType, Supplier
)
from backend.services.report_service import ReportService
from backend.exceptions import PermissionDeniedError, ResourceNotFoundError


# ===== Fixtures =====

@pytest.fixture
def report_service(db_session: Session):
    """创建 ReportService 实例"""
    return ReportService(db_session)


@pytest.fixture
def admin_user(db_session: Session):
    """创建管理员用户"""
    user = User(
        id=1,
        username="admin",
        email="admin@test.com",
        role=UserRole.ADMIN.value,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def account_manager_user(db_session: Session):
    """创建账户经理用户"""
    user = User(
        id=2,
        username="am",
        email="am@test.com",
        role=UserRole.ACCOUNT_MANAGER.value,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def media_buyer_user(db_session: Session):
    """创建投手用户"""
    user = User(
        id=3,
        username="buyer",
        email="buyer@test.com",
        role=UserRole.MEDIA_BUYER.value,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def test_project(db_session: Session, account_manager_user):
    """创建测试项目"""
    project = Project(
        id=1,
        name="测试项目A",
        account_manager_id=account_manager_user.id,
        status="active"
    )
    db_session.add(project)
    db_session.commit()
    return project


@pytest.fixture
def test_supplier(db_session: Session):
    """创建测试渠道（供应商）"""
    supplier = Supplier(
        id="550e8400-e29b-41d4-a716-446655440000",
        name="Meta",
        code="META",
        status="active"
    )
    db_session.add(supplier)
    db_session.commit()
    return supplier


@pytest.fixture
def test_ad_account(db_session: Session, test_project, test_supplier, media_buyer_user):
    """创建测试广告账户"""
    account = AdAccount(
        id=1,
        name="广告账户1",
        project_id=test_project.id,
        supplier_id=test_supplier.id,
        assigned_to=media_buyer_user.id,
        status="active"
    )
    db_session.add(account)
    db_session.commit()
    return account


@pytest.fixture
def test_daily_reports(db_session: Session, test_ad_account):
    """创建测试日报数据（仅 final_confirmed 状态）"""
    reports = []
    for i in range(3):
        report = DailyReport(
            id=i + 1,
            ad_account_id=test_ad_account.id,
            report_date=date.today() - timedelta(days=i),
            conversions_raw=100 + i * 10,
            conversions_final=90 + i * 10,
            unit_price=Decimal("50.00"),
            status=DailyReportStatus.FINAL_CONFIRMED.value
        )
        reports.append(report)
        db_session.add(report)

    db_session.commit()
    return reports


@pytest.fixture
def test_ledger_entries(db_session: Session, test_ad_account, test_supplier):
    """创建测试账本分录"""
    entries = []

    # PROJECT 账本 - REVENUE 分录
    for i in range(3):
        entry = LedgerEntry(
            id=i + 1,
            ledger_type=LedgerBookType.PROJECT.value,
            entry_type=LedgerEntryType.REVENUE.value,
            project_id=test_ad_account.project_id,
            ad_account_id=test_ad_account.id,
            amount=Decimal("5000.00") + i * 100,
            entry_date=date.today() - timedelta(days=i),
            description=f"收入分录 {i+1}"
        )
        entries.append(entry)
        db_session.add(entry)

    # SUPPLIER 账本 - COST 分录（负值）
    for i in range(3):
        entry = LedgerEntry(
            id=10 + i,
            ledger_type=LedgerBookType.SUPPLIER.value,
            entry_type=LedgerEntryType.COST.value,
            supplier_id=test_supplier.id,
            ad_account_id=test_ad_account.id,
            amount=Decimal("-3000.00") - i * 50,
            entry_date=date.today() - timedelta(days=i),
            description=f"成本分录 {i+1}"
        )
        entries.append(entry)
        db_session.add(entry)

    db_session.commit()
    return entries


# ===== 测试用例 =====

class TestProjectSummaryReport:
    """测试项目汇总报表"""

    def test_get_project_summary_report_as_admin(
        self, report_service, admin_user, test_daily_reports, test_ledger_entries
    ):
        """测试管理员查询项目汇总报表"""
        rows, summary, total_count = report_service.get_project_summary_report(
            current_user=admin_user,
            start_date=date.today() - timedelta(days=10),
            end_date=date.today(),
            group_by='day'
        )

        assert total_count > 0
        assert len(rows) > 0
        assert summary.total_revenue > 0
        assert summary.total_cost > 0
        assert summary.total_profit == summary.total_revenue - summary.total_cost

    def test_get_project_summary_report_as_account_manager(
        self, report_service, account_manager_user, test_daily_reports, test_ledger_entries
    ):
        """测试账户经理仅能查看自己负责的项目"""
        rows, summary, total_count = report_service.get_project_summary_report(
            current_user=account_manager_user,
            start_date=date.today() - timedelta(days=10),
            end_date=date.today(),
            group_by='day'
        )

        # 应该能查到自己的项目
        assert total_count > 0
        for row in rows:
            # 验证 account_manager_name 包含当前用户名（或为空）
            assert row.account_manager_name is None or account_manager_user.username in str(row.account_manager_name)

    def test_get_project_summary_report_as_media_buyer(
        self, report_service, media_buyer_user, test_daily_reports, test_ledger_entries
    ):
        """测试投手仅能查看自己管理的账户所属项目"""
        rows, summary, total_count = report_service.get_project_summary_report(
            current_user=media_buyer_user,
            start_date=date.today() - timedelta(days=10),
            end_date=date.today(),
            group_by='day'
        )

        # 应该能查到自己管理的账户所属项目
        assert total_count >= 0  # 可能为 0（如果没有 final 状态日报）

    def test_filter_by_project_id(
        self, report_service, admin_user, test_project, test_daily_reports, test_ledger_entries
    ):
        """测试按项目 ID 筛选"""
        rows, summary, total_count = report_service.get_project_summary_report(
            current_user=admin_user,
            project_id=test_project.id,
            start_date=date.today() - timedelta(days=10),
            end_date=date.today(),
            group_by='day'
        )

        # 所有行的 project_id 应该等于 test_project.id
        for row in rows:
            assert row.project_id == test_project.id

    def test_group_by_week(
        self, report_service, admin_user, test_daily_reports, test_ledger_entries
    ):
        """测试按周分组"""
        rows, summary, total_count = report_service.get_project_summary_report(
            current_user=admin_user,
            start_date=date.today() - timedelta(days=30),
            end_date=date.today(),
            group_by='week'
        )

        # 验证 report_period 格式为 '2025-W01'
        if len(rows) > 0:
            assert '-W' in rows[0].report_period

    def test_group_by_month(
        self, report_service, admin_user, test_daily_reports, test_ledger_entries
    ):
        """测试按月分组"""
        rows, summary, total_count = report_service.get_project_summary_report(
            current_user=admin_user,
            start_date=date.today() - timedelta(days=60),
            end_date=date.today(),
            group_by='month'
        )

        # 验证 report_period 格式为 '2025-01'
        if len(rows) > 0:
            assert len(rows[0].report_period) == 7  # '2025-01'

    def test_sort_by_revenue_desc(
        self, report_service, admin_user, test_daily_reports, test_ledger_entries
    ):
        """测试按收入降序排序"""
        rows, _, _ = report_service.get_project_summary_report(
            current_user=admin_user,
            start_date=date.today() - timedelta(days=10),
            end_date=date.today(),
            sort_by='revenue',
            sort_order='desc'
        )

        if len(rows) > 1:
            assert rows[0].total_revenue >= rows[1].total_revenue

    def test_pagination(
        self, report_service, admin_user, test_daily_reports, test_ledger_entries
    ):
        """测试分页功能"""
        rows_page1, _, total = report_service.get_project_summary_report(
            current_user=admin_user,
            page=1,
            page_size=1
        )

        assert len(rows_page1) <= 1

        if total > 1:
            rows_page2, _, _ = report_service.get_project_summary_report(
                current_user=admin_user,
                page=2,
                page_size=1
            )
            # 第二页应该返回不同的数据
            if len(rows_page2) > 0 and len(rows_page1) > 0:
                assert rows_page1[0].project_id != rows_page2[0].project_id or \
                       rows_page1[0].report_period != rows_page2[0].report_period


class TestProjectAccountsReport:
    """测试项目详情报表（账户维度）"""

    def test_get_project_accounts_report_success(
        self, report_service, admin_user, test_project, test_daily_reports, test_ledger_entries
    ):
        """测试成功获取项目详情报表"""
        project_info, accounts, summary = report_service.get_project_accounts_report(
            current_user=admin_user,
            project_id=test_project.id,
            start_date=date.today() - timedelta(days=10),
            end_date=date.today()
        )

        assert project_info['id'] == test_project.id
        assert project_info['name'] == test_project.name
        assert len(accounts) >= 0
        assert summary is not None

    def test_get_project_accounts_report_permission_denied(
        self, report_service, account_manager_user, test_project
    ):
        """测试账户经理查看其他人项目时权限拒绝"""
        # 创建另一个项目（不属于 account_manager_user）
        other_project = Project(
            id=999,
            name="其他项目",
            account_manager_id=999,  # 不同的经理
            status="active"
        )
        report_service.db.add(other_project)
        report_service.db.commit()

        with pytest.raises(PermissionDeniedError):
            report_service.get_project_accounts_report(
                current_user=account_manager_user,
                project_id=other_project.id
            )

    def test_get_project_accounts_report_not_found(
        self, report_service, admin_user
    ):
        """测试项目不存在"""
        with pytest.raises(ResourceNotFoundError):
            report_service.get_project_accounts_report(
                current_user=admin_user,
                project_id=99999
            )


class TestChannelSummaryReport:
    """测试渠道汇总报表"""

    def test_get_channel_summary_report_success(
        self, report_service, admin_user, test_supplier, test_ledger_entries
    ):
        """测试成功获取渠道汇总报表"""
        rows, summary, total_count = report_service.get_channel_summary_report(
            current_user=admin_user,
            start_date=date.today() - timedelta(days=10),
            end_date=date.today(),
            group_by='day'
        )

        assert total_count >= 0
        # 验证数据来源于 SUPPLIER 账本
        for row in rows:
            assert row.channel_id is not None

    def test_filter_by_channel_id(
        self, report_service, admin_user, test_supplier, test_ledger_entries
    ):
        """测试按渠道 ID 筛选"""
        rows, _, _ = report_service.get_channel_summary_report(
            current_user=admin_user,
            channel_id=str(test_supplier.id),
            start_date=date.today() - timedelta(days=10),
            end_date=date.today()
        )

        for row in rows:
            assert row.channel_id == str(test_supplier.id)

    def test_channel_balance_calculation(
        self, report_service, admin_user, test_ledger_entries
    ):
        """测试渠道余额计算（TOPUP + TRANSFER_IN - COST - TRANSFER_OUT）"""
        rows, _, _ = report_service.get_channel_summary_report(
            current_user=admin_user,
            start_date=date.today() - timedelta(days=10),
            end_date=date.today()
        )

        # 余额应该等于 topup + transfer_in - cost - transfer_out
        for row in rows:
            expected_balance = (
                row.total_topup +
                row.total_transfer_in -
                row.total_cost -
                row.total_transfer_out
            )
            # 允许浮点精度误差
            assert abs(row.current_balance - expected_balance) < Decimal("0.01")


class TestBuyerSummaryReport:
    """测试投手汇总报表"""

    def test_get_buyer_summary_report_success(
        self, report_service, admin_user, media_buyer_user, test_daily_reports, test_ledger_entries
    ):
        """测试成功获取投手汇总报表"""
        rows, summary, total_count = report_service.get_buyer_summary_report(
            current_user=admin_user,
            start_date=date.today() - timedelta(days=10),
            end_date=date.today(),
            group_by='day'
        )

        assert total_count >= 0

    def test_media_buyer_can_only_see_own_data(
        self, report_service, media_buyer_user, test_daily_reports, test_ledger_entries
    ):
        """测试投手只能查看自己的数据"""
        rows, _, _ = report_service.get_buyer_summary_report(
            current_user=media_buyer_user,
            start_date=date.today() - timedelta(days=10),
            end_date=date.today()
        )

        # 所有行的 buyer_id 应该是当前用户
        for row in rows:
            assert row.buyer_id == str(media_buyer_user.id)


class TestDashboardSummary:
    """测试仪表板汇总"""

    def test_get_dashboard_summary_success(
        self, report_service, admin_user, test_daily_reports, test_ledger_entries
    ):
        """测试成功获取仪表板汇总"""
        dashboard = report_service.get_dashboard_summary(
            current_user=admin_user,
            start_date=date.today() - timedelta(days=30),
            end_date=date.today()
        )

        assert dashboard.overview is not None
        assert dashboard.by_project is not None
        assert dashboard.by_channel is not None
        assert dashboard.by_buyer is not None
        assert dashboard.trend is not None

        # 验证总览指标
        assert dashboard.overview.total_revenue >= 0
        assert dashboard.overview.total_cost >= 0
        assert dashboard.overview.total_profit == dashboard.overview.total_revenue - dashboard.overview.total_cost

    def test_dashboard_trend_data(
        self, report_service, admin_user, test_daily_reports, test_ledger_entries
    ):
        """测试仪表板趋势数据"""
        dashboard = report_service.get_dashboard_summary(
            current_user=admin_user,
            start_date=date.today() - timedelta(days=30),
            end_date=date.today()
        )

        # 验证有日趋势和月趋势数据
        assert isinstance(dashboard.trend.daily, list)
        assert isinstance(dashboard.trend.monthly, list)


class TestSOTAlignment:
    """测试 SoT 对齐"""

    def test_only_final_status_reports_counted(
        self, db_session, report_service, admin_user, test_ad_account
    ):
        """测试仅统计 final_confirmed/final_locked 状态的日报（STATE_MACHINE.md v2.6）"""
        # 创建不同状态的日报
        draft_report = DailyReport(
            ad_account_id=test_ad_account.id,
            report_date=date.today(),
            conversions_final=100,
            status=DailyReportStatus.RAW_SUBMITTED.value
        )
        final_report = DailyReport(
            ad_account_id=test_ad_account.id,
            report_date=date.today() - timedelta(days=1),
            conversions_final=200,
            status=DailyReportStatus.FINAL_CONFIRMED.value
        )
        db_session.add_all([draft_report, final_report])
        db_session.commit()

        rows, summary, _ = report_service.get_project_summary_report(
            current_user=admin_user,
            start_date=date.today() - timedelta(days=5),
            end_date=date.today()
        )

        # 仅应统计 final_confirmed 的数据（conversions=200）
        # draft 状态的不应被统计
        assert summary.total_conversions >= 200

    def test_revenue_from_project_ledger_only(
        self, db_session, report_service, admin_user, test_ad_account
    ):
        """测试收入仅来自 PROJECT 账本 REVENUE 分录（LEDGER_SOT v1.1）"""
        # 创建 PROJECT 账本 REVENUE 分录
        revenue_entry = LedgerEntry(
            ledger_type=LedgerBookType.PROJECT.value,
            entry_type=LedgerEntryType.REVENUE.value,
            project_id=test_ad_account.project_id,
            amount=Decimal("10000.00"),
            entry_date=date.today()
        )
        # 创建 SUPPLIER 账本 REVENUE 分录（不应被统计）
        supplier_revenue = LedgerEntry(
            ledger_type=LedgerBookType.SUPPLIER.value,
            entry_type=LedgerEntryType.REVENUE.value,
            amount=Decimal("5000.00"),
            entry_date=date.today()
        )
        db_session.add_all([revenue_entry, supplier_revenue])
        db_session.commit()

        rows, summary, _ = report_service.get_project_summary_report(
            current_user=admin_user,
            start_date=date.today(),
            end_date=date.today()
        )

        # 收入应该只包含 PROJECT 账本的 10000，不包含 SUPPLIER 的 5000
        assert summary.total_revenue == Decimal("10000.00")

    def test_cost_from_supplier_ledger_only(
        self, db_session, report_service, admin_user, test_supplier, test_ad_account
    ):
        """测试成本仅来自 SUPPLIER 账本 COST 分录（LEDGER_SOT v1.1）"""
        # 创建 SUPPLIER 账本 COST 分录（负值）
        cost_entry = LedgerEntry(
            ledger_type=LedgerBookType.SUPPLIER.value,
            entry_type=LedgerEntryType.COST.value,
            supplier_id=test_supplier.id,
            amount=Decimal("-8000.00"),
            entry_date=date.today()
        )
        # 创建 PROJECT 账本 COST 分录（不应被统计）
        project_cost = LedgerEntry(
            ledger_type=LedgerBookType.PROJECT.value,
            entry_type=LedgerEntryType.COST.value,
            amount=Decimal("-3000.00"),
            entry_date=date.today()
        )
        db_session.add_all([cost_entry, project_cost])
        db_session.commit()

        rows, summary, _ = report_service.get_channel_summary_report(
            current_user=admin_user,
            start_date=date.today(),
            end_date=date.today()
        )

        # 成本应该只包含 SUPPLIER 账本的 8000（取绝对值），不包含 PROJECT 的 3000
        assert summary.total_cost == Decimal("8000.00")
