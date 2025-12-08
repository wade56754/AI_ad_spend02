# 全局错误码真相源（Error Codes SoT）

**版本**: v2.1
**status**: active
**owner**: wade
**last_reviewed**: 2025-11-27
**最后更新**: 2025-01-21
**文档状态**: ✅ Source of Truth（真相源）

---

## 📌 真相源引用（Truth Source References）

本文档基于以下代码生成，所有错误码定义均来自实际代码实现：

| 文件路径 | 说明 | 代码行 |
|---------|------|--------|
| `backend/core/error_codes.py` | 标准错误码定义（AUTH/BIZ/VALIDATION/SYS/DB） | 48个错误码 |
| `backend/exceptions/handlers.py` | 自定义异常类及默认错误码 | 9个异常类 |
| `backend/core/response.py` | API响应封装（success_response/error_response） | Envelope格式 |

---

## 1. 概述

### 1.1 错误码体系架构

本系统采用**层次化错误码设计**，所有错误码遵循统一的命名规范和分类体系：

- **错误码（Error Code）**：唯一标识错误类型的字符串（如 `AUTH_001`）
- **错误消息（Error Message）**：面向开发者的中文错误描述
- **HTTP 状态码（Status Code）**：对应的 HTTP 响应状态码
- **状态标识（Status）**：USED（代码中使用）/ RESERVED（预留）

### 1.2 错误码设计原则

1. **唯一性**：每个错误码在全局唯一，不得重复定义
2. **语义化**：错误码前缀明确标识错误类别
3. **层次化**：采用三位数字编码，按功能模块划分区间
4. **可扩展**：预留足够的编码空间用于未来扩展
5. **向后兼容**：已定义的错误码不得修改或删除，只能新增

### 1.3 错误响应标准格式（Envelope）

所有 API 错误响应遵循全局 Envelope 格式（定义于 `backend/core/response.py`）：

```json
{
  "success": false,
  "message": "错误描述信息",
  "code": "ERROR_CODE",
  "data": null,
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2025-01-20T10:30:00Z"
}
```

**字段说明**：
- `success`: 布尔值，false 表示失败
- `message`: 面向开发者的错误描述（中文）
- `code`: 错误码字符串（如 `AUTH_001`）
- `data`: 错误详情（可选），通常为 `null`
- `request_id`: UUID v4 格式的请求追踪ID
- `timestamp`: ISO 8601 格式的UTC时间戳

---

## 2. 错误码命名规范

### 2.1 命名格式

```
<类别前缀>_<三位数字编码>
```

### 2.2 类别前缀定义

| 前缀 | 类别 | 说明 | HTTP 状态码范围 | 已定义数量 |
|------|------|------|----------------|-----------|
| `AUTH_` | 认证授权 | 用户认证、授权、权限相关错误 | 401, 403, 404, 500 | 24 |
| `BIZ_` | 业务逻辑 | 业务规则验证、状态转换等错误 | 400, 404, 409 | 10 |
| `VALIDATION_` | 参数验证 | 请求参数格式、类型验证错误 | 400 | 6 |
| `SYS_` | 系统错误 | 系统内部错误、服务不可用等 | 429, 500, 503, 504 | 4 |
| `DB_` | 数据库错误 | 数据库连接、查询、约束错误 | 400, 409, 500 | 5 |
| `STATE_` | 状态机错误 | 状态流转、终态保护等错误 | 400, 403, 409 | 6 |
| `TREND_` | 趋势风控错误 | 粉数确认趋势检查相关错误 | 200, 400 | 4 |

### 2.3 数字编码分段规则

#### AUTH_ 类（001-999）

- `001-099`: 登录相关
- `100-199`: 注册相关
- `200-299`: 密码相关
- `300-399`: 邮箱验证
- `400-499`: Token 相关
- `500-599`: 权限相关
- `900-999`: 通用认证错误

#### BIZ_ 类（001-999）

- `001-099`: 通用业务错误
- `100-199`: 金额相关
- `200-299`: 日期相关
- `300-399`: 状态相关
- `400-499`: 预留扩展
- `500-599`: 导入导出相关
- `600-699`: 账本/财务/统计相关
- `700-799`: 系统健康检查
- `800-899`: 预留扩展

#### VALIDATION_ 类（001-099）

- `001-009`: 必填字段
- `010-019`: 格式验证
- `020-029`: 范围验证
- `030-099`: 预留扩展

#### SYS_ 类（001-099）

- `001-009`: 内部错误
- `010-019`: 服务可用性
- `020-029`: 性能限制
- `030-099`: 预留扩展

#### DB_ 类（001-099）

- `001-019`: 连接和查询
- `020-099`: 约束违反

#### STATE_ 类（001-099）

- `001-099`: 状态机流转错误
- `100-199`: 终态保护错误
- `200-299`: 并发冲突错误
- `400-499`: 通用状态错误

#### TREND_ 类（001-099）

- `001-009`: 趋势风控触发
- `010-019`: 风控复核相关
- `020-099`: 预留扩展

---

## 3. 快速索引（常用错误码）

以下是最常使用的18个错误码：

| 错误码 | 消息 | HTTP | 使用场景 | 状态 |
|--------|------|------|----------|------|
| `AUTH_001` | 用户名或密码错误 | 401 | 登录验证失败 | USED |
| `AUTH_400` | 未提供认证令牌 | 401 | 请求头缺少Authorization | USED |
| `AUTH_401` | 无效的认证令牌 | 401 | Token签名验证失败 | USED |
| `AUTH_402` | 令牌已过期 | 401 | Token超过有效期 | USED |
| `AUTH_500` | 权限不足 | 403 | 用户角色不满足权限要求 | USED |
| `BIZ_001` | 无效的操作 | 400 | 业务规则验证失败 | USED |
| `BIZ_002` | 资源不存在 | 404 | 根据ID查询资源未找到 | USED |
| `BIZ_003` | 资源已存在 | 409 | 创建重复资源（唯一约束） | USED |
| `BIZ_201` | 日期不能为未来 | 400 | 日报提交日期晚于当前日期 | USED |
| `BIZ_300` | 状态无效 | 400 | 状态值不在枚举范围 | USED |
| `BIZ_301` | 状态转换不允许 | 400 | 违反状态机规则 | USED |
| `STATE_400` | 非法状态流转 | 400 | 不在白名单的状态流转 | USED |
| `STATE_402` | 终态非法回退 | 400 | 终态→非终态（非admin） | USED |
| `TREND_001` | 趋势风控触发 | 200 | 粉数骤降/骤增/消耗异常 | USED |
| `VALIDATION_001` | 必填字段缺失 | 400 | Pydantic必填字段为空 | USED |
| `VALIDATION_002` | 格式无效 | 400 | 字段格式不符合定义 | USED |
| `SYS_001` | 系统内部错误 | 500 | 未捕获的异常 | USED |
| `DB_004` | 唯一性约束违反 | 409 | 违反UNIQUE约束 | USED |

---

## 4. 错误码完整清单

### 4.1 认证授权类（AUTH_）

#### 登录相关（001-099）

| 错误码 | 消息 | HTTP | 触发场景 | 状态 |
|--------|------|------|----------|------|
| `AUTH_001` | 用户名或密码错误 | 401 | 提供的用户名或密码与数据库记录不匹配 | USED |
| `AUTH_002` | 账户已被禁用 | 403 | 用户账户的 `is_active` 字段为 `false` | USED |
| `AUTH_003` | 令牌已被撤销 | 401 | Token已在服务端被明确撤销（登出、安全操作） | USED |
| `AUTH_004` | 用户不存在或已被禁用 | 404 | 根据用户ID或邮箱查询时未找到用户记录 | USED |
| `AUTH_005` | 令牌刷新失败 | 401 | Refresh Token无效、过期或已被使用 | RESERVED |

#### 注册相关（100-199）

| 错误码 | 消息 | HTTP | 触发场景 | 状态 |
|--------|------|------|----------|------|
| `AUTH_100` | 邮箱已被注册 | 400 | 数据库中已存在相同邮箱的用户记录 | USED |
| `AUTH_101` | 用户名已被使用 | 400 | 数据库中已存在相同用户名的记录 | RESERVED |
| `AUTH_102` | 注册失败，请稍后重试 | 500 | 注册过程中发生数据库错误或外部服务调用失败 | RESERVED |

#### 密码相关（200-299）

| 错误码 | 消息 | HTTP | 触发场景 | 状态 |
|--------|------|------|----------|------|
| `AUTH_200` | 密码长度至少8位 | 400 | 密码长度 < 8 个字符 | RESERVED |
| `AUTH_201` | 密码必须包含至少一个数字 | 400 | 密码不包含数字字符（0-9） | RESERVED |
| `AUTH_202` | 密码必须包含至少一个字母 | 400 | 密码不包含字母字符（a-z, A-Z） | RESERVED |
| `AUTH_203` | 密码必须包含至少一个特殊字符 | 400 | 密码不包含特殊字符（!@#$%^&*等） | RESERVED |
| `AUTH_204` | 旧密码错误 | 400 | 修改密码时提供的旧密码不正确 | RESERVED |
| `AUTH_205` | 重置令牌无效或已过期 | 400 | 密码重置Token无效、已过期或已被使用 | RESERVED |
| `AUTH_206` | 密码修改失败 | 500 | 密码修改过程中发生数据库错误 | RESERVED |

#### 邮箱验证（300-399）

| 错误码 | 消息 | HTTP | 触发场景 | 状态 |
|--------|------|------|----------|------|
| `AUTH_300` | 邮箱未验证 | 403 | 用户的 `email_verified` 字段为 `false` | RESERVED |
| `AUTH_301` | 邮箱验证失败 | 400 | 验证Token无效或已过期 | RESERVED |
| `AUTH_302` | 邮箱已验证 | 400 | 用户邮箱已经完成验证 | RESERVED |

#### Token 相关（400-499）

| 错误码 | 消息 | HTTP | 触发场景 | 状态 |
|--------|------|------|----------|------|
| `AUTH_400` | 未提供认证令牌 | 401 | 请求头中缺少 `Authorization` 字段 | USED |
| `AUTH_401` | 无效的认证令牌 | 401 | Token格式错误、签名验证失败 | USED |
| `AUTH_402` | 令牌已过期 | 401 | Token的 `exp` 声明时间早于当前时间 | USED |

#### 权限相关（500-599）

| 错误码 | 消息 | HTTP | 触发场景 | 状态 |
|--------|------|------|----------|------|
| `AUTH_500` | 权限不足 | 403 | 用户角色不满足操作所需的权限要求 | USED |
| `AUTH_501` | 角色权限不足 | 403 | 用户的角色不在允许的角色列表中 | RESERVED |

#### 通用认证错误（900-999）

| 错误码 | 消息 | HTTP | 触发场景 | 状态 |
|--------|------|------|----------|------|
| `AUTH_900` | 登录失败，请稍后重试 | 500 | 登录过程中发生未预期的系统错误 | RESERVED |
| `AUTH_901` | 登出失败 | 500 | 登出过程中Token撤销操作失败 | RESERVED |
| `AUTH_999` | 认证失败 | 401 | 通用认证失败（无法归类到具体错误） | RESERVED |

---

### 4.2 业务逻辑类（BIZ_）

#### 通用业务错误（001-099）

| 错误码 | 消息 | HTTP | 触发场景 | 状态 |
|--------|------|------|----------|------|
| `BIZ_001` | 无效的操作 | 400 | 当前状态下不允许执行该操作 | USED |
| `BIZ_002` | 资源不存在 | 404 | 根据ID查询资源时未找到对应记录 | USED |
| `BIZ_003` | 资源已存在 | 409 | 尝试创建已存在的唯一资源（如项目代码） | USED |

#### 金额相关（100-199）

| 错误码 | 消息 | HTTP | 触发场景 | 状态 |
|--------|------|------|----------|------|
| `BIZ_100` | 金额无效 | 400 | 金额为负数、零或格式不正确 | USED |
| `BIZ_101` | 余额不足 | 400 | 项目余额不足以支付广告消费 | USED |

#### 日期相关（200-299）

| 错误码 | 消息 | HTTP | 触发场景 | 状态 |
|--------|------|------|----------|------|
| `BIZ_200` | 日期范围无效 | 400 | 开始日期晚于结束日期 | USED |
| `BIZ_201` | 日期不能为未来 | 400 | 输入的日期大于当前日期（日报提交、历史记录） | USED |

#### 状态相关（300-399）

| 错误码 | 消息 | HTTP | 触发场景 | 状态 |
|--------|------|------|----------|------|
| `BIZ_300` | 状态无效 | 400 | 提供的状态值不在允许的枚举值范围内 | USED |
| `BIZ_301` | 状态转换不允许 | 400 | 违反状态机规则的状态转换（如 archived → active） | USED |

#### 账本/财务/统计相关（600-699）

| 错误码 | 消息 | HTTP | 触发场景 | 状态 |
|--------|------|------|----------|------|
| `BIZ_600` | 账本创建失败 | 500 | 创建账本记录时发生数据库或业务逻辑错误 | USED |
| `BIZ_601` | 账本查询失败 | 500 | 查询账本记录时发生数据库错误 | USED |
| `BIZ_602` | 交易记录不存在 | 404 | 根据ID查询交易记录未找到 | USED |
| `BIZ_603` | 账本更新失败 | 500 | 更新账本记录时发生数据库错误 | USED |
| `BIZ_604` | 余额查询失败 | 500 | 查询项目/账户余额时发生错误 | USED |
| `BIZ_605` | 预算查询失败 | 500 | 查询预算信息时发生错误 | USED |
| `BIZ_606` | 预算创建失败 | 500 | 创建预算记录时发生错误 | USED |
| `BIZ_607` | 统计查询失败 | 500 | 执行统计聚合查询时发生错误（如利润汇总、交易统计） | USED |

---

### 4.3 参数验证类（VALIDATION_）

| 错误码 | 消息 | HTTP | 触发场景 | 状态 |
|--------|------|------|----------|------|
| `VALIDATION_001` | 必填字段缺失 | 400 | Pydantic验证时必填字段为 `None` 或未提供 | USED |
| `VALIDATION_002` | 格式无效 | 400 | 字段格式不符合Pydantic模型定义（如日期格式） | USED |
| `VALIDATION_003` | 邮箱格式无效 | 400 | 邮箱不符合标准邮箱格式规范 | USED |
| `VALIDATION_004` | 电话格式无效 | 400 | 电话号码不符合定义的正则表达式 | RESERVED |
| `VALIDATION_005` | 值超出范围 | 400 | 数值型字段超出 `ge`/`le`/`gt`/`lt` 限制 | RESERVED |
| `VALIDATION_006` | 枚举值无效 | 400 | 字符串字段的值不在允许的枚举值列表中 | RESERVED |

---

### 4.4 系统错误类（SYS_）

| 错误码 | 消息 | HTTP | 触发场景 | 状态 |
|--------|------|------|----------|------|
| `SYS_001` | 系统内部错误 | 500 | 发生未捕获的异常或系统内部逻辑错误 | USED |
| `SYS_002` | 服务暂时不可用 | 503 | 后端服务过载、维护中或依赖服务不可用 | USED |
| `SYS_003` | 请求超时 | 504 | 请求处理时间超过设定的超时阈值 | RESERVED |
| `SYS_004` | 请求过于频繁 | 429 | 触发了API限流规则（如IP/用户级别限流） | RESERVED |

---

### 4.5 数据库错误类（DB_）

| 错误码 | 消息 | HTTP | 触发场景 | 状态 |
|--------|------|------|----------|------|
| `DB_001` | 数据库连接失败 | 500 | 无法建立数据库连接（网络问题、凭证错误） | RESERVED |
| `DB_002` | 数据库查询失败 | 500 | SQL查询执行失败（语法错误、超时） | RESERVED |
| `DB_003` | 数据完整性约束违反 | 400 | 违反数据库CHECK约束 | RESERVED |
| `DB_004` | 唯一性约束违反 | 409 | 违反UNIQUE约束（如重复的项目代码） | USED |
| `DB_005` | 外键约束违反 | 400 | 违反外键约束（如引用不存在的用户ID） | RESERVED |

---

### 4.6 状态机错误类（STATE_）

**引用**: `STATE_MACHINE.md` v2.6 - 状态流转与终态保护规则

| 错误码 | 消息 | HTTP | 触发场景 | 状态 |
|--------|------|------|----------|------|
| `STATE_400` | 非法状态流转 | 400 | 不在白名单的状态流转（如 draft → completed） | USED |
| `STATE_401` | 跳过必要步骤 | 400 | 跳过审批等必要流程（如 draft → paid） | USED |
| `STATE_402` | 终态非法回退 | 400 | 终态 → 非终态（非admin角色） | USED |
| `STATE_403` | 系统无权限流转 | 403 | system尝试禁止的流转（如自动审批） | USED |
| `STATE_405` | 绝对禁止的流转 | 400 | 已完成充值回退等绝对禁止的操作 | USED |
| `STATE_409` | 并发冲突 | 409 | version不匹配（Optimistic Locking） | USED |

**使用示例**:
```python
from backend.core.error_codes import StateErrorCodes
from backend.exceptions import BusinessRuleException

# 场景1: 非法状态流转
if not validate_state_transition("topup_requests.status", current_status, target_status):
    raise BusinessRuleException(
        message=f"非法流转：{current_status} → {target_status}",
        code=StateErrorCodes.FORBIDDEN_TRANSITION.code  # STATE_400
    )

# 场景2: 终态回退
if is_final_state(current_status) and user.role != "admin":
    raise BusinessRuleException(
        message="终态回退需要admin权限",
        code=StateErrorCodes.FINAL_STATE_ROLLBACK.code  # STATE_402
    )

# 场景3: 并发冲突
if topup.version != expected_version:
    raise ConcurrencyConflictError(
        message=f"数据已被其他用户修改（当前版本：{topup.version}）",
        code=StateErrorCodes.CONCURRENCY_CONFLICT.code  # STATE_409
    )
```

---

### 4.7 趋势风控错误类（TREND_）

**引用**: `BR-RPT.md` BR-RPT-005 - 粉数确认流程规则 + `STATE_MACHINE.md` 第8章

**业务背景**: 基于BRD v3.1第4章"粉数确认状态机",系统采用三数据流(raw/real/final)分离设计,raw粉数需经过趋势风控检查(TF-001/002/003规则)后方可进入final确认。

| 错误码 | 消息 | HTTP | 触发场景 | 状态 |
|--------|------|------|----------|------|
| `TREND_001` | 趋势风控触发 | 200 | 粉数骤降/骤增/消耗异常（TF-001/002/003规则） | USED |
| `TREND_002` | 风控复核未完成 | 400 | trend_flagged状态下尝试进入final_pending | USED |
| `TREND_003` | 风控规则配置错误 | 500 | 趋势检查算法参数异常 | RESERVED |
| `TREND_010` | 复核原因缺失 | 400 | trend_resolved时未填写trend_resolution_note | USED |

**趋势风控规则映射**:

| 规则编号 | 规则名称 | 判断逻辑 | 触发后果 |
|---------|---------|---------| ---------|
| **TF-001** | 粉数骤降检查 | `conversions_raw < 昨日最大值 × 0.5` | `status=trend_flagged` + `TREND_001` |
| **TF-002** | 粉数骤增检查 | `conversions_raw > 昨日最大值 × 3` | `status=trend_flagged` + `TREND_001` |
| **TF-003** | 消耗异常检查 | `raw_spend > 昨日 × 2` | `status=trend_flagged` + `TREND_001` |

**使用示例**:
```python
from backend.core.error_codes import TrendErrorCodes
from backend.services.daily_report_service import DailyReportService

# 场景1: 趋势风控检查
def check_trend_risk(report: DailyReport):
    yesterday_max = get_yesterday_max_conversions(report.ad_account_id)

    # TF-001: 粉数骤降
    if report.conversions_raw < yesterday_max * 0.5:
        report.status = "trend_flagged"
        report.trend_flag_reason = "TF-001: 粉数骤降50%"
        # 注意: 这里返回200状态码,因为风控检查本身是成功的业务操作
        return {
            "success": True,
            "code": TrendErrorCodes.TREND_RISK_TRIGGERED.code,  # TREND_001
            "message": "粉数骤降，已标记trend_flagged",
            "data": {"status": "trend_flagged", "reason": report.trend_flag_reason}
        }

# 场景2: 跳过风控复核
def update_real_spend(report_id: int, real_spend: Decimal):
    report = get_report(report_id)

    if report.status == "trend_flagged":
        raise BusinessRuleException(
            message="trend_flagged状态必须复核",
            code=TrendErrorCodes.REVIEW_REQUIRED.code  # TREND_002
        )
```

---

## 5. 自定义异常类与错误码映射

### 5.1 异常类定义

系统定义了以下自定义异常类（位于 `backend/exceptions/handlers.py`）：

| 异常类 | 默认错误码 | HTTP状态码 | 推荐错误码 | 使用场景 |
|--------|-----------|-----------|-----------|----------|
| `AppException` | - | 400 | - | 基础异常类，所有自定义异常的父类 |
| `ValidationException` | `VALIDATION_ERROR` | 422 | `VALIDATION_001` ~ `VALIDATION_006` | 参数验证失败（Pydantic模型验证） |
| `AuthenticationException` | `AUTHENTICATION_ERROR` | 401 | `AUTH_001`, `AUTH_400`, `AUTH_401`, `AUTH_402` | 认证失败（登录、Token验证） |
| `AuthorizationException` | `AUTHORIZATION_ERROR` | 403 | `AUTH_500`, `AUTH_501` | 权限不足（角色/权限验证） |
| `ResourceNotFoundException` | `RESOURCE_NOT_FOUND` | 404 | `BIZ_002`, `AUTH_004` | 资源未找到（查询不存在的实体） |
| `ConflictException` | `RESOURCE_CONFLICT` | 409 | `BIZ_003`, `DB_004` | 资源冲突（唯一约束违反） |
| `BusinessRuleException` | `BUSINESS_RULE_ERROR` | 400 | `BIZ_001`, `BIZ_300`, `BIZ_301` | 业务规则违反（状态机、业务逻辑） |
| `ExternalServiceException` | `EXTERNAL_SERVICE_ERROR` | 502 | `SYS_002` | 外部服务调用失败（API、第三方服务） |
| `RateLimitException` | `RATE_LIMIT_EXCEEDED` | 429 | `SYS_004` | 限流触发（API访问频率限制） |

**注意事项**：
- "默认错误码"列是异常类内置的通用错误码，用于未指定具体错误码时的默认值
- "推荐错误码"列是业务代码中抛出异常时应该使用的具体错误码（来自 `error_codes.py`）
- 业务代码应**优先使用推荐错误码**，避免使用通用的默认错误码

### 5.2 异常使用示例

#### ✅ 推荐：抛出异常时明确指定错误码

```python
from backend.exceptions import BusinessRuleException, ResourceNotFoundException
from backend.core.error_codes import BusinessErrorCodes, AuthErrorCodes

# 示例1: 业务规则验证失败
if project.status == ProjectStatus.ARCHIVED:
    raise BusinessRuleException(
        message="已归档的项目无法修改",
        code=BusinessErrorCodes.STATUS_TRANSITION_NOT_ALLOWED.code  # BIZ_301
    )

# 示例2: 资源不存在
if not project:
    raise ResourceNotFoundException(
        message=f"项目 {project_id} 不存在",
        code=BusinessErrorCodes.RESOURCE_NOT_FOUND.code  # BIZ_002
    )

# 示例3: 权限验证失败
if not user.has_permission("project:delete"):
    raise AuthorizationException(
        message="您没有删除项目的权限",
        code=AuthErrorCodes.PERMISSION_DENIED.code  # AUTH_500
    )
```

#### ❌ 不推荐：使用默认错误码（语义不精确）

```python
# 不推荐：使用默认错误码 RESOURCE_NOT_FOUND
if not project:
    raise ResourceNotFoundException(f"项目 {project_id} 不存在")
    # 返回: code="RESOURCE_NOT_FOUND" (通用错误码，无法追溯到具体业务场景)
```

### 5.3 Router 层错误处理模式

```python
from fastapi import APIRouter, Depends
from backend.exceptions import ResourceNotFoundException, BusinessRuleException
from backend.core.response import success_response, error_response
from backend.services import ProjectService

router = APIRouter()

@router.get("/projects/{project_id}")
async def get_project(
    project_id: int,
    service: ProjectService = Depends()
):
    try:
        project = service.get_project(project_id)
        return success_response(data=project)

    except ResourceNotFoundException as e:
        # 异常携带了具体的错误码（如 BIZ_002）
        return error_response(
            code=e.code,
            message=e.message,
            status_code=e.status_code
        )

    except BusinessRuleException as e:
        return error_response(
            code=e.code,
            message=e.message,
            status_code=e.status_code
        )

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return error_response(
            code="SYS_001",  # 使用系统内部错误码
            message="系统内部错误",
            status_code=500
        )
```

---

## 6. API 文档引用规范

### 6.1 OpenAPI 错误响应定义

所有 API 端点应在 OpenAPI 文档中明确声明可能返回的错误码：

```python
@router.get(
    "/projects/{project_id}",
    responses={
        200: {"description": "成功", "model": ProjectResponse},
        401: {
            "description": "未认证",
            "content": {"application/json": {"example": {
                "success": False,
                "code": "AUTH_400",
                "message": "未提供认证令牌",
                "data": None,
                "request_id": "550e8400-e29b-41d4-a716-446655440000",
                "timestamp": "2025-01-20T10:30:00Z"
            }}}
        },
        403: {
            "description": "权限不足",
            "content": {"application/json": {"example": {
                "success": False,
                "code": "AUTH_500",
                "message": "权限不足",
                "data": None,
                "request_id": "550e8400-e29b-41d4-a716-446655440000",
                "timestamp": "2025-01-20T10:30:00Z"
            }}}
        },
        404: {
            "description": "资源不存在",
            "content": {"application/json": {"example": {
                "success": False,
                "code": "BIZ_002",
                "message": "资源不存在",
                "data": None,
                "request_id": "550e8400-e29b-41d4-a716-446655440000",
                "timestamp": "2025-01-20T10:30:00Z"
            }}}
        },
    }
)
async def get_project(project_id: int):
    ...
```

### 6.2 模块 API 文档中的错误码引用格式

在模块级 API 文档（如 `docs/modules/projects/API_GUIDE.md`）中，应按以下格式引用错误码：

```markdown
## 错误码

本模块 API 可能返回以下错误码：

| 错误码 | 说明 | 触发场景 |
|--------|------|----------|
| AUTH_400 | 未提供认证令牌 | 请求头缺少 Authorization 字段 |
| AUTH_500 | 权限不足 | 用户角色不满足操作权限要求 |
| BIZ_002 | 资源不存在 | 项目 ID 不存在 |
| BIZ_003 | 资源已存在 | 项目代码重复 |
| BIZ_300 | 状态无效 | 提供的状态值不在枚举范围内 |
| BIZ_301 | 状态转换不允许 | 违反状态机规则的状态转换 |
```

---

## 7. 错误码查询与维护

### 7.1 代码中查询错误码

```python
from backend.core.error_codes import (
    get_error_code,
    ERROR_CODE_MAP,
    AuthErrorCodes,
    BusinessErrorCodes,
    ValidationErrorCodes,
    SystemErrorCodes,
    DatabaseErrorCodes
)

# 方式 1：通过辅助函数查询
error = get_error_code("AUTH_001")
print(f"Code: {error.code}, Message: {error.message}, Status: {error.status_code}")
# 输出: Code: AUTH_001, Message: 用户名或密码错误, Status: 401

# 方式 2：直接查询映射表
error = ERROR_CODE_MAP.get("AUTH_001")

# 方式 3：使用错误码类（推荐）
error = AuthErrorCodes.INVALID_CREDENTIALS
print(error.code)  # AUTH_001
print(error.message)  # 用户名或密码错误
print(error.status_code)  # 401
```

### 7.2 添加新错误码的流程

#### 步骤 1：在 `error_codes.py` 中定义错误码

```python
# backend/core/error_codes.py

class BusinessErrorCodes:
    # ... 现有错误码 ...

    # 新增错误码
    PROJECT_ARCHIVED = ErrorCode(
        "BIZ_302",
        "项目已归档",
        400
    )
```

#### 步骤 2：添加到 ERROR_CODE_MAP

```python
# backend/core/error_codes.py

ERROR_CODE_MAP: Dict[str, ErrorCode] = {
    # ... 现有映射 ...

    # 新增映射
    "BIZ_302": BusinessErrorCodes.PROJECT_ARCHIVED,
}
```

#### 步骤 3：更新本文档

在对应分类表格中添加新错误码：

| 错误码 | 消息 | HTTP | 触发场景 | 状态 |
|--------|------|------|----------|------|
| `BIZ_302` | 项目已归档 | 400 | 尝试操作已归档的项目 | USED |

#### 步骤 4：在代码中使用

```python
from backend.core.error_codes import BusinessErrorCodes
from backend.exceptions import BusinessRuleException

# Service 层
def update_project(project_id: int, data: dict):
    project = get_project(project_id)

    if project.status == ProjectStatus.ARCHIVED:
        raise BusinessRuleException(
            message="项目已归档，无法修改",
            code=BusinessErrorCodes.PROJECT_ARCHIVED.code
        )

    # ... 业务逻辑 ...
```

---

## 8. 附录

### 8.1 错误码统计

#### 当前错误码数量

| 类别 | 已定义数量 | 已使用（USED） | 预留（RESERVED） | 可用编码空间 | 利用率 |
|------|-----------|---------------|----------------|-------------|--------|
| AUTH_ | 24 | 7 | 17 | 999 | 2.4% |
| BIZ_ | 18 | 17 | 1 | 999 | 1.8% |
| VALIDATION_ | 6 | 3 | 3 | 99 | 6.1% |
| SYS_ | 4 | 2 | 2 | 99 | 4.0% |
| DB_ | 5 | 1 | 4 | 99 | 5.1% |
| STATE_ | 6 | 6 | 0 | 99 | 6.1% |
| TREND_ | 4 | 3 | 1 | 99 | 4.0% |
| **总计** | **67** | **39** | **28** | **2,393** | **2.8%** |

#### HTTP 状态码分布

| HTTP 状态码 | 错误码数量 | 占比 |
|------------|-----------|------|
| 200 | 1 | 1.7% |
| 400 | 28 | 47.5% |
| 401 | 8 | 13.6% |
| 403 | 6 | 10.2% |
| 404 | 2 | 3.4% |
| 409 | 3 | 5.1% |
| 429 | 1 | 1.7% |
| 500 | 7 | 11.9% |
| 503 | 1 | 1.7% |
| 504 | 1 | 1.7% |
| 422 | 1 | 1.7% |

### 8.2 历史审计说明

#### 审计日期：2025-01-19

**审计发现（已归档）**：

1. **异常类默认错误码与 error_codes.py 定义存在差异**
   - **现状**：异常类使用通用错误码（如 `VALIDATION_ERROR`, `AUTHENTICATION_ERROR`），而不是具体的错误码（如 `VALIDATION_001`, `AUTH_001`）
   - **原因**：异常类设计为通用容器，具体错误码由业务代码在抛出异常时指定
   - **解决方案**：在文档第 5.1 节明确区分"默认错误码"和"推荐错误码"，引导开发者使用具体错误码

2. **部分错误码定义但未使用**
   - **现状**：48个已定义错误码中，仅21个处于USED状态（43.75%）
   - **原因**：部分错误码为预留设计（密码复杂度验证、邮箱验证等功能尚未实现）
   - **解决方案**：在文档第 4 节为所有错误码添加STATUS列，区分USED和RESERVED状态

3. **错误响应格式缺少 request_id 字段**
   - **现状**：初版文档未包含 `request_id` 字段
   - **原因**：文档创建时未参考 `backend/core/response.py` 的实际实现
   - **解决方案**：v2.0版本已更新错误响应格式，与代码实现完全一致

#### 规范化实施路径（已归档）

**阶段 1：文档规范（已完成）**
- ✅ 建立本 SoT 文档 v2.0
- ✅ 明确错误码命名和使用规范
- ✅ 添加 STATUS 列区分 USED/RESERVED
- ✅ 添加快速索引表
- ✅ 对齐错误响应格式与全局 Envelope

**阶段 2：代码审计（建议优先级：P1）**
- [ ] 扫描所有 Service 和 Router 层的错误码使用情况
- [ ] 将所有通用错误码（如 `VALIDATION_ERROR`）替换为具体错误码（如 `VALIDATION_001`）
- [ ] 统计错误码使用频率，识别热点错误码

**阶段 3：代码重构（建议优先级：P2）**
- [ ] 统一异常抛出模式，强制要求指定具体错误码
- [ ] 将所有硬编码错误码字符串替换为 `error_codes.py` 引用
- [ ] 添加单元测试覆盖所有错误码场景

### 8.3 相关文档

| 文档名称 | 路径 | 说明 |
|---------|------|------|
| 数据模型 SoT | `./DATA_SCHEMA.md` | 数据库表结构定义 |
| 业务规则 SoT | `./BUSINESS_RULES.md` | 业务规则和状态机定义 |
| 项目模块 API 文档 | `docs/modules/projects/API_GUIDE.md` | 项目模块接口说明 |

### 8.4 变更日志

| 版本 | 日期 | 变更内容 | 作者 |
|------|------|----------|------|
| v1.0 | 2025-01-19 | 初始版本，基于 error_codes.py v1.0 生成 | Claude |
| v2.0 | 2025-01-20 | **重大优化**：<br>• 添加快速索引表（第3节）<br>• 为所有错误码表添加STATUS列（USED/RESERVED）<br>• 修正错误响应格式，对齐全局Envelope（包含request_id）<br>• 修正异常类映射说明，区分默认错误码和推荐错误码<br>• 将历史审计说明移至附录<br>• 基于实际代码验证所有定义 | Claude（Chief Backend Auditor） |
| v2.1 | 2025-01-21 | **【BRD v3.1对齐更新】**<br>• 新增 STATE_ 类错误码（6个）: STATE_400/401/402/403/405/409<br>• 新增 TREND_ 类错误码（4个）: TREND_001/002/003/010<br>• 更新 BIZ_201 状态: RESERVED → USED (日报提交逾期)<br>• 更新快速索引表: 15个 → 18个常用错误码<br>• 新增第4.6节: 状态机错误类（STATE_）含使用示例<br>• 新增第4.7节: 趋势风控错误类（TREND_）含TF-001/002/003规则映射<br>• 更新错误码统计: 48个 → 59个总数 | 系统架构团队 |

---

**文档维护者**: 后端开发团队
**最后审核**: 2025-01-21
**下次审核**: 季度性审核或重大变更时
