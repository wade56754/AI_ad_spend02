#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库模型单元测试
测试所有核心模型的字段验证、约束和业务逻辑
"""

import pytest
from decimal import Decimal
from datetime import datetime, date
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.models import User, Project, Channel, AdAccount, TopUp, DailyReport, AuditLog
from tests.conftest import assert_decimal_equal, pytest_marks


@pytest.mark.unit
class TestUser:
    """用户模型测试"""

    def test_create_user_success(self, db_session: Session):
        """测试成功创建用户"""
        user = User(
            email="test@example.com",
            username="test_user",
            password_hash="hashed_password",
            name="测试用户",
            role="client"
        )

        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.username == "test_user"
        assert user.name == "测试用户"
        assert user.role == "client"
        assert user.is_active is True  # 默认值
        assert user.created_at is not None
        assert user.updated_at is not None

    def test_user_email_unique(self, db_session: Session):
        """测试邮箱唯一性约束"""
        # 创建第一个用户
        user1 = User(
            email="duplicate@example.com",
            username="user1",
            password_hash="pass1",
            name="用户1"
        )
        db_session.add(user1)
        db_session.commit()

        # 尝试创建相同邮箱的用户
        user2 = User(
            email="duplicate@example.com",
            username="user2",
            password_hash="pass2",
            name="用户2"
        )
        db_session.add(user2)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_user_role_validation(self, db_session: Session):
        """测试用户角色枚举值"""
        valid_roles = ["admin", "client", "operator", "manager"]

        for role in valid_roles:
            user = User(
                email=f"{role}@example.com",
                username=f"{role}_user",
                password_hash="pass",
                role=role,
                name=f"{role}用户"
            )
            db_session.add(user)
            db_session.commit()
            assert user.role == role
            db_session.delete(user)
            db_session.commit()

    def test_user_soft_delete(self, db_session: Session):
        """测试用户软删除"""
        user = User(
            email="delete@example.com",
            username="delete_user",
            password_hash="pass",
            name="待删除用户"
        )
        db_session.add(user)
        db_session.commit()

        # 软删除
        user.is_active = False
        user.deleted_at = datetime.now()
        db_session.commit()

        retrieved_user = db_session.query(User).filter(User.id == user.id).first()
        assert retrieved_user is not None
        assert retrieved_user.is_active is False
        assert retrieved_user.deleted_at is not None

    @pytest.mark.parametrize("field,value", [
        ("email", None),
        ("username", None),
        ("password_hash", None),
        ("role", None),
    ])
    def test_user_required_fields(self, db_session: Session, field, value):
        """测试必填字段"""
        user_data = {
            "email": "test@example.com",
            "username": "test_user",
            "password_hash": "pass",
            "name": "测试用户",
            "role": "client"
        }
        user_data[field] = value

        user = User(**user_data)
        db_session.add(user)

        with pytest.raises((IntegrityError, TypeError)):
            db_session.commit()


@pytest.mark.unit
class TestProject:
    """项目模型测试"""

    def test_create_project_success(self, db_session: Session, test_user):
        """测试成功创建项目"""
        project = Project(
            name="测试项目",
            description="项目描述",
            owner_id=test_user.id,
            total_budget=Decimal("10000.00"),
            daily_budget=Decimal("500.00"),
            cpl_target=Decimal("50.00"),
            cpl_tolerance=Decimal("5.00")
        )

        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)

        assert project.id is not None
        assert project.name == "测试项目"
        assert project.owner_id == test_user.id
        assert project.status == "active"  # 默认值
        assert_decimal_equal(project.total_budget, Decimal("10000.00"))
        assert_decimal_equal(project.daily_budget, Decimal("500.00"))

    def test_project_budget_validation(self, db_session: Session, test_user):
        """测试预算字段验证"""
        # 测试正数预算
        project = Project(
            name="正数预算项目",
            owner_id=test_user.id,
            total_budget=Decimal("10000.00"),
            daily_budget=Decimal("100.00")
        )
        db_session.add(project)
        db_session.commit()
        assert project.total_budget > 0
        assert project.daily_budget > 0

    def test_project_status_transition(self, db_session: Session, test_user):
        """测试项目状态转换"""
        project = Project(
            name="状态测试项目",
            owner_id=test_user.id,
            status="draft"
        )
        db_session.add(project)
        db_session.commit()

        # 测试状态转换
        valid_transitions = [
            ("draft", "active"),
            ("active", "paused"),
            ("paused", "active"),
            ("active", "completed"),
            ("paused", "completed"),
        ]

        for from_status, to_status in valid_transitions:
            project.status = from_status
            db_session.commit()
            assert project.status == from_status

            project.status = to_status
            db_session.commit()
            assert project.status == to_status

    def test_project_cpl_tolerance_calculation(self, db_session: Session, test_user):
        """测试CPL容差计算"""
        project = Project(
            name="CPL测试项目",
            owner_id=test_user.id,
            cpl_target=Decimal("50.00"),
            cpl_tolerance=Decimal("5.00")  # 10%
        )
        db_session.add(project)
        db_session.commit()

        # 计算容差百分比
        tolerance_percent = (project.cpl_tolerance / project.cpl_target) * 100
        assert tolerance_percent == 10.0

    def test_project_dates(self, db_session: Session, test_user):
        """测试项目日期字段"""
        start_date = date.today()
        end_date = date(2025, 12, 31)

        project = Project(
            name="日期测试项目",
            owner_id=test_user.id,
            start_date=start_date,
            end_date=end_date
        )
        db_session.add(project)
        db_session.commit()

        assert project.start_date == start_date
        assert project.end_date == end_date
        assert project.created_at is not None


@pytest.mark.unit
class TestTopUp:
    """充值申请模型测试"""

    def test_create_topup_success(self, db_session: Session, test_project, test_channel):
        """测试成功创建充值申请"""
        topup = TopUp(
            project_id=test_project.id,
            channel_id=test_channel.id,
            amount=Decimal("1000.00"),
            actual_amount=Decimal("1000.00"),
            status="draft",
            requested_by=test_project.owner_id,
            receipt_image="receipt.jpg",
            notes="测试充值"
        )

        db_session.add(topup)
        db_session.commit()
        db_session.refresh(topup)

        assert topup.id is not None
        assert topup.project_id == test_project.id
        assert topup.amount == Decimal("1000.00")
        assert topup.status == "draft"
        assert topup.created_at is not None

    @pytest.mark.parametrize("status", ["draft", "pending", "approved", "paid", "posted", "rejected"])
    def test_topup_status_values(self, db_session: Session, test_project, status):
        """测试充值申请状态值"""
        topup = TopUp(
            project_id=test_project.id,
            amount=Decimal("1000.00"),
            status=status,
            requested_by=test_project.owner_id
        )
        db_session.add(topup)
        db_session.commit()
        assert topup.status == status

    def test_topup_amount_validation(self, db_session: Session, test_project):
        """测试充值金额验证"""
        # 测试正数金额
        topup = TopUp(
            project_id=test_project.id,
            amount=Decimal("1000.00"),
            status="draft",
            requested_by=test_project.owner_id
        )
        db_session.add(topup)
        db_session.commit()
        assert topup.amount > 0

    def test_topup_status_flow(self, db_session: Session, test_project):
        """测试充值申请状态流"""
        topup = TopUp(
            project_id=test_project.id,
            amount=Decimal("1000.00"),
            status="draft",
            requested_by=test_project.owner_id
        )
        db_session.add(topup)
        db_session.commit()

        # 正常状态流
        status_flow = ["draft", "pending", "approved", "paid", "posted"]

        for status in status_flow:
            topup.status = status
            topup.updated_at = datetime.now()
            db_session.commit()
            assert topup.status == status

    def test_topup_with_approval_chain(self, db_session: Session, test_project, test_user):
        """测试充值申请审批链"""
        topup = TopUp(
            project_id=test_project.id,
            amount=Decimal("1000.00"),
            status="draft",
            requested_by=test_project.owner_id
        )
        db_session.add(topup)
        db_session.commit()

        # 提交审批
        topup.status = "pending"
        topup.submitted_at = datetime.now()
        db_session.commit()

        # 审批
        topup.status = "approved"
        topup.approved_by = test_user.id
        topup.approved_at = datetime.now()
        db_session.commit()

        assert topup.approved_by == test_user.id
        assert topup.approved_at is not None


@pytest.mark.unit
class TestDailyReport:
    """日报模型测试"""

    def test_create_daily_report_success(self, db_session: Session, test_ad_account):
        """测试成功创建日报"""
        report = DailyReport(
            account_id=test_ad_account.id,
            report_date=date.today(),
            impressions=10000,
            clicks=500,
            conversions=10,
            spend=Decimal("250.00"),
            revenue=Decimal("500.00"),
            cpl=Decimal("25.00"),
            cpa=Decimal("50.00"),
            ctr=Decimal("0.05"),
            conversion_rate=Decimal("0.02")
        )

        db_session.add(report)
        db_session.commit()
        db_session.refresh(report)

        assert report.id is not None
        assert report.account_id == test_ad_account.id
        assert report.report_date == date.today()
        assert report.impressions == 10000
        assert report.clicks == 500
        assert Decimal(str(report.spend)) == Decimal("250.00")

    def test_daily_report_unique_date(self, db_session: Session, test_ad_account):
        """测试日报日期唯一性"""
        report_date = date.today()

        # 创建第一条日报
        report1 = DailyReport(
            account_id=test_ad_account.id,
            report_date=report_date,
            impressions=1000,
            spend=Decimal("100.00")
        )
        db_session.add(report1)
        db_session.commit()

        # 尝试创建相同日期的日报
        report2 = DailyReport(
            account_id=test_ad_account.id,
            report_date=report_date,
            impressions=2000,
            spend=Decimal("200.00")
        )
        db_session.add(report2)

        # 应该违反唯一约束
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_daily_report_calculations(self, db_session: Session, test_ad_account):
        """测试日报计算字段"""
        report = DailyReport(
            account_id=test_ad_account.id,
            report_date=date.today(),
            impressions=10000,
            clicks=500,
            conversions=10,
            spend=Decimal("250.00"),
            revenue=Decimal("500.00")
        )

        # 手动计算
        report.cpl = report.spend / Decimal(str(report.conversions))
        report.cpa = report.spend / Decimal(str(report.conversions))
        report.ctr = Decimal(str(report.clicks)) / Decimal(str(report.impressions))
        report.conversion_rate = Decimal(str(report.conversions)) / Decimal(str(report.clicks))

        db_session.add(report)
        db_session.commit()

        assert_decimal_equal(report.cpl, Decimal("25.00"))
        assert_decimal_equal(report.cpa, Decimal("25.00"))
        assert_decimal_equal(report.ctr, Decimal("0.05"))
        assert_decimal_equal(report.conversion_rate, Decimal("0.02"))

    def test_daily_report_zero_conversions(self, db_session: Session, test_ad_account):
        """测试零转化情况"""
        report = DailyReport(
            account_id=test_ad_account.id,
            report_date=date.today(),
            impressions=10000,
            clicks=100,
            conversions=0,
            spend=Decimal("100.00"),
            revenue=Decimal("0.00")
        )

        # 零转化时的处理
        if report.conversions > 0:
            report.cpl = report.spend / Decimal(str(report.conversions))
        else:
            report.cpl = None

        if report.clicks > 0:
            report.conversion_rate = Decimal(str(report.conversions)) / Decimal(str(report.clicks))
        else:
            report.conversion_rate = Decimal("0.00")

        db_session.add(report)
        db_session.commit()

        assert report.cpl is None
        assert_decimal_equal(report.conversion_rate, Decimal("0.00"))


@pytest.mark.unit
class TestAuditLog:
    """审计日志模型测试"""

    def test_create_audit_log_success(self, db_session: Session, test_user):
        """测试成功创建审计日志"""
        audit_log = AuditLog(
            event_type="user_login",
            user_id=test_user.id,
            resource_type="user",
            resource_id=str(test_user.id),
            action="login",
            ip_address="127.0.0.1",
            user_agent="pytest",
            old_values='{"last_login": null}',
            new_values='{"last_login": "2025-01-01T00:00:00Z"}'
        )

        db_session.add(audit_log)
        db_session.commit()
        db_session.refresh(audit_log)

        assert audit_log.id is not None
        assert audit_log.event_type == "user_login"
        assert audit_log.user_id == test_user.id
        assert audit_log.action == "login"
        assert audit_log.created_at is not None

    def test_audit_log_json_fields(self, db_session: Session, test_user):
        """测试审计日志JSON字段"""
        test_data = {
            "field1": "value1",
            "field2": 123,
            "field3": True
        }

        audit_log = AuditLog(
            event_type="test_event",
            user_id=test_user.id,
            resource_type="test",
            action="test",
            old_values=str(test_data).replace("'", '"'),  # 转换为JSON格式
            new_values=str({"updated": True}).replace("'", '"')
        )

        db_session.add(audit_log)
        db_session.commit()

        # 验证JSON可以被解析
        import json
        old_data = json.loads(audit_log.old_values)
        assert old_data["field1"] == "value1"
        assert old_data["field2"] == 123
        assert old_data["field3"] is True

    @pytest.mark.parametrize("event_type", [
        "user_login", "user_logout", "password_change",
        "project_created", "project_updated",
        "topup_created", "topup_approved",
        "report_uploaded", "settings_changed"
    ])
    def test_audit_log_event_types(self, db_session: Session, test_user, event_type):
        """测试各种审计事件类型"""
        audit_log = AuditLog(
            event_type=event_type,
            user_id=test_user.id,
            action="test",
            resource_type="test"
        )

        db_session.add(audit_log)
        db_session.commit()
        assert audit_log.event_type == event_type


@pytest.mark.unit
class TestChannel:
    """渠道模型测试"""

    def test_create_channel_success(self, db_session: Session):
        """测试成功创建渠道"""
        channel = Channel(
            name="测试渠道",
            channel_type="douyin",
            account_type="agency",
            contact_info="contact@test.com",
            status="active",
            config={"api_endpoint": "https://api.test.com", "token": "test_token"}
        )

        db_session.add(channel)
        db_session.commit()
        db_session.refresh(channel)

        assert channel.id is not None
        assert channel.name == "测试渠道"
        assert channel.channel_type == "douyin"
        assert channel.status == "active"

    @pytest.mark.parametrize("channel_type", ["douyin", "baidu", " Tencent", "bytedance"])
    def test_channel_types(self, db_session: Session, channel_type):
        """测试不同渠道类型"""
        channel = Channel(
            name=f"{channel_type}_channel",
            channel_type=channel_type,
            status="active"
        )

        db_session.add(channel)
        db_session.commit()
        assert channel.channel_type == channel_type


@pytest.mark.unit
class TestAdAccount:
    """广告账户模型测试"""

    def test_create_ad_account_success(self, db_session: Session, test_project, test_channel):
        """测试成功创建广告账户"""
        ad_account = AdAccount(
            project_id=test_project.id,
            channel_id=test_channel.id,
            account_name="测试广告账户",
            account_id="test_acc_001",
            status="active",
            daily_budget=Decimal("100.00"),
            total_budget=Decimal("5000.00")
        )

        db_session.add(ad_account)
        db_session.commit()
        db_session.refresh(ad_account)

        assert ad_account.id is not None
        assert ad_account.project_id == test_project.id
        assert ad_account.channel_id == test_channel.id
        assert ad_account.account_name == "测试广告账户"
        assert ad_account.status == "active"

    def test_ad_account_budget_constraints(self, db_session: Session, test_project, test_channel):
        """测试广告账户预算约束"""
        ad_account = AdAccount(
            project_id=test_project.id,
            channel_id=test_channel.id,
            account_name="预算测试账户",
            daily_budget=Decimal("100.00"),
            total_budget=Decimal("3000.00")  # 30天的日预算
        )

        db_session.add(ad_account)
        db_session.commit()

        # 验证总预算应该大于等于日预算
        assert ad_account.total_budget >= ad_account.daily_budget

    @pytest.mark.parametrize("status", ["new", "testing", "active", "suspended", "dead", "archived"])
    def test_ad_account_status_values(self, db_session: Session, test_project, test_channel, status):
        """测试广告账户状态值"""
        ad_account = AdAccount(
            project_id=test_project.id,
            channel_id=test_channel.id,
            account_name=f"{status}_account",
            status=status
        )

        db_session.add(ad_account)
        db_session.commit()
        assert ad_account.status == status