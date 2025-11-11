#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
业务逻辑测试
测试状态机、金额计算、权限验证等核心业务逻辑
"""

import pytest
from decimal import Decimal, InvalidOperation
from datetime import datetime, date, timedelta
from unittest.mock import patch, Mock
from sqlalchemy.orm import Session

from backend.models import User, Project, TopUp, AdAccount, DailyReport, Ledger
from backend.services.topup_service import TopUpService
from backend.services.project_service import ProjectService
from backend.services.auth_service import AuthService
from backend.services.financial_service import FinancialService
from backend.exceptions import BusinessError, PermissionError, ValidationError
from tests.conftest import assert_decimal_equal, pytest_marks


@pytest.mark.integration
class TestTopUpStateMachine:
    """充值申请状态机测试"""

    def test_topup_draft_to_pending(self, db_session: Session, test_topup):
        """测试草稿到待审批状态转换"""
        service = TopUpService(db_session)

        # 初始状态应该是draft
        assert test_topup.status == "draft"

        # 提交审批
        updated_topup = service.submit_for_approval(test_topup.id, requested_by=test_topup.requested_by)

        assert updated_topup.status == "pending"
        assert updated_topup.submitted_at is not None

    def test_topup_pending_to_approved(self, db_session: Session, test_topup, admin_user):
        """测试待审批到已批准状态转换"""
        service = TopUpService(db_session)

        # 先提交审批
        service.submit_for_approval(test_topup.id, requested_by=test_topup.requested_by)

        # 审批通过
        updated_topup = service.approve_topup(
            test_topup.id,
            approved_by=admin_user.id,
            notes="审批通过"
        )

        assert updated_topup.status == "approved"
        assert updated_topup.approved_by == admin_user.id
        assert updated_topup.approved_at is not None

    def test_topup_approved_to_paid(self, db_session: Session, test_topup, admin_user):
        """测试已批准到已支付状态转换"""
        service = TopUpService(db_session)

        # 设置为已批准状态
        test_topup.status = "approved"
        test_topup.approved_by = admin_user.id
        test_topup.approved_at = datetime.now()
        db_session.commit()

        # 标记为已支付
        updated_topup = service.mark_as_paid(
            test_topup.id,
            actual_amount=Decimal("1000.00"),
            payment_method="bank_transfer",
            paid_by=admin_user.id
        )

        assert updated_topup.status == "paid"
        assert updated_topup.actual_amount == Decimal("1000.00")
        assert updated_topup.paid_at is not None

    def test_topup_paid_to_posted(self, db_session: Session, test_topup, admin_user):
        """测试已支付到已入账状态转换"""
        service = TopUpService(db_session)

        # 设置为已支付状态
        test_topup.status = "paid"
        test_topup.actual_amount = Decimal("1000.00")
        test_topup.paid_at = datetime.now()
        db_session.commit()

        # 标记为已入账
        updated_topup = service.post_to_ledger(
            test_topup.id,
            posted_by=admin_user.id,
            ledger_reference="LEDGER_001"
        )

        assert updated_topup.status == "posted"
        assert updated_topup.posted_at is not None
        assert updated_topup.ledger_reference == "LEDGER_001"

    def test_topup_rejection_flow(self, db_session: Session, test_topup, admin_user):
        """测试充值申请拒绝流程"""
        service = TopUpService(db_session)

        # 先提交审批
        service.submit_for_approval(test_topup.id, requested_by=test_topup.requested_by)

        # 审批拒绝
        updated_topup = service.reject_topup(
            test_topup.id,
            rejected_by=admin_user.id,
            reason="金额超出预算"
        )

        assert updated_topup.status == "rejected"
        assert updated_topup.rejected_by == admin_user.id
        assert updated_topup.rejected_at is not None
        assert "金额超出预算" in updated_topup.notes

    @pytest.mark.parametrize("from_status,to_status,should_fail", [
        ("draft", "approved", True),   # 不能跳过pending
        ("pending", "paid", True),     # 不能跳过approved
        ("approved", "draft", True),   # 不能回退
        ("posted", "paid", True),      # 不能回退
        ("rejected", "pending", True), # 拒绝后不能恢复
    ])
    def test_invalid_state_transitions(self, db_session: Session, test_topup,
                                     from_status, to_status, should_fail):
        """测试无效的状态转换"""
        service = TopUpService(db_session)
        test_topup.status = from_status
        db_session.commit()

        with pytest.raises((BusinessError, ValidationError)) if should_fail else nullcontext():
            if to_status == "approved":
                service.approve_topup(test_topup.id, approved_by=test_topup.requested_by)
            elif to_status == "paid":
                service.mark_as_paid(test_topup.id, actual_amount=Decimal("1000.00"))
            elif to_status == "posted":
                service.post_to_ledger(test_topup.id, ledger_reference="TEST")
            elif to_status == "rejected":
                service.reject_topup(test_topup.id, rejected_by=test_topup.requested_by, reason="test")

    def test_state_transition_permissions(self, db_session: Session, test_topup, test_user):
        """测试状态转换权限"""
        service = TopUpService(db_session)

        # 普通用户不能审批自己的申请
        service.submit_for_approval(test_topup.id, requested_by=test_topup.requested_by)

        with pytest.raises(PermissionError):
            service.approve_topup(
                test_topup.id,
                approved_by=test_topup.requested_by,  # 自己审批自己的申请
                notes="测试权限"
            )


@pytest.mark.integration
class TestFinancialCalculations:
    """财务计算测试"""

    def test_cpl_calculation_within_tolerance(self, db_session: Session, test_project):
        """测试CPL在容差范围内的计算"""
        service = FinancialService(db_session)

        # 目标CPL 50元，容差5元（10%）
        target_cpl = Decimal("50.00")
        actual_cpl = Decimal("52.30")  # 超出4.6%，在容差范围内

        is_within_tolerance = service.check_cpl_tolerance(target_cpl, actual_cpl, Decimal("5.00"))

        assert is_within_tolerance is True

    def test_cpl_calculation_outside_tolerance(self, db_session: Session, test_project):
        """测试CPL超出容差范围"""
        service = FinancialService(db_session)

        target_cpl = Decimal("50.00")
        actual_cpl = Decimal("60.00")  # 超出20%，超出容差

        is_within_tolerance = service.check_cpl_tolerance(target_cpl, actual_cpl, Decimal("5.00"))

        assert is_within_tolerance is False

    def test_budget_utilization_calculation(self, db_session: Session, test_project):
        """测试预算使用率计算"""
        service = FinancialService(db_session)

        # 创建一些消费记录
        daily_spends = [Decimal("100.00"), Decimal("150.00"), Decimal("200.00")]
        total_budget = test_project.total_budget
        total_spend = sum(daily_spends)

        utilization = service.calculate_budget_utilization(total_budget, total_spend)
        expected_utilization = (total_spend / total_budget) * 100

        assert_decimal_equal(utilization, expected_utilization, Decimal("0.01"))

    def test_remaining_days_calculation(self, db_session: Session, test_project):
        """测试剩余天数计算"""
        service = FinancialService(db_session)

        # 设置项目日期
        today = date.today()
        test_project.start_date = today - timedelta(days=10)
        test_project.end_date = today + timedelta(days=20)
        db_session.commit()

        remaining_days = service.calculate_remaining_days(test_project.end_date)

        assert remaining_days == 20

    def test_daily_budget_recommendation(self, db_session: Session, test_project):
        """测试日预算推荐"""
        service = FinancialService(db_session)

        total_budget = Decimal("10000.00")
        remaining_days = 30
        current_spend = Decimal("2000.00")

        recommended_budget = service.recommend_daily_budget(
            total_budget,
            remaining_days,
            current_spend
        )

        expected_budget = (total_budget - current_spend) / remaining_days
        assert_decimal_equal(recommended_budget, expected_budget)

    def test_roi_calculation(self, db_session: Session):
        """测试ROI计算"""
        service = FinancialService(db_session)

        spend = Decimal("1000.00")
        revenue = Decimal("1500.00")

        roi = service.calculate_roi(spend, revenue)
        expected_roi = ((revenue - spend) / spend) * 100

        assert_decimal_equal(roi, expected_roi)

    def test_profit_margin_calculation(self, db_session: Session):
        """测试利润率计算"""
        service = FinancialService(db_session)

        revenue = Decimal("1500.00")
        cost = Decimal("1000.00")

        profit_margin = service.calculate_profit_margin(revenue, cost)
        expected_margin = ((revenue - cost) / revenue) * 100

        assert_decimal_equal(profit_margin, expected_margin)

    @pytest.mark.parametrize("amount", [
        Decimal("0.00"),
        Decimal("100.00"),
        Decimal("999999.99"),
        Decimal("1000000.00")  # 边界值
    ])
    def test_amount_validation(self, db_session: Session, amount):
        """测试金额验证"""
        service = FinancialService(db_session)

        # 测试有效金额
        if amount >= 0 and amount <= 999999.99:
            is_valid = service.validate_amount(amount)
            assert is_valid is True
        else:
            is_valid = service.validate_amount(amount)
            assert is_valid is False


@pytest.mark.security
class TestPermissions:
    """权限验证测试"""

    def test_project_owner_access(self, db_session: Session, test_project, test_user):
        """测试项目所有者权限"""
        service = ProjectService(db_session)

        # 项目所有者应该有访问权限
        has_access = service.check_project_access(
            project_id=test_project.id,
            user_id=test_project.owner_id,
            action="read"
        )

        assert has_access is True

    def test_non_member_access_denied(self, db_session: Session, test_project, test_client_user):
        """测试非成员访问被拒绝"""
        service = ProjectService(db_session)

        # 非项目成员不应该有访问权限
        has_access = service.check_project_access(
            project_id=test_project.id,
            user_id=test_client_user.id,
            action="read"
        )

        assert has_access is False

    def test_admin_access_all_projects(self, db_session: Session, test_project, admin_user):
        """测试管理员访问所有项目"""
        service = ProjectService(db_session)

        # 管理员应该有访问所有项目的权限
        has_access = service.check_project_access(
            project_id=test_project.id,
            user_id=admin_user.id,
            action="read"
        )

        assert has_access is True

    def test_topup_approval_permissions(self, db_session: Session, test_topup, test_user, admin_user):
        """测试充值审批权限"""
        service = TopUpService(db_session)

        # 先提交审批
        service.submit_for_approval(test_topup.id, requested_by=test_topup.requested_by)

        # 普通用户不能审批
        with pytest.raises(PermissionError):
            service.approve_topup(
                test_topup.id,
                approved_by=test_user.id,  # 普通用户
                notes="无权限审批"
            )

        # 管理员可以审批
        updated_topup = service.approve_topup(
            test_topup.id,
            approved_by=admin_user.id,  # 管理员
            notes="有权限审批"
        )

        assert updated_topup.status == "approved"

    def test_role_based_permissions(self, db_session: Session):
        """测试基于角色的权限"""
        auth_service = AuthService()

        # 测试不同角色的权限
        role_permissions = {
            "admin": ["read", "write", "delete", "approve", "manage"],
            "manager": ["read", "write", "approve"],
            "operator": ["read", "write"],
            "client": ["read"]
        }

        for role, expected_permissions in role_permissions.items():
            user_permissions = auth_service.get_role_permissions(role)
            for perm in expected_permissions:
                assert perm in user_permissions

    def test_user_project_membership(self, db_session: Session, test_project, test_user):
        """测试用户项目成员关系"""
        from backend.models import ProjectMember

        service = ProjectService(db_session)

        # 添加用户到项目
        member = ProjectMember(
            project_id=test_project.id,
            user_id=test_user.id,
            role="member"
        )
        db_session.add(member)
        db_session.commit()

        # 检查成员权限
        is_member = service.is_project_member(test_project.id, test_user.id)
        assert is_member is True

        # 移除成员
        db_session.delete(member)
        db_session.commit()

        # 再次检查
        is_member = service.is_project_member(test_project.id, test_user.id)
        assert is_member is False


@pytest.mark.functional
class TestDataIntegrity:
    """数据完整性测试"""

    def test_foreign_key_constraints(self, db_session: Session):
        """测试外键约束"""
        # 尝试创建属于不存在项目的充值申请
        with pytest.raises(Exception):  # 应该是IntegrityError
            topup = TopUp(
                project_id="00000000-0000-0000-0000-000000000000",  # 不存在的UUID
                amount=Decimal("1000.00"),
                status="draft"
            )
            db_session.add(topup)
            db_session.commit()

    def test_cascade_deletion(self, db_session: Session, test_project, test_user):
        """测试级联删除"""
        from backend.models import ProjectMember

        # 添加项目成员
        member = ProjectMember(
            project_id=test_project.id,
            user_id=test_user.id,
            role="member"
        )
        db_session.add(member)
        db_session.commit()

        # 删除项目
        db_session.delete(test_project)
        db_session.commit()

        # 检查成员记录是否被级联删除
        remaining_member = db_session.query(ProjectMember).filter(
            ProjectMember.project_id == test_project.id
        ).first()

        assert remaining_member is None

    def test_transaction_rollback(self, db_session: Session, test_project):
        """测试事务回滚"""
        original_budget = test_project.total_budget

        try:
            # 开始事务
            # 更新项目预算
            test_project.total_budget = Decimal("20000.00")

            # 创建一个会导致错误的操作
            invalid_topup = TopUp(
                project_id=None,  # 必填字段为空
                amount=Decimal("1000.00")
            )
            db_session.add(invalid_topup)
            db_session.commit()

        except Exception:
            # 事务应该回滚
            db_session.rollback()

            # 检查预算是否恢复原值
            db_session.refresh(test_project)
            assert test_project.total_budget == original_budget

    def test_concurrent_updates(self, db_session: Session, test_project):
        """测试并发更新"""
        # 使用两个会话模拟并发
        session1 = TestSessionLocal()
        session2 = TestSessionLocal()

        try:
            # 会话1读取
            project1 = session1.query(Project).filter(Project.id == test_project.id).first()

            # 会话2读取
            project2 = session2.query(Project).filter(Project.id == test_project.id).first()

            # 会话1更新
            project1.total_budget = Decimal("15000.00")
            session1.commit()

            # 会话2更新（应该基于旧版本）
            project2.total_budget = Decimal("20000.00")

            # 这里可能会有并发冲突，取决于数据库配置
            session2.commit()

            # 验证最终状态
            final_project = db_session.query(Project).filter(Project.id == test_project.id).first()
            assert final_project.total_budget in [Decimal("15000.00"), Decimal("20000.00")]

        finally:
            session1.close()
            session2.close()


@pytest.mark.unit
class TestValidationRules:
    """验证规则测试"""

    def test_email_validation(self):
        """测试邮箱验证"""
        from backend.core.validators import validate_email

        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "user+tag@example.org"
        ]

        invalid_emails = [
            "invalid-email",
            "@example.com",
            "user@",
            "user..name@example.com",
            "user@.com"
        ]

        for email in valid_emails:
            assert validate_email(email) is True

        for email in invalid_emails:
            assert validate_email(email) is False

    def test_phone_validation(self):
        """测试手机号验证"""
        from backend.core.validators import validate_phone

        valid_phones = [
            "13812345678",
            "+8613812345678",
            "15912345678"
        ]

        invalid_phones = [
            "12812345678",  # 不是有效的手机号段
            "123456",
            "abc12345678"
        ]

        for phone in valid_phones:
            assert validate_phone(phone) is True

        for phone in invalid_phones:
            assert validate_phone(phone) is False

    def test_date_range_validation(self):
        """测试日期范围验证"""
        from datetime import date
        from backend.core.validators import validate_date_range

        start_date = date(2025, 1, 1)
        end_date = date(2025, 12, 31)

        # 有效范围
        assert validate_date_range(start_date, end_date) is True

        # 开始日期晚于结束日期
        invalid_end_date = date(2024, 12, 31)
        assert validate_date_range(start_date, invalid_end_date) is False

        # 未来的结束日期
        future_date = date.today() + timedelta(days=400)
        assert validate_date_range(date.today(), future_date) is False

    def test_budget_validation(self):
        """测试预算验证"""
        from backend.core.validators import validate_budget

        # 有效预算
        assert validate_budget(Decimal("100.00")) is True
        assert validate_budget(Decimal("999999.99")) is True

        # 无效预算
        assert validate_budget(Decimal("0.00")) is False
        assert validate_budget(Decimal("-100.00")) is False
        assert validate_budget(Decimal("1000000.00")) is False