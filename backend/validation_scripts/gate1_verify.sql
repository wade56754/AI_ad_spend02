-- ========== Gate #1: reconciliation主键迁移验证 ==========
\echo '==========================================';
\echo '🚪 Gate #1: reconciliation主键迁移验证';
\echo '==========================================';

-- 验证1: 主键类型
\echo '';
\echo '检查项1: 主键类型为bigint';
SELECT
    table_name,
    column_name,
    data_type,
    CASE
        WHEN data_type = 'bigint' THEN '✅ PASS'
        ELSE '❌ FAIL'
    END as status
FROM information_schema.columns
WHERE table_name IN (
    'reconciliation_batches',
    'reconciliation_details',
    'reconciliation_adjustments',
    'reconciliation_reports'
)
AND column_name = 'id';

-- 验证2: 序列类型
\echo '';
\echo '检查项2: 序列类型为bigint';
SELECT
    sequencename,
    data_type,
    CASE
        WHEN data_type = 'bigint' THEN '✅ PASS'
        ELSE '❌ FAIL'
    END as status
FROM pg_sequences
WHERE sequencename LIKE 'reconciliation_%_id_seq';

-- 验证3: FK关联完整性
\echo '';
\echo '检查项3: FK关联完整性（无孤儿记录）';
SELECT
    'reconciliation_details → batches' as fk_relation,
    COUNT(*) as total,
    COUNT(b.id) as matched,
    COUNT(*) - COUNT(b.id) as orphans,
    CASE
        WHEN COUNT(*) = COUNT(b.id) THEN '✅ PASS'
        ELSE '❌ FAIL'
    END as status
FROM reconciliation_details d
LEFT JOIN reconciliation_batches b ON d.batch_id = b.id;

-- 验证4: 状态枚举
\echo '';
\echo '检查项4: 状态枚举合法性';
SELECT
    status,
    COUNT(*) as count,
    CASE
        WHEN status IN ('draft', 'pending', 'reviewing', 'closed') THEN '✅ PASS'
        ELSE '❌ FAIL - 非法状态!'
    END as status_check
FROM reconciliation_batches
GROUP BY status;

\echo '';
\echo '==========================================';
\echo '🏁 Gate #1 验证完成';
\echo '==========================================';
