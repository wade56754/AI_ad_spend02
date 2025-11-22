# 错误码同步校准报告

**生成时间**: 2025-01-19
**报告版本**: v1.0
**基准文档**: `docs/ERROR_CODES.md`
**基准代码**: `backend/core/error_codes.py`

---

## 📊 执行摘要

本报告对比了文档 `ERROR_CODES.md`、代码 `error_codes.py` 和实际业务代码（services/* 和 routers/*）中的错误码使用情况，发现以下关键问题：

| 问题类型 | 数量 | 严重程度 |
|---------|------|---------|
| 代码中使用但未定义的错误码 | 58+ | 🔴 P0 严重 |
| 异常类默认错误码冲突 | 10 | 🔴 P0 严重 |
| HTTP状态码映射错误码未定义 | 11 | 🟡 P1 高 |
| 文档与代码不一致 | 0 | ✅ 正常 |

---

## 1️⃣ 代码中使用但未在 error_codes.py 中定义的错误码

### 1.1 认证相关（AUTH_*）

| 错误码 | 使用位置 | HTTP | 建议操作 |
|-------|---------|------|---------|
| `AUTH_LOGOUT_ALL_ERROR` | `routers/authentication.py:249` | 500 | 新增或使用 `AUTH_901` |
| `AUTH_RESET_PASSWORD_ERROR` | `routers/authentication.py:378` | 500 | 新增 `AUTH_207` |
| `AUTH_VERIFY_EMAIL_FAILED` | `routers/authentication.py:401` | 400 | 使用 `AUTH_301` |
| `AUTH_VERIFY_EMAIL_ERROR` | `routers/authentication.py:408` | 500 | 使用 `AUTH_301` |
| `AUTH_ALREADY_VERIFIED` | `routers/authentication.py:431` | 400 | 使用 `AUTH_302` |
| `AUTH_RESEND_VERIFICATION_ERROR` | `routers/authentication.py:438` | 500 | 新增 `AUTH_303` |
| `REGISTER_FAILED` | `routers/supabase_auth.py:119` | 500 | 使用 `AUTH_102` |
| `LOGIN_FAILED` | `routers/supabase_auth.py:166` | 500 | 使用 `AUTH_900` |
| `LOGOUT_FAILED` | `routers/supabase_auth.py:199` | 500 | 使用 `AUTH_901` |
| `REFRESH_FAILED` | `routers/supabase_auth.py:228` | 401 | 使用 `AUTH_005` |
| `UPDATE_PASSWORD_FAILED` | `routers/supabase_auth.py:295` | 500 | 使用 `AUTH_206` |
| `VERIFY_EMAIL_FAILED` | `routers/supabase_auth.py:324` | 400 | 使用 `AUTH_301` |
| `UPDATE_PROFILE_FAILED` | `routers/supabase_auth.py:440` | 500 | 新增 `AUTH_903` |
| `GET_SESSIONS_FAILED` | `routers/supabase_auth.py:470` | 500 | 新增 `AUTH_904` |
| `REVOKE_SESSION_FAILED` | `routers/supabase_auth.py:498` | 500 | 新增 `AUTH_905` |
| `REVOKE_SESSIONS_FAILED` | `routers/supabase_auth.py:531` | 500 | 新增 `AUTH_906` |
| `ACTIVATE_USER_FAILED` | `routers/supabase_auth.py:575` | 500 | 新增 `AUTH_907` |
| `DEACTIVATE_USER_FAILED` | `routers/supabase_auth.py:618` | 500 | 新增 `AUTH_908` |

### 1.2 业务逻辑相关（BIZ_*）

| 错误码 | 使用位置 | HTTP | 建议操作 |
|-------|---------|------|---------|
| `BIZ_202` | `services/topup_service.py:722` | 400 | 新增：金额格式无效 |
| `BIZ_203` | `services/topup_service.py:214,257,302` | 400 | 新增：状态不符合操作要求 |
| `BIZ_204` | `services/topup_service.py:744` | 400 | 新增：操作时间限制 |
| `BIZ_206` | `services/topup_service.py:702,785,798,801` | 403 | 新增：无权限访问资源 |
| `BIZ_207` | `services/topup_service.py:307` | 409 | 新增：重复操作冲突 |
| `BIZ_301` | `services/reconciliation_service_optimized.py:57` | 400 | ✅ 已定义（状态转换不允许） |
| `BIZ_303` | `services/reconciliation_service.py:149` | 403 | 新增：无权限访问对账批次 |
| `BIZ_306` | `services/reconciliation_service.py:162,298` | 400 | 新增：对账批次状态错误 |
| `BIZ_401` | `services/ad_account_service.py:63` | 400 | 新增：项目不存在 |
| `BIZ_402` | `services/ad_account_service.py:68` | 400 | 新增：渠道不存在 |
| `BIZ_403` | `services/ad_account_service.py:75,190,195` | 400/403 | 新增：平台账户ID冲突/无权限 |
| `BIZ_405` | `services/ad_account_service.py:640` | 400 | 新增：账户状态不允许删除 |
| `BIZ_INVALID_FILE_TYPE` | `routers/daily_reports.py:685` | 400 | 新增 `BIZ_401` |
| `BIZ_FILE_TOO_LARGE` | `routers/daily_reports.py:699` | 400 | 新增 `BIZ_402` |
| `BIZ_EXCEL_PARSE_ERROR` | `routers/daily_reports.py:712` | 400 | 新增 `BIZ_403` |
| `BIZ_EMPTY_FILE` | `routers/daily_reports.py:720` | 400 | 新增 `BIZ_404` |
| `BIZ_MISSING_COLUMNS` | `routers/daily_reports.py:732` | 400 | 新增 `BIZ_405` |
| `BIZ_EXPORT_LIMIT_EXCEEDED` | `routers/daily_reports.py:856` | 400 | 新增 `BIZ_406` |
| `BIZ_NO_DATA` | `routers/daily_reports.py:872` | 404 | 使用 `BIZ_002` |
| `BIZ_ERROR` | `custom_exceptions.py:30` + `routers/topup.py` | 400 | 删除，使用具体错误码 |

### 1.3 系统错误相关（SYS_*）

| 错误码 | 使用位置 | HTTP | 建议操作 |
|-------|---------|------|---------|
| `SYS_500` | `routers/projects.py:99,467` 等多处 | 500 | 使用 `SYS_001` |
| `SYS_005` | `custom_exceptions.py:51` | 409 | 删除，使用 `BIZ_003` |
| `SYS_429` | `custom_exceptions.py:79` | 429 | 删除，使用 `SYS_004` |
| `SYS_503` | `custom_exceptions.py:86` | 503 | 删除，使用 `SYS_002` |
| `SYS_CONFIG` | `custom_exceptions.py:93` | 500 | 新增 `SYS_005` |

### 1.4 数据验证相关（VALIDATION_*）

| 错误码 | 使用位置 | HTTP | 建议操作 |
|-------|---------|------|---------|
| `VALIDATION_ERROR` | `handlers.py:62,202` + routers 多处 | 422 | 使用 `VALIDATION_001` |
| `MISSING_REQUIRED_COLUMN` | `routers/daily_reports.py:106` | 400 | 使用 `VALIDATION_001` |
| `EMPTY_REQUIRED_FIELD` | `routers/daily_reports.py:123` | 400 | 使用 `VALIDATION_001` |
| `VALUE_OUT_OF_RANGE` | `routers/daily_reports.py:154,163,178` | 400 | 使用 `VALIDATION_005` |
| `STRING_TOO_LONG` | `routers/daily_reports.py:193` | 400 | 新增 `VALIDATION_007` |
| `TYPE_CONVERSION_ERROR` | `routers/daily_reports.py:208` | 400 | 新增 `VALIDATION_008` |

### 1.5 数据库相关（DB_*）

| 错误码 | 使用位置 | HTTP | 建议操作 |
|-------|---------|------|---------|
| `DATABASE_ERROR` | `handlers.py:278` | 500 | 使用 `DB_002` |
| `INTEGRITY_ERROR` | `handlers.py:270` | 400 | 使用 `DB_003` |

### 1.6 其他未分类错误码

| 错误码 | 使用位置 | HTTP | 建议操作 |
|-------|---------|------|---------|
| `SUCCESS` | `response.py:26,127` | 200 | 保留为特殊成功标识 |
| `INTERNAL_ERROR` | `response.py:51,154` | 400/500 | 使用 `SYS_001` |
| `SEC_ERROR` | `custom_exceptions.py:72` | 403 | 新增 `SEC_001` 或使用 `AUTH_500` |
| `IMPORT_ERROR` | `services/daily_report_service.py:480` | 500 | 新增 `BIZ_500` |
| `PARSE_ERROR` | `routers/daily_reports.py:231` | 400 | 新增 `BIZ_501` |
| `LEDGER_CREATE_ERROR` | `routers/ledger.py:142` | 500 | 新增 `BIZ_510` |
| `LEDGER_QUERY_ERROR` | `routers/ledger.py:181` | 500 | 新增 `BIZ_511` |
| `TRANSACTION_NOT_FOUND` | `routers/ledger.py:208` | 404 | 使用 `BIZ_002` |
| `LEDGER_UPDATE_ERROR` | `routers/ledger.py:220` | 500 | 新增 `BIZ_512` |
| `BALANCE_QUERY_ERROR` | `routers/ledger.py:250` | 500 | 新增 `BIZ_513` |
| `BUDGET_QUERY_ERROR` | `routers/ledger.py:276` | 500 | 新增 `BIZ_514` |
| `BUDGET_CREATE_ERROR` | `routers/ledger.py:319` | 500 | 新增 `BIZ_515` |
| `STATISTICS_QUERY_ERROR` | `routers/ledger.py:350` | 500 | 新增 `BIZ_516` |
| `EXPORT_ERROR` | `routers/ledger.py:416` | 500 | 新增 `BIZ_517` |
| `NOT_FOUND` | `routers/reconciliation_extended.py:292,328` | 404 | 使用 `BIZ_002` |
| `AUTHENTICATION_ERROR` | `handlers.py:73` | 401 | 使用 `AUTH_999` |
| `AUTHORIZATION_ERROR` | `handlers.py:83` | 403 | 使用 `AUTH_500` |
| `RESOURCE_NOT_FOUND` | `handlers.py:93` | 404 | 使用 `BIZ_002` |
| `RESOURCE_CONFLICT` | `handlers.py:103` | 409 | 使用 `BIZ_003` |
| `BUSINESS_RULE_ERROR` | `handlers.py:113` | 400 | 使用 `BIZ_001` |
| `EXTERNAL_SERVICE_ERROR` | `handlers.py:123` | 502 | 使用 `SYS_002` |
| `RATE_LIMIT_EXCEEDED` | `handlers.py:134` | 429 | 使用 `SYS_004` |
| `BAD_REQUEST` | `handlers.py:214` | 400 | 使用 `VALIDATION_001` |
| `UNAUTHORIZED` | `handlers.py:215` | 401 | 使用 `AUTH_999` |
| `FORBIDDEN` | `handlers.py:216` | 403 | 使用 `AUTH_500` |
| `METHOD_NOT_ALLOWED` | `handlers.py:218` | 405 | 新增 `SYS_006` |
| `TOO_MANY_REQUESTS` | `handlers.py:219` | 429 | 使用 `SYS_004` |
| `INTERNAL_SERVER_ERROR` | `handlers.py:220,307` | 500 | 使用 `SYS_001` |
| `BAD_GATEWAY` | `handlers.py:221` | 502 | 新增 `SYS_007` |
| `SERVICE_UNAVAILABLE` | `handlers.py:222` | 503 | 使用 `SYS_002` |
| `HTTP_ERROR` | `handlers.py:225` | - | 使用 `SYS_001` |

---

## 2️⃣ 异常类默认错误码冲突问题

### 2.1 custom_exceptions.py 中的冲突

| 异常类 | 当前默认错误码 | 问题描述 | 建议修正 |
|-------|--------------|---------|---------|
| `BusinessLogicError` | `BIZ_ERROR` | 未定义的错误码 | 改为 `BIZ_001` |
| `ResourceNotFoundError` | `SYS_004` | `SYS_004` 定义为"请求过于频繁"，语义冲突 | 改为 `BIZ_002` |
| `PermissionDeniedError` | `SYS_003` | `SYS_003` 定义为"请求超时"，语义冲突 | 改为 `AUTH_500` |
| `ResourceConflictError` | `SYS_005` | 未定义的错误码 | 改为 `BIZ_003` |
| `ValidationError` | `SYS_001` | `SYS_001` 定义为"系统内部错误"，不适合验证错误 | 改为 `VALIDATION_001` |
| `AuthenticationError` | `SYS_002` | `SYS_002` 定义为"服务暂时不可用"，语义冲突 | 改为 `AUTH_999` |
| `SecurityError` | `SEC_ERROR` | 未定义的错误码 | 改为 `AUTH_500` 或新增 `SEC_001` |
| `RateLimitError` | `SYS_429` | 未定义的错误码 | 改为 `SYS_004` |
| `ExternalServiceError` | `SYS_503` | 未定义的错误码 | 改为 `SYS_002` |
| `ConfigurationError` | `SYS_CONFIG` | 未定义的错误码 | 新增 `SYS_005` |

### 2.2 handlers.py 中的异常类（未使用 error_codes.py）

| 异常类 | 当前错误码 | HTTP | 建议映射 |
|-------|-----------|------|---------|
| `ValidationException` | `VALIDATION_ERROR` | 422 | `VALIDATION_001` |
| `AuthenticationException` | `AUTHENTICATION_ERROR` | 401 | `AUTH_999` |
| `AuthorizationException` | `AUTHORIZATION_ERROR` | 403 | `AUTH_500` |
| `ResourceNotFoundException` | `RESOURCE_NOT_FOUND` | 404 | `BIZ_002` |
| `ConflictException` | `RESOURCE_CONFLICT` | 409 | `BIZ_003` |
| `BusinessRuleException` | `BUSINESS_RULE_ERROR` | 400 | `BIZ_001` |
| `ExternalServiceException` | `EXTERNAL_SERVICE_ERROR` | 502 | `SYS_002` |
| `RateLimitException` | `RATE_LIMIT_EXCEEDED` | 429 | `SYS_004` |

---

## 3️⃣ 错误码 → HTTP 状态码映射冲突

### 3.1 SYS_004 的语义冲突

**文档定义**: `SYS_004` = "请求过于频繁" (HTTP 429)
**实际使用**:
- `routers/projects.py:161,197,234,313` 等多处用于 404 错误
- `custom_exceptions.py:37` 作为 `ResourceNotFoundError` 的默认错误码

**冲突点**: 同一个错误码同时用于 429 和 404，语义混乱

**解决方案**:
1. 保持 `SYS_004` = "请求过于频繁" (429)
2. 所有 404 场景改用 `BIZ_002`（资源不存在）
3. 修正 `ResourceNotFoundError` 默认错误码为 `BIZ_002`

### 3.2 其他HTTP映射冲突

| 错误码 | 定义HTTP | 实际使用HTTP | 冲突位置 |
|-------|---------|------------|---------|
| `BIZ_403` | - | 400/403 | `services/ad_account_service.py` |

---

## 4️⃣ 文档中存在但代码未使用的错误码

**检查结果**: ✅ 无

所有在 `ERROR_CODES.md` 和 `error_codes.py` 中定义的 48 个错误码均可正常使用，无需删除。

---

## 5️⃣ 建议的最终错误码列表

### 5.1 新增错误码（需添加到 error_codes.py）

#### 认证类（AUTH_）

```python
# 密码相关（200-299）
PASSWORD_RESET_FAILED = ErrorCode("AUTH_207", "密码重置失败", 500)

# 邮箱验证（300-399）
EMAIL_RESEND_FAILED = ErrorCode("AUTH_303", "重新发送验证邮件失败", 500)

# 通用认证错误（900-999）
PROFILE_UPDATE_FAILED = ErrorCode("AUTH_903", "用户信息更新失败", 500)
SESSION_QUERY_FAILED = ErrorCode("AUTH_904", "会话查询失败", 500)
SESSION_REVOKE_FAILED = ErrorCode("AUTH_905", "会话撤销失败", 500)
ALL_SESSIONS_REVOKE_FAILED = ErrorCode("AUTH_906", "批量撤销会话失败", 500)
USER_ACTIVATE_FAILED = ErrorCode("AUTH_907", "用户激活失败", 500)
USER_DEACTIVATE_FAILED = ErrorCode("AUTH_908", "用户停用失败", 500)
```

#### 业务逻辑类（BIZ_）

```python
# 金额相关（100-199）
INVALID_AMOUNT_FORMAT = ErrorCode("BIZ_102", "金额格式无效", 400)

# 状态相关（300-399）
BATCH_ACCESS_DENIED = ErrorCode("BIZ_303", "无权限访问对账批次", 403)
BATCH_STATUS_ERROR = ErrorCode("BIZ_306", "对账批次状态不允许操作", 400)

# 资源访问相关（400-499）
PROJECT_NOT_FOUND = ErrorCode("BIZ_401", "项目不存在", 404)
CHANNEL_NOT_FOUND = ErrorCode("BIZ_402", "渠道不存在", 404)
PLATFORM_ACCOUNT_CONFLICT = ErrorCode("BIZ_403", "平台账户ID已存在", 409)
ACCOUNT_STATUS_DELETE_ERROR = ErrorCode("BIZ_405", "只有归档状态的账户才能删除", 400)
RESOURCE_ACCESS_DENIED = ErrorCode("BIZ_406", "无权限访问该资源", 403)
DUPLICATE_OPERATION = ErrorCode("BIZ_407", "重复操作冲突", 409)

# 文件处理相关（500-599）
IMPORT_ERROR = ErrorCode("BIZ_500", "数据导入失败", 500)
PARSE_ERROR = ErrorCode("BIZ_501", "文件解析失败", 400)
INVALID_FILE_TYPE = ErrorCode("BIZ_502", "文件类型不支持", 400)
FILE_TOO_LARGE = ErrorCode("BIZ_503", "文件大小超过限制", 400)
EXCEL_PARSE_ERROR = ErrorCode("BIZ_504", "Excel文件解析失败", 400)
EMPTY_FILE = ErrorCode("BIZ_505", "文件内容为空", 400)
MISSING_COLUMNS = ErrorCode("BIZ_506", "缺少必需的列", 400)
EXPORT_LIMIT_EXCEEDED = ErrorCode("BIZ_507", "导出数据量超过限制", 400)

# 账本相关（510-529）
LEDGER_CREATE_ERROR = ErrorCode("BIZ_510", "账本记录创建失败", 500)
LEDGER_QUERY_ERROR = ErrorCode("BIZ_511", "账本查询失败", 500)
LEDGER_UPDATE_ERROR = ErrorCode("BIZ_512", "账本更新失败", 500)
BALANCE_QUERY_ERROR = ErrorCode("BIZ_513", "余额查询失败", 500)
BUDGET_QUERY_ERROR = ErrorCode("BIZ_514", "预算查询失败", 500)
BUDGET_CREATE_ERROR = ErrorCode("BIZ_515", "预算创建失败", 500)
STATISTICS_QUERY_ERROR = ErrorCode("BIZ_516", "统计查询失败", 500)
EXPORT_ERROR = ErrorCode("BIZ_517", "数据导出失败", 500)
```

#### 系统错误类（SYS_）

```python
CONFIGURATION_ERROR = ErrorCode("SYS_005", "系统配置错误", 500)
METHOD_NOT_ALLOWED = ErrorCode("SYS_006", "请求方法不允许", 405)
BAD_GATEWAY = ErrorCode("SYS_007", "网关错误", 502)
```

#### 验证错误类（VALIDATION_）

```python
STRING_TOO_LONG = ErrorCode("VALIDATION_007", "字符串长度超过限制", 400)
TYPE_CONVERSION_ERROR = ErrorCode("VALIDATION_008", "数据类型转换失败", 400)
```

### 5.2 需删除的错误码

以下错误码为临时/非标准错误码，应从代码中移除：

- `BIZ_ERROR` → 替换为具体的 BIZ_xxx 错误码
- `SYS_005`（custom_exceptions.py中） → 使用新增的 `SYS_005`
- `SYS_429` → 替换为 `SYS_004`
- `SYS_503` → 替换为 `SYS_002`
- `SEC_ERROR` → 替换为 `AUTH_500` 或新增 `SEC_001`
- `SYS_500` → 替换为 `SYS_001`
- `INTERNAL_ERROR` → 替换为 `SYS_001`

---

## 6️⃣ 异常类默认 error_code 调整方案

### 6.1 修改 custom_exceptions.py

```python
class BusinessLogicError(BaseCustomException):
    """业务逻辑错误"""
    def __init__(self, message: str, error_code: str = "BIZ_001", details: Optional[Any] = None):
        super().__init__(message, error_code, 400, details)


class ResourceNotFoundError(BaseCustomException):
    """资源不存在错误"""
    def __init__(self, message: str, error_code: str = "BIZ_002", details: Optional[Any] = None):
        super().__init__(message, error_code, 404, details)


class PermissionDeniedError(BaseCustomException):
    """权限不足错误"""
    def __init__(self, message: str, error_code: str = "AUTH_500", details: Optional[Any] = None):
        super().__init__(message, error_code, 403, details)


class ResourceConflictError(BaseCustomException):
    """资源冲突错误"""
    def __init__(self, message: str, error_code: str = "BIZ_003", details: Optional[Any] = None):
        super().__init__(message, error_code, 409, details)


class ValidationError(BaseCustomException):
    """数据验证错误"""
    def __init__(self, message: str, error_code: str = "VALIDATION_001", details: Optional[Any] = None):
        super().__init__(message, error_code, 422, details)


class AuthenticationError(BaseCustomException):
    """认证错误"""
    def __init__(self, message: str, error_code: str = "AUTH_999", details: Optional[Any] = None):
        super().__init__(message, error_code, 401, details)


class SecurityError(BaseCustomException):
    """安全错误"""
    def __init__(self, message: str, error_code: str = "AUTH_500", details: Optional[Any] = None):
        super().__init__(message, error_code, 403, details)


class RateLimitError(BaseCustomException):
    """限流错误"""
    def __init__(self, message: str, error_code: str = "SYS_004", details: Optional[Any] = None):
        super().__init__(message, error_code, 429, details)


class ExternalServiceError(BaseCustomException):
    """外部服务错误"""
    def __init__(self, message: str, error_code: str = "SYS_002", details: Optional[Any] = None):
        super().__init__(message, error_code, 503, details)


class ConfigurationError(BaseCustomException):
    """配置错误"""
    def __init__(self, message: str, error_code: str = "SYS_005", details: Optional[Any] = None):
        super().__init__(message, error_code, 500, details)
```

### 6.2 修改 handlers.py 异常类

```python
class ValidationException(AppException):
    """验证异常"""
    def __init__(self, message: str = "参数验证失败", details: dict = None):
        super().__init__(
            code="VALIDATION_001",  # 改为 VALIDATION_001
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details
        )


class AuthenticationException(AppException):
    """认证异常"""
    def __init__(self, message: str = "认证失败"):
        super().__init__(
            code="AUTH_999",  # 改为 AUTH_999
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED
        )


class AuthorizationException(AppException):
    """授权异常"""
    def __init__(self, message: str = "权限不足"):
        super().__init__(
            code="AUTH_500",  # 改为 AUTH_500
            message=message,
            status_code=status.HTTP_403_FORBIDDEN
        )


class ResourceNotFoundException(AppException):
    """资源未找到异常"""
    def __init__(self, message: str = "资源不存在"):
        super().__init__(
            code="BIZ_002",  # 改为 BIZ_002
            message=message,
            status_code=status.HTTP_404_NOT_FOUND
        )


class ConflictException(AppException):
    """资源冲突异常"""
    def __init__(self, message: str = "资源冲突"):
        super().__init__(
            code="BIZ_003",  # 改为 BIZ_003
            message=message,
            status_code=status.HTTP_409_CONFLICT
        )


class BusinessRuleException(AppException):
    """业务规则异常"""
    def __init__(self, message: str = "违反业务规则", details: dict = None):
        super().__init__(
            code="BIZ_001",  # 改为 BIZ_001
            message=message,
            details=details
        )


class ExternalServiceException(AppException):
    """外部服务异常"""
    def __init__(self, message: str = "外部服务错误", service_name: str = None):
        super().__init__(
            code="SYS_002",  # 改为 SYS_002
            message=message,
            status_code=status.HTTP_502_BAD_GATEWAY,
            details={"service_name": service_name} if service_name else None
        )


class RateLimitException(AppException):
    """限流异常"""
    def __init__(self, message: str = "请求过于频繁", retry_after: int = None):
        super().__init__(
            code="SYS_004",  # 改为 SYS_004
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details={"retry_after": retry_after} if retry_after else None
        )
```

### 6.3 修改 response.py 默认错误码

```python
def success_response(data: Any = None, message: str = "操作成功", code: str = "SUCCESS", **kwargs) -> JSONResponse:
    """成功响应函数"""
    # SUCCESS 保持不变（特殊标识）
    ...


def error_response(message: str, code: str = "SYS_001", status_code: int = 400, **kwargs) -> JSONResponse:
    """错误响应函数"""
    # 将 INTERNAL_ERROR 改为 SYS_001
    return StandardResponse.error(message=message, code=code, status_code=status_code, **kwargs)
```

---

## 7️⃣ 代码重构优先级与执行计划

### 🔴 P0 - 立即执行（阻断性问题）

**影响**: 错误码语义冲突导致监控、日志分析和前端错误处理混乱

1. **修正 custom_exceptions.py 中的 10 个异常类默认错误码**
   - 文件: `backend/exceptions/custom_exceptions.py`
   - 预计工作量: 1小时
   - 影响范围: 全局异常处理

2. **修正 handlers.py 中的 8 个异常类错误码**
   - 文件: `backend/exceptions/handlers.py`
   - 预计工作量: 1小时
   - 影响范围: 全局异常处理

3. **修正 response.py 的默认错误码**
   - 文件: `backend/core/response.py`
   - 预计工作量: 30分钟
   - 影响范围: 所有 API 响应

### 🟡 P1 - 近期执行（功能性问题）

**影响**: 错误码缺失导致错误信息不精确

1. **添加新增的 40+ 错误码到 error_codes.py**
   - 文件: `backend/core/error_codes.py`
   - 预计工作量: 2小时
   - 按优先级分批添加：
     - 批次1: AUTH_* 认证相关（18个）
     - 批次2: BIZ_* 业务相关（22个）
     - 批次3: SYS_*/VALIDATION_* 系统验证相关（5个）

2. **替换 routers/* 中的硬编码错误码**
   - 文件: `backend/routers/*.py`（13个文件）
   - 预计工作量: 4小时
   - 使用 `from backend.core.error_codes import ...` 替代字符串

3. **替换 services/* 中的硬编码错误码**
   - 文件: `backend/services/*.py`（9个文件）
   - 预计工作量: 3小时

### 🟢 P2 - 长期优化（规范性问题）

**影响**: 代码可维护性和一致性

1. **统一错误码导入方式**
   - 强制使用 `from backend.core.error_codes import AuthErrorCodes`
   - 禁止硬编码字符串错误码
   - 添加 pre-commit hook 检查

2. **添加错误码单元测试**
   - 测试所有异常类的默认错误码
   - 测试 error_codes.py 的完整性
   - 测试 HTTP 状态码映射正确性

3. **更新 ERROR_CODES.md 文档**
   - 添加新增的错误码
   - 更新错误码统计
   - 更新异常类映射表

---

## 8️⃣ 代码修改脚本示例

### 8.1 批量替换错误码脚本（Python）

```python
#!/usr/bin/env python3
"""
错误码批量替换脚本
使用方法: python replace_error_codes.py
"""
import re
from pathlib import Path

# 错误码映射表
ERROR_CODE_REPLACEMENTS = {
    # 认证相关
    'REGISTER_FAILED': 'AUTH_102',
    'LOGIN_FAILED': 'AUTH_900',
    'LOGOUT_FAILED': 'AUTH_901',
    'REFRESH_FAILED': 'AUTH_005',
    # 系统相关
    'SYS_500': 'SYS_001',
    'INTERNAL_ERROR': 'SYS_001',
    # 验证相关
    'VALIDATION_ERROR': 'VALIDATION_001',
    # 业务相关
    'BIZ_ERROR': 'BIZ_001',
    'NOT_FOUND': 'BIZ_002',
    # ... 更多映射
}

def replace_in_file(file_path: Path):
    """在文件中替换错误码"""
    content = file_path.read_text(encoding='utf-8')
    original = content

    for old_code, new_code in ERROR_CODE_REPLACEMENTS.items():
        # 替换 code="OLD_CODE" 形式
        content = re.sub(
            rf'code\s*=\s*"{old_code}"',
            f'code="{new_code}"',
            content
        )
        # 替换 error_code="OLD_CODE" 形式
        content = re.sub(
            rf'error_code\s*=\s*"{old_code}"',
            f'error_code="{new_code}"',
            content
        )

    if content != original:
        file_path.write_text(content, encoding='utf-8')
        print(f"✅ 已更新: {file_path}")
        return True
    return False

def main():
    backend_path = Path("backend")
    updated_files = []

    # 遍历 routers 和 services
    for pattern in ["routers/**/*.py", "services/**/*.py"]:
        for file_path in backend_path.glob(pattern):
            if replace_in_file(file_path):
                updated_files.append(file_path)

    print(f"\n✅ 共更新 {len(updated_files)} 个文件")
    for file_path in updated_files:
        print(f"  - {file_path}")

if __name__ == "__main__":
    main()
```

### 8.2 错误码检查脚本（验证一致性）

```python
#!/usr/bin/env python3
"""
错误码一致性检查脚本
检查代码中使用的错误码是否都在 error_codes.py 中定义
"""
import re
from pathlib import Path

def extract_error_codes_from_definition():
    """从 error_codes.py 提取所有定义的错误码"""
    error_codes_file = Path("backend/core/error_codes.py")
    content = error_codes_file.read_text(encoding='utf-8')

    # 匹配 ErrorCode("CODE", ...) 形式
    pattern = r'ErrorCode\s*\(\s*"([A-Z_0-9]+)"'
    return set(re.findall(pattern, content))

def extract_error_codes_from_usage():
    """从代码中提取所有使用的错误码"""
    used_codes = set()
    backend_path = Path("backend")

    for pattern in ["routers/**/*.py", "services/**/*.py", "exceptions/**/*.py"]:
        for file_path in backend_path.glob(pattern):
            content = file_path.read_text(encoding='utf-8')

            # 匹配 code="CODE" 和 error_code="CODE" 形式
            codes = re.findall(r'(?:code|error_code)\s*=\s*"([A-Z_0-9]+)"', content)
            used_codes.update(codes)

    # 排除特殊码
    used_codes.discard("SUCCESS")
    return used_codes

def main():
    defined_codes = extract_error_codes_from_definition()
    used_codes = extract_error_codes_from_usage()

    undefined_codes = used_codes - defined_codes
    unused_codes = defined_codes - used_codes

    print("=" * 60)
    print("错误码一致性检查报告")
    print("=" * 60)

    print(f"\n✅ 已定义错误码数量: {len(defined_codes)}")
    print(f"📊 实际使用错误码数量: {len(used_codes)}")

    if undefined_codes:
        print(f"\n🔴 代码中使用但未定义的错误码 ({len(undefined_codes)} 个):")
        for code in sorted(undefined_codes):
            print(f"  - {code}")
    else:
        print("\n✅ 所有使用的错误码都已定义")

    if unused_codes:
        print(f"\n🟡 已定义但未使用的错误码 ({len(unused_codes)} 个):")
        for code in sorted(unused_codes):
            print(f"  - {code}")
    else:
        print("\n✅ 所有定义的错误码都有使用")

if __name__ == "__main__":
    main()
```

---

## 9️⃣ 总结与建议

### 9.1 核心发现

1. **错误码碎片化严重**: 58+ 个错误码散布在代码中但未集中定义
2. **异常类默认值混乱**: 10 个异常类的默认错误码与标准定义冲突
3. **语义冲突**: `SYS_004` 同时用于 429 和 404，导致监控混乱
4. **缺少规范约束**: 没有 linter 或 pre-commit hook 防止硬编码错误码

### 9.2 行动建议

**短期（1-2周）**:
1. ✅ 执行 P0 优先级任务：修正异常类默认错误码（3小时）
2. ✅ 添加前 20 个高频错误码到 error_codes.py（2小时）
3. ✅ 运行替换脚本批量更新代码（2小时）

**中期（1个月）**:
1. ✅ 执行 P1 优先级任务：完成所有错误码添加和替换（9小时）
2. ✅ 添加单元测试覆盖错误码（4小时）
3. ✅ 更新 ERROR_CODES.md 文档（2小时）

**长期（持续）**:
1. ✅ 添加 pre-commit hook 检查硬编码错误码
2. ✅ 在 CI/CD 中集成错误码一致性检查
3. ✅ 定期（季度）审核新增错误码

### 9.3 风险提示

⚠️ **重要**: 修改异常类默认错误码是**破坏性变更**，可能影响：
- 前端错误处理逻辑（如果前端硬编码了错误码判断）
- 监控告警规则（如果基于错误码配置告警）
- 日志分析脚本（如果脚本依赖特定错误码）

**建议**:
1. 在测试环境先完整验证
2. 通知前端团队同步更新
3. 更新监控配置和告警规则
4. 发布变更通知和迁移指南

---

**报告生成者**: Claude Code
**审核状态**: 待人工审核
**下次同步**: 建议每季度执行一次同步检查
