-- =====================================================
-- 安全迁移脚本 - 适配现有数据库
-- 版本: 2.1
--
-- 说明：此脚本会检查现有表结构并安全地添加缺失的字段和表
-- =====================================================

-- 设置执行参数
SET statement_timeout = '600s';
SET search_path = public;

-- =====================================================
-- 第一步：诊断现有结构
-- =====================================================

-- 创建临时表存储诊断结果
DROP TABLE IF EXISTS migration_diagnosis;
CREATE TEMP TABLE migration_diagnosis (
    step TEXT,
    status TEXT,
    details TEXT
);

-- 记录诊断开始
INSERT INTO migration_diagnosis VALUES ('诊断开始', 'INFO', '开始检查现有数据库结构');

-- 检查必要的扩展
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'uuid-ossp') THEN
        INSERT INTO migration_diagnosis VALUES ('扩展检查', 'WARNING', 'uuid-ossp扩展不存在，将创建');
        CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
    ELSE
        INSERT INTO migration_diagnosis VALUES ('扩展检查', 'OK', 'uuid-ossp扩展已存在');
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'pgcrypto') THEN
        INSERT INTO migration_diagnosis VALUES ('扩展检查', 'WARNING', 'pgcrypto扩展不存在，将创建');
        CREATE EXTENSION IF NOT EXISTS "pgcrypto";
    ELSE
        INSERT INTO migration_diagnosis VALUES ('扩展检查', 'OK', 'pgcrypto扩展已存在');
    END IF;
END $$;

-- =====================================================
-- 第二步：安全地更新users表
-- =====================================================

-- 检查并添加缺失的列
DO $$
BEGIN
    -- 检查username列
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'users' AND column_name = 'username'
    ) THEN
        INSERT INTO migration_diagnosis VALUES ('users表', 'ADD COLUMN', '添加username列');
        ALTER TABLE users ADD COLUMN username VARCHAR(50);
        -- 生成唯一的username
        UPDATE users SET username = 'user_' || id WHERE username IS NULL;
        ALTER TABLE users ALTER COLUMN username SET NOT NULL;
        CREATE UNIQUE INDEX IF NOT EXISTS idx_users_username ON users(username);
    ELSE
        INSERT INTO migration_diagnosis VALUES ('users表', 'OK', 'username列已存在');
    END IF;

    -- 检查role列
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'users' AND column_name = 'role'
    ) THEN
        INSERT INTO migration_diagnosis VALUES ('users表', 'ADD COLUMN', '添加role列');
        ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'media_buyer';
        ALTER TABLE users ALTER COLUMN role SET NOT NULL;
        -- 添加约束
        ALTER TABLE users ADD CONSTRAINT users_role_check
            CHECK (role IN ('admin', 'finance', 'data_operator', 'account_manager', 'media_buyer'));
    ELSE
        INSERT INTO migration_diagnosis VALUES ('users表', 'OK', 'role列已存在');
    END IF;

    -- 检查is_superuser列
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'users' AND column_name = 'is_superuser'
    ) THEN
        INSERT INTO migration_diagnosis VALUES ('users表', 'ADD COLUMN', '添加is_superuser列');
        ALTER TABLE users ADD COLUMN is_superuser BOOLEAN DEFAULT false;
    ELSE
        INSERT INTO migration_diagnosis VALUES ('users表', 'OK', 'is_superuser列已存在');
    END IF;

    -- 检查full_name列
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'users' AND column_name = 'full_name'
    ) THEN
        INSERT INTO migration_diagnosis VALUES ('users表', 'ADD COLUMN', '添加full_name列');
        ALTER TABLE users ADD COLUMN full_name VARCHAR(100);
    ELSE
        INSERT INTO migration_diagnosis VALUES ('users表', 'OK', 'full_name列已存在');
    END IF;

    -- 检查avatar_url列
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'users' AND column_name = 'avatar_url'
    ) THEN
        INSERT INTO migration_diagnosis VALUES ('users表', 'ADD COLUMN', '添加avatar_url列');
        ALTER TABLE users ADD COLUMN avatar_url TEXT;
    ELSE
        INSERT INTO migration_diagnosis VALUES ('users表', 'OK', 'avatar_url列已存在');
    END IF;

    -- 检查email_verified列
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'users' AND column_name = 'email_verified'
    ) THEN
        INSERT INTO migration_diagnosis VALUES ('users表', 'ADD COLUMN', '添加email_verified列');
        ALTER TABLE users ADD COLUMN email_verified BOOLEAN DEFAULT false;
    ELSE
        INSERT INTO migration_diagnosis VALUES ('users表', 'OK', 'email_verified列已存在');
    END IF;

    -- 检查last_login_at列
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'users' AND column_name = 'last_login_at'
    ) THEN
        INSERT INTO migration_diagnosis VALUES ('users表', 'ADD COLUMN', '添加last_login_at列');
        ALTER TABLE users ADD COLUMN last_login_at TIMESTAMPTZ;
    ELSE
        INSERT INTO migration_diagnosis VALUES ('users表', 'OK', 'last_login_at列已存在');
    END IF;

    -- 检查created_at列
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'users' AND column_name = 'created_at'
    ) THEN
        INSERT INTO migration_diagnosis VALUES ('users表', 'ADD COLUMN', '添加created_at列');
        ALTER TABLE users ADD COLUMN created_at TIMESTAMPTZ DEFAULT NOW();
    ELSE
        INSERT INTO migration_diagnosis VALUES ('users表', 'OK', 'created_at列已存在');
    END IF;

    -- 检查updated_at列
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'users' AND column_name = 'updated_at'
    ) THEN
        INSERT INTO migration_diagnosis VALUES ('users表', 'ADD COLUMN', '添加updated_at列');
        ALTER TABLE users ADD COLUMN updated_at TIMESTAMPTZ DEFAULT NOW();
    ELSE
        INSERT INTO migration_diagnosis VALUES ('users表', 'OK', 'updated_at列已存在');
    END IF;
END $$;

-- =====================================================
-- 第三步：创建其他表（如果不存在）
-- =====================================================

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

INSERT INTO migration_diagnosis VALUES ('projects表', 'OK', '项目表已就绪');

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

INSERT INTO migration_diagnosis VALUES ('channels表', 'OK', '渠道表已就绪');

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

INSERT INTO migration_diagnosis VALUES ('ad_accounts表', 'OK', '广告账户表已就绪');

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

INSERT INTO migration_diagnosis VALUES ('daily_reports表', 'OK', '日报表已就绪');

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

INSERT INTO migration_diagnosis VALUES ('topups表', 'OK', '充值表已就绪');

-- =====================================================
-- 第四步：创建索引
-- =====================================================

-- 用户表索引
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- 其他表索引
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

INSERT INTO migration_diagnosis VALUES ('索引创建', 'OK', '所有索引已创建');

-- =====================================================
-- 第五步：创建函数和触发器
-- =====================================================

-- 更新时间戳函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 创建触发器（只创建不存在的）
DO $$
DECLARE
    table_name TEXT;
    trigger_name TEXT;
BEGIN
    FOREACH table_name IN ARRAY ARRAY['users', 'projects', 'channels', 'ad_accounts', 'daily_reports', 'topups']
    LOOP
        trigger_name := 'update_' || table_name || '_updated_at';

        -- 检查触发器是否存在
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.triggers
            WHERE trigger_name = trigger_name
        ) THEN
            EXECUTE format('CREATE TRIGGER %I BEFORE UPDATE ON %I FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()', trigger_name, table_name);
        END IF;
    END LOOP;
END $$;

INSERT INTO migration_diagnosis VALUES ('触发器', 'OK', '所有触发器已创建');

-- 创建密码加密函数
CREATE OR REPLACE FUNCTION hash_password(password TEXT)
RETURNS TEXT AS $$
BEGIN
    RETURN crypt(password, gen_salt('bf'));
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

INSERT INTO migration_diagnosis VALUES ('函数', 'OK', '密码加密函数已创建');

-- =====================================================
-- 第六步：创建或更新管理员用户
-- =====================================================

-- 检查是否存在管理员用户
DO $$
BEGIN
    -- 尝试通过email查找
    IF NOT EXISTS (SELECT 1 FROM users WHERE email = 'admin@aiad.com') THEN
        -- 检查是否有admin用户
        IF EXISTS (SELECT 1 FROM users WHERE username = 'admin') THEN
            -- 更新现有admin用户
            UPDATE users
            SET
                email = COALESCE(NULLIF(email, ''), 'admin@aiad.com'),
                full_name = COALESCE(NULLIF(full_name, ''), '系统管理员'),
                role = COALESCE(NULLIF(role, ''), 'admin'),
                is_superuser = true,
                email_verified = true
            WHERE username = 'admin';

            INSERT INTO migration_diagnosis VALUES ('管理员用户', 'UPDATED', '已更新现有admin用户');
        ELSE
            -- 创建新的管理员用户
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
                hash_password('admin123!@#'),
                '系统管理员',
                'admin',
                true,
                true,
                true
            );

            INSERT INTO migration_diagnosis VALUES ('管理员用户', 'CREATED', '已创建新admin用户');
        END IF;
    ELSE
        INSERT INTO migration_diagnosis VALUES ('管理员用户', 'OK', 'admin用户已存在');
    END IF;
END $$;

-- =====================================================
-- 第七步：显示诊断结果
-- =====================================================

SELECT * FROM migration_diagnosis ORDER BY step;

-- 显示最终状态
DO $$
BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE '迁移完成！';
    RAISE NOTICE '';
    RAISE NOTICE '默认管理员账号：';
    RAISE NOTICE '  邮箱: admin@aiad.com';
    RAISE NOTICE '  密码: admin123!@#';
    RAISE NOTICE '========================================';
END $$;

-- 清理临时表
DROP TABLE migration_diagnosis;