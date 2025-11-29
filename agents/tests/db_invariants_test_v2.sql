-- =============================================================================
-- DEPRECATED: 本文件已迁移至 tests/db_invariants_test_v2.sql
-- =============================================================================
--
-- 正确的 SQL 测试文件位置:
--   - SOT_FILES["DB_INVARIANTS_SQL"] -> tests/db_invariants_test_v2.sql
--   - 完整测试版本 -> backend/db/db_invariants_test_v2.sql
--
-- 本文件仅作为历史记录保留，不应被使用。
-- 如果看到此文件被加载，说明路径配置可能有误。
-- =============================================================================

DO $$
BEGIN
    RAISE WARNING '[DEPRECATED] agents/tests/db_invariants_test_v2.sql 已弃用';
    RAISE WARNING '请使用 tests/db_invariants_test_v2.sql (相对于项目根目录)';
END $$;
