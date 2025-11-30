"""
供应商服务层测试
Version: 1.0
Author: Claude Code (full_pipeline)

测试范围：
- SupplierService CRUD 操作
- 权限验证
- 业务规则校验
"""

import pytest
from decimal import Decimal
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from backend.schemas.supplier import (
    SupplierCreateRequest,
    SupplierUpdateRequest,
    SupplierStatus,
    PaymentMethod
)
from backend.services.supplier_service import SupplierService
from backend.exceptions.custom_exceptions import (
    ResourceNotFoundError,
    PermissionDeniedError,
    ResourceConflictError,
    BusinessLogicError
)


class TestSupplierService:
    """供应商服务测试类"""

    @pytest.fixture
    def supplier_service(self, db_session):
        """创建供应商服务实例"""
        return SupplierService(db_session)

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
        return SupplierCreateRequest(
            name="测试供应商",
            contact_name="张三",
            contact_email="zhangsan@example.com",
            contact_phone="13800138000",
            base_currency="USD",
            payment_method=PaymentMethod.BANK_TRANSFER,
            payment_terms="Net 30",
            country="CN",
            notes="测试供应商备注"
        )

    class TestCreateSupplier:
        """创建供应商测试"""

        def test_create_supplier_as_admin_success(
            self, supplier_service, admin_user_context, sample_create_request
        ):
            """测试管理员成功创建供应商"""
            result = supplier_service.create_supplier(
                request=sample_create_request,
                current_user_id=admin_user_context["id"],
                current_user_role=admin_user_context["role"]
            )

            assert result["name"] == "测试供应商"
            assert result["contact_name"] == "张三"
            assert result["base_currency"] == "USD"
            assert result["payment_method"] == PaymentMethod.BANK_TRANSFER.value
            assert result["status"] == SupplierStatus.ACTIVE.value

        def test_create_supplier_as_finance_success(
            self, supplier_service, finance_user_context, sample_create_request
        ):
            """测试财务成功创建供应商"""
            result = supplier_service.create_supplier(
                request=sample_create_request,
                current_user_id=finance_user_context["id"],
                current_user_role=finance_user_context["role"]
            )

            assert result["name"] == "测试供应商"

        def test_create_supplier_as_media_buyer_denied(
            self, supplier_service, media_buyer_user_context, sample_create_request
        ):
            """测试投手无权创建供应商"""
            with pytest.raises(PermissionDeniedError):
                supplier_service.create_supplier(
                    request=sample_create_request,
                    current_user_id=media_buyer_user_context["id"],
                    current_user_role=media_buyer_user_context["role"]
                )

    class TestGetSuppliers:
        """获取供应商列表测试"""

        def test_get_suppliers_empty_list(
            self, supplier_service, admin_user_context
        ):
            """测试获取空供应商列表"""
            suppliers, total = supplier_service.get_suppliers(
                current_user_id=admin_user_context["id"],
                current_user_role=admin_user_context["role"],
                page=1,
                page_size=20
            )

            assert isinstance(suppliers, list)
            assert total >= 0

        def test_get_suppliers_with_pagination(
            self, supplier_service, admin_user_context
        ):
            """测试分页获取供应商列表"""
            suppliers, total = supplier_service.get_suppliers(
                current_user_id=admin_user_context["id"],
                current_user_role=admin_user_context["role"],
                page=1,
                page_size=10
            )

            # 验证返回格式正确
            assert isinstance(suppliers, list)
            assert isinstance(total, int)

        def test_get_suppliers_with_filters(
            self, supplier_service, admin_user_context
        ):
            """测试带过滤条件获取供应商列表"""
            suppliers, total = supplier_service.get_suppliers(
                current_user_id=admin_user_context["id"],
                current_user_role=admin_user_context["role"],
                page=1,
                page_size=20,
                status="active",
                country="CN",
                search="测试"
            )

            assert isinstance(suppliers, list)

    class TestGetSupplier:
        """获取供应商详情测试"""

        def test_get_supplier_not_found(
            self, supplier_service, admin_user_context
        ):
            """测试获取不存在的供应商"""
            with pytest.raises(ResourceNotFoundError):
                supplier_service.get_supplier(
                    supplier_id=99999,
                    current_user_id=admin_user_context["id"],
                    current_user_role=admin_user_context["role"]
                )

    class TestUpdateSupplier:
        """更新供应商测试"""

        def test_update_supplier_permission_denied(
            self, supplier_service, media_buyer_user_context
        ):
            """测试投手无权更新供应商"""
            update_request = SupplierUpdateRequest(name="更新名称")

            with pytest.raises(PermissionDeniedError):
                supplier_service.update_supplier(
                    supplier_id=1,
                    request=update_request,
                    current_user_id=media_buyer_user_context["id"],
                    current_user_role=media_buyer_user_context["role"]
                )

    class TestDeleteSupplier:
        """删除供应商测试"""

        def test_delete_supplier_permission_denied_for_finance(
            self, supplier_service, finance_user_context
        ):
            """测试财务无权删除供应商"""
            with pytest.raises(PermissionDeniedError):
                supplier_service.delete_supplier(
                    supplier_id=1,
                    current_user_id=finance_user_context["id"],
                    current_user_role=finance_user_context["role"]
                )

        def test_delete_supplier_permission_denied_for_media_buyer(
            self, supplier_service, media_buyer_user_context
        ):
            """测试投手无权删除供应商"""
            with pytest.raises(PermissionDeniedError):
                supplier_service.delete_supplier(
                    supplier_id=1,
                    current_user_id=media_buyer_user_context["id"],
                    current_user_role=media_buyer_user_context["role"]
                )

    class TestSupplierStatistics:
        """供应商统计测试"""

        def test_get_supplier_statistics(
            self, supplier_service, admin_user_context
        ):
            """测试获取供应商统计信息"""
            stats = supplier_service.get_supplier_statistics(
                current_user_id=admin_user_context["id"],
                current_user_role=admin_user_context["role"]
            )

            assert "total_suppliers" in stats
            assert "active_suppliers" in stats
            assert "total_accounts_managed" in stats
            assert "total_spend" in stats

    class TestSupplierLedgerSummary:
        """供应商账本汇总测试"""

        def test_get_supplier_ledger_summary_permission_denied(
            self, supplier_service, media_buyer_user_context
        ):
            """测试投手无权查看供应商账本汇总"""
            with pytest.raises(PermissionDeniedError):
                supplier_service.get_supplier_ledger_summary(
                    supplier_id=1,
                    current_user_id=media_buyer_user_context["id"],
                    current_user_role=media_buyer_user_context["role"]
                )
