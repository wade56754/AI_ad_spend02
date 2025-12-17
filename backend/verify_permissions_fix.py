"""
简单验证脚本：检查 test_permissions.py 的导入是否正确
"""
import sys
sys.path.insert(0, 'd:/git/1108')

print("Step 1: 验证 backend.core.permissions 导入...")
try:
    from backend.core.permissions import (
        Permission,
        ROLE_PERMISSIONS,
        get_user_permissions,
        check_role_permission,
        check_user_permission,
        require_permissions,
    )
    print("✅ 所有函数导入成功!")
    print(f"  - Permission: {Permission}")
    print(f"  - ROLE_PERMISSIONS: {type(ROLE_PERMISSIONS)}")
    print(f"  - get_user_permissions: {get_user_permissions}")
    print(f"  - check_role_permission: {check_role_permission}")
    print(f"  - check_user_permission: {check_user_permission}")
    print(f"  - require_permissions: {require_permissions}")
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    sys.exit(1)

print("\nStep 2: 验证 AuthenticatedUser 导入...")
try:
    from backend.core.security import AuthenticatedUser
    print("✅ AuthenticatedUser 导入成功!")
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    sys.exit(1)

print("\nStep 3: 验证 UserRole 导入...")
try:
    from backend.models.enums import UserRole
    print("✅ UserRole 导入成功!")
    print(f"  角色列表: {[r.value for r in UserRole]}")
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    sys.exit(1)

print("\nStep 4: 测试基本权限检查...")
try:
    admin_user = AuthenticatedUser(
        user_id="test-admin",
        username="admin",
        email="admin@test.com",
        role=UserRole.ADMIN,
        is_active=True
    )

    # 测试 get_user_permissions
    perms = get_user_permissions(admin_user)
    print(f"✅ get_user_permissions 工作正常! 管理员权限数: {len(perms)}")

    # 测试 check_user_permission
    has_perm = check_user_permission(admin_user, [Permission.USER_MANAGE])
    print(f"✅ check_user_permission 工作正常! 结果: {has_perm}")

except Exception as e:
    print(f"❌ 运行时错误: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*60)
print("🎉 所有验证通过! test_permissions.py 的修复应该是正确的!")
print("="*60)
