# Supabase 快速设置指南

## 📋 前置条件

1. 确保您已经有Supabase项目
2. 已获得项目URL和API密钥
3. 有足够的权限执行DDL操作

## 🚀 快速执行步骤

### 第1步：登录Supabase

1. 访问 [https://supabase.com](https://supabase.com)
2. 登录您的账号
3. 选择您的项目：`jzmcoivxhiyidizncyaq`

### 第2步：打开SQL编辑器

1. 在左侧菜单中点击 **SQL Editor**
2. 点击 **New query** 创建新查询

### 第3步：复制并执行脚本

复制以下脚本并粘贴到SQL编辑器中：

```sql
-- AI广告代投系统数据库初始化脚本
-- 设置执行参数
SET statement_timeout = '600s';
SET search_path = public;

-- 创建必要的扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 创建用户表
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    avatar_url TEXT,
    role VARCHAR(20) NOT NULL DEFAULT 'media_buyer',
    is_active BOOLEAN NOT NULL DEFAULT true,
    is_superuser BOOLEAN NOT NULL DEFAULT false,
    email_verified BOOLEAN NOT NULL DEFAULT false,
    last_login_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT users_role_check CHECK (role IN ('admin', 'finance', 'data_operator', 'account_manager', 'media_buyer'))
);

-- 创建项目表
CREATE TABLE IF NOT EXISTS projects (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    client_name VARCHAR(100) NOT NULL,
    client_email VARCHAR(255),
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    budget DECIMAL(12, 2),
    currency VARCHAR(3) DEFAULT 'CNY',
    start_date DATE,
    end_date DATE,
    owner_id INTEGER NOT NULL REFERENCES users(id),
    created_by INTEGER NOT NULL REFERENCES users(id),
    updated_by INTEGER NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT projects_status_check CHECK (status IN ('active', 'paused', 'completed', 'cancelled'))
);

-- 创建渠道表
CREATE TABLE IF NOT EXISTS channels (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    platform VARCHAR(50) NOT NULL,
    account_id VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    manager_id INTEGER REFERENCES users(id),
    created_by INTEGER NOT NULL REFERENCES users(id),
    updated_by INTEGER NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT channels_status_check CHECK (status IN ('active', 'inactive', 'suspended')),
    UNIQUE(platform, account_id)
);

-- 创建广告账户表
CREATE TABLE IF NOT EXISTS ad_accounts (
    id SERIAL PRIMARY KEY,
    account_id VARCHAR(100) NOT NULL,
    name VARCHAR(100) NOT NULL,
    platform VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    channel_id INTEGER NOT NULL REFERENCES channels(id),
    project_id INTEGER REFERENCES projects(id),
    assigned_to INTEGER REFERENCES users(id),
    balance DECIMAL(12, 2) DEFAULT 0,
    spent DECIMAL(12, 2) DEFAULT 0,
    currency VARCHAR(3) DEFAULT 'CNY',
    created_by INTEGER NOT NULL REFERENCES users(id),
    updated_by INTEGER NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ad_accounts_status_check CHECK (status IN ('active', 'inactive', 'banned', 'pending', 'suspended')),
    UNIQUE(platform, account_id)
);

-- 创建日报表
CREATE TABLE IF NOT EXISTS daily_reports (
    id SERIAL PRIMARY KEY,
    report_date DATE NOT NULL,
    account_id INTEGER NOT NULL REFERENCES ad_accounts(id),
    submitter_id INTEGER NOT NULL REFERENCES users(id),
    status VARCHAR(20) NOT NULL DEFAULT 'draft',
    spend DECIMAL(10, 2) NOT NULL DEFAULT 0,
    impressions INTEGER NOT NULL DEFAULT 0,
    clicks INTEGER NOT NULL DEFAULT 0,
    conversions INTEGER NOT NULL DEFAULT 0,
    revenue DECIMAL(10, 2) DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT daily_reports_status_check CHECK (status IN ('draft', 'submitted', 'reviewed', 'approved', 'rejected')),
    UNIQUE(report_date, account_id)
);

-- 创建充值表
CREATE TABLE IF NOT EXISTS topups (
    id SERIAL PRIMARY KEY,
    request_id VARCHAR(50) UNIQUE NOT NULL DEFAULT concat('TP', EXTRACT(EPOCH FROM NOW())::bigint),
    account_id INTEGER NOT NULL REFERENCES ad_accounts(id),
    requester_id INTEGER NOT NULL REFERENCES users(id),
    status VARCHAR(20) NOT NULL DEFAULT 'draft',
    amount DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'CNY',
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT topups_status_check CHECK (status IN ('draft', 'pending_review', 'approved', 'rejected', 'paid', 'confirmed', 'cancelled'))
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_projects_owner_id ON projects(owner_id);
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);
CREATE INDEX IF NOT EXISTS idx_channels_manager_id ON channels(manager_id);
CREATE INDEX IF NOT EXISTS idx_ad_accounts_channel_id ON ad_accounts(channel_id);
CREATE INDEX IF NOT EXISTS idx_ad_accounts_project_id ON ad_accounts(project_id);
CREATE INDEX IF NOT EXISTS idx_ad_accounts_assigned_to ON ad_accounts(assigned_to);
CREATE INDEX IF NOT EXISTS idx_daily_reports_account_id ON daily_reports(account_id);
CREATE INDEX IF NOT EXISTS idx_daily_reports_date ON daily_reports(report_date);
CREATE INDEX IF NOT EXISTS idx_topups_account_id ON topups(account_id);
CREATE INDEX IF NOT EXISTS idx_topups_status ON topups(status);

-- 创建更新时间戳函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 创建触发器
DO $$
DECLARE
    table_name TEXT;
BEGIN
    FOREACH table_name IN ARRAY ARRAY['users', 'projects', 'channels', 'ad_accounts', 'daily_reports', 'topups']
    LOOP
        EXECUTE format('DROP TRIGGER IF EXISTS update_%I_updated_at ON %I', table_name, table_name);
        EXECUTE format('CREATE TRIGGER update_%I_updated_at BEFORE UPDATE ON %I FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()', table_name, table_name);
    END LOOP;
END $$;

-- 创建密码加密函数
CREATE OR REPLACE FUNCTION hash_password(password TEXT)
RETURNS TEXT AS $$
BEGIN
    RETURN crypt(password, gen_salt('bf'));
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 插入默认管理员用户
INSERT INTO users (
    email,
    username,
    password_hash,
    full_name,
    role,
    is_active,
    is_superuser,
    email_verified
) VALUES (
    'admin@aiad.com',
    'admin',
    crypt('admin123!@#', gen_salt('bf')),
    '系统管理员',
    'admin',
    true,
    true,
    true
) ON CONFLICT (email) DO NOTHING;

-- 显示成功消息
DO $$
BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE '数据库初始化成功完成！';
    RAISE NOTICE '';
    RAISE NOTICE '默认管理员账号：';
    RAISE NOTICE '  邮箱: admin@aiad.com';
    RAISE NOTICE '  密码: admin123!@#';
    RAISE NOTICE '========================================';
END $$;
```

### 第4步：执行脚本

1. 点击 **Run** 按钮执行脚本
2. 等待执行完成（应该很快完成）
3. 查看执行结果，确认没有错误

## 📊 验证数据库

执行以下查询验证表是否创建成功：

```sql
-- 查看所有表
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;
```

应该看到以下表：
- ad_accounts
- channels
- daily_reports
- projects
- topups
- users

## 🎯 下一步操作

### 1. 配置应用环境变量

在您的应用 `.env.local` 文件中添加：

```env
NEXT_PUBLIC_SUPABASE_URL=https://jzmcoivxhiyidizncyaq.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key_here
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here
```

### 2. 创建完整的RLS策略（可选）

如果需要完整的安全策略，可以执行 `02_create_rls_policies.sql` 中的内容。

### 3. 登录测试

1. 启动您的应用
2. 使用默认管理员账号登录
3. 立即修改默认密码！

## 🔧 故障排除

### 如果遇到权限错误

确保您使用的是 `service_role` 密钥，而不是 `anon` 密钥。

### 如果表已存在

脚本使用了 `IF NOT EXISTS`，应该不会重复创建。如果仍有问题，可以：

```sql
-- 删除所有表（谨慎使用！）
DROP TABLE IF EXISTS topups CASCADE;
DROP TABLE IF EXISTS daily_reports CASCADE;
DROP TABLE IF EXISTS ad_accounts CASCADE;
DROP TABLE IF EXISTS channels CASCADE;
DROP TABLE IF EXISTS projects CASCADE;
DROP TABLE IF EXISTS users CASCADE;
```

### 如果需要完整功能

执行完整的脚本 `01_optimize_database_schema.sql` 来获得所有功能，包括：
- 完整的表结构
- 所有索引
- 完整的RLS策略
- 审计日志
- 视图和更多函数

---

**重要提醒**：
- 请在生产环境中立即修改默认密码
- 定期备份您的数据库
- 根据需要调整RLS策略