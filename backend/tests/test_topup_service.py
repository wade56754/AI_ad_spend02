"""
充值管理服务层测试
Version: 1.0
Author: Claude协作开发
"""

import pytest
from decimal import Decimal
from datetime import date, datetime, timedelta
from unittest.mock import Mock, patch

from models.topup import TopupRequest, TopupTransaction, TopupApprovalLog
from models.user import User
from models.ad_account import AdAccount
from models.project import Project
from schemas.topup import (
    TopupRequestCreate,
    TopupDataReviewRequest,
    TopupFinanceApprovalRequest,
    TopupMarkPaidRequest,
    TopupReceiptUploadRequest
)
from services.topup_service import TopupService
from exceptions.custom_exceptions import (
    ResourceNotFoundError,
    PermissionDeniedError,
    BusinessLogicError,
    ResourceConflictError
)


class TestTopupService:
    """充值管理服务测试类"""

    @pytest.fixture
    def topup_service(self, db_session):
        """创建充值服务实例"""
        return TopupService(db_session)

    @pytest.fixture
    def admin_user(self, db_session):
        """创建管理员用户"""
        user = User(
            id=1,
            email="admin@example.com",
            nickname="管理员",
            role="admin"
        )
        db_session.add(user)
        db_session.commit()
        return user

    @pytest.fixture
    def finance_user(self, db_session):
        """创建财务用户"""
        user = User(
            id=2,
            email="finance@example.com",
            nickname="财务",
            role="finance"
        )
        db_session.add(user)
        db_session.commit()
        return user

    @pytest.fixture
    def data_operator_user(self, db_session):
        """创建数据员用户"""
        user = User(
            id=3,
            email="operator@example.com",
            nickname="数据员",
            role="data_operator"
        )
        db_session.add(user)
        db_session.commit()
        return user

    @pytest.fixture
    def account_manager_user(self, db_session):
        """创建账户管理员用户"""
        user = User(
            id=4,
            email="manager@example.com",
            nickname="账户经理",
            role="account_manager"
        )
        db_session.add(user)
        db_session.commit()
        return user

    @pytest.fixture
    def media_buyer_user(self, db_session):
        """创建媒体买家用户"""
        user = User(
            id=5,
            email="buyer@example.com",
            nickname="媒体买家",
            role="media_buyer"
        )
        db_session.add(user)
        db_session.commit()
        return user

    @pytest.fixture
    def sample_project(self, db_session, admin_user):
        """创建示例项目"""
        project = Project(
            name="测试项目",
            client_name="客户A",
            client_company="客户公司A",
            status="active",
            created_by=admin_user.id
        )
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)
        return project

    @pytest.fixture
    def managed_project(self, db_session, admin_user, account_manager_user):
        """创建由账户经理管理的项目"""
        project = Project(
            name="经理项目",
            client_name="客户B",
            client_company="客户公司B",
            status="active",
            account_manager_id=account_manager_user.id,
            created_by=admin_user.id
        )
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)
        return project

    @pytest.fixture
    def sample_ad_account(self, db_session, sample_project):
        """创建示例广告账户"""
        ad_account = AdAccount(
            name="测试账户",
            project_id=sample_project.id,
            status="active"
        )
        db_session.add(ad_account)
        db_session.commit()
        db_session.refresh(ad_account)
        return ad_account

    @pytest.fixture
    def managed_ad_account(self, db_session, managed_project, media_buyer_user):
        """创建由媒体买家管理的账户"""
        ad_account = AdAccount(
            name="买家账户",
            project_id=managed_project.id,
            assigned_user_id=media_buyer_user.id,
            status="active"
        )
        db_session.add(ad_account)
        db_session.commit()
        db_session.refresh(ad_account)
        return ad_account

    @pytest.fixture
    def sample_topup_request(self, db_session, sample_ad_account, admin_user):
        """创建示例充值申请"""
        request = TopupRequest(
            request_no="TOP20251112143045001",
            ad_account_id=sample_ad_account.id,
            project_id=sample_ad_account.project_id,
            requested_amount=Decimal("1000.00"),
            currency="USD",
            urgency_level="normal",
            reason="测试充值",
            status="pending",
            requested_by=admin_user.id
        )
        db_session.add(request)
        db_session.commit()
        db_session.refresh(request)
        return request

    class TestCreateRequest:
        """创建充值申请测试"""

        def test_create_request_success(self, topup_service, media_buyer_user, managed_ad_account):
            """测试成功创建充值申请"""
            request_data = TopupRequestCreate(
                ad_account_id=managed_ad_account.id,
                requested_amount=Decimal("500.00"),
                reason="测试充值",
                urgency_level="normal"
            )

            with patch('services.topup_service.generate_request_no') as mock_generate:
                mock_generate.return_value = "TOP20251112143045002"

                request = topup_service.create_request(
                    request_data,
                    media_buyer_user
                )

            assert request.request_no == "TOP20251112143045002"
            assert request.ad_account_id == managed_ad_account.id
            assert request.requested_amount == Decimal("500.00")
            assert request.status == "pending"
            assert request.requested_by == media_buyer_user.id

        def test_create_request_amount_too_large(self, topup_service, media_buyer_user, managed_ad_account):
            """测试创建金额过大的申请"""
            request_data = TopupRequestCreate(
                ad_account_id=managed_ad_account.id,
                requested_amount=Decimal("200000.00"),  # 超过10万上限
                reason="测试充值"
            )

            with pytest.raises(BusinessLogicError) as exc:
                topup_service.create_request(request_data, media_buyer_user)

            assert "BIZ_201" in str(exc.value)

        def test_create_request_invalid_date(self, topup_service, media_buyer_user, managed_ad_account):
            """测试创建无效期望日期的申请"""
            yesterday = date.today() - timedelta(days=1)
            request_data = TopupRequestCreate(
                ad_account_id=managed_ad_account.id,
                requested_amount=Decimal("500.00"),
                reason="测试充值",
                expected_date=yesterday  # 昨天的日期
            )

            with pytest.raises(Exception):  # PydanticValidationError
                topup_service.create_request(request_data, media_buyer_user)

        def test_create_request_exceed_daily_limit(self, topup_service, media_buyer_user, managed_ad_account, db_session):
            """测试超出每日申请次数限制"""
            # 创建3个已存在的申请（达到上限）
            for i in range(3):
                request = TopupRequest(
                    request_no=f"TOP20251112143045{i:03d}",
                    ad_account_id=managed_ad_account.id,
                    project_id=managed_ad_account.project_id,
                    requested_amount=Decimal("100.00"),
                    reason="测试",
                    requested_by=media_buyer_user.id,
                    created_at=datetime.utcnow()  # 今天
                )
                db_session.add(request)
            db_session.commit()

            # 尝试创建第4个申请
            request_data = TopupRequestCreate(
                ad_account_id=managed_ad_account.id,
                requested_amount=Decimal("500.00"),
                reason="超出限制的申请"
            )

            with pytest.raises(BusinessLogicError) as exc:
                topup_service.create_request(request_data, media_buyer_user)

            assert "BIZ_204" in str(exc.value)

        def test_create_request_no_permission(self, topup_service, admin_user, sample_ad_account):
            """测试无权限创建申请"""
            # 管理员不能创建申请（只有投手和账户经理可以）
            request_data = TopupRequestCreate(
                ad_account_id=sample_ad_account.id,
                requested_amount=Decimal("500.00"),
                reason="管理员测试"
            )

            with patch('services.topup_service.generate_request_no'):
                with pytest.raises(Exception):  # 会因为权限验证失败
                    topup_service.create_request(request_data, admin_user)

    class TestDataReview:
        """数据审核测试"""

        def test_data_review_approve(self, topup_service, sample_topup_request, data_operator_user):
            """测试数据员审核通过"""
            review_data = TopupDataReviewRequest(
                action="approve",
                notes="审核通过"
            )

            request = topup_service.data_review(
                sample_topup_request.id,
                review_data,
                data_operator_user
            )

            assert request.status == "data_review"
            assert request.data_reviewed_by == data_operator_user.id
            assert request.data_review_notes == "审核通过"

        def test_data_review_reject(self, topup_service, sample_topup_request, data_operator_user):
            """测试数据员审核拒绝"""
            review_data = TopupDataReviewRequest(
                action="reject",
                notes="审核拒绝：金额不合理"
            )

            request = topup_service.data_review(
                sample_topup_request.id,
                review_data,
                data_operator_user
            )

            assert request.status == "rejected"
            assert request.data_reviewed_by == data_operator_user.id

        def test_data_review_invalid_status(self, topup_service, sample_topup_request, data_operator_user):
            """测试审核无效状态"""
            # 将状态改为已审核
            sample_topup_request.status = "data_review"
            topup_service.db.commit()

            review_data = TopupDataReviewRequest(action="approve")

            with pytest.raises(BusinessLogicError) as exc:
                topup_service.data_review(
                    sample_topup_request.id,
                    review_data,
                    data_operator_user
                )

            assert "BIZ_203" in str(exc.value)

        def test_data_review_no_permission(self, topup_service, sample_topup_request, finance_user):
            """测试非数据员无权限审核"""
            review_data = TopupDataReviewRequest(action="approve")

            with pytest.raises(PermissionDeniedError):
                topup_service.data_review(
                    sample_topup_request.id,
                    review_data,
                    finance_user
                )

    class TestFinanceApproval:
        """财务审批测试"""

        def test_finance_approve_success(self, topup_service, sample_topup_request, finance_user):
            """测试财务审批通过"""
            # 先将状态改为数据审核通过
            sample_topup_request.status = "data_review"
            topup_service.db.commit()

            approval_data = TopupFinanceApprovalRequest(
                action="approve",
                actual_amount=Decimal("950.00"),
                payment_method="bank_transfer",
                notes="财务审批通过"
            )

            request = topup_service.finance_approve(
                sample_topup_request.id,
                approval_data,
                finance_user
            )

            assert request.status == "finance_approve"
            assert request.finance_approved_by == finance_user.id
            assert request.actual_amount == Decimal("950.00")
            assert request.payment_method == "bank_transfer"

        def test_finance_approve_reject(self, topup_service, sample_topup_request, finance_user):
            """测试财务审批拒绝"""
            # 先将状态改为数据审核通过
            sample_topup_request.status = "data_review"
            topup_service.db.commit()

            approval_data = TopupFinanceApprovalRequest(
                action="reject",
                notes="财务拒绝：额度不足"
            )

            request = topup_service.finance_approve(
                sample_topup_request.id,
                approval_data,
                finance_user
            )

            assert request.status == "rejected"

        def test_finance_approve_no_actual_amount(self, topup_service, sample_topup_request, finance_user):
            """测试审批通过但未填写实际金额"""
            # 先将状态改为数据审核通过
            sample_topup_request.status = "data_review"
            topup_service.db.commit()

            approval_data = TopupFinanceApprovalRequest(
                action="approve",
                notes="忘记填金额"
            )

            with pytest.raises(Exception):  # PydanticValidationError
                topup_service.finance_approve(
                    sample_topup_request.id,
                    approval_data,
                    finance_user
                )

    class TestMarkAsPaid:
        """标记已打款测试"""

        def test_mark_as_paid_success(self, topup_service, sample_topup_request, finance_user):
            """测试成功标记为已打款"""
            # 先将状态改为财务审批通过
            sample_topup_request.status = "finance_approve"
            topup_service.db.commit()

            paid_data = TopupMarkPaidRequest(
                transaction_id="TXN20251112143045",
                notes="已通过银行转账"
            )

            request = topup_service.mark_as_paid(
                sample_topup_request.id,
                paid_data,
                finance_user
            )

            assert request.status == "paid"
            assert request.paid_at is not None
            assert request.transaction_id == "TXN20251112143045"

        def test_mark_as_paid_already_paid(self, topup_service, sample_topup_request, finance_user):
            """测试重复标记已打款"""
            # 先设置为已打款
            sample_topup_request.status = "paid"
            sample_topup_request.paid_at = datetime.utcnow()
            topup_service.db.commit()

            paid_data = TopupMarkPaidRequest()

            with pytest.raises(ResourceConflictError) as exc:
                topup_service.mark_as_paid(
                    sample_topup_request.id,
                    paid_data,
                    finance_user
                )

            assert "BIZ_207" in str(exc.value)

    class TestUploadReceipt:
        """上传凭证测试"""

        def test_upload_receipt_complete(self, topup_service, sample_topup_request, finance_user):
            """测试上传凭证并完成流程"""
            # 先标记为已打款
            sample_topup_request.status = "paid"
            sample_topup_request.paid_at = datetime.utcnow()
            sample_topup_request.actual_amount = Decimal("1000.00")
            topup_service.db.commit()

            receipt_data = TopupReceiptUploadRequest(
                receipt_url="https://example.com/receipt.jpg",
                transaction_id="TXN20251112143046",
                notes="凭证已上传"
            )

            request = topup_service.upload_receipt(
                sample_topup_request.id,
                receipt_data,
                finance_user
            )

            assert request.status == "completed"
            assert request.completed_at is not None
            assert request.receipt_url == "https://example.com/receipt.jpg"

        def test_upload_receipt_only(self, topup_service, sample_topup_request, finance_user):
            """测试仅上传凭证（未完成）"""
            # 状态不是paid
            receipt_data = TopupReceiptUploadRequest(
                receipt_url="https://example.com/receipt.jpg"
            )

            request = topup_service.upload_receipt(
                sample_topup_request.id,
                receipt_data,
                finance_user
            )

            assert request.receipt_url == "https://example.com/receipt.jpg"
            assert request.status == "pending"  # 状态未改变

    class TestGetRequests:
        """获取申请列表测试"""

        def test_get_requests_with_pagination(self, topup_service, admin_user, sample_topup_request, db_session):
            """测试分页获取申请列表"""
            # 创建多个申请
            for i in range(25):
                request = TopupRequest(
                    request_no=f"TOP20251112143045{i:03d}",
                    ad_account_id=sample_topup_request.ad_account_id,
                    project_id=sample_topup_request.project_id,
                    requested_amount=Decimal(f"{100 + i}.00"),
                    reason=f"测试申请{i}",
                    status="pending",
                    requested_by=admin_user.id
                )
                db_session.add(request)
            db_session.commit()

            requests, total = topup_service.get_requests(
                current_user=admin_user,
                page=1,
                page_size=10
            )

            assert len(requests) == 10
            assert total == 26  # 25 + 1 (fixture)

        def test_get_requests_with_filters(self, topup_service, admin_user, sample_topup_request, db_session):
            """测试带过滤条件获取申请列表"""
            # 创建不同状态的申请
            active_request = TopupRequest(
                request_no="TOP20251112143046001",
                ad_account_id=sample_topup_request.ad_account_id,
                project_id=sample_topup_request.project_id,
                requested_amount=Decimal("500.00"),
                reason="活跃申请",
                status="data_review",
                requested_by=admin_user.id
            )
            db_session.add(active_request)
            db_session.commit()

            # 按状态过滤
            requests, total = topup_service.get_requests(
                current_user=admin_user,
                status="data_review"
            )
            assert len(requests) == 1
            assert requests[0].status == "data_review"

    class TestGetStatistics:
        """获取统计数据测试"""

        def test_get_statistics_success(self, topup_service, admin_user, sample_topup_request, db_session):
            """测试成功获取统计数据"""
            # 创建不同状态的申请
            paid_request = TopupRequest(
                request_no="TOP20251112143046002",
                ad_account_id=sample_topup_request.ad_account_id,
                project_id=sample_topup_request.project_id,
                requested_amount=Decimal("2000.00"),
                actual_amount=Decimal("2000.00"),
                reason="已支付申请",
                status="completed",
                requested_by=admin_user.id
            )
            db_session.add(paid_request)
            db_session.commit()

            stats = topup_service.get_statistics(admin_user)

            assert stats.total_requests >= 2  # 至少2个申请
            assert stats.total_amount_requested >= Decimal("3000.00")

        def test_get_statistics_permission_denied(self, topup_service, media_buyer_user):
            """测试无权限获取统计数据"""
            with pytest.raises(PermissionDeniedError):
                topup_service.get_statistics(media_buyer_user)

    class TestAccountBalance:
        """账户余额测试"""

        def test_get_account_balance_success(self, topup_service, admin_user, sample_ad_account):
            """测试成功获取账户余额"""
            balance = topup_service.get_account_balance(
                sample_ad_account.id,
                admin_user
            )

            assert balance.ad_account_id == sample_ad_account.id
            assert balance.ad_account_name == sample_ad_account.name
            assert balance.max_balance == Decimal("500000")
            assert balance.available_topup == Decimal("500000")  # 初始状态

        def test_get_account_balance_no_permission(self, topup_service, media_buyer_user, sample_ad_account):
            """测试无权限获取账户余额"""
            # 媒体买家无权限访问未分配的账户
            with pytest.raises(PermissionDeniedError):
                topup_service.get_account_balance(
                    sample_ad_account.id,
                    media_buyer_user
                )