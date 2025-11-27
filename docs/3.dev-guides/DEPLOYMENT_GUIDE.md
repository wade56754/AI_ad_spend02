---
version: v1.0
status: ready_for_production
layer: dev-guide
owner: wade
last_reviewed: 2025-11-27
baseline: MASTER.md v3.4, SoT Freeze v2.6
---

# 部署指南 (Deployment Guide)

> **互锁文档**:
> - 数据结构 → `../2.sot/DATA_SCHEMA.md` v5.2
> - 状态机 → `../2.sot/STATE_MACHINE.md` v2.6
> - 错误码 → `../2.sot/ERROR_CODES_SOT.md` v2.1
> - 业务规则 → `../2.sot/BUSINESS_RULES.md` v3.1
> - RLS策略 → `../2.sot/RLS_POLICIES_SOT.md` v2.1 (planned)
> - 后端配置 → `BACKEND_SETUP.md`
> - 前端配置 → `FRONTEND_SETUP.md`
> - 测试策略 → `TESTING_GUIDE.md`

---

## 目录

1. [架构概览](#1-架构概览)
2. [环境配置](#2-环境配置)
3. [Supabase配置](#3-supabase配置)
4. [数据库迁移](#4-数据库迁移)
5. [后端部署 (Supabase Edge Functions)](#5-后端部署-supabase-edge-functions)
6. [前端部署 (Vercel)](#6-前端部署-vercel)
7. [环境变量管理](#7-环境变量管理)
8. [监控与日志](#8-监控与日志)
9. [健康检查与冒烟测试](#9-健康检查与冒烟测试)
10. [回滚程序](#10-回滚程序)
11. [安全加固](#11-安全加固)
12. [部署检查清单](#12-部署检查清单)

---

## 1. 架构概览

### 1.1 技术栈

```
┌─────────────────────────────────────────────────────────────┐
│                    AI 广告代投系统                            │
├─────────────────────────────────────────────────────────────┤
│  Frontend (Vercel)                                          │
│  ├─ Next.js 16.0.2 (React 18.3.1)                          │
│  ├─ Tailwind CSS + Radix UI                                │
│  ├─ TypeScript                                             │
│  └─ Supabase Client (@supabase/supabase-js)               │
├─────────────────────────────────────────────────────────────┤
│  Backend (Supabase Edge Functions)                         │
│  ├─ Deno Runtime                                           │
│  ├─ FastAPI (Python 3.11) - optional for complex logic    │
│  └─ PostgreSQL Functions                                   │
├─────────────────────────────────────────────────────────────┤
│  Database & Services (Supabase)                            │
│  ├─ PostgreSQL 15                                          │
│  ├─ Row Level Security (RLS)                               │
│  ├─ Auth (JWT-based)                                       │
│  ├─ Storage                                                │
│  └─ Realtime                                               │
├─────────────────────────────────────────────────────────────┤
│  Infrastructure                                             │
│  ├─ Vercel Edge Network (CDN)                             │
│  ├─ Supabase Global Infrastructure                         │
│  └─ Redis (optional, for caching)                         │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 部署流程概览

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ Development  │────▶│   Staging    │────▶│ Production   │
└──────────────┘     └──────────────┘     └──────────────┘
      │                     │                     │
      ▼                     ▼                     ▼
┌──────────────────────────────────────────────────────────┐
│ 1. 代码提交 → 2. 数据库迁移 → 3. 后端部署 → 4. 前端部署 │
└──────────────────────────────────────────────────────────┘
```

---

## 2. 环境配置

### 2.1 环境说明

本系统支持三个部署环境：

| 环境 | 用途 | 域名示例 | 数据库 | 分支 |
|-----|------|---------|--------|------|
| **Development** | 本地开发 | localhost:3000 | 本地/Supabase Dev | feature/* |
| **Staging** | 集成测试 | staging.example.com | Supabase Staging | develop |
| **Production** | 生产环境 | app.example.com | Supabase Production | master |

### 2.2 环境要求

#### 本地开发环境

- **Node.js**: >= 18.17.0 (推荐使用 LTS)
- **Python**: 3.11
- **PostgreSQL**: 15+ (可选，使用 Supabase 托管则不需要)
- **Git**: >= 2.30
- **Supabase CLI**: >= 1.100.0 (用于本地开发与迁移)
- **Vercel CLI**: >= 32.0.0 (用于本地测试与部署)

#### 安装工具

```bash
# 安装 Supabase CLI
npm install -g supabase

# 安装 Vercel CLI
npm install -g vercel

# 验证安装
supabase --version
vercel --version
```

### 2.3 Supabase 项目初始化

```bash
# 登录 Supabase
supabase login

# 初始化项目 (仅首次)
supabase init

# 链接到远程项目
supabase link --project-ref <your-project-ref>

# 启动本地 Supabase (开发环境)
supabase start
```

---

## 3. Supabase配置

### 3.1 创建 Supabase 项目

1. 访问 [Supabase Dashboard](https://app.supabase.com/)
2. 点击 "New Project"
3. 填写项目信息：
   - **Organization**: 选择或创建组织
   - **Name**: `ai-ad-spend-{env}` (如 `ai-ad-spend-prod`)
   - **Database Password**: 使用强密码（保存至密钥管理系统）
   - **Region**: 选择离用户最近的区域（如 `East Asia (Seoul)`)
   - **Pricing Plan**: 根据需求选择（推荐生产环境使用 Pro）

4. 等待项目初始化（约 2-3 分钟）

### 3.2 获取项目凭证

前往 **Project Settings** > **API**，记录以下信息：

```bash
# Project URL
SUPABASE_URL=https://xxxxxxxxxxxxx.supabase.co

# anon (public) key - 用于前端
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# service_role key - 用于后端管理操作（严格保密）
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# JWT Secret - 用于令牌验证
SUPABASE_JWT_SECRET=your-jwt-secret-here
```

### 3.3 配置 Supabase Auth

1. 前往 **Authentication** > **Providers**
2. 启用所需的认证提供商：
   - **Email**: 启用（必须）
   - **Email Confirmations**: 根据业务需求启用
   - **Password**: 最小长度 8 位，要求大小写+数字
   - **Third-party Providers**: 可选（Google, Facebook 等）

3. 配置邮件模板：
   - 前往 **Authentication** > **Email Templates**
   - 自定义确认邮件、密码重置邮件等

### 3.4 配置 Database

#### 3.4.1 启用必要的 PostgreSQL 扩展

```sql
-- 在 SQL Editor 中执行
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";      -- UUID 生成
CREATE EXTENSION IF NOT EXISTS "pgcrypto";       -- 加密函数
CREATE EXTENSION IF NOT EXISTS "pg_trgm";        -- 模糊搜索
CREATE EXTENSION IF NOT EXISTS "btree_gist";     -- 索引优化
```

#### 3.4.2 配置连接池 (Supavisor)

1. 前往 **Database** > **Connection Pooling**
2. 启用 **Transaction** 模式（推荐用于 FastAPI/SQLAlchemy）
3. 记录连接字符串：

```bash
# Direct connection (管理操作)
DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.xxxxx.supabase.co:5432/postgres

# Pooled connection (应用使用)
DATABASE_POOLER_URL=postgresql://postgres.[PROJECT-REF]:[YOUR-PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres
```

---

## 4. 数据库迁移

### 4.1 迁移策略

本系统使用 **Supabase Migrations** 管理数据库变更，所有迁移文件位于 `backend/migrations/versions/`。

#### 迁移文件命名规范

```
<序号>_<描述>.py
例如: 001_create_daily_reports.py
```

### 4.2 本地开发迁移

#### 创建新迁移

```bash
# 生成新迁移文件
supabase migration new <migration_name>

# 示例
supabase migration new add_user_preferences_table
```

#### 应用迁移

```bash
# 应用所有待执行迁移
supabase db push

# 查看迁移状态
supabase migration list

# 回滚最近一次迁移 (谨慎使用)
supabase db reset
```

### 4.3 生产环境迁移

#### 4.3.1 预部署检查

```bash
# 1. 在本地测试迁移
supabase db reset  # 重置本地数据库
supabase db push   # 应用所有迁移

# 2. 验证迁移脚本
# - 检查 SQL 语法
# - 确保有回滚计划
# - 确认不会丢失数据

# 3. 备份生产数据库
# 在 Supabase Dashboard > Database > Backups 创建手动备份
```

#### 4.3.2 执行迁移

```bash
# 方式1: 使用 Supabase CLI (推荐)
supabase link --project-ref <prod-project-ref>
supabase db push

# 方式2: 通过 SQL Editor 手动执行
# 1. 登录 Supabase Dashboard
# 2. 前往 SQL Editor
# 3. 粘贴迁移 SQL 并执行
```

#### 4.3.3 迁移后验证

```sql
-- 检查表结构
SELECT table_name, column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_schema = 'public'
ORDER BY table_name, ordinal_position;

-- 验证索引
SELECT schemaname, tablename, indexname, indexdef
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname;

-- 检查约束
SELECT conname, contype, conrelid::regclass AS table_name
FROM pg_constraint
WHERE connamespace = 'public'::regnamespace
ORDER BY conrelid::regclass::text;
```

### 4.4 RLS 策略部署

根据 `RLS_POLICIES_SOT.md` v2.1 (planned)，在迁移后应用 Row Level Security 策略：

```sql
-- 启用 RLS
ALTER TABLE daily_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE ad_accounts ENABLE ROW LEVEL SECURITY;
-- ... (其他表)

-- 创建策略示例
CREATE POLICY "Users can view own projects" ON projects
  FOR SELECT
  USING (
    id IN (
      SELECT project_id FROM project_members
      WHERE user_id = auth.uid()
    )
  );

-- 参考迁移文件:
-- - 002_enable_rls_daily_reports.py
-- - 004_enable_rls_projects.py
-- - 006_enable_rls_topup.py
```

### 4.5 迁移回滚计划

**关键原则**: 禁止物理删除数据（参考 `BUSINESS_RULES.md` BR-DATA-001）

#### 非破坏性迁移回滚

```sql
-- 回滚添加列
ALTER TABLE table_name DROP COLUMN column_name;

-- 回滚添加索引
DROP INDEX index_name;

-- 回滚添加约束
ALTER TABLE table_name DROP CONSTRAINT constraint_name;
```

#### 破坏性迁移处理

对于可能丢失数据的迁移（如删除列、修改类型），必须：

1. **创建备份表**
   ```sql
   CREATE TABLE table_name_backup AS SELECT * FROM table_name;
   ```

2. **执行迁移**

3. **验证数据完整性**
   ```sql
   SELECT COUNT(*) FROM table_name;
   SELECT COUNT(*) FROM table_name_backup;
   ```

4. **保留备份表至少 30 天**

---

## 5. 后端部署 (Supabase Edge Functions)

### 5.1 Edge Functions 概述

Supabase Edge Functions 基于 Deno 运行时，用于处理业务逻辑、数据验证等。

### 5.2 创建 Edge Function

```bash
# 创建新函数
supabase functions new <function-name>

# 示例: 创建日报提交函数
supabase functions new submit-daily-report
```

### 5.3 函数结构示例

```typescript
// supabase/functions/submit-daily-report/index.ts
import { serve } from "https://deno.land/std@0.177.0/http/server.ts"
import { createClient } from "https://esm.sh/@supabase/supabase-js@2"

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

serve(async (req) => {
  // 处理 CORS 预检请求
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    // 初始化 Supabase 客户端
    const supabaseClient = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_ANON_KEY') ?? '',
      {
        global: {
          headers: { Authorization: req.headers.get('Authorization')! },
        },
      }
    )

    // 验证用户身份
    const {
      data: { user },
    } = await supabaseClient.auth.getUser()

    if (!user) {
      throw new Error('Unauthorized')
    }

    // 业务逻辑
    const body = await req.json()

    // 数据验证 (参考 ERROR_CODES_SOT.md)
    if (!body.ad_account_id || !body.report_date) {
      return new Response(
        JSON.stringify({
          success: false,
          code: 'VALIDATION_001',
          message: '缺少必需参数',
        }),
        {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
          status: 400,
        }
      )
    }

    // 数据库操作
    const { data, error } = await supabaseClient
      .from('daily_reports')
      .insert({
        ad_account_id: body.ad_account_id,
        report_date: body.report_date,
        status: 'raw_submitted', // 参考 STATE_MACHINE.md
        // ... 其他字段
      })

    if (error) throw error

    // 返回标准 Envelope 格式 (参考 ERROR_CODES_SOT.md)
    return new Response(
      JSON.stringify({
        success: true,
        message: '日报提交成功',
        data: data,
        request_id: crypto.randomUUID(),
        timestamp: new Date().toISOString(),
      }),
      {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 200,
      }
    )
  } catch (error) {
    return new Response(
      JSON.stringify({
        success: false,
        code: 'SYS_001',
        message: error.message,
        request_id: crypto.randomUUID(),
        timestamp: new Date().toISOString(),
      }),
      {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 500,
      }
    )
  }
})
```

### 5.4 本地测试 Edge Functions

```bash
# 启动本地函数服务器
supabase functions serve submit-daily-report

# 在另一个终端测试
curl -i --location --request POST 'http://localhost:54321/functions/v1/submit-daily-report' \
  --header 'Authorization: Bearer YOUR_ANON_KEY' \
  --header 'Content-Type: application/json' \
  --data '{"ad_account_id": 1, "report_date": "2025-11-27"}'
```

### 5.5 部署 Edge Functions

```bash
# 部署单个函数
supabase functions deploy submit-daily-report

# 部署所有函数
supabase functions deploy

# 验证部署
supabase functions list
```

### 5.6 配置函数环境变量

```bash
# 设置函数环境变量
supabase secrets set API_KEY=your_secret_value

# 查看已设置的密钥名称
supabase secrets list

# 删除密钥
supabase secrets unset API_KEY
```

### 5.7 监控 Edge Functions

```bash
# 查看函数日志
supabase functions logs submit-daily-report

# 实时查看日志
supabase functions logs submit-daily-report --follow
```

---

## 6. 前端部署 (Vercel)

### 6.1 准备工作

#### 6.1.1 配置 Next.js

确保 `frontend/package.json` 中的构建脚本正确：

```json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "type-check": "tsc --noEmit"
  }
}
```

#### 6.1.2 创建 Vercel 配置 (可选)

创建 `frontend/vercel.json`：

```json
{
  "buildCommand": "npm run build",
  "devCommand": "npm run dev",
  "installCommand": "npm install",
  "framework": "nextjs",
  "regions": ["sin1", "icn1"],
  "headers": [
    {
      "source": "/api/:path*",
      "headers": [
        {
          "key": "Access-Control-Allow-Origin",
          "value": "*"
        }
      ]
    }
  ],
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "https://xxxxx.supabase.co/:path*"
    }
  ]
}
```

### 6.2 Vercel 项目初始化

#### 6.2.1 通过 CLI 部署

```bash
# 进入前端目录
cd frontend

# 登录 Vercel
vercel login

# 初始化项目 (首次)
vercel

# 按提示操作:
# - Set up and deploy "frontend"? [Y/n] y
# - Which scope? [select your team]
# - Link to existing project? [y/N] n
# - What's your project's name? ai-ad-spend-frontend
# - In which directory is your code located? ./
# - Want to override the settings? [y/N] n
```

#### 6.2.2 通过 Dashboard 部署

1. 访问 [Vercel Dashboard](https://vercel.com/dashboard)
2. 点击 "Add New..." > "Project"
3. 导入 Git 仓库
4. 配置项目：
   - **Framework Preset**: Next.js
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `.next`
   - **Install Command**: `npm install`

### 6.3 配置环境变量

在 Vercel Dashboard > Project Settings > Environment Variables 添加：

```bash
# Supabase 配置
NEXT_PUBLIC_SUPABASE_URL=https://xxxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# 应用配置
NEXT_PUBLIC_APP_NAME=AI广告代投系统
NEXT_PUBLIC_APP_VERSION=2.1.0
NEXT_PUBLIC_ENV_NAME=production

# API 配置 (如使用自定义后端)
NEXT_PUBLIC_API_URL=https://api.example.com

# 可选: 监控配置
NEXT_PUBLIC_SENTRY_DSN=https://xxx@sentry.io/xxx
```

**环境分离**:
- **Production**: 用于生产环境
- **Preview**: 用于预览分支（如 develop）
- **Development**: 用于本地开发

### 6.4 部署流程

#### 6.4.1 自动部署（推荐）

配置后，Vercel 会自动部署：
- **Production**: `master` 分支的每次推送
- **Preview**: 其他分支的每次推送

#### 6.4.2 手动部署

```bash
# 部署到生产环境
vercel --prod

# 部署到预览环境
vercel

# 查看部署状态
vercel ls

# 查看部署日志
vercel logs <deployment-url>
```

### 6.5 自定义域名配置

1. 前往 **Project Settings** > **Domains**
2. 添加自定义域名: `app.example.com`
3. 配置 DNS 记录：

```
类型: CNAME
名称: app
值: cname.vercel-dns.com
```

4. 启用 HTTPS（Vercel 自动提供）

### 6.6 性能优化

#### 6.6.1 启用边缘缓存

在 `frontend/next.config.js` 中配置：

```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  images: {
    domains: ['xxxxx.supabase.co'],
  },
  // 启用 ISR (Incremental Static Regeneration)
  experimental: {
    isrMemoryCacheSize: 0, // 禁用内存缓存（使用 Vercel 缓存）
  },
  // 配置重定向
  async redirects() {
    return [
      {
        source: '/',
        destination: '/dashboard',
        permanent: false,
      },
    ]
  },
}

module.exports = nextConfig
```

#### 6.6.2 优化构建产物

```bash
# 分析包大小
npm install -g @next/bundle-analyzer

# 在 next.config.js 中启用
const withBundleAnalyzer = require('@next/bundle-analyzer')({
  enabled: process.env.ANALYZE === 'true',
})

module.exports = withBundleAnalyzer(nextConfig)

# 运行分析
ANALYZE=true npm run build
```

---

## 7. 环境变量管理

### 7.1 环境变量清单

#### 7.1.1 后端环境变量 (Supabase)

参考 `backend/.env.example`：

```bash
# === 应用基础配置 ===
APP_NAME=AI广告代投系统
APP_VERSION=2.3.0
DEBUG=false
ENV_NAME=production  # development | staging | production

# === 数据库配置 ===
DATABASE_URL=postgresql://postgres:[PASSWORD]@db.xxxxx.supabase.co:5432/postgres
POOL_SIZE=20
MAX_OVERFLOW=30
POOL_TIMEOUT=30
DB_POOL_PRE_PING=true
DB_POOL_RECYCLE=3600

# === RLS 和审计日志 ===
ENABLE_RLS=true
ENABLE_AUDIT_LOG=true
AUDIT_LOG_RETENTION_DAYS=365

# === JWT 和加密 ===
# 生成命令: openssl rand -hex 32
JWT_SECRET=<64-char-hex-string>
ENCRYPTION_KEY=<32-char-hex-string>
PASSWORD_SALT_ROUNDS=12
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# === Supabase 配置 ===
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIs...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIs...
SUPABASE_JWT_SECRET=your-jwt-secret

# === CORS 配置 ===
ALLOWED_ORIGINS=["https://app.example.com"]

# === API 安全配置 ===
RATE_LIMIT=1000
RATE_WINDOW=60
MAX_FILE_SIZE=10485760
BCRYPT_ROUNDS=12

# === 日志配置 ===
LOG_LEVEL=INFO           # DEBUG | INFO | WARNING | ERROR
LOG_FORMAT=json          # json | text
LOG_REQUEST_ID_ENABLED=true

# === Redis 配置 (可选) ===
REDIS_URL=redis://localhost:6379/0
REDIS_DB=0
REDIS_PASSWORD=
REDIS_MAX_CONNECTIONS=20

# === 监控配置 (可选) ===
SENTRY_DSN=https://xxx@sentry.io/xxx
SENTRY_TRACES_SAMPLE_RATE=1.0
SENTRY_ENVIRONMENT=production

# === SMTP 配置 (可选) ===
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_USE_TLS=true
```

#### 7.1.2 前端环境变量 (Vercel)

```bash
# === Supabase 配置 ===
NEXT_PUBLIC_SUPABASE_URL=https://xxxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIs...

# === 应用配置 ===
NEXT_PUBLIC_APP_NAME=AI广告代投系统
NEXT_PUBLIC_APP_VERSION=2.1.0
NEXT_PUBLIC_ENV_NAME=production

# === API 配置 ===
NEXT_PUBLIC_API_URL=https://app.example.com/api

# === 监控配置 ===
NEXT_PUBLIC_SENTRY_DSN=https://xxx@sentry.io/xxx

# === 功能开关 ===
NEXT_PUBLIC_ENABLE_ANALYTICS=true
NEXT_PUBLIC_ENABLE_DEBUG=false
```

### 7.2 密钥生成

#### 7.2.1 生成强随机密钥

```bash
# 生成 64 字符 JWT Secret
openssl rand -hex 32

# 生成 32 字符 Encryption Key
openssl rand -hex 16

# 生成 UUID (用于 request_id)
python3 -c "import uuid; print(uuid.uuid4())"

# Python 方式生成 (推荐)
python3 -c "import secrets; print(secrets.token_urlsafe(64))"
```

#### 7.2.2 密钥轮换策略

- **JWT Secret**: 每 90 天轮换一次
- **Encryption Key**: 每 180 天轮换一次
- **Database Password**: 每 90 天轮换一次
- **Service Role Key**: 不轮换（除非泄露）

### 7.3 密钥管理最佳实践

1. **禁止硬编码**: 所有密钥必须通过环境变量注入
2. **密钥分离**: 不同环境使用不同密钥
3. **最小权限**: Service Role Key 仅用于后端管理操作
4. **审计日志**: 记录所有使用 Service Role Key 的操作
5. **定期审查**: 每季度审查环境变量配置

---

## 8. 监控与日志

### 8.1 Supabase 内置监控

#### 8.1.1 数据库监控

1. 前往 **Database** > **Reports**
2. 查看关键指标：
   - **Query Performance**: 慢查询分析
   - **Database Health**: CPU、内存、磁盘使用率
   - **Active Connections**: 连接数监控

3. 配置告警（Pro 计划）：
   - CPU 使用率 > 80%
   - 磁盘使用率 > 90%
   - 连接数 > 80% 配额

#### 8.1.2 API 监控

1. 前往 **Logs** > **API Logs**
2. 筛选关键事件：
   - 4xx 错误（客户端错误）
   - 5xx 错误（服务器错误）
   - 慢请求（> 1000ms）

### 8.2 Vercel Analytics

#### 8.2.1 启用 Web Analytics

在 `frontend/app/layout.tsx` 中添加：

```typescript
import { Analytics } from '@vercel/analytics/react';

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="zh-CN">
      <body>
        {children}
        <Analytics />
      </body>
    </html>
  )
}
```

#### 8.2.2 监控指标

- **Real Experience Score (RES)**: 用户体验评分
- **Core Web Vitals**: LCP、FID、CLS
- **Page Views**: 页面访问量
- **Unique Visitors**: 独立访客

### 8.3 应用日志管理

#### 8.3.1 日志级别定义

参考 `ERROR_CODES_SOT.md` v2.1：

| 级别 | 用途 | 示例 |
|-----|------|------|
| **DEBUG** | 开发调试 | 变量值、函数调用 |
| **INFO** | 业务操作 | 用户登录、日报提交 |
| **WARNING** | 潜在问题 | 趋势异常、权限不足 |
| **ERROR** | 业务错误 | 数据验证失败、状态流转非法 |
| **CRITICAL** | 系统故障 | 数据库连接失败、服务不可用 |

#### 8.3.2 日志格式（JSON）

```json
{
  "timestamp": "2025-11-27T10:30:00Z",
  "level": "INFO",
  "message": "日报提交成功",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "user-uuid-here",
  "code": "BIZ_001",
  "data": {
    "ad_account_id": 123,
    "report_date": "2025-11-27"
  }
}
```

#### 8.3.3 查询日志

```bash
# Supabase Edge Functions 日志
supabase functions logs <function-name> --follow

# Vercel 部署日志
vercel logs <deployment-url>

# 筛选错误日志
supabase functions logs <function-name> | grep "ERROR"
```

### 8.4 第三方监控 (Sentry)

#### 8.4.1 安装配置

```bash
# 前端安装
cd frontend
npm install @sentry/nextjs

# 初始化
npx @sentry/wizard -i nextjs
```

#### 8.4.2 配置 Sentry

在 `frontend/sentry.client.config.ts` 中：

```typescript
import * as Sentry from "@sentry/nextjs";

Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
  environment: process.env.NEXT_PUBLIC_ENV_NAME,
  tracesSampleRate: 1.0,
  integrations: [
    new Sentry.BrowserTracing(),
    new Sentry.Replay({
      maskAllText: true,
      blockAllMedia: true,
    }),
  ],
  replaysSessionSampleRate: 0.1,
  replaysOnErrorSampleRate: 1.0,
});
```

#### 8.4.3 捕获异常

```typescript
try {
  // 业务逻辑
} catch (error) {
  Sentry.captureException(error, {
    tags: {
      module: 'daily-report',
      operation: 'submit',
    },
    extra: {
      ad_account_id: 123,
      report_date: '2025-11-27',
    },
  });
  throw error;
}
```

---

## 9. 健康检查与冒烟测试

### 9.1 健康检查端点

#### 9.1.1 后端健康检查

创建 Edge Function: `supabase/functions/health/index.ts`

```typescript
import { serve } from "https://deno.land/std@0.177.0/http/server.ts"

serve(async (req) => {
  try {
    // 检查数据库连接
    const dbCheck = await checkDatabase();

    // 检查 Auth 服务
    const authCheck = await checkAuth();

    const health = {
      status: 'healthy',
      timestamp: new Date().toISOString(),
      version: '2.3.0',
      checks: {
        database: dbCheck,
        auth: authCheck,
      },
    };

    return new Response(JSON.stringify(health), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    });
  } catch (error) {
    return new Response(
      JSON.stringify({
        status: 'unhealthy',
        error: error.message,
      }),
      {
        status: 503,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
});

async function checkDatabase() {
  // 简单查询测试
  const client = createClient(/* ... */);
  const { data, error } = await client.from('users').select('count');
  if (error) throw error;
  return { status: 'ok', latency: '10ms' };
}

async function checkAuth() {
  // Auth 服务测试
  return { status: 'ok' };
}
```

#### 9.1.2 前端健康检查

创建 `frontend/app/api/health/route.ts`：

```typescript
import { NextResponse } from 'next/server';

export async function GET() {
  const health = {
    status: 'healthy',
    timestamp: new Date().toISOString(),
    version: process.env.NEXT_PUBLIC_APP_VERSION,
    environment: process.env.NEXT_PUBLIC_ENV_NAME,
  };

  return NextResponse.json(health);
}
```

### 9.2 冒烟测试脚本

创建 `scripts/smoke-test.sh`：

```bash
#!/bin/bash
set -e

ENV=${1:-staging}
BASE_URL=${2:-https://staging.example.com}

echo "========================================"
echo "冒烟测试: $ENV 环境"
echo "========================================"

# 1. 检查前端健康
echo "检查前端健康..."
curl -f "$BASE_URL/api/health" || exit 1
echo "✓ 前端健康检查通过"

# 2. 检查后端健康
echo "检查后端健康..."
SUPABASE_URL=$(grep NEXT_PUBLIC_SUPABASE_URL .env.$ENV | cut -d '=' -f2)
curl -f "$SUPABASE_URL/functions/v1/health" || exit 1
echo "✓ 后端健康检查通过"

# 3. 测试登录接口
echo "测试登录接口..."
LOGIN_RESPONSE=$(curl -s -X POST "$SUPABASE_URL/auth/v1/token?grant_type=password" \
  -H "apikey: $SUPABASE_ANON_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"test@example.com\",\"password\":\"testpassword\"}")

if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
  echo "✓ 登录接口正常"
else
  echo "✗ 登录接口异常"
  exit 1
fi

# 4. 测试数据库连接
echo "测试数据库连接..."
# (通过健康检查已覆盖)

# 5. 测试 API 响应格式 (Envelope)
echo "测试 API Envelope 格式..."
API_RESPONSE=$(curl -s "$SUPABASE_URL/functions/v1/some-endpoint" \
  -H "Authorization: Bearer $ACCESS_TOKEN")

if echo "$API_RESPONSE" | jq -e '.success' > /dev/null; then
  echo "✓ Envelope 格式正确"
else
  echo "✗ Envelope 格式错误"
  exit 1
fi

echo "========================================"
echo "✓ 所有冒烟测试通过"
echo "========================================"
```

使用方式：

```bash
# 测试 Staging 环境
bash scripts/smoke-test.sh staging https://staging.example.com

# 测试 Production 环境
bash scripts/smoke-test.sh production https://app.example.com
```

### 9.3 部署验证检查表

- [ ] 前端首页可访问
- [ ] 登录功能正常
- [ ] 数据库连接正常
- [ ] API 返回正确的 Envelope 格式
- [ ] 状态机流转正常（提交日报 → `raw_submitted`）
- [ ] 错误码符合 `ERROR_CODES_SOT.md` 规范
- [ ] 审计日志正常记录
- [ ] RLS 策略生效（用户只能查看自己的数据）
- [ ] 监控告警配置正确
- [ ] 性能指标在可接受范围（P95 < 500ms）

---

## 10. 回滚程序

### 10.1 前端回滚

#### 10.1.1 Vercel 回滚

```bash
# 方式1: 通过 CLI
vercel rollback <deployment-url>

# 方式2: 通过 Dashboard
# 1. 前往 Vercel Dashboard > Deployments
# 2. 找到上一个稳定版本
# 3. 点击 "..." > "Promote to Production"
```

#### 10.1.2 验证回滚

```bash
# 检查当前部署版本
curl https://app.example.com/api/health | jq '.version'

# 预期输出: "2.0.0" (回滚前版本)
```

### 10.2 后端回滚 (Edge Functions)

#### 10.2.1 回滚函数

```bash
# 查看函数版本历史
supabase functions list

# 回滚到指定版本
supabase functions deploy <function-name> --version <version-id>
```

#### 10.2.2 紧急回滚

如果函数完全不可用，临时禁用：

```sql
-- 在 SQL Editor 中执行
DROP FUNCTION IF EXISTS public.<function_name>;
```

### 10.3 数据库回滚

#### 10.3.1 迁移回滚

```bash
# 回滚最近一次迁移
supabase db reset

# 回滚到指定迁移
# 1. 手动在 SQL Editor 中执行回滚脚本
# 2. 或使用数据库备份恢复
```

#### 10.3.2 从备份恢复

1. 前往 **Database** > **Backups**
2. 选择备份点（推荐迁移前的备份）
3. 点击 "Restore"
4. 确认恢复操作（注意：会丢失恢复点之后的所有数据）

**警告**: 数据库恢复会导致数据丢失，仅在紧急情况下使用。

### 10.4 回滚决策流程

```
┌─────────────────────┐
│ 发现生产问题         │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 问题严重程度评估     │
└──────────┬──────────┘
           │
     ┌─────┴─────┐
     │           │
    严重        不严重
     │           │
     ▼           ▼
┌────────┐  ┌─────────┐
│ 立即回滚 │  │ 发布修复 │
└────────┘  └─────────┘

严重问题定义:
- 用户无法登录
- 数据丢失/损坏
- 核心业务流程中断
- 安全漏洞
```

---

## 11. 安全加固

### 11.1 数据库安全

#### 11.1.1 启用 SSL/TLS

Supabase 默认强制 SSL，确保连接字符串包含 `sslmode=require`：

```bash
DATABASE_URL=postgresql://postgres:[PASSWORD]@db.xxxxx.supabase.co:5432/postgres?sslmode=require
```

#### 11.1.2 限制数据库访问

1. 前往 **Database** > **Network Restrictions**
2. 配置 IP 白名单（仅允许必要的 IP）
3. 禁用公网访问（如不需要）

#### 11.1.3 审计数据库操作

确保 `ENABLE_AUDIT_LOG=true`，并定期审查：

```sql
-- 查询最近的管理操作
SELECT * FROM audit_logs
WHERE operation IN ('DELETE', 'UPDATE', 'ALTER', 'DROP')
  AND created_at > NOW() - INTERVAL '7 days'
ORDER BY created_at DESC;

-- 查询异常登录
SELECT * FROM user_sessions
WHERE is_suspicious = true
  AND created_at > NOW() - INTERVAL '24 hours';
```

### 11.2 应用安全

#### 11.2.1 CORS 配置

严格限制允许的源：

```bash
# 生产环境 (错误示例)
ALLOWED_ORIGINS=["*"]  # ❌ 禁止使用通配符

# 生产环境 (正确示例)
ALLOWED_ORIGINS=["https://app.example.com","https://www.example.com"]  # ✅
```

#### 11.2.2 速率限制

配置 API 速率限制（参考 `.env.example`）：

```bash
RATE_LIMIT=1000      # 每窗口期最大请求数
RATE_WINDOW=60       # 窗口期（秒）
```

在 Edge Functions 中实现：

```typescript
// 使用 Upstash Rate Limit (推荐)
import { Ratelimit } from "@upstash/ratelimit";
import { Redis } from "@upstash/redis";

const redis = new Redis({
  url: Deno.env.get("UPSTASH_REDIS_REST_URL")!,
  token: Deno.env.get("UPSTASH_REDIS_REST_TOKEN")!,
});

const ratelimit = new Ratelimit({
  redis: redis,
  limiter: Ratelimit.slidingWindow(1000, "60 s"),
});

serve(async (req) => {
  const ip = req.headers.get("x-forwarded-for") ?? "anonymous";
  const { success } = await ratelimit.limit(ip);

  if (!success) {
    return new Response(
      JSON.stringify({
        success: false,
        code: "SYS_003",
        message: "请求过于频繁",
      }),
      { status: 429 }
    );
  }

  // 继续处理请求...
});
```

#### 11.2.3 输入验证

所有用户输入必须验证（参考 `ERROR_CODES_SOT.md` VALIDATION_ 系列）：

```typescript
import { z } from "zod";

const DailyReportSchema = z.object({
  ad_account_id: z.number().int().positive(),
  report_date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
  spend: z.number().nonnegative(),
  // ...
});

try {
  const validated = DailyReportSchema.parse(body);
} catch (error) {
  return errorResponse("VALIDATION_001", "参数验证失败", 400);
}
```

### 11.3 密钥管理

#### 11.3.1 密钥轮换

定期轮换以下密钥：

```bash
# 生成新的 JWT Secret
NEW_JWT_SECRET=$(openssl rand -hex 32)

# 更新环境变量
# 1. Supabase: supabase secrets set JWT_SECRET=$NEW_JWT_SECRET
# 2. Vercel: 在 Dashboard 更新

# 逐步迁移（双密钥验证）
# - 同时支持旧密钥和新密钥（7天过渡期）
# - 7天后删除旧密钥
```

#### 11.3.2 密钥泄露应急

如果密钥泄露：

1. **立即轮换密钥**
2. **撤销所有活跃会话**
   ```sql
   DELETE FROM user_sessions WHERE is_valid = true;
   ```
3. **审查访问日志**，确认是否有异常操作
4. **通知受影响用户**重新登录

### 11.4 依赖安全

#### 11.4.1 定期更新依赖

```bash
# 检查前端依赖漏洞
cd frontend
npm audit

# 修复漏洞
npm audit fix

# 强制修复（可能破坏兼容性）
npm audit fix --force

# 后端依赖扫描
pip install safety
safety check
```

#### 11.4.2 启用 Dependabot (GitHub)

创建 `.github/dependabot.yml`：

```yaml
version: 2
updates:
  - package-ecosystem: "npm"
    directory: "/frontend"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 10

  - package-ecosystem: "pip"
    directory: "/backend"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 10
```

---

## 12. 部署检查清单

### 12.1 部署前检查

#### 12.1.1 代码质量

- [ ] 所有测试通过 (`npm test`, `pytest`)
- [ ] 类型检查通过 (`tsc --noEmit`)
- [ ] Lint 检查通过 (`npm run lint`, `flake8`)
- [ ] 代码审查完成（至少 1 人审批）
- [ ] 无未解决的 TODO/FIXME

#### 12.1.2 SoT 合规性

- [ ] 状态机流转符合 `STATE_MACHINE.md` v2.6
- [ ] 错误码使用符合 `ERROR_CODES_SOT.md` v2.1
- [ ] 数据结构符合 `DATA_SCHEMA.md` v5.2
- [ ] 业务规则符合 `BUSINESS_RULES.md` v3.1
- [ ] API 响应使用 Envelope 格式
- [ ] 金额使用 Decimal (2位小数)
- [ ] 时间使用 UTC (TIMESTAMPTZ)

#### 12.1.3 安全检查

- [ ] 环境变量已配置且无硬编码密钥
- [ ] JWT Secret 强度足够（≥64字符）
- [ ] CORS 配置正确（无 `*` 通配符）
- [ ] RLS 策略已启用
- [ ] 依赖无已知漏洞 (`npm audit`, `safety check`)
- [ ] 输入验证完整
- [ ] 速率限制已配置

#### 12.1.4 数据库检查

- [ ] 迁移脚本已测试
- [ ] 迁移前已创建备份
- [ ] 索引已优化
- [ ] 外键约束正确
- [ ] 状态枚举符合 `STATE_MACHINE.md`

### 12.2 部署中检查

- [ ] 数据库迁移成功
- [ ] 无迁移错误或警告
- [ ] Edge Functions 部署成功
- [ ] 前端构建成功（无错误）
- [ ] 环境变量已注入
- [ ] DNS 配置正确

### 12.3 部署后检查

#### 12.3.1 功能验证

- [ ] 冒烟测试通过 (`bash scripts/smoke-test.sh`)
- [ ] 健康检查端点正常 (`/api/health`)
- [ ] 登录功能正常
- [ ] 核心业务流程正常（日报提交、充值申请等）
- [ ] 数据查询正常（列表、详情、搜索）

#### 12.3.2 性能验证

- [ ] 页面加载时间 < 3秒
- [ ] API 响应时间 P95 < 500ms
- [ ] 数据库查询无慢查询（> 1秒）
- [ ] Core Web Vitals 正常（LCP < 2.5s）

#### 12.3.3 安全验证

- [ ] RLS 策略生效（用户只能看到授权数据）
- [ ] 未授权访问返回 403
- [ ] SQL 注入防护生效
- [ ] XSS 防护生效
- [ ] HTTPS 强制启用

#### 12.3.4 监控验证

- [ ] 日志正常输出
- [ ] Sentry 错误追踪正常
- [ ] 数据库监控正常
- [ ] 告警配置正确
- [ ] 审计日志正常记录

### 12.4 回滚准备

- [ ] 前一版本部署 URL 已记录
- [ ] 数据库备份已验证可恢复
- [ ] 回滚脚本已测试
- [ ] 回滚决策树已沟通
- [ ] 紧急联系人列表已更新

---

## 13. 常见问题 (FAQ)

### 13.1 部署问题

**Q: Vercel 构建失败，提示 "Module not found"**

A: 检查 `package.json` 依赖是否正确安装，运行 `npm install` 后重新部署。

**Q: Edge Function 部署后无响应**

A: 检查函数日志 (`supabase functions logs <name>`)，确认环境变量和权限配置。

**Q: 数据库迁移失败**

A: 回滚到备份点，检查迁移脚本 SQL 语法，确保无约束冲突。

### 13.2 性能问题

**Q: API 响应慢（> 1秒）**

A:
1. 检查数据库索引是否完整
2. 启用查询缓存（Redis）
3. 优化 SQL 查询（避免 N+1）
4. 使用 Connection Pooling

**Q: 前端加载慢**

A:
1. 启用 Next.js ISR
2. 优化图片（使用 WebP）
3. 启用 CDN 缓存
4. 减少 bundle 大小（Code Splitting）

### 13.3 安全问题

**Q: 用户可以看到其他人的数据**

A: 检查 RLS 策略是否启用，确认 `auth.uid()` 验证正确。

**Q: 密钥泄露到 Git 仓库**

A:
1. 立即轮换密钥
2. 撤销 Git 历史中的密钥（`git filter-branch` 或 BFG Repo-Cleaner）
3. 审查访问日志

---

## 14. 附录

### 14.1 参考文档

- **核心规范**:
  - `docs/1.core/MASTER.md` v3.4 - 系统总纲
- **SoT 文档**:
  - `docs/2.sot/DATA_SCHEMA.md` v5.2 - 数据结构
  - `docs/2.sot/STATE_MACHINE.md` v2.6 - 状态机
  - `docs/2.sot/ERROR_CODES_SOT.md` v2.1 - 错误码
  - `docs/2.sot/BUSINESS_RULES.md` v3.1 - 业务规则
- **开发指南**:
  - `docs/3.dev-guides/BACKEND_SETUP.md` - 后端配置
  - `docs/3.dev-guides/FRONTEND_SETUP.md` - 前端配置
  - `docs/3.dev-guides/TESTING_GUIDE.md` - 测试策略

### 14.2 外部资源

- [Supabase 官方文档](https://supabase.com/docs)
- [Vercel 官方文档](https://vercel.com/docs)
- [Next.js 官方文档](https://nextjs.org/docs)
- [PostgreSQL 官方文档](https://www.postgresql.org/docs/)

### 14.3 更新历史

| 版本 | 日期 | 作者 | 变更说明 |
|-----|------|------|---------|
| v1.0 | 2025-11-27 | wade | 初始版本，完整部署流程 |

---

**文档结束**

如有疑问，请联系项目负责人或查阅相关 SoT 文档。
