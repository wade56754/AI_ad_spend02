-- =====================================================
-- 数据库诊断脚本
-- 用于检查当前数据库状态和冲突
-- =====================================================

-- 检查当前数据库中已存在的表
SELECT
    table_name,
    table_type
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;

-- 检查扩展
SELECT
    extname,
    extversion
FROM pg_extension
WHERE extname IN ('uuid-ossp', 'pgcrypto');

-- 检查用户表结构
SELECT
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_schema = 'public'
AND table_name = 'users'
ORDER BY ordinal_position;

-- 检查约束
SELECT
    tc.constraint_name,
    tc.constraint_type,
    kcu.column_name
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu
    ON tc.constraint_name = kcu.constraint_name
WHERE tc.table_schema = 'public'
AND tc.table_name = 'users';

-- 检查是否有默认管理员用户
SELECT * FROM users WHERE email = 'admin@aiad.com' OR username = 'admin';

-- 检查触发器
SELECT
    trigger_name,
    event_manipulation,
    event_object_table,
    action_timing
FROM information_schema.triggers
WHERE trigger_schema = 'public';

-- 检查RLS状态
SELECT
    schemaname,
    tablename,
    rowsecurity
FROM pg_tables
WHERE schemaname = 'public';

-- 检查函数
SELECT
    proname,
    prosrc
FROM pg_proc
WHERE proname IN ('update_updated_at_column', 'hash_password');