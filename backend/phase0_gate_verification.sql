-- =====================================================================
-- Phase 0 Gate 验证脚本
-- =====================================================================
-- 用途: 验证废弃表清理和新表创建是否成功
-- 执行方式: psql $DATABASE_URL -f phase0_gate_verification.sql
-- 预期结果: 所有 Check 都应该 PASS
-- =====================================================================

\echo ''
\echo '====================================================================='
\echo 'Phase 0 Gate 验证'
\echo '====================================================================='
\echo ''

-- ====================================================================
-- Check 1: 废弃表已删除
-- ====================================================================
\echo '[Check 1] 验证废弃表已删除...'

SELECT
    CASE
        WHEN NOT EXISTS (SELECT 1 FROM pg_tables WHERE tablename = 'topups')
            AND NOT EXISTS (SELECT 1 FROM pg_tables WHERE tablename = 'ledgers')
        THEN '  [PASS] 废弃表已删除 (topups, ledgers)'
        ELSE '  [FAIL] 废弃表仍然存在'
    END AS check1_result;

-- 详细检查
SELECT
    tablename,
    CASE
        WHEN tablename IN ('topups', 'ledgers') THEN '[FAIL] 废弃表未删除'
        ELSE '[INFO] 表存在'
    END AS status
FROM pg_tables
WHERE tablename IN ('topups', 'ledgers');

\echo ''

-- ====================================================================
-- Check 2: 新表已创建
-- ====================================================================
\echo '[Check 2] 验证新表已创建...'

WITH required_tables AS (
    SELECT unnest(ARRAY[
        'topup_requests',
        'topup_transactions',
        'topup_approval_logs',
        'ledger_entries'
    ]) AS table_name
),
existing_tables AS (
    SELECT tablename AS table_name
    FROM pg_tables
    WHERE schemaname = 'public'
    AND tablename IN ('topup_requests', 'topup_transactions', 'topup_approval_logs', 'ledger_entries')
)
SELECT
    rt.table_name,
    CASE
        WHEN et.table_name IS NOT NULL THEN '[PASS] 表已创建'
        ELSE '[FAIL] 表缺失'
    END AS status
FROM required_tables rt
LEFT JOIN existing_tables et ON rt.table_name = et.table_name
ORDER BY rt.table_name;

-- 汇总
SELECT
    CASE
        WHEN COUNT(*) = 4 THEN '  [PASS] 所有新表都已创建 (4/4)'
        ELSE '  [FAIL] 部分表缺失 (' || COUNT(*) || '/4)'
    END AS check2_result
FROM pg_tables
WHERE tablename IN ('topup_requests', 'topup_transactions', 'topup_approval_logs', 'ledger_entries');

\echo ''

-- ====================================================================
-- Check 3: 主键类型验证（应为 BIGSERIAL）
-- ====================================================================
\echo '[Check 3] 验证主键类型（应为 bigint）...'

SELECT
    t.table_name,
    c.column_name,
    c.data_type,
    CASE
        WHEN c.data_type = 'bigint' AND c.column_default LIKE 'nextval%' THEN '[PASS] BIGSERIAL'
        ELSE '[FAIL] 类型不符'
    END AS status
FROM information_schema.tables t
JOIN information_schema.columns c ON t.table_name = c.table_name
WHERE t.table_schema = 'public'
AND t.table_name IN ('topup_requests', 'topup_transactions', 'topup_approval_logs', 'ledger_entries')
AND c.column_name = 'id'
ORDER BY t.table_name;

\echo ''

-- ====================================================================
-- Check 4: 时间字段类型验证（应为 TIMESTAMPTZ）
-- ====================================================================
\echo '[Check 4] 验证时间字段类型（应为 timestamptz）...'

SELECT
    table_name,
    column_name,
    data_type,
    CASE
        WHEN data_type = 'timestamp with time zone' THEN '[PASS] TIMESTAMPTZ'
        ELSE '[FAIL] 类型不符: ' || data_type
    END AS status
FROM information_schema.columns
WHERE table_name IN ('topup_requests', 'topup_transactions', 'topup_approval_logs', 'ledger_entries')
AND column_name IN ('created_at', 'updated_at', 'paid_at', 'occurred_at')
ORDER BY table_name, column_name;

-- 汇总
SELECT
    CASE
        WHEN COUNT(*) = COUNT(*) FILTER (WHERE data_type = 'timestamp with time zone')
        THEN '  [PASS] 所有时间字段都是 TIMESTAMPTZ'
        ELSE '  [FAIL] 部分时间字段类型不符'
    END AS check4_result
FROM information_schema.columns
WHERE table_name IN ('topup_requests', 'topup_transactions', 'topup_approval_logs', 'ledger_entries')
AND column_name IN ('created_at', 'updated_at', 'paid_at', 'occurred_at');

\echo ''

-- ====================================================================
-- Check 5: 外键约束验证
-- ====================================================================
\echo '[Check 5] 验证外键约束...'

SELECT
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name,
    '[PASS] FK 已建立' AS status
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
    AND tc.table_schema = kcu.table_schema
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
    AND ccu.table_schema = tc.table_schema
WHERE tc.constraint_type = 'FOREIGN KEY'
AND tc.table_name IN ('topup_requests', 'topup_transactions', 'topup_approval_logs', 'ledger_entries')
ORDER BY tc.table_name, kcu.column_name;

-- 汇总外键数量
SELECT
    CASE
        WHEN COUNT(*) >= 10 THEN '  [PASS] 外键约束已建立 (' || COUNT(*) || ' 个)'
        ELSE '  [WARN] 外键数量偏少 (' || COUNT(*) || ' 个，预期 >= 10)'
    END AS check5_result
FROM information_schema.table_constraints AS tc
WHERE tc.constraint_type = 'FOREIGN KEY'
AND tc.table_name IN ('topup_requests', 'topup_transactions', 'topup_approval_logs', 'ledger_entries');

\echo ''

-- ====================================================================
-- Check 6: 索引验证
-- ====================================================================
\echo '[Check 6] 验证索引创建...'

SELECT
    schemaname,
    tablename,
    indexname,
    '[PASS] 索引已创建' AS status
FROM pg_indexes
WHERE schemaname = 'public'
AND tablename IN ('topup_requests', 'topup_transactions', 'topup_approval_logs', 'ledger_entries')
AND indexname LIKE 'idx_%'
ORDER BY tablename, indexname;

-- 汇总索引数量
SELECT
    CASE
        WHEN COUNT(*) >= 11 THEN '  [PASS] 索引已创建 (' || COUNT(*) || ' 个，预期 11 个)'
        ELSE '  [WARN] 索引数量偏少 (' || COUNT(*) || ' 个，预期 11 个)'
    END AS check6_result
FROM pg_indexes
WHERE schemaname = 'public'
AND tablename IN ('topup_requests', 'topup_transactions', 'topup_approval_logs', 'ledger_entries')
AND indexname LIKE 'idx_%';

\echo ''

-- ====================================================================
-- Check 7: 字段完整性检查
-- ====================================================================
\echo '[Check 7] 验证关键字段完整性...'

-- topup_requests 必须字段
WITH topup_requests_fields AS (
    SELECT column_name
    FROM information_schema.columns
    WHERE table_name = 'topup_requests'
    AND column_name IN ('id', 'request_no', 'project_id', 'applicant_id', 'amount', 'status', 'created_at', 'updated_at')
)
SELECT
    CASE
        WHEN COUNT(*) = 8 THEN '  [PASS] topup_requests 必要字段完整 (8/8)'
        ELSE '  [FAIL] topup_requests 字段缺失 (' || COUNT(*) || '/8)'
    END AS topup_requests_check
FROM topup_requests_fields;

-- topup_transactions 必须字段
WITH topup_transactions_fields AS (
    SELECT column_name
    FROM information_schema.columns
    WHERE table_name = 'topup_transactions'
    AND column_name IN ('id', 'topup_request_id', 'paid_amount', 'payment_method', 'paid_at', 'created_at')
)
SELECT
    CASE
        WHEN COUNT(*) = 6 THEN '  [PASS] topup_transactions 必要字段完整 (6/6)'
        ELSE '  [FAIL] topup_transactions 字段缺失 (' || COUNT(*) || '/6)'
    END AS topup_transactions_check
FROM topup_transactions_fields;

-- ledger_entries 必须字段
WITH ledger_entries_fields AS (
    SELECT column_name
    FROM information_schema.columns
    WHERE table_name = 'ledger_entries'
    AND column_name IN ('id', 'project_id', 'entry_type', 'amount', 'currency', 'occurred_at')
)
SELECT
    CASE
        WHEN COUNT(*) = 6 THEN '  [PASS] ledger_entries 必要字段完整 (6/6)'
        ELSE '  [FAIL] ledger_entries 字段缺失 (' || COUNT(*) || '/6)'
    END AS ledger_entries_check
FROM ledger_entries_fields;

\echo ''

-- ====================================================================
-- 综合汇总
-- ====================================================================
\echo '====================================================================='
\echo '综合汇总'
\echo '====================================================================='

SELECT
    '  [CHECK 1] 废弃表删除' AS check_item,
    CASE
        WHEN NOT EXISTS (SELECT 1 FROM pg_tables WHERE tablename IN ('topups', 'ledgers'))
        THEN 'PASS'
        ELSE 'FAIL'
    END AS result;

SELECT
    '  [CHECK 2] 新表创建' AS check_item,
    CASE
        WHEN COUNT(*) = 4 THEN 'PASS'
        ELSE 'FAIL'
    END AS result
FROM pg_tables
WHERE tablename IN ('topup_requests', 'topup_transactions', 'topup_approval_logs', 'ledger_entries');

SELECT
    '  [CHECK 3] 主键类型' AS check_item,
    CASE
        WHEN COUNT(*) = COUNT(*) FILTER (WHERE c.data_type = 'bigint' AND c.column_default LIKE 'nextval%')
        THEN 'PASS'
        ELSE 'FAIL'
    END AS result
FROM information_schema.columns c
WHERE c.table_name IN ('topup_requests', 'topup_transactions', 'topup_approval_logs', 'ledger_entries')
AND c.column_name = 'id';

SELECT
    '  [CHECK 4] 时间字段类型' AS check_item,
    CASE
        WHEN COUNT(*) = COUNT(*) FILTER (WHERE data_type = 'timestamp with time zone')
        THEN 'PASS'
        ELSE 'FAIL'
    END AS result
FROM information_schema.columns
WHERE table_name IN ('topup_requests', 'topup_transactions', 'topup_approval_logs', 'ledger_entries')
AND column_name IN ('created_at', 'updated_at', 'paid_at', 'occurred_at');

SELECT
    '  [CHECK 5] 外键约束' AS check_item,
    CASE
        WHEN COUNT(*) >= 10 THEN 'PASS'
        ELSE 'WARN'
    END AS result
FROM information_schema.table_constraints AS tc
WHERE tc.constraint_type = 'FOREIGN KEY'
AND tc.table_name IN ('topup_requests', 'topup_transactions', 'topup_approval_logs', 'ledger_entries');

SELECT
    '  [CHECK 6] 索引创建' AS check_item,
    CASE
        WHEN COUNT(*) >= 11 THEN 'PASS'
        ELSE 'WARN'
    END AS result
FROM pg_indexes
WHERE schemaname = 'public'
AND tablename IN ('topup_requests', 'topup_transactions', 'topup_approval_logs', 'ledger_entries')
AND indexname LIKE 'idx_%';

\echo ''
\echo '====================================================================='
\echo '如果所有 Check 都是 PASS，Phase 0 迁移成功！'
\echo '如果有 FAIL，请检查迁移脚本执行日志，必要时执行回滚。'
\echo '====================================================================='
\echo ''
