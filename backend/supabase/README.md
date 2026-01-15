# Supabase 集成指南

> **版本**: 1.0
> **更新日期**: 2025-11-16
> **适用范围**: AI 广告代投系统后端

---

## 📋 目录

1. [架构概览](#架构概览)
2. [认证流程](#认证流程)
3. [数据库迁移](#数据库迁移)
4. [后端集成](#后端集成)
5. [RLS 策略说明](#rls-策略说明)
6. [常见问题](#常见问题)

---

## 🏗️ 架构概览

### 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                         前端应用                             │
│                    (Next.js + TypeScript)                   │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  │ HTTP + JWT
                  │
┌─────────────────▼───────────────────────────────────────────┐
│                       FastAPI 后端                           │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Supabase Auth 中间件                                 │  │
│  │  - 验证 JWT Token                                     │  │
│  │  - 获取 user_id                                       │  │
│  │  - 加载 user_profile                                  │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  应用层权限控制                                        │  │
│  │  - 角色权限检查                                        │  │
│  │  - 业务逻辑权限                                        │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  │ SQL
                  │
┌─────────────────▼───────────────────────────────────────────┐
│                    Supabase PostgreSQL                       │
│  ┌──────────────────┐  ┌──────────────────────────────┐    │
│  │   auth.users     │  │   public.user_profiles       │    │
│  │  (Supabase 管理)  │  │   (业务数据)                  │    │
│  │  - id (UUID)     │  │   - id (UUID, PK)            │    │
│  │  - email         │◄─┤   - user_id (FK)             │    │
│  │  - password      │  │   - role                     │    │
│  │  - metadata      │  │   - department               │    │
│  └──────────────────┘  │   - phone                    │    │
│                        │   - RLS 策略                  │    │
│                        └──────────────────────────────┘    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  业务表 (projects, ad_accounts, etc.)                 │  │
│  │  - RLS 基础隔离                                        │  │
│  │  - 应用层复杂权限                                      │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 用户数据分离

**Supabase Auth (auth.users)**
- 用途：认证信息管理
- 字段：id, email, encrypted_password, email_confirmed_at
- 管理方式：Supabase 自动管理
- 访问方式：通过 Supabase Client SDK

**业务数据 (public.user_profiles)**
- 用途：业务信息存储
- 字段：role, department, phone, avatar_url
- 管理方式：应用层管理
- 访问方式：通过 SQLAlchemy ORM

---

## 🔐 认证流程

### 1. 用户注册流程

```python
# 前端调用
supabase.auth.signUp({
    email: "user@example.com",
    password: "password123",
    options: {
        data: {
            name: "张三",
            role: "media_buyer"
        }
    }
})

# 后端自动触发
# 1. Supabase 在 auth.users 创建用户
# 2. 触发器 on_auth_user_created 自动执行
# 3. 在 user_profiles 创建对应记录
```

**触发器代码** (`20251116000001_create_user_profiles.sql:106-118`):
```sql
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.user_profiles (id, user_id, email, name, role)
    VALUES (
        NEW.id,
        NEW.id,
        NEW.email,
        COALESCE(NEW.raw_user_meta_data->>'name', NEW.email),
        COALESCE(NEW.raw_user_meta_data->>'role', 'media_buyer')
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

### 2. 用户登录流程

```python
# 前端调用
const { data, error } = await supabase.auth.signInWithPassword({
    email: "user@example.com",
    password: "password123"
})

# 返回 JWT Token
const token = data.session.access_token

# 后续请求携带 Token
fetch("/api/projects", {
    headers: {
        "Authorization": `Bearer ${token}`
    }
})
```

### 3. 后端 Token 验证

```python
# backend/deps/supabase_auth.py

from supabase import create_client
from fastapi import Header, HTTPException

async def get_current_user(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
) -> UserProfile:
    """验证 Supabase JWT 并获取用户信息"""

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")

    token = authorization.replace("Bearer ", "")

    try:
        # 1. 验证 JWT Token
        user_data = supabase.auth.get_user(token)

        # 2. 从数据库加载 user_profile
        user_profile = db.query(UserProfile).filter(
            UserProfile.user_id == user_data.user.id
        ).first()

        if not user_profile:
            raise HTTPException(status_code=404, detail="User profile not found")

        if not user_profile.is_active:
            raise HTTPException(status_code=403, detail="User account is inactive")

        # 3. 更新最后登录时间
        user_profile.last_login_at = datetime.utcnow()
        db.commit()

        return user_profile

    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
```

---

## 📦 数据库迁移

### 迁移步骤

#### Step 1: 执行 Supabase 迁移

```bash
# 1. 安装 Supabase CLI
pnpm add -g supabase

# 2. 登录 Supabase
supabase login

# 3. 链接项目
supabase link --project-ref <your-project-ref>

# 4. 执行迁移
supabase db push

# 或者手动在 Supabase Dashboard 的 SQL Editor 中执行：
# - supabase/migrations/20251116000001_create_user_profiles.sql
# - supabase/migrations/20251116000002_migrate_existing_users.sql
```

#### Step 2: 验证迁移结果

```sql
-- 检查 user_profiles 表
SELECT COUNT(*) FROM public.user_profiles;

-- 检查 RLS 策略
SELECT schemaname, tablename, policyname
FROM pg_policies
WHERE tablename = 'user_profiles';

-- 检查触发器
SELECT trigger_name, event_manipulation, event_object_table
FROM information_schema.triggers
WHERE trigger_name = 'on_auth_user_created';
```

#### Step 3: 测试认证流程

```python
# 在 Python 中测试
from supabase import create_client

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

# 测试注册
response = supabase.auth.sign_up({
    "email": "test@example.com",
    "password": "test123456",
    "options": {
        "data": {
            "name": "测试用户",
            "role": "media_buyer"
        }
    }
})

print(response)

# 测试登录
response = supabase.auth.sign_in_with_password({
    "email": "test@example.com",
    "password": "test123456"
})

print(response.session.access_token)
```

### 回滚方案

```sql
-- 如果需要回滚迁移：

-- 1. 删除触发器
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
DROP FUNCTION IF EXISTS public.handle_new_user();

-- 2. 删除 RLS 策略
DROP POLICY IF EXISTS "Users can view own profile" ON public.user_profiles;
DROP POLICY IF EXISTS "Admins can view all profiles" ON public.user_profiles;
-- ... 其他策略

-- 3. 删除表
DROP TABLE IF EXISTS public.user_profiles CASCADE;

-- 4. 恢复原 users 表（如果做了备份）
ALTER TABLE public.users_backup RENAME TO users;
```

---

## 🔌 后端集成

### 环境变量配置

```bash
# .env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-role-key  # 仅用于服务端操作
```

### 更新后端代码

#### 1. 更新 User Model

```python
# backend/models/user_profile.py

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from core.db import Base
import uuid

class UserProfile(Base):
    """用户业务信息表"""
    __tablename__ = "user_profiles"

    # 主键
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # 关联 Supabase Auth
    user_id = Column(UUID(as_uuid=True), unique=True, nullable=False)

    # 基础信息
    email = Column(String(255), nullable=False)
    name = Column(String(100))

    # 角色权限
    role = Column(String(64), nullable=False, default="media_buyer")

    # 业务信息
    department = Column(String(100))
    phone = Column(String(20))
    avatar_url = Column(String(500))

    # 状态
    is_active = Column(Boolean, default=True, nullable=False)
    last_login_at = Column(DateTime)

    # 审计字段
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("user_profiles.id"))
    updated_by = Column(UUID(as_uuid=True), ForeignKey("user_profiles.id"))
```

#### 2. 创建 Supabase 客户端

```python
# backend/core/supabase_client.py

from supabase import create_client, Client
from core.config import settings

def get_supabase_client() -> Client:
    """获取 Supabase 客户端"""
    return create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_KEY
    )

supabase: Client = get_supabase_client()
```

#### 3. 更新依赖注入

```python
# backend/deps/supabase_auth.py

from typing import Optional
from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session
from core.db import get_db
from core.supabase_client import supabase
from models.user_profile import UserProfile

async def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> UserProfile:
    """获取当前登录用户"""

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="未提供认证 Token"
        )

    token = authorization.replace("Bearer ", "")

    try:
        # 验证 Supabase JWT
        user_data = supabase.auth.get_user(token)

        # 加载用户业务信息
        user_profile = db.query(UserProfile).filter(
            UserProfile.user_id == user_data.user.id
        ).first()

        if not user_profile:
            raise HTTPException(
                status_code=404,
                detail="用户信息不存在"
            )

        if not user_profile.is_active:
            raise HTTPException(
                status_code=403,
                detail="用户账户已被禁用"
            )

        return user_profile

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail=f"Token 验证失败: {str(e)}"
        )


def require_role(allowed_roles: list[str]):
    """角色权限装饰器"""
    def decorator(current_user: UserProfile = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail=f"需要以下角色之一: {', '.join(allowed_roles)}"
            )
        return current_user
    return decorator
```

#### 4. 更新路由

```python
# backend/routers/projects.py

from fastapi import APIRouter, Depends
from deps.supabase_auth import get_current_user, require_role
from models.user_profile import UserProfile

router = APIRouter(prefix="/projects", tags=["projects"])

@router.get("")
async def list_projects(
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取项目列表"""
    # current_user 已经是 UserProfile 对象
    # 包含 role, department 等业务字段
    pass

@router.post("")
async def create_project(
    request: ProjectCreateRequest,
    current_user: UserProfile = Depends(require_role(["admin", "account_manager"])),
    db: Session = Depends(get_db)
):
    """创建项目（需要管理员或客户经理权限）"""
    pass
```

---

## 🛡️ RLS 策略说明

### 混合权限模型

本项目采用 **RLS + 应用层** 混合权限控制：

#### RLS 负责（数据库层）
1. **基础数据隔离**：用户只能看到自己的 profile
2. **管理员全局访问**：admin 角色可以查看所有数据
3. **防止直接 SQL 注入**：即使绕过应用层，RLS 仍然有效

#### 应用层负责（Service 层）
1. **复杂业务权限**：项目成员、跨表关联、状态流转
2. **动态权限计算**：基于业务规则的权限判断
3. **审计日志记录**：记录所有权限检查和操作日志

### RLS 策略列表

```sql
-- 1. 用户查看自己的 profile
CREATE POLICY "Users can view own profile"
ON user_profiles FOR SELECT
USING (auth.uid() = user_id);

-- 2. 管理员查看所有 profiles
CREATE POLICY "Admins can view all profiles"
ON user_profiles FOR SELECT
USING (
    EXISTS (
        SELECT 1 FROM user_profiles
        WHERE user_id = auth.uid() AND role = 'admin'
    )
);

-- 3. 用户更新自己的 profile（不能改 role）
CREATE POLICY "Users can update own profile"
ON user_profiles FOR UPDATE
USING (auth.uid() = user_id)
WITH CHECK (
    auth.uid() = user_id
    AND role = (SELECT role FROM user_profiles WHERE user_id = auth.uid())
);

-- 4. 管理员更新所有 profiles
CREATE POLICY "Admins can update all profiles"
ON user_profiles FOR UPDATE
USING (
    EXISTS (
        SELECT 1 FROM user_profiles
        WHERE user_id = auth.uid() AND role = 'admin'
    )
);

-- 5. 管理员插入新 profiles
CREATE POLICY "Admins can insert profiles"
ON user_profiles FOR INSERT
WITH CHECK (
    EXISTS (
        SELECT 1 FROM user_profiles
        WHERE user_id = auth.uid() AND role = 'admin'
    )
);

-- 6. 管理员删除 profiles
CREATE POLICY "Admins can delete profiles"
ON user_profiles FOR DELETE
USING (
    EXISTS (
        SELECT 1 FROM user_profiles
        WHERE user_id = auth.uid() AND role = 'admin'
    )
);
```

### 测试 RLS 策略

```sql
-- 以普通用户身份测试
SET ROLE authenticated;
SET request.jwt.claim.sub = '<user_uuid>';

-- 应该只能看到自己的 profile
SELECT * FROM user_profiles;

-- 以管理员身份测试
SET request.jwt.claim.sub = '<admin_uuid>';

-- 应该能看到所有 profiles
SELECT * FROM user_profiles;
```

---

## ❓ 常见问题

### Q1: 如何处理现有用户迁移？

**A**: 需要先在 Supabase Auth 中创建用户，然后执行迁移脚本。

```python
# 批量导入现有用户到 Supabase Auth
import pandas as pd
from supabase import create_client

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# 读取现有用户
users_df = pd.read_sql("SELECT * FROM users", engine)

for _, user in users_df.iterrows():
    # 在 Supabase Auth 创建用户
    supabase.auth.admin.create_user({
        "email": user.email,
        "password": "temp_password_123",  # 临时密码，需要用户重置
        "email_confirm": True,
        "user_metadata": {
            "name": user.name,
            "role": user.role
        }
    })
```

### Q2: RLS 策略影响性能吗？

**A**: 有一定影响，但可以通过索引优化：

```sql
-- 为 RLS 查询创建索引
CREATE INDEX idx_user_profiles_user_id_role ON user_profiles(user_id, role);
```

建议：
- 简单查询使用 RLS
- 复杂查询在应用层处理

### Q3: 如何在本地开发环境测试？

**A**: 使用 Supabase Local Development：

```bash
# 启动本地 Supabase
supabase start

# 执行迁移
supabase db reset

# 更新 .env.local
SUPABASE_URL=http://localhost:54321
SUPABASE_KEY=<local-anon-key>
```

### Q4: JWT Token 过期如何处理?

**A**: Supabase 自动处理 Token 刷新：

```typescript
// 前端自动刷新 Token
supabase.auth.onAuthStateChange((event, session) => {
    if (event === 'TOKEN_REFRESHED') {
        // 更新本地存储的 Token
        localStorage.setItem('token', session.access_token)
    }
})
```

### Q5: 如何实现用户注销？

```python
# 前端
await supabase.auth.signOut()

# 后端不需要特殊处理，Token 验证会自动失败
```

---

## 📚 参考资料

- [Supabase Auth 文档](https://supabase.com/docs/guides/auth)
- [Supabase RLS 指南](https://supabase.com/docs/guides/auth/row-level-security)
- [FastAPI 依赖注入](https://fastapi.tiangolo.com/tutorial/dependencies/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/en/20/orm/)

---

**文档版本**: 1.0
**最后更新**: 2025-11-16
**维护责任人**: 后端团队
