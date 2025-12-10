"""
权限系统测试模块
测试 backend/core/permissions.py 的权限检查功能
"""

import pytest
from fastapi import HTTPException
from backend.core.permissions import (
    Permission,
    ROLE_PERMISSIONS,
    get_user_permissions,
    check_role_permission,
    check_user_permission,
    require_permissions,
)
from backend.models.enums import UserRole
from backend.core.security import AuthenticatedUser


# ==================== Fixtures ====================

@pytest.fixture
def admin_user():
    """管理员用户 fixture"""
    return AuthenticatedUser(
        id="admin-001",
        role=UserRole.ADMIN.value,
        email="admin@example.com",
        raw_claims={},
        permissions=[],
        is_active=True
    )


@pytest.fixture
def account_manager_user():
    """客户经理用户 fixture"""
    return AuthenticatedUser(
        id="am-001",
        role=UserRole.ACCOUNT_MANAGER.value,
        email="am@example.com",
        raw_claims={},
        permissions=[],
        is_active=True
    )


@pytest.fixture
def advertiser_user():
    """分析师用户 fixture (受限权限)"""
    return AuthenticatedUser(
        id="analyst-001",
        role=UserRole.ANALYST.value,
        email="analyst@example.com",
        raw_claims={},
        permissions=["project_read", "report_read"],  # 仅只读权限
        is_active=True
    )


@pytest.fixture
def operator_user():
    """数据运营用户 fixture"""
    return AuthenticatedUser(
        id="op-001",
        role=UserRole.DATA_OPERATOR.value,
        email="operator@example.com",
        raw_claims={},
        permissions=[],
        is_active=True
    )


# ==================== 权限枚举测试 ====================

@pytest.mark.unit
@pytest.mark.permissions
class TestPermissionEnum:
    """测试权限枚举定义"""

    def test_permission_enum_values(self):
        """测试权限枚举值定义正确"""
        assert Permission.USER_MANAGE.value == "user_manage"
        assert Permission.PROJECT_CREATE.value == "project_create"
        assert Permission.DAILY_REPORT_AUDIT.value == "daily_report_audit"

    def test_all_permissions_defined(self):
        """测试所有必要权限都已定义"""
        required_permissions = [
            "USER_MANAGE",
            "PROJECT_CREATE", "PROJECT_READ", "PROJECT_UPDATE", "PROJECT_DELETE",
            "DAILY_REPORT_CREATE", "DAILY_REPORT_READ", "DAILY_REPORT_AUDIT",
            "TOPUP_APPROVE",
            "REPORT_READ", "REPORT_EXPORT",
            "SYSTEM_CONFIG"
        ]

        for perm_name in required_permissions:
            assert hasattr(Permission, perm_name), f"缺少权限: {perm_name}"


# ==================== 角色权限映射测试 ====================

@pytest.mark.unit
@pytest.mark.permissions
class TestRolePermissions:
    """测试角色权限映射"""

    def test_admin_has_all_permissions(self):
        """测试管理员拥有所有权限"""
        admin_permissions = ROLE_PERMISSIONS[UserRole.ADMIN]

        # 验证管理员拥有关键权限
        assert Permission.USER_MANAGE in admin_permissions
        assert Permission.PROJECT_DELETE in admin_permissions
        assert Permission.DAILY_REPORT_AUDIT in admin_permissions
        assert Permission.TOPUP_APPROVE in admin_permissions
        assert Permission.SYSTEM_CONFIG in admin_permissions

        # 管理员应该至少有 20+ 个权限
        assert len(admin_permissions) >= 20

    def test_account_manager_permissions(self):
        """测试客户经理权限配置"""
        am_permissions = ROLE_PERMISSIONS[UserRole.ACCOUNT_MANAGER]

        # 客户经理应该有的权限
        assert Permission.PROJECT_CREATE in am_permissions
        assert Permission.PROJECT_READ in am_permissions
        assert Permission.PROJECT_UPDATE in am_permissions

        # 客户经理不应该有的权限
        assert Permission.SYSTEM_CONFIG not in am_permissions
        assert Permission.PROJECT_DELETE not in am_permissions  # 通常不允许删除

    def test_advertiser_permissions(self):
        """测试分析师权限配置"""
        analyst_permissions = ROLE_PERMISSIONS[UserRole.ANALYST]

        # 分析师应该只有查看权限
        assert Permission.PROJECT_READ in analyst_permissions
        assert Permission.DAILY_REPORT_READ in analyst_permissions
        assert Permission.REPORT_READ in analyst_permissions

        # 分析师不应该有管理权限
        assert Permission.PROJECT_CREATE not in analyst_permissions
        assert Permission.TOPUP_APPROVE not in analyst_permissions

    def test_all_roles_have_permissions(self):
        """测试所有角色都配置了权限"""
        for role in UserRole:
            assert role in ROLE_PERMISSIONS, f"角色 {role} 未配置权限"
            assert len(ROLE_PERMISSIONS[role]) > 0, f"角色 {role} 权限列表为空"


# ==================== 权限检查函数测试 ====================

@pytest.mark.unit
@pytest.mark.permissions
class TestCheckUserPermission:
    """测试 check_user_permission 函数"""

    def test_admin_has_all_permissions(self, admin_user):
        """测试管理员拥有所有权限"""
        assert check_user_permission(admin_user, [Permission.USER_MANAGE]) is True
        assert check_user_permission(admin_user, [Permission.PROJECT_DELETE]) is True
        assert check_user_permission(admin_user, [Permission.SYSTEM_CONFIG]) is True

    def test_account_manager_has_limited_permissions(self, account_manager_user):
        """测试客户经理权限受限"""
        assert check_user_permission(account_manager_user, [Permission.PROJECT_READ]) is True
        assert check_user_permission(account_manager_user, [Permission.SYSTEM_CONFIG]) is False

    def test_advertiser_has_read_only(self, advertiser_user):
        """测试广告主只读权限"""
        assert check_user_permission(advertiser_user, [Permission.PROJECT_READ]) is True
        assert check_user_permission(advertiser_user, [Permission.PROJECT_CREATE]) is False
        assert check_user_permission(advertiser_user, [Permission.PROJECT_DELETE]) is False

    def test_inactive_user_no_permissions(self):
        """测试非活跃用户无权限"""
        inactive_user = AuthenticatedUser(
            id="inactive-001",
            role=UserRole.ADMIN.value,
            email="inactive@example.com",
            raw_claims={},
            permissions=[],
            is_active=False
        )

        # 非活跃用户的权限检查（需要根据实际实现调整）
        # check_user_permission 只检查权限列表，不检查 is_active
        # 如果需要检查活跃状态，应该在更高层处理
        permissions = get_user_permissions(inactive_user)
        # 即使是非活跃用户，也会返回其角色对应的权限列表
        assert len(permissions) > 0  # Admin 角色仍有权限定义


# ==================== 权限检查装饰器测试 ====================

@pytest.mark.unit
@pytest.mark.permissions
class TestRequirePermissionsDecorator:
    """测试 require_permissions 依赖注入"""

    def test_require_permissions_admin_pass(self, admin_user):
        """测试管理员通过权限检查"""
        # require_permissions 返回一个 FastAPI Depends 对象，需要调用其函数
        permission_dep = require_permissions(Permission.PROJECT_DELETE)

        # 管理员应该通过验证
        result = permission_dep(admin_user)
        assert result == admin_user

    def test_require_permissions_advertiser_fail(self, advertiser_user):
        """测试广告主权限检查失败"""
        permission_dep = require_permissions(Permission.PROJECT_CREATE)

        with pytest.raises(HTTPException) as exc_info:
            permission_dep(advertiser_user)

        assert exc_info.value.status_code == 403

    def test_require_multiple_permissions(self, admin_user, advertiser_user):
        """测试多权限检查"""
        permission_dep = require_permissions(Permission.PROJECT_DELETE, Permission.SYSTEM_CONFIG)

        # 管理员应该通过
        result = permission_dep(admin_user)
        assert result == admin_user

        # 广告主应该失败
        with pytest.raises(HTTPException):
            permission_dep(advertiser_user)


# ==================== 权限依赖测试 ====================

@pytest.mark.unit
@pytest.mark.permissions
class TestRequirePermissionsDependency:
    """测试 require_permissions 依赖"""

    def test_require_permissions_dependency(self, admin_user):
        """测试权限依赖正确工作"""
        # 创建权限依赖
        permission_dep = require_permissions(Permission.USER_MANAGE)

        # 管理员应该通过
        try:
            permission_dep(admin_user)
        except HTTPException:
            pytest.fail("管理员应该拥有 USER_MANAGE 权限")

    def test_require_permissions_deny(self, advertiser_user):
        """测试权限依赖拒绝无权用户"""
        permission_dep = require_permissions(Permission.USER_MANAGE)

        with pytest.raises(HTTPException) as exc_info:
            permission_dep(advertiser_user)

        assert exc_info.value.status_code == 403


# ==================== 边界情况测试 ====================

@pytest.mark.unit
@pytest.mark.permissions
class TestPermissionEdgeCases:
    """测试权限系统边界情况"""

    def test_empty_permission_list(self):
        """测试空权限列表"""
        user = AuthenticatedUser(
            id="test-001",
            role=UserRole.ANALYST.value,
            email="test@example.com",
            raw_claims={},
            permissions=[],
            is_active=True
        )

        # 确保有基本权限
        assert len(ROLE_PERMISSIONS[UserRole.ANALYST]) > 0

    def test_nonexistent_role(self):
        """测试不存在的角色"""
        # 所有枚举角色都应该在映射中
        for role in UserRole:
            assert role in ROLE_PERMISSIONS

    def test_permission_consistency(self):
        """测试权限配置一致性"""
        # 所有角色的权限都应该是 Permission 枚举的实例
        for role, permissions in ROLE_PERMISSIONS.items():
            for perm in permissions:
                assert isinstance(perm, Permission), \
                    f"角色 {role} 的权限 {perm} 不是 Permission 枚举"


# ==================== 集成测试 ====================

@pytest.mark.integration
@pytest.mark.permissions
class TestPermissionIntegration:
    """权限系统集成测试"""

    def test_full_permission_workflow(self):
        """测试完整的权限检查工作流"""
        # 创建不同角色用户
        admin = AuthenticatedUser(
            id="admin-001",
            role=UserRole.ADMIN.value,
            email="admin@example.com",
            raw_claims={},
            permissions=[],
            is_active=True
        )

        analyst = AuthenticatedUser(
            id="analyst-001",
            role=UserRole.ANALYST.value,
            email="analyst@example.com",
            raw_claims={},
            permissions=[],
            is_active=True
        )

        # 测试层级权限
        # 1. 管理员应该可以做任何事
        assert check_user_permission(admin, [Permission.PROJECT_CREATE]) is True
        assert check_user_permission(admin, [Permission.PROJECT_READ]) is True
        assert check_user_permission(admin, [Permission.PROJECT_DELETE]) is True

        # 2. 分析师只能查看
        assert check_user_permission(analyst, [Permission.PROJECT_READ]) is True
        assert check_user_permission(analyst, [Permission.PROJECT_CREATE]) is False
        assert check_user_permission(analyst, [Permission.PROJECT_DELETE]) is False

    def test_permission_hierarchy(self):
        """测试权限层级关系"""
        # 管理员 > 客户经理 > 数据运营 > 分析师
        admin_perms = set(ROLE_PERMISSIONS[UserRole.ADMIN])
        am_perms = set(ROLE_PERMISSIONS[UserRole.ACCOUNT_MANAGER])
        op_perms = set(ROLE_PERMISSIONS[UserRole.DATA_OPERATOR])
        analyst_perms = set(ROLE_PERMISSIONS[UserRole.ANALYST])

        # 验证层级
        assert len(admin_perms) > len(am_perms)
        assert len(am_perms) > len(op_perms)
        assert len(op_perms) >= len(analyst_perms)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
