# test_permissions.py 修复指南

## 问题分析

test_permissions.py 文件中使用了不存在的函数名，需要更新为实际存在的函数。

## 需要修改的导入语句

### 当前导入（第7-13行）
```python
from backend.core.permissions import (
    Permission,
    ROLE_PERMISSIONS,
    check_permission,      # ❌ 不存在
    has_permission,         # ❌ 不存在
    require_permission,     # ❌ 不存在
)
```

### 修复后的导入
```python
from backend.core.permissions import (
    Permission,
    ROLE_PERMISSIONS,
    get_user_permissions,      # ✅ 获取用户权限列表
    check_role_permission,     # ✅ 检查角色权限
    check_user_permission,     # ✅ 检查用户权限
    require_permissions,       # ✅ 权限装饰器（注意是复数）
)
```

## 需要修改的测试代码

### 1. has_permission() 调用需要改为 check_user_permission()

**查找**: `has_permission(`
**替换为**: `check_user_permission(`

**示例**:
```python
# 修改前
assert has_permission(admin_user, [Permission.PROJECT_CREATE])

# 修改后
assert check_user_permission(admin_user, [Permission.PROJECT_CREATE])
```

### 2. check_permission() 装饰器需要改为 require_permissions()

**查找**: `@check_permission(`
**替换为**: `@require_permissions(`

**示例**:
```python
# 修改前
@check_permission(Permission.PROJECT_CREATE)
def create_project():
    pass

# 修改后
@require_permissions(Permission.PROJECT_CREATE)
def create_project():
    pass
```

### 3. require_permission() 需要改为 require_permissions()

**查找**: `require_permission(`
**替换为**: `require_permissions(`

**注意**: 是复数形式 permissions，不是 permission

## 快速修复方法

### 方法1: 手动编辑（推荐）
1. 打开 `backend/tests/core/test_permissions.py`
2. 修改导入语句（第7-13行）
3. 全局搜索替换：
   - `has_permission(` → `check_user_permission(`
   - `@check_permission(` → `@require_permissions(`
   - `require_permission(` → `require_permissions(`

### 方法2: 使用编辑器批量替换
在VS Code中:
1. Ctrl+H 打开查找替换
2. 依次替换：
   - 查找: `has_permission\(`，替换为: `check_user_permission(`
   - 查找: `@check_permission\(`，替换为: `@require_permissions(`
   - 查找: `require_permission\(`，替换为: `require_permissions(`

## 函数签名对照表

| 测试中使用的名称 | 实际函数名称 | 用途 |
|-----------------|-------------|------|
| `has_permission` | `check_user_permission` | 检查用户是否拥有指定权限 |
| `check_permission` | `require_permissions` | 装饰器：要求用户拥有指定权限 |
| `require_permission` | `require_permissions` | 装饰器：要求用户拥有指定权限（注意复数） |
| - | `check_role_permission` | 检查用户角色是否匹配 |
| - | `get_user_permissions` | 获取用户的所有权限列表 |

## 函数签名说明

### get_user_permissions(user: AuthenticatedUser) -> List[Permission]
获取用户的所有权限列表
```python
permissions = get_user_permissions(admin_user)
# 返回: [Permission.PROJECT_CREATE, Permission.PROJECT_READ, ...]
```

### check_user_permission(user: AuthenticatedUser, required_permissions: Iterable[Union[str, Permission]]) -> bool
检查用户是否拥有所需的全部权限
```python
has_perm = check_user_permission(user, [Permission.PROJECT_CREATE, Permission.PROJECT_READ])
# 返回: True/False
```

### check_role_permission(user: AuthenticatedUser, required_roles: Iterable[str]) -> bool
检查用户角色是否在指定角色列表中
```python
is_admin = check_role_permission(user, ["admin", "account_manager"])
# 返回: True/False
```

### require_permissions(*permissions: Union[str, Permission])
FastAPI依赖注入装饰器，要求用户拥有所有指定权限
```python
@router.post("/projects")
@require_permissions(Permission.PROJECT_CREATE)
async def create_project(...):
    pass
```

## 验证修复

修复后运行测试验证：
```powershell
cd d:\git\1108\backend
python -m pytest tests/core/test_permissions.py -v --tb=short
```

如果所有测试通过，表示修复成功！

## 其他可能需要修复的文件

如果其他测试文件也使用了这些函数，需要同样的修复：
- 搜索所有 `.py` 文件中的 `has_permission(`
- 搜索所有 `.py` 文件中的 `check_permission(`
- 搜索所有 `.py` 文件中的 `require_permission(`

```powershell
# 在backend目录下搜索
cd d:\git\1108\backend
Get-ChildItem -Recurse -Filter "*.py" | Select-String "has_permission\(|check_permission\(|require_permission\("
```
