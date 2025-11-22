# 错误码规范文档

> ⚠️ **文档状态**: 已废弃 (DEPRECATED)
> **废弃日期**: 2025-11-20
> **替代文档**: 请使用 [`docs/core/ERROR_CODES.md`](./core/ERROR_CODES.md) (v2.0) 作为权威 SoT
> **代码实现**: [`backend/core/error_codes.py`](../backend/core/error_codes.py)
>
> 本文档保留仅供历史参考。所有错误码定义以 `docs/core/ERROR_CODES.md` 为准。

---

> **版本**: v2.0 (P2.5) - DEPRECATED
> **更新日期**: 2025-11-20
> **适用范围**: AI广告代投系统后端API

---

## 📋 概述

本文档定义了系统所有API响应中使用的**字符串业务错误码**（Business Error Codes）。

### 核心原则

1. **code 字段为字符串**: 所有业务码均为字符串类型，不使用数字
2. **语义化命名**: 错误码名称直观反映错误类型
3. **HTTP 状态码分离**: HTTP 状态码仅在响应头中，不在 JSON body 中
4. **无 error_code 字段**: 已废弃，统一使用 code 字段

---

## 🎯 响应格式规范

### 成功响应

```json
{
  "success": true,
  "message": "操作成功",
  "code": "OK",
  "data": {...},
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2025-11-20T10:00:00Z"
}
```

### 错误响应

```json
{
  "success": false,
  "message": "未提供认证令牌",
  "code": "AUTH_400",
  "data": null,
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2025-11-20T10:00:00Z"
}
```

**注意**: `error_code` 字段已在 P2.5 版本中删除。

---

## 📊 业务错误码列表

### 1. 成功类 (2xx)

| 业务码 | HTTP Status | 说明 | 使用场景 |
|--------|------------|------|---------|
| `OK` | 200 | 通用成功 | 所有成功操作的默认值 |

**示例**:
```python
return success_response(
    data={"user_id": "123"},
    message="查询成功"
)
# code 默认为 "OK"
```

---

### 2. 认证类 (AUTH_xxx)

#### 2.1 未授权 (401)

| 业务码 | HTTP Status | 说明 | 触发条件 |
|--------|------------|------|---------|
| `AUTH_400` | 401 | 未提供认证令牌 | 缺少 Authorization header |
| `AUTH_401` | 401 | 认证令牌无效 | Token 验证失败或已过期 |
| `AUTH_004` | 401 | 用户不存在 | Token 有效但数据库无此用户 |

**示例**:
```python
# dependencies.py - get_current_user()
raise HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail={
        "success": False,
        "message": "未提供认证令牌",
        "code": "AUTH_400",
        "request_id": request_id
    }
)
```

#### 2.2 权限不足 (403)

| 业务码 | HTTP Status | 说明 | 触发条件 |
|--------|------------|------|---------|
| `AUTH_002` | 403 | 账户已禁用 | is_active = false |
| `AUTH_403` | 403 | 权限不足 | 通用权限错误 |
| `AUTH_500` | 403 | 角色权限不足 | 用户角色不在允许列表中 |

**示例**:
```python
# dependencies.py - require_role()
raise HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail={
        "success": False,
        "message": f"权限不足，需要以下角色之一: {', '.join(allowed_roles)}",
        "code": "AUTH_500",
        "request_id": request_id
    }
)
```

---

### 3. 资源类 (4xx)

#### 3.1 资源未找到 (404)

| 业务码 | HTTP Status | 说明 | 使用场景 |
|--------|------------|------|---------|
| `RESOURCE_NOT_FOUND` | 404 | 通用资源未找到 | 未指定具体资源类型 |
| `USER_NOT_FOUND` | 404 | 用户不存在 | 查询用户失败 |
| `ROLE_NOT_FOUND` | 404 | 角色不存在 | admin_roles.py 删除角色失败 |
| `PROJECT_NOT_FOUND` | 404 | 项目不存在 | 项目相关操作 |
| `ACCOUNT_NOT_FOUND` | 404 | 广告账户不存在 | 账户相关操作 |

**示例**:
```python
# routers/admin_roles.py
return error_response(
    message="未找到角色记录",
    code="ROLE_NOT_FOUND"
)
```

#### 3.2 数据验证 (422)

| 业务码 | HTTP Status | 说明 | 触发条件 |
|--------|------------|------|---------|
| `VALIDATION_ERROR` | 422 | 数据验证失败 | Pydantic 模型验证错误 |

**示例**:
```python
return validation_error_response(
    errors={"field": "error message"}
)
```

---

### 4. 系统类 (5xx)

| 业务码 | HTTP Status | 说明 | 触发条件 |
|--------|------------|------|---------|
| `SYS_001` | 500 | 系统内部错误 | 未预期的异常 |
| `SERVICE_UNHEALTHY` | 503 | 服务不健康 | /health 检查失败 |
| `UNKNOWN_ERROR` | (动态) | 未知错误 | 向后兼容的默认值 |

**示例**:
```python
# main.py - general_exception_handler
return create_api_response(
    success=False,
    message="服务器内部错误",
    code="SYS_001",
    http_status_code=500
)
```

---

## 🔧 使用指南

### 后端开发者

#### 1. 返回成功响应

```python
from app.utils.response import success_response

# 默认使用 code="OK"
return success_response(
    data={"items": []},
    message="查询成功"
)
```

#### 2. 返回错误响应

```python
from app.utils.response import error_response

# 使用字符串业务码
return error_response(
    message="资源不存在",
    code="RESOURCE_NOT_FOUND"
)
```

#### 3. 使用专用错误函数

```python
from app.utils.response import (
    validation_error_response,    # code="VALIDATION_ERROR"
    not_found_response,           # code="RESOURCE_NOT_FOUND"
    unauthorized_response,        # code="AUTH_401"
    forbidden_response,           # code="AUTH_403"
    server_error_response         # code="SYS_001"
)

# 示例
return not_found_response(resource="用户")
# 返回: {"code": "RESOURCE_NOT_FOUND", "message": "用户不存在", ...}
```

#### 4. 抛出 HTTPException

```python
from fastapi import HTTPException, status
import uuid

raise HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail={
        "success": False,
        "message": "项目不存在",
        "code": "PROJECT_NOT_FOUND",
        "request_id": str(uuid.uuid4())
    }
)
```

---

### 前端开发者

#### 1. 判断成功/失败

```javascript
// 使用 success 字段
if (response.success) {
  // 成功处理
} else {
  // 错误处理
}
```

#### 2. 根据业务码处理

```javascript
switch (response.code) {
  case "OK":
    // 成功
    break;
  case "AUTH_401":
    // 跳转登录
    router.push('/login');
    break;
  case "AUTH_500":
    // 权限不足提示
    showError("您没有权限执行此操作");
    break;
  case "RESOURCE_NOT_FOUND":
    // 资源不存在
    showError("请求的资源不存在");
    break;
  default:
    // 通用错误处理
    showError(response.message);
}
```

#### 3. 不要使用 error_code

```javascript
// ❌ 错误 - error_code 字段已删除
if (response.error_code === "AUTH_401") { ... }

// ✅ 正确 - 使用 code 字段
if (response.code === "AUTH_401") { ... }
```

---

## 📚 扩展指南

### 添加新的业务错误码

1. **命名规范**:
   - 认证相关: `AUTH_xxx`
   - 资源相关: `<RESOURCE>_NOT_FOUND`
   - 验证相关: `VALIDATION_xxx`
   - 系统相关: `SYS_xxx`

2. **在代码中定义**:
   ```python
   # app/utils/response.py 或业务模块
   return error_response(
       message="余额不足",
       code="BALANCE_INSUFFICIENT"
   )
   ```

3. **更新本文档**: 在对应分类中添加新错误码说明

---

## 📜 历史变更

### v2.0 (P2.5 - 2025-11-20)

**重大变更**:
- ✅ code 字段从 `int` 改为 `str`
- ✅ 删除 error_code 字段
- ✅ 新增业务错误码规范
- ✅ HTTP 状态码与业务码分离

**迁移指南**: 见 `P2.5_CHANGELOG.md`

### v1.0 (P2.3/P2.4 - 2025-11-19)

- 引入 request_id 字段
- 引入可选的 error_code 字段

---

## ⚠️ 注意事项

1. **禁止硬编码数字**:
   ```python
   # ❌ 错误
   if response["code"] == 200:

   # ✅ 正确
   if response["code"] == "OK":
   ```

2. **HTTP 状态码用途**:
   - 仅用于 HTTP 协议层面
   - 不应作为业务逻辑判断依据
   - 前端应优先使用 `code` 字段

3. **向后兼容**:
   - 旧系统可能仍使用 error_code，需渐进迁移
   - 新代码禁止使用 error_code

---

## 📞 技术支持

如有疑问或需要添加新的业务错误码，请参考:
- `docs/P2.5_CHANGELOG.md` - P2.5 变更详情
- `docs/P2.5_ERROR_CODE_UNIFICATION_PLAN.md` - 执行计划
- `backend/app/utils/response.py` - 响应工具函数源码

---

**文档维护者**: 开发团队
**最后更新**: 2025-11-20
