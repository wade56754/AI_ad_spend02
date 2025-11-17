# Supabase 前端集成指南

> **版本**: 1.0
> **更新日期**: 2025-11-16
> **状态**: ✅ 已完成

---

## 📋 概览

前端已集成 Supabase Auth，支持用户注册、登录、登出、密码重置等功能。

---

## 🚀 快速开始

### 1. 配置环境变量

创建 `frontend/.env.local` 文件：

```bash
# Supabase 配置
NEXT_PUBLIC_SUPABASE_URL=https://jzmcoivxhiyidizncyaq.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key_here
```

**获取 Anon Key**:
1. 访问 [Supabase Dashboard](https://app.supabase.com/project/jzmcoivxhiyidizncyaq/settings/api)
2. 进入 **Settings → API**
3. 复制 **anon / public** key

### 2. 安装依赖

```bash
cd frontend
npm install @supabase/supabase-js --legacy-peer-deps
```

---

## 📁 文件结构

```
frontend/
├── lib/
│   └── supabase.ts          # Supabase 客户端配置
├── hooks/
│   └── use-auth.ts          # 认证 Hook
├── app/
│   └── auth/
│       ├── login/           # 登录页面
│       ├── sign-up/         # 注册页面
│       ├── forgot-password/ # 忘记密码
│       └── update-password/ # 更新密码
└── .env.local.example       # 环境变量示例
```

---

## 🔧 使用方法

### 方法 1：使用 `useAuth` Hook（推荐）

```tsx
'use client'

import { useAuth } from '@/hooks/use-auth'

export default function LoginPage() {
  const { signIn, loading, error } = useAuth()

  const handleLogin = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const formData = new FormData(e.currentTarget)
    const email = formData.get('email') as string
    const password = formData.get('password') as string

    const { success, error } = await signIn(email, password)

    if (success) {
      // 登录成功，自动跳转到首页
      console.log('登录成功')
    } else {
      // 显示错误
      console.error('登录失败:', error)
    }
  }

  return (
    <form onSubmit={handleLogin}>
      <input type="email" name="email" required />
      <input type="password" name="password" required />
      <button type="submit" disabled={loading}>
        {loading ? '登录中...' : '登录'}
      </button>
      {error && <p className="error">{error}</p>}
    </form>
  )
}
```

### 方法 2：直接使用 Supabase 客户端

```tsx
import { supabase, signIn } from '@/lib/supabase'

// 登录
const { data, error } = await signIn('user@example.com', 'password123')

// 注册
const { data, error } = await supabase.auth.signUp({
  email: 'user@example.com',
  password: 'password123',
  options: {
    data: {
      username: 'johndoe',
      full_name: 'John Doe',
      role: 'media_buyer'
    }
  }
})

// 登出
await supabase.auth.signOut()
```

---

## 🎯 `useAuth` Hook API

### 状态

```typescript
{
  user: User | null              // Supabase Auth 用户对象
  profile: UserProfile | null    // 用户业务信息
  session: Session | null        // 当前会话
  loading: boolean               // 加载状态
  error: string | null           // 错误信息
  isAuthenticated: boolean       // 是否已登录
}
```

### 方法

```typescript
{
  signIn(email, password)        // 登录
  signUp(email, password, metadata) // 注册
  signOut()                      // 登出
  resetPassword(email)           // 重置密码
  updatePassword(newPassword)    // 更新密码
}
```

---

## 🔐 认证流程

### 1. 用户注册

```typescript
const { success, error } = await signUp(
  'user@example.com',
  'password123',
  {
    username: 'johndoe',
    full_name: 'John Doe',
    role: 'media_buyer'
  }
)

if (success) {
  // 注册成功
  // 1. Supabase Auth 创建用户
  // 2. 触发器自动在 user_profiles 创建记录
  // 3. 发送验证邮件（如果启用）
}
```

### 2. 用户登录

```typescript
const { success, error } = await signIn(
  'user@example.com',
  'password123'
)

if (success) {
  // 登录成功
  // 1. 获取 JWT Token
  // 2. 自动加载 user_profile
  // 3. 跳转到首页
}
```

### 3. 自动登录

Hook 会自动检测现有会话：

```typescript
useEffect(() => {
  // 页面加载时自动检查是否已登录
  // 如果有有效 session，自动登录
}, [])
```

### 4. 会话刷新

Supabase 自动处理 Token 刷新：

```typescript
supabase.auth.onAuthStateChange((event, session) => {
  if (event === 'TOKEN_REFRESHED') {
    // Token 已自动刷新
  }
})
```

---

## 📊 用户 Profile 结构

```typescript
interface UserProfile {
  id: string                     // UUID (与 auth.users.id 一致)
  username: string | null        // 用户名
  full_name: string | null       // 全名
  phone: string | null           // 电话
  avatar_url: string | null      // 头像 URL
  role: 'admin' | 'finance' | 'data_operator' | 'account_manager' | 'media_buyer'
  department: string | null      // 部门
  position: string | null        // 职位
  account_manager_id: string | null // 上级经理 ID
  is_active: boolean             // 是否激活
  is_verified: boolean           // 是否已验证
  last_login_at: string | null   // 最后登录时间
  last_login_ip: string | null   // 最后登录 IP
  preferences: Record<string, any> // 用户偏好
  timezone: string               // 时区
  language: string               // 语言
  notification_settings: Record<string, any> // 通知设置
  profile_metadata: Record<string, any> // 元数据
  created_at: string            // 创建时间
  updated_at: string            // 更新时间
}
```

---

## 🛡️ 权限控制

### RLS 策略

Supabase 已配置 6 条 RLS 策略：

1. **Users can view own profile** - 用户可查看自己的 profile
2. **Users can update own profile** - 用户可更新自己的 profile（不能改 role）
3. **Admins can view all profiles** - 管理员可查看所有 profiles
4. **Admins can update all profiles** - 管理员可更新所有 profiles
5. **Admins can insert profiles** - 管理员可插入新 profiles
6. **Admins can delete profiles** - 管理员可删除 profiles

### 客户端检查

```typescript
const { profile } = useAuth()

// 检查角色
if (profile?.role === 'admin') {
  // 管理员功能
}

// 检查权限
if (['admin', 'finance'].includes(profile?.role)) {
  // 财务相关功能
}
```

---

## 🧪 测试用户

系统已创建 3 个测试用户：

| 邮箱 | 密码 | 角色 | 用途 |
|------|------|------|------|
| admin@test.com | Test123456! | admin | 测试管理员功能 |
| manager@test.com | Test123456! | account_manager | 测试客户经理功能 |
| buyer@test.com | Test123456! | media_buyer | 测试投手功能 |

---

## 🔍 调试

### 查看当前会话

```typescript
import { getSession } from '@/lib/supabase'

const session = await getSession()
console.log('Current session:', session)
```

### 监听认证事件

```typescript
supabase.auth.onAuthStateChange((event, session) => {
  console.log('Auth event:', event)
  console.log('Session:', session)
})
```

### 常见事件

- `SIGNED_IN` - 用户登录
- `SIGNED_OUT` - 用户登出
- `TOKEN_REFRESHED` - Token 刷新
- `USER_UPDATED` - 用户信息更新
- `PASSWORD_RECOVERY` - 密码恢复

---

## ❓ 常见问题

### Q1: 注册后没有自动创建 user_profile？

**A**: 检查触发器是否正常：

```sql
SELECT trigger_name
FROM information_schema.triggers
WHERE trigger_name = 'on_auth_user_created';
```

### Q2: RLS 策略导致无法查询数据？

**A**: 确保请求携带有效的 JWT Token：

```typescript
// Supabase 客户端会自动处理
// 确保在登录后查询
const { data } = await supabase
  .from('user_profiles')
  .select('*')
```

### Q3: 如何在服务端获取用户信息？

**A**: 使用 Server Components：

```typescript
import { createServerClient } from '@supabase/ssr'
import { cookies } from 'next/headers'

export async function getUser() {
  const cookieStore = cookies()

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        get(name: string) {
          return cookieStore.get(name)?.value
        },
      },
    }
  )

  const { data: { user } } = await supabase.auth.getUser()
  return user
}
```

---

## 📚 参考资料

- [Supabase Auth 文档](https://supabase.com/docs/guides/auth)
- [Next.js + Supabase](https://supabase.com/docs/guides/getting-started/tutorials/with-nextjs)
- [RLS 策略指南](https://supabase.com/docs/guides/auth/row-level-security)

---

**文档版本**: 1.0
**最后更新**: 2025-11-16
**维护责任人**: 前端团队
