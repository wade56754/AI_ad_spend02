# 认证与授权规范（AUTH_SPEC - Single Source of Truth�?

> **文档版本**: v2.0 (正式SoT�?
> **发布日期**: 2025-01-22
> **文档类型**: 认证授权领域唯一真相源（SoT-Auth�?
> **适用范围**: FastAPI后端 + Supabase Auth + Next.js前端
> **规范级别**: 🔴 强制执行（PR必查�?
> **文档定位**: 开�?测试/前端/后端/架构都可单独依赖本文件完成认证授权实�?

---

## �?快速导�?

| 章节 | 内容 | 适用人员 |
|-----|------|---------|
| [1. 文档定位](#1-文档定位sot声明) | SoT仲裁规则 | 架构师、Tech Lead |
| [2. 用户模型](#2-用户模型user-model-sot) | users表结构�?大角�?| 后端开发、DBA |
| [3. 认证机制](#3-认证机制authentication) | Supabase Auth、JWT Token | 前端+后端开�?|
| [4. Auth状态机](#4-auth状态机) | Token生命周期、状态流�?| 后端开�?|
| [5. 授权机制](#5-授权机制authorization) | RBAC、SOD、数据隔�?| 后端开�?|
| [6. Auth API SoT](#6-auth-api-sot) | 登录/登出/刷新端点 | 全栈开�?|
| [7. 错误码](#7-错误码auth错误码sot) | AUTH_*错误�?| 全栈开�?|
| [8. 审计要求](#8-审计要求audit-specification) | 审计日志规范 | 后端开发、安�?|
| [9. 安全策略](#9-安全策略security-rules) | Zero Trust原则 | 全员 |
| [10. 测试矩阵](#10-测试矩阵auth-test-plan) | 测试用例清单 | 测试工程�?|

---

## 1. 文档定位（SoT声明�?

### 1.1 AUTH_SPEC的SoT职责

**本文档是AI_AD_SYSTEM认证授权领域的唯一真相�?*，负责定义：

- �?认证流程（Supabase Auth集成、JWT Token验证�?
- �?授权机制（RBAC角色系统、权限矩阵）
- �?Token生命周期（TTL、刷新策略、失效策略）
- �?Auth状态机（active/expired/invalidated状态流转）
- �?数据权限过滤（Service层数据隔离）
- �?Session管理（单设备/多设备登录）
- �?审计要求（audit_logs记录规范�?

### 1.2 仲裁顺序（冲突优先级�?

| 领域 | 唯一真相�?| 仲裁规则 | 示例 |
|-----|-----------|---------|------|
| **数据库字�?* | DATA_SCHEMA.md v5.2 | 字段�?类型/约束以DATA_SCHEMA为准 | `users.role`的CHECK约束 |
| **业务规则** | BUSINESS_RULES.md v3.1 | 权限/SOD规则以BUSINESS_RULES为准 | BR-USER-002（职责分离） |
| **错误�?* | ERROR_CODES_SOT.md v2.1 | 错误�?HTTP状态以ERROR_CODES为准 | `AUTH_500`权限不足 |
| **状态流�?* | STATE_MACHINE.md v2.6 | 业务状态以STATE_MACHINE为准 | 项目/日报状态机 |
| **Token生命周期** | AUTH_SPEC.md v2.0 (本文�? | Token TTL/刷新策略以本文档为准 | Access Token 1小时 |
| **认证流程** | AUTH_SPEC.md v2.0 (本文�? | Token验证/权限校验链路以本文档为准 | JWT验证逻辑 |

**冲突处理规则**:
- �?如果DATA_SCHEMA与AUTH_SPEC字段定义冲突 �?**以DATA_SCHEMA为准，修改AUTH_SPEC**
- �?如果BUSINESS_RULES与AUTH_SPEC权限规则冲突 �?**以BUSINESS_RULES为准，修改AUTH_SPEC**
- �?如果ERROR_CODES与AUTH_SPEC错误码冲�?�?**以ERROR_CODES为准，修改AUTH_SPEC**
- �?如果API_SOT.md与AUTH_SPEC认证流程冲突 �?**修改API_SOT.md，以AUTH_SPEC为准**

### 1.3 禁止绕过规则

⚠️ **任何开发者不得绕过本文档设计Auth机制**

- �?**禁止**在Router层直接解析JWT或验证权�?
- �?**禁止**前端直接解析JWT Payload获取user_id
- �?**禁止**前端传递user_id修改他人数据（必须从Token中提取）
- �?**禁止**创建�?个固定角色外的任何新角色
- �?**禁止**在数据库直接UPDATE用户角色（必须通过API+审计�?

---

## 2. 用户模型（User Model SoT�?

### 2.1 users表完整定�?

**引用**: DATA_SCHEMA.md v5.2 �?.1.1�?

```sql
CREATE TABLE users (
    -- ===== 主键（与Supabase Auth同步�?=====
    id UUID PRIMARY KEY,  -- FK �?auth.users(id) ON DELETE CASCADE

    -- ===== 基础信息 =====
    username VARCHAR(50) NOT NULL UNIQUE,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(255),  -- 冗余字段，从auth.users同步

    -- ===== 角色与权限（五枚举固定定义） =====
    role VARCHAR(20) NOT NULL CHECK (role IN (
        'admin',
        'finance',
        'data_operator',
        'account_manager',
        'media_buyer'
    )),

    -- ===== 组织信息 =====
    department VARCHAR(100),
    position VARCHAR(100),
    account_manager_id UUID REFERENCES users(id),  -- 投手关联的户�?

    -- ===== 账户状�?=====
    is_active BOOLEAN DEFAULT true NOT NULL,
    is_verified BOOLEAN DEFAULT false NOT NULL,

    -- ===== 登录信息 =====
    last_login_at TIMESTAMPTZ,
    last_login_ip VARCHAR(45),  -- 支持IPv4/IPv6

    -- ===== 扩展配置（JSONB�?=====
    preferences JSONB DEFAULT '{}'::jsonb NOT NULL,
    notification_settings JSONB DEFAULT '{}'::jsonb NOT NULL,
    profile_metadata JSONB DEFAULT '{}'::jsonb NOT NULL,

    -- ===== 地区与语言 =====
    timezone VARCHAR(50) DEFAULT 'UTC' NOT NULL,
    language VARCHAR(10) DEFAULT 'zh-CN' NOT NULL,

    -- ===== 审计字段 =====
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id)
);

-- 索引
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_account_manager ON users(account_manager_id);
CREATE INDEX idx_users_created_at ON users(created_at);
CREATE INDEX idx_users_last_login ON users(last_login_at);
CREATE INDEX idx_users_email ON users(email);
```

### 2.2 role五枚举固定定�?

**引用**: BUSINESS_RULES.md v3.1 - BR-AUTH-001, BR-USER-001

| 角色代码 | 角色名称 | 权限级别 | 主要职责 |
|---------|---------|---------|---------|
| `admin` | 系统管理�?| L5 (最�? | 系统配置、全局审计、紧急干预、用户管�?|
| `finance` | 财务 | L4 | 充值终审、资金监控、财务对账、账本管�?|
| `data_operator` | 数据操作�?户管 | L3 | 日报审核、数据校验、Excel导入导出 |
| `account_manager` | 客户经理 | L2 | 项目维护、成员管理、充值初�?|
| `media_buyer` | 投手/媒体采购 | L1 (最�? | 日报提交、充值申请、凭证上�?|

**强制约束**:
- �?**禁止**添加新角色（如`super_admin`、`manager`、`operator`等）
- �?**禁止**一个用户拥有多个角色（不支持角色数组）
- �?角色一旦创建，仅`admin`可修改（需记录审计日志�?
- �?角色修改必须通过API，禁止直接UPDATE数据�?

### 2.3 JSONB字段结构

#### 2.3.1 preferences JSONB字段

**允许的Key及默认�?*:

```typescript
interface UserPreferences {
  theme: 'light' | 'dark' | 'auto';  // 默认: 'light'
  sidebar_collapsed: boolean;         // 默认: false
  dashboard_layout: string;           // 默认: '{}' (JSON字符�?
  date_format: 'YYYY-MM-DD' | 'DD/MM/YYYY' | 'MM/DD/YYYY';  // 默认: 'YYYY-MM-DD'
  number_format: 'comma' | 'space' | 'dot';  // 默认: 'comma'
}
```

**示例�?*:
```json
{
  "theme": "dark",
  "sidebar_collapsed": false,
  "dashboard_layout": "{\"widgets\": [\"revenue\", \"cost\"]}",
  "date_format": "YYYY-MM-DD",
  "number_format": "comma"
}
```

**禁止行为**:
- �?**禁止**添加未定义的Key（必须在此文档中明确定义�?
- �?**禁止**将preferences设为null（必须保持默认值`{}`�?

#### 2.3.2 notification_settings JSONB字段

```typescript
interface NotificationSettings {
  email_enabled: boolean;             // 默认: true
  sms_enabled: boolean;               // 默认: false
  push_enabled: boolean;              // 默认: true
  notify_on_report_approved: boolean; // 默认: true
  notify_on_topup_approved: boolean;  // 默认: true
  notify_on_trend_flagged: boolean;   // 默认: true
}
```

#### 2.3.3 profile_metadata JSONB字段

```typescript
interface ProfileMetadata {
  avatar_url?: string;         // 头像URL
  phone?: string;              // 手机�?
  wechat_id?: string;          // 微信�?
  qq?: string;                 // QQ�?
  employee_id?: string;        // 工号
  join_date?: string;          // 入职日期 (YYYY-MM-DD)
  custom_fields?: Record<string, any>;  // 自定义扩�?
}
```

### 2.4 is_active / is_verified 规则

| 字段 | 类型 | 默认�?| 说明 | 状态组�?|
|------|------|--------|------|---------|
| `is_active` | BOOLEAN | `true` | 账号可用�?| `false`时禁止登录（返回`AUTH_002`�?|
| `is_verified` | BOOLEAN | `false` | 资料验证状�?| 由admin手动验证，不影响登录 |

**状态组合表**:

| is_active | is_verified | 登录权限 | API访问 | 说明 |
|-----------|-------------|---------|--------|------|
| `true` | `true` | �?允许 | �?全部 | 正常用户 |
| `true` | `false` | �?允许 | �?全部 | 新用户（待验证，不影响使用） |
| `false` | `true` | �?禁止 | �?禁止 | 已禁用账�?|
| `false` | `false` | �?禁止 | �?禁止 | 已禁�?未验�?|

### 2.5 last_login_at / last_login_ip 规则

- **更新时机**: 每次成功调用`POST /api/v1/auth/login`后立即更�?
- **时区要求**: 统一使用UTC时区（TIMESTAMPTZ�?
- **IP格式**: 支持IPv4/IPv6，最大长�?5字符
- **隐私保护**: 非admin角色不可查询他人的last_login_ip

---

## 3. 认证机制（Authentication�?

### 3.1 Supabase Auth

#### 3.1.1 Access Token生成方式

**流程**:
```mermaid
sequenceDiagram
    participant FE as 前端
    participant SB as Supabase Auth
    participant BE as 后端API
    participant DB as PostgreSQL

    FE->>SB: POST /auth/v1/token (email, password)
    SB->>DB: 查询 auth.users
    DB-->>SB: 返回用户记录
    SB->>SB: 验证密码hash
    SB->>SB: 生成JWT (HS256签名)
    SB-->>FE: 返回 {access_token, refresh_token, user}
    FE->>BE: API请求 (Authorization: Bearer <access_token>)
    BE->>SB: 验证JWT签名
    SB-->>BE: 返回decoded payload
    BE->>DB: 查询 users �?
    DB-->>BE: 返回业务用户信息
    BE-->>FE: 返回业务数据
```

#### 3.1.2 Token Payload标准

**Access Token Payload**:

```json
{
  "sub": "550e8400-e29b-41d4-a716-446655440000",  // user.id (UUID)
  "email": "alice@example.com",
  "role": "authenticated",  // Supabase固定角色（非业务角色�?
  "iat": 1705910400,        // 签发时间 (Unix timestamp)
  "exp": 1705914000,        // 过期时间 (iat + 3600�?= 1小时)
  "aud": "authenticated",
  "iss": "https://your-project.supabase.co/auth/v1"
}
```

**Refresh Token Payload**:

```json
{
  "sub": "550e8400-e29b-41d4-a716-446655440000",
  "session_id": "d7f8c3b1-9a2e-4f5b-8c3d-1a2b3c4d5e6f",
  "iat": 1705910400,
  "exp": 1708502400  // 30天后
}
```

**重要说明**:
- ⚠️ Supabase的`role`字段固定为`authenticated`�?*不是业务角色**
- ⚠️ 业务角色（admin/finance/...）必须从`users`表查询，**禁止依赖JWT Payload**
- ⚠️ 前端**禁止**直接解析JWT获取user_id或role

### 3.2 Bearer Token

#### 3.2.1 请求头格�?

**标准格式**:
```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**错误格式示例**:
- �?`Authorization: eyJhbGc...` (缺少Bearer前缀)
- �?`Authorization: bearer eyJhbGc...` (小写bearer)
- �?`X-Auth-Token: eyJhbGc...` (错误的Header名称)

#### 3.2.2 后端验证流程（必须写伪代码）

**完整验证链路**:

```python
# backend/dependencies/auth.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import Client
from sqlalchemy.orm import Session

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
    supabase: Client = Depends(get_supabase_client)
) -> Dict:
    """
    验证Access Token并返回当前用�?

    步骤:
    1. 提取Token
    2. Supabase JWT验证
    3. 查询业务users�?
    4. 验证账户状�?
    5. 返回用户上下�?
    """
    token = credentials.credentials

    # Step 1: 验证Token格式
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"success": False, "message": "未提供认证令�?, "code": "AUTH_400"}
        )

    # Step 2: Supabase JWT验证
    try:
        user_response = supabase.auth.get_user(token)
        auth_user = user_response.user
    except Exception as e:
        if "expired" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"success": False, "message": "令牌已过�?, "code": "AUTH_402"}
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"success": False, "message": "无效的认证令�?, "code": "AUTH_401"}
            )

    # Step 3: 查询业务user�?
    db_user = db.query(User).filter(User.id == auth_user.id).first()

    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"success": False, "message": "用户不存在或已被删除", "code": "AUTH_004"}
        )

    # Step 4: 验证账户状�?
    if not db_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"success": False, "message": "账户已被禁用", "code": "AUTH_002"}
        )

    # Step 5: 返回用户上下文（注入到Router�?
    return {
        "user_id": str(db_user.id),
        "username": db_user.username,
        "full_name": db_user.full_name,
        "email": db_user.email,
        "role": db_user.role,  # 业务角色（非JWT的role�?
        "is_active": db_user.is_active,
        "is_verified": db_user.is_verified
    }
```

#### 3.2.3 Token注入User Context机制

**Router层使�?*:

```python
# backend/routers/daily_reports.py
from fastapi import APIRouter, Depends
from dependencies.auth import get_current_user

router = APIRouter(prefix="/api/v1/daily-reports", tags=["DailyReports"])

@router.post("")
async def create_daily_report(
    report: DailyReportCreate,
    current_user: Dict = Depends(get_current_user),  # �?自动注入
    db: Session = Depends(get_db)
):
    # current_user已经包含完整的用户上下文
    # {'user_id': '...', 'role': 'media_buyer', ...}

    # 业务逻辑直接使用current_user
    service = DailyReportService(db)
    return service.create_report(report, current_user)
```

**Service层使�?*:

```python
# backend/services/daily_report_service.py
class DailyReportService:
    def create_report(self, report: DailyReportCreate, user: Dict):
        # 自动填充created_by（从user上下文提取）
        new_report = DailyReport(
            ad_account_id=report.ad_account_id,
            report_date=report.report_date,
            conversions_raw=report.conversions_raw,
            raw_spend=report.raw_spend,
            created_by=user["user_id"],  # �?从Token提取，前端无法伪�?
            status="raw_submitted"
        )
        self.db.add(new_report)
        self.db.commit()
        return new_report
```

### 3.3 Token生命周期（SOT级别�?

#### 3.3.1 TTL配置

| Token类型 | 默认TTL | 可配置范�?| 配置位置 |
|----------|--------|-----------|---------|
| **Access Token** | 1小时�?600秒） | 5分钟 - 24小时 | Supabase Dashboard �?Auth Settings |
| **Refresh Token** | 30天（2592000秒） | 7�?- 365�?| Supabase Dashboard �?Auth Settings |

**Supabase配置路径**:
```
项目Dashboard �?Authentication �?Settings �?JWT Settings
- JWT expiry limit: 3600 (�?
- Refresh token rotation: Enabled (推荐)
```

#### 3.3.2 Token Rotation策略

**启用Refresh Token Rotation**（推荐）:

```mermaid
sequenceDiagram
    participant FE as 前端
    participant SB as Supabase Auth

    FE->>SB: POST /auth/v1/token (grant_type=refresh_token, refresh_token=OLD)
    SB->>SB: 验证OLD refresh_token
    SB->>SB: 标记OLD为已使用（一次性）
    SB->>SB: 生成NEW access_token
    SB->>SB: 生成NEW refresh_token
    SB-->>FE: 返回 {access_token: NEW, refresh_token: NEW}
    Note over FE: 存储NEW tokens，废弃OLD tokens
```

**关键规则**:
- �?每次刷新后，旧Refresh Token立即失效（一次性使用）
- �?如果旧Refresh Token被重复使�?�?返回`AUTH_003`（令牌已被撤销�?
- �?刷新后Access Token和Refresh Token都会更新

#### 3.3.3 单设�?多设备登录策�?

**策略A: 多设备登录（当前默认�?*

- �?同一用户可在多个设备同时登录
- �?每个设备拥有独立的Session（不同的session_id�?
- �?登出只影响当前设备的Token

**实现**:
```python
# backend/services/auth_service.py
def login(self, email: str, password: str, request: Request):
    # Supabase登录
    auth_response = supabase.auth.sign_in_with_password({
        "email": email,
        "password": password
    })

    # 创建新Session记录（不使旧Session失效�?
    new_session = UserSession(
        user_id=user.id,
        session_id=auth_response.session.access_token[:36],
        ip_address=request.client.host,
        user_agent=request.headers.get("User-Agent"),
        expires_at=datetime.fromtimestamp(auth_response.session.expires_at, timezone.utc)
    )
    self.db.add(new_session)
    self.db.commit()

    return auth_response
```

**策略B: 单设备登录（需开启）**

- �?新设备登录后，旧设备Session自动失效
- �?通过`user_sessions`表的`invalidated_at`字段实现

**实现**:
```python
def login_single_device(self, email: str, password: str, request: Request):
    # Step 1: Supabase登录
    auth_response = supabase.auth.sign_in_with_password({"email": email, "password": password})

    # Step 2: 使旧Session失效
    old_sessions = self.db.query(UserSession).filter(
        UserSession.user_id == user.id,
        UserSession.invalidated_at.is_(None)
    ).all()

    for old_session in old_sessions:
        old_session.invalidated_at = datetime.now(timezone.utc)

    # Step 3: 创建新Session
    new_session = UserSession(...)
    self.db.add(new_session)
    self.db.commit()

    return auth_response
```

#### 3.3.4 强制失效策略

**失效场景**:

| 场景 | 触发方式 | 失效范围 | 错误�?|
|------|---------|---------|--------|
| **用户主动登出** | 调用`POST /auth/logout` | 当前Session | `AUTH_003` |
| **账户被禁�?* | `is_active=false` | 所有Session | `AUTH_002` |
| **风控强制下线** | Admin调用`POST /users/{id}/force-logout` | 所有Session | `AUTH_003` |
| **密码修改** | 调用`PUT /users/me/password` | 所有Session（除当前�?| `AUTH_003` |
| **Token泄露响应** | Admin手动撤销 | 指定Session或所有Session | `AUTH_003` |

**实现示例（风控强制下线）**:

```python
# backend/routers/users.py
@router.post("/{user_id}/force-logout")
async def force_logout(
    user_id: str,
    reason: str,
    current_user: Dict = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
):
    """
    强制用户下线（仅admin�?

    业务规则: BR-AUTH-004 - 最小权限原�?
    """
    # Step 1: 使所有Session失效
    sessions = db.query(UserSession).filter(
        UserSession.user_id == user_id,
        UserSession.invalidated_at.is_(None)
    ).all()

    now = datetime.now(timezone.utc)
    for session in sessions:
        session.invalidated_at = now

    # Step 2: 记录审计日志
    audit_log = AuditLog(
        module="auth",
        action="force_logout",
        entity_id=user_id,
        performed_by=current_user["user_id"],
        role=current_user["role"],
        ip_address=request.client.host,
        payload_before={"active_sessions": len(sessions)},
        payload_after={"reason": reason, "invalidated_sessions": len(sessions)}
    )
    db.add(audit_log)
    db.commit()

    return success_response(message=f"已强制下线用户（共{len(sessions)}个Session�?)
```

---

## 4. Auth状态机

### 4.1 状态定�?

**Token/Session状态枚�?*:

| 状�?| 说明 | 终�?| 可�?|
|-----|------|------|------|
| `active` | Token有效且未过期 | �?| - |
| `expired` | Token自然过期（exp < NOW()�?| �?| �?不可�?|
| `invalidated` | 主动失效（登出、强制下线） | �?| �?不可�?|

**引用**: STATE_MACHINE.md v2.6（本状态机为Auth专用，不在STATE_MACHINE.md中）

### 4.2 状态流转白名单�?

| 当前状�?| 事件 | 目标状�?| 触发条件 | 操作�?|
|---------|------|---------|---------|--------|
| `active` | `refresh` | `active` | 有效的Refresh Token | 用户 |
| `active` | `expire` | `expired` | `exp < NOW()` | system（自动） |
| `active` | `logout` | `invalidated` | 用户主动登出 | 用户 |
| `active` | `security_invalid` | `invalidated` | 账户禁用、风控下�?| admin/system |
| `expired` | `refresh` | �?禁止 | 过期后不可刷�?| - |
| `invalidated` | `refresh` | �?禁止 | 已失效不可恢�?| - |

**禁止行为**:
- �?`expired` 状态下尝试刷新 �?返回`AUTH_402`
- �?`invalidated` 状态下尝试刷新 �?返回`AUTH_003`
- �?任何终态状态不可回退到`active`

### 4.3 状态流转Mermaid�?

```mermaid
stateDiagram-v2
    [*] --> active: 登录成功

    active --> active: refresh (有效Refresh Token)
    active --> expired: 自然过期 (exp < NOW())
    active --> invalidated: 主动登出
    active --> invalidated: 账户禁用 (is_active=false)
    active --> invalidated: 风控强制下线 (admin)

    expired --> [*]
    invalidated --> [*]

    note right of expired
        终态，不可刷新
        错误�? AUTH_402
    end note

    note right of invalidated
        终态，不可恢复
        错误�? AUTH_003
    end note
```

### 4.4 状态转换代码示�?

```python
# backend/services/auth_service.py
class AuthService:
    def check_token_state(self, token: str) -> str:
        """
        检查Token状�?

        返回: 'active' | 'expired' | 'invalidated'
        """
        try:
            # Step 1: 验证JWT签名
            user = supabase.auth.get_user(token).user

            # Step 2: 查询Session�?
            session = self.db.query(UserSession).filter(
                UserSession.session_id == token[:36]
            ).first()

            if not session:
                return "invalidated"  # Session不存�?

            # Step 3: 检查手动失�?
            if session.invalidated_at is not None:
                return "invalidated"  # 已被手动失效

            # Step 4: 检查自然过�?
            now = datetime.now(timezone.utc)
            if session.expires_at < now:
                return "expired"  # 已自然过�?

            # Step 5: 检查用户状�?
            user = self.db.query(User).filter(User.id == session.user_id).first()
            if not user or not user.is_active:
                return "invalidated"  # 账户已禁�?

            return "active"  # 正常状�?

        except Exception as e:
            if "expired" in str(e).lower():
                return "expired"
            else:
                return "invalidated"
```

---

## 5. 授权机制（Authorization�?

### 5.1 角色系统（RBAC�?

#### 5.1.1 五个角色完整定义

**引用**: SYSTEM_OVERVIEW.md v2.0 - �?�? BUSINESS_RULES.md v3.1 - BR-USER-001

##### 角色1: admin（系统管理员�?

**权限级别**: L5（最高）

**可见范围**:
- �?所有模块无过滤（`WHERE 1=1`�?
- �?可查看所有用户、项目、账户、日报、充值、对账数�?

**可操作范�?*:
- �?创建/编辑/删除用户
- �?修改任何用户的角色（需审计�?
- �?强制解锁任何流程（需填写原因+审计�?
- �?绕过SOD限制（需审计�?
- �?强制标记死号、余额迁�?
- �?查看所有审计日�?

**禁止行为**:
- �?**禁止**在未填写原因的情况下绕过SOD
- �?**禁止**修改已锁定的Ledger记录（除非通过红冲�?

**典型用例**:
- 紧急解决生产问�?
- 修复数据异常
- 用户权限管理
- 系统配置管理

##### 角色2: finance（财务）

**权限级别**: L4

**可见范围**:
- �?充值申请无过滤
- �?Ledger账本无过�?
- �?对账批次无过�?
- �?项目财务数据无过�?

**可操作范�?*:
- �?审批充值申请（终审�?
- �?标记充值支付完�?
- �?创建/关闭对账批次
- �?查看所有Ledger记录
- �?同供应商余额迁移审批

**禁止行为**:
- �?**禁止**创建/编辑用户
- �?**禁止**审核日报（职责分离）
- �?**禁止**修改项目单粉价格（仅admin�?
- �?**禁止**删除Ledger记录

**典型用例**:
- 充值审批（财务终审�?
- 月度对账
- 资金流水监控

##### 角色3: data_operator（数据操作员/户管�?

**权限级别**: L3

**可见范围**:
- �?日报无过滤（全局视野�?
- �?广告账户无过�?
- �?项目无过�?

**可操作范�?*:
- �?审核日报（趋势风控复核）
- �?录入real_spend（真实消耗）
- �?确认conversions_final（最终粉数）
- �?批量导入Excel数据
- �?充值申请数据审核（初审�?

**禁止行为**:
- �?**禁止**审核自己提交的日报（SOD�?
- �?**禁止**财务审批充�?
- �?**禁止**修改已锁定的日报（final_locked�?
- �?**禁止**创建/编辑项目

**典型用例**:
- 审核投手提交的日�?
- 录入供应商后台真实消�?
- 趋势风控复核

##### 角色4: account_manager（客户经理）

**权限级别**: L2

**可见范围**:
- �?仅可见自己管理的项目（`WHERE account_manager_id = :user_id`�?
- �?关联项目的广告账�?
- �?关联项目的日�?

**可操作范�?*:
- �?创建/编辑项目（仅自己管理的）
- �?管理项目成员（project_members�?
- �?发起充值申请（初审�?
- �?分配广告账户给投�?

**禁止行为**:
- �?**禁止**查看其他客户经理的项�?
- �?**禁止**审核日报（职责分离）
- �?**禁止**财务审批充�?
- �?**禁止**修改用户角色

**典型用例**:
- 创建新项�?
- 分配账户给投�?
- 发起充值申�?

##### 角色5: media_buyer（投�?媒体采购�?

**权限级别**: L1（最低）

**可见范围**:
- �?仅可见分配给自己的广告账户（`WHERE assigned_to = :user_id`�?
- �?仅可见自己提交的日报

**可操作范�?*:
- �?提交日报（conversions_raw, raw_spend�?
- �?发起充值申�?
- �?上传充值凭�?

**禁止行为**:
- �?**禁止**查看其他投手的账�?日报
- �?**禁止**审核日报
- �?**禁止**审批充�?
- �?**禁止**修改已提交的日报（仅在raw_submitted状态可修改�?

**典型用例**:
- 每日提交广告账户日报
- 余额不足时申请充�?
- 上传充值凭�?

#### 5.1.2 SOD（职责分离）规则

**定义**: Separation of Duties - 防止内部欺诈和数据篡�?

**引用**: BUSINESS_RULES.md v3.1 - BR-FIN-002, BR-USER-002

**SOD规则矩阵**:

| 业务流程 | 提交角色 | 审核/审批角色 | SOD规则 | 违反错误�?|
|---------|---------|--------------|--------|-----------|
| **日报审核** | media_buyer | data_operator | 提交�?�?审核�?| `BIZ_001` |
| **充值审�?* | media_buyer/account_manager | data_operator (初审) + finance (终审) | 申请�?�?审核�?�?审批�?| `BIZ_001` |
| **对账确认** | data_operator | finance | 提交�?�?确认�?| `BIZ_001` |

**实现示例**:

```python
# backend/services/daily_report_service.py
class DailyReportService:
    def approve_report(self, report_id: int, user: Dict) -> DailyReport:
        """
        审核日报（data_operator操作�?

        业务规则: BR-FIN-002 - 职责分离
        """
        report = self.db.query(DailyReport).filter(
            DailyReport.id == report_id
        ).first()

        if not report:
            raise ResourceNotFoundException(code="BIZ_002", message="日报不存�?)

        # ===== 角色权限校验 =====
        if user["role"] not in ["admin", "data_operator"]:
            raise AuthorizationException(
                code="AUTH_500",
                message="仅数据操作员可以审核日报"
            )

        # ===== SOD检�?=====
        if report.created_by == user["user_id"]:
            raise BusinessRuleException(
                code="BIZ_001",
                message="不能审核自己提交的日报（职责分离�?
            )

        # ===== 执行审核 =====
        with self.db.begin():
            report.status = "trend_ok"
            report.approved_by = user["user_id"]
            report.approved_at = datetime.now(timezone.utc)
            self.db.add(report)

        return report
```

**Admin绕过SOD规则**:

```python
def admin_force_approve(self, report_id: int, user: Dict, reason: str):
    """
    管理员强制审核（绕过SOD�?

    业务规则: BR-AUTH-004 - 最小权限原�?
    """
    if user["role"] != "admin":
        raise AuthorizationException(code="AUTH_500")

    if not reason or len(reason) < 10:
        raise ValidationException(code="VALIDATION_001", message="必须填写详细原因（至�?0字符�?)

    report = self.db.query(DailyReport).filter(DailyReport.id == report_id).first()

    with self.db.begin():
        report.status = "trend_ok"
        report.approved_by = user["user_id"]
        report.approved_at = datetime.now(timezone.utc)

        # 记录审计日志（带ADMIN_OVERRIDE标记�?
        audit_log = AuditLog(
            module="daily_reports",
            action="admin_force_approve",
            entity_id=str(report_id),
            performed_by=user["user_id"],
            role="admin",
            payload_before={"status": "raw_submitted", "created_by": report.created_by},
            payload_after={"status": "trend_ok", "reason": reason},
            tags=["ADMIN_OVERRIDE", "SOD_BYPASS"]
        )
        self.db.add(audit_log)

    return report
```

### 5.2 权限矩阵（Permission Matrix�?

**完整权限表（模块 × API × 五角色）**:

| 模块/API | admin | finance | data_operator | account_manager | media_buyer |
|---------|-------|---------|---------------|----------------|-------------|
| **用户管理 (Users)** |
| GET /users | �?全部 | 🔍 只读 | 🔍 只读 | 🔍 只读 | �?|
| POST /users | �?| �?| �?| �?| �?|
| PUT /users/{id} | �?| �?| �?| �?| �?|
| PUT /users/me | �?| �?| �?| �?| �?|
| POST /users/{id}/force-logout | �?| �?| �?| �?| �?|
| **项目管理 (Projects)** |
| GET /projects | �?全部 | 🔍 全部 | 🔍 全部 | 🔍 仅自己管理的 | �?|
| POST /projects | �?| �?| �?| �?| �?|
| PUT /projects/{id} | �?| �?| �?| �?(仅自己管理的) | �?|
| POST /projects/{id}/archive | �?| �?| �?| �?(仅自己管理的) | �?|
| **日报管理 (Daily Reports)** |
| GET /daily-reports | �?全部 | 🔍 全部 | 🔍 全部 | 🔍 仅所管项�?| 🔍 仅自己提交的 |
| POST /daily-reports | �?| �?| �?| �?| �?|
| PUT /daily-reports/{id} | �?| �?| �?| �?| �?(仅raw_submitted) |
| POST /daily-reports/{id}/approve | �?| �?| �?(禁止审核自己提交�? | �?| �?|
| POST /daily-reports/{id}/confirm-final | �?| �?| �?| �?| �?|
| **充值管�?(Topup Requests)** |
| GET /topup-requests | �?全部 | �?全部 | 🔍 全部 | 🔍 仅所管项�?| 🔍 仅自己申请的 |
| POST /topup-requests | �?| �?| �?| �?| �?|
| POST /topup-requests/{id}/review | �?| �?| �?(初审) | �?| �?|
| POST /topup-requests/{id}/approve | �?| �?(终审) | �?| �?| �?|
| POST /topup-requests/{id}/mark-paid | �?| �?| �?| �?| �?|
| **账本管理 (Ledger)** |
| GET /ledger | �?全部 | �?全部 | 🔍 只读 | �?| �?|
| POST /ledger/reversal | �?| �?| �?| �?| �?|
| **对账管理 (Reconciliation)** |
| GET /reconciliations | �?全部 | �?全部 | 🔍 只读 | �?| �?|
| POST /reconciliations | �?| �?| �?| �?| �?|
| POST /reconciliations/{id}/close | �?| �?| �?| �?| �?|

**图例**:
- �?完整权限（CRUD�?
- 🔍 只读权限（Read-only�?
- �?禁止访问

### 5.3 数据权限过滤（Data Access Filtering�?

**引用**: SYSTEM_OVERVIEW.md v2.0 - �?.2�?

#### 5.3.1 过滤规则矩阵

| 角色 | 模块 | SQL过滤条件 | 说明 |
|-----|------|-----------|------|
| **admin** | 所有模�?| `WHERE 1=1` | 无过�?|
| **finance** | 充�?账本/对账 | `WHERE 1=1` | 无过�?|
| **data_operator** | 日报/账户/项目 | `WHERE 1=1` | 全局视野 |
| **account_manager** | 项目 | `WHERE account_manager_id = :user_id` | 仅自己管理的项目 |
| **account_manager** | 日报 | `JOIN ad_accounts aa JOIN projects p WHERE p.account_manager_id = :user_id` | 仅所管项目的日报 |
| **media_buyer** | 日报 | `WHERE created_by = :user_id` | 仅自己提交的 |
| **media_buyer** | 账户 | `WHERE assigned_to = :user_id` | 仅分配给自己�?|

#### 5.3.2 Service层实现（绝不能在Router层过滤）

**示例1: 投手查询日报列表**

```python
# backend/services/daily_report_service.py
class DailyReportService:
    def list_reports(self, filters: Dict, user: Dict, pagination: PaginationParams):
        """
        获取日报列表（按角色自动过滤数据范围�?

        业务规则: BR-AUTH-004 - 最小权限原�?
        """
        query = self.db.query(DailyReport)

        # ===== 按角色自动过�?=====
        user_role = user["role"]
        user_id = user["user_id"]

        if user_role == "admin":
            pass  # 可见所有数�?

        elif user_role == "data_operator":
            pass  # 全局视野

        elif user_role == "account_manager":
            # 仅可见自己管理的项目的日�?
            managed_project_ids = (
                self.db.query(Project.id)
                .filter(Project.account_manager_id == user_id)
                .subquery()
            )
            query = query.join(AdAccount).filter(
                AdAccount.project_id.in_(managed_project_ids)
            )

        elif user_role == "media_buyer":
            # 仅可见自己提交的日报
            query = query.filter(DailyReport.created_by == user_id)

        else:
            # 其他角色（如finance）禁止访�?
            raise AuthorizationException(code="AUTH_500", message="权限不足")

        # ===== 应用额外过滤条件 =====
        if filters.get("report_date"):
            query = query.filter(DailyReport.report_date == filters["report_date"])

        if filters.get("status"):
            query = query.filter(DailyReport.status == filters["status"])

        # ===== 分页 =====
        total = query.count()
        reports = query.offset((pagination.page - 1) * pagination.page_size)\
                       .limit(pagination.page_size)\
                       .all()

        return {
            "items": reports,
            "total": total,
            "page": pagination.page,
            "page_size": pagination.page_size
        }
```

**示例2: SQL JOIN过滤（客户经理查询日报）**

```python
# backend/services/daily_report_service.py (account_manager专用)
def list_reports_for_account_manager(self, user_id: str, filters: Dict):
    """
    客户经理查询日报（仅可见自己管理的项目的日报�?
    """
    query = (
        self.db.query(DailyReport)
        .join(AdAccount, DailyReport.ad_account_id == AdAccount.id)
        .join(Project, AdAccount.project_id == Project.id)
        .filter(Project.account_manager_id == user_id)  # �?关键过滤
    )

    # 应用额外过滤
    if filters.get("report_date"):
        query = query.filter(DailyReport.report_date == filters["report_date"])

    return query.all()
```

---

## 6. Auth API SoT

### 6.1 POST /api/v1/auth/login

**功能**: 用户登录

**Method**: `POST`

**URL**: `/api/v1/auth/login`

**认证**: �?不需要（公开端点�?

**角色要求**: �?无（任何人可调用�?

**幂等�?*: �?非幂等（每次生成新Token�?

#### 请求参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|------|------|------|---------|------|
| `email` | string | �?| 标准邮箱格式 | 用户邮箱 |
| `password` | string | �?| 长度�? | 密码 |

**请求示例**:

```json
{
  "email": "alice@example.com",
  "password": "SecurePass123!"
}
```

#### 响应字段

**成功响应（HTTP 200�?*:

| 字段 | 类型 | 说明 |
|------|------|------|
| `success` | boolean | 固定为`true` |
| `message` | string | "登录成功" |
| `data.access_token` | string | JWT Access Token |
| `data.refresh_token` | string | Refresh Token |
| `data.expires_in` | integer | Access Token有效期（秒），默�?600 |
| `data.token_type` | string | 固定�?Bearer" |
| `data.user` | object | 用户信息 |
| `data.user.id` | string (UUID) | 用户ID |
| `data.user.email` | string | 邮箱 |
| `data.user.username` | string | 用户�?|
| `data.user.full_name` | string | 真实姓名 |
| `data.user.role` | string | 业务角色（admin/finance/...�?|

**成功响应示例**:

```json
{
  "success": true,
  "message": "登录成功",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "v1.MjIzNDU2Nzg5MA...",
    "expires_in": 3600,
    "token_type": "Bearer",
    "user": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "alice@example.com",
      "username": "alice",
      "full_name": "Alice Wang",
      "role": "media_buyer"
    }
  }
}
```

#### 错误码白名单

| 错误�?| HTTP状态码 | 触发条件 |
|--------|-----------|---------|
| `AUTH_001` | 401 | 用户名或密码错误 |
| `AUTH_002` | 403 | 账户已被禁用（`is_active=false`�?|
| `AUTH_004` | 404 | 用户不存�?|
| `VALIDATION_001` | 400 | 参数校验失败（邮箱格式错误、密码长度不足） |

**错误响应示例**:

```json
{
  "success": false,
  "message": "账户已被禁用",
  "code": "AUTH_002"
}
```

#### 实现伪代�?

```python
# backend/routers/auth.py
@router.post("/api/v1/auth/login")
async def login(credentials: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """
    用户登录

    业务规则: BR-AUTH-001 - 用户角色唯一�?
    """
    # Step 1: Supabase认证
    try:
        auth_response = supabase.auth.sign_in_with_password({
            "email": credentials.email,
            "password": credentials.password
        })
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"success": False, "message": "用户名或密码错误", "code": "AUTH_001"}
        )

    # Step 2: 查询业务users�?
    user = db.query(User).filter(User.id == auth_response.user.id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"success": False, "message": "用户不存在或已被删除", "code": "AUTH_004"}
        )

    # Step 3: 验证账户状�?
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"success": False, "message": "账户已被禁用", "code": "AUTH_002"}
        )

    # Step 4: 更新登录信息
    user.last_login_at = datetime.now(timezone.utc)
    user.last_login_ip = request.client.host
    db.commit()

    # Step 5: 创建Session记录
    new_session = UserSession(
        user_id=user.id,
        session_id=auth_response.session.access_token[:36],
        ip_address=request.client.host,
        user_agent=request.headers.get("User-Agent"),
        expires_at=datetime.fromtimestamp(auth_response.session.expires_at, timezone.utc)
    )
    db.add(new_session)
    db.commit()

    # Step 6: 返回成功响应
    return success_response(
        message="登录成功",
        data={
            "access_token": auth_response.session.access_token,
            "refresh_token": auth_response.session.refresh_token,
            "expires_in": 3600,
            "token_type": "Bearer",
            "user": {
                "id": str(user.id),
                "email": user.email,
                "username": user.username,
                "full_name": user.full_name,
                "role": user.role
            }
        }
    )
```

---

### 6.2 POST /api/v1/auth/refresh

**功能**: 刷新Access Token

**Method**: `POST`

**URL**: `/api/v1/auth/refresh`

**认证**: �?不需要（使用Refresh Token�?

**角色要求**: �?�?

**幂等�?*: �?非幂等（每次生成新Token�?

#### 请求参数

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `refresh_token` | string | �?| Refresh Token |

**请求示例**:

```json
{
  "refresh_token": "v1.MjIzNDU2Nzg5MA..."
}
```

#### 响应字段

**成功响应（HTTP 200�?*:

```json
{
  "success": true,
  "message": "Token刷新成功",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "v1.MzkwMTIzNDU2Nzg...",  // 新的Refresh Token（如果启用Rotation�?
    "expires_in": 3600,
    "token_type": "Bearer"
  }
}
```

#### 错误码白名单

| 错误�?| HTTP状态码 | 触发条件 |
|--------|-----------|---------|
| `AUTH_005` | 401 | Refresh Token无效、过期或已被使用 |
| `AUTH_003` | 401 | Refresh Token已被撤销（登出、强制下线） |
| `AUTH_002` | 403 | 账户已被禁用 |

---

### 6.3 POST /api/v1/auth/logout

**功能**: 用户登出

**Method**: `POST`

**URL**: `/api/v1/auth/logout`

**认证**: �?需要（Bearer Token�?

**角色要求**: �?所有已登录用户

**幂等�?*: �?幂等（重复登出返回成功）

#### 请求参数

�?无（从Token中提取user_id�?

#### 响应字段

**成功响应（HTTP 200�?*:

```json
{
  "success": true,
  "message": "登出成功"
}
```

#### 错误码白名单

| 错误�?| HTTP状态码 | 触发条件 |
|--------|-----------|---------|
| `AUTH_400` | 401 | 未提供Token |
| `AUTH_401` | 401 | Token无效 |
| `AUTH_402` | 401 | Token已过�?|

#### 实现伪代�?

```python
@router.post("/api/v1/auth/logout")
async def logout(
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    用户登出
    """
    token = credentials.credentials

    # Step 1: 撤销Supabase Session
    try:
        supabase.auth.sign_out()
    except Exception:
        pass  # 忽略Supabase错误（可能已过期�?

    # Step 2: 标记Session为失�?
    session = db.query(UserSession).filter(
        UserSession.session_id == token[:36]
    ).first()

    if session:
        session.invalidated_at = datetime.now(timezone.utc)
        db.commit()

    return success_response(message="登出成功")
```

---

### 6.4 GET /api/v1/auth/me

**功能**: 获取当前用户信息

**Method**: `GET`

**URL**: `/api/v1/auth/me`

**认证**: �?需要（Bearer Token�?

**角色要求**: �?所有已登录用户

**幂等�?*: �?幂等（只读操作）

#### 请求参数

�?无（从Token中提取user_id�?

#### 响应字段

**成功响应（HTTP 200�?*:

```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "alice",
    "full_name": "Alice Wang",
    "email": "alice@example.com",
    "role": "media_buyer",
    "department": "市场�?,
    "position": "投手",
    "is_active": true,
    "is_verified": true,
    "last_login_at": "2025-01-22T10:30:00Z",
    "preferences": {
      "theme": "dark",
      "sidebar_collapsed": false
    },
    "notification_settings": {
      "email_enabled": true,
      "notify_on_report_approved": true
    }
  }
}
```

#### 错误码白名单

| 错误�?| HTTP状态码 | 触发条件 |
|--------|-----------|---------|
| `AUTH_400` | 401 | 未提供Token |
| `AUTH_401` | 401 | Token无效 |
| `AUTH_402` | 401 | Token已过�?|
| `AUTH_002` | 403 | 账户已被禁用 |

---

## 7. 错误码（Auth错误码SoT�?

**引用**: ERROR_CODES_SOT.md v2.1 - �?.1�?

### 7.1 认证错误码（AUTH_�?

| 错误�?| HTTP状态码 | 消息 | 触发场景 | 状�?|
|--------|-----------|------|----------|------|
| `AUTH_001` | 401 | 用户名或密码错误 | 登录验证失败 | USED |
| `AUTH_002` | 403 | 账户已被禁用 | `users.is_active = false` | USED |
| `AUTH_003` | 401 | 令牌已被撤销 | 主动登出、多端登录、强制下�?| USED |
| `AUTH_004` | 404 | 用户不存在或已被删除 | `users`表无记录 | USED |
| `AUTH_005` | 401 | 令牌刷新失败 | Refresh Token无效、过期或已被使用 | RESERVED |
| `AUTH_100` | 400 | 邮箱已被注册 | 注册时邮箱重�?| USED |
| `AUTH_400` | 401 | 未提供认证令�?| 缺少`Authorization` Header | USED |
| `AUTH_401` | 401 | 无效的认证令�?| Token格式错误、签名验证失�?| USED |
| `AUTH_402` | 401 | 令牌已过�?| Token超过TTL | USED |
| `AUTH_500` | 403 | 权限不足 | 角色不满足权限要�?| USED |
| `AUTH_501` | 403 | 角色权限不足 | 未分配有效角�?| RESERVED |

### 7.2 业务错误码（BIZ_�?

| 错误�?| HTTP状态码 | 消息 | 触发场景 | 状�?|
|--------|-----------|------|----------|------|
| `BIZ_001` | 400 | 无效的操�?| 违反业务规则（如SOD�?| USED |
| `BIZ_002` | 404 | 资源不存�?| 根据ID查询资源未找�?| USED |

### 7.3 典型响应结构

**成功响应**:

```json
{
  "success": true,
  "message": "操作成功",
  "data": { ... }
}
```

**错误响应**:

```json
{
  "success": false,
  "message": "权限不足",
  "code": "AUTH_500"
}
```

### 7.4 前端错误处理示例

```typescript
// frontend/lib/api.ts
export async function apiFetch<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const { data: { session } } = await supabase.auth.getSession();

  if (!session) {
    window.location.href = '/login';
    throw new Error('未登�?);
  }

  const response = await fetch(endpoint, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${session.access_token}`,
      ...options?.headers
    }
  });

  const data: ApiResponse<T> = await response.json();

  if (!data.success) {
    // 统一错误处理
    switch (data.code) {
      case 'AUTH_400':
      case 'AUTH_401':
      case 'AUTH_402':
        // Token问题，跳转登�?
        window.location.href = '/login';
        break;

      case 'AUTH_002':
        // 账户禁用
        alert('您的账户已被禁用，请联系管理�?);
        await supabase.auth.signOut();
        window.location.href = '/login';
        break;

      case 'AUTH_500':
        // 权限不足
        alert(`权限不足: ${data.message}`);
        break;

      case 'BIZ_001':
        // 业务规则违反
        alert(`操作失败: ${data.message}`);
        break;

      default:
        alert(`错误: ${data.message}`);
    }
    throw new Error(data.message);
  }

  return data.data as T;
}
```

---

## 8. 审计要求（Audit Specification�?

### 8.1 必须记录审计日志的操�?

**引用**: DATA_SCHEMA.md v5.2 - �?.1.4�?(audit_logs�?

| 操作类型 | 触发场景 | 必填字段 |
|---------|---------|---------|
| **登录** | 成功登录 | user_id, role, ip_address, user_agent |
| **登出** | 主动登出 | user_id, role |
| **Token刷新** | 刷新Access Token | user_id, role, ip_address |
| **强制下线** | Admin强制用户下线 | performed_by, entity_id (被下线的user_id), reason |
| **角色变更** | 修改用户角色 | performed_by, entity_id, payload_before, payload_after |
| **绕过SOD** | Admin强制审核（绕过职责分离） | performed_by, entity_id, tags=["ADMIN_OVERRIDE", "SOD_BYPASS"], reason |
| **账户禁用** | 设置`is_active=false` | performed_by, entity_id, reason |
| **账户启用** | 设置`is_active=true` | performed_by, entity_id, reason |
| **密码修改** | 用户修改密码 | user_id, ip_address |

### 8.2 audit_logs表字�?

```sql
CREATE TABLE audit_logs (
    id BIGSERIAL PRIMARY KEY,
    module VARCHAR(100) NOT NULL,           -- 业务模块名（�?"auth", "users", "daily_reports"�?
    action VARCHAR(50) NOT NULL,            -- 操作类型（如 "login", "force_logout", "role_change"�?
    entity_id VARCHAR(64),                  -- 关联实体主键或编�?
    performed_by UUID REFERENCES users(id), -- 操作者ID
    role VARCHAR(20),                       -- 操作者角�?
    ip_address INET,                        -- IP地址
    user_agent TEXT,                        -- User-Agent
    payload_before JSONB,                   -- 操作前数�?
    payload_after JSONB,                    -- 操作后数�?
    tags TEXT[],                            -- 标签数组（如 ["ADMIN_OVERRIDE", "SOD_BYPASS"]�?
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE INDEX idx_audit_logs_module ON audit_logs(module);
CREATE INDEX idx_audit_logs_performed_by ON audit_logs(performed_by);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);
CREATE INDEX idx_audit_logs_tags ON audit_logs USING GIN(tags);
```

### 8.3 审计日志记录示例

**示例1: 登录审计**

```python
# backend/routers/auth.py (login endpoint)
def login(...):
    # ... 登录成功�?

    audit_log = AuditLog(
        module="auth",
        action="login",
        entity_id=str(user.id),
        performed_by=user.id,
        role=user.role,
        ip_address=request.client.host,
        user_agent=request.headers.get("User-Agent"),
        payload_after={
            "username": user.username,
            "email": user.email,
            "login_time": datetime.now(timezone.utc).isoformat()
        }
    )
    db.add(audit_log)
    db.commit()
```

**示例2: 强制下线审计**

```python
# backend/routers/users.py (force_logout endpoint)
def force_logout(user_id: str, reason: str, current_user: Dict, ...):
    # ... 强制下线逻辑

    audit_log = AuditLog(
        module="auth",
        action="force_logout",
        entity_id=user_id,
        performed_by=current_user["user_id"],
        role=current_user["role"],
        ip_address=request.client.host,
        payload_before={"active_sessions": len(sessions)},
        payload_after={"reason": reason, "invalidated_sessions": len(sessions)},
        tags=["ADMIN_OVERRIDE"]
    )
    db.add(audit_log)
    db.commit()
```

**示例3: 绕过SOD审计**

```python
# backend/services/daily_report_service.py (admin_force_approve)
def admin_force_approve(report_id: int, user: Dict, reason: str):
    # ... 强制审核逻辑

    audit_log = AuditLog(
        module="daily_reports",
        action="admin_force_approve",
        entity_id=str(report_id),
        performed_by=user["user_id"],
        role="admin",
        payload_before={"status": "raw_submitted", "created_by": report.created_by},
        payload_after={"status": "trend_ok", "reason": reason},
        tags=["ADMIN_OVERRIDE", "SOD_BYPASS"]
    )
    db.add(audit_log)
    db.commit()
```

### 8.4 审计日志查询API

**GET /api/v1/audit-logs**

**角色要求**: `admin` (仅管理员可查�?

**查询参数**:
- `module`: 模块名（可选）
- `action`: 操作类型（可选）
- `performed_by`: 操作者ID（可选）
- `start_date`: 开始日期（可选）
- `end_date`: 结束日期（可选）
- `tags`: 标签过滤（可选，�?`ADMIN_OVERRIDE`�?

---

## 9. 安全策略（Security Rules�?

### 9.1 Zero Trust原则

**定义**: 永远不信任任何客户端传来的用户身份信�?

**强制规则**:
- �?**必须**从Token中提取user_id�?*禁止**前端传递user_id
- �?**必须**在Service层验证数据归属，**禁止**信任前端过滤
- �?**必须**在后端验证角色权限，**禁止**仅依赖前端路由守�?

**错误示例**:

```python
# �?错误：信任前端传递的user_id
@router.post("/daily-reports")
def create_report(report: DailyReportCreate):
    # 前端可以伪造created_by
    new_report = DailyReport(
        created_by=report.created_by,  # �?危险�?
        ...
    )
```

**正确示例**:

```python
# �?正确：从Token提取user_id
@router.post("/daily-reports")
def create_report(
    report: DailyReportCreate,
    current_user: Dict = Depends(get_current_user)  # �?从Token提取
):
    new_report = DailyReport(
        created_by=current_user["user_id"],  # �?安全
        ...
    )
```

### 9.2 禁止前端解析JWT

**原因**:
- �?JWT Payload未加密，任何人可解码
- �?前端无法验证JWT签名
- �?前端可伪造解析结�?

**禁止行为**:

```typescript
// �?错误：前端解析JWT获取user_id
const token = session.access_token;
const payload = JSON.parse(atob(token.split('.')[1]));  // �?危险�?
const userId = payload.sub;  // 用于业务逻辑
```

**正确做法**:

```typescript
// �?正确：调用GET /auth/me获取用户信息
const user = await apiFetch<User>('/api/v1/auth/me');
const userId = user.id;  // 由后端验证Token后返�?
```

### 9.3 禁止前端传user_id修改他人数据

**场景**: 用户尝试修改他人的日�?

**错误示例**:

```typescript
// �?错误：前端传递user_id
await apiFetch('/api/v1/daily-reports/123', {
  method: 'PUT',
  body: JSON.stringify({
    conversions_raw: 100,
    created_by: 'other-user-id'  // �?前端可伪�?
  })
});
```

**后端防御**:

```python
# �?正确：后端验证归�?
@router.put("/daily-reports/{report_id}")
def update_report(
    report_id: int,
    updates: DailyReportUpdate,
    current_user: Dict = Depends(get_current_user)
):
    report = db.query(DailyReport).filter(DailyReport.id == report_id).first()

    # 验证归属（仅允许修改自己的日报）
    if report.created_by != current_user["user_id"] and current_user["role"] != "admin":
        raise AuthorizationException(code="AUTH_500", message="权限不足")

    # 执行更新（忽略前端传递的created_by�?
    report.conversions_raw = updates.conversions_raw
    # 绝不更新created_by字段
    db.commit()
    return report
```

### 9.4 CSRF防护

**Supabase Auth自动防护**:
- �?Supabase使用HTTP-only Cookie存储Refresh Token
- �?Access Token通过`Authorization` Header传递（非Cookie�?
- �?前端使用`@supabase/supabase-js`自动处理

**无需额外配置**（Supabase已内置）

### 9.5 Token重放攻击防护

**防护措施**:

1. **Refresh Token Rotation** (已启�?
   - �?每次刷新后旧Refresh Token立即失效
   - �?重复使用旧Refresh Token �?返回`AUTH_003`

2. **Session绑定IP**（可选，当前未启用）
   ```python
   # 在Token验证时检查IP
   def get_current_user(...):
       session = db.query(UserSession).filter(
           UserSession.session_id == token[:36]
       ).first()

       # 可选：检查IP是否变化
       if session.ip_address != request.client.host:
           # 警告或拒绝（根据安全策略�?
           pass
   ```

3. **短TTL** (Access Token 1小时)
   - �?即使Token泄露，窗口期�?小时

---

## 10. 测试矩阵（Auth Test Plan�?

### 10.1 登录测试

| 测试用例编号 | 测试场景 | 输入 | 期望输出 | 优先�?|
|------------|---------|------|---------|--------|
| TC-AUTH-001 | 正常登录 | 正确的email+password | HTTP 200, 返回token | P0 |
| TC-AUTH-002 | 密码错误 | 错误的password | HTTP 401, `AUTH_001` | P0 |
| TC-AUTH-003 | 邮箱不存�?| 不存在的email | HTTP 401, `AUTH_001` | P0 |
| TC-AUTH-004 | 账户已禁�?| `is_active=false`的用�?| HTTP 403, `AUTH_002` | P0 |
| TC-AUTH-005 | 参数校验失败 | 邮箱格式错误 | HTTP 400, `VALIDATION_001` | P1 |

### 10.2 Token过期测试

| 测试用例编号 | 测试场景 | 输入 | 期望输出 | 优先�?|
|------------|---------|------|---------|--------|
| TC-AUTH-006 | Token过期 | 过期的Access Token | HTTP 401, `AUTH_402` | P0 |
| TC-AUTH-007 | 过期Token刷新（失败） | 过期的Refresh Token | HTTP 401, `AUTH_005` | P0 |
| TC-AUTH-008 | Token未过�?| 有效的Access Token | 正常返回业务数据 | P0 |

### 10.3 刷新测试

| 测试用例编号 | 测试场景 | 输入 | 期望输出 | 优先�?|
|------------|---------|------|---------|--------|
| TC-AUTH-009 | 正常刷新 | 有效的Refresh Token | HTTP 200, 返回新token | P0 |
| TC-AUTH-010 | Refresh Token重复使用 | 已使用过的Refresh Token | HTTP 401, `AUTH_003` | P0 |
| TC-AUTH-011 | 刷新后旧Token失效 | 使用刷新前的旧Access Token | HTTP 401, `AUTH_402` | P1 |

### 10.4 越权测试

| 测试用例编号 | 测试场景 | 输入 | 期望输出 | 优先�?|
|------------|---------|------|---------|--------|
| TC-AUTHZ-001 | 投手提交日报（允许） | media_buyer | POST /daily-reports (自己账户) | HTTP 201 | P0 |
| TC-AUTHZ-002 | 投手提交他人账户日报（禁止） | media_buyer | POST /daily-reports (他人账户) | HTTP 403, `AUTH_500` | P0 |
| TC-AUTHZ-003 | 投手审核日报（禁止） | media_buyer | POST /daily-reports/{id}/approve | HTTP 403, `AUTH_500` | P0 |
| TC-AUTHZ-004 | 数据操作员审核日报（允许�?| data_operator | POST /daily-reports/{id}/approve | HTTP 200 | P0 |
| TC-AUTHZ-005 | SOD检�?- 自我审核（禁止） | data_operator | 审核自己提交的日�?| HTTP 400, `BIZ_001` | P0 |
| TC-AUTHZ-006 | 管理员强制审核（允许�?| admin | admin_force_approve(reason="...") | HTTP 200, 审计日志含`ADMIN_OVERRIDE` | P0 |
| TC-AUTHZ-007 | 管理员强制审核缺少原因（禁止�?| admin | admin_force_approve(reason="") | HTTP 400, `VALIDATION_001` | P1 |

### 10.5 多设备登录测�?

| 测试用例编号 | 测试场景 | 输入 | 期望输出 | 优先�?|
|------------|---------|------|---------|--------|
| TC-SESSION-001 | 多设备同时登�?| 用户在设备A和设备B登录 | 两个设备都可正常访问 | P0 |
| TC-SESSION-002 | 设备A登出 | 设备A调用logout | 设备A无法访问，设备B正常 | P0 |
| TC-SESSION-003 | 强制下线所有设�?| Admin调用force_logout | 所有设备均返回`AUTH_003` | P0 |

### 10.6 SOD测试

| 测试用例编号 | 测试场景 | 输入 | 期望输出 | 优先�?|
|------------|---------|------|---------|--------|
| TC-SOD-001 | 投手提交+数据员审核（允许�?| 投手A提交，数据员B审核 | HTTP 200 | P0 |
| TC-SOD-002 | 投手提交+同一投手审核（禁止） | 投手A提交，投手A审核 | HTTP 403, `AUTH_500` | P0 |
| TC-SOD-003 | 数据员提�?同一数据员审核（禁止�?| 数据员A提交并尝试审�?| HTTP 400, `BIZ_001` | P0 |
| TC-SOD-004 | Admin绕过SOD（允�?审计�?| Admin强制审核自己提交的日�?| HTTP 200, 审计日志含`SOD_BYPASS` | P0 |

### 10.7 风控场景测试

| 测试用例编号 | 测试场景 | 输入 | 期望输出 | 优先�?|
|------------|---------|------|---------|--------|
| TC-SECURITY-001 | 账户被禁用后访问API | `is_active=false`的用户访问API | HTTP 403, `AUTH_002` | P0 |
| TC-SECURITY-002 | 强制下线后刷新Token | 被强制下线的用户刷新Token | HTTP 401, `AUTH_003` | P0 |
| TC-SECURITY-003 | 密码修改后旧Token失效 | 用户修改密码后使用旧Token | HTTP 401, `AUTH_003` | P1 |

---

## 11. 参考文�?

本文档基于以下SoT文档编写�?

| SoT文档 | 版本 | 引用章节 | 引用次数 |
|---------|------|---------|---------|
| **DATA_SCHEMA.md** | v5.1 | 3.1.1 users�? 3.1.3 user_sessions�? 3.1.4 audit_logs�?| 15+ |
| **BUSINESS_RULES.md** | v3.1 | BR-AUTH-001~004, BR-USER-001~003, BR-FIN-002 | 12+ |
| **ERROR_CODES_SOT.md** | v2.1 | 4.1 认证授权类（AUTH_*�? 4.2 业务逻辑类（BIZ_*�?| 8+ |
| **STATE_MACHINE.md** | v2.5 | 角色定义、操作者规�?| 3+ |
| **SYSTEM_OVERVIEW.md** | v2.0 | �?�?- 核心角色与职�?| 5+ |
| **API_SOT.md** | v9.0 | �?�?- 统一规范（认证与授权�?| 4+ |

---

## 12. 版本历史

| 版本 | 日期 | 变更内容 | 作�?|
|------|------|---------|------|
| v1.0 | 2025-01-22 | 初始版本 | 系统架构团队 |
| v2.0 | 2025-01-22 | **正式SoT�?*<br>- 补全Auth状态机定义<br>- 补全4个Auth API端点完整规范<br>- 补全SOD规则矩阵与实�?br>- 补全数据隔离Service层实�?br>- 补全Token生命周期（TTL、Rotation、失效策略）<br>- 补全安全策略（Zero Trust、CSRF、重放攻击防护）<br>- 补全测试矩阵�?大类测试场景�?br>- 补全审计日志规范 | 系统架构团队 |

---

**文档性质**: 认证授权领域唯一真相源（SoT�?
**执行级别**: 🔴 强制执行（PR必查�?
**违规处理**: PR自动拒绝 / 代码回滚
**最后更�?*: 2025-01-22
**版本**: v2.0 (正式SoT�?

---

**END OF DOCUMENT**
