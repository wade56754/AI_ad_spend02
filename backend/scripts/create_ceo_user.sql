-- 创建 CEO 账号 SQL 脚本
-- 适用于数据库表已存在的情况

-- 注意：请根据实际数据库类型调整语法
-- PostgreSQL: 使用 CURRENT_TIMESTAMP
-- SQLite: 使用 datetime('now')

-- 检查用户是否已存在
-- SELECT id, username, email, role FROM users WHERE email = 'ceo@example.com' OR username = 'ceo';

-- 如果用户不存在，执行以下 SQL（PostgreSQL 版本）
/*
INSERT INTO users (
    id, 
    username, 
    email, 
    password_hash, 
    full_name, 
    role, 
    is_active, 
    created_at, 
    updated_at
)
VALUES (
    gen_random_uuid(),  -- PostgreSQL UUID 生成
    'ceo',
    'ceo@example.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyY5GyY5GyY5',  -- 这是 'ceo123456' 的 bcrypt 哈希（示例，需要重新生成）
    '老板',
    'admin',
    true,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
)
ON CONFLICT (email) DO UPDATE SET
    password_hash = EXCLUDED.password_hash,
    role = EXCLUDED.role,
    updated_at = CURRENT_TIMESTAMP;
*/

-- SQLite 版本
/*
INSERT OR REPLACE INTO users (
    id, 
    username, 
    email, 
    password_hash, 
    full_name, 
    role, 
    is_active, 
    created_at, 
    updated_at
)
VALUES (
    lower(hex(randomblob(4)) || '-' || hex(randomblob(2)) || '-4' || substr(hex(randomblob(2)), 2) || '-' || substr('89ab', abs(random()) % 4 + 1, 1) || substr(hex(randomblob(2)), 2) || '-' || hex(randomblob(6))),  -- SQLite UUID 生成
    'ceo',
    'ceo@example.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyY5GyY5GyY5',  -- 需要替换为实际的 bcrypt 哈希
    '老板',
    'admin',
    1,
    datetime('now'),
    datetime('now')
);
*/

