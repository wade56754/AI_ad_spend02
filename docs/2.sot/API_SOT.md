# API 开发与使用规范（API Single Source of Truth）

> **文档版本**: v9.2 (对齐 MASTER.md v4.4)
> **status**: frozen
> **owner**: wade
> **last_reviewed**: 2025-12-24
> **文档类型**: 项目唯一真相源（SoT）
> **适用范围**: 所有后端API开发与前端API调用
> **规范级别**: 🔴 强制执行
> **最后更新**: 2025-12-24
> **文档定位**: 端点级API规范,任何开发者仅凭本文档即可完成API开发/调用/测试

---

## ⚡ 使用声明

**本文档是端点级API的唯一真相源**,对于任意API端点,开发者应该能够仅通过本文档完成:

1. **后端开发**: Schema → Service → Router 的完整实现
2. **前端调用**: 请求参数、响应字段、错误码处理
3. **测试编写**: 正常流程、异常场景、权限验证
4. **问题排查**: 根据错误码快速定位问题

**禁止猜测或脑补**: 所有字段名、类型、枚举值、状态流转必须在本文档中明确定义。

---

## 目录

1. [核心约束与真相源](#1-核心约束与真相源)
2. [统一规范](#2-统一规范)
3. [API 开发流程](#3-api-开发流程)
4. [响应格式规范](#4-响应格式规范)
5. [Users API（用户与认证）](#5-users-api用户与认证)
6. [Projects API（项目管理）](#6-projects-api项目管理)
6A. [Project Members API（项目成员）](#6a-project-members-api项目成员)
7. [Channels API（渠道管理）](#7-channels-api渠道管理)
8. [Ad Accounts API（广告账户）](#8-ad-accounts-api广告账户)
9. [Daily Reports API（日报管理）](#9-daily-reports-api日报管理)
10. [Topup Requests API（充值申请）](#10-topup-requests-api充值申请)
11. [Ledger API（资金账本）](#11-ledger-api资金账本)
11A. [Finance Profit API（财务利润统计）](#11a-finance-profit-api财务利润统计)
12. [Reconciliation API（对账管理）](#12-reconciliation-api对账管理)
12W. [Weekly Briefs API（周报管理）](#12w-weekly-briefs-api周报管理)
13. [全局规范参考](#13-全局规范参考)

---

## 1. 核心约束与真相源

### 1.1 唯一真相源（强制依赖）

- **系统宪法**: [`../1.overview/MASTER.md`](../1.overview/MASTER.md) v4.4 - 系统全局规则、角色定义、Phase 边界
- **数据定义**: [`./DATA_SCHEMA.md`](./DATA_SCHEMA.md) v5.2 - 表结构、字段、类型的唯一来源
- **状态机定义**: [`./STATE_MACHINE.md`](./STATE_MACHINE.md) v2.6 - 业务状态流转的唯一来源
- **业务规则**: [`./BUSINESS_RULES.md`](./BUSINESS_RULES.md) v3.2 - 业务约束的唯一来源
- **错误码**: [`./ERROR_CODES_SOT.md`](./ERROR_CODES_SOT.md) v2.1 - 错误码定义的唯一来源
- **认证授权**: [`./AUTH_SPEC.md`](./AUTH_SPEC.md) v2.0 - 权限矩阵的唯一来源

### 1.2 五个不可违背的规则

1. **数据库字段禁止自创** - 所有字段必须在 DATA_SCHEMA.md 中定义
2. **角色限定为7个** - 见下方角色定义表（来源: MASTER.md v4.4 §2.4）
3. **响应必须使用 Envelope** - 使用 `success_response`/`error_response`
4. **前端必须通过 apiFetch** - 禁止直接 fetch 或其他 HTTP 库
5. **开发顺序强制执行** - Schema → Service → Router → Test → Exception Handler

#### 1.2.1 角色定义（7 角色，来源: MASTER.md v4.4 §2.4）

| 角色 | 系统角色名 | 职责边界 | 典型操作 |
|------|-----------|---------|---------|
| 老板 | `ceo` | 资金安全、公司盈亏、最终决策 | 批准充值、锁定结算、查看全部 |
| 项目负责人 | `project_owner` | 项目盈亏、资金使用效率 | 申请充值、查看项目、提交周报 |
| 财务 | `finance` | 资金出入准确、数据真实、对账 | 审核充值、确认付款、查看账本 |
| 主管 | `supervisor` | 团队产出、投手管理、日常监督 | 审核日报、标记异常、查看团队 |
| 投手 | `pitcher` | CPL 达标、日报准确、执行投放 | 填报日报、查看自己数据 |
| 户管 | `account_manager` | 账户分配、账户状态监控 | 分配账户、标记死号、余额迁移 |
| 管理员 | `admin` | 系统配置（不参与业务） | 用户管理、系统配置 |

> **旧角色映射说明**: 文档中出现的 `media_buyer` 等同于 `pitcher`，`data_operator` 等同于 `supervisor`。新开发应使用 7 角色标准名称。

### 1.3 三数据流与双账本（核心概念）

#### 三数据流（raw/real/final）

| 数据流 | 字段 | 提交者 | 时效性 | 用途 |
|-------|------|--------|--------|------|
| **raw数据流** | `conversions_raw`, `raw_spend` | 投手 | T+0 23:59前 | 趋势监控，风控检查 |
| **real数据流** | `real_spend` | 运营 | T+1 12:00前 | 成本核算 |
| **final数据流** | `conversions_final` | 运营 | T+1 14:00前 | 计费基准 |

**引用**: MASTER.md v4.4 §4（三数据流）、BUSINESS_RULES.md v3.2

#### 双账本（PROJECT/SUPPLIER）

| 账本类型 | 用途 | 关联实体 | entry_type范围 | 计费公式 |
|---------|------|---------|---------------|---------|
| **PROJECT** | 项目收入账本 | `project_id` | `REVENUE`, `REVERSAL` | `revenue = conversions_final × unit_price` |
| **SUPPLIER** | 供应商成本账本 | `supplier_id` | `COST`, `TRANSFER_OUT`, `TRANSFER_IN`, `REVERSAL` | `cost = real_spend + fee` |

**引用**: LEDGER_SOT.md v1.1、DATA_SCHEMA.md v5.2 §3.4.4

### 1.4 Phase 边界说明（MASTER v4.4 对齐）

> **引用**: MASTER.md v4.4 §2.5、§4.1

#### 1.4.1 数据流 Phase 适用性

| 数据流 | Phase 1 | Phase 2 |
|-------|---------|---------|
| raw数据流 | 正常使用 | 正常使用 |
| real数据流 | 可选使用（简化模式可跳过） | 强制使用 |
| final数据流 | 可选使用（简化模式可跳过） | 强制使用（计费基准） |

#### 1.4.2 API 行为 Phase 差异

| API 类型 | Phase 1 行为 | Phase 2 行为 |
|---------|-------------|-------------|
| 日报状态转换 | 支持简化 3 状态跳转 | 完整 8 状态流程 |
| 充值审批 | 无预算阻断 | 可启用预算阻断 |
| 项目暂停 | 仅标记状态 | 可联动阻断投放 |

**Phase 1 核心原则**：API 只做「记录」与「查询」，不做「阻断」或「惩罚」。

---

## 2. 统一规范

### 2.1 路由规范

- **路由前缀**: `/api/v1`
- **命名规则**: 复数形式，kebab-case（如 `/api/v1/topups`）
- **路径参数**: 使用有意义的名称（如 `{project_id}`，不是 `{id}`）

### 2.2 认证与授权

- **认证方式**: JWT（Supabase Auth）
- **令牌传递**: `Authorization: Bearer <token>` 请求头
- **前端调用**: 统一使用 `lib/api.ts::apiFetch`
- **禁止**: 组件内直接使用 `fetch()` / `axios` 调用业务API

### 2.3 数据类型规范

| 数据类型 | Python 类型 | TypeScript 类型 | 数据库类型 | 说明 |
|---------|------------|----------------|-----------|------|
| 金额 | `Decimal` | `string` | `DECIMAL(15,2)` | 两位小数，HALF_UP 舍入 |
| 日期时间 | `datetime` | `string (ISO 8601)` | `TIMESTAMPTZ` | UTC 时区 |
| UUID | `UUID` | `string` | `UUID` | 主键、外键使用 |
| 枚举 | `Literal` | `string` | `VARCHAR` + `CHECK` | 状态、类型字段 |
| 整数 | `int` | `number` | `INTEGER` | 粉数、点击等指标 |
| 大整数 | `int` | `number` | `BIGINT` | 主键(业务表) |

### 2.4 分页规范

- **分页参数**:
  - `page`: 整数，从 1 开始，默认 1
  - `page_size`: 整数，1-100，默认 20
- **排序**: 默认按 `created_at DESC`（最新的在前）

### 2.5 并发控制

- **乐观锁**: 使用 `expected_version` 字段（涉及余额、计费的表）
- **悲观锁**: 使用 `SELECT ... FOR UPDATE`（事务内锁定）
- **冲突处理**: 返回错误码 `STATE_409`

### 2.6 幂等性保证

- **唯一键**: `(ad_account_id, report_date)`, `request_no` 等
- **Idempotency-Key**: Header头（适用于充值、对账等）
- **状态机保护**: 终态不可重复提交

---

## 3. API 开发流程

### 3.1 开发步骤（强制流程）

#### Step 1: 确认需求与文档（10分钟）

```bash
# 1. 查看表结构定义
grep -A 50 "{{table_name}}" ./DATA_SCHEMA.md

# 2. 查看状态机定义
grep -A 30 "{{state_machine_name}}" ./STATE_MACHINE.md

# 3. 查看业务规则
grep "BR-{{MODULE}}" ./BUSINESS_RULES.md

# 4. 查看错误码
grep "{{ERROR_CODE}}" ./ERROR_CODES_SOT.md
```

#### Step 2: Schema 层实现（15分钟）

```python
# backend/schemas/{module}.py
from pydantic import BaseModel, Field, ConfigDict, field_validator
from decimal import Decimal
from typing import Optional, Literal
from datetime import datetime
from uuid import UUID

# 状态定义来自 STATE_MACHINE.md
STATUS_ENUM = Literal["draft", "pending", "approved", "rejected"]

class ResourceCreate(BaseModel):
    """创建资源 - 基于 DATA_SCHEMA.md {table}表"""
    model_config = ConfigDict(from_attributes=True)

    # 字段严格对应 DATA_SCHEMA.md 定义
    name: str = Field(..., min_length=1, max_length=200)
    amount: Decimal = Field(..., ge=0, description="金额 - DECIMAL(15,2)")

    @field_validator('amount')
    def validate_amount(cls, v):
        # 金额必须两位小数
        return v.quantize(Decimal('0.01'))
```

#### Step 3: Service 层实现（30分钟）

```python
# backend/services/{module}_service.py
from typing import List, Optional
from sqlalchemy.orm import Session
from backend.models.{module} import Resource
from backend.schemas.{module} import ResourceCreate
from backend.core.exceptions import BusinessError, PermissionError
from backend.core.error_codes import ErrorCode

class ResourceService:
    """资源服务 - 实现 STATE_MACHINE.md 定义的状态机"""

    def __init__(self, db: Session):
        self.db = db

    def create_resource(
        self,
        data: ResourceCreate,
        current_user_id: UUID,
        current_user_role: str
    ) -> Resource:
        """创建资源"""

        # 权限检查（基于 BUSINESS_RULES.md）
        if current_user_role not in ['admin', 'finance']:
            raise PermissionError(
                code=ErrorCode.AUTH_500,
                message="无权限创建资源"
            )

        # 业务逻辑
        resource = Resource(
            **data.model_dump(),
            status='draft',  # 初始状态
            created_by=current_user_id,
            created_at=datetime.utcnow()
        )

        self.db.add(resource)
        self.db.commit()
        self.db.refresh(resource)

        return resource
```

#### Step 4: Router 层实现（20分钟）

```python
# backend/routers/{module}.py
from fastapi import APIRouter, Depends
from backend.core.dependencies import get_db, get_current_user
from backend.core.response import success_response, error_response
from backend.services.{module}_service import ResourceService
from backend.schemas.{module} import ResourceCreate, ResourceResponse
from backend.models.users import User
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/v1/resources", tags=["资源管理"])

@router.post("", summary="创建资源")
async def create_resource(
    request: ResourceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建资源（初始状态为draft）"""
    service = ResourceService(db)
    result = service.create_resource(
        data=request,
        current_user_id=current_user.id,
        current_user_role=current_user.role
    )

    return success_response(
        data=ResourceResponse.model_validate(result),
        message="资源已创建"
    )
```

---

## 4. 响应格式规范

### 4.1 Envelope 格式（强制）

所有API响应必须使用 Envelope 格式，**禁止**返回 FastAPI 默认的 `{detail: "..."}` 响应。

### 4.2 成功响应

```json
{
  "success": true,
  "data": {
    "id": 1,
    "status": "pending",
    "amount": "10000.00"
  },
  "message": "操作成功",
  "code": "SUCCESS",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2025-01-22T10:00:00Z"
}
```

**字段说明**:
- `success`: 布尔值，true 表示成功
- `data`: 业务数据（可以是对象、数组或null）
- `message`: 面向开发者的操作说明
- `code`: 成功状态码，默认为 "SUCCESS"
- `request_id`: UUID v4格式的请求追踪ID
- `timestamp`: ISO 8601格式的UTC时间戳

### 4.3 错误响应

```json
{
  "success": false,
  "error": {
    "code": "BIZ_301",
    "message": "状态转换非法",
    "details": {
      "from": "approved",
      "to": "pending",
      "help": "请查阅 STATE_MACHINE.md 了解合法的状态转换"
    }
  },
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2025-01-22T10:00:00Z"
}
```

**字段说明**:
- `success`: 布尔值，false 表示失败
- `error.code`: 错误码（来自 ERROR_CODES_SOT.md）
- `error.message`: 面向开发者的错误描述（中文）
- `error.details`: 错误详情（可选）
- `request_id`: UUID v4格式的请求追踪ID
- `timestamp`: ISO 8601格式的UTC时间戳

### 4.4 分页响应

```json
{
  "success": true,
  "data": {
    "items": [...],
    "meta": {
      "pagination": {
        "page": 1,
        "page_size": 20,
        "total": 100,
        "total_pages": 5,
        "has_next": true,
        "has_prev": false
      }
    }
  },
  "message": "查询成功",
  "code": "SUCCESS"
}
```

---

## 5. Users API（用户与认证）

### 5.1 端点总览

| 方法 | 路径 | 功能 | 权限 | 状态 |
|------|------|------|------|------|
| POST | `/api/v1/auth/login` | 用户登录 | 公开 | implemented |
| POST | `/api/v1/auth/register` | 用户注册 | 公开 | implemented |
| POST | `/api/v1/auth/logout` | 用户登出 | 已登录用户 | implemented |
| GET | `/api/v1/users/me` | 获取当前用户信息 | 已登录用户 | implemented |
| GET | `/api/v1/users` | 获取用户列表 | `admin` | implemented |
| POST | `/api/v1/users` | 创建用户 | `admin` | implemented |
| PUT | `/api/v1/users/{user_id}` | 更新用户 | `admin` | implemented |

### 5.2 POST `/api/v1/auth/login` - 用户登录

#### 请求

**Request Schema**:

| 字段 | 类型 | 必填 | 约束 | 说明 | 对应表字段 |
|------|------|------|------|------|-----------|
| `email` | string | ✅ | 邮箱格式 | 用户邮箱 | `auth.users.email` |
| `password` | string | ✅ | 最少8位 | 用户密码 | - |

**Request示例**:
```json
{
  "email": "user@example.com",
  "password": "Password123!"
}
```

#### 响应

**Success (200 OK)**:

```json
{
  "success": true,
  "data": {
    "user": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "username": "john_doe",
      "full_name": "John Doe",
      "email": "user@example.com",
      "role": "pitcher",
      "is_active": true,
      "created_at": "2025-01-01T00:00:00Z"
    },
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expires_in": 3600
  },
  "message": "登录成功",
  "code": "SUCCESS"
}
```

**Response Schema** (`data`字段):

| 字段 | 类型 | 来源 | 说明 |
|------|------|------|------|
| `user.id` | UUID | `users.id` | 用户ID |
| `user.username` | string | `users.username` | 用户名 |
| `user.full_name` | string | `users.full_name` | 真实姓名 |
| `user.email` | string | `users.email` | 邮箱 |
| `user.role` | string | `users.role` | 角色（技术层 5 个值，见 §1.2.1 角色定义） |
| `user.is_active` | boolean | `users.is_active` | 账号可用性 |
| `user.created_at` | ISO 8601 | `users.created_at` | 创建时间 |
| `access_token` | string | Supabase Auth | JWT访问令牌 |
| `refresh_token` | string | Supabase Auth | JWT刷新令牌 |
| `expires_in` | integer | Supabase Auth | Token有效期(秒) |

**Error Responses**:

| 错误码 | HTTP状态码 | 触发场景 |
|--------|-----------|----------|
| `AUTH_001` | 401 | 用户名或密码错误 |
| `AUTH_002` | 403 | 账户已被禁用 |
| `AUTH_100` | 400 | 邮箱格式无效 |
| `SYS_001` | 500 | 系统内部错误 |

**引用**:
- 业务规则: BR-AUTH-001, BR-AUTH-002
- 数据表: DATA_SCHEMA.md 3.1.1节 `users`
- 错误码: ERROR_CODES_SOT.md 4.1节

#### 权限

- **允许角色**: 公开（无需认证）
- **业务约束**: 无

#### 并发控制

- **幂等性**: 否（每次调用返回新Token）
- **事务**: 无

#### 使用示例

**Frontend (TypeScript)**:
```typescript
import { apiFetch } from '@/lib/api';

const loginResult = await apiFetch('/api/v1/auth/login', {
  method: 'POST',
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'Password123!'
  })
});

// 存储Token
localStorage.setItem('access_token', loginResult.data.access_token);
```

---

### 5.3 GET `/api/v1/users` - 获取用户列表

#### 请求

**Query Parameters**:

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `page` | integer | 否 | 1 | 页码 |
| `page_size` | integer | 否 | 20 | 每页数量(1-100) |
| `role` | string | 否 | - | 角色过滤 |
| `is_active` | boolean | 否 | - | 账号状态过滤 |
| `search` | string | 否 | - | 搜索用户名或姓名 |

**Request示例**:
```http
GET /api/v1/users?page=1&page_size=20&role=pitcher&is_active=true
```

#### 响应

**Success (200 OK)**:

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "username": "john_doe",
        "full_name": "John Doe",
        "email": "user@example.com",
        "role": "pitcher",
        "department": "Marketing",
        "is_active": true,
        "created_at": "2025-01-01T00:00:00Z"
      }
    ],
    "meta": {
      "pagination": {
        "page": 1,
        "page_size": 20,
        "total": 100,
        "total_pages": 5,
        "has_next": true,
        "has_prev": false
      }
    }
  },
  "message": "查询成功",
  "code": "SUCCESS"
}
```

**Response Schema** (`data.items[i]`字段):

| 字段 | 类型 | 来源 | 说明 |
|------|------|------|------|
| `id` | UUID | `users.id` | 用户ID |
| `username` | string | `users.username` | 用户名 |
| `full_name` | string | `users.full_name` | 真实姓名 |
| `email` | string | `users.email` | 邮箱 |
| `role` | string | `users.role` | 角色（技术层 5 个值，见 §1.2.1 角色定义） |
| `department` | string | `users.department` | 部门 |
| `is_active` | boolean | `users.is_active` | 账号可用性 |
| `created_at` | ISO 8601 | `users.created_at` | 创建时间 |

**Error Responses**:

| 错误码 | HTTP状态码 | 触发场景 |
|--------|-----------|----------|
| `AUTH_500` | 403 | 非admin角色访问 |
| `VALIDATION_002` | 400 | role参数不在合法枚举值 |
| `SYS_001` | 500 | 系统内部错误 |

**引用**:
- 业务规则: BR-USER-001
- 数据表: DATA_SCHEMA.md 3.1.1节 `users`
- 错误码: ERROR_CODES_SOT.md

#### 权限

- **允许角色**: `admin`
- **业务约束**: 仅admin可查看全部用户

#### 并发控制

- **幂等性**: 是
- **事务**: 无

---

## 6. Projects API（项目管理）

### 6.1 端点总览

| 方法 | 路径 | 功能 | 权限 | 状态机 | 状态 |
|------|------|------|------|--------|------|
| GET | `/api/v1/projects` | 获取项目列表 | 所有已登录用户（RBAC过滤） | - | implemented |
| POST | `/api/v1/projects` | 创建项目 | `admin`, `account_manager` | `draft` | implemented |
| GET | `/api/v1/projects/{project_id}` | 获取项目详情 | 根据角色过滤 | - | implemented |
| PUT | `/api/v1/projects/{project_id}` | 更新项目 | `admin`, `account_manager`（仅管理的项目） | - | implemented |
| DELETE | `/api/v1/projects/{project_id}` | 删除项目 | `admin` | - | implemented |
| POST | `/api/v1/projects/{project_id}/members` | 分配项目成员 | `admin`, `account_manager` | - | implemented |
| GET | `/api/v1/projects/{project_id}/members` | 获取项目成员列表 | 根据角色过滤 | - | implemented |
| DELETE | `/api/v1/projects/{project_id}/members/{user_id}` | 移除项目成员 | `admin`, `account_manager` | - | implemented |

**状态机**: `draft` → `active` → `suspended` → `archived`（来自 STATE_MACHINE.md 第5章）

**引用**:
- 数据表: DATA_SCHEMA.md 3.2.1-3.2.3节
- 状态机: STATE_MACHINE.md 第5章
- 业务规则: BR-PROJ-001, BR-PROJ-003, BR-PROJ-004

### 6.2 POST `/api/v1/projects` - 创建项目

#### 请求

**Request Schema**:

| 字段 | 类型 | 必填 | 约束 | 默认值 | 说明 | 对应表字段 |
|------|------|------|------|--------|------|-----------|
| `name` | string | ✅ | 1-200字符 | - | 项目名称 | `projects.name` |
| `client_name` | string | ✅ | 1-200字符 | - | 客户联系人姓名 | `projects.client_name` |
| `client_company` | string | ✅ | 1-200字符 | - | 客户公司名称 | `projects.client_company` |
| `description` | string | 否 | ≤1000字符 | null | 项目描述 | `projects.description` |
| `budget_total` | string | 否 | DECIMAL(15,2), ≥0 | "0.00" | 项目总预算 | `projects.budget_total` |
| `budget_currency` | string | 否 | 3字符 | "CNY" | 货币类型 | `projects.budget_currency` |
| `unit_price` | string | 否 | DECIMAL(15,2), ≥0 | "0.00" | 单粉价格(Per Lead) | `projects.unit_price` |
| `start_date` | string | 否 | ISO 8601 date | null | 开始日期 | `projects.start_date` |
| `end_date` | string | 否 | ISO 8601 date | null | 结束日期 | `projects.end_date` |
| `account_manager_id` | string | 否 | UUID | null | 项目经理ID | `projects.account_manager_id` |

**Request示例**:
```json
{
  "name": "新项目",
  "client_name": "王五",
  "client_company": "示例公司",
  "description": "项目详细描述",
  "budget_total": "200000.00",
  "budget_currency": "USD",
  "unit_price": "50.00",
  "start_date": "2025-02-01",
  "end_date": "2025-12-31",
  "account_manager_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

#### 响应

**Success (201 Created)**:

```json
{
  "success": true,
  "data": {
    "id": 2,
    "name": "新项目",
    "client_name": "王五",
    "client_company": "示例公司",
    "description": "项目详细描述",
    "status": "draft",
    "budget_total": "200000.00",
    "budget_currency": "USD",
    "unit_price": "50.00",
    "start_date": "2025-02-01",
    "end_date": "2025-12-31",
    "account_manager_id": "550e8400-e29b-41d4-a716-446655440000",
    "account_manager_name": null,
    "created_by": "550e8400-e29b-41d4-a716-446655440001",
    "created_by_name": "管理员",
    "created_at": "2025-01-22T08:00:00Z",
    "updated_at": "2025-01-22T08:00:00Z"
  },
  "message": "项目创建成功",
  "code": "SUCCESS"
}
```

**Response Schema** (`data`字段):

| 字段 | 类型 | 来源 | 说明 |
|------|------|------|------|
| `id` | integer (BIGINT) | `projects.id` | 项目ID（主键） |
| `name` | string | `projects.name` | 项目名称 |
| `client_name` | string | `projects.client_name` | 客户联系人 |
| `client_company` | string | `projects.client_company` | 客户公司 |
| `description` | string | `projects.description` | 项目描述 |
| `status` | string | `projects.status` | 项目状态（初始为draft） |
| `budget_total` | string | `projects.budget_total` | 项目总预算 |
| `budget_currency` | string | `projects.budget_currency` | 货币类型 |
| `unit_price` | string | `projects.unit_price` | 单粉价格 |
| `start_date` | string | `projects.start_date` | 开始日期 |
| `end_date` | string | `projects.end_date` | 结束日期 |
| `account_manager_id` | UUID | `projects.account_manager_id` | 项目经理ID |
| `account_manager_name` | string | JOIN `users.full_name` | 项目经理姓名（聚合字段） |
| `created_by` | UUID | `projects.created_by` | 创建人ID |
| `created_by_name` | string | JOIN `users.full_name` | 创建人姓名（聚合字段） |
| `created_at` | ISO 8601 | `projects.created_at` | 创建时间 |
| `updated_at` | ISO 8601 | `projects.updated_at` | 更新时间 |

**Error Responses**:

| 错误码 | HTTP状态码 | 触发场景 |
|--------|-----------|----------|
| `AUTH_500` | 403 | 非admin/account_manager角色创建 |
| `BIZ_003` | 409 | 项目名称已存在 |
| `BIZ_200` | 400 | 开始日期晚于结束日期 |
| `VALIDATION_001` | 400 | 必填字段缺失 |
| `VALIDATION_002` | 400 | 字段格式无效 |
| `SYS_001` | 500 | 系统内部错误 |

**引用**:
- 业务规则: BR-PROJ-001（创建权限）
- 数据表: DATA_SCHEMA.md 3.2.1节
- 状态机: STATE_MACHINE.md 第5章（初始状态为draft）
- 错误码: ERROR_CODES_SOT.md

#### 权限

- **允许角色**: `admin`, `account_manager`
- **业务约束**:
  - BR-PROJ-001: 项目创建权限约束
  - 项目名称必须唯一
  - 如果指定account_manager_id，必须是有效用户且角色为account_manager

#### 并发控制

- **幂等性**: 否（每次调用创建新项目）
- **事务**: 单表INSERT，无跨表事务
- **唯一键**: `projects.name`（应用层校验+数据库UNIQUE索引）

#### 使用示例

**Frontend (TypeScript)**:
```typescript
import { apiFetch } from '@/lib/api';

const newProject = await apiFetch('/api/v1/projects', {
  method: 'POST',
  body: JSON.stringify({
    name: "新项目",
    client_name: "王五",
    client_company: "示例公司",
    budget_total: "200000.00",
    unit_price: "50.00"
  })
});
```

---

## 6A. Project Members API（项目成员）

### 6A.1 端点总览

| 方法 | 路径 | 功能 | 权限 | 状态 |
|------|------|------|------|------|
| GET | `/api/v1/projects/{project_id}/members` | 获取项目成员列表 | 项目相关角色 | implemented |
| POST | `/api/v1/projects/{project_id}/members` | 添加项目成员 | `admin`, `project_owner` | implemented |
| PUT | `/api/v1/projects/{project_id}/members/{member_id}` | 更新成员角色 | `admin`, `project_owner` | implemented |
| DELETE | `/api/v1/projects/{project_id}/members/{member_id}` | 移除成员 | `admin`, `project_owner` | implemented |

**引用**:
- 数据表: DATA_SCHEMA.md 3.2.3节 `project_members`
- 业务规则: BR-PROJ-003（项目成员管理）

### 6A.2 GET `/api/v1/projects/{project_id}/members` - 获取项目成员列表

#### 请求

**Path Parameters**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `project_id` | integer | ✅ | 项目ID |

**Query Parameters**:

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `page` | integer | 否 | 1 | 页码 |
| `page_size` | integer | 否 | 20 | 每页数量(1-100) |
| `role` | string | 否 | - | 按角色筛选 |

#### 响应

**Success (200 OK)**:

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": 1,
        "project_id": 101,
        "user_id": "550e8400-e29b-41d4-a716-446655440000",
        "user_name": "张三",
        "user_email": "zhangsan@example.com",
        "role": "pitcher",
        "joined_at": "2025-01-01T00:00:00Z",
        "created_at": "2025-01-01T00:00:00Z"
      }
    ],
    "meta": {
      "pagination": {
        "page": 1,
        "page_size": 20,
        "total": 5,
        "total_pages": 1
      }
    }
  },
  "message": "查询成功"
}
```

**Response Schema** (`data.items[i]`):

| 字段 | 类型 | 来源 | 说明 |
|------|------|------|------|
| `id` | integer | `project_members.id` | 成员记录ID |
| `project_id` | integer | `project_members.project_id` | 项目ID |
| `user_id` | UUID | `project_members.user_id` | 用户ID |
| `user_name` | string | JOIN `users.full_name` | 用户姓名 |
| `user_email` | string | JOIN `users.email` | 用户邮箱 |
| `role` | string | `project_members.role` | 成员角色 |
| `joined_at` | ISO 8601 | `project_members.joined_at` | 加入时间 |
| `created_at` | ISO 8601 | `project_members.created_at` | 记录创建时间 |

**Error Responses**:

| 错误码 | HTTP状态码 | 触发场景 |
|--------|-----------|----------|
| `BIZ_002` | 404 | project_id 不存在 |
| `AUTH_500` | 403 | 无权访问该项目 |

#### 权限

- **允许角色**: 项目相关角色（项目成员、`admin`）
- **业务约束**: 仅能查看自己所属项目的成员

### 6A.3 POST `/api/v1/projects/{project_id}/members` - 添加项目成员

#### 请求

**Path Parameters**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `project_id` | integer | ✅ | 项目ID |

**Request Schema**:

| 字段 | 类型 | 必填 | 约束 | 说明 | 对应表字段 |
|------|------|------|------|------|-----------|
| `user_id` | UUID | ✅ | 有效的用户ID | 要添加的用户 | `project_members.user_id` |
| `role` | string | ✅ | 见角色定义 | 成员角色 | `project_members.role` |

**Request示例**:
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "role": "pitcher"
}
```

#### 响应

**Success (201 Created)**:

```json
{
  "success": true,
  "data": {
    "id": 1,
    "project_id": 101,
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "role": "pitcher",
    "joined_at": "2025-01-22T10:00:00Z",
    "created_at": "2025-01-22T10:00:00Z"
  },
  "message": "成员添加成功"
}
```

**Error Responses**:

| 错误码 | HTTP状态码 | 触发场景 |
|--------|-----------|----------|
| `BIZ_002` | 404 | project_id 或 user_id 不存在 |
| `BIZ_003` | 409 | 用户已是项目成员 |
| `AUTH_500` | 403 | 无权限添加成员 |
| `VALIDATION_001` | 400 | 必填字段缺失 |

#### 权限

- **允许角色**: `admin`, `project_owner`
- **业务约束**:
  - 不能重复添加同一用户
  - project_owner 只能管理自己负责的项目

### 6A.4 PUT `/api/v1/projects/{project_id}/members/{member_id}` - 更新成员角色

#### 请求

**Path Parameters**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `project_id` | integer | ✅ | 项目ID |
| `member_id` | integer | ✅ | 成员记录ID |

**Request Schema**:

| 字段 | 类型 | 必填 | 约束 | 说明 |
|------|------|------|------|------|
| `role` | string | ✅ | 见角色定义 | 新角色 |

**Request示例**:
```json
{
  "role": "supervisor"
}
```

#### 响应

**Success (200 OK)**:

```json
{
  "success": true,
  "data": {
    "id": 1,
    "project_id": 101,
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "role": "supervisor",
    "updated_at": "2025-01-22T11:00:00Z"
  },
  "message": "成员角色更新成功"
}
```

**Error Responses**:

| 错误码 | HTTP状态码 | 触发场景 |
|--------|-----------|----------|
| `BIZ_002` | 404 | member_id 不存在 |
| `AUTH_500` | 403 | 无权限更新成员 |
| `VALIDATION_002` | 400 | role 不是合法值 |

#### 权限

- **允许角色**: `admin`, `project_owner`

### 6A.5 DELETE `/api/v1/projects/{project_id}/members/{member_id}` - 移除成员

#### 请求

**Path Parameters**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `project_id` | integer | ✅ | 项目ID |
| `member_id` | integer | ✅ | 成员记录ID |

#### 响应

**Success (200 OK)**:

```json
{
  "success": true,
  "data": null,
  "message": "成员已移除"
}
```

**Error Responses**:

| 错误码 | HTTP状态码 | 触发场景 |
|--------|-----------|----------|
| `BIZ_002` | 404 | member_id 不存在 |
| `AUTH_500` | 403 | 无权限移除成员 |
| `BIZ_001` | 400 | 不能移除 project_owner 自己 |

#### 权限

- **允许角色**: `admin`, `project_owner`
- **业务约束**:
  - 不能移除项目的最后一个 project_owner
  - project_owner 不能移除自己

---

## 7. Channels API（渠道管理）

### 7.1 端点总览

| 方法 | 路径 | 功能 | 权限 | 状态 |
|------|------|------|------|------|
| GET | `/api/v1/channels` | 获取渠道列表 | 所有已登录用户 | implemented |
| POST | `/api/v1/channels` | 创建渠道 | `admin`, `account_manager` | implemented |
| GET | `/api/v1/channels/{channel_id}` | 获取渠道详情 | 所有已登录用户 | implemented |
| PUT | `/api/v1/channels/{channel_id}` | 更新渠道 | `admin` | implemented |

**状态机**: `active` → `inactive`（来自 STATE_MACHINE.md 第6.1节）

**引用**:
- 数据表: DATA_SCHEMA.md 3.2.4节
- 状态机: STATE_MACHINE.md 第6.1节
- 业务规则: BR-CHAN-001

---

## 8. Ad Accounts API（广告账户）

### 8.1 端点总览

| 方法 | 路径 | 功能 | 权限 | 状态机 | 状态 |
|------|------|------|------|--------|------|
| GET | `/api/v1/ad-accounts` | 获取账户列表 | 根据角色过滤 | - | implemented |
| POST | `/api/v1/ad-accounts` | 创建账户 | `admin`, `account_manager` | `new` | implemented |
| GET | `/api/v1/ad-accounts/{account_id}` | 获取账户详情 | 根据角色过滤 | - | implemented |
| PUT | `/api/v1/ad-accounts/{account_id}` | 更新账户 | `admin`, `account_manager` | - | implemented |
| POST | `/api/v1/ad-accounts/{account_id}/assign` | 分配账户给投手 | `admin`, `account_manager` | - | implemented |
| POST | `/api/v1/ad-accounts/{account_id}/mark-dead` | 标记死号 | `admin`, `account_manager` | `dead` | implemented |
| POST | `/api/v1/ad-accounts/{account_id}/balance-transfer` | 死号余额迁移 | `admin`, `finance` | - | implemented |

**状态机**: `new` → `testing` → `active` → `suspended` → `dead` → `archived`（来自 STATE_MACHINE.md 第7.1节）

**引用**:
- 数据表: DATA_SCHEMA.md 3.2.9节
- 状态机: STATE_MACHINE.md 第7章
- 业务规则: BR-ACCT-001, BR-ACCT-002

---

## 9. Daily Reports API（日报管理）

### 9.1 端点总览

| 方法 | 路径 | 功能 | 权限 | 状态机 | 状态 |
|------|------|------|------|--------|------|
| GET | `/api/v1/daily-reports` | 获取日报列表 | 根据角色过滤 | - | implemented |
| POST | `/api/v1/daily-reports` | 提交日报（raw粉数） | `pitcher` | `raw_submitted` | implemented |
| GET | `/api/v1/daily-reports/{report_id}` | 获取日报详情 | 根据角色过滤 | - | implemented |
| PUT | `/api/v1/daily-reports/{report_id}` | 更新日报（仅草稿） | `pitcher`（仅自己的） | - | implemented |
| POST | `/api/v1/daily-reports/{report_id}/trend-check` | 趋势风控检查 | 系统自动 | `trend_pending` → `trend_ok`/`trend_flagged` | implemented |
| POST | `/api/v1/daily-reports/{report_id}/trend-resolve` | 趋势风控复核 | `supervisor`, `admin` | `trend_flagged` → `trend_resolved` | implemented |
| PUT | `/api/v1/daily-reports/{report_id}/real-spend` | 录入real粉数 | `supervisor`, `admin` | `trend_ok`/`trend_resolved` → `final_pending` | implemented |
| POST | `/api/v1/daily-reports/{report_id}/final-confirm` | 确认final粉数 | `supervisor`, `admin` | `final_pending` → `final_confirmed` | implemented |
| POST | `/api/v1/daily-reports/{report_id}/final-lock` | 计费锁定 | 系统自动 | `final_confirmed` → `final_locked` | implemented |
| POST | `/api/v1/daily-reports/{report_id}/reversal` | 红冲修正 | `admin` | `final_locked` → (创建REVERSAL记录) | implemented |

**粉数确认状态机（8状态）**:
```
raw_submitted → trend_pending → trend_ok/trend_flagged → trend_resolved →
final_pending → final_confirmed → final_locked
```

**引用**:
- 数据表: DATA_SCHEMA.md 3.3.1节
- 状态机: STATE_MACHINE.md 第8章（粉数确认状态机）
- 业务规则: BR-RPT-001, BR-RPT-002, BR-RPT-004, BR-RPT-005
- 三数据流: MASTER.md v4.4 §4

### 9.2 POST `/api/v1/daily-reports` - 提交日报（raw粉数）

#### 请求

**Request Schema**:

| 字段 | 类型 | 必填 | 约束 | 默认值 | 说明 | 对应表字段 |
|------|------|------|------|--------|------|-----------|
| `report_date` | string | ✅ | ISO 8601 date, ≤今天 | - | 日报日期 | `daily_reports.report_date` |
| `ad_account_id` | integer | ✅ | BIGINT, 存在的账户ID | - | 广告账户ID | `daily_reports.ad_account_id` |
| `campaign_name` | string | 否 | ≤200字符 | null | 广告系列名称 | `daily_reports.campaign_name` |
| `ad_group_name` | string | 否 | ≤200字符 | null | 广告组名称 | `daily_reports.ad_group_name` |
| `ad_creative_name` | string | 否 | ≤200字符 | null | 广告创意名称 | `daily_reports.ad_creative_name` |
| `impressions` | integer | 否 | ≥0 | 0 | 曝光量 | `daily_reports.impressions` |
| `clicks` | integer | 否 | ≥0 | 0 | 点击量 | `daily_reports.clicks` |
| `conversions_raw` | integer | ✅ | ≥0 | - | 原始粉数（raw数据流） | `daily_reports.conversions_raw` |
| `raw_spend` | string | ✅ | DECIMAL(15,2), ≥0 | - | 原始消耗（raw数据流） | `daily_reports.raw_spend` |
| `notes` | string | 否 | ≤1000字符 | null | 备注 | `daily_reports.notes` |

**Request示例**:
```json
{
  "report_date": "2025-01-21",
  "ad_account_id": 123,
  "campaign_name": "春节推广",
  "conversions_raw": 100,
  "raw_spend": "5000.00",
  "impressions": 50000,
  "clicks": 1200,
  "notes": "数据正常"
}
```

#### 响应

**Success (201 Created)**:

```json
{
  "success": true,
  "data": {
    "id": 456,
    "report_date": "2025-01-21",
    "ad_account_id": 123,
    "ad_account_name": "FB账户001",
    "project_id": 1,
    "project_name": "春节项目",
    "status": "raw_submitted",
    "conversions_raw": 100,
    "raw_spend": "5000.00",
    "conversions_final": 0,
    "real_spend": "0.00",
    "unit_price": "50.00",
    "trend_flag": "normal",
    "trend_flag_reason": null,
    "impressions": 50000,
    "clicks": 1200,
    "notes": "数据正常",
    "created_by": "550e8400-e29b-41d4-a716-446655440000",
    "created_by_name": "投手小王",
    "created_at": "2025-01-22T10:00:00Z",
    "updated_at": "2025-01-22T10:00:00Z"
  },
  "message": "日报提交成功，等待趋势风控检查",
  "code": "SUCCESS"
}
```

**Response Schema** (`data`字段):

| 字段 | 类型 | 来源 | 说明 |
|------|------|------|------|
| `id` | integer (BIGINT) | `daily_reports.id` | 日报ID（主键） |
| `report_date` | string | `daily_reports.report_date` | 日报日期 |
| `ad_account_id` | integer | `daily_reports.ad_account_id` | 广告账户ID |
| `ad_account_name` | string | JOIN `ad_accounts.name` | 账户名称（聚合字段） |
| `project_id` | integer | JOIN `ad_accounts.project_id` | 项目ID（聚合字段） |
| `project_name` | string | JOIN `projects.name` | 项目名称（聚合字段） |
| `status` | string | `daily_reports.status` | 状态（raw_submitted） |
| `conversions_raw` | integer | `daily_reports.conversions_raw` | 原始粉数（raw） |
| `raw_spend` | string | `daily_reports.raw_spend` | 原始消耗（raw） |
| `conversions_final` | integer | `daily_reports.conversions_final` | 最终粉数（未确认时为0） |
| `real_spend` | string | `daily_reports.real_spend` | 真实消耗（未录入时为0.00） |
| `unit_price` | string | `daily_reports.unit_price` | 单粉价格（从项目继承） |
| `trend_flag` | string | `daily_reports.trend_flag` | 趋势标记（normal/flagged/resolved） |
| `trend_flag_reason` | string | `daily_reports.trend_flag_reason` | 异常原因（如TF-001） |
| `impressions` | integer | `daily_reports.impressions` | 曝光量 |
| `clicks` | integer | `daily_reports.clicks` | 点击量 |
| `notes` | string | `daily_reports.notes` | 备注 |
| `created_by` | UUID | `daily_reports.created_by` | 创建人ID |
| `created_by_name` | string | JOIN `users.full_name` | 创建人姓名 |
| `created_at` | ISO 8601 | `daily_reports.created_at` | 创建时间 |
| `updated_at` | ISO 8601 | `daily_reports.updated_at` | 更新时间 |

**Error Responses**:

| 错误码 | HTTP状态码 | 触发场景 |
|--------|-----------|----------|
| `AUTH_500` | 403 | 非 pitcher 角色提交 |
| `BIZ_003` | 409 | (ad_account_id, report_date)重复 |
| `BIZ_201` | 400 | report_date大于今天 |
| `BIZ_002` | 404 | ad_account_id不存在 |
| `VALIDATION_001` | 400 | 必填字段缺失 |
| `SYS_001` | 500 | 系统内部错误 |

**引用**:
- 业务规则: BR-RPT-001（提交约束）, BR-RPT-005（粉数确认流程）
- 数据表: DATA_SCHEMA.md 3.3.1节
- 状态机: STATE_MACHINE.md 第8章
- 三数据流: MASTER.md v4.4 §4

#### 权限

- **允许角色**: `pitcher`
- **业务约束**:
  - BR-RPT-001: 日报提交约束
  - 唯一键: (ad_account_id, report_date)
  - report_date不能为未来日期
  - 投手只能提交自己负责账户的日报

#### 并发控制

- **幂等性**: 是（唯一键冲突时返回409）
- **事务**: 单表INSERT
- **唯一键**: `(ad_account_id, report_date)`（应用层校验+数据库UNIQUE索引）

#### 状态流转

```
初始状态: raw_submitted
自动触发: 系统异步调用 POST /daily-reports/{id}/trend-check
```

#### 使用示例

**Frontend (TypeScript)**:
```typescript
import { apiFetch } from '@/lib/api';

const newReport = await apiFetch('/api/v1/daily-reports', {
  method: 'POST',
  body: JSON.stringify({
    report_date: "2025-01-21",
    ad_account_id: 123,
    conversions_raw: 100,
    raw_spend: "5000.00",
    impressions: 50000,
    clicks: 1200
  })
});

// 提交后系统自动触发趋势风控检查
// 前端可轮询查询状态或通过WebSocket接收状态变更通知
```

---

### 9.3 POST `/api/v1/daily-reports/{report_id}/trend-check` - 趋势风控检查

#### 请求

**Path Parameters**:

| 参数 | 类型 | 说明 |
|------|------|------|
| `report_id` | integer | 日报ID |

**Request Body**: 无

#### 响应

**Success (200 OK) - 趋势正常**:

```json
{
  "success": true,
  "data": {
    "id": 456,
    "status": "trend_ok",
    "trend_flag": "normal",
    "trend_flag_reason": null,
    "conversions_raw": 100,
    "raw_spend": "5000.00"
  },
  "message": "趋势检查通过",
  "code": "SUCCESS"
}
```

**Success (200 OK) - 趋势异常**:

```json
{
  "success": true,
  "data": {
    "id": 456,
    "status": "trend_flagged",
    "trend_flag": "flagged",
    "trend_flag_reason": "TF-001: 粉数骤降50%（昨日最大值200，今日100）",
    "conversions_raw": 100,
    "raw_spend": "5000.00",
    "yesterday_max_conversions": 200
  },
  "message": "趋势异常，需要人工复核",
  "code": "TREND_001"
}
```

**Response Schema** (`data`字段):

| 字段 | 类型 | 来源 | 说明 |
|------|------|------|------|
| `id` | integer | `daily_reports.id` | 日报ID |
| `status` | string | `daily_reports.status` | 状态（trend_ok/trend_flagged） |
| `trend_flag` | string | `daily_reports.trend_flag` | 趋势标记 |
| `trend_flag_reason` | string | `daily_reports.trend_flag_reason` | 异常原因（如果有） |
| `conversions_raw` | integer | `daily_reports.conversions_raw` | 原始粉数 |
| `raw_spend` | string | `daily_reports.raw_spend` | 原始消耗 |
| `yesterday_max_conversions` | integer | 计算字段 | 昨日最大粉数（仅异常时返回） |

**Error Responses**:

| 错误码 | HTTP状态码 | 触发场景 |
|--------|-----------|----------|
| `BIZ_002` | 404 | 日报不存在 |
| `STATE_400` | 400 | 当前状态不是raw_submitted |
| `SYS_001` | 500 | 系统内部错误 |

**引用**:
- 业务规则: BR-RPT-005（趋势风控规则）
- 状态机: STATE_MACHINE.md 第8.3节（TF-001/002/003规则）
- 错误码: ERROR_CODES_SOT.md 4.7节（TREND_001）

#### 权限

- **允许角色**: 系统自动（异步任务）
- **业务约束**:
  - 仅当status=raw_submitted时可执行
  - 检查三个规则:
    - TF-001: `conversions_raw < 昨日最大值 × 0.5`
    - TF-002: `conversions_raw > 昨日最大值 × 3`
    - TF-003: `raw_spend > 昨日 × 2`

#### 并发控制

- **幂等性**: 是（可重复调用）
- **事务**: 单表UPDATE
- **锁**: 使用乐观锁（version字段）

#### 状态流转

```
当前状态: raw_submitted
成功流转:
  - trend_ok（通过检查）
  - trend_flagged（异常检查）
```

#### 趋势风控算法

```python
# 伪代码示例
def check_trend_risk(report: DailyReport):
    yesterday_max = get_yesterday_max_conversions(report.ad_account_id)

    # TF-001: 粉数骤降
    if report.conversions_raw < yesterday_max * 0.5:
        report.status = "trend_flagged"
        report.trend_flag = "flagged"
        report.trend_flag_reason = f"TF-001: 粉数骤降50%（昨日最大值{yesterday_max}，今日{report.conversions_raw}）"
        return TrendErrorCodes.TREND_RISK_TRIGGERED  # TREND_001

    # TF-002: 粉数骤增
    if report.conversions_raw > yesterday_max * 3:
        report.status = "trend_flagged"
        report.trend_flag = "flagged"
        report.trend_flag_reason = f"TF-002: 粉数骤增200%（昨日最大值{yesterday_max}，今日{report.conversions_raw}）"
        return TrendErrorCodes.TREND_RISK_TRIGGERED  # TREND_001

    # TF-003: 消耗异常
    yesterday_spend = get_yesterday_spend(report.ad_account_id)
    if report.raw_spend > yesterday_spend * 2:
        report.status = "trend_flagged"
        report.trend_flag = "flagged"
        report.trend_flag_reason = f"TF-003: 消耗异常（昨日{yesterday_spend}，今日{report.raw_spend}）"
        return TrendErrorCodes.TREND_RISK_TRIGGERED  # TREND_001

    # 通过检查
    report.status = "trend_ok"
    report.trend_flag = "normal"
    return "SUCCESS"
```

---

### 9.4 POST `/api/v1/daily-reports/{report_id}/trend-resolve` - 趋势风控复核

#### 请求

**Path Parameters**:

| 参数 | 类型 | 说明 |
|------|------|------|
| `report_id` | integer | 日报ID |

**Request Schema**:

| 字段 | 类型 | 必填 | 说明 | 对应表字段 |
|------|------|------|------|-----------|
| `trend_resolution_note` | string | ✅ | 运营复核说明 | `daily_reports.trend_resolution_note` |
| `confirmed_normal` | boolean | ✅ | 是否确认正常 | - |

**Request示例**:
```json
{
  "trend_resolution_note": "已联系投手确认，粉数骤降是因为周末流量下降，属于正常波动",
  "confirmed_normal": true
}
```

#### 响应

**Success (200 OK)**:

```json
{
  "success": true,
  "data": {
    "id": 456,
    "status": "trend_resolved",
    "trend_flag": "resolved",
    "trend_flag_reason": "TF-001: 粉数骤降50%（昨日最大值200，今日100）",
    "trend_resolution_note": "已联系投手确认，粉数骤降是因为周末流量下降，属于正常波动"
  },
  "message": "趋势复核完成",
  "code": "SUCCESS"
}
```

**Error Responses**:

| 错误码 | HTTP状态码 | 触发场景 |
|--------|-----------|----------|
| `AUTH_500` | 403 | 非 supervisor/admin 角色 |
| `BIZ_002` | 404 | 日报不存在 |
| `STATE_400` | 400 | 当前状态不是trend_flagged |
| `VALIDATION_001` | 400 | 未填写复核说明 |
| `SYS_001` | 500 | 系统内部错误 |

**引用**:
- 业务规则: BR-RPT-005（复核流程）
- 状态机: STATE_MACHINE.md 第8.2节

#### 权限

- **允许角色**: `supervisor`, `admin`
- **业务约束**:
  - 仅当status=trend_flagged时可执行
  - 必须填写trend_resolution_note

#### 并发控制

- **幂等性**: 否（每次调用更新复核说明）
- **事务**: 单表UPDATE
- **审计日志**: 必须记录（[AUDIT]）

#### 状态流转

```
当前状态: trend_flagged
成功流转:
  - trend_resolved（confirmed_normal=true）
  - raw_submitted（confirmed_normal=false，要求投手重新提交）
```

---

### 9.5 PUT `/api/v1/daily-reports/{report_id}/real-spend` - 录入real粉数

#### 请求

**Path Parameters**:

| 参数 | 类型 | 说明 |
|------|------|------|
| `report_id` | integer | 日报ID |

**Request Schema**:

| 字段 | 类型 | 必填 | 约束 | 说明 | 对应表字段 |
|------|------|------|------|------|-----------|
| `real_spend` | string | ✅ | DECIMAL(15,2), ≥0 | 真实消耗（运营从供应商后台获取） | `daily_reports.real_spend` |
| `fee` | string | 否 | DECIMAL(15,2), ≥0 | 手续费（默认0.00） | `daily_reports.fee` |

**Request示例**:
```json
{
  "real_spend": "4800.00",
  "fee": "0.00"
}
```

#### 响应

**Success (200 OK)**:

```json
{
  "success": true,
  "data": {
    "id": 456,
    "status": "final_pending",
    "real_spend": "4800.00",
    "fee": "0.00",
    "conversions_raw": 100,
    "conversions_final": 0
  },
  "message": "真实消耗已录入，等待确认final粉数",
  "code": "SUCCESS"
}
```

**Error Responses**:

| 错误码 | HTTP状态码 | 触发场景 |
|--------|-----------|----------|
| `AUTH_500` | 403 | 非 supervisor/admin 角色 |
| `BIZ_002` | 404 | 日报不存在 |
| `STATE_400` | 400 | 当前状态不是trend_ok/trend_resolved |
| `TREND_002` | 400 | 当前状态为trend_flagged，禁止录入 |
| `VALIDATION_001` | 400 | 必填字段缺失 |
| `SYS_001` | 500 | 系统内部错误 |

**引用**:
- 业务规则: BR-RPT-005（real数据流）
- 数据表: DATA_SCHEMA.md 3.3.1节
- 状态机: STATE_MACHINE.md 第8.4节

#### 权限

- **允许角色**: `supervisor`, `admin`
- **业务约束**:
  - 仅当status=trend_ok或trend_resolved时可执行
  - 禁止在trend_flagged状态下录入
  - real_spend从供应商后台获取，T+1日12:00前录入

#### 并发控制

- **幂等性**: 是（可覆盖更新）
- **事务**: 单表UPDATE

#### 状态流转

```
当前状态: trend_ok / trend_resolved
成功流转: final_pending
```

---

### 9.6 POST `/api/v1/daily-reports/{report_id}/final-confirm` - 确认final粉数

#### 请求

**Path Parameters**:

| 参数 | 类型 | 说明 |
|------|------|------|
| `report_id` | integer | 日报ID |

**Request Schema**:

| 字段 | 类型 | 必填 | 约束 | 说明 | 对应表字段 |
|------|------|------|------|------|-----------|
| `conversions_final` | integer | ✅ | ≥0 | 最终粉数（运营确认） | `daily_reports.conversions_final` |
| `final_confirm_note` | string | 否 | ≤500字符 | 确认说明 | `daily_reports.notes` |

**Request示例**:
```json
{
  "conversions_final": 95,
  "final_confirm_note": "运营审核后剔除5个无效线索，最终确认95粉"
}
```

#### 响应

**Success (200 OK)**:

```json
{
  "success": true,
  "data": {
    "id": 456,
    "status": "final_confirmed",
    "conversions_raw": 100,
    "conversions_final": 95,
    "real_spend": "4800.00",
    "unit_price": "50.00",
    "estimated_revenue": "4750.00"
  },
  "message": "final粉数已确认，等待系统计费锁定",
  "code": "SUCCESS"
}
```

**Response Schema** (`data`字段):

| 字段 | 类型 | 来源 | 说明 |
|------|------|------|------|
| `id` | integer | `daily_reports.id` | 日报ID |
| `status` | string | `daily_reports.status` | 状态（final_confirmed） |
| `conversions_raw` | integer | `daily_reports.conversions_raw` | 原始粉数 |
| `conversions_final` | integer | `daily_reports.conversions_final` | 最终粉数 |
| `real_spend` | string | `daily_reports.real_spend` | 真实消耗 |
| `unit_price` | string | `daily_reports.unit_price` | 单粉价格 |
| `estimated_revenue` | string | 计算字段 | 预估收入（conversions_final × unit_price） |

**Error Responses**:

| 错误码 | HTTP状态码 | 触发场景 |
|--------|-----------|----------|
| `AUTH_500` | 403 | 非 supervisor/admin 角色 |
| `BIZ_002` | 404 | 日报不存在 |
| `STATE_400` | 400 | 当前状态不是final_pending |
| `VALIDATION_001` | 400 | 必填字段缺失 |
| `SYS_001` | 500 | 系统内部错误 |

**引用**:
- 业务规则: BR-RPT-005（final数据流）
- 数据表: DATA_SCHEMA.md 3.3.1节
- 状态机: STATE_MACHINE.md 第8.2节

#### 权限

- **允许角色**: `supervisor`, `admin`
- **业务约束**:
  - 仅当status=final_pending时可执行
  - conversions_final可以≠conversions_raw（允许运营调整）
  - 确认后不可修改（除红冲外）

#### 并发控制

- **幂等性**: 否（确认一次后不可重复）
- **事务**: 单表UPDATE
- **审计日志**: 必须记录（[AUDIT]）

#### 状态流转

```
当前状态: final_pending
成功流转: final_confirmed
自动触发: 系统异步调用 POST /daily-reports/{id}/final-lock
```

---

### 9.7 POST `/api/v1/daily-reports/{report_id}/final-lock` - 计费锁定

#### 请求

**Path Parameters**:

| 参数 | 类型 | 说明 |
|------|------|------|
| `report_id` | integer | 日报ID |

**Request Body**: 无

#### 响应

**Success (200 OK)**:

```json
{
  "success": true,
  "data": {
    "id": 456,
    "status": "final_locked",
    "conversions_final": 95,
    "real_spend": "4800.00",
    "unit_price": "50.00",
    "revenue": "4750.00",
    "cost": "4800.00",
    "profit": "-50.00",
    "final_locked_at": "2025-01-22T14:00:00Z",
    "ledger_entries": [
      {
        "id": 789,
        "ledger_type": "PROJECT",
        "entry_type": "REVENUE",
        "amount": "4750.00",
        "project_id": 1
      },
      {
        "id": 790,
        "ledger_type": "SUPPLIER",
        "entry_type": "COST",
        "amount": "4800.00",
        "supplier_id": "550e8400-e29b-41d4-a716-446655440002"
      }
    ]
  },
  "message": "计费锁定成功，已生成Ledger记录",
  "code": "SUCCESS"
}
```

**Response Schema** (`data`字段):

| 字段 | 类型 | 来源 | 说明 |
|------|------|------|------|
| `id` | integer | `daily_reports.id` | 日报ID |
| `status` | string | `daily_reports.status` | 状态（final_locked） |
| `conversions_final` | integer | `daily_reports.conversions_final` | 最终粉数 |
| `real_spend` | string | `daily_reports.real_spend` | 真实消耗 |
| `unit_price` | string | `daily_reports.unit_price` | 单粉价格 |
| `revenue` | string | 计算字段 | 收入（conversions_final × unit_price） |
| `cost` | string | 计算字段 | 成本（real_spend + fee） |
| `profit` | string | 计算字段 | 毛利（revenue - cost） |
| `final_locked_at` | ISO 8601 | `daily_reports.final_locked_at` | 锁定时间戳 |
| `ledger_entries` | array | 聚合字段 | 生成的Ledger记录 |

**Error Responses**:

| 错误码 | HTTP状态码 | 触发场景 |
|--------|-----------|----------|
| `BIZ_002` | 404 | 日报不存在 |
| `STATE_400` | 400 | 当前状态不是final_confirmed |
| `SYS_001` | 500 | 系统内部错误 |

**引用**:
- 业务规则: BR-RPT-004（终态保护）, BR-RPT-005（计费锁定）
- 数据表: DATA_SCHEMA.md 3.3.1, 3.4.4节
- 双账本: LEDGER_SOT.md v1.1

#### 权限

- **允许角色**: 系统自动（异步任务）
- **业务约束**:
  - 仅当status=final_confirmed时可执行
  - 必须在单个事务内完成:
    1. UPDATE daily_reports SET status='final_locked', final_locked_at=NOW()
    2. INSERT ledger_entries (PROJECT账本, REVENUE)
    3. INSERT ledger_entries (SUPPLIER账本, COST)
    4. INSERT daily_report_audit_logs

#### 并发控制

- **幂等性**: 是（锁定一次后不可重复）
- **事务**: 跨表事务（daily_reports + ledger_entries）
- **锁**: 使用 `SELECT FOR UPDATE` 锁定daily_reports和project记录

#### 事务边界

```python
# 伪代码示例
with db.begin():
    # 1. 锁定日报记录
    report = db.query(DailyReport).filter(...).with_for_update().first()

    # 2. 锁定项目记录（更新余额）
    project = db.query(Project).filter(...).with_for_update().first()

    # 3. 计算收入和成本
    revenue = report.conversions_final * report.unit_price
    cost = report.real_spend + report.fee

    # 4. 生成PROJECT账本记录
    project_entry = LedgerEntry(
        ledger_type="PROJECT",
        entry_type="REVENUE",
        amount=revenue,
        project_id=project.id,
        reference_id=report.id
    )
    db.add(project_entry)

    # 5. 生成SUPPLIER账本记录
    supplier_entry = LedgerEntry(
        ledger_type="SUPPLIER",
        entry_type="COST",
        amount=cost,
        supplier_id=ad_account.supplier_id,
        reference_id=report.id
    )
    db.add(supplier_entry)

    # 6. 更新日报状态
    report.status = "final_locked"
    report.final_locked_at = datetime.utcnow()

    # 7. 记录审计日志
    audit_log = DailyReportAuditLog(
        daily_report_id=report.id,
        old_status="final_confirmed",
        new_status="final_locked",
        audit_user_id=None,  # system
        audit_notes=f"计费锁定: 收入{revenue}, 成本{cost}"
    )
    db.add(audit_log)

    db.commit()
```

#### 状态流转

```
当前状态: final_confirmed
成功流转: final_locked（终态）
```

---

### 9.8 POST `/api/v1/daily-reports/{report_id}/reversal` - 红冲修正

#### 请求

**Path Parameters**:

| 参数 | 类型 | 说明 |
|------|------|------|
| `report_id` | integer | 日报ID |

**Request Schema**:

| 字段 | 类型 | 必填 | 约束 | 说明 |
|------|------|------|------|------|
| `corrected_conversions_final` | integer | ✅ | ≥0 | 修正后的final粉数 |
| `reversal_reason` | string | ✅ | ≥20字符 | 红冲原因（必须详细说明） |

**Request示例**:
```json
{
  "corrected_conversions_final": 90,
  "reversal_reason": "发现5粉为重复线索，需要从95调整为90，已与客户确认"
}
```

#### 响应

**Success (200 OK)**:

```json
{
  "success": true,
  "data": {
    "id": 456,
    "status": "final_locked",
    "conversions_final_before": 95,
    "conversions_final_after": 90,
    "revenue_before": "4750.00",
    "revenue_after": "4500.00",
    "reversal_entries": [
      {
        "id": 791,
        "ledger_type": "PROJECT",
        "entry_type": "REVERSAL",
        "amount": "-4750.00",
        "notes": "红冲原记录#789，粉数错误"
      },
      {
        "id": 792,
        "ledger_type": "PROJECT",
        "entry_type": "REVENUE",
        "amount": "4500.00",
        "notes": "修正后的正确记录（90粉）"
      }
    ]
  },
  "message": "红冲修正成功",
  "code": "SUCCESS"
}
```

**Error Responses**:

| 错误码 | HTTP状态码 | 触发场景 |
|--------|-----------|----------|
| `AUTH_500` | 403 | 非admin角色 |
| `BIZ_002` | 404 | 日报不存在 |
| `STATE_402` | 400 | 当前状态不是final_locked |
| `VALIDATION_001` | 400 | 必填字段缺失 |
| `SYS_001` | 500 | 系统内部错误 |

**引用**:
- 业务规则: BR-RPT-004（终态保护）
- 状态机: STATE_MACHINE.md 第8.8节（红冲机制）
- 数据表: DATA_SCHEMA.md 3.4.4节

#### 权限

- **允许角色**: `admin`
- **业务约束**:
  - 仅当status=final_locked时可执行
  - 必须填写详细的reversal_reason（≥20字符）
  - 红冲金额 = -原金额
  - 必须生成新的正确Ledger记录

#### 并发控制

- **幂等性**: 否（每次调用创建新红冲记录）
- **事务**: 跨表事务（daily_reports + ledger_entries）
- **锁**: 使用 `SELECT FOR UPDATE` 锁定daily_reports和project记录
- **审计日志**: 必须记录（[AUDIT]强制）

#### 事务边界

```python
# 伪代码示例
with db.begin():
    # 1. 锁定日报记录
    report = db.query(DailyReport).filter(...).with_for_update().first()

    # 2. 锁定项目记录
    project = db.query(Project).filter(...).with_for_update().first()

    # 3. 查找原Ledger记录
    original_entry = db.query(LedgerEntry).filter(
        ledger_type="PROJECT",
        entry_type="REVENUE",
        reference_id=report.id
    ).first()

    # 4. 创建红冲记录
    reversal_entry = LedgerEntry(
        ledger_type="PROJECT",
        entry_type="REVERSAL",
        amount=-original_entry.amount,
        project_id=project.id,
        reference_id=original_entry.id,
        notes=f"红冲原记录#{original_entry.id}，{reversal_reason}"
    )
    db.add(reversal_entry)

    # 5. 生成新的正确记录
    corrected_revenue = corrected_conversions_final * report.unit_price
    new_entry = LedgerEntry(
        ledger_type="PROJECT",
        entry_type="REVENUE",
        amount=corrected_revenue,
        project_id=project.id,
        reference_id=report.id,
        notes=f"修正后的正确记录（{corrected_conversions_final}粉）"
    )
    db.add(new_entry)

    # 6. 更新项目余额（原子操作）
    balance_adjustment = corrected_revenue - original_entry.amount
    project.balance = project.balance + balance_adjustment

    # 7. 记录审计日志
    audit_log = DailyReportAuditLog(
        daily_report_id=report.id,
        action="reversal",
        audit_user_id=current_user.id,
        audit_notes=f"红冲修正: {original_entry.amount} → {corrected_revenue}, 原因: {reversal_reason}"
    )
    db.add(audit_log)

    db.commit()
```

---

## 10. Topup Requests API（充值申请）

### 10.1 端点总览

| 方法 | 路径 | 功能 | 权限 | 状态机 | 状态 |
|------|------|------|------|--------|------|
| GET | `/api/v1/topups` | 获取充值申请列表 | 根据角色过滤 | - | implemented |
| POST | `/api/v1/topups` | 创建充值申请 | `admin`, `finance`, `pitcher`, `account_manager` | `draft` | implemented |
| GET | `/api/v1/topups/{request_id}` | 获取充值申请详情 | 根据角色过滤 | - | implemented |
| POST | `/api/v1/topups/{request_id}/submit` | 提交审批 | 申请人 | `draft` → `pending_review` | implemented |
| POST | `/api/v1/topups/{request_id}/review` | 数据审核 | `supervisor`, `admin` | `pending_review` → `finance_approve` | implemented |
| POST | `/api/v1/topups/{request_id}/approve` | 财务审批 | `finance`, `admin` | `finance_approve` → `paid` | implemented |
| PUT | `/api/v1/topups/{request_id}/pay` | 记录付款 | `finance`, `admin` | `paid` → - | implemented |
| POST | `/api/v1/topups/{request_id}/confirm-paid` | 到账确认 | `finance`, `admin` | `paid` → `completed` | implemented |
| POST | `/api/v1/topups/{request_id}/reject` | 拒绝申请 | `supervisor`, `finance`, `admin` | 任意状态 → `rejected` | implemented |
| POST | `/api/v1/topups/{request_id}/cancel` | 取消申请 | 申请人 | `draft` → `cancelled` | implemented |
| GET | `/api/v1/topups/{request_id}/logs` | 获取审批日志 | 所有已登录用户 | - | implemented |
| GET | `/api/v1/topups/statistics` | 获取充值统计 | `admin`, `finance` | - | implemented |
| GET | `/api/v1/topups/dashboard` | 获取仪表盘数据 | 所有已登录用户 | - | implemented |
| GET | `/api/v1/topups/accounts/{account_id}/balance` | 获取账户余额 | 所有已登录用户 | - | implemented |
| GET | `/api/v1/topups/export` | 导出充值数据 | `admin`, `finance` | - | implemented |
| POST | `/api/v1/topups/{request_id}/receipt` | 上传付款凭证 | `finance`, `admin` | - | implemented |

**充值状态机**: `draft` → `pending_review` → `finance_approve` → `paid` → `completed`（来自 STATE_MACHINE.md 第9章）

**引用**:
- 数据表: DATA_SCHEMA.md 3.4.1-3.4.3节
- 状态机: STATE_MACHINE.md 第9章
- 业务规则: BR-FIN-001, BR-FIN-002, BR-FIN-005

### 10.2 POST `/api/v1/topups` - 创建充值申请

#### 请求

**Request Schema**:

| 字段 | 类型 | 必填 | 约束 | 默认值 | 说明 | 对应表字段 |
|------|------|------|------|--------|------|-----------|
| `project_id` | integer | ✅ | BIGINT, 存在的项目ID | - | 项目ID | `topup_requests.project_id` |
| `ad_account_id` | integer | 否 | BIGINT, 存在的账户ID | null | 广告账户ID | `topup_requests.ad_account_id` |
| `amount` | string | ✅ | DECIMAL(15,2), ≥100, ≤1000000 | - | 充值金额 | `topup_requests.amount` |
| `currency` | string | 否 | 3字符 | "CNY" | 货币类型 | `topup_requests.currency` |
| `urgency_level` | string | 否 | Enum: low/normal/high/urgent | "normal" | 紧急程度 | `topup_requests.urgency_level` |
| `expected_pay_date` | string | 否 | ISO 8601 date | null | 期望到账日期 | `topup_requests.expected_pay_date` |
| `notes` | string | 否 | ≤1000字符 | null | 申请说明 | `topup_requests.notes` |

**Request示例**:
```json
{
  "project_id": 1,
  "ad_account_id": 123,
  "amount": "10000.00",
  "currency": "CNY",
  "urgency_level": "high",
  "expected_pay_date": "2025-01-25",
  "notes": "Facebook广告账户余额不足，需要补充推广预算"
}
```

#### 响应

**Success (201 Created)**:

```json
{
  "success": true,
  "data": {
    "id": 789,
    "request_no": "TOPUP-2025-01-22-0001",
    "project_id": 1,
    "project_name": "春节项目",
    "ad_account_id": 123,
    "ad_account_name": "FB账户001",
    "applicant_id": "550e8400-e29b-41d4-a716-446655440000",
    "applicant_name": "投手小王",
    "amount": "10000.00",
    "currency": "CNY",
    "urgency_level": "high",
    "status": "draft",
    "expected_pay_date": "2025-01-25",
    "notes": "Facebook广告账户余额不足，需要补充推广预算",
    "created_at": "2025-01-22T10:00:00Z",
    "updated_at": "2025-01-22T10:00:00Z"
  },
  "message": "充值申请已创建",
  "code": "SUCCESS"
}
```

**Response Schema** (`data`字段):

| 字段 | 类型 | 来源 | 说明 |
|------|------|------|------|
| `id` | integer (BIGINT) | `topup_requests.id` | 申请ID（主键） |
| `request_no` | string | `topup_requests.request_no` | 申请编号（唯一） |
| `project_id` | integer | `topup_requests.project_id` | 项目ID |
| `project_name` | string | JOIN `projects.name` | 项目名称（聚合字段） |
| `ad_account_id` | integer | `topup_requests.ad_account_id` | 广告账户ID |
| `ad_account_name` | string | JOIN `ad_accounts.name` | 账户名称（聚合字段） |
| `applicant_id` | UUID | `topup_requests.applicant_id` | 申请人ID |
| `applicant_name` | string | JOIN `users.full_name` | 申请人姓名（聚合字段） |
| `amount` | string | `topup_requests.amount` | 充值金额 |
| `currency` | string | `topup_requests.currency` | 货币类型 |
| `urgency_level` | string | `topup_requests.urgency_level` | 紧急程度 |
| `status` | string | `topup_requests.status` | 状态（draft） |
| `expected_pay_date` | string | `topup_requests.expected_pay_date` | 期望到账日期 |
| `notes` | string | `topup_requests.notes` | 申请说明 |
| `created_at` | ISO 8601 | `topup_requests.created_at` | 创建时间 |
| `updated_at` | ISO 8601 | `topup_requests.updated_at` | 更新时间 |

**Error Responses**:

| 错误码 | HTTP状态码 | 触发场景 |
|--------|-----------|----------|
| `AUTH_500` | 403 | 非允许角色创建 |
| `BIZ_002` | 404 | project_id或ad_account_id不存在 |
| `BIZ_100` | 400 | 金额≤100或≥1000000 |
| `VALIDATION_001` | 400 | 必填字段缺失 |
| `SYS_001` | 500 | 系统内部错误 |

**引用**:
- 业务规则: BR-FIN-001（充值权限）
- 数据表: DATA_SCHEMA.md 3.4.1节
- 状态机: STATE_MACHINE.md 第9章

#### 权限

- **允许角色**: `admin`, `finance`, `pitcher`, `account_manager`
- **业务约束**:
  - BR-FIN-001: 充值请求创建权限
  - 金额范围: ¥100 ~ ¥1,000,000
  - 自动生成唯一request_no（格式: TOPUP-YYYY-MM-DD-XXXX）

#### 并发控制

- **幂等性**: 否（每次调用创建新申请）
- **事务**: 单表INSERT
- **唯一键**: `request_no`（系统自动生成）

---

## 11. Ledger API（资金账本）

### 11.1 端点总览

| 方法 | 路径 | 功能 | 权限 | 状态 |
|------|------|------|------|------|
| GET | `/api/v1/ledger/project/{project_id}` | 查询项目Ledger | `admin`, `finance`, `account_manager`（仅自己管理的） | implemented |
| GET | `/api/v1/ledger/supplier/{supplier_id}` | 查询供应商Ledger | `admin`, `finance` | implemented |
| POST | `/api/v1/ledger/reversal` | 创建红冲记录 | `admin` | implemented |

**双账本类型**:
- **PROJECT账本**: 项目收入（REVENUE, REVERSAL）
- **SUPPLIER账本**: 供应商成本（COST, TRANSFER_OUT, TRANSFER_IN, REVERSAL）

**引用**:
- 数据表: DATA_SCHEMA.md 3.4.4节
- 双账本: LEDGER_SOT.md v1.1
- 业务规则: BR-FIN-005（双写一致性）

---

## 11A. Finance Profit API（财务利润统计）

### 11A.1 端点总览

| 方法 | 路径 | 功能 | 权限 | 状态 |
|------|------|------|------|------|
| POST | `/api/v1/finance/profit/generate` | 生成利润聚合 | `admin`, `finance` | implemented |
| GET | `/api/v1/finance/profit/monthly` | 月度利润表 | `admin`, `finance` | implemented |
| GET | `/api/v1/finance/profit/daily` | 日度利润数据 | `admin`, `finance` | implemented |
| GET | `/api/v1/finance/profit/projects/{id}` | 项目利润明细 | `admin`, `finance`, `account_manager` | implemented |
| GET | `/api/v1/finance/profit/accounts/{id}` | 账户消耗明细 | `admin`, `finance`, `account_manager`, `pitcher` | implemented |
| GET | `/api/v1/finance/profit/summary` | 整体利润汇总 | `admin`, `finance` | implemented |

**错误码**: PROFIT_001 ~ PROFIT_008（详见 ERROR_CODES_SOT.md v2.1）

**计费公式**（来自 BUSINESS_RULES.md v3.2）:
- `revenue = conversions_final × unit_price`
- `cost = real_spend + fee`
- `profit = revenue - cost`
- `profit_margin = profit / revenue × 100`

**引用**:
- 数据表: DATA_SCHEMA.md 3.3.1节 `daily_reports`, 3.2.1节 `projects`, 3.2.9节 `ad_accounts`
- 业务规则: BUSINESS_RULES.md v3.2 利润计算公式
- 权限矩阵: AUTH_SPEC.md v2.0

---

### 11A.2 GET `/api/v1/finance/profit/summary` - 获取利润汇总

#### 请求

**Query Parameters**:

| 参数 | 类型 | 必填 | 默认值 | 说明 | 约束 |
|------|------|------|--------|------|------|
| `project_id` | integer | 否 | - | 项目ID（BIGINT） | 存在的项目ID |
| `start_date` | string | 否 | - | 开始日期 | ISO 8601 date |
| `end_date` | string | 否 | - | 结束日期 | ISO 8601 date, ≥ start_date |

**Request示例**:
```http
GET /api/v1/finance/profit/summary?project_id=1&start_date=2025-01-01&end_date=2025-01-31
Authorization: Bearer <token>
```

#### 响应

**Success (200 OK)**:

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "report_date": "2025-01-21",
        "project_id": 1,
        "project_name": "春节推广项目",
        "conversions_final": 100,
        "unit_price": "50.00",
        "revenue": "5000.00",
        "real_spend": "3000.00",
        "fee": "0.00",
        "cost": "3000.00",
        "profit": "2000.00",
        "profit_margin": 40.0
      }
    ],
    "total_conversions": 100,
    "total_revenue": "5000.00",
    "total_cost": "3000.00",
    "total_profit": "2000.00",
    "overall_profit_margin": 40.0
  },
  "message": "获取利润汇总成功",
  "code": "SUCCESS"
}
```

**Response Schema** (`data`字段):

| 字段 | 类型 | 说明 | 计算方式/来源 |
|------|------|------|---------------|
| `items` | array | 利润明细列表 | - |
| `items[].report_date` | date | 报告日期 | `daily_reports.report_date` |
| `items[].project_id` | integer | 项目ID | `ad_accounts.project_id` |
| `items[].project_name` | string | 项目名称 | `projects.name` |
| `items[].conversions_final` | integer | 最终粉数 | `SUM(daily_reports.conversions_final)` |
| `items[].unit_price` | string | 单粉价格 | `AVG(daily_reports.unit_price)` |
| `items[].revenue` | string | 收入 | `conversions_final × unit_price` |
| `items[].real_spend` | string | 真实消耗 | `SUM(daily_reports.real_spend)` |
| `items[].fee` | string | 服务费 | 默认 "0.00" |
| `items[].cost` | string | 成本 | `real_spend + fee` |
| `items[].profit` | string | 利润 | `revenue - cost` |
| `items[].profit_margin` | float | 利润率(%) | `profit / revenue × 100` |
| `total_conversions` | integer | 总粉数 | 汇总计算 |
| `total_revenue` | string | 总收入 | 汇总计算 |
| `total_cost` | string | 总成本 | 汇总计算 |
| `total_profit` | string | 总利润 | 汇总计算 |
| `overall_profit_margin` | float | 总体利润率(%) | 汇总计算 |

**金额精度**:
- 所有金额字段: `DECIMAL(15,2)`, 使用 `ROUND_HALF_UP` 舍入
- 币种: 继承自项目配置 (默认 CNY)

**Error Responses**:

| 错误码 | HTTP状态码 | 触发场景 | 对应异常类 |
|--------|-----------|----------|-----------|
| `AUTH_400` | 401 | 未提供认证令牌 | - |
| `AUTH_500` | 403 | 非 admin/finance/supervisor 角色访问 | `AuthorizationException` |
| `BIZ_002` | 404 | project_id 不存在 | `ResourceNotFoundException` |
| `BIZ_001` | 400 | start_date > end_date（日期范围无效） | `BusinessRuleException` |
| `BIZ_607` | 500 | 利润统计查询失败 | 通用异常捕获 |

**引用**:
- 错误码: ERROR_CODES_SOT.md v2.1 第3-4节
- 权限: AUTH_SPEC.md v2.0 权限矩阵

#### 权限

- **允许角色**: `admin`, `finance`, `supervisor`
- **业务约束**:
  - 查询范围受角色限制（参考 AUTH_SPEC.md v2.0 第3章）
  - project_id 若指定必须存在
  - 日期范围 start_date ≤ end_date

#### 并发控制

- **幂等性**: 是（只读查询）
- **事务**: 只读查询，无事务需求
- **缓存**: 可考虑缓存（TTL 建议 5 分钟）

#### 数据聚合逻辑

```
数据流向:
daily_reports → ad_accounts → projects

聚合维度:
- 按 report_date 分组
- 按 project_id 分组
- 排序: report_date DESC
```

#### 使用示例

**Frontend (TypeScript)**:
```typescript
import { apiFetch } from '@/lib/api';

// 查询指定项目的利润汇总
const profitSummary = await apiFetch('/api/v1/finance/profit/summary', {
  method: 'GET',
  params: {
    project_id: 1,
    start_date: '2025-01-01',
    end_date: '2025-01-31'
  }
});

// 查询所有项目汇总
const allProjectsSummary = await apiFetch('/api/v1/finance/profit/summary');
```

---

## 12. Reconciliation API（对账管理）

### 12.1 端点总览

| 方法 | 路径 | 功能 | 权限 | 状态机 | 状态 |
|------|------|------|------|--------|------|
| GET | `/api/v1/reconciliations/batches` | 获取对账批次列表 | `admin`, `finance`, `supervisor` | - | implemented |
| POST | `/api/v1/reconciliations/batches` | 创建对账批次 | `finance`, `admin` | `draft` | implemented |
| GET | `/api/v1/reconciliations/batches/{batch_id}` | 获取批次详情 | `admin`, `finance`, `supervisor` | - | implemented |
| PUT | `/api/v1/reconciliations/batches/{batch_id}` | 更新批次 | `finance`, `admin` | - | implemented |
| DELETE | `/api/v1/reconciliations/batches/{batch_id}` | 删除批次 | `admin` | - | implemented |
| POST | `/api/v1/reconciliations/batches/{batch_id}/submit` | 提交审核 | `finance`, `admin` | `draft` → `pending_review` | implemented |
| POST | `/api/v1/reconciliations/batches/{batch_id}/approve` | 批准对账 | `finance`, `admin` | `pending_review` → `approved` | implemented |
| POST | `/api/v1/reconciliations/batches/{batch_id}/request-adjustment` | 要求调整 | `finance`, `admin` | `pending_review` → `needs_adjustment` | implemented |
| POST | `/api/v1/reconciliations/batches/{batch_id}/complete` | 完成对账 | `finance`, `admin` | `approved` → `completed` | implemented |
| POST | `/api/v1/reconciliations/batches/{batch_id}/run` | 执行对账 | `finance`, `admin` | - | implemented |
| GET | `/api/v1/reconciliations/batches/{batch_id}/details` | 获取批次明细列表 | `admin`, `finance`, `supervisor` | - | implemented |
| PUT | `/api/v1/reconciliations/batches/{batch_id}/resubmit` | 重新提交 | `finance`, `admin` | - | implemented |
| PUT | `/api/v1/reconciliations/batches/{batch_id}/force-complete` | 强制完成 | `admin` | - | implemented |
| GET | `/api/v1/reconciliations/details/{detail_id}` | 获取明细详情 | `admin`, `finance`, `supervisor` | - | implemented |
| PUT | `/api/v1/reconciliations/details/{detail_id}/review` | 审核明细 | `finance`, `admin` | - | implemented |
| POST | `/api/v1/reconciliations/details/{detail_id}/adjust` | 调整明细 | `finance`, `admin` | - | implemented |
| PUT | `/api/v1/reconciliations/details/{detail_id}/confirm` | 确认明细 | `finance`, `admin` | - | implemented |
| GET | `/api/v1/reconciliations/statistics` | 获取对账统计 | `admin`, `finance` | - | implemented |
| GET | `/api/v1/reconciliations/export` | 导出对账数据 | `admin`, `finance` | - | implemented |
| GET | `/api/v1/reconciliations/reports` | 获取对账报告列表 | `admin`, `finance` | - | implemented |
| POST | `/api/v1/reconciliations/reports` | 创建对账报告 | `finance`, `admin` | - | implemented |
| GET | `/api/v1/reconciliations/reports/{report_id}` | 获取报告详情 | `admin`, `finance` | - | implemented |
| DELETE | `/api/v1/reconciliations/reports/{report_id}` | 删除报告 | `admin` | - | implemented |
| GET | `/api/v1/reconciliations/adjustments` | 获取调整记录列表 | `admin`, `finance` | - | implemented |
| GET | `/api/v1/reconciliations/adjustments/{adjustment_id}` | 获取调整详情 | `admin`, `finance` | - | implemented |
| POST | `/api/v1/reconciliations/adjustments/{adjustment_id}/execute` | 执行调整 | `admin` | - | implemented |

**对账状态机**: `draft` → `pending_review` → `approved` → `completed` (或 `needs_adjustment` → `approved` → `completed`)（来自 STATE_MACHINE.md v2.6 第11.1节）

**引用**:
- 数据表: DATA_SCHEMA.md 3.5节
- 状态机: STATE_MACHINE.md 第11章
- 业务规则: BR-RECON-001, BR-RECON-003

---

## 12A. Transfers API（死号余额迁移）

### 12A.1 端点总览

| 方法 | 路径 | 功能 | 权限 | 状态机 | 状态 |
|------|------|------|------|--------|------|
| GET | `/api/v1/transfers` | 获取迁移申请列表 | 所有已登录用户 | - | implemented |
| POST | `/api/v1/transfers` | 创建迁移申请 | `admin`, `account_manager`, `finance` | `draft` | implemented |
| GET | `/api/v1/transfers/{transfer_id}` | 获取迁移申请详情 | 所有已登录用户 | - | implemented |
| POST | `/api/v1/transfers/{transfer_id}/submit` | 提交审批 | 申请人, `admin` | `draft` → `pending_approval` | implemented |
| POST | `/api/v1/transfers/{transfer_id}/approve` | 审批通过 | `finance`, `admin` | `pending_approval` → `approved` | implemented |
| POST | `/api/v1/transfers/{transfer_id}/reject` | 拒绝申请 | `finance`, `admin` | → `rejected` | implemented |
| POST | `/api/v1/transfers/{transfer_id}/complete` | 完成迁移 | `admin` | `approved` → `completed` | implemented |

**迁移状态机**: `draft` → `pending_approval` → `approved` → `completed` (或 `rejected`)（来自 STATE_MACHINE.md v2.6 第12章）

**引用**:
- 数据表: DATA_SCHEMA.md 3.4.6节 `transfer_requests`
- 状态机: STATE_MACHINE.md 第12章
- 账本规则: LEDGER_SOT.md v1.1 (TRANSFER_OUT/TRANSFER_IN)

---

## 12B. Suppliers API（供应商管理）

### 12B.1 端点总览

| 方法 | 路径 | 功能 | 权限 | 状态 |
|------|------|------|------|------|
| GET | `/api/v1/suppliers` | 获取供应商列表 | `admin`, `finance`, `account_manager` | implemented |
| POST | `/api/v1/suppliers` | 创建供应商 | `admin`, `finance` | implemented |
| GET | `/api/v1/suppliers/statistics` | 获取供应商统计 | `admin`, `finance` | implemented |
| GET | `/api/v1/suppliers/{supplier_id}` | 获取供应商详情 | `admin`, `finance`, `account_manager` | implemented |
| PUT | `/api/v1/suppliers/{supplier_id}` | 更新供应商 | `admin`, `finance` | implemented |
| DELETE | `/api/v1/suppliers/{supplier_id}` | 删除供应商 | `admin` | implemented |
| GET | `/api/v1/suppliers/{supplier_id}/accounts` | 获取供应商关联账户 | `admin`, `finance`, `account_manager` | implemented |
| GET | `/api/v1/suppliers/{supplier_id}/ledger-summary` | 获取供应商账本汇总 | `admin`, `finance` | implemented |

**引用**:
- 数据表: DATA_SCHEMA.md `suppliers` 表
- 账本规则: LEDGER_SOT.md v1.1 (SUPPLIER 账本)

---

## 12C. Settlements API（结算管理）

### 12C.1 端点总览

| 方法 | 路径 | 功能 | 权限 | 状态机 | 状态 |
|------|------|------|------|--------|------|
| GET | `/api/v1/settlements` | 获取结算列表 | `admin`, `finance` | - | implemented |
| POST | `/api/v1/settlements` | 创建结算 | `admin`, `finance` | `draft` | implemented |
| GET | `/api/v1/settlements/statistics` | 获取结算统计 | `admin`, `finance` | - | implemented |
| GET | `/api/v1/settlements/overdue` | 获取逾期结算 | `admin`, `finance` | - | implemented |
| GET | `/api/v1/settlements/{settlement_id}` | 获取结算详情 | `admin`, `finance` | - | implemented |
| PUT | `/api/v1/settlements/{settlement_id}` | 更新结算 | `admin`, `finance` | - | implemented |
| POST | `/api/v1/settlements/{settlement_id}/submit` | 提交审批 | `admin`, `finance` | `draft` → `pending` | implemented |
| POST | `/api/v1/settlements/{settlement_id}/approve` | 审批结算 | `admin` | `pending` → `approved`/`rejected` | implemented |
| POST | `/api/v1/settlements/{settlement_id}/payment` | 记录支付 | `admin`, `finance` | - | implemented |
| POST | `/api/v1/settlements/{settlement_id}/cancel` | 取消结算 | `admin` | → `cancelled` | implemented |

**引用**:
- 账本规则: LEDGER_SOT.md v1.1 (支付记录生成账本分录)

---

## 12D. Reports API（报表统计）

### 12D.1 端点总览

| 方法 | 路径 | 功能 | 权限 | 状态 |
|------|------|------|------|------|
| GET | `/api/v1/reports/dashboard` | 获取仪表盘数据 | 所有已登录用户 | implemented |
| GET | `/api/v1/reports/performance` | 获取绩效报表 | 所有已登录用户 | implemented |
| GET | `/api/v1/reports/profit` | 获取利润报表 | `admin`, `finance` | implemented |
| GET | `/api/v1/reports/reconciliation` | 获取对账报表 | `admin`, `finance`, `supervisor` | implemented |
| GET | `/api/v1/reports/financial` | 获取财务报表 | `admin`, `finance` | implemented |
| GET | `/api/v1/reports/trends/{metric}` | 获取趋势数据 | 所有已登录用户 | implemented |
| GET | `/api/v1/reports` | 获取报表列表 | 所有已登录用户 | implemented |
| GET | `/api/v1/reports/{project_id}` | 获取项目报表 | 根据角色过滤 | implemented |

---

## 12E. Project Templates API（项目模板）

### 12E.1 端点总览

| 方法 | 路径 | 功能 | 权限 | 状态 |
|------|------|------|------|------|
| GET | `/api/v1/project-templates` | 获取模板列表 | 所有已登录用户 | implemented |
| POST | `/api/v1/project-templates` | 创建模板 | `admin`, `account_manager` | implemented |
| GET | `/api/v1/project-templates/{template_id}` | 获取模板详情 | 所有已登录用户 | implemented |
| PUT | `/api/v1/project-templates/{template_id}` | 更新模板 | `admin`, `account_manager` | implemented |
| DELETE | `/api/v1/project-templates/{template_id}` | 删除模板 | `admin` | implemented |
| POST | `/api/v1/project-templates/{template_id}/apply` | 应用模板创建项目 | `admin`, `account_manager` | implemented |
| GET | `/api/v1/project-templates/{template_id}/preview` | 预览模板效果 | 所有已登录用户 | implemented |

---

## 12F. Import Jobs API（数据导入）

### 12F.1 端点总览

| 方法 | 路径 | 功能 | 权限 | 状态 |
|------|------|------|------|------|
| POST | `/api/v1/import-jobs/upload` | 上传导入文件 | `admin`, `supervisor` | implemented |
| GET | `/api/v1/import-jobs` | 获取导入任务列表 | `admin`, `supervisor` | implemented |
| GET | `/api/v1/import-jobs/statistics` | 获取导入统计 | `admin`, `supervisor` | implemented |
| GET | `/api/v1/import-jobs/{job_id}` | 获取任务详情 | `admin`, `supervisor` | implemented |
| GET | `/api/v1/import-jobs/{job_id}/progress` | 获取任务进度 | `admin`, `supervisor` | implemented |
| GET | `/api/v1/import-jobs/{job_id}/errors` | 获取错误详情 | `admin`, `supervisor` | implemented |
| POST | `/api/v1/import-jobs/{job_id}/start` | 启动导入任务 | `admin`, `supervisor` | implemented |
| POST | `/api/v1/import-jobs/{job_id}/cancel` | 取消导入任务 | `admin`, `supervisor` | implemented |
| DELETE | `/api/v1/import-jobs/{job_id}` | 删除导入任务 | `admin` | implemented |
| POST | `/api/v1/import-jobs/check-duplicate` | 检查重复数据 | `admin`, `supervisor` | implemented |

---

## 12G. AI Analytics API（AI 分析）

### 12G.1 端点总览

| 方法 | 路径 | 功能 | 权限 | 状态 |
|------|------|------|------|------|
| POST | `/api/v1/ai-analytics/predict` | AI 预测 | `admin`, `supervisor` | implemented |
| POST | `/api/v1/ai-analytics/optimize` | AI 优化建议 | `admin`, `supervisor` | implemented |
| GET | `/api/v1/ai-analytics/insights` | 获取 AI 洞察 | 所有已登录用户 | implemented |
| GET | `/api/v1/ai-analytics/recommendations` | 获取推荐 | 所有已登录用户 | implemented |
| GET | `/api/v1/ai-analytics/anomalies` | 获取异常检测结果 | `admin`, `supervisor` | implemented |
| GET | `/api/v1/ai-analytics/forecasts` | 获取预测数据 | `admin`, `finance` | implemented |

---

## 12H. Agents API（Agent 编排）

### 12H.1 端点总览

| 方法 | 路径 | 功能 | 权限 | 状态 |
|------|------|------|------|------|
| GET | `/api/v1/agents` | 获取可用 Agent 列表 | `admin` | implemented |
| GET | `/api/v1/agents/{agent_name}` | 获取 Agent 详情 | `admin` | implemented |
| POST | `/api/v1/agents/run` | 执行单个 Agent | `admin` | implemented |
| POST | `/api/v1/agents/orch` | 编排执行多个 Agent | `admin` | implemented |

---

## 12W. Weekly Briefs API（周报管理）

> **来源**: B3-weekly-brief.md §4.1
> **状态**: 新增模块

### 12W.1 端点总览

| 方法 | 路径 | 功能 | 权限 | 状态 |
|------|------|------|------|------|
| GET | `/api/v1/weekly-briefs` | 获取周报列表 | 角色过滤 | implemented |
| GET | `/api/v1/weekly-briefs/stats` | 获取周报统计 | `ceo`, `supervisor` | implemented |
| GET | `/api/v1/weekly-briefs/{brief_id}` | 获取周报详情 | 角色过滤 | implemented |
| POST | `/api/v1/weekly-briefs` | 创建周报 | `project_owner`, `admin` | implemented |
| PUT | `/api/v1/weekly-briefs/{brief_id}` | 更新周报 | `project_owner`(草稿), `admin` | implemented |
| POST | `/api/v1/weekly-briefs/{brief_id}/submit` | 提交周报 | `project_owner`, `admin` | implemented |
| GET | `/api/v1/weekly-briefs/export` | 导出周报 | `project_owner`, `ceo`, `admin` | planned |
| GET | `/api/v1/weekly-briefs/projects/{project_id}/weekly-summary` | 项目周数据汇总 | 角色过滤 | implemented |

### 12W.2 数据模型

**周报状态机** (2 状态):
```
draft → submitted
```

**请求 Schema (创建)**:

| 字段 | 类型 | 必填 | 约束 | 说明 |
|------|------|------|------|------|
| `project_id` | integer | ✅ | >0 | 项目ID |
| `week_start` | date | ✅ | 必须是周一 | 周开始日期 |
| `achievements` | string | 否 | ≤5000字符 | 本周成果 |
| `issues` | string | 否 | ≤5000字符 | 遇到问题 |
| `solutions` | string | 否 | ≤5000字符 | 解决方案 |
| `next_week_plan` | string | 否 | ≤5000字符 | 下周计划 |

**响应 Schema**:

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | integer | 周报ID |
| `project_id` | integer | 项目ID |
| `project_name` | string | 项目名称 |
| `week_start` | date | 周开始日期 |
| `week_end` | date | 周结束日期 |
| `week_label` | string | 周次标签 (如 "2025-W51") |
| `submitter_id` | UUID | 提交人ID |
| `submitter_name` | string | 提交人姓名 |
| `status` | string | 状态 (draft/submitted) |
| `weekly_spend` | decimal | 周消耗 (自动汇总) |
| `weekly_conversions` | integer | 周进粉 (自动汇总) |
| `weekly_cpl` | decimal | 周CPL (自动计算) |
| `cpl_trend` | decimal | CPL环比 |
| `achievements` | string | 本周成果 |
| `issues` | string | 遇到问题 |
| `solutions` | string | 解决方案 |
| `next_week_plan` | string | 下周计划 |
| `submitted_at` | datetime | 提交时间 |
| `created_at` | datetime | 创建时间 |
| `updated_at` | datetime | 更新时间 |

### 12W.3 权限矩阵

| 操作 | ceo | project_owner | supervisor | finance | pitcher | admin |
|------|-----|---------------|------------|---------|---------|-------|
| 列表查询 | 全部 | 自己项目 | 团队项目 | 全部(只读) | ❌ | 全部 |
| 详情查询 | ✅ | 自己项目 | 团队项目 | ✅ | ❌ | ✅ |
| 创建 | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ |
| 更新(草稿) | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ |
| 提交 | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ |
| 统计查询 | ✅ | ❌ | ✅ | ❌ | ❌ | ✅ |

### 12W.4 业务规则

- **BR-WB-001**: 每项目每周只能有一份周报
- **BR-WB-002**: `week_start` 必须是周一
- **BR-WB-003**: 创建时自动汇总 `weekly_spend` 和 `weekly_conversions`
- **BR-WB-004**: 只有草稿状态可以更新
- **BR-WB-005**: 提交后状态不可回退 (Phase 1 不强制)

**引用**:
- 数据表: DATA_SCHEMA.md (weekly_briefs 表)
- 业务规则: BUSINESS_RULES.md v3.2

---

## 12I. Health API（健康检查）

### 12I.1 端点总览

| 方法 | 路径 | 功能 | 权限 | 状态 |
|------|------|------|------|------|
| GET | `/api/v1/health` | 健康检查 | 公开 | implemented |

---

## 13. 全局规范参考

### 13.1 核心常量定义

#### 13.1.1 角色常量（7 角色，来源: MASTER.md v4.4 §2.4）

```python
# backend/core/constants.py
VALID_ROLES = [
    "ceo",             # 老板 - 资金安全、公司盈亏、最终决策
    "project_owner",   # 项目负责人 - 项目盈亏、资金使用效率
    "finance",         # 财务 - 资金出入准确、数据真实、对账
    "supervisor",      # 主管 - 团队产出、投手管理、日常监督
    "pitcher",         # 投手 - CPL 达标、日报准确、执行投放
    "account_manager", # 户管 - 账户分配、账户状态监控
    "admin"            # 管理员 - 系统配置（不参与业务）
]

# 旧角色映射（兼容性）
ROLE_ALIASES = {
    "media_buyer": "pitcher",      # 旧名 → 新名
    "data_operator": "supervisor"  # 旧名 → 新名
}
```

#### 13.1.2 状态枚举（严格对齐 STATE_MACHINE.md v2.6）

⚠️ **强制约束**: 所有状态枚举必须严格对齐 [STATE_MACHINE.md v2.6](./STATE_MACHINE.md) 定义，禁止使用未在下方列出的旧状态值。任何状态流转必须遵循 STATE_MACHINE.md 中的合法流转白名单。

**项目状态** (STATE_MACHINE.md v2.6 第5章):
```python
PROJECT_STATUS = Literal["draft", "active", "suspended", "archived"]
```

**日报状态** (STATE_MACHINE.md v2.6 第8章):
```python
DAILY_REPORT_STATUS = Literal[
    "raw_submitted",
    "trend_pending",
    "trend_ok",
    "trend_flagged",
    "trend_resolved",
    "final_pending",
    "final_confirmed",
    "final_locked"
]
```

**充值状态** (STATE_MACHINE.md v2.6 第9章):
```python
TOPUP_STATUS = Literal[
    "draft",
    "pending_review",
    "finance_approve",
    "paid",
    "completed",
    "rejected",
    "cancelled"
]
```

**对账状态** (STATE_MACHINE.md v2.6 第11章):
```python
RECONCILIATION_STATUS = Literal[
    "draft",
    "pending_review",
    "approved",
    "needs_adjustment",
    "completed"
]
```

**迁移状态** (STATE_MACHINE.md v2.6 第12章):
```python
TRANSFER_STATUS = Literal[
    "draft",
    "pending_approval",
    "approved",
    "rejected",
    "completed"
]
```

#### 13.1.3 错误码前缀

```python
ERROR_PREFIXES = {
    "AUTH_": "认证授权（401/403）",
    "BIZ_": "业务逻辑（400/404/409）",
    "VALIDATION_": "参数验证（422）",
    "STATE_": "状态机（400/403/409）",
    "TREND_": "趋势风控（200/400）",
    "SYS_": "系统错误（500）",
    "DB_": "数据库（400/409/500）"
}
```

### 13.2 前端调用规范

#### 13.2.1 统一使用 apiFetch

```typescript
// frontend/lib/api.ts
import { apiFetch } from '@/lib/api';

// ✅ 正确
const response = await apiFetch<ProjectResponse>('/api/v1/projects/1');

// ❌ 禁止
const response = await fetch('/api/v1/projects/1');
const response = await axios.get('/api/v1/projects/1');
```

#### 13.2.2 错误处理

```typescript
try {
  const project = await apiFetch('/api/v1/projects', {
    method: 'POST',
    body: JSON.stringify(projectData)
  });
} catch (error) {
  // apiFetch自动处理Envelope格式错误
  if (error.code === 'AUTH_500') {
    // 权限不足
    showErrorMessage('您没有权限创建项目');
  } else if (error.code === 'BIZ_003') {
    // 项目名称重复
    showErrorMessage('项目名称已存在');
  } else {
    // 其他错误
    showErrorMessage(error.message);
  }
}
```

### 13.3 AI 工具开发指导

#### 13.3.1 Claude Code / Cursor 推荐 Prompt 模板

```markdown
基于 API_SOT.md 创建 {{模块名}} 模块的 {{功能}} API：

1. 参考端点: API_SOT.md 第{{章节}}节
2. 数据定义: DATA_SCHEMA.md 3.{{节}}节 {{表名}} 表
3. 状态机: STATE_MACHINE.md 第{{章节}}章
4. 业务规则: BUSINESS_RULES.md BR-{{MODULE}}-{{编号}}
5. 错误码: ERROR_CODES_SOT.md 4.{{节}}节

请严格按照以下顺序生成代码：
1. Schema定义（backend/schemas/{{module}}.py）
2. Service实现（backend/services/{{module}}_service.py）
3. Router接口（backend/routers/{{module}}.py）
4. 测试用例（backend/tests/test_{{module}}_api.py）

注意事项：
- 所有字段名必须与 DATA_SCHEMA.md 完全一致
- 状态枚举必须来自 STATE_MACHINE.md
- 错误码必须来自 ERROR_CODES_SOT.md
- 响应必须使用 success_response/error_response
```

---

**文档性质**: 项目强制规范
**执行级别**: 🔴 必须严格遵守
**违规处理**: PR自动拒绝 / 代码回滚
**最后更新**: 2025-12-24
**版本**: v9.2 (对齐 MASTER.md v4.4)

**v9.2 更新说明** (2025-12-24):
- 统一角色名称：`media_buyer` → `pitcher`, `data_operator` → `supervisor`
- 修复权限描述和示例代码中的角色不一致问题
- 新增 Project Members API（§6A）章节：项目成员管理 CRUD
- 修正角色数量描述："5个合法值" → "技术层 5 个值，见 §1.2.1 角色定义"
- 更新所有 API 端点表格中的角色权限为标准 7 角色名称

**v9.1 更新说明** (2025-12-23):
- 修复 SYSTEM_OVERVIEW.md 断链引用（已归档），更新为 MASTER.md v4.4
- 统一角色定义为 7 角色（ceo/project_owner/finance/supervisor/pitcher/account_manager/admin）
- 添加旧角色映射说明（media_buyer→pitcher, data_operator→supervisor）
- 更新 BUSINESS_RULES.md 版本引用 v3.1 → v3.2
- 新增 Weekly Briefs API（§12W）章节
- 更新 SoT 引用清单，添加 MASTER.md 和 AUTH_SPEC.md

**v9.0 更新说明** (2025-01-22):
- 完全重写为端点级API规范
- 新增所有核心模块的详细端点定义（Users/Projects/Channels/AdAccounts/DailyReports/Topup/Ledger/Reconciliation）
- 每个端点包含完整的Request/Response Schema、字段映射、错误码、权限、并发控制、事务边界
- 集成三数据流（raw/real/final）和双账本（PROJECT/SUPPLIER）概念
- 新增8状态粉数确认状态机完整流程
- 新增红冲修正机制详细说明
- 所有字段严格对齐 DATA_SCHEMA.md v5.2
- 所有状态流转严格对齐 STATE_MACHINE.md v2.6
- 所有错误码严格对齐 ERROR_CODES_SOT.md v2.1
- 所有业务规则严格对齐 BUSINESS_RULES.md v3.2
