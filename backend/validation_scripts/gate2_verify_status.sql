-- =============================================
-- Gate #2: 验证status枚举对齐结果
-- =============================================
-- 用途: 验证reconciliation_batches.status是否符合STATE_MACHINE.md规范
-- 执行时机: Rev 002执行后
-- 通过标准: 仅存在SoT定义的4个状态值
-- =============================================

\echo '=========================================='
\echo '🔍 Gate #2: 验证status枚举对齐结果'
\echo '=========================================='

-- ============ 检查1: 验证status值合法性 ============
\echo ''
\echo '✓ 检查1: 验证status值合法性'
\echo '预期: 仅包含 draft, pending, reviewing, closed'

SELECT
    status,
    COUNT(*) as record_count,
    CASE
        WHEN status IN ('draft', 'pending', 'reviewing', 'closed') THEN '✅ PASS'
        ELSE '❌ FAIL - 非法状态值'
    END as validation_result
FROM reconciliation_batches
GROUP BY status
ORDER BY status;

-- ============ 检查2: 统计迁移映射结果 ============
\echo ''
\echo '✓ 检查2: 统计迁移映射结果（对比legacy列）'
\echo '预期: 所有旧值都正确映射到新值'

SELECT
    status_legacy as old_status,
    status as new_status,
    COUNT(*) as count,
    CASE
        WHEN status_legacy = 'pending' AND status = 'draft' THEN '✅ PASS'
        WHEN status_legacy = 'processing' AND status = 'pending' THEN '✅ PASS'
        WHEN status_legacy = 'completed' AND status = 'closed' THEN '✅ PASS'
        WHEN status_legacy = 'exception' AND status = 'reviewing' THEN '✅ PASS'
        WHEN status_legacy = 'resolved' AND status = 'closed' THEN '✅ PASS'
        ELSE '❌ FAIL - 映射错误'
    END as validation_result
FROM reconciliation_batches
WHERE status_legacy IS NOT NULL
GROUP BY status_legacy, status
ORDER BY status_legacy;

-- ============ 检查3: 验证CHECK约束 ============
\echo ''
\echo '✓ 检查3: 验证CHECK约束是否正确更新'

SELECT
    conname as constraint_name,
    pg_get_constraintdef(oid) as constraint_definition,
    CASE
        WHEN pg_get_constraintdef(oid) LIKE '%draft%pending%reviewing%closed%' THEN '✅ PASS'
        ELSE '❌ FAIL - 约束未更新'
    END as validation_result
FROM pg_constraint
WHERE conrelid = 'reconciliation_batches'::regclass
  AND contype = 'c'
  AND conname LIKE '%status%';

-- ============ 检查4: 识别异常记录 ============
\echo ''
\echo '✓ 检查4: 识别异常记录（如果有）'

SELECT
    id,
    batch_no,
    status,
    status_legacy,
    '❌ 非法状态' as issue
FROM reconciliation_batches
WHERE status NOT IN ('draft', 'pending', 'reviewing', 'closed')
LIMIT 10;

-- 如果没有异常记录
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM reconciliation_batches
        WHERE status NOT IN ('draft', 'pending', 'reviewing', 'closed')
    ) THEN
        RAISE NOTICE '✅ 未发现异常记录';
    END IF;
END $$;

-- ============ 总结报告 ============
\echo ''
\echo '=========================================='
\echo '📊 Gate #2 验证总结'
\echo '=========================================='

DO $$
DECLARE
    total_batches INTEGER;
    invalid_status INTEGER;
    legacy_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO total_batches FROM reconciliation_batches;
    SELECT COUNT(*) INTO invalid_status FROM reconciliation_batches
        WHERE status NOT IN ('draft', 'pending', 'reviewing', 'closed');
    SELECT COUNT(*) INTO legacy_count FROM reconciliation_batches
        WHERE status_legacy IS NOT NULL;

    RAISE NOTICE '总批次数: %', total_batches;
    RAISE NOTICE '非法状态记录数: %', invalid_status;
    RAISE NOTICE '包含legacy备份的记录数: %', legacy_count;
    RAISE NOTICE '==========================================';

    IF invalid_status = 0 THEN
        RAISE NOTICE '✅ Gate #2 通过！可继续执行Rev 003';
    ELSE
        RAISE NOTICE '❌ Gate #2 失败！请检查非法状态记录';
        RAISE NOTICE '回退命令: alembic downgrade 20251117_reconciliation_pk_bigserial';
    END IF;
END $$;

\echo '=========================================='
