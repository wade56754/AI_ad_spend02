# CEO 仪表盘访问权限问题修复

## 问题描述

用户以"管理员"角色登录后，访问 CEO 仪表盘时出现错误：
- **错误信息**: "CEO 驾驶舱仅限老板和管理员访问"
- **用户显示**: "Anthony" - "管理员"

## 问题分析

### 1. 权限检查逻辑

`require_ceo_access` 函数使用 `role_in_list` 检查用户角色是否在允许列表中：
- 允许的角色：`["admin", "ceo"]`
- 使用 `role_in_list` 函数支持等价角色检查

### 2. 可能的原因

1. **角色值不规范**：数据库中用户的角色值可能包含空格或大小写不一致
2. **角色值不匹配**：数据库中用户的角色值可能不是 "admin" 或 "ceo"
3. **日志级别过低**：原日志使用 `logger.debug()`，可能没有记录到实际的检查过程

### 3. 角色映射关系

根据 `backend/core/role_mapping.py`：
- `{"ceo", "admin"}` 是等价角色组
- `role_in_list` 函数会检查等价角色关系
- `is_role_equivalent` 函数会处理大小写和空格

## 修复方案

### 修改文件
- `backend/routers/dashboard.py` - `require_ceo_access` 函数

### 修复内容

1. **角色值规范化**：
   ```python
   # 规范化角色值（去除空格，转小写）
   if user_role:
       user_role = user_role.strip().lower()
   ```

2. **增强日志记录**：
   - 将日志级别从 `debug` 改为 `info`，确保能够记录到实际的检查过程
   - 添加更详细的日志信息，包括：
     - 用户 ID
     - 用户 Email
     - 规范化后的角色值
     - 原始角色值（用于调试）
     - 允许的角色列表

3. **添加成功日志**：
   - 当用户成功访问时，记录日志以便追踪

### 修复后的代码

```python
def require_ceo_access(current_user: User = Depends(get_current_user)) -> User:
    """
    CEO 驾驶舱权限检查

    仅允许以下角色访问：
    - admin
    - ceo (映射到 admin)

    使用 role_in_list 支持等价角色
    """
    allowed_roles = ["admin", "ceo"]
    
    # 获取用户角色（可能为 None）
    user_role = current_user.role if current_user.role else None
    
    # 规范化角色值（去除空格，转小写）
    if user_role:
        user_role = user_role.strip().lower()
    
    # 详细日志：记录实际角色值和检查过程
    logger.info(
        f"CEO dashboard access check: user_id={current_user.id}, "
        f"email={current_user.email}, "
        f"user_role={user_role} (raw={current_user.role}), "
        f"allowed_roles={allowed_roles}"
    )

    # 检查角色是否在允许列表中
    if not role_in_list(user_role, allowed_roles):
        logger.warning(
            f"User {current_user.id} (email={current_user.email}, role={user_role}) "
            f"denied access to CEO dashboard. Allowed roles: {allowed_roles}"
        )
        raise PermissionDeniedError(
            message="CEO 驾驶舱仅限老板和管理员访问"
        )
    
    logger.info(
        f"User {current_user.id} (role={user_role}) granted access to CEO dashboard"
    )

    return current_user
```

## 验证步骤

1. **检查后端日志**：
   - 查看 `CEO dashboard access check` 日志，确认用户的实际角色值
   - 查看 `denied access` 或 `granted access` 日志，确认权限检查结果

2. **检查数据库**：
   - 确认用户表中的角色值是否正确（应该是 "admin" 或 "ceo"）
   - 确认角色值没有额外的空格或大小写问题

3. **测试访问**：
   - 使用管理员账号登录
   - 访问 CEO 仪表盘
   - 确认能够正常访问

## 后续建议

1. **统一角色值**：确保数据库中所有用户的角色值都是规范化的（小写，无空格）
2. **添加数据验证**：在用户创建/更新时，验证角色值是否符合规范
3. **监控日志**：定期检查权限拒绝日志，及时发现权限配置问题

## 相关文件

- `backend/routers/dashboard.py` - CEO 仪表盘路由和权限检查
- `backend/core/role_mapping.py` - 角色映射和等价角色检查
- `backend/core/dependencies.py` - 用户认证和角色提取
- `backend/services/local_auth_service.py` - JWT token 验证和用户信息提取

## 更新日期

2026-01-12

