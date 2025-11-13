# Supabase Auth 混合方案指南

## 概述

本方案将Supabase Auth的强大安全特性与自定义的业务逻辑管理相结合，实现一个既安全又灵活的认证系统。

## 架构设计

### 1. 认证层（Supabase Auth）
- ✅ 用户注册、登录、密码管理
- ✅ JWT令牌生成和验证
- ✅ 邮箱验证、密码重置
- ✅ OAuth2集成（可选）
- ✅ 多因素认证（可选）

### 2. 业务层（自定义）
- 用户资料和角色管理
- 业务特定的权限控制
- 登录历史和审计日志
- 项目和资源关联

## 实现方案

### 步骤1：数据库设计

```sql
-- 1. 启用Supabase Auth扩展
-- 已默认启用，只需配置

-- 2. 创建用户资料表
CREATE TABLE user_profiles (
    id UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
    username TEXT UNIQUE,
    full_name TEXT,
    role TEXT NOT NULL DEFAULT 'media_buyer'
        CHECK (role IN ('admin', 'finance', 'data_operator', 'account_manager', 'media_buyer')),
    account_manager_id UUID REFERENCES user_profiles(id),
    department TEXT,
    is_active BOOLEAN DEFAULT true,
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. 创建登录历史表
CREATE TABLE user_login_history (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    login_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    logout_time TIMESTAMP WITH TIME ZONE,
    ip_address INET,
    user_agent TEXT,
    login_type TEXT DEFAULT 'password',
    status TEXT DEFAULT 'success'
);

-- 4. 创建用户会话表（扩展Supabase的会话管理）
CREATE TABLE user_sessions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    session_token TEXT UNIQUE,
    device_info JSONB,
    is_active BOOLEAN DEFAULT true,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 索引
CREATE INDEX idx_user_profiles_role ON user_profiles(role);
CREATE INDEX idx_user_profiles_manager ON user_profiles(account_manager_id);
CREATE INDEX idx_login_history_user ON user_login_history(user_id);
CREATE INDEX idx_login_history_time ON user_login_history(login_time);
CREATE INDEX idx_user_sessions_user ON user_sessions(user_id);
CREATE INDEX idx_user_sessions_token ON user_sessions(session_token);
```

### 步骤2：RLS策略

```sql
-- 启用RLS
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_login_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_sessions ENABLE ROW LEVEL SECURITY;

-- 用户资料策略
CREATE POLICY "Users can view own profile" ON user_profiles
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON user_profiles
    FOR UPDATE USING (auth.uid() = id);

CREATE POLICY "Admins can view all profiles" ON user_profiles
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM user_profiles
            WHERE id = auth.uid() AND role = 'admin'
        )
    );

CREATE POLICY "Account managers can view their team" ON user_profiles
    FOR SELECT USING (
        account_manager_id = auth.uid()
        OR auth.uid() = id
    );

-- 登录历史策略
CREATE POLICY "Users can view own login history" ON user_login_history
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Admins can view all login history" ON user_login_history
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM user_profiles
            WHERE id = auth.uid() AND role = 'admin'
        )
    );

-- 会话策略
CREATE POLICY "Users can manage own sessions" ON user_sessions
    FOR ALL USING (auth.uid() = user_id);

-- 触发器：自动创建用户资料
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    INSERT INTO public.user_profiles (id, username, full_name, role)
    VALUES (
        new.id,
        new.raw_user_meta_data->>'username',
        COALESCE(
            new.raw_user_meta_data->>'full_name',
            new.email
        ),
        COALESCE(
            new.raw_user_meta_data->>'role',
            'media_buyer'
        )
    );

    -- 记录注册日志
    INSERT INTO public.user_login_history (user_id, login_type, status)
    VALUES (new.id, 'registration', 'success');

    RETURN new;
END;
$$;

-- 触发器：更新时间戳
CREATE OR REPLACE FUNCTION public.handle_profile_update()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    new.updated_at = NOW();
    RETURN new;
END;
$$;

-- 应用触发器
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

CREATE TRIGGER on_profile_updated
    BEFORE UPDATE ON user_profiles
    FOR EACH ROW EXECUTE FUNCTION public.handle_profile_update();
```

### 步骤3：后端集成

```python
# core/supabase_client.py
import os
from supabase import create_client, Client
from typing import Optional, Dict, Any

class SupabaseClient:
    def __init__(self):
        self.supabase: Client = create_client(
            supabase_url=os.getenv("SUPABASE_URL"),
            supabase_key=os.getenv("SUPABASE_ANON_KEY")
        )
        self.service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    def get_admin_client(self) -> Client:
        """获取管理员权限的客户端"""
        return create_client(
            supabase_url=os.getenv("SUPABASE_URL"),
            supabase_key=self.service_key
        )

# 单例
supabase_client = SupabaseClient()

# services/supabase_auth_service.py
from datetime import datetime, timezone
from typing import Optional, Tuple, Dict, Any
from fastapi import HTTPException
from supabase import Client

from core.supabase_client import supabase_client
from models.user_profile import UserProfile

class SupabaseAuthService:
    """Supabase认证服务"""

    def __init__(self):
        self.client = supabase_client.supabase
        self.admin_client = supabase_client.get_admin_client()

    async def register_user(
        self,
        email: str,
        password: str,
        username: Optional[str] = None,
        full_name: Optional[str] = None,
        role: str = "media_buyer",
        account_manager_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """用户注册"""
        try:
            # 构建用户元数据
            user_metadata = {
                "username": username,
                "full_name": full_name,
                "role": role,
                "account_manager_id": account_manager_id
            }
            if metadata:
                user_metadata.update(metadata)

            # 通过Supabase注册
            response = self.client.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": user_metadata
                }
            })

            if response.user is None:
                raise HTTPException(400, detail="注册失败")

            return {
                "user_id": response.user.id,
                "email": response.user.email,
                "role": role,
                "message": "注册成功，请查收验证邮件"
            }

        except Exception as e:
            raise HTTPException(400, detail=str(e))

    async def login_user(
        self,
        email: str,
        password: str,
        remember_me: bool = False
    ) -> Dict[str, Any]:
        """用户登录"""
        try:
            # 通过Supabase登录
            response = self.client.auth.sign_in_with_password({
                "email": email,
                "password": password
            })

            if not response.user or not response.session:
                raise HTTPException(401, detail="登录失败")

            # 获取用户资料
            profile = self._get_user_profile(response.user.id)

            # 记录登录历史
            self._record_login(response.user.id, "password", "success")

            return {
                "user": {
                    "id": response.user.id,
                    "email": response.user.email,
                    "profile": profile
                },
                "session": {
                    "access_token": response.session.access_token,
                    "refresh_token": response.session.refresh_token,
                    "expires_at": response.session.expires_at,
                    "expires_in": response.session.expires_in
                }
            }

        except Exception as e:
            # 记录失败登录
            self._record_login_by_email(email, "password", "failed")
            raise HTTPException(401, detail="邮箱或密码错误")

    async def logout_user(self, token: str) -> None:
        """用户登出"""
        try:
            # 通过Supabase登出
            self.client.auth.sign_out(token)

            # 更新登录历史
            # （可以通过JWT token获取用户ID）

        except Exception as e:
            raise HTTPException(400, detail=str(e))

    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """刷新令牌"""
        try:
            response = self.client.auth.refresh_session(refresh_token)

            if not response.session:
                raise HTTPException(401, detail="刷新失败")

            return {
                "access_token": response.session.access_token,
                "refresh_token": response.session.refresh_token,
                "expires_at": response.session.expires_at
            }

        except Exception as e:
            raise HTTPException(401, detail=str(e))

    async def reset_password(self, email: str) -> None:
        """重置密码"""
        try:
            response = self.client.auth.reset_password_for_email(email)

            if response is None:
                raise HTTPException(400, detail="重置失败")

        except Exception as e:
            raise HTTPException(400, detail=str(e))

    async def verify_token(self, token: str) -> Dict[str, Any]:
        """验证JWT令牌"""
        try:
            response = self.client.auth.get_user(token)

            if not response.user:
                raise HTTPException(401, detail="无效令牌")

            # 获取用户资料
            profile = self._get_user_profile(response.user.id)

            return {
                "user": response.user,
                "profile": profile
            }

        except Exception as e:
            raise HTTPException(401, detail="无效令牌")

    def _get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取用户资料"""
        try:
            response = self.admin_client.table("user_profiles")\
                .select("*")\
                .eq("id", user_id)\
                .single()\
                .execute()

            return response.data if response.data else None

        except Exception:
            return None

    def _record_login(self, user_id: str, login_type: str, status: str) -> None:
        """记录登录历史"""
        try:
            self.admin_client.table("user_login_history")\
                .insert({
                    "user_id": user_id,
                    "login_type": login_type,
                    "status": status,
                    "login_time": datetime.now(timezone.utc).isoformat()
                })\
                .execute()
        except Exception:
            pass  # 忽略记录错误

    def _record_login_by_email(self, email: str, login_type: str, status: str) -> None:
        """通过邮箱记录登录尝试"""
        try:
            # 先通过邮箱查找用户
            response = self.admin_client.auth.admin.list_users()
            user = next((u for u in response.users if u.email == email), None)

            if user:
                self._record_login(user.id, login_type, status)
        except Exception:
            pass
```

### 步骤4：认证中间件

```python
# deps/supabase_auth.py
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

from services.supabase_auth_service import SupabaseAuthService
from core.supabase_client import supabase_client

security = HTTPBearer()
auth_service = SupabaseAuthService()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """获取当前用户"""
    try:
        # 验证令牌
        token_data = await auth_service.verify_token(credentials.credentials)

        # 检查用户是否激活
        if not token_data["profile"].get("is_active", True):
            raise HTTPException(403, detail="账户已被禁用")

        return token_data

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(401, detail="认证失败")

async def get_current_active_user(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """获取当前活跃用户"""
    return current_user

def require_role(required_roles: list[str]):
    """角色权限装饰器"""
    def role_checker(
        current_user: Dict[str, Any] = Depends(get_current_active_user)
    ) -> Dict[str, Any]:
        user_role = current_user["profile"].get("role")

        if user_role not in required_roles:
            raise HTTPException(
                403,
                detail=f"需要以下角色之一: {', '.join(required_roles)}"
            )

        return current_user

    return role_checker

# 角色依赖
require_admin = require_role(["admin"])
require_finance = require_role(["admin", "finance"])
require_data_operator = require_role(["admin", "finance", "data_operator"])
```

### 步骤5：更新路由

```python
# routers/supabase_auth.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from services.supabase_auth_service import SupabaseAuthService
from deps.supabase_auth import get_current_active_user

router = APIRouter(prefix="/auth", tags=["认证"])
auth_service = SupabaseAuthService()

class RegisterRequest(BaseModel):
    email: str
    password: str
    username: Optional[str] = None
    full_name: Optional[str] = None
    role: str = "media_buyer"
    account_manager_id: Optional[str] = None

class LoginRequest(BaseModel):
    email: str
    password: str
    remember_me: bool = False

@router.post("/register")
async def register(request: RegisterRequest):
    """用户注册"""
    result = await auth_service.register_user(
        email=request.email,
        password=request.password,
        username=request.username,
        full_name=request.full_name,
        role=request.role,
        account_manager_id=request.account_manager_id
    )

    return {
        "success": True,
        "data": result,
        "message": "注册成功"
    }

@router.post("/login")
async def login(request: LoginRequest):
    """用户登录"""
    result = await auth_service.login_user(
        email=request.email,
        password=request.password,
        remember_me=request.remember_me
    )

    return {
        "success": True,
        "data": result,
        "message": "登录成功"
    }

@router.post("/logout")
async def logout(
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """用户登出"""
    # 从请求头获取token
    # 实际实现需要从依赖注入中获取
    await auth_service.logout_user(current_user["session"]["access_token"])

    return {
        "success": True,
        "message": "登出成功"
    }

@router.get("/me")
async def get_current_user_info(
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """获取当前用户信息"""
    return {
        "success": True,
        "data": current_user,
        "message": "获取成功"
    }
```

## 迁移步骤

### 1. 备份现有数据
```sql
-- 备份现有用户表
CREATE TABLE users_backup AS SELECT * FROM users;
```

### 2. 迁移用户数据
```python
# scripts/migrate_users.py
import asyncio
from supabase import create_client
from core.config import get_settings

async def migrate_users():
    settings = get_settings()
    admin_client = create_client(
        settings.supabase_url,
        settings.supabase_service_role_key
    )

    # 1. 从旧表读取用户
    old_users = db.query(User).all()

    for user in old_users:
        # 2. 在Supabase Auth中创建用户
        admin_client.auth.admin.create_user({
            "email": user.email,
            "password": "temp_password_123",  # 需要用户重置
            "email_confirm": True,
            "user_metadata": {
                "username": user.username,
                "role": user.role,
                "full_name": user.full_name
            }
        })

    print("迁移完成")

asyncio.run(migrate_users())
```

### 3. 更新前端代码
```javascript
// 前端使用Supabase客户端
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY
)

// 登录
const { data, error } = await supabase.auth.signInWithPassword({
  email: 'user@example.com',
  password: 'password'
})

// API调用时携带token
const { data } = await supabase
  .from('projects')
  .select('*')
  .eq('user_id', user.id)
```

## 优势总结

1. **安全性**：利用Supabase的成熟认证机制
2. **灵活性**：保留自定义业务逻辑
3. **可扩展性**：支持OAuth2、MFA等高级功能
4. **简化维护**：减少自研代码，降低维护成本
5. **一致性**：统一的JWT令牌管理

## 注意事项

1. 确保Supabase配置正确
2. 设置适当的RLS策略
3. 处理好用户ID的映射关系（UUID）
4. 确保所有API调用都验证JWT令牌
5. 定期备份Supabase数据