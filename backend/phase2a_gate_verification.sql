-- ============================================================
-- Phase 2A Gate 验证脚本
-- 用途: 验证 Phase 2A 所有时间字段迁移是否成功
-- 执行环境: Dev
-- 执行时机: Phase 2A-001/002/003 全部完成后
-- ============================================================

-- ========== Gate #2A: 全局验证 ==========

-- Check 1: 验证所有时间字段类型是否为 TIMESTAMPTZ
SELECT
    table_name,
    column_name,
    data_type,
    CASE
        WHEN data_type = 'timestamp with time zone' THEN '✅ PASS'
        ELSE '❌ FAIL'
    END AS status
FROM information_schema.columns
WHERE table_name IN (
    'projects',
    'project_members',
    'project_expenses',
    'topup_requests',
    'topup_transactions',
    'topup_approval_logs',
    'ledger_entries'
)
AND column_name IN (
    'created_at',
    'updated_at',
    'occurred_at',
    'joined_at',
    'paid_at'
)
ORDER BY table_name, column_name;

-- 预期结果: 所有字段的 status 应为 '✅ PASS'
-- 总共应该有 14 行记录，全部 PASS

-- ========== Check 2: 数据完整性验证 ==========

-- 表 1: projects
SELECT
    'projects' AS table_name,
    COUNT(*) AS total_count,
    COUNT(created_at) AS created_at_count,
    COUNT(updated_at) AS updated_at_count,
    CASE
        WHEN COUNT(*) = COUNT(created_at) AND COUNT(*) = COUNT(updated_at) THEN '✅ PASS'
        ELSE '❌ FAIL'
    END AS status
FROM projects;

-- 表 2: project_members
SELECT
    'project_members' AS table_name,
    COUNT(*) AS total_count,
    COUNT(joined_at) AS joined_at_count,
    CASE
        WHEN COUNT(*) = COUNT(joined_at) THEN '✅ PASS'
        ELSE '❌ FAIL'
    END AS status
FROM project_members;

-- 表 3: project_expenses
SELECT
    'project_expenses' AS table_name,
    COUNT(*) AS total_count,
    COUNT(occurred_at) AS occurred_at_count,
    COUNT(created_at) AS created_at_count,
    CASE
        WHEN COUNT(*) = COUNT(occurred_at) AND COUNT(*) = COUNT(created_at) THEN '✅ PASS'
        ELSE '❌ FAIL'
    END AS status
FROM project_expenses;

-- 表 4: topup_requests
SELECT
    'topup_requests' AS table_name,
    COUNT(*) AS total_count,
    COUNT(created_at) AS created_at_count,
    COUNT(updated_at) AS updated_at_count,
    CASE
        WHEN COUNT(*) = COUNT(created_at) AND COUNT(*) = COUNT(updated_at) THEN '✅ PASS'
        ELSE '❌ FAIL'
    END AS status
FROM topup_requests;

-- 表 5: topup_transactions
SELECT
    'topup_transactions' AS table_name,
    COUNT(*) AS total_count,
    COUNT(paid_at) AS paid_at_count,
    COUNT(created_at) AS created_at_count,
    CASE
        WHEN COUNT(*) = COUNT(paid_at) AND COUNT(*) = COUNT(created_at) THEN '✅ PASS'
        ELSE '❌ FAIL'
    END AS status
FROM topup_transactions;

-- 表 6: topup_approval_logs
SELECT
    'topup_approval_logs' AS table_name,
    COUNT(*) AS total_count,
    COUNT(created_at) AS created_at_count,
    CASE
        WHEN COUNT(*) = COUNT(created_at) THEN '✅ PASS'
        ELSE '❌ FAIL'
    END AS status
FROM topup_approval_logs;

-- 表 7: ledger_entries
SELECT
    'ledger_entries' AS table_name,
    COUNT(*) AS total_count,
    COUNT(occurred_at) AS occurred_at_count,
    CASE
        WHEN COUNT(*) = COUNT(occurred_at) THEN '✅ PASS'
        ELSE '❌ FAIL'
    END AS status
FROM ledger_entries;

-- 预期结果: 所有表的 status 应为 '✅ PASS'

-- ========== Check 3: 时间范围合理性验证 ==========

-- 检查是否有异常的时间值（未来时间或过早时间）
SELECT
    'projects' AS table_name,
    MIN(created_at) AS earliest_time,
    MAX(created_at) AS latest_time,
    MAX(updated_at) AS latest_update,
    CASE
        WHEN MIN(created_at) >= '2020-01-01'::TIMESTAMPTZ
             AND MAX(created_at) <= NOW()
             AND MAX(updated_at) <= NOW() THEN '✅ PASS'
        ELSE '❌ FAIL'
    END AS status
FROM projects
WHERE created_at IS NOT NULL;

SELECT
    'project_members' AS table_name,
    MIN(joined_at) AS earliest_time,
    MAX(joined_at) AS latest_time,
    CASE
        WHEN MIN(joined_at) >= '2020-01-01'::TIMESTAMPTZ
             AND MAX(joined_at) <= NOW() THEN '✅ PASS'
        ELSE '❌ FAIL'
    END AS status
FROM project_members
WHERE joined_at IS NOT NULL;

SELECT
    'project_expenses' AS table_name,
    MIN(occurred_at) AS earliest_time,
    MAX(occurred_at) AS latest_time,
    CASE
        WHEN MIN(occurred_at) >= '2020-01-01'::TIMESTAMPTZ
             AND MAX(occurred_at) <= NOW() THEN '✅ PASS'
        ELSE '❌ FAIL'
    END AS status
FROM project_expenses
WHERE occurred_at IS NOT NULL;

SELECT
    'topup_requests' AS table_name,
    MIN(created_at) AS earliest_time,
    MAX(created_at) AS latest_time,
    CASE
        WHEN MIN(created_at) >= '2020-01-01'::TIMESTAMPTZ
             AND MAX(created_at) <= NOW() THEN '✅ PASS'
        ELSE '❌ FAIL'
    END AS status
FROM topup_requests
WHERE created_at IS NOT NULL;

SELECT
    'topup_transactions' AS table_name,
    MIN(paid_at) AS earliest_time,
    MAX(paid_at) AS latest_time,
    CASE
        WHEN MIN(paid_at) >= '2020-01-01'::TIMESTAMPTZ
             AND MAX(paid_at) <= NOW() THEN '✅ PASS'
        ELSE '❌ FAIL'
    END AS status
FROM topup_transactions
WHERE paid_at IS NOT NULL;

SELECT
    'ledger_entries' AS table_name,
    MIN(occurred_at) AS earliest_time,
    MAX(occurred_at) AS latest_time,
    CASE
        WHEN MIN(occurred_at) >= '2020-01-01'::TIMESTAMPTZ
             AND MAX(occurred_at) <= NOW() THEN '✅ PASS'
        ELSE '❌ FAIL'
    END AS status
FROM ledger_entries
WHERE occurred_at IS NOT NULL;

-- 预期结果: 所有表的 status 应为 '✅ PASS'

-- ========== Check 4: Timezone 设置验证 ==========

-- 验证数据库当前 timezone 设置
SHOW timezone;
-- 预期结果: UTC（或应用层使用的标准时区）

-- ========== Check 5: 综合统计 ==========

SELECT
    '=== Phase 2A Gate 验证汇总 ===' AS summary;

SELECT
    'Phase 2A-001' AS revision,
    'projects 模块' AS module,
    3 AS tables_affected,
    5 AS fields_affected,
    (SELECT COUNT(DISTINCT table_name)
     FROM information_schema.columns
     WHERE table_name IN ('projects', 'project_members', 'project_expenses')
     AND column_name IN ('created_at', 'updated_at', 'occurred_at', 'joined_at')
     AND data_type = 'timestamp with time zone') AS verified_tables,
    (SELECT COUNT(*)
     FROM information_schema.columns
     WHERE table_name IN ('projects', 'project_members', 'project_expenses')
     AND column_name IN ('created_at', 'updated_at', 'occurred_at', 'joined_at')
     AND data_type = 'timestamp with time zone') AS verified_fields

UNION ALL

SELECT
    'Phase 2A-002' AS revision,
    'topup 模块' AS module,
    3 AS tables_affected,
    5 AS fields_affected,
    (SELECT COUNT(DISTINCT table_name)
     FROM information_schema.columns
     WHERE table_name IN ('topup_requests', 'topup_transactions', 'topup_approval_logs')
     AND column_name IN ('created_at', 'updated_at', 'paid_at')
     AND data_type = 'timestamp with time zone') AS verified_tables,
    (SELECT COUNT(*)
     FROM information_schema.columns
     WHERE table_name IN ('topup_requests', 'topup_transactions', 'topup_approval_logs')
     AND column_name IN ('created_at', 'updated_at', 'paid_at')
     AND data_type = 'timestamp with time zone') AS verified_fields

UNION ALL

SELECT
    'Phase 2A-003' AS revision,
    'ledger 模块' AS module,
    1 AS tables_affected,
    1 AS fields_affected,
    (SELECT COUNT(DISTINCT table_name)
     FROM information_schema.columns
     WHERE table_name = 'ledger_entries'
     AND column_name = 'occurred_at'
     AND data_type = 'timestamp with time zone') AS verified_tables,
    (SELECT COUNT(*)
     FROM information_schema.columns
     WHERE table_name = 'ledger_entries'
     AND column_name = 'occurred_at'
     AND data_type = 'timestamp with time zone') AS verified_fields;

-- 预期结果:
-- Phase 2A-001: verified_tables = 3, verified_fields = 5
-- Phase 2A-002: verified_tables = 3, verified_fields = 5
-- Phase 2A-003: verified_tables = 1, verified_fields = 1

-- ========== 最终结论 ==========

SELECT
    CASE
        WHEN (
            SELECT COUNT(*)
            FROM information_schema.columns
            WHERE table_name IN (
                'projects', 'project_members', 'project_expenses',
                'topup_requests', 'topup_transactions', 'topup_approval_logs',
                'ledger_entries'
            )
            AND column_name IN ('created_at', 'updated_at', 'occurred_at', 'joined_at', 'paid_at')
            AND data_type = 'timestamp with time zone'
        ) = 14
        THEN '✅ Phase 2A Gate 验证通过！所有 14 个时间字段已成功升级为 TIMESTAMPTZ'
        ELSE '❌ Phase 2A Gate 验证失败！请检查上述详细验证结果'
    END AS gate_result;

-- ============================================================
-- 验证通过标准:
-- 1. Check 1: 所有 14 个字段类型为 'timestamp with time zone'
-- 2. Check 2: 所有表的数据完整性验证 PASS
-- 3. Check 3: 所有时间值在合理范围内（2020-01-01 至当前时间）
-- 4. Check 4: 数据库 timezone 设置正确
-- 5. Check 5: 综合统计正确（verified_fields 总计 = 14）
--
-- 如果所有检查通过，可以进入 3 天观察期
-- 如果任何检查失败，立即停止并执行回滚
-- ============================================================
