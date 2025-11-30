"""
结算服务层测试
Version: 1.0
Author: Claude Code (full_pipeline)

测试范围：
- SettlementService CRUD 操作
- 权限验证
- 状态流转验证
- 业务规则校验
"""

import pytest
from decimal import Decimal
from datetime import datetime, date, timedelta
from unittest.mock import Mock, patch, MagicMock

from backend.schemas.settlement import (
    SettlementCreateRequest,
    SettlementUpdateRequest,
    SettlementApproveRequest,
    SettlementPaymentRequest,
    SettlementStatus,
    SettlementType,
    PaymentStatus
)
from backend.services.settlement_service import SettlementService
from backend.exceptions.custom_exceptions import (
    ResourceNotFoundError,
    PermissionDeniedError,
    ResourceConflictError,
    BusinessLogicError
)


class TestSettlementService:
    """结算服务测试类"""

    @pytest.fixture
    def settlement_service(self, db_session):
        """创建结算服务实例"""
        return SettlementService(db_session)

    @pytest.fixture
    def admin_user_context(self):
        """管理员用户上下文"""
        return {"id": 1, "role": "admin"}

    @pytest.fixture
    def finance_user_context(self):
        """财务用户上下文"""
        return {"id": 2, "role": "finance"}

    @pytest.fixture
    def media_buyer_user_context(self):
        """投手用户上下文"""
        return {"id": 3, "role": "media_buyer"}

    @pytest.fixture
    def sample_create_request(self):
        """示例创建请求"""
        return SettlementCreateRequest(
            settlement_type=SettlementType.SUPPLIER_PAYMENT,
            supplier_id=1,
            period_start=date.today() - timedelta(days=30),
            period_end=date.today(),
            currency="USD",
            amount=Decimal("10000.00"),
            exchange_rate=Decimal("7.2"),
            due_date=date.today() + timedelta(days=30),
            description="测试结算"
        )

    class TestCreateSettlement:
        """创建结算测试"""

        def test_create_settlement_as_admin_success(
            self, settlement_service, admin_user_context, sample_create_request
        ):
            """测试管理员成功创建结算"""
            result = settlement_service.create_settlement(
                request=sample_create_request,
                current_user_id=admin_user_context["id"],
                current_user_role=admin_user_context["role"]
            )

            assert result["settlement_type"] == SettlementType.SUPPLIER_PAYMENT.value
            assert result["supplier_id"] == 1
            assert result["currency"] == "USD"
            assert result["status"] == SettlementStatus.DRAFT.value
            assert result["payment_status"] == PaymentStatus.UNPAID.value
            assert "settlement_no" in result
            assert result["settlement_no"].startswith("SP-")

        def test_create_settlement_as_finance_success(
            self, settlement_service, finance_user_context, sample_create_request
        ):
            """测试财务成功创建结算"""
            result = settlement_service.create_settlement(
                request=sample_create_request,
                current_user_id=finance_user_context["id"],
                current_user_role=finance_user_context["role"]
            )

            assert result["status"] == SettlementStatus.DRAFT.value

        def test_create_settlement_as_media_buyer_denied(
            self, settlement_service, media_buyer_user_context, sample_create_request
        ):
            """测试投手无权创建结算"""
            with pytest.raises(PermissionDeniedError):
                settlement_service.create_settlement(
                    request=sample_create_request,
                    current_user_id=media_buyer_user_context["id"],
                    current_user_role=media_buyer_user_context["role"]
                )

        def test_create_supplier_settlement_without_supplier_id(
            self, settlement_service, admin_user_context
        ):
            """测试供应商结算必须指定供应商ID"""
            request = SettlementCreateRequest(
                settlement_type=SettlementType.SUPPLIER_PAYMENT,
                supplier_id=None,  # 缺少供应商ID
                period_start=date.today() - timedelta(days=30),
                period_end=date.today(),
                currency="USD",
                amount=Decimal("10000.00")
            )

            with pytest.raises(BusinessLogicError) as exc_info:
                settlement_service.create_settlement(
                    request=request,
                    current_user_id=admin_user_context["id"],
                    current_user_role=admin_user_context["role"]
                )
            assert "供应商ID" in str(exc_info.value)

        def test_create_client_billing_without_client_id(
            self, settlement_service, admin_user_context
        ):
            """测试客户账单必须指定客户ID"""
            request = SettlementCreateRequest(
                settlement_type=SettlementType.CLIENT_BILLING,
                client_id=None,  # 缺少客户ID
                period_start=date.today() - timedelta(days=30),
                period_end=date.today(),
                currency="USD",
                amount=Decimal("10000.00")
            )

            with pytest.raises(BusinessLogicError) as exc_info:
                settlement_service.create_settlement(
                    request=request,
                    current_user_id=admin_user_context["id"],
                    current_user_role=admin_user_context["role"]
                )
            assert "客户ID" in str(exc_info.value)

    class TestGetSettlements:
        """获取结算列表测试"""

        def test_get_settlements_as_admin(
            self, settlement_service, admin_user_context
        ):
            """测试管理员获取结算列表"""
            settlements, total = settlement_service.get_settlements(
                current_user_id=admin_user_context["id"],
                current_user_role=admin_user_context["role"],
                page=1,
                page_size=20
            )

            assert isinstance(settlements, list)
            assert isinstance(total, int)

        def test_get_settlements_as_media_buyer_denied(
            self, settlement_service, media_buyer_user_context
        ):
            """测试投手无权查看结算列表"""
            with pytest.raises(PermissionDeniedError):
                settlement_service.get_settlements(
                    current_user_id=media_buyer_user_context["id"],
                    current_user_role=media_buyer_user_context["role"],
                    page=1,
                    page_size=20
                )

        def test_get_settlements_with_filters(
            self, settlement_service, admin_user_context
        ):
            """测试带过滤条件获取结算列表"""
            settlements, total = settlement_service.get_settlements(
                current_user_id=admin_user_context["id"],
                current_user_role=admin_user_context["role"],
                page=1,
                page_size=20,
                settlement_type="supplier_payment",
                status="draft",
                supplier_id=1
            )

            assert isinstance(settlements, list)

    class TestGetSettlement:
        """获取结算详情测试"""

        def test_get_settlement_not_found(
            self, settlement_service, admin_user_context
        ):
            """测试获取不存在的结算"""
            with pytest.raises(ResourceNotFoundError):
                settlement_service.get_settlement(
                    settlement_id=99999,
                    current_user_id=admin_user_context["id"],
                    current_user_role=admin_user_context["role"]
                )

        def test_get_settlement_permission_denied(
            self, settlement_service, media_buyer_user_context
        ):
            """测试投手无权查看结算详情"""
            with pytest.raises(PermissionDeniedError):
                settlement_service.get_settlement(
                    settlement_id=1,
                    current_user_id=media_buyer_user_context["id"],
                    current_user_role=media_buyer_user_context["role"]
                )

    class TestUpdateSettlement:
        """更新结算测试"""

        def test_update_settlement_permission_denied(
            self, settlement_service, media_buyer_user_context
        ):
            """测试投手无权更新结算"""
            update_request = SettlementUpdateRequest(
                description="更新说明"
            )

            with pytest.raises(PermissionDeniedError):
                settlement_service.update_settlement(
                    settlement_id=1,
                    request=update_request,
                    current_user_id=media_buyer_user_context["id"],
                    current_user_role=media_buyer_user_context["role"]
                )

    class TestApproveSettlement:
        """审批结算测试"""

        def test_approve_settlement_permission_denied_for_finance(
            self, settlement_service, finance_user_context
        ):
            """测试财务无权审批结算"""
            approve_request = SettlementApproveRequest(
                action="approve",
                comment="同意"
            )

            with pytest.raises(PermissionDeniedError):
                settlement_service.approve_settlement(
                    settlement_id=1,
                    request=approve_request,
                    current_user_id=finance_user_context["id"],
                    current_user_role=finance_user_context["role"]
                )

    class TestRecordPayment:
        """记录支付测试"""

        def test_record_payment_permission_denied(
            self, settlement_service, media_buyer_user_context
        ):
            """测试投手无权记录支付"""
            payment_request = SettlementPaymentRequest(
                paid_amount=Decimal("5000.00"),
                payment_method="bank_transfer",
                payment_reference="PAY-001"
            )

            with pytest.raises(PermissionDeniedError):
                settlement_service.record_payment(
                    settlement_id=1,
                    request=payment_request,
                    current_user_id=media_buyer_user_context["id"],
                    current_user_role=media_buyer_user_context["role"]
                )

    class TestCancelSettlement:
        """取消结算测试"""

        def test_cancel_settlement_permission_denied_for_finance(
            self, settlement_service, finance_user_context
        ):
            """测试财务无权取消结算"""
            with pytest.raises(PermissionDeniedError):
                settlement_service.cancel_settlement(
                    settlement_id=1,
                    current_user_id=finance_user_context["id"],
                    current_user_role=finance_user_context["role"],
                    reason="测试取消"
                )

    class TestSettlementStatistics:
        """结算统计测试"""

        def test_get_statistics_success(
            self, settlement_service, admin_user_context
        ):
            """测试获取结算统计"""
            stats = settlement_service.get_settlement_statistics(
                current_user_id=admin_user_context["id"],
                current_user_role=admin_user_context["role"]
            )

            assert "total_settlements" in stats
            assert "pending_settlements" in stats
            assert "completed_settlements" in stats
            assert "total_amount" in stats
            assert "total_paid" in stats
            assert "total_unpaid" in stats

        def test_get_statistics_permission_denied(
            self, settlement_service, media_buyer_user_context
        ):
            """测试投手无权查看统计"""
            with pytest.raises(PermissionDeniedError):
                settlement_service.get_settlement_statistics(
                    current_user_id=media_buyer_user_context["id"],
                    current_user_role=media_buyer_user_context["role"]
                )

    class TestStatusTransition:
        """状态流转测试"""

        def test_validate_draft_to_pending(self, settlement_service):
            """测试 DRAFT -> PENDING 流转"""
            result = settlement_service._validate_status_transition(
                SettlementStatus.DRAFT,
                SettlementStatus.PENDING
            )
            assert result is True

        def test_validate_pending_to_approved(self, settlement_service):
            """测试 PENDING -> APPROVED 流转"""
            result = settlement_service._validate_status_transition(
                SettlementStatus.PENDING,
                SettlementStatus.APPROVED
            )
            assert result is True

        def test_validate_invalid_transition(self, settlement_service):
            """测试无效的状态流转"""
            with pytest.raises(BusinessLogicError) as exc_info:
                settlement_service._validate_status_transition(
                    SettlementStatus.COMPLETED,
                    SettlementStatus.DRAFT
                )
            assert "无效的状态流转" in str(exc_info.value)

        def test_validate_completed_is_terminal(self, settlement_service):
            """测试 COMPLETED 为终态"""
            with pytest.raises(BusinessLogicError):
                settlement_service._validate_status_transition(
                    SettlementStatus.COMPLETED,
                    SettlementStatus.PENDING
                )

    class TestOverdueSettlements:
        """逾期结算测试"""

        def test_get_overdue_settlements(
            self, settlement_service, admin_user_context
        ):
            """测试获取逾期结算"""
            overdue = settlement_service.get_overdue_settlements(
                current_user_id=admin_user_context["id"],
                current_user_role=admin_user_context["role"]
            )

            assert isinstance(overdue, list)

        def test_get_overdue_permission_denied(
            self, settlement_service, media_buyer_user_context
        ):
            """测试投手无权查看逾期结算"""
            with pytest.raises(PermissionDeniedError):
                settlement_service.get_overdue_settlements(
                    current_user_id=media_buyer_user_context["id"],
                    current_user_role=media_buyer_user_context["role"]
                )
