# 认证与授权规范文档（AUTH_SPEC）

**文档版本**: v2.0  
**最后更新**: 2025-01-20  
**维护团队**: 系统架构团队  
**文档定位**: 认证授权规范 SoT，与系统实现规范完全对齐

---

## 📑 目录

1. [文档定位与 SoT 关系](#1-文档定位与-sot-关系)
2. [认证体系架构](#2-认证体系架构)
3. [Supabase Auth + 应用层角色校验模型](#3-supabase-auth--应用层角色校验模型)
4. [Token 生命周期](#4-token-生命周期)
5. [应用层权限校验流程](#5-应用层权限校验流程)
6. [开发规范](#6-开发规范)
7. [错误码引用方式](#7-错误码引用方式)
8. [安全基线](#8-安全基线)
9. [未来扩展](#9-未来扩展)
10. [版本历史](#10-版本历史)

---

## 1. 文档定位与 SoT 关系

### 1.1 文档定位

本文档是 AI_AD_SPEND 系统认证与授权架构的**规范层 SoT**，定义：

1. **认证架构**：Supabase Auth 与应用层的集成方式
2. **权限模型**：应用层 RBAC 实现规范（API 层 + Service 层）
3. **开发规范**：后端如何正确使用 Supabase Auth 进行认证授权

**重要说明**：
- 本文档**不定义**角色模型（引用 `AI_AD_SYSTEM_MAIN_DOCUMENT.md`）
- 本文档**不定义**错误码（引用 `ERROR_CODES.md`）
- 本文档**不定义**数据模型（引用 `DATA_SCHEMA.md`）
- 本文档**不定义**RLS 策略（引用 `RLS_POLICIES.md`，当前未启用）

### 1.2 SoT 互锁关系

```
AUTH_SPEC.md (本文档)
    ├─→ AI_AD_SYSTEM_MAIN_DOCUMENT.md (角色定义、架构约束)
    ├─→ ERROR_CODES.md (认证错误码)
    ├─→ DATA_SCHEMA.md (users 表结构)
    ├─→ RLS_POLICIES.md (RLS 策略，当前未启用)
    └─→ API_DEVELOPMENT_FLOW.md (API 开发流程)
```

**强制规则**：
- 任何认证相关变更必须先更新本文档
- 角色定义变更必须同步更新 `AI_AD_SYSTEM_MAIN_DOCUMENT.md`
- 错误码变更必须同步更新 `ERROR_CODES.md`
- RLS 策略变更必须同步更新 `RLS_POLICIES.md`

### 1.3 适用范围

- **后端开发**：FastAPI 路由鉴权、Service 层权限校验、依赖注入
- **前端开发**：登录流程、Token 管理、路由守卫
- **安全运维**：Token 策略配置、审计日志

**不适用范围**：
- 数据库 RLS 策略设计（当前未启用，参考 `RLS_POLICIES.md` 作为未来扩展）
- 角色模型定义（引用 `AI_AD_SYSTEM_MAIN_DOCUMENT.md` 第 3 章）
- 错误码定义（引用 `ERROR_CODES.md` 第 4.1 章）

---

## 2. 认证体系架构

### 2.1 当前架构（基于 AI_AD_SYSTEM_MAIN_DOCUMENT.md）

```
┌─────────────────────────────────────────────────────────────┐
│                    客户端（Browser/Mobile）                   │
│              存储 Access Token + Refresh Token              │
│              （通过 Supabase Auth SDK）                      │
└────────────────────────────┬────────────────────────────────┘
                              │ Bearer Token
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  应用层（FastAPI Backend）                    │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    │
│  │ Supabase     │ -> │  用户查询    │ -> │  权限校验    │    │
│  │ Auth 验证    │    │ (users 表)   │    │ (Role Check) │    │
│  └──────────────┘    └──────────────┘    └──────────────┘    │
└────────────────────────────┬────────────────────────────────┘
                              │ SQL Query (Service 层过滤)
                              ▼
┌─────────────────────────────────────────────────────────────┐
│             数据库层（PostgreSQL，当前未启用 RLS）             │
│  - 所有权限通过 Service 层 RBAC + 查询过滤实现                │
│  - RLS 作为未来扩展（参考 RLS_POLICIES.md）                   │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 认证流程

#### 2.2.1 用户注册与首次登录

```
1. 前端调用 Supabase Auth API 注册用户
   POST /auth/v1/signup
   Body: { email, password }

2. Supabase 创建 auth.users 记录（UUID 主键）

3. Backend 触发器/Webhook 在应用 users 表创建用户记录
   INSERT INTO users (id, email, role, ...)
   VALUES (auth_user_uuid, email, 'media_buyer', ...)
   （字段定义参考 DATA_SCHEMA.md 3.1.1）

4. Supabase 返回 Access Token + Refresh Token
   - Access Token: 短期有效（默认 1 小时，可配置）
   - Refresh Token: 长期有效（默认 30 天，可配置）
```

#### 2.2.2 后续登录

```
1. 前端调用 Supabase Auth API 登录
   POST /auth/v1/token?grant_type=password
   Body: { email, password }

2. Supabase 验证凭证，返回 JWT Token

3. Frontend 存储 Token（通过 Supabase SDK 管理）

4. 所有 API 请求携带 Token
   Authorization: Bearer <access_token>
```

#### 2.2.3 Token 验证（每次 API 请求）

**实现方式**：通过 Supabase Auth SDK 验证 Token，禁止手写 JWT 验证逻辑。

```python
# backend/deps/supabase_auth.py

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    通过 Supabase Auth 验证 Token 并返回用户信息
    
    流程：
    1. 提取 Bearer Token
    2. 调用 Supabase Auth API 验证 Token（supabase.auth.get_user）
    3. 从 JWT 解析 user_id（sub）
    4. 从 users 表查询完整用户信息（含 role）
    5. 返回用户对象
    
    禁止：
    - 手写 JWT 签名验证
    - 手写 Token 黑名单检查
    - 手写 jti 验证
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "AUTH_400", "message": "未提供认证令牌"}
        )
    
    # 通过 Supabase Auth 验证 Token
    user_data = await supabase_auth_service.verify_token(credentials.credentials)
    
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "AUTH_401", "message": "无效的认证令牌"}
        )
    
    return user_data
```

### 2.3 会话管理

- **无状态会话**：不使用服务端 Session，完全依赖 Supabase Auth 的 JWT
- **Token 存储**：前端通过 Supabase SDK 管理，支持 localStorage/HttpOnly Cookie
- **并发登录**：允许同一用户多设备登录（Supabase 原生支持）
- **会话失效**：Access Token 过期后通过 Supabase SDK 自动使用 Refresh Token 续期

**禁止实现**：
- ❌ 手写 Token 黑名单（Redis/PostgreSQL）
- ❌ 手写 jti 验证
- ❌ 手写设备指纹绑定
- ❌ 手写双 Secret fallback

---

## 3. Supabase Auth + 应用层角色校验模型

### 3.1 JWT Claims 结构（Supabase 标准）

```json
{
  "header": {
    "alg": "HS256",
    "typ": "JWT"
  },
  "payload": {
    // ========== Supabase 标准 Claims ==========
    "aud": "authenticated",
    "exp": 1700000000,
    "iat": 1699996400,
    "iss": "https://your-project.supabase.co/auth/v1",
    "sub": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",  // 用户 UUID，对应 users.id
    "email": "user@example.com",
    "role": "authenticated",  // Supabase 内置角色，固定值

    // ========== 应用自定义 Claims（可选）==========
    "app_metadata": {
      "user_role": "media_buyer"  // 业务角色，与 users.role 同步
    },

    "user_metadata": {
      "display_name": "张三",
      "avatar_url": "https://..."
    }
  }
}
```

### 3.2 必选字段说明

| 字段路径 | 类型 | 说明 | 使用场景 |
|---------|------|------|---------|
| `sub` | UUID | Supabase Auth 用户 ID | 主身份标识，对应 `users.id`（参考 DATA_SCHEMA.md） |
| `email` | String | 用户邮箱 | 审计日志、通知 |
| `exp` | Unix Timestamp | Token 过期时间 | Supabase 自动验证 |
| `app_metadata.user_role` | String | 业务角色（可选） | 仅作为缓存，实际角色从 `users` 表查询 |

**重要原则**：
- **角色来源**：应用层必须从 `users` 表查询 `role` 字段，不得仅依赖 JWT 中的 `app_metadata.user_role`
- **JWT 角色同步**：`app_metadata.user_role` 应与 `users.role` 保持一致，但仅作为性能优化，不作为权限判断依据

### 3.3 角色模型引用

**角色定义以 `AI_AD_SYSTEM_MAIN_DOCUMENT.md` 第 3 章为准**。

合法角色仅为：`admin`, `finance`, `data_operator`, `account_manager`, `media_buyer`。

角色职责与权限矩阵详见 `AI_AD_SYSTEM_MAIN_DOCUMENT.md` 第 3 章，本文档不再重复定义。

### 3.4 JWT 验证实现规范

**强制要求**：所有 JWT 验证必须通过 Supabase Auth SDK，禁止手写验证逻辑。

```python
# backend/services/supabase_auth_service.py

async def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
    """
    通过 Supabase Auth 验证 JWT Token
    
    实现方式：
    1. 调用 supabase.auth.get_user(token) 验证 Token
    2. 从返回的 user 对象获取 user_id
    3. 查询 users 表获取完整用户信息（含 role）
    4. 返回用户对象
    
    禁止：
    - 手写 jwt.decode() 签名验证
    - 手写 Token 黑名单检查
    - 手写 jti 验证
    """
    try:
        # 通过 Supabase Auth 验证 Token
        response = self.client.auth.get_user(token)
        
        if not response.user:
            return None
        
        # 从 users 表查询完整用户信息（含 role）
        profile = await self._get_user_profile(response.user.id)
        
        return {
            "user": response.user,
            "profile": profile  # 包含 role 字段
        }
    except Exception:
        return None
```

---

## 4. Token 生命周期

### 4.1 Token 类型与有效期（Supabase 配置）

| Token 类型 | 有效期 | 用途 | 管理方式 |
|-----------|-------|------|---------|
| **Access Token** | 1 小时（默认，可配置） | API 调用鉴权 | Supabase Auth 自动管理 |
| **Refresh Token** | 30 天（默认，可配置） | 续期 Access Token | Supabase Auth 自动管理 |
| **Reset Token** | 15 分钟 | 密码重置 | Supabase Auth 自动管理 |
| **Invite Token** | 7 天 | 用户邀请 | Supabase Auth 自动管理 |

**配置位置**：Supabase Dashboard → Settings → Auth → JWT expiry

### 4.2 Token 续期流程（Supabase SDK）

**前端实现**（通过 Supabase SDK）：

```typescript
// frontend/lib/supabase/client.ts

// Supabase SDK 自动处理 Token 续期
// 无需手写 refresh 逻辑
const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
);

// 自动续期：SDK 在 Access Token 过期前自动使用 Refresh Token 续期
```

**后端实现**（通过 Supabase Auth Service）：

```python
# backend/services/supabase_auth_service.py

async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
    """
    通过 Supabase Auth 刷新 Token
    
    实现方式：
    1. 调用 supabase.auth.refresh_session(refresh_token)
    2. 返回新的 Access Token + Refresh Token
    
    禁止：
    - 手写 refresh 逻辑
    - 手写 Token 生成
    """
    try:
        response = self.client.auth.refresh_session(refresh_token)
        
        if not response.session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "AUTH_005", "message": "令牌刷新失败"}
            )
        
        return {
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token,
            "expires_at": response.session.expires_at,
            "expires_in": response.session.expires_in
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "AUTH_005", "message": "令牌已过期或无效"}
        )
```

### 4.3 Token 撤销策略

#### 4.3.1 主动撤销（用户登出）

```python
# backend/services/supabase_auth_service.py

async def logout_user(self, access_token: str, user_id: str) -> None:
    """
    用户登出
    
    实现方式：
    1. 调用 supabase.auth.sign_out(access_token)
    2. Supabase 自动撤销 Refresh Token
    3. 记录审计日志
    
    禁止：
    - 手写 Token 黑名单
    - 手写 jti 验证
    """
    try:
        # 通过 Supabase Auth 登出
        self.client.auth.sign_out(access_token)
        
        # 记录审计日志
        await audit_log_service.log(
            user_id=user_id,
            action="USER_LOGOUT",
            resource_type="auth"
        )
    except Exception:
        pass  # 即使登出失败也不抛出错误
```

#### 4.3.2 强制撤销（管理员操作）

```python
# backend/services/supabase_auth_service.py

async def revoke_user_sessions(self, user_id: str) -> None:
    """
    管理员强制撤销用户所有会话
    
    实现方式：
    1. 调用 supabase.auth.admin.sign_out(user_id)
    2. Supabase 自动撤销该用户的所有 Refresh Token
    
    禁止：
    - 手写 Token 黑名单
    - 手写设备指纹验证
    """
    try:
        # 通过 Supabase Admin API 撤销所有会话
        self.admin_client.auth.admin.sign_out(user_id)
        
        # 记录审计日志
        await audit_log_service.log(
            user_id=user_id,
            action="ADMIN_REVOKE_SESSIONS",
            resource_type="auth"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "SYS_001", "message": "撤销会话失败"}
        )
```

**禁止实现**：
- ❌ Token 黑名单（Redis/PostgreSQL）
- ❌ jti 验证
- ❌ 设备指纹绑定
- ❌ 手写会话管理表

---

## 5. 应用层权限校验流程

### 5.1 两层防御模型（当前实现）

```
┌──────────────────────────────────────────────────────────────┐
│                       第一层：API 路由层                       │
│  @router.get("/projects", dependencies=[Depends(require_auth)])│
│  - 验证 Token 有效性（通过 Supabase Auth）                    │
│  - 提取用户身份（get_current_user）                           │
│  - 角色权限校验（require_role）                              │
└────────────────────────┬─────────────────────────────────────┘
                         │ User 对象（含 role）
                         ▼
┌──────────────────────────────────────────────────────────────┐
│                      第二层：Service 层                        │
│  def get_projects(user: User, filters: dict):                │
│    # 基于角色的业务逻辑过滤                                    │
│    if user.role == UserRole.MEDIA_BUYER:                     │
│        return projects where assigned_to = user.id           │
│  - 数据范围过滤（基于 project_members 表）                     │
│  - 状态机权限校验（参考 STATE_MACHINE.md）                    │
└──────────────────────────────────────────────────────────────┘
```

**重要说明**：
- **当前未启用 RLS**：所有权限通过应用层（API + Service）实现
- **RLS 作为未来扩展**：参考 `RLS_POLICIES.md`，当前禁止启用

### 5.2 API 路由层权限装饰器

```python
# backend/deps/supabase_auth.py

from fastapi import Depends, HTTPException, status
from backend.models.enums import UserRole  # 引用 enums.py

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    基础认证：验证 Token 并返回用户对象
    
    实现方式：
    1. 通过 Supabase Auth 验证 Token
    2. 从 users 表查询完整用户信息（含 role）
    3. 返回用户对象
    """
    # 实现见 3.4 章节
    pass


def require_role(allowed_roles: list[UserRole]):
    """
    角色权限校验装饰器
    
    使用示例：
    @router.post("/projects")
    async def create_project(
        current_user: Dict = Depends(require_role([
            UserRole.ADMIN,
            UserRole.ACCOUNT_MANAGER
        ]))
    ):
        ...
    """
    async def role_checker(
        current_user: Dict[str, Any] = Depends(get_current_user)
    ) -> Dict[str, Any]:
        user_role = current_user.get("profile", {}).get("role")
        
        if not user_role or user_role not in [r.value for r in allowed_roles]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "AUTH_500",
                    "message": f"需要以下角色之一: {', '.join([r.value for r in allowed_roles])}"
                }
            )
        
        return current_user
    
    return role_checker


# 便捷别名
require_admin = Depends(require_role([UserRole.ADMIN]))
require_finance = Depends(require_role([UserRole.ADMIN, UserRole.FINANCE]))
```

### 5.3 Service 层权限过滤

```python
# backend/services/project_service.py

class ProjectService:
    async def get_projects(
        self,
        user: Dict[str, Any],
        filters: ProjectFilters
    ) -> List[Project]:
        """
        根据用户角色返回可访问的项目列表
        
        权限规则（参考 AI_AD_SYSTEM_MAIN_DOCUMENT.md 第 3 章）：
        - admin/data_operator/finance: 查看所有项目
        - account_manager: 查看自己管理的项目（通过 project_members 表）
        - media_buyer: 查看分配给自己的项目（通过 ad_accounts.assigned_to）
        """
        user_role = user.get("profile", {}).get("role")
        user_id = user.get("user", {}).id
        
        query = self.db.query(Project)
        
        # 基于角色的数据过滤
        if user_role == "media_buyer":
            # 投手只能看到自己的账户所属的项目
            query = query.join(AdAccount).filter(
                AdAccount.assigned_to == user_id
            ).distinct()
        
        elif user_role == "account_manager":
            # 客户经理只能看到自己管理的项目（通过 project_members 表）
            query = query.join(ProjectMember).filter(
                ProjectMember.user_id == user_id,
                ProjectMember.role.in_(['account_manager', 'project_owner'])
            )
        
        elif user_role in ["admin", "data_operator", "finance"]:
            # 全局视野，无需过滤
            pass
        
        # 应用其他过滤条件
        if filters.status:
            query = query.filter(Project.status == filters.status)
        
        return query.all()
```

**关键原则**：
- **项目关联判断**：必须使用 `project_members` 表（参考 DATA_SCHEMA.md 3.2.2）
- **角色定义**：必须使用 `AI_AD_SYSTEM_MAIN_DOCUMENT.md` 中定义的 5 个合法角色
- **状态流转**：必须遵循 `STATE_MACHINE.md` 中定义的状态机规则

### 5.4 RLS 策略层（未来扩展）

**当前状态**：RLS 未启用，所有权限通过应用层实现。

**未来扩展**：如启用 RLS，参考 `RLS_POLICIES.md` 中的策略定义。

**禁止操作**：
- ❌ 当前禁止执行 `ALTER TABLE ... ENABLE ROW LEVEL SECURITY`
- ❌ 当前禁止创建 RLS 策略
- ❌ 当前禁止在代码中假设 RLS 已启用

---

## 6. 开发规范

### 6.1 后端开发规范

#### 6.1.1 使用 Supabase Auth Service

**强制要求**：所有认证相关操作必须通过 `supabase_auth_service`，禁止直接调用 Supabase Client。

```python
# ✅ 正确：通过 Service 层
from backend.services.supabase_auth_service import supabase_auth_service

user_data = await supabase_auth_service.verify_token(token)

# ❌ 错误：直接调用 Supabase Client
from backend.core.supabase_client import supabase_client
user = supabase_client.auth.get_user(token)  # 禁止
```

#### 6.1.2 角色验证规范

**强制要求**：角色必须从 `users` 表查询，不得仅依赖 JWT Claims。

```python
# ✅ 正确：从 users 表查询角色
user_data = await supabase_auth_service.verify_token(token)
user_role = user_data.get("profile", {}).get("role")  # 来自 users 表

# ❌ 错误：仅依赖 JWT Claims
payload = jwt.decode(token, secret)
user_role = payload.get("app_metadata", {}).get("user_role")  # 禁止
```

#### 6.1.3 权限装饰器使用

```python
# backend/routers/projects.py

from backend.deps.supabase_auth import get_current_user, require_role
from backend.models.enums import UserRole

@router.get("/projects")
async def list_projects(
    current_user: Dict = Depends(get_current_user),
    filters: ProjectFilters = Query(...)
):
    """所有认证用户可以访问，但返回数据根据角色过滤"""
    return await project_service.get_projects(current_user, filters)


@router.post("/projects")
async def create_project(
    project_data: ProjectCreate,
    current_user: Dict = Depends(require_role([
        UserRole.ADMIN,
        UserRole.ACCOUNT_MANAGER
    ]))
):
    """只有管理员、客户经理可以创建项目"""
    return await project_service.create_project(project_data, current_user)
```

### 6.2 前端开发规范

#### 6.2.1 使用 Supabase SDK

**强制要求**：所有认证操作必须通过 Supabase SDK，禁止手写 Token 管理。

```typescript
// ✅ 正确：通过 Supabase SDK
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
)

// 登录
const { data, error } = await supabase.auth.signInWithPassword({
  email,
  password
})

// ❌ 错误：手写 Token 管理
localStorage.setItem('token', token)  // 禁止
```

#### 6.2.2 API 请求规范

**强制要求**：所有后端 API 调用必须通过 `lib/api.ts::apiFetch`，禁止直接调用 `fetch()`。

```typescript
// ✅ 正确：通过 apiFetch
import { apiFetch } from '@/lib/api'

const response = await apiFetch('/api/v1/projects', {
  method: 'GET',
  headers: {
    'Authorization': `Bearer ${accessToken}`
  }
})

// ❌ 错误：直接调用 fetch
const response = await fetch('/api/v1/projects', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
})  // 禁止
```

---

## 7. 错误码引用方式

### 7.1 错误码来源

**所有认证错误码必须引用 `ERROR_CODES.md` 第 4.1 章，禁止在本文档中重复定义。**

### 7.2 常用认证错误码（引用 ERROR_CODES.md）

| 错误码 | HTTP | 消息 | 说明 | 来源 |
|-------|------|------|------|------|
| `AUTH_001` | 401 | 用户名或密码错误 | 登录验证失败 | ERROR_CODES.md 4.1.1 |
| `AUTH_002` | 403 | 账户已被禁用 | `is_active = false` | ERROR_CODES.md 4.1.1 |
| `AUTH_003` | 401 | 令牌已被撤销 | Token 已撤销 | ERROR_CODES.md 4.1.1 |
| `AUTH_400` | 401 | 未提供认证令牌 | 缺少 Authorization 头 | ERROR_CODES.md 4.1.5 |
| `AUTH_401` | 401 | 无效的认证令牌 | Token 格式错误/签名失败 | ERROR_CODES.md 4.1.5 |
| `AUTH_402` | 401 | 令牌已过期 | Token 超过有效期 | ERROR_CODES.md 4.1.5 |
| `AUTH_500` | 403 | 权限不足 | 用户角色不满足权限要求 | ERROR_CODES.md 4.1.6 |

**完整错误码列表**：参考 `ERROR_CODES.md` 第 4.1 章"认证授权类（AUTH_）"。

### 7.3 错误响应格式

所有错误响应遵循全局 Envelope 格式（定义于 `backend/core/response.py`）：

```json
{
  "success": false,
  "message": "错误描述信息",
  "code": "AUTH_401",
  "data": null,
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2025-01-20T10:30:00Z"
}
```

---

## 8. 安全基线

### 8.1 最小权限原则

**规则**（参考 `BUSINESS_RULES.md` BR-AUTH-004）：
1. **默认无权限**：新用户默认为 `media_buyer`（最低权限角色）
2. **显式授权**：任何权限提升必须经过管理员审批
3. **角色验证**：应用层必须从 `users` 表查询角色，不得仅依赖 JWT Claims

### 8.2 防止角色伪造

**防御措施**：

1. **JWT 签名验证**（Supabase 自动处理）
   - 所有 Token 由 Supabase 签发，使用 Supabase JWT Secret 验证
   - 禁止手写 JWT 验证逻辑

2. **双重验证**：JWT Claims + 数据库查询
   ```python
   # 第一步：通过 Supabase Auth 验证 Token
   user_data = await supabase_auth_service.verify_token(token)
   
   # 第二步：从 users 表查询真实角色（强制）
   user_role = user_data.get("profile", {}).get("role")  # 来自 users 表
   
   # 禁止：仅依赖 JWT 中的 app_metadata.user_role
   ```

3. **前端参数过滤**：忽略客户端提交的 `role` 字段
   ```python
   @router.patch("/users/{user_id}")
   async def update_user(
       user_id: UUID,
       updates: UserUpdate,
       current_user: Dict = Depends(get_current_user)
   ):
       # 防止通过 API 修改自己的角色
       if "role" in updates.dict(exclude_unset=True):
           if current_user.get("user", {}).id == user_id:
               raise HTTPException(
                   status_code=status.HTTP_403_FORBIDDEN,
                   detail={"code": "AUTH_500", "message": "不能修改自己的角色"}
               )
   ```

### 8.3 防止重放攻击

**防御措施**：

1. **短期 Access Token**（1 小时）
   - 减少被窃取 Token 的可用时间窗口
   - 配置位置：Supabase Dashboard → Settings → Auth → JWT expiry

2. **Supabase 原生保护**
   - Supabase Auth 自动处理 Token 过期
   - Supabase Auth 自动处理 Refresh Token 轮换

**禁止实现**：
- ❌ JWT ID（jti）黑名单（当前未启用）
- ❌ 设备指纹绑定（当前未启用）
- ❌ 手写重放攻击检测（当前未启用）

### 8.4 审计与监控

**必须记录的认证事件**（参考 `BUSINESS_RULES.md` BR-AUTH-003）：

| 事件类型 | 记录内容 | 告警阈值 |
|---------|---------|---------|
| 登录成功 | user_id, IP, device, timestamp | - |
| 登录失败 | email, IP, reason, timestamp | 5次/15分钟 |
| Token 刷新 | user_id, IP, timestamp | - |
| 密码重置 | user_id, IP, timestamp | - |
| 角色变更 | user_id, old_role, new_role, operator_id | 立即告警 |
| 权限拒绝 | user_id, resource, action, IP | 10次/小时 |

**实现方式**：通过 `audit_logs` 表记录（参考 DATA_SCHEMA.md 3.1.4）。

### 8.5 HTTPS 强制与安全 Header

**生产环境强制要求**：

1. **HTTPS Only**
   ```python
   # backend/main.py
   from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
   
   if settings.ENVIRONMENT == "production":
       app.add_middleware(HTTPSRedirectMiddleware)
   ```

2. **安全响应头**
   ```python
   @app.middleware("http")
   async def add_security_headers(request, call_next):
       response = await call_next(request)
       response.headers["X-Content-Type-Options"] = "nosniff"
       response.headers["X-Frame-Options"] = "DENY"
       response.headers["X-XSS-Protection"] = "1; mode=block"
       response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
       return response
   ```

---

## 9. 未来扩展

### 9.1 RLS 策略（未来扩展）

**当前状态**：RLS 未启用，所有权限通过应用层实现。

**未来扩展**：如启用 RLS，必须：

1. **更新 SoT 文档**：
   - 更新 `AI_AD_SYSTEM_MAIN_DOCUMENT.md` 第 2.1 章（架构说明）
   - 更新 `DATA_SCHEMA.md` 第 1.1 章（权限说明）
   - 参考 `RLS_POLICIES.md` 中的策略定义

2. **实施步骤**：
   - 评估性能影响
   - 逐表启用 RLS
   - 同步更新应用层逻辑

**禁止操作**：
- ❌ 当前禁止执行 `ALTER TABLE ... ENABLE ROW LEVEL SECURITY`
- ❌ 当前禁止创建 RLS 策略
- ❌ 当前禁止在代码中假设 RLS 已启用

### 9.2 Token 黑名单（未来扩展）

**当前状态**：未启用 Token 黑名单，依赖 Supabase Auth 的 Token 管理。

**未来扩展**：如需要 Token 黑名单，必须：

1. **评估需求**：明确业务场景（如强制登出、安全事件响应）
2. **技术选型**：Redis 或 PostgreSQL 表
3. **更新文档**：同步更新本文档和 `AI_AD_SYSTEM_MAIN_DOCUMENT.md`

**禁止操作**：
- ❌ 当前禁止实现 Token 黑名单
- ❌ 当前禁止手写 jti 验证

### 9.3 设备指纹绑定（未来扩展）

**当前状态**：未启用设备指纹绑定。

**未来扩展**：如需要设备指纹绑定，必须：

1. **评估需求**：明确安全场景
2. **技术选型**：浏览器指纹或设备 ID
3. **更新文档**：同步更新本文档

**禁止操作**：
- ❌ 当前禁止实现设备指纹绑定
- ❌ 当前禁止在 JWT Claims 中存储 device_id

---

## 10. 版本历史

| 版本 | 日期 | 变更内容 | 作者 |
|------|------|---------|------|
| **v2.0** | **2025-01-20** | **重大修复版本**：<br>- 修复 RLS 当前未启用的错误描述<br>- 删除所有自建 JWT/Session/Blacklist 逻辑<br>- 删除角色模型重复定义（引用 AI_AD_SYSTEM_MAIN_DOCUMENT.md）<br>- 删除错误码重复定义（引用 ERROR_CODES.md）<br>- 精简为规范层，删除教程代码<br>- 与所有 SoT 文档完全对齐 | 系统架构团队 |
| v1.0 | 2025-11-20 | 初始版本 | 认证架构团队 |

---

**文档维护责任**：
- **主要维护者**：系统架构团队
- **评审周期**：每季度评审一次
- **变更审批**：技术负责人 + 安全负责人

**联系方式**：
- 技术问题：请在项目 Issue 中讨论
- 安全问题：请发送邮件至安全团队

---

**END OF DOCUMENT**
