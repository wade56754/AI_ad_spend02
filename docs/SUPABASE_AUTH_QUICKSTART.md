# Supabase Auth 混合方案快速入门指南

## 概述

本指南将帮助您快速配置和使用Supabase Auth混合方案，将强大的Supabase认证功能与自定义业务逻辑相结合。

## 前置条件

1. 已注册Supabase账号
2. 已创建Supabase项目
3. 已安装必要的Python依赖

```bash
pip install supabase fastapi python-dotenv
```

## 快速配置

### 1. 获取Supabase凭据

1. 登录 [Supabase Dashboard](https://app.supabase.com)
2. 选择您的项目
3. 进入 **Settings > API**
4. 复制以下信息：
   - Project URL
   - anon public key
   - service_role key（保密）

### 2. 配置环境变量

编辑 `.env` 文件：

```env
# Supabase配置
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key-here
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here

# 前端URL（用于重定向）
FRONTEND_URL=http://localhost:3000
```

### 3. 运行数据库迁移

```bash
# 执行迁移脚本
alembic upgrade head

# 该命令将：
# - 创建user_profiles表
# - 创建user_login_history表
# - 创建user_sessions表
# - 设置RLS策略
# - 创建触发器
```

### 4. 注册认证路由

在 `main.py` 中：

```python
from routers import supabase_auth

# 注册认证路由（注意放在其他路由之前）
app.include_router(supabase_auth.router, prefix=API_V1_PREFIX)
```

### 5. 使用认证服务

#### 前端示例

```javascript
// 安装Supabase客户端
npm install @supabase/supabase-js

// 初始化
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY
)

// 用户注册
const { data, error } = await supabase.auth.signUp({
  email: 'user@example.com',
  password: 'password123',
  options: {
    data: {
      role: 'media_buyer',
      full_name: '张三'
    }
  }
})

// 用户登录
const { data, error } = await supabase.auth.signInWithPassword({
  email: 'user@example.com',
  password: 'password123'
})

// 获取当前用户
const { data: { user } } = await supabase.auth.getUser()

// 登出
await supabase.auth.signOut()
```

#### API调用示例

```python
# 登录
POST /api/v1/auth/login
{
  "email": "user@example.com",
  "password": "password123",
  "remember_me": false
}

# 响应
{
  "success": true,
  "data": {
    "user": {
      "id": "uuid",
      "email": "user@example.com",
      "profile": {
        "role": "media_buyer",
        "full_name": "张三",
        "is_active": true
      }
    },
    "session": {
      "access_token": "jwt-token",
      "refresh_token": "refresh-token",
      "expires_at": "2024-01-01T00:00:00Z"
    }
  }
}

# 获取当前用户信息
GET /api/v1/auth/me
Headers: Authorization: Bearer <access_token>

# 更新用户资料
PATCH /api/v1/auth/profile
Headers: Authorization: Bearer <access_token>
{
  "full_name": "新名称",
  "phone": "13800138000"
}
```

## 迁移现有用户

如果您有现有用户需要迁移：

```bash
# 1. 检查迁移状态
python scripts/migrate_to_supabase_auth.py check-migration

# 2. 试运行（不实际执行）
python scripts/migrate_to_supabase_auth.py migrate --dry-run

# 3. 执行迁移
python scripts/migrate_to_supabase_auth.py migrate

# 4. 为特定用户创建profile（如果需要）
python scripts/migrate_to_supabase_auth.py create-profile --email user@example.com
```

## 权限控制

### 角色定义

- **admin**: 系统管理员，拥有所有权限
- **finance**: 财务人员，管理充值和对账
- **data_operator**: 数据员，处理日报和数据
- **account_manager**: 账户管理员，管理项目和广告账户
- **media_buyer**: 媒体买家，管理自己的广告账户

### 使用权限装饰器

```python
from deps.supabase_auth import (
    require_admin,
    require_finance,
    require_role,
    require_permission
)

# 需要管理员权限
@router.get("/admin-only")
async def admin_only(
    current_user: Dict = Depends(require_admin)
):
    pass

# 需要财务或管理员权限
@router.get("/finance-endpoint")
async def finance_endpoint(
    current_user: Dict = Depends(require_finance)
):
    pass

# 自定义角色要求
@router.get("/custom-role")
async def custom_role(
    current_user: Dict = Depends(require_role(["admin", "finance"]))
):
    pass

# 特定权限检查
@router.get("/permission-example")
async def permission_example(
    current_user: Dict = Depends(require_permission("manage_projects"))
):
    pass
```

### RLS策略示例

```sql
-- 用户只能访问自己的数据
CREATE POLICY "users_own_data" ON projects
FOR ALL USING (auth.uid() = created_by::text);

-- 财务可以访问所有财务相关数据
CREATE POLICY "finance_access" ON topup_requests
FOR SELECT USING (
    EXISTS (
        SELECT 1 FROM user_profiles
        WHERE id = auth.uid() AND role = 'finance'
    )
);

-- 账户管理员可以管理自己团队的项目
CREATE POLICY "manager_team" ON projects
FOR ALL USING (
    created_by IN (
        SELECT id FROM user_profiles
        WHERE account_manager_id = auth.uid()
    )
);
```

## 常见问题

### Q: 如何处理密码重置？

A: 使用内置的密码重置功能：

```python
# 发送重置邮件
POST /api/v1/auth/reset-password
{
  "email": "user@example.com"
}

# 用户点击邮件中的链接后，在前端：
const { data, error } = await supabase.auth.updateUser({
  password: 'new-password'
})
```

### Q: 如何实现"记住我"功能？

A: 通过设置较长的refresh_token过期时间：

```python
# 登录时设置
POST /api/v1/auth/login
{
  "email": "user@example.com",
  "password": "password123",
  "remember_me": true  // 这将延长session有效期
}
```

### Q: 如何获取用户的真实IP？

A: 使用提供的工具函数：

```python
from deps.supabase_auth import get_client_ip

@app.post("/some-endpoint")
async def some_endpoint(request: Request):
    ip = get_client_ip(request)
    # 使用IP...
```

### Q: 如何自定义用户元数据？

A: 在注册时或通过profile更新接口：

```python
# 注册时
POST /api/v1/auth/register
{
  "email": "user@example.com",
  "password": "password123",
  "role": "media_buyer",
  "full_name": "张三"
}

# 更新profile时
PATCH /api/v1/auth/profile
{
  "preferences": {
    "theme": "dark",
    "notifications": true
  },
  "metadata": {
    "department": "营销部",
    "employee_id": "E001"
  }
}
```

## 安全最佳实践

1. **环境变量安全**
   - 不要在代码中硬编码密钥
   - 使用.env文件管理敏感信息
   - service_role_key只能在后端使用

2. **密码策略**
   - 强制用户在首次登录后修改密码
   - 实施密码强度要求
   - 定期提醒用户更新密码

3. **会话管理**
   - 设置合理的token过期时间
   - 实施会话监控
   - 提供撤销所有会话的功能

4. **日志记录**
   - 记录所有认证事件
   - 监控异常登录行为
   - 实施登录尝试限制

## 故障排除

### 1. JWT验证失败

检查：
- 令牌是否过期
- 令牌格式是否正确（Bearer token）
- Supabase URL和密钥是否正确

### 2. 用户资料未创建

运行：
```bash
python scripts/migrate_to_supabase_auth.py check-migration
```

检查触发器是否正确创建。

### 3. RLS策略问题

使用Supabase SQL编辑器检查：
- 表是否启用了RLS
- 策略是否正确
- 用户是否有必要的权限

## 下一步

1. 查看完整的[API文档](../BACKEND_API_GUIDE.md)
2. 了解[数据库设计](../DATA_SCHEMA.md)
3. 配置[前端集成](../FRONTEND_GUIDE.md)
4. 设置[监控和日志](../MONITORING_OPS.md)

## 支持

如有问题，请：
1. 查看[Supabase文档](https://supabase.com/docs)
2. 提交GitHub Issue
3. 联系开发团队